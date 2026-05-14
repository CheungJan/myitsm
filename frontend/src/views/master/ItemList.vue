<template>
    <div class="items-page">
        <!-- 左侧分类树 -->
        <div class="tree-panel">
            <el-card shadow="never">
                <template #header>
                    <div class="tree-header">
                        <span>物料分类</span>
                        <el-button type="primary" size="small" @click="openClassDialog()">新增</el-button>
                    </div>
                </template>
                <el-input v-model="treeFilterText" placeholder="输入关键字过滤" clearable size="small" style="margin-bottom:4px" />
                <div class="tree-actions">
                    <el-button link size="small" @click="expandAll">全部展开</el-button>
                    <el-button link size="small" @click="collapseAll">全部收缩</el-button>
                </div>
                <el-tree
                    ref="treeRef"
                    :data="treeData"
                    :props="{ label: 'class_nm', children: 'children' }"
                    node-key="class_cd"
                    highlight-current
                    :filter-node-method="filterTreeNode"
                    @node-click="onTreeClick"
                >
                    <template #default="{ data }">
                        <span class="tree-node">
                            <span class="tree-node-label">{{ data.class_nm }}</span>
                            <span class="tree-node-code">({{ data.class_cd }})</span>
                            <span class="tree-node-actions">
                                <el-button link size="small" @click.stop="openClassDialog(data)">编辑</el-button>
                                <el-button link size="small" type="danger" @click.stop="handleDeleteClass(data)">删除</el-button>
                            </span>
                        </span>
                    </template>
                </el-tree>
            </el-card>
        </div>

        <!-- 右侧物料表格 -->
        <div class="table-panel">
            <el-card>
                <template #header>
                    <div class="page-header">
                        <span>物料管理（共 {{ total }} 条）<template v-if="selectedClassCd"> — 分类: {{ selectedClassCd }}</template></span>
                        <div class="header-actions">
                            <el-input v-model="searchText" placeholder="搜索编码或名称" clearable size="small" style="width:200px" @keyup.enter="onSearch" @clear="onSearch" />
                            <el-button type="primary" size="small" style="margin-left:8px" @click="openItemDialog()">新增物料</el-button>
                        </div>
                    </div>
                </template>
                <el-table :data="items" v-loading="loading" stripe>
                    <el-table-column prop="item_cd" label="物料编码" width="120" />
                    <el-table-column prop="item_nm" label="物料名称" min-width="150" />
                    <el-table-column prop="class_cd" label="分类编码" width="100" />
                    <el-table-column prop="itemanm" label="别名" width="120" />
                    <el-table-column prop="unit" label="单位" width="80" />
                    <el-table-column label="库存上限" width="85">
                        <template #default="{ row }">{{ row.upperlimit ?? '-' }}</template>
                    </el-table-column>
                    <el-table-column label="库存下限" width="85">
                        <template #default="{ row }">{{ row.lowerlimit ?? '-' }}</template>
                    </el-table-column>
                    <el-table-column label="最小订购" width="85">
                        <template #default="{ row }">{{ row.minorder ?? '-' }}</template>
                    </el-table-column>
                    <el-table-column label="新品周期" width="85">
                        <template #default="{ row }">{{ row.newperiod ?? '-' }}</template>
                    </el-table-column>
                    <el-table-column label="旧品周期" width="85">
                        <template #default="{ row }">{{ row.oldperiod ?? '-' }}</template>
                    </el-table-column>
                    <el-table-column label="采购负责人" width="100">
                        <template #default="{ row }">{{ row.pcrep ?? '-' }}</template>
                    </el-table-column>
                    <el-table-column label="操作" width="120" fixed="right">
                        <template #default="{ row }">
                            <el-button type="primary" link size="small" @click="openItemDialog(row)">编辑</el-button>
                            <el-button type="danger" link size="small" @click="handleDeleteItem(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
            </el-card>
        </div>

        <!-- 物料新增/编辑弹窗 -->
        <el-dialog :title="itemEditing ? '编辑物料' : '新增物料'" v-model="itemDialogVisible" width="650px">
            <el-tabs v-model="itemActiveTab" type="border-card">
                <el-tab-pane label="基本信息" name="base">
                    <el-form :model="itemForm" label-width="80px">
                        <el-form-item label="编码" required><el-input v-model="itemForm.item_cd" :disabled="!!itemEditing" /></el-form-item>
                        <el-form-item label="名称" required><el-input v-model="itemForm.item_nm" /></el-form-item>
                        <el-form-item label="分类"><el-select v-model="itemForm.class_cd" clearable filterable style="width:100%"><el-option v-for="c in classOptions" :key="c.class_cd" :label="`${c.class_cd} - ${c.class_nm}`" :value="c.class_cd" /></el-select></el-form-item>
                        <el-form-item label="别名"><el-input v-model="itemForm.itemanm" /></el-form-item>
                        <el-form-item label="单位"><el-input v-model="itemForm.unit" /></el-form-item>
                        <el-form-item label="规格"><el-input v-model="itemForm.spec" /></el-form-item>
                        <el-form-item label="类型"><el-select v-model="itemForm.typflg" style="width:100%"><el-option label="成品/整机" value="1" /><el-option label="配件" value="0" /></el-select></el-form-item>
                    </el-form>
                </el-tab-pane>
                <el-tab-pane label="库存周期" name="stock">
                    <el-form :model="itemForm" label-width="100px">
                        <el-form-item label="库存上限"><el-input-number v-model="itemForm.upperlimit" :min="0" style="width:100%" /></el-form-item>
                        <el-form-item label="库存下限"><el-input-number v-model="itemForm.lowerlimit" :min="0" style="width:100%" /></el-form-item>
                        <el-form-item label="最小订购量"><el-input-number v-model="itemForm.minorder" :min="0" style="width:100%" /></el-form-item>
                        <el-form-item label="新品周期(天)"><el-input-number v-model="itemForm.newperiod" :min="0" style="width:100%" /></el-form-item>
                        <el-form-item label="旧品周期(天)"><el-input-number v-model="itemForm.oldperiod" :min="0" style="width:100%" /></el-form-item>
                        <el-form-item label="采购负责人"><el-input v-model="itemForm.pcrep" /></el-form-item>
                    </el-form>
                </el-tab-pane>
                <el-tab-pane label="供应商" name="supplier" v-if="itemEditing">
                    <div style="margin-bottom:8px"><el-button type="primary" size="small" @click="openAddSupplier">添加供应商</el-button></div>
                    <el-table :data="itemSuppliers" size="small" stripe>
                        <el-table-column prop="custcd" label="供应商编码" width="100" />
                        <el-table-column prop="supp_nm" label="供应商名称" min-width="140" show-overflow-tooltip />
                        <el-table-column label="默认" width="70"><template #default="{row}">
                            <el-switch :model-value="row.dfltflg==='Y'" size="small" @change="(v:boolean) => handleSetDefaultSupplier(row, v)" />
                        </template></el-table-column>
                        <el-table-column label="保修期(天)" width="110"><template #default="{row}">
                            <el-input-number v-model="row.guaranteeperiod" :min="0" size="small" controls-position="right" style="width:90px" @change="(v:number|undefined) => handleUpdateSupplier(row, 'guaranteeperiod', v)" />
                        </template></el-table-column>
                        <el-table-column label="配送周期" width="100"><template #default="{row}">
                            <el-input-number v-model="row.delivercycle" :min="0" size="small" controls-position="right" style="width:80px" @change="(v:number|undefined) => handleUpdateSupplier(row, 'delivercycle', v)" />
                        </template></el-table-column>
                        <el-table-column label="服务周期" width="100"><template #default="{row}">
                            <el-input-number v-model="row.servicecycle" :min="0" size="small" controls-position="right" style="width:80px" @change="(v:number|undefined) => handleUpdateSupplier(row, 'servicecycle', v)" />
                        </template></el-table-column>
                        <el-table-column label="操作" width="70"><template #default="{row}"><el-button link type="danger" size="small" @click="handleRemoveSupplier(row)">移除</el-button></template></el-table-column>
                    </el-table>
                </el-tab-pane>
                <el-tab-pane label="商品价格" name="price" v-if="itemEditing">
                    <el-table :data="itemPrices" size="small" stripe>
                        <el-table-column prop="busityp" label="业务类型" width="90" />
                        <el-table-column prop="itemprice" label="单价" width="100" />
                        <el-table-column prop="unitcd" label="单位" width="70" />
                        <el-table-column label="当前有效" width="80"><template #default="{row}"><el-tag :type="row.is_current?'success':'info'" size="small">{{ row.is_current?'有效':'失效' }}</el-tag></template></el-table-column>
                        <el-table-column prop="effective_date" label="生效日期" width="110" />
                        <el-table-column prop="expire_date" label="失效日期" width="110" />
                    </el-table>
                </el-tab-pane>
                <el-tab-pane label="相关BOM" name="bom" v-if="itemEditing">
                    <el-table :data="itemBoms" size="small" stripe>
                        <el-table-column prop="bomcd" label="BOM编码" width="90" />
                        <el-table-column prop="bomnm" label="BOM名称" min-width="150" show-overflow-tooltip />
                        <el-table-column label="类型" width="80"><template #default="{row}">{{ row.details?.some((d:any)=>d.itemtyp==='1')?'全配件':'主机+配件' }}</template></el-table-column>
                        <el-table-column label="有效" width="60"><template #default="{row}"><el-tag :type="row.useflg==='0'?'danger':'success'" size="small">{{ row.useflg==='0'?'无效':'有效' }}</el-tag></template></el-table-column>
                    </el-table>
                </el-tab-pane>
            </el-tabs>
            <template #footer>
                <el-button @click="itemDialogVisible = false">取消</el-button>
                <el-button v-if="!!itemEditing" type="danger" @click="handleDeleteItem(itemEditing)">删除</el-button>
                <el-button type="primary" @click="handleSaveItem" :loading="itemSaving">保存</el-button>
            </template>
        </el-dialog>

        <!-- 分类新增/编辑弹窗 -->
        <el-dialog :title="classEditing ? '编辑分类' : '新增分类'" v-model="classDialogVisible" width="500px">
            <el-form :model="classForm" label-width="80px">
                <el-form-item label="编码" required>
                    <el-input v-model="classForm.class_cd" :disabled="!!classEditing" />
                </el-form-item>
                <el-form-item label="名称" required>
                    <el-input v-model="classForm.class_nm" />
                </el-form-item>
                <el-form-item label="上级分类">
                    <el-select v-model="classForm.parent_cd" clearable filterable style="width:100%" placeholder="空 = 根分类">
                        <el-option v-for="c in classOptions" :key="c.class_cd" :label="`${c.class_cd} - ${c.class_nm}`" :value="c.class_cd" />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="classDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSaveClass" :loading="classSaving">保存</el-button>
            </template>
        </el-dialog>

        <!-- 添加供应商弹窗 -->
        <el-dialog title="选择供应商" v-model="supplierDialogVisible" width="480px">
            <el-select v-model="selectedSuppCd" filterable placeholder="搜索供应商" style="width:100%">
                <el-option v-for="s in allSuppliers" :key="s.supp_cd" :label="`${s.supp_cd} ${s.supp_nm}`" :value="s.supp_cd" />
            </el-select>
            <template #footer>
                <el-button @click="supplierDialogVisible = false">取消</el-button>
                <el-button type="primary" :disabled="!selectedSuppCd" @click="handleAddSupplier">添加</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { watch } from 'vue'
