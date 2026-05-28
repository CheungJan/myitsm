<template>
  <div class="page">
    <div class="page-header"><h2>入库单管理</h2><el-button type="primary" size="small" @click="openCreate">新建</el-button></div>

    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field">
          <label>单号</label>
          <el-input v-model="s.bill" placeholder="单号" size="small" style="width:140px" clearable @keyup.enter="doSearch"/>
        </div>
        <div class="field">
          <label>仓库</label>
          <el-select v-model="s.whcd" size="small" style="width:130px" clearable>
            <el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd"/>
          </el-select>
        </div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDrawer">
        <el-table-column prop="inbillid" label="入库单号" width="110"/>
        <el-table-column prop="refbillid" label="关联单据" width="100"/>
        <el-table-column label="仓库" width="110">
          <template #default="{ row }">
            <span v-if="!row.whcd" style="color:#e6a23c;font-size:12px">⚠ 待填仓库</span>
            <span v-else>{{ row.whnm || row.whcd }}</span>
          </template>
        </el-table-column>
        <el-table-column label="入库类型" width="80">
          <template #default="{ row }">{{ ivLabel(row.invtyp as string) }}</template>
        </el-table-column>
        <el-table-column label="入库日期" width="110">
          <template #default="{ row }">{{ formatDate(row.indate as string || row.gendate) }}</template>
        </el-table-column>
        <el-table-column prop="memo" label="备注" min-width="100" show-overflow-tooltip/>
        <el-table-column label="操作员" width="80">
          <template #default="{ row }">{{ userName(row.opercd as string) }}</template>
        </el-table-column>
        <el-table-column label="审批" width="70">
          <template #default="{ row }">
            <el-tag :type="auditTag(row.auditflg as string)" size="small">{{ auditLabel(row.auditflg as string) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.auditflg === '0'" link type="primary" size="small" @click.stop="openAudit(row)">审核</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <!-- 审核弹窗 -->
    <el-dialog title="审核入库单" v-model="auditing" width="620px" @closed="auditTarget = null; auditWhcd = ''; auditMemo = ''">
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ (auditTarget as any).inbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ (auditTarget as any).refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="入库类型">{{ ivLabel((auditTarget as any).invtyp) }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ (auditTarget as any).suppcd || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-form style="margin-top:14px" label-width="80px" size="small">
          <el-form-item label="入库仓库" required>
            <el-select v-model="auditWhcd" placeholder="请选择入库仓库" style="width:220px" filterable>
              <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
            </el-select>
            <span v-if="!(auditTarget as any).whcd" style="margin-left:8px;color:#e6a23c;font-size:12px">
              系统自动生成草稿，请选择实际入库仓库
            </span>
          </el-form-item>
        </el-form>
        <h4 style="margin:8px 0 8px">入库明细</h4>
        <el-table :data="(auditTarget as any).details || []" size="small" stripe>
          <el-table-column prop="itemcd" label="物料" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
          <el-table-column prop="inqty" label="数量" width="70"/>
        </el-table>
        <el-input v-model="auditMemo" type="textarea" :rows="2" placeholder="审核备注" style="margin-top:12px"/>
      </template>
      <template #footer>
        <el-button @click="auditing = false">取消</el-button>
        <el-button type="success" @click="handleAudit" :loading="auditLoading" :disabled="!auditWhcd">审核通过</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer" title="入库单详情" size="550px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ (detail as any).inbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ (detail as any).refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库">
            <span v-if="!(detail as any).whcd" style="color:#e6a23c">待填仓库</span>
            <span v-else>{{ (detail as any).whnm || (detail as any).whcd }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="入库类型">{{ ivLabel((detail as any).invtyp) }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ formatDate((detail as any).indate || (detail as any).gendate) }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ userName((detail as any).opercd) }}</el-descriptions-item>
          <el-descriptions-item label="审批状态">
            <el-tag :type="auditTag((detail as any).auditflg)" size="small">{{ auditLabel((detail as any).auditflg) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ (detail as any).memo || '-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">入库明细</h4>
        <el-table :data="(detail as any).details || []" size="small" stripe>
          <el-table-column prop="itemcd" label="物料" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
          <el-table-column prop="inqty" label="数量" width="70"/>
        </el-table>
      </template>
    </el-drawer>

    <!-- 新建入库单 -->
    <el-dialog title="新建入库单" v-model="creating" width="750px" @closed="resetCreateForm">
      <el-form :model="createForm" label-width="90px" size="small">
        <el-form-item label="入库类型" required>
          <el-select v-model="createForm.invtyp" style="width:100%" @change="onInvtypChange">
            <el-option v-for="o in invtypOptions" :key="o.value" :label="o.label" :value="o.value"/>
          </el-select>
        </el-form-item>
        <el-form-item label="入库仓库" required>
          <el-select v-model="createForm.whcd" style="width:100%" filterable placeholder="选择仓库">
            <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="showRefBillid" label="关联单据号">
          <el-input v-model="createForm.refbillid" :placeholder="refBillidPlaceholder"/>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp === '1'" label="供应商">
          <el-select v-model="createForm.suppcd" style="width:100%" filterable placeholder="选择供应商">
            <el-option v-for="s in suppOptions" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="入库日期">
          <el-date-picker v-model="createForm.indate" type="date" style="width:100%" value-format="YYYY-MM-DD"/>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.memo" type="textarea" :rows="2"/>
        </el-form-item>
        <el-form-item label="入库明细">
          <div style="width:100%">
            <el-table :data="createDetails" size="small" stripe>
              <el-table-column label="物料" min-width="180">
                <template #default="{$index}">
                  <el-select v-model="createDetails[$index].itemcd" filterable remote reserve-keyword :remote-method="(q:string)=>searchItems(q)" :loading="itemSearching" style="width:100%" size="small" placeholder="搜索物料" clearable>
                    <el-option v-for="it in itemOptions" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd"/>
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="数量" width="100">
                <template #default="{$index}">
                  <el-input-number v-model="createDetails[$index].inqty" :min="1" size="small" style="width:90px"/>
                </template>
              </el-table-column>
              <el-table-column label="关联行号" width="100">
                <template #default="{$index}">
                  <el-input-number v-model="createDetails[$index].reflineno" :min="0" size="small" style="width:90px"/>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60">
                <template #default="{$index}">
                  <el-button link type="danger" size="small" @click="removeDetail($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button type="primary" link size="small" @click="addDetail" style="margin-top:8px">+ 添加明细</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="creating = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="createSaving">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useUserNames } from '@/composables/useUserNames'
import { useDict } from '@/composables/useDict'
import { fetchSyscodes, fetchSuppliersSimple, fetchItems, type ItemRecord } from '@/api/master'
import { fetchStockIn, fetchStockInDetail, fetchWarehouses, createStockIn, auditStockIn, type StockInRecord } from '@/api/warehouse'

const { userName } = useUserNames()
const { dictLabel: ivLabel } = useDict('IV')
const { items, loading, page, perPage, total, onSearch, load } = useListPage<StockInRecord>(fetchStockIn)

const s = reactive({ bill: '', whcd: '' })
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
const drawer = ref(false)
const detail = ref<StockInRecord | null>(null)
const auditMap = ref<Record<string, string>>({})

// ---- 新建入库单 ----
const invtypOptions = [
    { value: '1', label: '采购入库' },
    { value: '2', label: '销售退货入库' },
    { value: '3', label: '服务返还入库' },
    { value: '4', label: '调拨入库' },
    { value: '5', label: '借出归还' },
    { value: '6', label: '翻新入库' },
    { value: '7', label: '回收入库' },
    { value: '8', label: '其他入库' },
]
const creating = ref(false)
const createSaving = ref(false)
const createForm = reactive({ invtyp: '', whcd: '', refbillid: '', suppcd: '', indate: '', memo: '' })
interface DetailRow { itemcd: string; inqty: number; reflineno: number | undefined }
const createDetails = reactive<DetailRow[]>([])
const suppOptions = ref<{ supp_cd: string; supp_nm: string }[]>([])
const itemOptions = ref<ItemRecord[]>([])
const itemSearching = ref(false)

const showRefBillid = computed(() => ['1', '3', '4'].includes(createForm.invtyp))
const refBillidPlaceholder = computed(() => {
    if (createForm.invtyp === '1') return '采购订单号'
    if (createForm.invtyp === '4') return '调拨出库单号'
    return '关联单据号'
})

onMounted(async () => {
    try { const r = await fetchWarehouses(); whOptions.value = r.data || [] } catch { /* 忽略 */ }
    try {
        const r = await fetchSyscodes('AF')
        ;(r.data || []).forEach((c: { code_cd: string; code_nm: string }) => {
            auditMap.value[c.code_cd] = c.code_nm
        })
    } catch { /* 忽略 */ }
})

function formatDate(val: string | undefined): string {
    if (!val) return '-'
    return val.replace('T', ' ').substring(0, 19)
}

function auditTag(cd: string) {
    const m: Record<string, string> = { '0': 'info', '1': 'warning', '2': 'success' }
    return m[cd] || 'info'
}

function auditLabel(cd: string) { return auditMap.value[cd] || cd }

function doSearch() {
    const p: Record<string, string> = {}
    if (s.bill) p.inbillid = s.bill
    if (s.whcd) p.whcd = s.whcd
    onSearch(p)
}

async function openDrawer(row: StockInRecord) {
    drawer.value = true
    try { const r = await fetchStockInDetail(row.inbillid); detail.value = r.data as any } catch { detail.value = row }
}

// ---- 新建入库单 ----
function openCreate() {
    creating.value = true
    fetchSuppliersSimple().then(r => { suppOptions.value = r.data || [] }).catch(() => {})
}

function onInvtypChange() {
    createForm.refbillid = ''
    createForm.suppcd = ''
}

async function searchItems(query: string) {
    if (!query || query.length < 1) { itemOptions.value = []; return }
    itemSearching.value = true
    try {
        const r = await fetchItems({ search: query, per_page: 20 })
        itemOptions.value = r.data?.items || []
    } catch { /* 忽略 */ }
    finally { itemSearching.value = false }
}

function addDetail() {
    createDetails.push({ itemcd: '', inqty: 1, reflineno: undefined })
}

function removeDetail(index: number) {
    createDetails.splice(index, 1)
}

function resetCreateForm() {
    createForm.invtyp = ''
    createForm.whcd = ''
    createForm.refbillid = ''
    createForm.suppcd = ''
    createForm.indate = ''
    createForm.memo = ''
    createDetails.length = 0
}

async function handleCreate() {
    if (!createForm.whcd || !createForm.invtyp) { ElMessage.warning('请填写入库类型和入库仓库'); return }
    if (createDetails.length === 0 || createDetails.some(d => !d.itemcd || !d.inqty)) { ElMessage.warning('请完善入库明细'); return }
    createSaving.value = true
    try {
        const body: Record<string, unknown> = {
            whcd: createForm.whcd,
            invtyp: createForm.invtyp,
            details: createDetails.map(d => ({
                itemcd: d.itemcd,
                inqty: d.inqty,
                ...(d.reflineno != null ? { reflineno: d.reflineno } : {}),
            })),
        }
        if (createForm.indate) body.indate = createForm.indate
        if (createForm.refbillid) body.refbillid = createForm.refbillid
        if (createForm.suppcd) body.suppcd = createForm.suppcd
        if (createForm.memo) body.memo = createForm.memo
        await createStockIn(body)
        ElMessage.success('入库单创建成功')
        creating.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '创建失败')
    } finally { createSaving.value = false }
}

// ---- 审核 ----
const auditing = ref(false)
const auditTarget = ref<StockInRecord | null>(null)
const auditLoading = ref(false)
const auditWhcd = ref('')
const auditMemo = ref('')

async function openAudit(row: StockInRecord) {
    auditTarget.value = row
    auditWhcd.value = (row as any).whcd || ''
    auditMemo.value = ''
    auditing.value = true
    try {
        const r = await fetchStockInDetail(row.inbillid)
        auditTarget.value = r.data as any
        auditWhcd.value = (r.data as any).whcd || ''
    } catch { /* use row data */ }
}

async function handleAudit() {
    if (!auditTarget.value || !auditWhcd.value) return
    auditLoading.value = true
    try {
        await auditStockIn((auditTarget.value as any).inbillid, auditWhcd.value, auditMemo.value || undefined)
        ElMessage.success('审核通过')
        auditing.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '审核失败')
    } finally { auditLoading.value = false }
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0 }
.search-bar { display: flex; gap: 12px; align-items: center }
.field { display: flex; align-items: center; gap: 6px }
.field label { font-size: 13px; color: #606266 }
</style>