<template>
    <div class="bom-page">
        <!-- 左侧：物料分类树 -->
        <div class="tree-panel">
            <el-card shadow="never">
                <template #header><span>成品分类</span></template>
                <el-input v-model="treeFilter" placeholder="过滤分类" size="small" clearable />
                <el-tree :data="treeData" :props="{ label: 'class_nm', children: 'children' }"
                    node-key="class_cd" highlight-current :filter-node-method="filterNode"
                    ref="treeRef" @node-click="onTreeNodeClick" style="margin-top:8px" />
            </el-card>
        </div>

        <!-- 右侧 -->
        <div class="content-panel">
            <!-- 子类表格 -->
            <div class="list-panel" v-if="showClasses && childClasses.length">
                <el-card shadow="never">
                    <template #header><span>{{ selectedClassNm }} — 子分类（共 {{ childClasses.length }} 个）</span></template>
                    <el-table :data="childClasses" stripe size="small" highlight-current-row @row-click="(row: ItemClassNode) => onSelectChildClass(row)">
                        <el-table-column prop="class_cd" label="类别代码" width="100" />
                        <el-table-column prop="class_nm" label="类别名称" min-width="150" show-overflow-tooltip />
                        <el-table-column prop="parent_cd" label="所属大类" width="80" />
                        <el-table-column prop="opercd" label="操作员" width="80">
                            <template #default="{ row }">{{ (row as ItemClassNode).opercd || '-' }}</template>
                        </el-table-column>
                        <el-table-column label="创建日期" width="110">
                            <template #default="{ row }">{{ (row as ItemClassNode).gendate || '-' }}</template>
                        </el-table-column>
                    </el-table>
                </el-card>
            </div>

            <!-- 成品列表 -->
            <div class="list-panel" v-if="showItems && items.length >= 0">
                <el-card shadow="never">
                    <template #header>
                        <div class="panel-header">
                            <span>成品列表 — {{ selectedClassNm || '请选择分类' }}（共 {{ total }} 个）</span>
                        </div>
                    </template>
                    <div style="display:flex;gap:8px;margin-bottom:12px">
                        <el-input v-model="searchText" placeholder="搜索成品编码或名称" clearable size="small" @keyup.enter="onSearch" @clear="onSearch" style="flex:1" />
                    </div>
                    <el-table :data="items" v-loading="loading" stripe highlight-current-row @row-click="onSelectItem" size="small">
                        <el-table-column prop="item_cd" label="成品编码" width="100" />
                        <el-table-column prop="item_nm" label="成品名称" min-width="160" show-overflow-tooltip />
                        <el-table-column prop="spec" label="规格" min-width="120" show-overflow-tooltip />
                        <el-table-column label="BOM状态" width="80" align="center">
                            <template #default="{ row }">
                                <template v-if="bomStatusMap[row.item_cd] === undefined"><span style="font-size:12px;color:#ccc">-</span></template>
                                <template v-else-if="bomStatusMap[row.item_cd] === null"><el-tag type="info" size="small">无BOM</el-tag></template>
                                <template v-else><el-tag :type="bomStatusMap[row.item_cd]==='0'?'danger':'success'" size="small">{{ bomStatusMap[row.item_cd]==='0'?'无效':'有效' }}</el-tag></template>
                            </template>
                        </el-table-column>
                    </el-table>
                    <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top: 12px; justify-content: flex-end" />
                </el-card>
            </div>

        </div>

        <!-- BOM 编辑/新建弹窗 -->
        <el-dialog :title="bomDialogTitle" v-model="bomDialogVisible" width="420px">
            <el-form :model="bomForm" label-width="80px">
                <el-form-item label="成品编码">
                    <el-input :model-value="bomForm.bomcd" disabled />
                </el-form-item>
                <el-form-item label="BOM 名称">
                    <el-input v-model="bomForm.bomnm" placeholder="如 TFP4000 4LR4" />
                </el-form-item>
                <el-form-item label="状态">
                    <el-select v-model="bomForm.useflg" style="width: 100%">
                        <el-option label="有效" value="1" /><el-option label="无效" value="0" />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="bomDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSaveBom" :loading="saving">确定</el-button>
            </template>
        </el-dialog>

        <!-- BOM 详情弹窗 -->
        <el-dialog :title="(selectedItem?.item_nm || '') + ' BOM 配置'" v-model="bomDetailVisible" width="750px" @opened="onBomDetailOpened">
            <template v-if="selectedBom">
                <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap">
                    <span style="font-weight:bold">{{ selectedItem?.item_cd }}</span>
                    <span style="color:#999;font-size:13px">{{ selectedBom.bomnm || selectedItem?.item_nm }}</span>
                    <el-tag :type="bomType.type" size="small">{{ bomType.label }}</el-tag>
                    <el-tag :type="selectedBom.useflg==='0'?'danger':'success'" size="small">{{ selectedBom.useflg==='0'?'无效':'有效' }}</el-tag>
                    <el-button type="primary" size="small" @click="openAddDetail">添加物料</el-button>
                    <el-button size="small" @click="openEditBom">重命名</el-button>
                </div>
                <el-table :data="details" stripe size="small">
                    <el-table-column prop="itemcd" label="物料代码" width="100" />
                    <el-table-column prop="item_nm" label="物料名称" min-width="160" show-overflow-tooltip />
                    <el-table-column label="数量" width="80" align="center">
                        <template #default="{ row }"><el-input-number v-model="row.bomqty" :min="1" size="small" controls-position="right" style="width:70px" @change="(v: number|undefined) => handleUpdateDetail(row, 'bomqty', v)" /></template>
                    </el-table-column>
                    <el-table-column label="类型" width="110" align="center">
                        <template #default="{ row }"><el-select v-model="row.itemtyp" size="small" style="width:100px" @change="(v: unknown) => handleUpdateDetail(row, 'itemtyp', v)"><el-option label="外设配件" value="0" /><el-option label="核心配件" value="1" /></el-select></template>
                    </el-table-column>
                    <el-table-column label="操作" width="70" align="center">
                        <template #default="{ row }"><el-button type="danger" link size="small" @click="handleDeleteDetail(row)">删除</el-button></template>
                    </el-table-column>
                </el-table>
            </template>
            <div v-else class="empty-hint">该成品暂无 BOM 配置
                <el-button type="primary" size="small" style="margin-top:12px" @click="openCreateBomForItem">新建 BOM</el-button>
            </div>
        </el-dialog>

        <!-- 添加物料弹窗（树形多选） -->
        <el-dialog title="添加物料" v-model="addDetailVisible" width="600px">
            <div style="display:flex;gap:12px">
                <div style="flex:1;max-height:400px;overflow:auto;border:1px solid #eee;border-radius:4px;padding:8px">
                    <el-input v-model="addTreeFilter" placeholder="过滤物料" size="small" clearable style="margin-bottom:8px" />
                    <el-tree :data="addTreeData" :props="{ label: 'class_nm', children: 'children' }"
                        node-key="class_cd" show-checkbox :filter-node-method="filterAddTree"
                        ref="addTreeRef" @check="onAddTreeCheck" />
                </div>
                <div style="width:180px;flex-shrink:0">
                    <div style="font-size:13px;margin-bottom:4px">已选 {{ checkedItems.length }} 个</div>
                    <div style="max-height:340px;overflow:auto;font-size:12px">
                        <div v-for="it in checkedItems" :key="it.class_cd" style="display:flex;align-items:center;margin-bottom:4px">
                            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="it.class_nm">{{ it.class_nm }}</span>
                            <el-input-number v-model="checkQtys[it.class_cd]" :min="1" size="small" style="width:60px" controls-position="right" />
                            <el-select v-model="checkTyps[it.class_cd]" size="small" style="width:80px;margin-left:4px">
                                <el-option label="外设" value="0" /><el-option label="核心" value="1" />
                            </el-select>
                        </div>
                    </div>
                </div>
            </div>
            <template #footer>
                <el-button @click="addDetailVisible = false">取消</el-button>
                <el-button type="primary" @click="handleBatchAddDetail" :loading="addingDetail" :disabled="!checkedItems.length">批量添加</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, computed } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'