import type { ElTree } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
    fetchItems, createItem, updateItem, deleteItem,
    fetchItemClassTree, fetchItemClasses,
    createItemClass, updateItemClass, deleteItemClass,
} from '@/api/master'
import type { ItemClassNode, ItemRecord, ItemsPage } from '@/api/master'

// ---- 分类树 ----
const treeData = ref<ItemClassNode[]>([])
const treeFilterText = ref('')
const treeRef = ref<InstanceType<typeof ElTree>>()
const selectedClassCd = ref('')
const classOptions = ref<{ class_cd: string; class_nm: string; parent_cd: string }[]>([])

// ---- 物料列表 ----
const items = ref<ItemRecord[]>([])
const loading = ref(false)
const searchText = ref('')
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

// ---- 物料弹窗 ----
const itemDialogVisible = ref(false); const itemActiveTab = ref('base')
const itemSuppliers = ref<Record<string,unknown>[]>([]); const itemBoms = ref<Record<string,unknown>[]>([]); const itemPrices = ref<Record<string,unknown>[]>([])
const supplierDialogVisible = ref(false); const selectedSuppCd = ref('')
const allSuppliers = ref<{supp_cd:string;supp_nm:string}[]>([])
const itemEditing = ref<ItemRecord | null>(null)
const itemSaving = ref(false)
const itemForm = reactive<Record<string, unknown>>({ item_cd: '', item_nm: '', class_cd: '', itemanm: '', unit: '', spec: '', typflg: '0', upperlimit: undefined, lowerlimit: undefined, minorder: undefined, newperiod: undefined, oldperiod: undefined, pcrep: '' })

