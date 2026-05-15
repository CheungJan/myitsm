<template>
  <div class="plan-page">
    <div class="page-header">
      <h2>预计划管理</h2>
      <el-button type="primary" @click="openCreate">＋ 新建预计划</el-button>
    </div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>计划单号</label><el-input v-model="searchPlanno" placeholder="输入单号" size="small" style="width:140px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>客户名称</label><el-input v-model="searchCustNm" placeholder="输入客户" size="small" style="width:160px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>状态</label><el-select v-model="searchStatus" size="small" style="width:120px" clearable><el-option label="待确认" value="0" /><el-option label="已确认" value="1" /><el-option label="已完成" value="2" /></el-select></div>
        <el-button type="primary" size="small" @click="onSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="plans" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDetail">
        <el-table-column prop="planno" label="计划单号" width="110" />
        <el-table-column prop="custnm" label="客户名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="custcard" label="磁卡号" width="100" />
        <el-table-column label="计划日期" width="100"><template #default="{row}">{{ (row as Record<string,unknown>).plandate || row.gendate || '-' }}</template></el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{row}"><el-tag :type="statusTag(row.plan_status)" size="small">{{ statusLabel(row.plan_status) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="opercd" label="操作员" width="80" />
        <el-table-column label="操作" width="120"><template #default="{row}"><el-button link type="primary" size="small" @click.stop="openDetail(row)">详情</el-button><el-button link type="primary" size="small" @click.stop="openEdit(row)">编辑</el-button></template></el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchPlans } from '@/api/sales'
import type { PlanRecord } from '@/api/sales'

const plans = ref<PlanRecord[]>([]); const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const searchPlanno = ref(''); const searchCustNm = ref(''); const searchStatus = ref('')

function statusTag(s: string) { const m: Record<string,string> = {'0':'warning','1':'success','2':'info'}; return m[s] || 'info' }
function statusLabel(s: string) { const m: Record<string,string> = {'0':'待确认','1':'已确认','2':'已完成'}; return m[s] || s }

watch(page, () => loadData()); watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const params: Record<string,string> = { page: String(page.value), per_page: String(perPage.value) }
    if (searchPlanno.value) params.planno = searchPlanno.value
    if (searchCustNm.value) params.custnm = searchCustNm.value
    if (searchStatus.value) params.plan_status = searchStatus.value
    const res = await fetchPlans(params)
    plans.value = res.data.items || []; total.value = res.data.total || 0
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function onSearch() { page.value = 1; loadData() }
function openDetail(row: PlanRecord) { ElMessage.info(`详情: ${row.planno}`) }
function openEdit(row: PlanRecord) { ElMessage.info(`编辑: ${row.planno}`) }
function openCreate() { ElMessage.info('新建预计划 — F2 后续实现') }
</script>

<style scoped>
.plan-page { padding: 0 }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px }
.page-header h2 { font-size:18px; font-weight:600; margin:0 }
.search-bar { display:flex; gap:12px; flex-wrap:wrap; align-items:center }
.field { display:flex; align-items:center; gap:6px }
.field label { font-size:13px; color:#606266; white-space:nowrap }
</style>
