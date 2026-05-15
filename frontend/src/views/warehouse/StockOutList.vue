<template>
  <div class="page">
    <div class="page-header"><h2>出库单管理</h2></div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>出库单号</label><el-input v-model="s.bill" placeholder="单号" size="small" style="width:140px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>仓库</label><el-select v-model="s.whcd" size="small" style="width:130px" clearable><el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd" /></el-select></div>
        <el-button type="primary" size="small" @click="onSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDrawer">
        <el-table-column prop="outbillid" label="出库单号" width="120" />
        <el-table-column label="仓库" width="100"><template #default="{row}">{{ row.whnm || row.whcd }}</template></el-table-column>
        <el-table-column prop="gendate" label="出库日期" width="110" />
        <el-table-column label="操作员" width="80"><template #default="{row}">{{ (row as Record<string,unknown>).opercd || '-' }}</template></el-table-column>
        <el-table-column label="操作" width="80"><template #default="{row}"><el-button link type="primary" size="small" @click.stop="openDrawer(row)">详情</el-button></template></el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <el-drawer v-model="drawer" title="出库单详情" size="600px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ detail.outbillid }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ detail.whnm || detail.whcd }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ detail.gendate }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ (detail as Record<string,unknown>).opercd || '-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">出库明细</h4>
        <el-table :data="detail.details || []" size="small" stripe>
          <el-table-column prop="itemcd" label="物料编码" width="100" />
          <el-table-column prop="item_nm" label="物料名称" min-width="140" show-overflow-tooltip />
          <el-table-column prop="outqty" label="数量" width="70" />
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchStockOut, fetchStockOutDetail, fetchWarehouses } from '@/api/warehouse'
import type { StockOutRecord } from '@/api/warehouse'

const items = ref<StockOutRecord[]>([]); const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const s = reactive({ bill:'', whcd:'' })
const whOptions = ref<{whcd:string;whnm:string}[]>([])
const drawer = ref(false); const detail = ref<StockOutRecord|null>(null)

watch(page,()=>loadData()); watch(perPage,()=>{page.value=1;loadData()})
onMounted(async ()=>{ try{const r=await fetchWarehouses();whOptions.value=r.data||[]}catch{}; loadData() })

async function loadData(){loading.value=true;try{const p:Record<string,string>={page:String(page.value),per_page:String(perPage.value)};if(s.bill)p.outbillid=s.bill;if(s.whcd)p.whcd=s.whcd;const r=await fetchStockOut(p);items.value=r.data.items||[];total.value=r.data.total||0}catch{ElMessage.error('加载失败')}finally{loading.value=false}}
function onSearch(){page.value=1;loadData()}
async function openDrawer(row:StockOutRecord){drawer.value=true;try{const r=await fetchStockOutDetail(row.outbillid);detail.value=r.data}catch{detail.value=row}}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}.search-bar{display:flex;gap:12px;flex-wrap:wrap;align-items:center}.field{display:flex;align-items:center;gap:6px}.field label{font-size:13px;color:#606266;white-space:nowrap}</style>