// ---- 分类弹窗 ----
const classDialogVisible = ref(false)
const classEditing = ref<ItemClassNode | null>(null)
const classSaving = ref(false)
const classForm = reactive({ class_cd: '', class_nm: '', parent_cd: '' })

watch(page, () => loadItems())
watch(perPage, () => { page.value = 1; loadItems() })
watch(treeFilterText, (v) => treeRef.value?.filter(v))

onMounted(async () => {
    await Promise.all([loadTree(), loadClassOptions()])
    loadItems()
})

// ---- 分类树 ----

async function loadTree() {
    try {
        const res = await fetchItemClassTree()
        treeData.value = res.data || []
    } catch {
        ElMessage.error('加载分类树失败')
    }
}

async function loadClassOptions() {
    try {
        const res = await fetchItemClasses()
        classOptions.value = (res.data || []) as { class_cd: string; class_nm: string; parent_cd: string }[]
    } catch { /* 非关键 */ }
}

function filterTreeNode(value: string, data: ItemClassNode): boolean {
    if (!value) return true
    const kw = value.toLowerCase()
    return data.class_nm.toLowerCase().includes(kw) || data.class_cd.toLowerCase().includes(kw)
}

function expandAll() {
    const nodes = (treeRef.value as unknown as { store: { nodesMap: Record<string, { expand: () => void }> } })?.store?.nodesMap
    if (nodes) Object.values(nodes).forEach((n) => n.expand?.())
}

