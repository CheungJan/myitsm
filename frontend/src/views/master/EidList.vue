<template>
    <div class="eid-page">
        <div class="tree-panel">
            <el-card shadow="never">
                <template #header>
                    <div class="tree-header">
                        <span>设备分类</span>
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
                            <span v-if="data.eid_count" class="tree-node-count">{{ data.eid_count }}</span>
                        </span>
                    </template>
                </el-tree>
            </el-card>
        </div>

        <div class="table-panel">
            <el-card>
                <template #header>
                    <div class="page-header">
                        <span>EID 设备管理（共 {{ total }} 条）<template v-if="selectedClassCd"> — 分类: {{ selectedClassCd }}</template></span>
                        <div class="header-actions">
                            <el-input v-model="searchText" placeholder="搜索 SN 或物料编码" clearable size="small" style="width:220px" @keyup.enter="onSearch" @clear="onSearch" />
                            <el-button type="primary" size="small" style="margin-left:8px" @click="openDialog()">新增设备</el-button>
                        </div>
                    </div>
                </template>
                <el-table :data="eids" v-loading="loading" stripe>
                    <el-table-column prop="eid" label="设备 SN" min-width="150" />
                    <el-table-column prop="item_nm" label="商品名" min-width="160" />
                    <el-table-column prop="itemcd" label="物料编码" width="100" />
                    <el-table-column prop="etyp" label="类型" width="70">
                        <template #default="{ row }">{{ codeMaps.ET?.[row.etyp] || row.etyp }}</template>
                    </el-table-column>
                    <el-table-column prop="sflg" label="状态" width="80">
                        <template #default="{ row }">{{ codeMaps.ES?.[row.sflg] || row.sflg }}</template>
                    </el-table-column>
                    <el-table-column prop="qcflg" label="质检" width="80">
                        <template #default="{ row }">{{ codeMaps.QS?.[row.qcflg] || row.qcflg }}</template>
                    </el-table-column>
                    <el-table-column label="仓库" width="100">
                        <template #default="{ row }">{{ (row as Record<string,unknown>).wh_nm || row.whcd || '-' }}</template>
                    </el-table-column>
                    <el-table-column prop="manuf_seq" label="制造序列号" width="130" />
                    <el-table-column prop="refid" label="关联单号" width="100" />
                    <el-table-column label="新旧" width="70">
                        <template #default="{ row }">{{ codeMaps.NO?.[row.new_old] || row.new_old }}</template>
                    </el-table-column>
                    <el-table-column prop="prddate" label="生产日期" width="110" />
                    <el-table-column label="操作" width="180" fixed="right">
                        <template #default="{ row }">
                            <el-button type="info" link size="small" @click="openHistory(row)">历史</el-button>
                            <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
            </el-card>
        </div>

        <el-dialog :title="editing ? '编辑 EID' : '新增 EID'" v-model="dialogVisible" width="550px">
            <el-form :model="form" label-width="90px">
                <el-row :gutter="12">
                    <el-col :span="12"><el-form-item label="物料编码" required><el-input v-model="form.itemcd" :disabled="!!editing" /></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="设备 SN" required><el-input v-model="form.eid" :disabled="!!editing" /></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="类型"><el-select v-model="form.etyp" style="width:100%"><el-option v-for="t in etypOptions" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="状态"><el-select v-model="form.sflg" clearable style="width:100%"><el-option v-for="t in sflgOptions" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="质检"><el-select v-model="form.qcflg" clearable style="width:100%"><el-option v-for="t in qcflgOptions" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="仓库"><el-select v-model="form.whcd" clearable style="width:100%"><el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd" /></el-select></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="新旧"><el-select v-model="form.new_old" clearable style="width:100%"><el-option v-for="t in noOptions" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="质保范围"><el-select v-model="form.old_degree" clearable style="width:100%"><el-option v-for="t in odOptions" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="是否整机"><el-select v-model="form.isunit" clearable style="width:100%"><el-option v-for="t in iuOptions" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="关联单号"><el-input v-model="form.refid" /></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="生产日期"><el-input v-model="form.prddate" /></el-form-item></el-col>
                    <el-col :span="12"><el-form-item label="制造序列号"><el-input v-model="form.manuf_seq" /></el-form-item></el-col>
                    <el-col :span="24"><el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item></el-col>
                </el-row>
            </el-form>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
            </template>
        </el-dialog>

        <!-- 历史记录弹窗 -->
        <el-dialog title="设备变更历史" v-model="historyVisible" width="800px">
            <el-table :data="tracks" v-loading="trackLoading" stripe max-height="500">
                <el-table-column type="index" label="序号" width="50" />
                <el-table-column prop="change_date" label="变更日期" width="155" />
                <el-table-column label="操作" width="80">
                    <template #default="{ row }">
                        <el-tag v-if="row.type === 'i'" type="success" size="small">首次录入</el-tag>
                        <el-tag v-else-if="row.type === 'u'" type="warning" size="small">状态变更</el-tag>
                        <el-tag v-else-if="row.type === 'd'" type="danger" size="small">删除</el-tag>
                        <span v-else>{{ row.type }}</span>
                    </template>
                </el-table-column>
                <el-table-column label="状态" width="120">
                    <template #default="{ row }">
                        <template v-if="row.type === 'i'">{{ codeMaps.ES?.[row.sflg] || row.sflg }}</template>
                        <template v-else>{{ codeMaps.ES?.[row.sflg] || row.sflg }}→{{ codeMaps.ES?.[row.n_sflg] || row.n_sflg }}</template>
                    </template>
                </el-table-column>
                <el-table-column label="质检" width="100">
                    <template #default="{ row }">
                        <template v-if="row.type === 'i'">{{ codeMaps.QS?.[row.qcflg] || row.qcflg }}</template>
                        <template v-else>{{ codeMaps.QS?.[row.qcflg] || row.qcflg }}→{{ codeMaps.QS?.[row.n_qcflg] || row.n_qcflg }}</template>
                    </template>
                </el-table-column>
                <el-table-column label="仓库" width="100">
                    <template #default="{ row }">
                        <template v-if="row.type === 'i'">{{ (row as Record<string,unknown>).wh_nm || row.whcd }}</template>
                        <template v-else>{{ (row as Record<string,unknown>).wh_nm || row.whcd }}→{{ (row as Record<string,unknown>).n_wh_nm || row.n_whcd }}</template>
                    </template>
                </el-table-column>
                <el-table-column label="关联单号" width="100">
                    <template #default="{ row }">{{ row.n_refid || row.refid }}</template>
                </el-table-column>
                <el-table-column prop="remark" label="备注" min-width="120" />
            </el-table>
            <template #footer>
                <el-button @click="historyVisible = false">关闭</el-button>
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
import { fetchEidList, createEid, updateEid, deleteEid, fetchEidTree, fetchSyscodes, fetchWarehouses, fetchEidTracks } from '@/api/master'
import type { ItemClassNode, EidRecord, EidPage } from '@/api/master'

