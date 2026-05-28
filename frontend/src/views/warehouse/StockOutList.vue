<template>
  <div class="page">
    <div class="page-header"><h2>出库单管理</h2><el-button type="primary" size="small" @click="openCreate">新建</el-button></div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field">
          <label>单号</label>
          <el-input v-model="s.bill" placeholder="单号" size="small" style="width:140px" clearable @keyup.enter="doSearch" />
        </div>
        <div class="field">
          <label>仓库</label>
          <el-select v-model="s.whcd" size="small" style="width:130px" clearable>
            <el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd" />
          </el-select>
        </div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDrawer">
        <el-table-column prop="outbillid" label="出库单号" width="120" />
        <el-table-column prop="refbillid" label="关联单据" width="120" />
        <el-table-column label="仓库" width="100">
          <template #default="{ row }">{{ row.whnm || row.whcd }}</template>
        </el-table-column>
        <el-table-column label="出库类型" width="80">
          <template #default="{ row }">{{ ovLabel(row.invtyp) }}</template>
        </el-table-column>
        <el-table-column label="出库日期" width="140">
          <template #default="{ row }">{{ formatDate(row.outdate || row.gendate) }}</template>
        </el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作员" width="80">
          <template #default="{ row }">{{ userName(row.opercd) }}</template>
        </el-table-column>
        <el-table-column label="审批" width="70">
          <template #default="{ row }">
            <el-tag :type="auditTag(row.auditflg)" size="small">{{ auditLabel(row.auditflg) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.auditflg === '0'" link type="primary" size="small" @click.stop="openAudit(row)">审核</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <!-- 审核弹窗 -->
    <el-dialog title="审核出库单" v-model="auditing" width="620px" @closed="auditTarget = null; auditMemo = ''">
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ auditTarget.outbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ auditTarget.refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ auditTarget.whnm || auditTarget.whcd }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ ovLabel(auditTarget.invtyp as string) }}</el-descriptions-item>
        </el-descriptions>
        <template v-if="((auditTarget.details_prd as any[])||[]).length > 0">
          <h4 style="margin:12px 0 8px">出库明细</h4>
          <el-table :data="(auditTarget.details_prd as any[]) || []" size="small" stripe>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column prop="outqty" label="数量" width="70"/>
          </el-table>
        </template>
        <template v-if="((auditTarget.details_eid as any[])||[]).length > 0">
          <h4 style="margin:12px 0 8px">出库明细(EID)</h4>
          <el-table :data="(auditTarget.details_eid as any[]) || []" size="small" stripe>
            <el-table-column prop="eid" label="EID" min-width="140"/>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column prop="outqty" label="数量" width="70"/>
          </el-table>
        </template>
        <el-input
          v-model="auditMemo"
          type="textarea"
          :rows="2"
          placeholder="审核备注"
          style="margin-top:12px"
        />
      </template>
      <template #footer>
        <el-button @click="auditing = false">取消</el-button>
        <el-button type="danger" @click="handleAudit('9')" :loading="auditLoading">退回</el-button>
        <el-button type="success" @click="handleAudit('2')" :loading="auditLoading">审核通过</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawer" title="出库单详情" size="550px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ detail.outbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ detail.refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ detail.whnm || detail.whcd }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ ovLabel(detail.invtyp as string) }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ formatDate((detail.outdate || detail.gendate) as string) }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ userName(detail.opercd as string) }}</el-descriptions-item>
          <el-descriptions-item label="审批">
            <el-tag :type="auditTag(detail.auditflg as string)" size="small">{{ auditLabel(detail.auditflg as string) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo || '-' }}</el-descriptions-item>
        </el-descriptions>
        <template v-if="((detail.details_prd as any[])||[]).length > 0">
          <h4 style="margin:16px 0 8px">出库明细</h4>
          <el-table :data="(detail.details_prd as any[]) || []" size="small" stripe>
            <el-table-column prop="itemcd" label="物料" width="100" />
            <el-table-column prop="item_nm" label="物料名称" min-width="140" />
            <el-table-column prop="outqty" label="数量" width="70" />
          </el-table>
        </template>
        <template v-if="((detail.details_eid as any[])||[]).length > 0">
          <h4 style="margin:16px 0 8px">出库明细(EID)</h4>
          <el-table :data="(detail.details_eid as any[]) || []" size="small" stripe>
            <el-table-column prop="eid" label="EID" min-width="140" />
            <el-table-column prop="itemcd" label="物料" width="100" />
            <el-table-column prop="item_nm" label="物料名称" min-width="140" />
            <el-table-column prop="outqty" label="数量" width="70" />
          </el-table>
        </template>
      </template>
    </el-drawer>

    <!-- 新建出库单 -->
    <el-dialog title="新建出库单" v-model="creating" width="750px" @closed="resetCreateForm">
      <el-form :model="createForm" label-width="100px" size="small">
        <el-form-item label="出库类型" required>
          <el-select v-model="createForm.invtyp" style="width:100%" @change="onInvtypChange">
            <el-option v-for="o in invtypOptions" :key="o.value" :label="o.label" :value="o.value"/>
          </el-select>
        </el-form-item>
        <el-form-item label="出库仓库" required>
          <el-select v-model="createForm.whcd" style="width:100%" filterable placeholder="选择仓库">
            <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="showRefBillid" label="关联单据号">
          <el-input v-model="createForm.refbillid" :placeholder="refBillidPlaceholder"/>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp === '3'" label="目标仓库">
          <el-select v-model="createForm.targetwhcd" style="width:100%" filterable placeholder="选择目标仓库">
            <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp === '6'" label="供应商">
          <el-select v-model="createForm.suppcd" style="width:100%" filterable placeholder="选择供应商">
            <el-option v-for="s in suppOptions" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="出库日期">
          <el-date-picker v-model="createForm.outdate" type="date" style="width:100%" value-format="YYYY-MM-DD"/>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.memo" type="textarea" :rows="2"/>
        </el-form-item>
        <el-form-item label="出库明细">
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
                  <el-input-number v-model="createDetails[$index].outqty" :min="1" size="small" style="width:90px"/>
                </template>
              </el-table-column>
              <el-table-column label="EID" width="130">
                <template #default="{$index}">
                  <el-input v-model="createDetails[$index].eid" size="small" placeholder="可选"/>
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
const { userName } = useUserNames()
const { dictLabel: ovLabel } = useDict('OV')