import {
    fetchBom, createBom, updateBom, deleteBom,
    addBomDetail, updateBomDetail, deleteBomDetail,
    fetchItems, fetchBomClassTree,
} from '@/api/master'
import type { BomRecord, BomDetailRecord, ItemRecord, ItemClassNode } from '@/api/master'

const treeData = ref<ItemClassNode[]>([]); const treeFilter = ref(''); const treeRef = ref()
const selectedClassCd = ref(''); const selectedClassNm = ref('')
const childClasses = ref<ItemClassNode[]>([]); const showClasses = ref(false); const showItems = ref(false)

function filterNode(value: string, data: { class_nm: string }): boolean {
    return !value || data.class_nm.toLowerCase().includes(value.toLowerCase())
}
watch(treeFilter, (v) => { (treeRef.value as any)?.filter(v) })
async function loadTree() { try { const r = await fetchBomClassTree(); treeData.value = r.data || [] } catch { /* */ } }

function onTreeNodeClick(node: ItemClassNode) {
    selectedItem.value = null; selectedBom.value = null
    selectedClassNm.value = node.class_nm
    // 点击具体物料（成品）→ 直接显示 BOM 详情
    if (node.type === 'item') {
        showClasses.value = false; showItems.value = false
        const fakeItem = { item_cd: node.class_cd, item_nm: node.class_nm } as ItemRecord
        onSelectItem(fakeItem)
        return
    }
    const subClasses = (node.children || []).filter((c: ItemClassNode) => c.type === 'class')
    if (subClasses.length > 0) {
        childClasses.value = subClasses; showClasses.value = true; showItems.value = false
        return
    }
    selectedClassCd.value = node.class_cd; showClasses.value = false; showItems.value = true
    page.value = 1; loadItems()
}

