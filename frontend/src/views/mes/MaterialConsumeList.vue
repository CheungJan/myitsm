<template>
  <div class="page">
    <div class="page-header">
      <h2>物料消耗</h2>
      <el-radio-group v-model="viewMode" size="small">
        <el-radio-button label="group">按工单分组</el-radio-button>
        <el-radio-button label="flat">明细列表</el-radio-button>
      </el-radio-group>
    </div>
    <el-card shadow="never" style="margin-bottom:12px">
      <el-form inline size="small">
        <el-form-item label="工单"><el-input v-model="filters.woId" placeholder="工单号" clearable style="width:160px" @change="applyFilters"/></el-form-item>
        <el-form-item label="类型"><el-select v-model="filters.consumeType" placeholder="全部" clearable style="width:120px" @change="applyFilters"><el-option v-for="t in consumeTypes" :key="t.value" :label="t.label" :value="t.value"/></el-select></el-form-item>
        <el-form-item label="日期"><el-date-picker v-model="filters.dateRange" type="daterange" range-separator="~" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width:240px" @change="applyFilters"/></el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <!-- 按工单分组视图 -->
      <template v-if="viewMode === 'group'">
        <el-table :data="groupedItems" v-loading="loading" stripe size="small" @expand-change="onExpand" row-key="wo_id">
          <el-table-column type="expand">
            <template #default="{ row }">
              <!-- 成本汇总卡片 -->
              <div style="margin:8px 24px 12px;padding:12px;background:#f5f7fa;border-radius:4px">
                <div style="display:flex;gap:20px;flex-wrap:wrap">
                  <span><b>计划成本:</b> ¥{{row._costSummary.planCost.toFixed(2)}}</span>
                  <span><b>实际成本:</b> ¥{{row._costSummary.actualCost.toFixed(2)}}</span>
                  <span style="color:#ff4d4f"><b>损耗成本:</b> ¥{{row._costSummary.lossCost.toFixed(2)}}</span>
                </div>
              </div>
              <!-- 按消耗类型分组 -->
              <div v-for="type in consumeTypes" :key="type.value" style="margin:4px 0 4px 24px;width:calc(100% - 24px)">
                <div v-if="row._groupedByType[type.value]?.length" style="margin-bottom:8px">
                  <div style="font-weight:600;padding:6px 0;color:#606266">{{type.label}}</div>
                  <el-table :data="row._groupedByType[type.value]" size="small" stripe>
                    <el-table-column prop="item_cd" label="物料编码" width="100"/>
                    <el-table-column label="计划用量" width="80"><template #default="{row:r}">{{r.plan_qty||0}}</template></el-table-column>
                    <el-table-column label="实际用量" width="80"><template #default="{row:r}">{{r.actual_qty||0}}</template></el-table-column>
                    <el-table-column label="单价" width="90"><template #default="{row:r}">¥{{r.unit_cost?.toFixed(2)||'-'}}</template></el-table-column>
                    <el-table-column label="总成本" width="100"><template #default="{row:r}">¥{{r.total_cost?.toFixed(2)||'-'}}</template></el-table-column>
                    <el-table-column label="来源单据" width="120">
                      <template #default="{row:r}">
                        <el-link v-if="r.ref_bill_id" type="primary" @click="viewBill(r)">{{r.ref_bill_id}}</el-link>
                        <span v-else>-</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="ref_qc_id" label="关联质检" width="100"/>
                    <el-table-column prop="consume_date" label="日期" width="100"/>
                  </el-table>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="wo_id" label="工单编号" width="140"/>
          <el-table-column prop="material_count" label="物料数" width="80"/>
          <el-table-column prop="total_actual" label="总消耗" width="80"/>
          <el-table-column label="总成本" width="120">
            <template #default="{row}">
              <span style="font-weight:600">¥{{row._costSummary?.actualCost?.toFixed(2)||'0.00'}}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>

      <!-- 明细列表视图 -->
      <template v-else>
        <el-table :data="flatItems" v-loading="loading" stripe size="small">
          <el-table-column prop="wo_id" label="工单编号" width="120"/>
          <el-table-column prop="item_cd" label="物料编码" width="100"/>
          <el-table-column label="消耗类型" width="90">
            <template #default="{row}">
              <el-tag :type="consumeTypeTag(row.consume_type)" size="small">{{consumeTypeLabel(row.consume_type)}}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="计划用量" width="80"><template #default="{row}">{{row.plan_qty||0}}</template></el-table-column>
          <el-table-column label="实际用量" width="80"><template #default="{row}">{{row.actual_qty||0}}</template></el-table-column>
          <el-table-column label="单价" width="90"><template #default="{row}">¥{{row.unit_cost?.toFixed(2)||'-'}}</template></el-table-column>
          <el-table-column label="总成本" width="100"><template #default="{row}">¥{{row.total_cost?.toFixed(2)||'-'}}</template></el-table-column>
          <el-table-column label="来源单据" width="120">
            <template #default="{row}">
              <el-link v-if="row.ref_bill_id" type="primary" @click="viewBill(row)">{{row.ref_bill_id}}</el-link>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="ref_qc_id" label="关联质检" width="100"/>
          <el-table-column prop="consume_date" label="日期" width="100"/>
        </el-table>
      </template>

      <div v-if="flatItems.length" style="margin-top:12px;padding:8px 12px;background:#f5f7fa;border-radius:4px;font-size:13px;display:flex;gap:20px;flex-wrap:wrap">
        <span>总数: <b>{{totalSummary.totalItems}}</b> 条</span>
        <span v-for="t in consumeTypes" :key="t.value">{{t.label}}: <b>{{totalSummary.typeCounts[t.value]||0}}</b></span>
        <span style="color:#409eff">总成本: <b>¥{{totalSummary.totalCost.toFixed(2)}}</b></span>
      </div>

      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchAllMaterialConsumes } from '@/api/mes'
