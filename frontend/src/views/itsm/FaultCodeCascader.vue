<template>
  <div class="fault-code-cascader">
    <!-- 最近选择区（门店维度 Top 10） -->
    <div v-if="recentItems.length" class="recent-row">
      <span class="recent-label">最近选择：</span>
      <el-tag
        v-for="it in recentItems"
        :key="it.code"
        size="small"
        class="recent-tag"
        @click="onPickRecent(it.code)"
      >
        {{ it.label }}（{{ it.code }}）
      </el-tag>
    </div>
    <!-- 关键字跨层级搜索（后端 keyword 搜索，弥补懒加载 filterable 盲区） -->
    <div class="search-row">
      <el-input
        v-model="searchKw"
        size="small"
        clearable
        placeholder="关键字搜索故障代码（编码/名称）"
        @input="onSearchInput"
        @focus="onSearchFocus"
        @blur="onSearchBlur"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div v-if="showSearchPanel" class="search-panel">
        <div v-if="searchLoading" class="search-hint">搜索中…</div>
        <div v-else-if="!searchResults.length" class="search-hint">无匹配结果</div>
        <div
          v-for="it in searchResults"
          :key="it.code"
          class="search-item"
          @mousedown.prevent="onPickSearch(it)"
        >
          <span class="search-item-label">{{ it.label }}</span>
          <span class="search-item-code">（{{ it.code }}）</span>
        </div>
      </div>
    </div>
    <!-- 级联选择器（懒加载 + 树形导航） -->
    <el-cascader
      v-model="selected"
      :options="options"
      :props="cascaderProps"
      :placeholder="placeholder"
      :disabled="disabled"
      filterable
      clearable
      style="width:100%"
      @change="onChange"
    >
      <template #default="{ data }">
        <span>{{ data.label }}</span>
        <span
          v-if="data.code"
          style="color:#909399;font-size:12px;margin-left:4px"
        >({{ data.code }})</span>
      </template>
    </el-cascader>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { fetchArchiveCodes } from '@/api/itsm'
import { pinyin } from 'pinyin-pro'

interface CascaderOption { value: string; label: string; code?: string; leaf: boolean; children?: CascaderOption[] }
interface RecentItem { code: string; label: string; ts: number }
interface SearchResult { code: string; label: string; arch_group?: string; fault_type?: string }

const props = withDefaults(defineProps<{
  modelValue?: string
  placeholder?: string
  disabled?: boolean
  /** 门店ID（用于门店维度最近选择缓存） */
  storeId?: string
  /** 故障类型前缀过滤（B3：配件更换时按 itemcd 前两位预过滤故障现象） */
  faultType?: string
}>(), {
  modelValue: '',
  placeholder: '请选择故障代码',
  disabled: false,
  storeId: '',
  faultType: '',
})

const emit = defineEmits<{ 'update:modelValue': [v: string]; change: [v: string, node?: CascaderOption] }>()

const selected = ref<string[]>([])
const options = ref<CascaderOption[]>([])

// ---- 关键字跨层级搜索 ----
const searchKw = ref('')
const searchResults = ref<SearchResult[]>([])
const searchLoading = ref(false)
const showSearchPanel = ref(false)
let searchTimer: ReturnType<typeof setTimeout> | null = null