function collapseAll() {
    const nodes = (treeRef.value as unknown as { store: { nodesMap: Record<string, { collapse: () => void }> } })?.store?.nodesMap
    if (nodes) Object.values(nodes).forEach((n) => n.collapse?.())
}

function onTreeClick(node: ItemClassNode) {
    // 点击具体物料 → 直接打开编辑弹窗
    if (node.type === 'item') {
        openItemDialog({ item_cd: node.class_cd, item_nm: node.class_nm } as ItemRecord)
        return
    }
    selectedClassCd.value = node.class_cd
    searchText.value = ''
    page.value = 1
    loadItems()
}

// ---- 分类 CRUD ----

function openClassDialog(data?: ItemClassNode) {
    if (data) {
        classEditing.value = data
        classForm.class_cd = data.class_cd || ''
        classForm.class_nm = data.class_nm || ''
        classForm.parent_cd = (data as unknown as Record<string,string>).parent_cd || ''
    } else {
        classEditing.value = null
        // 新增子分类时自动继承当前选中节点的编码作为前缀
        classForm.class_cd = selectedClassCd.value || ''
        classForm.class_nm = ''
        classForm.parent_cd = selectedClassCd.value || ''
    }
    classDialogVisible.value = true
}

async function handleSaveClass() {
    if (!classForm.class_cd || !classForm.class_nm) {
        ElMessage.warning('编码和名称为必填项')
        return
    }
    classSaving.value = true
    try {
        const payload: Record<string, string> = { class_nm: classForm.class_nm, useflg: classForm.useflg }
        if (classForm.parent_cd) payload.parent_cd = classForm.parent_cd
        if (classEditing.value) {
            await updateItemClass(classEditing.value.class_cd, payload)
            ElMessage.success('更新成功')
        } else {
            payload.class_cd = classForm.class_cd
            await createItemClass(payload)
            ElMessage.success('创建成功')
        }
        classDialogVisible.value = false
        await Promise.all([loadTree(), loadClassOptions()])
    } finally { classSaving.value = false }
}