import { useDict } from '@/composables/useDict'
import type { MesRecord } from '@/api/mes'

const router = useRouter()
const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const rawItems = ref<MesRecord[]>([])
const allItems = ref<MesRecord[]>([])  // 完整数据集，用于前端筛选
const groupedItems = ref<any[]>([])
const viewMode = ref<'group'|'flat'>('group')

const filters = ref({ woId: '', consumeType: '', dateRange: [] as string[] })

const filteredRawItems = computed(() => {
  let items = allItems.value
  if (filters.value.woId) {
    const kw = filters.value.woId.toLowerCase()
    items = items.filter(i => ((i as any).wo_id || '').toLowerCase().includes(kw))
  }
  if (filters.value.consumeType) {
    items = items.filter(i => String((i as any).consume_type || '1') === filters.value.consumeType)
  }
  if (filters.value.dateRange?.length === 2) {
    const [s, e] = filters.value.dateRange
    items = items.filter(i => {
      const d = (i as any).consume_date || ''
      return d >= s && d <= e
    })
  }
  return items
})

function applyFilters() {
  rawItems.value = filteredRawItems.value
  page.value = 1
  groupItems()
}

// 消耗类型映射
const { dictMap: ovMap } = useDict('OV')
const { dictMap: ivMap } = useDict('IV')
const ctTagTypeMap: Record<string, string> = { '1': 'success', '2': 'warning', '3': 'danger', '4': 'info', '5': 'info', '6': 'info' }
function consumeTypeLabel(type: string): string {
  const code = { '1':'11','2':'12','3':'7','4':'9','5':'12','6':'6' }[type] || type
  const map = type === '5' ? ivMap.value : ovMap.value
  return map[code] || type || '未知'
}
function consumeTypeTag(type: string): string { return ctTagTypeMap[type] || '' }
const consumeTypes = computed(() => {
  return ['1','2','3','4','5','6'].map(v => ({
    value: v,
    label: consumeTypeLabel(v),
    tagType: ctTagTypeMap[v] || '',
  }))
})