async function onSearchInput(kw: string): Promise<void> {
  if (searchTimer) clearTimeout(searchTimer)
  const trimmed = (kw || '').trim()
  if (!trimmed) {
    searchResults.value = []
    showSearchPanel.value = false
    return
  }
  showSearchPanel.value = true
  searchLoading.value = true
  searchTimer = setTimeout(async () => {
    try {
      // 纯 ascii 字母/数字：按拼音首字母匹配（拉全量客户端过滤）
      const isAscii = /^[a-zA-Z0-9]+$/.test(trimmed)
      const lower = trimmed.toLowerCase()
      if (isAscii) {
        const params: Record<string, string> = { limit: '500' }
        if (props.faultType) params.fault_type = props.faultType
        const r = await fetchArchiveCodes(params)
        const items = ((r?.data || []) as unknown) as Record<string, unknown>[]
        searchResults.value = items.map(it => ({
          code: (it.arch_cd as string) || '',
          label: (it.arch_nm as string) || '',
          arch_group: (it.arch_group as string) || undefined,
          fault_type: (it.fault_type as string) || undefined,
        })).filter(it => {
          if (!it.code) return false
          // arch_cd 子串匹配 或 arch_nm 拼音首字母匹配
          if (it.code.toLowerCase().includes(lower)) return true
          const fullPinyin = pinyin(it.label, { toneType: 'none', type: 'array' }).join('').toLowerCase()
          const initials = pinyin(it.label, { pattern: 'first', toneType: 'none', type: 'array' }).join('').toLowerCase()
          return fullPinyin.includes(lower) || initials.includes(lower)
        }).slice(0, 20)
      } else {
        // 中文关键字：后端 keyword 模糊搜索（可叠加 faultType 过滤）
        const params: Record<string, string> = { keyword: trimmed, limit: '20' }
        if (props.faultType) params.fault_type = props.faultType
        const r = await fetchArchiveCodes(params)
        const items = ((r?.data || []) as unknown) as Record<string, unknown>[]
        searchResults.value = items.map(it => ({
          code: (it.arch_cd as string) || '',
          label: (it.arch_nm as string) || '',
          arch_group: (it.arch_group as string) || undefined,
          fault_type: (it.fault_type as string) || undefined,
        })).filter(it => it.code)
      }
    } catch {
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }, 200)
}

function onSearchFocus(): void {
  if (searchKw.value.trim() && searchResults.value.length) {
    showSearchPanel.value = true
  }
}

function onSearchBlur(): void {
  // 延迟关闭，允许 mousedown 选中
  setTimeout(() => { showSearchPanel.value = false }, 150)
}

function onPickSearch(it: SearchResult): void {
  selected.value = [it.code]
  emit('update:modelValue', it.code)
  emit('change', it.code, { value: it.code, label: it.label, leaf: true })
  pushRecent(it.code, it.label)
  searchKw.value = ''
  searchResults.value = []
  showSearchPanel.value = false
}

/** localStorage 键（门店维度） */
const recentKey = computed(() => `faultcode:recent:${props.storeId || '_global'}`)

/** 最近选择列表（Top 10，按时间倒序） */
const recentItems = ref<RecentItem[]>([])

/** 读取 localStorage 最近选择 */
function loadRecent(): void {
  try {
    const raw = localStorage.getItem(recentKey.value)
    if (!raw) { recentItems.value = []; return }
    const arr = JSON.parse(raw) as RecentItem[]
    recentItems.value = Array.isArray(arr) ? arr.slice(0, 10) : []
  } catch {
    recentItems.value = []
  }
}

/** 写入最近选择（去重 + Top 10 + 时间戳） */
function pushRecent(code: string, label: string): void {
  if (!code) return
  const arr = recentItems.value.filter(it => it.code !== code)
  arr.unshift({ code, label, ts: Date.now() })
  recentItems.value = arr.slice(0, 10)
  try {
    localStorage.setItem(recentKey.value, JSON.stringify(recentItems.value))
  } catch {
    // localStorage 不可用时静默忽略
  }
}

/** 点击最近选择 tag */
async function onPickRecent(code: string): Promise<void> {
  if (!code) return
  selected.value = [code]
  emit('update:modelValue', code)
  // 若 label 未知，尝试从 recentItems 取
  const ri = recentItems.value.find(it => it.code === code)
  emit('change', code, ri ? { value: code, label: ri.label, leaf: true } : undefined)
}

const cascaderProps = {
  expandTrigger: 'hover' as const,
  checkStrictly: false,
  emitPath: false,
  value: 'value',
  label: 'label',
  children: 'children',
  leaf: 'leaf',
  lazy: true,
  lazyLoad: async (node: { value?: string; level: number }, resolve: (children: CascaderOption[]) => void) => {
    // 根节点（level=0）：加载顶层
    if (node.level === 0) {
      await loadTopLevel()
      resolve(options.value)
      return
    }
    // 子节点：按父级 arch_cd 懒加载
    const parentCd = (node.value as string) || ''
    if (!parentCd) { resolve([]); return }
    const children = await loadChildren(parentCd)
    resolve(children)
  },
}

/**
 * 将后端返回的记录转为级联节点。
 */
function toOptions(items: Record<string, unknown>[]): CascaderOption[] {
  return items.map(it => {
    const childFlg = (it.child_flg as string) || ''
    const cd = (it.arch_cd as string) || ''
    const nm = (it.arch_nm as string) || ''
    return {
      value: cd,
      label: nm,
      code: cd,
      leaf: childFlg !== '1',
      children: undefined,
    }
  })
}

/**
 * 加载顶层故障代码（parent='%'，可按 faultType 过滤）。
 */
async function loadTopLevel(): Promise<void> {
  try {
    const params: Record<string, string> = { parent: '%', limit: '200' }
    if (props.faultType) params.fault_type = props.faultType
    const r = await fetchArchiveCodes(params)
    const items = ((r?.data || []) as unknown) as Record<string, unknown>[]
    options.value = toOptions(items)
  } catch {
    options.value = []
  }
}

/**
 * 懒加载子级：根据父级 arch_cd 查子节点（子级不再按 faultType 过滤，由父级已限定）。
 */
async function loadChildren(parentCd: string): Promise<CascaderOption[]> {
  try {
    const r = await fetchArchiveCodes({ parent: parentCd, limit: '200' })
    const items = ((r?.data || []) as unknown) as Record<string, unknown>[]
    return toOptions(items)
  } catch {
    return []
  }
}

onMounted(() => {
  loadTopLevel()
  loadRecent()
})

// 监听外部 modelValue 变化，回填级联路径
watch(() => props.modelValue, async (v) => {
  if (!v) { selected.value = []; return }
  if (selected.value[selected.value.length - 1] === v) return
  // 简化回填：直接设末级值，el-cascader emitPath=false 时只存末级
  selected.value = [v]
}, { immediate: true })

// 监听 storeId 变化，重新加载最近选择
watch(() => props.storeId, () => {
  loadRecent()
})

// 监听 faultType 变化，重新加载顶层选项
watch(() => props.faultType, () => {
  loadTopLevel()
})

function onChange(val: string[] | string): void {
  const v = Array.isArray(val) ? val[val.length - 1] || '' : (val as string) || ''
  emit('update:modelValue', v)
  const node = findOption(options.value, v)
  emit('change', v, node)
  // 写入最近选择
  if (v && node) {
    pushRecent(v, node.label)
  } else if (v) {
    // 末级节点可能未加载，label 从 recentItems 或 options 找
    const ri = recentItems.value.find(it => it.code === v)
    pushRecent(v, ri?.label || v)
  }
}

function findOption(opts: CascaderOption[], target: string): CascaderOption | undefined {
  for (const o of opts) {
    if (o.value === target) return o
    if (o.children?.length) {
      const sub = findOption(o.children, target)
      if (sub) return sub
    }
  }
  return undefined
}

defineExpose({ loadTopLevel, loadChildren, loadRecent })
</script>

<style scoped>
.fault-code-cascader {
  width: 100%;
}
.recent-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  font-size: 12px;
}
.recent-label {
  color: #909399;
  flex-shrink: 0;
}
.recent-tag {
  cursor: pointer;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.recent-tag:hover {
  background-color: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
}
.search-row {
  position: relative;
  margin-bottom: 6px;
}
.search-panel {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 2000;
  max-height: 240px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
.search-hint {
  padding: 8px 12px;
  color: #909399;
  font-size: 12px;
}
.search-item {
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.search-item:hover {
  background-color: #f5f7fa;
}
.search-item-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.search-item-code {
  color: #909399;
  font-size: 12px;
  flex-shrink: 0;
}
</style>
