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

        <!-- 右侧：成品列表 + BOM 明细 -->
        <div class="content-panel">
            <div class="list-panel">
                <el-card shadow="never">
                    <template #header>
                        <div class="panel-header">
                            <span>成品列表（共 {{ total }} 个）</span>
                            <span style="font-size:12px;color:#999">仅显示 typflg=1 的整机物料</span>
                        </div>
                    </template>
                    <div style="display:flex;gap:8px;margin-bottom:12px">
                        <el-input v-model="searchText" placeholder="搜索成品编码或名称" clearable size="small" @keyup.enter="onSearch" @clear="onSearch" style="flex:1" />
                    </div>
                    <el-table :data="items" v-loading="loading" stripe highlight-current-row @row-click="onSelectItem" size="small">
                        <el-table-column prop="item_cd" label="成品编码" width="100" />
                        <el-table-column prop="item_nm" label="成品名称" min-width="160" show-overflow-tooltip />
                        <el-table-column prop="spec" label="规格" min-width="120" show-overflow-tooltip />
                        <el-table-column label="BOM" width="70" align="center">
                            <template #default="{ row }">
                                <span style="font-size:12px;color:#999">点击查看</span>
                            </template>
                        </el-table-column>
                    </el-table>
                    <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top: 12px; justify-content: flex-end" />
                </el-card>
            </div>

            <div class="detail-panel" v-if="selectedItem">
                <el-card shadow="never">
                    <template #header>
                        <div class="panel-header">
                            <span>{{ selectedItem.item_cd }} — {{ selectedItem.item_nm }} BOM 明细</span>
                            <template v-if="selectedBom">
                                <div style="display:flex;gap:8px">
                                    <el-tag :type="bomType.type" size="small">{{ bomType.label }}</el-tag>
                                    <el-button type="primary" size="small" @click="openAddDetail">添加物料</el-button>
                                    <el-button size="small" @click="openEditBom">编辑</el-button>
                                </div>
                            </template>
                            <el-button v-else type="primary" size="small" @click="openCreateBomForItem">新建 BOM</el-button>
                        </div>
                    </template>
                    <template v-if="selectedBom">
                        <el-table :data="details" v-loading="detailLoading" stripe size="small">
                            <el-table-column prop="itemcd" label="物料代码" width="100" />
                            <el-table-column prop="item_nm" label="物料名称" min-width="160" show-overflow-tooltip />
                            <el-table-column prop="bomqty" label="数量" width="60" align="center" />
                            <el-table-column label="类型" width="90" align="center">
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
                    </template>
                    <div v-else class="empty-hint">该成品暂无 BOM 配置</div>
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

        <!-- 添加物料弹窗 -->
        <el-dialog title="添加物料" v-model="addDetailVisible" width="420px">
            <el-form :model="detailForm" label-width="80px">
                <el-form-item label="选择物料">
                    <el-select v-model="detailForm.itemcd" filterable placeholder="搜索配件物料" style="width: 100%" :filter-method="filterAccessories" @visible-change="onDetailSelectOpen">
                        <el-option v-for="it in filteredAccessories" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="数量">
                    <el-input-number v-model="detailForm.bomqty" :min="1" style="width: 100%" />
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
    fetchBom, createBom, updateBom, deleteBom,
    addBomDetail, deleteBomDetail,
    fetchItems, fetchItemClassTree,
} from '@/api/master'
import type { BomRecord, BomDetailRecord, ItemRecord, ItemClassNode } from '@/api/master'

const treeData = ref<ItemClassNode[]>([]); const treeFilter = ref(''); const treeRef = ref()
const selectedClassCd = ref('')

function filterNode(value: string, data: { class_nm: string }): boolean {
    return !value || data.class_nm.toLowerCase().includes(value.toLowerCase())
}
watch(treeFilter, (v) => { (treeRef.value as any)?.filter(v) })
async function loadTree() { try { const r = await fetchItemClassTree(); treeData.value = r.data || [] } catch { /* */ } }

function onTreeNodeClick(node: ItemClassNode) {
    selectedClassCd.value = node.type === 'item' ? '' : node.class_cd
    page.value = 1; loadItems()
}

// 成品列表（仅 typflg=1）
const items = ref<ItemRecord[]>([]); const loading = ref(false)
const total = ref(0); const page = ref(1); const perPage = ref(20); const searchText = ref('')
const selectedItem = ref<ItemRecord | null>(null)
const selectedBom = ref<BomRecord | null>(null)
const details = ref<BomDetailRecord[]>([]); const detailLoading = ref(false)