const totalSummary = computed(() => {
  const typeCounts: Record<string, number> = {}
  let totalCost = 0
  for (const item of rawItems.value) {
    const ct = String((item as any).consume_type || '1')
    typeCounts[ct] = (typeCounts[ct] || 0) + 1
    totalCost += Number((item as any).total_cost || 0)
  }
  return { totalItems: rawItems.value.length, typeCounts, totalCost }
})

// 明细列表（扁平视图）
const flatItems = computed(() => {
  return rawItems.value.map(item => ({
    ...item,
    consume_type_label: consumeTypeLabel((item as any).consume_type),
  }))
})

async function load() {
  loading.value = true
  try {
    const r = await fetchAllMaterialConsumes({ page: '1', per_page: '500' }) as any
    allItems.value = r?.data?.items || []
    rawItems.value = filteredRawItems.value
    total.value = rawItems.value.length
    groupItems()
  } catch { allItems.value = []; rawItems.value = []; total.value = 0 }
  finally { loading.value = false }
}

function groupItems() {
  const map = new Map<string, {
    wo_id: string;
    materials: any[];
    material_count: number;
    total_actual: number;
    _costSummary: { planCost: number; actualCost: number; lossCost: number };
    _groupedByType: Record<string, any[]>;
  }>()

  for (const item of rawItems.value) {
    const wo = (item as any).wo_id || ''
    if (!map.has(wo)) {
      map.set(wo, {
        wo_id: wo,
        materials: [],
        material_count: 0,
        total_actual: 0,
        _costSummary: { planCost: 0, actualCost: 0, lossCost: 0 },
        _groupedByType: {},
      })
    }
    const g = map.get(wo)!
    g.materials.push(item)
    g.material_count++
    g.total_actual += Number((item as any).actual_qty || 0)

    // 按消耗类型分组
    const ct = (item as any).consume_type || '1'
    if (!g._groupedByType[ct]) g._groupedByType[ct] = []
    g._groupedByType[ct].push(item)

    // 成本计算
    const totalCost = Number((item as any).total_cost || 0)
    const planQty = Number((item as any).plan_qty || 0)
    const actualQty = Number((item as any).actual_qty || 0)
    const unitCost = totalCost / actualQty || 0

    if (ct === '1') {
      // 定额：计划成本 = 计划数量 * 单价，实际成本 = 实际数量 * 单价
      g._costSummary.planCost += planQty * unitCost
      g._costSummary.actualCost += totalCost
    } else if (ct === '2') {
      // 补料：计入实际成本，无计划成本
      g._costSummary.actualCost += totalCost
    } else if (['3', '4', '5'].includes(ct)) {
      // 报废/返修/退换：计入损耗
      g._costSummary.lossCost += totalCost
      g._costSummary.actualCost += totalCost
    }
  }
  groupedItems.value = Array.from(map.values())
}

function onExpand(row: any, _rows: any[]) {
  if (!row._materials) { row._materials = row.materials }
}

// 查看来源单据
function viewBill(row: any) {
  const billType = row.ref_bill_type
  const billId = row.ref_bill_id
  if (!billId) return

  if (billType === 'OV') {
    router.push(`/warehouse/stock-out?billid=${billId}`)
  } else if (billType === 'IV') {
    router.push(`/warehouse/stock-in?billid=${billId}`)
  }
}

watch([page, perPage], load)
load()
</script>

<style scoped>
.page{padding:0}.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}
.cost-summary-card{background:#f5f7fa;border-radius:4px;padding:12px;margin-bottom:12px}
.consume-type-header{font-weight:600;padding:8px 0;color:#606266;border-bottom:1px solid #e4e7ed;margin-bottom:8px}
</style>