function onSelectChildClass(c: ItemClassNode) { onTreeNodeClick(c) }

// 成品列表（仅 typflg=1）
const items = ref<ItemRecord[]>([]); const loading = ref(false)
const total = ref(0); const page = ref(1); const perPage = ref(20); const searchText = ref('')
const selectedItem = ref<ItemRecord | null>(null)
const selectedBom = ref<BomRecord | null>(null)
const details = ref<BomDetailRecord[]>([]); const detailLoading = ref(false)
const bomDetailVisible = ref(false); const bomStatusMap = ref<Record<string,string|null>>({})

const bomDialogVisible = ref(false); const isEditingBom = ref(false); const saving = ref(false)
const bomForm = reactive({ bomcd: '', bomnm: '', useflg: '1' })
const bomDialogTitle = computed(() => isEditingBom.value ? '编辑 BOM' : '新建 BOM')

const addDetailVisible = ref(false); const addingDetail = ref(false)
const addTreeData = ref<ItemClassNode[]>([]); const addTreeFilter = ref(''); const addTreeRef = ref()
const checkedItems = ref<ItemClassNode[]>([])
const checkQtys = reactive<Record<string,number>>({}); const checkTyps = reactive<Record<string,string>>({})

function filterAddTree(value: string, data: { class_nm: string }): boolean {
    return !value || data.class_nm.toLowerCase().includes(value.toLowerCase())
}
watch(addTreeFilter, (v) => { (addTreeRef.value as any)?.filter(v) })

function onAddTreeCheck(_node: ItemClassNode, checked: { checkedNodes: ItemClassNode[] }) {
    checkedItems.value = checked.checkedNodes.filter(n => n.type === 'item')
    for (const it of checkedItems.value) {
        if (!(it.class_cd in checkQtys)) checkQtys[it.class_cd] = 1
        if (!(it.class_cd in checkTyps)) checkTyps[it.class_cd] = '0'
    }
}

async function handleBatchAddDetail() {
    if (!selectedBom.value || !checkedItems.value.length) return
    addingDetail.value = true
    const total = checkedItems.value.length
    let done = 0
    try {
        for (const it of checkedItems.value) {
            const qty = checkQtys[it.class_cd] || 1
            const typ = checkTyps[it.class_cd] || '0'
            await addBomDetail(selectedBom.value.bomcd, { itemcd: it.class_cd, bomqty: qty, itemtyp: typ })
            done++
        }
        ElMessage.success(`已添加 ${done} 个配件`)
        addDetailVisible.value = false
        if (selectedItem.value) await onSelectItem(selectedItem.value)
    } catch { ElMessage.error(`已添加 ${done}/${total}，部分失败`) }
    finally { addingDetail.value = false }
}

const bomType = computed(() => {
    if (!selectedBom.value?.details || selectedBom.value.details.length === 0) return { type: 'info', label: '主机+配件' }
    return selectedBom.value.details.some(d => d.itemtyp === '1')
        ? { type: 'warning', label: '全配件' } : { type: 'info', label: '主机+配件' }
})