async function handleDeleteClass(data: ItemClassNode) {
    try {
        await ElMessageBox.confirm(`确定删除分类 ${data.class_cd}（${data.class_nm}）？子分类和物料可能受影响。`, '确认删除')
        await deleteItemClass(data.class_cd)
        ElMessage.success('已删除')
        if (selectedClassCd.value === data.class_cd) selectedClassCd.value = ''
        await Promise.all([loadTree(), loadClassOptions()])
        loadItems()
    } catch (e: unknown) {
        if (e !== 'cancel') {
            ElMessage.error('删除失败')
        }
    }
}

// ---- 物料列表 ----

async function loadItems() {
    loading.value = true
    try {
        const params: { page: string; per_page: string; class_cd?: string; recursive?: string; search?: string } = {
            page: String(page.value),
            per_page: String(perPage.value),
        }
        // 搜索优先：有搜索词时全局搜索，忽略分类筛选
        if (searchText.value) {
            params.search = searchText.value
        } else if (selectedClassCd.value) {
            params.class_cd = selectedClassCd.value
            params.recursive = '1'
        }
        const res = await fetchItems(params)
        const data = res.data as ItemsPage
        items.value = data.items || []
        total.value = data.total || 0
    } catch {
        ElMessage.error('加载物料列表失败')
    } finally { loading.value = false }
}

function onSearch() {
    page.value = 1
    loadItems()
}

// ---- 物料 CRUD ----

async function openAddSupplier() {
    supplierDialogVisible.value = true; selectedSuppCd.value = ''
    if (!allSuppliers.value.length) {
        try { const { fetchSuppliers } = await import('@/api/master'); const r = await fetchSuppliers(); allSuppliers.value = r.data || [] } catch { /**/ }
    }
}
async function handleAddSupplier() {
    if (!selectedSuppCd.value || !itemEditing.value) return
    try {
        const { addItemSupplier } = await import('@/api/master')
        await addItemSupplier(itemEditing.value.item_cd, { custcd: selectedSuppCd.value, dfltflg: itemSuppliers.value.length === 0 ? 'Y' : 'N' })
        supplierDialogVisible.value = false
        const { fetchItemSuppliers } = await import('@/api/master')
        const r = await fetchItemSuppliers(itemEditing.value.item_cd)
        itemSuppliers.value = r.data || []
    } catch { ElMessage.error('添加失败') }
}
async function handleUpdateSupplier(row: Record<string,unknown>, field: string, val: unknown) {
    if (!itemEditing.value) return
    try { const { updateItemSupplier } = await import('@/api/master'); await updateItemSupplier(itemEditing.value.item_cd, row.custcd as string, { [field]: val }) } catch { ElMessage.error('更新失败') }
}
async function handleSetDefaultSupplier(row: Record<string,unknown>, val: boolean) {
    if (!itemEditing.value || !val) return
    try { const { updateItemSupplier } = await import('@/api/master'); await updateItemSupplier(itemEditing.value.item_cd, row.custcd as string, { dfltflg: 'Y' }) } catch { ElMessage.error('设置失败') }
    // 刷新列表
    const { fetchItemSuppliers } = await import('@/api/master'); const r = await fetchItemSuppliers(itemEditing.value.item_cd); itemSuppliers.value = r.data || []
}
async function handleRemoveSupplier(row: Record<string,unknown>) {
    if (!itemEditing.value) return
    try { await ElMessageBox.confirm(`确定移除供应商 ${row.supp_nm}？`, '确认', { type: 'warning' }) } catch { return }
    try {
        const { deleteItemSupplier } = await import('@/api/master')
        await deleteItemSupplier(itemEditing.value.item_cd, row.custcd as string)
        const { fetchItemSuppliers } = await import('@/api/master')
        const r = await fetchItemSuppliers(itemEditing.value.item_cd)
        itemSuppliers.value = r.data || []
    } catch { ElMessage.error('移除失败') }
}