const bomDialogVisible = ref(false); const isEditingBom = ref(false); const saving = ref(false)
const bomForm = reactive({ bomcd: '', bomnm: '', useflg: '1' })
const bomDialogTitle = computed(() => isEditingBom.value ? '编辑 BOM' : '新建 BOM')

const addDetailVisible = ref(false); const addingDetail = ref(false)
const detailForm = reactive({ itemcd: '', bomqty: 1, itemtyp: '0' })
const allAccessories = ref<ItemRecord[]>([]); const filteredAccessories = ref<ItemRecord[]>([])

const bomType = computed(() => {
    if (!selectedBom.value?.details || selectedBom.value.details.length === 0) return { type: 'info', label: '主机+配件' }
    return selectedBom.value.details.some(d => d.itemtyp === '1')
        ? { type: 'warning', label: '全配件' } : { type: 'info', label: '主机+配件' }
})

watch(page, () => loadItems()); watch(perPage, () => { page.value = 1; loadItems() })
onMounted(() => { loadTree(); loadItems() })

async function loadItems() {
    loading.value = true
    try {
        const params: Record<string, unknown> = { page: page.value, per_page: perPage.value, typflg: '1' }
        if (searchText.value) params.search = searchText.value
        if (selectedClassCd.value) params.class_cd = selectedClassCd.value
        const res = await fetchItems(params as any)
        items.value = (res.data as any).items || []
        total.value = (res.data as any).total || 0
    } catch { ElMessage.error('加载失败') }
    finally { loading.value = false }
}

function onSearch() { page.value = 1; loadItems() }

async function onSelectItem(row: ItemRecord) {
    selectedItem.value = row; detailLoading.value = true
    try {
        const res = await fetchBom(row.item_cd)
        selectedBom.value = res.data; details.value = res.data.details || []
    } catch {
        selectedBom.value = null; details.value = []
    }
    finally { detailLoading.value = false }
}

function openCreateBomForItem() {
    if (!selectedItem.value) return
    bomForm.bomcd = selectedItem.value.item_cd
    bomForm.bomnm = selectedItem.value.item_nm
    bomForm.useflg = '1'; isEditingBom.value = false; bomDialogVisible.value = true
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
    detailForm.itemcd = ''; detailForm.bomqty = 1; detailForm.itemtyp = '0'
    if (!allAccessories.value.length) {
        try {
            const r = await fetchItems({ per_page: 999, typflg: '0' } as any)
            allAccessories.value = (r.data as any).items || []
        } catch { /* */ }
    }
    filteredAccessories.value = [...allAccessories.value]
}

function filterAccessories(v: string) {
    filteredAccessories.value = allAccessories.value.filter(i => i.item_cd.includes(v.toUpperCase()) || i.item_nm.includes(v))
}
function onDetailSelectOpen(_v: boolean) {
    if (_v && !allAccessories.value.length) {
        fetchItems({ per_page: 999, typflg: '0' } as any).then(r => { allAccessories.value = (r.data as any).items || [] }).catch(() => {})
    }
}

async function handleAddDetail() {
    if (!detailForm.itemcd || !selectedBom.value) return
    addingDetail.value = true
    try {
        await addBomDetail(selectedBom.value.bomcd, { itemcd: detailForm.itemcd, bomqty: detailForm.bomqty, itemtyp: detailForm.itemtyp })
        addDetailVisible.value = false
        if (selectedItem.value) await onSelectItem(selectedItem.value)
    } catch { ElMessage.error('添加失败') }
    finally { addingDetail.value = false }
}

async function handleDeleteDetail(row: BomDetailRecord) {
    if (!selectedBom.value) return
    try {
        await ElMessageBox.confirm(`确定移除 ${row.itemcd}？`, '确认', { type: 'warning' })
        await deleteBomDetail(selectedBom.value.bomcd, row.itemcd)
        if (selectedItem.value) await onSelectItem(selectedItem.value)
    } catch { /* */ }
}
</script>

<style lang="scss" scoped>
.bom-page { display: flex; gap: 12px; height: calc(100vh - 120px) }
.tree-panel { width: 220px; flex-shrink: 0; overflow: auto }
.content-panel { flex: 1; display: flex; flex-direction: column; gap: 12px; overflow: auto }
.panel-header { display: flex; justify-content: space-between; align-items: center }
.empty-hint { text-align: center; color: #999; padding: 40px 0 }
</style>