import {
    fetchStockOut,
    fetchStockOutDetail,
    fetchWarehouses,
    createStockOut,
    auditStockOut,
    type StockOutRecord,
} from '@/api/warehouse'

const { items, loading, page, perPage, total, onSearch, load } = useListPage<StockOutRecord>(fetchStockOut)
const s = reactive({ bill: '', whcd: '' })
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
const drawer = ref(false)
const detail = ref<StockOutRecord | null>(null)
const auditMap = ref<Record<string, string>>({})

// ---- 新建出库单 ----
const invtypOptions = [
    { value: '1', label: '销售出库' },
    { value: '2', label: '服务领用' },
    { value: '3', label: '调拨出库' },
    { value: '4', label: '借出出库' },
    { value: '5', label: '质检出库' },
    { value: '6', label: '退货出库' },
    { value: '7', label: '报废出库' },
    { value: '8', label: '其他出库' },
]
const creating = ref(false)
const createSaving = ref(false)
const createForm = reactive({ invtyp: '', whcd: '', refbillid: '', targetwhcd: '', suppcd: '', outdate: '', memo: '' })
interface DetailRow { itemcd: string; outqty: number; eid: string; reflineno: number | undefined }
const createDetails = reactive<DetailRow[]>([])
const suppOptions = ref<{ supp_cd: string; supp_nm: string }[]>([])
const itemOptions = ref<ItemRecord[]>([])
const itemSearching = ref(false)

const showRefBillid = computed(() => ['2', '5', '6'].includes(createForm.invtyp))
const refBillidPlaceholder = computed(() => {
    if (createForm.invtyp === '2') return '服务领用单号'
    if (createForm.invtyp === '5') return '质检单号'
    if (createForm.invtyp === '6') return '采购退货单号'
    return '关联单据号'
})