watch(page, () => loadItems()); watch(perPage, () => { page.value = 1; loadItems() })
onMounted(() => { loadTree(); showItems.value = true; loadItems() })

async function loadItems() {
    loading.value = true
    try {
        const params: Record<string, unknown> = { page: page.value, per_page: perPage.value, typflg: '1' }
        if (searchText.value) params.search = searchText.value
        if (selectedClassCd.value) params.class_cd = selectedClassCd.value
        const res = await fetchItems(params as any)
        items.value = (res.data as any).items || []
        total.value = (res.data as any).total || 0
        // 批量查 BOM 状态
        const itemcds = items.value.map(i => i.item_cd).join(',')
        if (itemcds) {
            try { const r = await request.get('/bom/check', { params: { items: itemcds } }); bomStatusMap.value = r.data || {} } catch { /* */ }
        }
    } catch { ElMessage.error('加载失败') }
    finally { loading.value = false }
}

function onSearch() { page.value = 1; loadItems() }

async function onSelectItem(row: ItemRecord) {
    selectedItem.value = row; detailLoading.value = true
    try {
        const res = await fetchBom(row.item_cd.toUpperCase())
        selectedBom.value = (res.data && res.data.bomcd) ? res.data : null
        details.value = selectedBom.value?.details || []
    } catch {
        selectedBom.value = null; details.value = []
    }
    finally { detailLoading.value = false; bomDetailVisible.value = true }
}
function onBomDetailOpened() { if (!selectedBom.value) return }

async function openCreateBomForItem() {
    if (!selectedItem.value) return
    try {
        const bomcd = selectedItem.value.item_cd.toUpperCase()
        const existing = await fetchBom(bomcd)
        if (!existing.data || !existing.data.bomcd) {
            await createBom({ bomcd, bomnm: selectedItem.value.item_nm })
        }
    } catch (e: unknown) {
        const status = (e as any)?.response?.status
        if (status && status !== 404) ElMessage.error('创建BOM失败')
    }
    await onSelectItem(selectedItem.value)
}

function openEditBom() {
    if (!selectedBom.value) return
    bomForm.bomcd = selectedBom.value.bomcd
    bomForm.bomnm = selectedBom.value.bomnm
    bomForm.useflg = selectedBom.value.useflg; isEditingBom.value = true; bomDialogVisible.value = true
}

async function handleSaveBom() {
    if (!bomForm.bomnm.trim()) { ElMessage.warning('请填写 BOM 名称'); return }
    saving.value = true
    try {
        if (isEditingBom.value) {
            await updateBom(bomForm.bomcd, { bomnm: bomForm.bomnm, useflg: bomForm.useflg })
        } else {
            await createBom({ bomcd: bomForm.bomcd, bomnm: bomForm.bomnm })
        }
        bomDialogVisible.value = false
        if (selectedItem.value) { await onSelectItem(selectedItem.value); loadItems() }
    } catch { ElMessage.error('保存失败') }
    finally { saving.value = false }
}

async function openAddDetail() {
    addDetailVisible.value = true
    checkedItems.value = []
    try {
        const r = await fetchBomClassTree('0')
        addTreeData.value = r.data || []
    } catch { ElMessage.error('操作失败') }
}

async function handleUpdateDetail(row: BomDetailRecord, field: string, val: unknown) {
    if (!selectedBom.value) return
    try { await updateBomDetail(selectedBom.value.bomcd, row.itemcd, { [field]: val }) } catch { /* */ }
}
async function handleDeleteDetail(row: BomDetailRecord) {
    if (!selectedBom.value) return
    try {
        await ElMessageBox.confirm(`确定移除 ${row.itemcd}？`, '确认', { type: 'warning' })
        await deleteBomDetail(selectedBom.value.bomcd, row.itemcd)
        if (selectedItem.value) await onSelectItem(selectedItem.value)
    } catch { ElMessage.error('操作失败') }
}
</script>

<style lang="scss" scoped>
.bom-page { display: flex; gap: 12px; height: calc(100vh - 120px) }
.tree-panel { width: 220px; flex-shrink: 0; overflow: auto }
.content-panel { flex: 1; display: flex; flex-direction: column; gap: 12px; overflow: auto }
.panel-header { display: flex; justify-content: space-between; align-items: center }
.empty-hint { text-align: center; color: #999; padding: 40px 0 }
</style>