async function openItemDialog(row?: ItemRecord) {
    if (row) {
        // 从树节点点击时只有 item_cd/item_nm，需补全字段
        if (!row.class_cd) {
            try {
                const params: Record<string,unknown> = { per_page: 1, search: row.item_cd }
                const r = await fetchItems(params as any)
                const full = (r.data as ItemsPage).items?.find((i: ItemRecord) => i.item_cd === row.item_cd)
                if (full) row = full
            } catch { /* fallback to partial */ }
        }
        itemEditing.value = row
        itemForm.item_cd = row.item_cd || ''
        itemForm.item_nm = row.item_nm || ''
        itemForm.class_cd = row.class_cd || ''
        itemForm.itemanm = row.itemanm || ''
        itemForm.unit = row.unit || ''
        itemForm.upperlimit = (row as Record<string,unknown>).upperlimit
        itemForm.lowerlimit = (row as Record<string,unknown>).lowerlimit
        itemForm.minorder = (row as Record<string,unknown>).minorder
        itemForm.newperiod = (row as Record<string,unknown>).newperiod
        itemForm.oldperiod = (row as Record<string,unknown>).oldperiod
        itemForm.spec = (row as Record<string,unknown>).spec || ''
        itemForm.typflg = (row as Record<string,unknown>).typflg || '0'
        itemForm.pcrep = (row as Record<string,unknown>).pcrep || ''
        itemActiveTab.value = 'base'
        import('@/api/master').then(m => {
            m.fetchItemSuppliers(row!.item_cd).then(r => itemSuppliers.value = r.data || []).catch(() => itemSuppliers.value = [])
            m.fetchBom(row!.item_cd).then(r => itemBoms.value = r.data ? [r.data] : []).catch(() => itemBoms.value = [])
            m.fetchItemPrices(row!.item_cd).then(r => itemPrices.value = r.data || []).catch(() => itemPrices.value = [])
        })
    } else {
        itemEditing.value = null
        itemActiveTab.value = 'base'
        itemSuppliers.value = []
        itemBoms.value = []
        // 新增时自动继承左侧选中分类
        itemForm.item_cd = selectedClassCd.value || ''
        itemForm.item_nm = ''
        itemForm.class_cd = selectedClassCd.value || ''
        itemForm.itemanm = ''
        itemForm.unit = ''
        itemForm.upperlimit = undefined
        itemForm.lowerlimit = undefined
        itemForm.minorder = undefined
        itemForm.newperiod = undefined
        itemForm.oldperiod = undefined
        itemForm.pcrep = ''
        itemForm.unit = ''
    }
    itemDialogVisible.value = true
}

async function handleSaveItem() {
    if (!itemForm.item_cd || !itemForm.item_nm) {
        ElMessage.warning('编码和名称为必填项')
        return
    }
    itemSaving.value = true
    try {
        const payload = { ...itemForm, useflg: '1' }
        if (itemEditing.value) {
            await updateItem(itemEditing.value.item_cd, payload)
            ElMessage.success('更新成功')
        } else {
            await createItem(payload)
            ElMessage.success('创建成功')
        }
        itemDialogVisible.value = false
        loadItems()
    } finally { itemSaving.value = false }
}

async function handleDeleteItem(row: ItemRecord) {
    try {
        await ElMessageBox.confirm(`确定删除物料 ${row.item_cd}？`, '确认删除')
        await deleteItem(row.item_cd)
        ElMessage.success('已删除')
        itemDialogVisible.value = false; itemEditing.value = null
        loadItems()
    } catch (e: unknown) {
        if (e !== 'cancel') ElMessage.error('删除失败')
    }
}
</script>

<style lang="scss" scoped>
.items-page {
    display: flex; gap: 12px; padding: 16px; height: calc(100vh - 80px);
}
.tree-panel {
    width: 280px; flex-shrink: 0; overflow-y: auto;
    :deep(.el-card__body) { padding: 8px; }
    :deep(.el-tree-node__content) { height: auto; min-height: 28px; padding-right: 4px; }
}
.tree-header {
    display: flex; justify-content: space-between; align-items: center;
}
.tree-actions {
    display: flex; gap: 4px; margin-bottom: 4px;
}
.tree-node {
    display: flex; align-items: center; flex: 1; min-width: 0; font-size: 13px; overflow: hidden;
    .tree-node-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 1; }
    .tree-node-code { color: #909399; font-size: 11px; flex-shrink: 0; margin-left: 2px; }
    .tree-node-actions {
        display: none; flex-shrink: 0; margin-left: 2px;
        .el-button { padding: 0 2px; font-size: 12px; height: auto; min-height: auto; }
    }
    &:hover .tree-node-actions { display: flex; }
}
.table-panel { flex: 1; overflow-y: auto; min-width: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.header-actions { display: flex; align-items: center; }
</style>
