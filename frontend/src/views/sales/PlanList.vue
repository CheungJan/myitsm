<template>
  <div class="plan-page">
    <div class="page-header">
      <h2>预计划管理</h2>
      <el-button type="primary" @click="openCreate">＋ 新建预计划</el-button>
    </div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>计划单号</label><el-input v-model="searchPlanno" placeholder="输入单号" size="small" style="width:130px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>磁卡号</label><el-input v-model="searchCustcard" placeholder="磁卡号模糊" size="small" style="width:130px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>客户名称</label><el-input v-model="searchCustNm" placeholder="输入客户" size="small" style="width:130px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>计划类型</label><el-select v-model="searchPlantyp" size="small" style="width:110px" clearable>
          <el-option label="新机开通" value="00" /><el-option label="设备变更" value="10" />
          <el-option label="旧机翻新" value="20" /><el-option label="设备取回" value="30" />
          <el-option label="门店关闭" value="40" /></el-select></div>
        <div class="field"><label>状态</label><el-select v-model="searchStatus" size="small" style="width:110px" clearable>
          <el-option label="计划中" value="00" /><el-option label="计划完成" value="01" />
          <el-option label="分派中" value="02" /><el-option label="实施完成" value="03" />
          <el-option label="实施中" value="04" /><el-option label="计划退回" value="08" />
          <el-option label="计划作废" value="09" /></el-select></div>
        <div class="field"><label>计划日期</label>
          <el-date-picker v-model="searchDateFrom" type="date" placeholder="开始" size="small" style="width:120px" value-format="YYYY-MM-DD" clearable />
          <span style="margin:0 4px">至</span>
          <el-date-picker v-model="searchDateTo" type="date" placeholder="结束" size="small" style="width:120px" value-format="YYYY-MM-DD" clearable />
        </div>
        <div class="field"><el-checkbox v-model="searchServeStatus" true-value="01" false-value="">仅呼出中</el-checkbox></div>
        <el-button type="primary" size="small" @click="onSearch">查询</el-button>
        <el-button size="small" @click="onReset">重置</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="plans" v-loading="loading" stripe size="small" highlight-current-row>
        <el-table-column prop="planno" label="计划单号" width="110" />
        <el-table-column prop="custnm" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="custcard" label="磁卡号" width="100" />
        <el-table-column prop="contactor" label="联系人" width="80" />
        <el-table-column prop="phoneno" label="电话" width="120" />
        <el-table-column label="计划类型" width="80"><template #default="{row}">{{ plLabel(row.plantyp) }}</template></el-table-column>
        <el-table-column label="业务类型" width="80"><template #default="{row}">{{ bsLabel(row.busityp) }}</template></el-table-column>
        <el-table-column label="租赁/购买" width="70"><template #default="{row}"><el-tag :type="row.is_rent==='Y'?'success':'info'" size="small">{{ row.is_rent==='Y'?'租赁':'购买' }}</el-tag></template></el-table-column>
        <el-table-column label="机型" width="80"><template #default="{row}">{{ row.pos_item || '-' }}</template></el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{row}"><el-tag :type="statusTag(row.plan_status)" size="small">{{ statusLabel(row.plan_status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="客户" width="70" align="center">
          <template #default="{row}"><el-tag :type="custTag(row)" size="small">{{ custLabel(row) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="deposit" label="押金" width="100" align="right"><template #default="{row}">{{ row.deposit ? '¥'+Number(row.deposit).toLocaleString() : '-' }}</template></el-table-column>
        <el-table-column prop="gendate" label="日期" width="90" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{row}">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="row.plan_status==='00'" link type="success" size="small" @click="doTransition(row,'02')">确认</el-button>
            <el-button v-if="row.plan_status==='02'" link type="warning" size="small" @click="doImplement(row)">实施</el-button>
            <el-button v-if="row.plan_status==='04'" link type="primary" size="small" @click="doOutbound(row)">出库</el-button>
            <el-button v-if="row.plan_status==='04'" link type="success" size="small" @click="doComplete(row)">完成</el-button>
            <el-button v-if="vCan(row)" link type="danger" size="small" @click="doVoid(row)">作废</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="预计划详情" size="620px">
      <template v-if="detail">
        <el-tabs v-model="detailTab">
          <el-tab-pane label="预计划单" name="info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="计划单号">{{ detail.planno }}</el-descriptions-item>
              <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.plan_status)" size="small">{{ statusLabel(detail.plan_status) }}</el-tag></el-descriptions-item>
              <el-descriptions-item label="客户名称">{{ detail.custnm }}</el-descriptions-item>
              <el-descriptions-item label="客户实名">{{ detail.custrnm || '-' }}</el-descriptions-item>
              <el-descriptions-item label="客户编码">{{ detail.custcd || '-' }}</el-descriptions-item>
              <el-descriptions-item label="磁卡号">{{ detail.custcard || '-' }}</el-descriptions-item>
              <el-descriptions-item label="新磁卡号" v-if="detail.new_custcard">{{ detail.new_custcard }}</el-descriptions-item>
              <el-descriptions-item label="新客户" v-if="detail.new_custcd">{{ detail.new_custcd }} {{ detail.new_custnm || '' }}</el-descriptions-item>
              <el-descriptions-item label="地址">{{ detail.address || '-' }}</el-descriptions-item>
              <el-descriptions-item label="新地址" v-if="detail.new_address">{{ detail.new_address }}</el-descriptions-item>
              <el-descriptions-item label="联系人">{{ detail.contactor || '-' }}</el-descriptions-item>
              <el-descriptions-item label="电话">{{ detail.phoneno || '-' }}</el-descriptions-item>
              <el-descriptions-item label="经理">{{ detail.jl_contactor || '-' }}</el-descriptions-item>
              <el-descriptions-item label="经理电话">{{ detail.jl_phoneno || '-' }}</el-descriptions-item>
              <el-descriptions-item label="计划类型">{{ plLabel(detail.plantyp) }}</el-descriptions-item>
              <el-descriptions-item label="业务类型">{{ bsLabel(detail.busityp) || detail.busityp || '-' }}</el-descriptions-item>
              <el-descriptions-item label="设备来源">{{ detail.pos_from || '-' }}</el-descriptions-item>
              <el-descriptions-item label="机型">{{ detail.pos_item || '-' }}</el-descriptions-item>
              <el-descriptions-item label="押金">{{ detail.deposit ? '¥'+Number(detail.deposit).toLocaleString() : '-' }}</el-descriptions-item>
              <el-descriptions-item label="租赁">{{ detail.is_rent==='Y'?'租赁':'购买' }}</el-descriptions-item>
              <el-descriptions-item label="合同">{{ detail.is_contract==='1'?'是':'否' }}</el-descriptions-item>
              <el-descriptions-item label="运营类型">{{ detail.yun_type || '-' }}</el-descriptions-item>
              <el-descriptions-item label="下游单据">{{ detail.imple_billid || '未生成' }}</el-descriptions-item>
              <el-descriptions-item label="出库标志">{{ detail.is_outflag==='1'?'已出库':'未出库' }}</el-descriptions-item>
              <el-descriptions-item label="服务工程师">{{ detail.serve_ercd || '-' }}</el-descriptions-item>
              <el-descriptions-item label="创建日期">{{ detail.gendate || '-' }}</el-descriptions-item>
              <el-descriptions-item label="操作员">{{ detail.opercd || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <el-tab-pane label="呼出记录" name="serve">
            <el-table :data="serveRecords" size="small" v-loading="serveLoading" empty-text="暂无呼出记录">
              <el-table-column prop="servetyp" label="类型" width="80"><template #default="{row}">{{ ['客户确认','预计划呼出','实施任务'][Number(row.servetyp)]||row.servetyp }}</template></el-table-column>
              <el-table-column prop="serve_task" label="任务" min-width="100" show-overflow-tooltip />
              <el-table-column prop="serve_back" label="呼出结果" width="80"><template #default="{row}"><el-tag :type="{Y:'success',N:'danger',O:'warning'}[row.serve_back]||'info'" size="small">{{ {Y:'同意',N:'不同意',O:'未接通'}[row.serve_back]||row.serve_back||'-' }}</el-tag></template></el-table-column>
              <el-table-column prop="serve_mark" label="客户反馈" min-width="120" show-overflow-tooltip />
              <el-table-column prop="commmode" label="通讯方式" width="80" />
              <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='01'?'success':row.status==='09'?'danger':'info'" size="small">{{ {00:'待呼出',01:'已呼出',09:'已作废'}[row.status]||row.status }}</el-tag></template></el-table-column>
              <el-table-column prop="gendate" label="日期" width="90" />
              <el-table-column prop="genercd" label="操作员" width="70" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="当前设备" name="device">
            <el-table :data="custDevices" size="small" v-loading="deviceLoading" empty-text="暂无设备信息">
              <el-table-column prop="eid" label="设备EID" width="130" />
              <el-table-column prop="itemcd" label="物料编码" width="80" />
              <el-table-column label="EID状态" width="70"><template #default="{row}">{{ {0:'新品',1:'已使用',2:'报废',3:'待检',5:'返修中',7:'生产中',8:'在库',S:'已售'}[row.sflg]||row.sflg }}</template></el-table-column>
              <el-table-column label="质检" width="60"><template #default="{row}"><el-tag size="small" :type="row.qcflg==='GA'?'success':'info'">{{ row.qcflg||'-' }}</el-tag></template></el-table-column>
              <el-table-column prop="whcd" label="仓库" width="60" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="历史设备" name="history">
            <el-table :data="deviceHistory" size="small" v-loading="historyLoading" empty-text="暂无历史记录">
              <el-table-column prop="change_type" label="变更类型" width="90" />
              <el-table-column prop="old_eid" label="旧值" min-width="100" show-overflow-tooltip />
              <el-table-column prop="new_eid" label="新值" min-width="100" show-overflow-tooltip />
              <el-table-column prop="change_date" label="变更日期" width="90" />
            </el-table>
          </el-tab-pane>
        </el-tabs>

        <!-- 操作区 -->
        <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">
          <el-button v-if="detail.plan_status==='00'" type="success" size="small" @click="doTransition(detail,'02')">确认呼出</el-button>
          <el-button v-if="detail.plan_status==='02'" type="warning" size="small" @click="doImplement(detail)">实施确认（生成下游单据）</el-button>
          <el-button v-if="detail.plan_status==='04'" type="primary" size="small" @click="doOutbound(detail)">生成出库单(OV=1)</el-button>
          <el-button v-if="detail.plan_status==='04'" type="success" size="small" @click="doComplete(detail)">完成（客户转正）</el-button>
          <el-button v-if="vCan(detail)" type="danger" size="small" @click="doVoid(detail)">作废</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 新建/编辑对话框 -->
    <el-dialog :title="isEdit?'编辑预计划':'新建预计划'" v-model="dialogVisible" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="客户名称"><el-input v-model="form.custnm"/></el-form-item>
        <el-form-item label="磁卡号"><el-input v-model="form.custcard"/></el-form-item>
        <el-form-item label="客户编码"><el-input v-model="form.custcd"/></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contactor"/></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phoneno"/></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address"/></el-form-item>
        <el-form-item label="计划类型"><el-select v-model="form.plantyp" style="width:100%"><el-option v-for="o in plOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item>
        <el-form-item label="租赁/购买"><el-radio-group v-model="form.is_rent"><el-radio value="Y">租赁</el-radio><el-radio value="N">购买</el-radio></el-radio-group></el-form-item>
        <el-form-item label="机型"><el-input v-model="form.pos_item" placeholder="POS物料编码"/></el-form-item>
        <el-form-item label="押金金额"><el-input-number v-model="form.deposit" :min="0" :precision="2" style="width:100%" controls-position="right"/></el-form-item>
        <el-form-item label="运营类型"><el-input v-model="form.yun_type" placeholder="运营类型编码"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="handleSave" :loading="saving">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useUserNames } from '@/composables/useUserNames'
import { useDict } from '@/composables/useDict'
import {
  fetchPlans, createPlan, updatePlan,
  transitionPlan, implementPlan, completePlan, voidPlan, createOutbound,
  fetchPlanServes,
} from '@/api/sales'
import type { PlanRecord, ServeRecord } from '@/api/sales'
import request from '@/api/request'

const { userName } = useUserNames()
const { dictLabel: plLabel } = useDict('PL')
const { dictLabel: bsLabel } = useDict('BT')

// PL 码表作为下拉选项（兜底硬编码）
const plOptions = [
  { value: '00', label: '新机开通' }, { value: '10', label: '设备变更' },
  { value: '20', label: '旧机翻新' }, { value: '30', label: '设备取回' },
  { value: '40', label: '门店关闭' },
]

// 状态标签映射 (对齐 PB plan_cust.status: 00/01/02/04/09)
function statusLabel(s: string) {
  const m: Record<string, string> = { '00': '计划中', '01': '计划完成', '02': '分派中', '03': '实施完成', '04': '实施中', '08': '计划退回', '09': '计划作废' }
  return m[s] || s
}
function statusTag(s: string) {
  const m: Record<string, string> = { '00': 'info', '01': 'success', '02': 'warning', '03': 'primary', '04': '', '08': 'danger', '09': 'danger' }
  return m[s] || 'info'
}
// 客户生命周期标签
function custLabel(row: PlanRecord) {
  const s = row.plan_status
  if (s === '09') return '已失效'
  if (s === '01') return '正式'
  if (s === '00') return '临时'
  return '进行中'
}
function custTag(row: PlanRecord) {
  const s = row.plan_status
  if (s === '09') return 'danger'
  if (s === '01') return 'success'
  if (s === '00') return 'info'
  return 'warning'
}
// 可作废的状态
function vCan(row: PlanRecord) { return ['00', '02', '03', '04', '08'].includes(row.plan_status || '') }

// 列表
const plans = ref<PlanRecord[]>([]); const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const searchPlanno = ref(''); const searchCustNm = ref(''); const searchStatus = ref('')
const searchCustcard = ref(''); const searchPlantyp = ref('')
const searchDateFrom = ref(''); const searchDateTo = ref('')
const searchServeStatus = ref('')

watch(page, () => loadData()); watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => loadData())