const treeData = ref<ItemClassNode[]>([])
const treeFilterText = ref('')
const treeRef = ref<InstanceType<typeof ElTree>>()
const selectedClassCd = ref('')

const eids = ref<EidRecord[]>([])
const loading = ref(false)
const searchText = ref('')
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

const dialogVisible = ref(false)
const editing = ref<Record<string,string>|null>(null)
const saving = ref(false)
const form = reactive({ itemcd: '', eid: '', etyp: '0', whcd: '', sflg: '8', qcflg: '', new_old: '1', old_degree: '', isunit: '', refid: '', prddate: '', manuf_seq: '', remark: '' })
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
const noOptions = ref<{ code_cd: string; code_nm: string }[]>([])
const iuOptions = ref<{ code_cd: string; code_nm: string }[]>([])
const odOptions = ref<{ code_cd: string; code_nm: string }[]>([])
const historyVisible = ref(false)
const tracks = ref<Record<string,unknown>[]>([])
const trackLoading = ref(false)
const etypOptions = ref<{ code_cd: string; code_nm: string }[]>([])
const sflgOptions = ref<{ code_cd: string; code_nm: string }[]>([])
const qcflgOptions = ref<{ code_cd: string; code_nm: string }[]>([])
const codeMaps = ref<Record<string, Record<string, string>>>({})

