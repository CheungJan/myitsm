<template>
    <div class="bom-page">
        <!-- 左侧：物料分类树 -->
        <div class="tree-panel">
            <el-card shadow="never">
                <template #header><span>物料分类</span></template>
                <el-input v-model="treeFilter" placeholder="过滤分类" size="small" clearable />
                <el-tree :data="treeData" :props="{ label: 'class_nm', children: 'children' }"
                    node-key="class_cd" highlight-current :filter-node-method="filterNode"
                    ref="treeRef" @node-click="onTreeNodeClick" style="margin-top:8px" />
            </el-card>
        </div>

        <!-- 右侧：BOM 列表 + 明细 -->
        <div class="content-panel">
            <div class="list-panel">
                <el-card shadow="never">
                    <template #header>
                        <div class="panel-header">
                            <span>BOM 列表（共 {{ total }} 条）</span>
                            <el-button type="primary" size="small" @click="openCreateBom">新增 BOM</el-button>
                        </div>
                    </template>
                    <div style="display:flex;gap:8px;margin-bottom:12px">
                        <el-input v-model="searchText" placeholder="搜索 BOM 代码或名称" clearable size="small" @keyup.enter="onSearch" @clear="onSearch" style="flex:1" />
                    </div>
                    <el-table :data="boms" v-loading="loading" stripe highlight-current-row @row-click="onSelectBom" size="small">
                        <el-table-column prop="bomcd" label="BOM 代码" width="100" />
                        <el-table-column prop="bomnm" label="BOM 名称" min-width="160" show-overflow-tooltip />
                        <el-table-column label="BOM 类型" width="95" align="center">
                            <template #default="{ row }">
                                <el-tag :type="bomType(row).type" size="small">{{ bomType(row).label }}</el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column label="状态" width="60" align="center">
                            <template #default="{ row }">
                                <el-tag :type="row.useflg === '0' ? 'danger' : 'success'" size="small">{{ row.useflg === '0' ? '无效' : '有效' }}</el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="90">
                            <template #default="{ row }">
                                <el-button type="primary" link size="small" @click.stop="openEditBom(row)">编辑</el-button>
                                <el-button type="danger" link size="small" @click.stop="handleDeleteBom(row)">删除</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                    <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top: 12px; justify-content: flex-end" />
                </el-card>
            </div>

            <div class="detail-panel" v-if="selectedBom">
                <el-card shadow="never">
                    <template #header>
                        <div class="panel-header">
                            <span>{{ selectedBom.bomcd }} — {{ selectedBom.bomnm }} 明细</span>
                            <el-button type="primary" size="small" @click="openAddDetail">添加物料</el-button>
                        </div>
                    </template>
                    <el-table :data="details" v-loading="detailLoading" stripe size="small">
                        <el-table-column prop="itemcd" label="物料代码" width="100" />
                        <el-table-column prop="item_nm" label="物料名称" min-width="160" show-overflow-tooltip />
                        <el-table-column prop="bomqty" label="数量" width="60" align="center" />
                        <el-table-column label="物料类型" width="90" align="center">
                            <template #default="{ row }">
                                <el-tag :type="row.itemtyp === '1' ? 'warning' : 'info'" size="small">{{ row.itemtyp === '1' ? '核心配件' : '外设配件' }}</el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="70" align="center">
                            <template #default="{ row }">
                                <el-button type="danger" link size="small" @click="handleDeleteDetail(row)">删除</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-card>
            </div>
        </div>

        <el-dialog :title="bomDialogTitle" v-model="bomDialogVisible" width="420px">
            <el-form :model="bomForm" label-width="80px">
                <el-form-item label="BOM 代码">
                    <el-input v-model="bomForm.bomcd" maxlength="6" placeholder="6位整机物料编码" :disabled="isEditingBom" style="text-transform: uppercase" />
                </el-form-item>
                <el-form-item label="BOM 名称">
                    <el-input v-model="bomForm.bomnm" placeholder="如 TFP4000 4LR4" />
                </el-form-item>
                <el-form-item label="状态" v-if="isEditingBom">
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

        <el-dialog title="添加物料" v-model="addDetailVisible" width="420px">
            <el-form :model="detailForm" label-width="80px">
                <el-form-item label="选择物料">
                    <el-select v-model="detailForm.itemcd" filterable placeholder="搜索物料" style="width: 100%" :filter-method="filterItems" @visible-change="onItemSelectOpen">
                        <el-option v-for="it in filteredItems" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="数量">
                    <el-input-number v-model="detailForm.bomqty" :min="1" :max="9999" style="width: 100%" />
                </el-form-item>
                <el-form-item label="物料类型">
                    <el-select v-model="detailForm.itemtyp" style="width: 100%">
                        <el-option label="外设配件" value="0" /><el-option label="核心配件" value="1" />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="addDetailVisible = false">取消</el-button>
                <el-button type="primary" @click="handleAddDetail" :loading="addingDetail">确定</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, computed } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
    fetchBoms, fetchBom, createBom, updateBom, deleteBom,
    addBomDetail, deleteBomDetail,
    fetchItems, fetchItemClassTree,
} from '@/api/master'
import type { BomRecord, BomDetailRecord, ItemRecord, ItemClassNode } from '@/api/master'