function onReset() {
  searchPlanno.value = ''; searchCustNm.value = ''; searchStatus.value = ''
  searchCustcard.value = ''; searchPlantyp.value = ''
  searchDateFrom.value = ''; searchDateTo.value = ''; searchServeStatus.value = ''
  page.value = 1; loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, string> = { page: String(page.value), per_page: String(perPage.value) }
    if (searchPlanno.value) params.planno = searchPlanno.value
    if (searchCustNm.value) params.custnm = searchCustNm.value
    if (searchStatus.value) params.plan_status = searchStatus.value
    if (searchCustcard.value) params.custcard = searchCustcard.value
    if (searchPlantyp.value) params.plantyp = searchPlantyp.value
    if (searchDateFrom.value) params.date_from = searchDateFrom.value
    if (searchDateTo.value) params.date_to = searchDateTo.value
    if (searchServeStatus.value) params.serve_status = searchServeStatus.value
    const res = await fetchPlans(params)
    plans.value = res.data.items || []; total.value = res.data.total || 0
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function onSearch() { page.value = 1; loadData() }

// 对话框
const dialogVisible = ref(false); const isEdit = ref(false)
const form = reactive<PlanRecord & { deposit?: number; is_rent?: string; yun_type?: string; pos_item?: string }>({
  planno: '', custnm: '', custcard: '', custcd: '', plantyp: '00', plan_status: '00',
  is_rent: 'N', deposit: 0, yun_type: '', pos_item: '',
})
const saving = ref(false)

function openEdit(row: PlanRecord) { isEdit.value = true; Object.assign(form, { ...row, deposit: Number(row.deposit) || 0 }); dialogVisible.value = true }
function openCreate() { isEdit.value = false; Object.assign(form, { planno: '', custnm: '', custcard: '', custcd: '', plantyp: '00', plan_status: '00', is_rent: 'N', deposit: 0, yun_type: '', pos_item: '' }); dialogVisible.value = true }

async function handleSave() {
  saving.value = true
  try {
    const payload: Record<string, unknown> = { custnm: form.custnm, custcard: form.custcard, custrnm: form.custrnm, address: form.address, contactor: form.contactor, phoneno: form.phoneno, plantyp: form.plantyp, busityp: form.busityp, is_rent: form.is_rent, deposit: form.deposit, yun_type: form.yun_type, pos_item: form.pos_item }
    if (isEdit.value) { await updatePlan(form.planno, payload) } else { await createPlan({ custcd: form.custcd, ...payload }) }
    dialogVisible.value = false; loadData(); ElMessage.success('保存成功')
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

// 详情抽屉
const drawerVisible = ref(false); const detail = ref<PlanRecord | null>(null); const detailTab = ref('info')
const serveRecords = ref<ServeRecord[]>([]); const serveLoading = ref(false)
const custDevices = ref<any[]>([]); const deviceLoading = ref(false)
const deviceHistory = ref<any[]>([]); const historyLoading = ref(false)

async function openDetail(row: PlanRecord) {
  detail.value = row; drawerVisible.value = true; detailTab.value = 'info'
  serveLoading.value = true
  try {
    const res = await fetchPlanServes(row.planno)
    serveRecords.value = (res.data as ServeRecord[]) || []
  } catch { serveRecords.value = [] }
  finally { serveLoading.value = false }

  // 当前设备：客户当前有效的门店设备 (cust_cd)
  if (row.custcd) {
    deviceLoading.value = true
    try {
      const r = await request.get('/assets', { params: { cust_cd: row.custcd, useflg: '1', per_page: 100 } }) as any
      custDevices.value = (r?.data?.items || []).map((a: any) => ({
        eid: a.eid, itemcd: a.item_cd || a.itemcd, sflg: a.sflg, qcflg: a.qcflg, whcd: a.whcd,
      }))
    } catch { custDevices.value = [] }
    finally { deviceLoading.value = false }

    // 历史设备：预计划关联的设备(取回/变更) + EID追溯
    historyLoading.value = true
    try {
      const posid = row.posid
      const posItem = row.pos_item || ''
      if (posid && posItem) {
        const t = await request.get(`/eid/${posItem}/${posid}/tracks`) as any
        deviceHistory.value = (t?.data || []).map((tr: any) => ({
          change_type: tr.type, old_eid: tr.from_value, new_eid: tr.to_value, change_date: tr.gendate || tr.update_time,
        }))
      } else {
        deviceHistory.value = []
      }
    } catch { deviceHistory.value = [] }
    finally { historyLoading.value = false }
  } else {
    custDevices.value = []; deviceHistory.value = []
  }
}

// 状态操作
async function doTransition(row: PlanRecord, to: string) {
  try {
    await transitionPlan(row.planno, to)
    ElMessage.success(`已流转到 ${statusLabel(to)}`)
    loadData()
  } catch { ElMessage.error('操作失败') }
}
async function doImplement(row: PlanRecord) {
  try {
    await ElMessageBox.confirm(`确认实施？将为预计划 ${row.planno} 生成下游单据。`, '实施确认', { type: 'warning' })
    const res = await implementPlan(row.planno)
    const dsid = (res.data as any)?.downstream_id || ''
    ElMessage.success(`实施确认成功，下游单据: ${dsid}`)
    loadData()
  } catch { /* 取消 */ }
}
async function doOutbound(row: PlanRecord) {
  try {
    await ElMessageBox.confirm(`为预计划 ${row.planno} 生成 OV=1 销售出库草稿？`, '生成出库单', { type: 'info' })
    const res = await createOutbound(row.planno, '04')
    const obid = (res.data as any)?.outbillid || ''
    ElMessage.success(`出库单已创建: ${obid}`)
    loadData()
  } catch { /* 取消 */ }
}
async function doComplete(row: PlanRecord) {
  try {
    await ElMessageBox.confirm(`确认完成？客户将从待确认转为正式客户。`, '完成确认', { type: 'warning' })
    await completePlan(row.planno)
    ElMessage.success('已完成，客户已转正')
    loadData()
  } catch { /* 取消 */ }
}
async function doVoid(row: PlanRecord) {
  try {
    const { value: remark } = await ElMessageBox.prompt('作废原因（可选）', '作废预计划', { inputType: 'text' })
    await voidPlan(row.planno, remark || undefined)
    ElMessage.success('已作废')
    loadData()
  } catch { /* 取消 */ }
}
</script>

<style scoped>
.plan-page { padding: 0 }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px }
.page-header h2 { font-size:18px; font-weight:600; margin:0 }
.search-bar { display:flex; gap:12px; flex-wrap:wrap; align-items:center }
.field { display:flex; align-items:center; gap:6px }
.field label { font-size:13px; color:#606266; white-space:nowrap }
</style>
