<template>
    <div class="asset-page">
        <div class="tree-panel">
            <el-card shadow="never">
                <template #header><span>客户分类</span></template>
                <div style="margin-bottom:4px">
                    <el-button link size="small" @click="clearTreeFilter">全部设备</el-button>
                </div>
                <el-input v-model="treeFilter" placeholder="过滤" clearable size="small" style="margin-bottom:4px" />
                <el-tree ref="treeRef" :data="treeData" :props="{label:'class_nm',children:'children'}"
                    node-key="class_cd" highlight-current :filter-node-method="filterTree"
                    @node-click="onTreeClick" />
            </el-card>
        </div>
        <div class="table-panel">
            <el-card>
                <template #header>
                    <div class="page-header-title">
                        <span>资产台账（共 {{ total }} 条）<template v-if="selectedClass"> — {{ selectedClass }}</template></span>
                    </div>
                    <div class="header-actions">
                        <el-input v-model="searchText" placeholder="SN/客户/磁卡号" clearable size="small" style="width:170px" @keyup.enter="onSearch" @clear="onSearch" />
                        <el-select v-model="filterWhcd" placeholder="仓库" clearable filterable multiple collapse-tags collapse-tags-tooltip size="small" style="width:160px;margin-left:8px" @change="onFilterChange">
                            <el-option-group label="有效仓库">
                                <el-option v-for="w in whOptions.filter((w:Record<string,string>) => w.useflg !== '0')" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd" />
                            </el-option-group>
                            <el-option-group label="无效仓库">
                                <el-option v-for="w in whOptions.filter((w:Record<string,string>) => w.useflg === '0')" :key="w.whcd" :label="`${w.whcd} ${w.whnm} (无效)`" :value="w.whcd" />
                            </el-option-group>
                        </el-select>
                        <el-select v-model="filterLocation" placeholder="设备位置" clearable size="small" style="width:95px;margin-left:8px" @change="onFilterChange">
                            <el-option label="客户设备" value="customer" />
                            <el-option label="仓库库存" value="warehouse" />
                        </el-select>
                        <el-select v-model="filterAssetType" placeholder="资产类型" clearable size="small" style="width:100px;margin-left:8px" @change="onFilterChange">
                            <el-option v-for="t in assetTypes" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" />
                        </el-select>
                        <el-select v-model="filterAssetOwner" placeholder="所属方" clearable size="small" style="width:100px;margin-left:8px" @change="onFilterChange">
                            <el-option v-for="t in assetOwners" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" />
                        </el-select>
                        <el-select v-model="filterUseflg" placeholder="有效性" clearable size="small" style="width:90px;margin-left:8px" @change="onFilterChange">
                            <el-option label="有效" value="1" />
                            <el-option label="无效" value="0" />
                        </el-select>
                    </div>
                </template>
                <el-table :data="assets" v-loading="loading" stripe>
                    <el-table-column prop="eid" label="设备 SN" width="150" />
                    <el-table-column label="商品名" min-width="130">
                        <template #default="{ row }">{{ row.item_nm || row.item_cd }}</template>
                    </el-table-column>
                    <el-table-column label="客户名" min-width="130">
                        <template #default="{ row }">{{ row.cust_nm || row.cust_cd }}</template>
                    </el-table-column>
                    <el-table-column label="管理单位" width="130">
                        <template #default="{ row }">{{ (row as Record<string,unknown>).parentcd_nm || '-' }}</template>
                    </el-table-column>
                    <el-table-column label="资产类型" width="80">
                        <template #default="{ row }">{{ codeMaps.AT?.[row.asset_type as string] || row.asset_type || '-' }}</template>
                    </el-table-column>
                    <el-table-column label="所属方" width="85">
                        <template #default="{ row }">{{ codeMaps.OW?.[row.asset_owner as string] || row.asset_owner || '-' }}</template>
                    </el-table-column>
                    <el-table-column label="有效" width="60">
                        <template #default="{ row }">
                            <el-tag :type="row.useflg === '0' ? 'danger' : 'success'" size="small">{{ row.useflg === '0' ? '无效' : '有效' }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="设备状态" width="80">
                        <template #default="{ row }">{{ codeMaps.AS?.[(row as Record<string,unknown>).asset_status as string] || (row as Record<string,unknown>).asset_status || '-' }}</template>
                    </el-table-column>
                    <el-table-column prop="prddate" label="生产日期" width="100" />
                    <el-table-column label="操作" width="120" fixed="right">
                        <template #default="{ row }">
                            <el-button type="info" link size="small" @click="openDetail(row)">详情</el-button>
                            <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
            </el-card>
        </div>

        <el-dialog title="资产详情" v-model="detailVisible" width="700px">
            <template v-if="detailRow">
                <el-divider content-position="left">基础信息</el-divider>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="设备SN">{{ detailRow.eid }}</el-descriptions-item>
                    <el-descriptions-item label="商品名">{{ detailRow.item_nm || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="客户名">{{ detailRow.cust_nm || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="管理单位">{{ (detailRow as Record<string,unknown>).parentcd_nm || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="磁卡号">{{ (detailRow as Record<string,unknown>).cust_card || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">资产属性</el-divider>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="资产类型">{{ codeMaps.AT?.[detailRow.asset_type as string] || detailRow.asset_type || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="回收状态">{{ codeMaps.RS?.[detailRow.recycle_status as string] || detailRow.recycle_status || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="所属方">{{ codeMaps.OW?.[detailRow.asset_owner as string] || detailRow.asset_owner || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="安装日期">{{ detailRow.install_date || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="设备状态">{{ codeMaps.AS?.[(detailRow as Record<string,unknown>).asset_status as string] || (detailRow as Record<string,unknown>).asset_status || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="仓库">{{ (detailRow as Record<string,unknown>).wh_nm || (detailRow as Record<string,unknown>).whcd || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">序列号信息</el-divider>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="质检">{{ codeMaps.QS?.[detailRow.qcflg as string] || detailRow.qcflg || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="设备状态">{{ codeMaps.ES?.[detailRow.sflg as string] || detailRow.sflg || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="设备类型">{{ codeMaps.ET?.[detailRow.etyp as string] || detailRow.etyp || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="新旧">{{ codeMaps.NO?.[detailRow.new_old as string] || detailRow.new_old || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="关联单号">{{ detailRow.refid || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="生产日期">{{ detailRow.prddate || '-' }}</el-descriptions-item>
                </el-descriptions>
            </template>
            <template #footer><el-button @click="detailVisible = false">关闭</el-button></template>
        </el-dialog>

        <el-dialog title="编辑资产属性" v-model="editVisible" width="500px">
            <el-form :model="editForm" label-width="90px">
                <el-form-item label="资产类型"><el-select v-model="editForm.asset_type" style="width:100%"><el-option v-for="t in assetTypes" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item>
                <el-form-item label="回收状态"><el-select v-model="editForm.recycle_status" clearable style="width:100%"><el-option v-for="t in recycleStatuses" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item>
                <el-form-item label="资产所属方"><el-select v-model="editForm.asset_owner" style="width:100%" :disabled="!isAdmin"><el-option v-for="t in assetOwners" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item>
                <el-form-item label="安装日期"><el-input v-model="editForm.install_date" /></el-form-item>
                <el-form-item label="可回收"><el-switch v-model="editForm.recyclable" /></el-form-item>
            </el-form>
            <template #footer><el-button @click="editVisible = false">取消</el-button><el-button type="primary" @click="handleSave" :loading="saving">保存</el-button></template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, watch } from 'vue'
import type { ElTree } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { fetchAssets, fetchCustClassTree, fetchSyscodes, fetchWarehouses } from '@/api/master'
import type { ItemClassNode } from '@/api/master'

const authStore = useAuthStore()
const isAdmin = authStore.userCode === 'admin'

const treeData = ref<ItemClassNode[]>([])
const treeFilter = ref(''); const treeRef = ref<InstanceType<typeof ElTree>>()
const selectedClassCd = ref(''); const selectedClass = ref('')

const assets = ref<Record<string,unknown>[]>([])
const loading = ref(false); const searchText = ref(''); const page = ref(1); const perPage = ref(20); const total = ref(0)
const filterAssetType = ref(''); const filterAssetOwner = ref(''); const filterUseflg = ref(''); const filterLocation = ref('')
const filterWhcd = ref<string[]>([])

const assetTypes = ref<{code_cd:string;code_nm:string}[]>([])
const whOptions = ref<{whcd:string;whnm:string}[]>([])
const recycleStatuses = ref<{code_cd:string;code_nm:string}[]>([])
const assetOwners = ref<{code_cd:string;code_nm:string}[]>([])
const codeMaps = ref<Record<string,Record<string,string>>>({})

const detailVisible = ref(false); const detailRow = ref<Record<string,unknown>|null>(null)
const editVisible = ref(false); const editRow = ref<Record<string,unknown>|null>(null)
const saving = ref(false)
const editForm = reactive({ asset_type:'', recycle_status:'', asset_owner:'', install_date:'', recyclable:false })

watch(page, () => loadData())
watch(perPage, () => { page.value = 1; loadData() })
watch(treeFilter, (v) => treeRef.value?.filter(v))

onMounted(async () => {
    const [tree, at, rs, ow, es, qs, et, no, asCode, iuCode] = await Promise.all([
        fetchCustClassTree(), fetchSyscodes('AT'), fetchSyscodes('RS'), fetchSyscodes('OW'),
        fetchSyscodes('ES'), fetchSyscodes('QS'), fetchSyscodes('ET'), fetchSyscodes('NO'), fetchSyscodes('AS'),
        fetchSyscodes('IU'),
    ])
    treeData.value = tree.data || []
    assetTypes.value = at.data || []; recycleStatuses.value = rs.data || []; assetOwners.value = ow.data || []
    codeMaps.value = {
        AT: Object.fromEntries(assetTypes.value.map(t => [t.code_cd, t.code_nm])),
        RS: Object.fromEntries(recycleStatuses.value.map(t => [t.code_cd, t.code_nm])),
        OW: Object.fromEntries(assetOwners.value.map(t => [t.code_cd, t.code_nm])),
        ES: Object.fromEntries((es.data||[]).map(t => [t.code_cd, t.code_nm])),
        QS: Object.fromEntries((qs.data||[]).map(t => [t.code_cd, t.code_nm])),
        ET: Object.fromEntries((et.data||[]).map(t => [t.code_cd, t.code_nm])),
        NO: Object.fromEntries((no.data||[]).map(t => [t.code_cd, t.code_nm])),
        AS: Object.fromEntries((asCode.data||[]).map(t => [t.code_cd, t.code_nm])),
        IU: Object.fromEntries((iuCode.data||[]).map(t => [t.code_cd, t.code_nm])),
    }
    const wh = await fetchWarehouses()
    whOptions.value = wh.data || []
    loadData()
})

function filterTree(v: string, d: ItemClassNode) { return !v || d.class_nm.includes(v) }
function onTreeClick(n: ItemClassNode) { selectedClassCd.value = n.class_cd; selectedClass.value = `(${n.class_cd})`; searchText.value = ''; page.value = 1; loadData() }
function clearTreeFilter() { selectedClassCd.value = ''; selectedClass.value = ''; treeRef.value?.setCurrentKey(null); page.value = 1; loadData() }

async function loadData() {
    loading.value = true
    try {
        const params: Record<string,string> = { page: String(page.value), per_page: String(perPage.value) }
        if (searchText.value) params.search = searchText.value
        else if (selectedClassCd.value) params.class_cd = selectedClassCd.value
        if (filterAssetType.value) params.asset_type = filterAssetType.value
        if (filterAssetOwner.value) params.asset_owner = filterAssetOwner.value
        if (filterUseflg.value) params.useflg = filterUseflg.value
        if (filterLocation.value) params.location = filterLocation.value
        if (filterWhcd.value.length > 0) params.whcd = filterWhcd.value.join(',')
        const res = await fetchAssets(params)
        const d = res.data as { items: Record<string,unknown>[]; total: number }
        assets.value = d.items || []; total.value = d.total || 0
    } catch { ElMessage.error('加载失败') }
    finally { loading.value = false }
}

function onSearch() { page.value = 1; loadData() }
function onFilterChange() { page.value = 1; loadData() }

function openDetail(row: Record<string,unknown>) { detailRow.value = row; detailVisible.value = true }
function openEdit(row: Record<string,unknown>) {
    editRow.value = row
    editForm.asset_type = (row.asset_type as string) || ''
    editForm.recycle_status = (row.recycle_status as string) || ''
    editForm.asset_owner = (row.asset_owner as string) || ''
    editForm.install_date = (row.install_date as string) || ''
    editForm.recyclable = !!(row as Record<string,unknown>).recyclable
    editVisible.value = true
}

async function handleSave() {
    saving.value = true
    try {
        const token = localStorage.getItem('token')
        const resp = await fetch(`/api/v1/assets/${editRow.value?.id}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify(editForm),
        })
        if (!resp.ok) { const err = await resp.json(); throw new Error(err.message) }
        ElMessage.success('保存成功')
        editVisible.value = false
        loadData()
    } catch { ElMessage.error('保存失败') }
    finally { saving.value = false }
}
</script>

<style lang="scss" scoped>
.asset-page { display: flex; gap: 12px; padding: 16px; height: calc(100vh - 80px); }
.tree-panel { width: 220px; flex-shrink: 0; overflow-y: auto; :deep(.el-card__body) { padding: 8px; } }
.table-panel { flex: 1; overflow-y: auto; min-width: 0; }
.page-header-title { font-size: 14px; font-weight: 500; margin-bottom: 8px; }
.header-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
</style>