function openCreate() {
    creating.value = true
    fetchSuppliersSimple().then(r => { suppOptions.value = r.data || [] }).catch(() => {})
}

function onInvtypChange() {
    createForm.refbillid = ''
    createForm.targetwhcd = ''
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
    createDetails.push({ itemcd: '', outqty: 1, eid: '', reflineno: undefined })
}

function removeDetail(index: number) {
    createDetails.splice(index, 1)
}

function resetCreateForm() {
    createForm.invtyp = ''
    createForm.whcd = ''
    createForm.refbillid = ''
    createForm.targetwhcd = ''
    createForm.suppcd = ''
    createForm.outdate = ''
    createForm.memo = ''
    createDetails.length = 0
}

async function handleCreate() {
    if (!createForm.whcd || !createForm.invtyp) { ElMessage.warning('请填写出库类型和出库仓库'); return }
    if (createDetails.length === 0 || createDetails.some(d => !d.itemcd || !d.outqty)) { ElMessage.warning('请完善出库明细'); return }
    createSaving.value = true
    try {
        const body: Record<string, unknown> = {
            whcd: createForm.whcd,
            invtyp: createForm.invtyp,
            details_prd: createDetails
                .filter(d => !d.eid)
                .map(d => ({
                    itemcd: d.itemcd,
                    outqty: d.outqty,
                    ...(d.reflineno != null ? { reflineno: d.reflineno } : {}),
                })),
            details_eid: createDetails
                .filter(d => d.eid)
                .map(d => ({
                    itemcd: d.itemcd,
                    outqty: d.outqty,
                    eid: d.eid,
                    ...(d.reflineno != null ? { reflineno: d.reflineno } : {}),
                })),
        }
        if (createForm.outdate) body.outdate = createForm.outdate
        if (createForm.refbillid) body.refbillid = createForm.refbillid
        if (createForm.targetwhcd) body.targetwhcd = createForm.targetwhcd
        if (createForm.suppcd) body.suppcd = createForm.suppcd
        if (createForm.memo) body.memo = createForm.memo
        await createStockOut(body)
        ElMessage.success('出库单创建成功')
        creating.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '创建失败')
    } finally { createSaving.value = false }
}

onMounted(async () => {
    try {
        const r = await fetchWarehouses()
        whOptions.value = r.data || []
    } catch { /* 忽略 */ }
    try {
        const r = await fetchSyscodes('AF')
        ;(r.data || []).forEach((c: { code_cd: string; code_nm: string }) => {
            auditMap.value[c.code_cd] = c.code_nm
        })
    } catch { /* 忽略 */ }
})

function auditTag(cd: string) {
    const m: Record<string, string> = { '0': 'info', '1': 'warning', '2': 'success' }
    return m[cd] || 'info'
}

function formatDate(val: string | undefined): string {
    if (!val) return '-'
    return val.replace('T', ' ').substring(0, 19)
}

function auditLabel(cd: string) {
    return auditMap.value[cd] || cd
}

function doSearch() {
    const p: Record<string, string> = {}
    if (s.bill) p.outbillid = s.bill
    if (s.whcd) p.whcd = s.whcd
    onSearch(p)
}

async function openDrawer(row: StockOutRecord) {
    drawer.value = true
    try {
        const r = await fetchStockOutDetail(row.outbillid)
        detail.value = r.data as any
    } catch {
        detail.value = row
    }
}

const auditing = ref(false)
const auditTarget = ref<StockOutRecord | null>(null)
const auditLoading = ref(false)
const auditMemo = ref('')

async function openAudit(row: StockOutRecord) {
    auditTarget.value = row
    auditing.value = true
    try {
        const r = await fetchStockOutDetail(row.outbillid)
        auditTarget.value = r.data as any
    } catch { /* use row data */ }
}

async function handleAudit(flg: string) {
    if (!auditTarget.value) return
    auditLoading.value = true
    try {
        await auditStockOut(auditTarget.value.outbillid, flg, auditMemo.value || undefined)
        ElMessage.success(flg === '2' ? '审核通过' : '已退回')
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
