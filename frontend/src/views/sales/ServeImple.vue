<template>
  <div class="page">
    <div class="page-header"><h2>计划实施管理</h2></div>

    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>计划单号</label><el-input v-model="searchPlanno" placeholder="输入单号" size="small" style="width:140px" clearable /></div>
        <div class="field"><label>客户名称</label><el-input v-model="searchCustNm" placeholder="输入客户" size="small" style="width:140px" clearable /></div>
        <div class="field"><label>状态</label><el-select v-model="searchStatus" size="small" style="width:110px" clearable>
          <el-option label="分派中" value="02" /><el-option label="实施中" value="04" /><el-option label="实施完成" value="03" /></el-select></div>
        <el-button type="primary" size="small" @click="onSearch">查询</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small">
        <el-table-column prop="planno" label="计划单号" width="110" />
        <el-table-column prop="custnm" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="custcard" label="磁卡号" width="100" />
        <el-table-column prop="contactor" label="联系人" width="80" />
        <el-table-column prop="phoneno" label="电话" width="110" />
        <el-table-column label="计划类型" width="80"><template #default="{row}">{{ plLabel(row.plantyp) }}</template></el-table-column>
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="statusTag(row.plan_status)" size="small">{{ statusLabel(row.plan_status) }}</el-tag></template></el-table-column>
        <el-table-column prop="imple_date" label="实施日期" width="100" />
        <el-table-column prop="send_date" label="配送日期" width="100" />
        <el-table-column prop="train_date" label="培训日期" width="100" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{row}">
            <el-button link type="primary" size="small" @click="openPlan(row)">制定计划</el-button>
            <el-button v-if="row.plan_status==='02'" link type="warning" size="small" @click="doImplement(row)">实施确认</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <!-- 制定实施计划对话框 -->
    <el-dialog v-model="planVisible" title="制定实施计划" width="440px">
      <el-form :model="planForm" label-width="90px">
        <el-form-item label="计划单号"><el-input :model-value="planForm.planno" disabled /></el-form-item>
        <el-form-item label="实施日期"><el-date-picker v-model="planForm.imple_date" type="date" placeholder="选择实施日期" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="配送日期"><el-date-picker v-model="planForm.send_date" type="date" placeholder="选择配送日期" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="培训日期"><el-date-picker v-model="planForm.train_date" type="date" placeholder="选择培训日期" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="实施备注"><el-input v-model="planForm.imple_mark" type="textarea" :rows="2" placeholder="配送地址/安装要求等" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="planVisible=false">取消</el-button><el-button type="primary" :loading="planSaving" @click="doSavePlan">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useDict } from '@/composables/useDict'
import { fetchPlans, updatePlan, implementPlan, type PlanRecord } from '@/api/sales'

const { dictLabel: plLabel } = useDict('PL')
const items = ref<PlanRecord[]>([]); const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const searchPlanno = ref(''); const searchCustNm = ref(''); const searchStatus = ref('')

function statusLabel(s: string) {
  const m: Record<string, string> = { '00': '计划中', '01': '计划完成', '02': '分派中', '03': '实施完成', '04': '实施中', '08': '计划退回', '09': '计划作废' }
  return m[s] || s
}
function statusTag(s: string) {
  const m: Record<string, string> = { '00': 'info', '01': 'success', '02': 'warning', '03': 'primary', '04': '', '08': 'danger', '09': 'danger' }
  return m[s] || 'info'
}

watch(page, () => loadData()); watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, string> = { page: String(page.value), per_page: String(perPage.value) }
    if (searchStatus.value) params.plan_status = searchStatus.value
    if (searchPlanno.value) params.planno = searchPlanno.value
    if (searchCustNm.value) params.custnm = searchCustNm.value
    const res = await fetchPlans(params)
    items.value = res.data.items || []; total.value = res.data.total || 0
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function onSearch() { page.value = 1; loadData() }

// 制定计划
const planVisible = ref(false); const planForm = ref({ planno: '', imple_date: '', send_date: '', train_date: '', imple_mark: '' }); const planSaving = ref(false)
function openPlan(row: PlanRecord) {
  planForm.value = { planno: row.planno, imple_date: row.imple_date || '', send_date: row.send_date || '', train_date: row.train_date || '', imple_mark: row.imple_mark || '' }
  planVisible.value = true
}
async function doSavePlan() {
  planSaving.value = true
  try {
    await updatePlan(planForm.value.planno, { imple_date: planForm.value.imple_date, send_date: planForm.value.send_date, train_date: planForm.value.train_date, imple_mark: planForm.value.imple_mark })
    planVisible.value = false; loadData(); ElMessage.success('已保存')
  } catch { ElMessage.error('保存失败') }
  finally { planSaving.value = false }
}

// 实施确认
async function doImplement(row: PlanRecord) {
  try {
    await ElMessageBox.confirm(`确认实施？将为预计划 ${row.planno} 生成下游单据。`, '实施确认', { type: 'warning' })
    const res = await implementPlan(row.planno)
    ElMessage.success(`实施确认成功，下游单据: ${(res.data as any)?.downstream_id || ''}`)
    loadData()
  } catch { /* 取消 */ }
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