const treeData = ref<ItemClassNode[]>([])
const treeFilter = ref('')
const treeRef = ref()
const selectedClassCd = ref('')

function filterNode(value: string, data: { class_nm: string }): boolean {
    if (!value) return true
    return data.class_nm.toLowerCase().includes(value.toLowerCase())
}
watch(treeFilter, (v) => { (treeRef.value as any)?.filter(v) })

async function loadTree() {
    try { const r = await fetchItemClassTree(); treeData.value = r.data || [] } catch { /**/ }
}

function onTreeNodeClick(node: ItemClassNode) {
    selectedClassCd.value = node.type === 'item' ? '' : node.class_cd
    page.value = 1; loadBoms()
}

// ---- BOM ----
const boms = ref<BomRecord[]>([]); const loading = ref(false)
const total = ref(0); const page = ref(1); const perPage = ref(20); const searchText = ref('')
const selectedBom = ref<BomRecord | null>(null)
const details = ref<BomDetailRecord[]>([]); const detailLoading = ref(false)

const bomDialogVisible = ref(false); const isEditingBom = ref(false); const saving = ref(false)
const bomForm = reactive({ bomcd: '', bomnm: '', useflg: '1' })
const bomDialogTitle = computed(() => isEditingBom.value ? '编辑 BOM' : '新增 BOM')

const addDetailVisible = ref(false); const addingDetail = ref(false)
const detailForm = reactive({ itemcd: '', bomqty: 1, itemtyp: '0' })
const allItems = ref<ItemRecord[]>([]); const filteredItems = ref<ItemRecord[]>([])

function bomType(row: BomRecord): { type: string; label: string } {
    if (!row.details || row.details.length === 0) return { type: 'info', label: '主机+配件' }
    const hasCore = row.details.some((d) => d.itemtyp === '1')
    return hasCore ? { type: 'warning', label: '全配件' } : { type: 'info', label: '主机+配件' }
}

watch(page, () => loadBoms()); watch(perPage, () => { page.value = 1; loadBoms() })
onMounted(() => { loadTree(); loadBoms() })

async function loadBoms() {
    loading.value = true
    try {
        const params: Record<string, unknown> = { page: page.value, per_page: perPage.value }
        if (searchText.value) params.search = searchText.value
        if (selectedClassCd.value) params.class_cd = selectedClassCd.value
        const res = await fetchBoms(params as any)
        boms.value = res.data.items || []; total.value = res.data.total || 0
    } catch { ElMessage.error('加载 BOM 失败') }
    finally { loading.value = false }
}

function onSearch() { page.value = 1; loadBoms() }

