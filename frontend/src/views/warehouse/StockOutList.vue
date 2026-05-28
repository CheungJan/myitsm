<template>
  <div class="page">
    <div class="page-header">
      <h2>出库单管理</h2>
    </div>
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
        <el-table-column label="出库日期" width="100">
          <template #default="{ row }">{{ row.outdate || row.gendate || '-' }}</template>
        </el-table-column>
        <el-table-column prop="memo" label="备注" min-width="140" show-overflow-tooltip />
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
    <el-dialog title="审核出库单" v-model="auditing" width="600px" @closed="auditTarget = null">
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ auditTarget.outbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ auditTarget.refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ auditTarget.whnm || auditTarget.whcd }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ ovLabel(auditTarget.invtyp) }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:12px 0 8px">出库明细</h4>
        <el-table :data="auditTarget.details || []" size="small" stripe>
          <el-table-column prop="itemcd" label="物料" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
          <el-table-column prop="outqty" label="数量" width="70"/>
        </el-table>
      </template>
      <template #footer>
        <el-button @click="handleAudit('9')" :loading="auditLoading">退回</el-button>
        <el-button type="primary" @click="handleAudit('2')" :loading="auditLoading">审核通过</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawer" title="出库单详情" size="550px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ detail.outbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ detail.refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ detail.whnm || detail.whcd }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ ovLabel(detail.invtyp) }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ detail.outdate || detail.gendate }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ userName(detail.opercd) }}</el-descriptions-item>
          <el-descriptions-item label="审批">
            <el-tag :type="auditTag(detail.auditflg)" size="small">{{ auditLabel(detail.auditflg) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo || '-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">出库明细</h4>
        <el-table :data="detail.details || []" size="small" stripe>
          <el-table-column prop="itemcd" label="物料" width="100" />
          <el-table-column prop="item_nm" label="物料名称" min-width="140" />
          <el-table-column prop="outqty" label="数量" width="70" />
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useUserNames } from '@/composables/useUserNames'
import { useDict } from '@/composables/useDict'
import { fetchSyscodes } from '@/api/master'
const { userName } = useUserNames()
const { dictLabel: ovLabel } = useDict('OV')

import {
    fetchStockOut,
    fetchStockOutDetail,
    fetchWarehouses,
    auditStockOut,
    type StockOutRecord,
} from '@/api/warehouse'

const { items, loading, page, perPage, total, onSearch, load } = useListPage<StockOutRecord>(fetchStockOut)
const s = reactive({ bill: '', whcd: '' })
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
const drawer = ref(false)
const detail = ref<StockOutRecord | null>(null)
const auditMap = ref<Record<string, string>>({})

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
        detail.value = r.data
    } catch {
        detail.value = row
    }
}

const auditing = ref(false)
const auditTarget = ref<StockOutRecord | null>(null)
const auditLoading = ref(false)

async function openAudit(row: StockOutRecord) {
    auditTarget.value = row
    auditing.value = true
    try {
        const r = await fetchStockOutDetail(row.outbillid)
        auditTarget.value = r.data
    } catch { /* use row data */ }
}

async function handleAudit(flg: string) {
    if (!auditTarget.value) return
    auditLoading.value = true
    try {
        await auditStockOut(auditTarget.value.outbillid, flg)
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
