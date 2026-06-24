<template>
  <div class="page">
    <div class="page-header"><h2>呼出管理</h2></div>

    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>计划单号</label><el-input v-model="searchPlanno" placeholder="输入单号" size="small" style="width:140px" clearable /></div>
        <div class="field"><label>呼出类型</label><el-select v-model="searchServetyp" size="small" style="width:130px" clearable>
          <el-option label="预计划呼出" value="1" /><el-option label="实施任务" value="2" /></el-select></div>
        <div class="field"><label>状态</label><el-select v-model="searchStatus" size="small" style="width:110px" clearable>
          <el-option label="待呼出" value="00" /><el-option label="已呼出" value="01" /><el-option label="已作废" value="09" /></el-select></div>
        <div class="field"><label>计划状态</label><el-select v-model="searchPlanStatus" size="small" style="width:110px" clearable>
          <el-option label="计划中" value="00" /><el-option label="计划完成" value="01" />
          <el-option label="分派中" value="02" /><el-option label="实施完成" value="03" />
          <el-option label="实施中" value="04" /><el-option label="计划退回" value="08" /></el-select></div>
        <el-button type="primary" size="small" @click="onSearch">查询</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small">
        <el-table-column prop="dtlid" label="ID" width="60" />
        <el-table-column prop="planno" label="计划单号" width="110" />
        <el-table-column label="类型" width="90"><template #default="{row}">{{ ['客户确认','预计划呼出','实施任务'][Number(row.servetyp)]||row.servetyp }}</template></el-table-column>
        <el-table-column prop="serve_task" label="任务" min-width="140" show-overflow-tooltip />
        <el-table-column label="呼出结果" width="90"><template #default="{row}"><el-tag v-if="row.serve_back" size="small" :type="{Y:'success',N:'danger',O:'warning'}[row.serve_back]">{{ {Y:'同意',N:'不同意',O:'未接通'}[row.serve_back]||row.serve_back }}</el-tag><span v-else style="color:#c0c4cc">未呼出</span></template></el-table-column>
        <el-table-column prop="serve_mark" label="反馈备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='01'?'success':row.status==='09'?'danger':'info'" size="small">{{ {00:'待呼出',01:'已呼出',09:'已作废'}[row.status] }}</el-tag></template></el-table-column>
        <el-table-column prop="gendate" label="日期" width="90" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{row}">
            <el-button v-if="row.status==='00'" link type="primary" size="small" @click="openFeedback(row)">录入反馈</el-button>
            <el-button v-if="row.status==='00'" link type="success" size="small" @click="doMarkDone(row)">标记已呼出</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <!-- 反馈录入对话框 -->
    <el-dialog v-model="feedbackVisible" title="呼出反馈" width="420px">
      <el-form :model="fbForm" label-width="80px">
        <el-form-item label="呼出结果"><el-radio-group v-model="fbForm.serve_back"><el-radio value="Y">同意</el-radio><el-radio value="N">不同意</el-radio><el-radio value="O">未接通</el-radio></el-radio-group></el-form-item>
        <el-form-item label="反馈备注"><el-input v-model="fbForm.serve_mark" type="textarea" :rows="3" placeholder="客户反馈/地址确认/时间安排等" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="feedbackVisible=false">取消</el-button><el-button type="primary" :loading="fbSaving" @click="doFeedback">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import request from '@/api/request'
import { updatePlanServe, transitionPlanServe, type ServeRecord } from '@/api/sales'

const items = ref<ServeRecord[]>([]); const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const searchPlanno = ref(''); const searchServetyp = ref(''); const searchStatus = ref(''); const searchPlanStatus = ref('')

watch(page, () => loadData()); watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const params: Record<string,string> = { page: String(page.value), per_page: String(perPage.value) }
    if (searchPlanno.value) params.planno = searchPlanno.value
    const res = await request.get<never, { data: { items: ServeRecord[]; total: number } }>('/sales/plan-serve', { params })
    let list = res?.data?.items || []
    if (searchServetyp.value) list = list.filter(r => r.servetyp === searchServetyp.value)
    if (searchStatus.value) list = list.filter(r => r.status === searchStatus.value)
    if (searchPlanStatus.value) {
      const plansRes = await request.get<never, { data: { items: { planno: string; plan_status: string }[] } }>('/sales/plans', { params: { per_page: '1000' } })
      const planStatusMap = new Map((plansRes?.data?.items || []).map(p => [p.planno, p.plan_status]))
      list = list.filter(r => planStatusMap.get(r.planno) === searchPlanStatus.value)
    }
    items.value = list.slice((page.value - 1) * perPage.value, page.value * perPage.value)
    total.value = list.length
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function onSearch() { page.value = 1; loadData() }

// 反馈
const feedbackVisible = ref(false); const fbForm = ref({ dtlid: 0, serve_back: 'Y', serve_mark: '' }); const fbSaving = ref(false)
function openFeedback(row: ServeRecord) { fbForm.value = { dtlid: row.dtlid, serve_back: row.serve_back || 'Y', serve_mark: row.serve_mark || '' }; feedbackVisible.value = true }
async function doFeedback() {
  fbSaving.value = true
  try { await updatePlanServe(fbForm.value.dtlid, { serve_back: fbForm.value.serve_back, serve_mark: fbForm.value.serve_mark }); feedbackVisible.value = false; loadData(); ElMessage.success('已保存') }
  catch { ElMessage.error('保存失败') }
  finally { fbSaving.value = false }
}
async function doMarkDone(row: ServeRecord) {
  try { await transitionPlanServe(row.dtlid, '01'); loadData(); ElMessage.success('已标记为已呼出') }
  catch { ElMessage.error('操作失败') }
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px }
.page-header h2 { font-size:18px; font-weight:600; margin:0 }
.search-bar { display:flex; gap:12px; flex-wrap:wrap; align-items:center }
.field { display:flex; align-items:center; gap:6px }
.field label { font-size:13px; color:#606266; white-space:nowrap }
</style>