async function onSelectBom(row: BomRecord) {
    selectedBom.value = row; detailLoading.value = true
    try {
        const res = await fetchBom(row.bomcd)
        details.value = res.data.details || []
    } catch { ElMessage.error('加载明细失败') }
    finally { detailLoading.value = false }
}

function openCreateBom() { bomForm.bomcd = ''; bomForm.bomnm = ''; bomForm.useflg = '1'; isEditingBom.value = false; bomDialogVisible.value = true }
function openEditBom(row: BomRecord) { bomForm.bomcd = row.bomcd; bomForm.bomnm = row.bomnm; bomForm.useflg = row.useflg; isEditingBom.value = true; bomDialogVisible.value = true }

async function handleSaveBom() {
    if (!bomForm.bomcd.trim() || !bomForm.bomnm.trim()) { ElMessage.warning('请填写 BOM 代码和名称'); return }
    saving.value = true
    try {
        if (isEditingBom.value) { await updateBom(bomForm.bomcd, { bomnm: bomForm.bomnm, useflg: bomForm.useflg }); ElMessage.success('更新成功') }
        else { await createBom({ bomcd: bomForm.bomcd.toUpperCase(), bomnm: bomForm.bomnm }); ElMessage.success('创建成功') }
        bomDialogVisible.value = false; loadBoms()
        if (selectedBom.value?.bomcd === bomForm.bomcd) await onSelectBom(selectedBom.value)
    } catch { ElMessage.error('保存失败') }
    finally { saving.value = false }
}

async function handleDeleteBom(row: BomRecord) {
    try {
        await ElMessageBox.confirm(`确定删除 BOM ${row.bomcd}？`, '确认', { type: 'warning' })
        await deleteBom(row.bomcd)
        if (selectedBom.value?.bomcd === row.bomcd) { selectedBom.value = null; details.value = [] }
        ElMessage.success('已删除'); loadBoms()
    } catch { /* cancelled */ }
}

async function openAddDetail() {
    addDetailVisible.value = true
    detailForm.itemcd = ''; detailForm.bomqty = 1; detailForm.itemtyp = '0'
    if (!allItems.value.length) {
        try { const r = await fetchItems({ per_page: 999 }); allItems.value = r.data.items || [] } catch { /**/ }
    }
    filteredItems.value = [...allItems.value]
}

function filterItems(v: string) { filteredItems.value = allItems.value.filter(i => i.item_cd.includes(v.toUpperCase()) || i.item_nm.includes(v)) }
function onItemSelectOpen(_visible: boolean) { if (_visible && !allItems.value.length) { fetchItems({ per_page: 999 }).then(r => { allItems.value = r.data.items || [] }).catch(() => {}) } }

async function handleAddDetail() {
    if (!detailForm.itemcd || !selectedBom.value) return
    addingDetail.value = true
    try {
        await addBomDetail(selectedBom.value.bomcd, { itemcd: detailForm.itemcd, bomqty: detailForm.bomqty, itemtyp: detailForm.itemtyp })
        addDetailVisible.value = false; onSelectBom(selectedBom.value)
    } catch { ElMessage.error('添加失败') }
    finally { addingDetail.value = false }
}

async function handleDeleteDetail(row: BomDetailRecord) {
    if (!selectedBom.value) return
    try {
        await ElMessageBox.confirm(`确定移除 ${row.itemcd}？`, '确认', { type: 'warning' })
        await deleteBomDetail(selectedBom.value.bomcd, row.itemcd)
        onSelectBom(selectedBom.value)
    } catch { /* cancelled */ }
}
</script>

<style lang="scss" scoped>
.bom-page { display: flex; gap: 12px; height: calc(100vh - 120px) }
.tree-panel { width: 220px; flex-shrink: 0; overflow: auto }
.content-panel { flex: 1; display: flex; flex-direction: column; gap: 12px; overflow: auto }
.detail-panel { flex-shrink: 0 }
.panel-header { display: flex; justify-content: space-between; align-items: center }
.empty-hint { text-align: center; color: #999; padding: 40px 0 }
</style>
