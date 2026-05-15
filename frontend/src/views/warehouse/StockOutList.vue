<template>
  <div class="page">
    <div class="page-header"><h2>出库单管理</h2></div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>单号</label><el-input v-model="s.bill" placeholder="单号" size="small" style="width:140px" clearable @keyup.enter="doSearch"/></div>
        <div class="field"><label>仓库</label><el-select v-model="s.whcd" size="small" style="width:130px" clearable><el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd"/></el-select></div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDrawer">
        <el-table-column prop="outbillid" label="出库单号" width="120"/>
        <el-table-column label="仓库" width="100"><template #default="{row}">{{ row.whnm || row.whcd }}</template></el-table-column>
        <el-table-column label="出库类型" width="80"><template #default="{row}">{{ row.invtyp || '-' }}</template></el-table-column>
        <el-table-column label="出库日期" width="100"><template #default="{row}">{{ row.outdate || row.gendate || '-' }}</template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="140" show-overflow-tooltip/>
        <el-table-column prop="opercd" label="操作员" width="80"/>
        <el-table-column label="审批" width="70"><template #default="{row}"><el-tag :type="row.auditflg==='2'?'success':'warning'" size="small">{{ row.auditflg==='2'?'已审':'待审' }}</el-tag></template></el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>
    <el-drawer v-model="drawer" title="出库单详情" size="550px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ detail.outbillid }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ detail.whnm || detail.whcd }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ detail.invtyp }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ detail.outdate || detail.gendate }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ detail.opercd }}</el-descriptions-item>
          <el-descriptions-item label="审批"><el-tag :type="detail.auditflg==='2'?'success':'warning'" size="small">{{ detail.auditflg==='2'?'已审批':'待审批' }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo || '-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">出库明细</h4>
        <el-table :data="detail.details || []" size="small" stripe>
          <el-table-column prop="itemcd" label="物料" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
          <el-table-column prop="outqty" label="数量" width="70"/>
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { fetchStockOut, fetchStockOutDetail, fetchWarehouses, type StockOutRecord } from '@/api/warehouse'
const { items, loading, page, perPage, total, onSearch } = useListPage<StockOutRecord>(fetchStockOut)
const s = reactive({ bill: '', whcd: '' })
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
const drawer = ref(false)
const detail = ref<StockOutRecord | null>(null)
onMounted(async () => { try { const r = await fetchWarehouses(); whOptions.value = r.data || [] } catch { /* */ } })
function doSearch() { const p: Record<string, string> = {}; if (s.bill) p.outbillid = s.bill; if (s.whcd) p.whcd = s.whcd; onSearch(p) }
async function openDrawer(row: StockOutRecord) { drawer.value = true; try { const r = await fetchStockOutDetail(row.outbillid); detail.value = r.data } catch { detail.value = row } }
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}.search-bar{display:flex;gap:12px;align-items:center}.field{display:flex;align-items:center;gap:6px}.field label{font-size:13px;color:#606266}</style>