watch(page, () => loadData())
watch(perPage, () => { page.value = 1; loadData() })
watch(treeFilterText, (v) => treeRef.value?.filter(v))
onMounted(async () => {
    await loadTree()
    const [et, es, qs, no, iu, od] = await Promise.all([
        fetchSyscodes('ET'), fetchSyscodes('ES'), fetchSyscodes('QS'),
        fetchSyscodes('NO'), fetchSyscodes('IU'), fetchSyscodes('OD'),
    ])
    etypOptions.value = et.data || []
    sflgOptions.value = es.data || []
    qcflgOptions.value = qs.data || []
    noOptions.value = no.data || []
    iuOptions.value = iu.data || []
    odOptions.value = od.data || []
    codeMaps.value = {
        ET: Object.fromEntries((et.data||[]).map(t => [t.code_cd, t.code_nm])),
        ES: Object.fromEntries((es.data||[]).map(t => [t.code_cd, t.code_nm])),
        QS: Object.fromEntries((qs.data||[]).map(t => [t.code_cd, t.code_nm])),
        NO: Object.fromEntries((no.data||[]).map(t => [t.code_cd, t.code_nm])),
        IU: Object.fromEntries((iu.data||[]).map(t => [t.code_cd, t.code_nm])),
        OD: Object.fromEntries((od.data||[]).map(t => [t.code_cd, t.code_nm])),
    }
    const wh = await fetchWarehouses()
    whOptions.value = wh.data || []
    loadData()
})

async function loadTree() {
    try { const res = await fetchEidTree(); treeData.value = res.data || [] } catch { /* */ }
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
    selectedClassCd.value = node.class_cd
    searchText.value = ''
    page.value = 1
    loadData()
}

async function loadData() {
    loading.value = true
    try {
        const params: { page: string; per_page: string; class_cd?: string; search?: string } = {
            page: String(page.value), per_page: String(perPage.value),
        }
        if (searchText.value) { params.search = searchText.value }
        else if (selectedClassCd.value) { params.class_cd = selectedClassCd.value }
        const res = await fetchEidList(params)
        const data = res.data as EidPage
        eids.value = data.items || []
        total.value = data.total || 0
    } catch { ElMessage.error('加载失败') }
    finally { loading.value = false }
}

function onSearch() { page.value = 1; loadData() }

function openDialog(row?: Record<string,string>) {
    if (row) {
        editing.value = row
        form.itemcd = row.itemcd || ''; form.eid = row.eid || ''
        form.etyp = row.etyp || '0'; form.whcd = row.whcd || ''
        form.sflg = row.sflg || '8'; form.qcflg = row.qcflg || ''
        form.new_old = row.new_old || '1'; form.old_degree = row.old_degree || ''
        form.isunit = row.isunit || ''; form.refid = row.refid || ''
        form.prddate = row.prddate || ''; form.manuf_seq = row.manuf_seq || ''
        form.remark = row.remark || ''
    } else {
        editing.value = null
        Object.assign(form, { itemcd: '', eid: '', etyp: '0', whcd: '', sflg: '8', qcflg: '', new_old: '1', old_degree: '', isunit: '', refid: '', prddate: '', manuf_seq: '', remark: '' })
    }
    dialogVisible.value = true
}

async function handleSave() {
    saving.value = true
    try {
        if (editing.value) {
            await updateEid(editing.value.itemcd, editing.value.eid, { ...form })
            ElMessage.success('更新成功')
        } else {
            await createEid({ ...form, useflg: '1' })
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } finally { saving.value = false }
}

async function openHistory(row: Record<string,string>) {
    historyVisible.value = true
    trackLoading.value = true
    try {
        const res = await fetchEidTracks(row.itemcd, row.eid)
        tracks.value = res.data || []
    } catch { ElMessage.error('加载历史失败') }
    finally { trackLoading.value = false }
}

async function handleDelete(row: Record<string,string>) {
    try {
        await ElMessageBox.confirm(`确定删除 EID ${row.eid}？`, '确认')
        await deleteEid(row.itemcd, row.eid)
        ElMessage.success('已删除')
        loadData()
    } catch (e: unknown) { if (e !== 'cancel') ElMessage.error('删除失败') }
}
</script>

<style lang="scss" scoped>
.eid-page { display: flex; gap: 12px; padding: 16px; height: calc(100vh - 80px); }
.tree-panel {
    width: 230px; flex-shrink: 0; overflow-y: auto;
    :deep(.el-card__body) { padding: 8px; }
}
.tree-header { display: flex; justify-content: space-between; align-items: center; }
.tree-actions { display: flex; gap: 4px; margin-bottom: 4px; }
.tree-node {
    display: flex; align-items: center; flex: 1; min-width: 0; font-size: 13px;
    .tree-node-label { flex-shrink: 1; }
    .tree-node-code { display: none; }
    .tree-node-count { color: #409eff; font-size: 11px; margin-left: 8px; background: #ecf5ff; padding: 0 5px; border-radius: 8px; flex-shrink: 0; }
}
.table-panel { flex: 1; overflow-y: auto; min-width: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.header-actions { display: flex; align-items: center; }
</style>
