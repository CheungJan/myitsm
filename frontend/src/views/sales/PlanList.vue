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
            <el-button v-if="row.plan_status==='00'" link type="info" size="small" @click="doRequestServe(row)">请求呼出</el-button>
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
    <el-drawer v-model="drawerVisible" title="预计划详情" size="780px">
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
            <el-table :data="custDevices" size="small" v-loading="deviceLoading" empty-text="暂无设备信息"
              row-key="_id" :tree-props="{ children: 'children', hasChildren: 'hasChildren' }" :indent="24" default-expand-all>
              <el-table-column prop="eid" label="EID" width="130" />
              <el-table-column label="物料编码/名称" min-width="220">
                <template #default="{row}">
                  <span>{{ row.itemcd }}</span>
                  <span style="color:#909399;margin-left:8px">{{ row.itemnm || '' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="80">
                <template #default="{row}">
                  <el-tag v-if="row.isPos" size="small" :type="row.useflg==='1'?'success':'danger'">{{ row.useflg==='1'?'在用':'已失效' }}</el-tag>
                  <el-tag v-else size="small" :type="row.useflg==='1'?'success':'danger'">{{ row.useflg==='1'?'有效':'失效' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="upddate" label="更新日期" width="100" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="历史设备" name="history">
            <el-table :data="deviceHistory" size="small" v-loading="historyLoading" empty-text="暂无历史记录">
              <el-table-column prop="eid" label="设备EID" width="130" />
              <el-table-column prop="itemcd" label="物料编码" width="80" />
              <el-table-column prop="itemnm" label="物料名称" min-width="120" show-overflow-tooltip />
              <el-table-column prop="sysinfo" label="系统信息" width="100" show-overflow-tooltip />
              <el-table-column prop="softinfo" label="软件版本" width="100" show-overflow-tooltip />
              <el-table-column prop="posinfo" label="POS信息" width="100" show-overflow-tooltip />
              <el-table-column label="状态" width="70"><template #default="{row}"><el-tag size="small" :type="row.useflg==='1'?'success':'danger'">{{ row.useflg==='1'?'有效':'失效' }}</el-tag></template></el-table-column>
              <el-table-column prop="upddate" label="更新日期" width="90" />
            </el-table>
          </el-tab-pane>
        </el-tabs>

      </template>
    </el-drawer>

    <!-- 新建/编辑对话框 -->
    <el-dialog :title="isEdit?'编辑预计划':'新建预计划'" v-model="dialogVisible" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="计划类型"><el-select v-model="form.plantyp" style="width:100%" @change="onPlantypChange"><el-option v-for="o in plOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item>
        <el-form-item label="客户名称"><el-input v-model="form.custnm"/></el-form-item>
        <el-form-item label="磁卡号"><el-input v-model="form.custcard"/></el-form-item>
        <el-form-item label="客户编码"><el-input v-model="form.custcd"/></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contactor"/></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phoneno"/></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address"/></el-form-item>
        <el-form-item v-if="showPosFrom" label="设备来源"><el-select v-model="form.pos_from" style="width:100%" @change="onPosFromChange"><el-option label="建议机型" value="00"/><el-option label="移机" value="01"/><el-option label="返修重开" value="02"/></el-select></el-form-item>
        <el-form-item label="租赁/购买"><el-radio-group v-model="form.is_rent"><el-radio value="Y">租赁</el-radio><el-radio value="N">购买</el-radio></el-radio-group></el-form-item>
        <el-form-item v-if="showModelSelect" label="机型"><el-select v-model="form.pos_item" filterable clearable placeholder="选择机型" style="width:100%" @change="onModelSelect"><el-option v-for="m in modelOptions" :key="m.model_cd" :label="`${m.model_cd} ${m.model_nm}`" :value="m.model_cd"/></el-select></el-form-item>
        <el-form-item v-if="!showModelSelect && showPosItem" label="机型"><el-input v-model="form.pos_item" placeholder="POS物料编码"/></el-form-item>
        <el-form-item v-if="showPosid" label="设备EID"><el-input v-model="form.posid" placeholder="设备EID"/></el-form-item>
        <el-form-item label="押金金额"><el-input-number v-model="form.deposit" :min="0" :precision="2" style="width:100%" controls-position="right"/></el-form-item>
        <el-form-item label="运营类型"><el-input v-model="form.yun_type" placeholder="运营类型编码"/></el-form-item>
        <el-form-item v-if="showNewFields" label="新磁卡号"><el-input v-model="form.new_custcard"/></el-form-item>
        <el-form-item v-if="showNewFields" label="新客户编码"><el-input v-model="form.new_custcd"/></el-form-item>
        <el-form-item v-if="showNewFields" label="新客户名称"><el-input v-model="form.new_custnm"/></el-form-item>
        <el-form-item v-if="showNewFields" label="新地址"><el-input v-model="form.new_address"/></el-form-item>
        <el-form-item v-if="showNewFields" label="新电话"><el-input v-model="form.new_phoneno"/></el-form-item>
        <el-form-item v-if="showCustUseflg" label="门店无效"><el-switch v-model="form.cust_useflg" active-value="1" inactive-value="0" active-text="是" inactive-text="否"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="handleSave" :loading="saving">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useUserNames } from '@/composables/useUserNames'
import { useDict } from '@/composables/useDict'
import {
  fetchPlans, createPlan, updatePlan,
  transitionPlan, implementPlan, completePlan, voidPlan, createOutbound,
  fetchPlanServes, createPlanServe,
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

// 机型下拉选项(从 DepositPosModel useflg='1' 读取)
const modelOptions = ref<{ model_cd: string; model_nm: string; rent_money: number }[]>([])
async function loadModels() {
  try { const r = await request.get<never,{data:any[]}>('/deposit/pos-models'); modelOptions.value = (r?.data||[]).filter((m:any)=>m.useflg==='1') } catch { modelOptions.value = [] }
}

// 表单字段条件显隐（按 plantyp + pos_from 联动）
const showPosFrom = computed(() => ['00','10','20'].includes(form.plantyp))
const showPosItem = computed(() => { if (['30','40'].includes(form.plantyp)) return true; if (form.plantyp==='10') return false; if (form.plantyp==='20') return true; return form.pos_from!=='00' })
const showPosid = computed(() => showPosItem.value)
const showModelSelect = computed(() => modelOptions.value.length>0 && (['30','40'].includes(form.plantyp) || (['00','20'].includes(form.plantyp) && form.pos_from!=='00')))
const showNewFields = computed(() => { if (form.plantyp==='10') return true; if (['00','20'].includes(form.plantyp)) return form.pos_from==='01'||form.pos_from==='02'; return false })
const showCustUseflg = computed(() => { if (form.plantyp==='30') return true; if (form.plantyp==='10') return false; if (['00','20'].includes(form.plantyp)) return form.pos_from==='01'||form.pos_from==='02'; return false })
function onPlantypChange() { form.pos_from=''; form.cust_useflg='0' }
function onPosFromChange() { if (form.pos_from==='00') form.cust_useflg='0' }
function onModelSelect(val: string) { const m = modelOptions.value.find(x=>x.model_cd===val); if (m) form.deposit = m.rent_money||0 }

// 状态标签映射 (对齐 PB plan_cust.status: 00/01/02/04/09)
function statusLabel(s: string) {
  const m: Record<string, string> = { '00': '计划中', '01': '计划完成', '02': '分派中', '03': '实施完成', '04': '实施中', '08': '计划退回', '09': '计划作废' }
  return m[s] || s
}
function statusTag(s: string) {
  const m: Record<string, string> = { '00': 'info', '01': 'success', '02': 'warning', '03': 'primary', '04': '', '08': 'danger', '09': 'danger' }
  return m[s] || 'info'
}
// 客户生命周期标签 — 优先读 customer_status(后端API新增字段)
function custLabel(row: PlanRecord) {
  const cs = row.customer_status as string
  if (cs === 'TEMP') return '临时'
  if (cs === 'PENDING') return '待确认'
  if (cs === 'ACTIVE') return '正式'
  if (cs === 'INVALID') return '已失效'
  // fallback: 从 plan_status 推断
  const s = row.plan_status
  if (s === '09') return '已失效'
  if (s === '01') return '正式'
  if (s === '00') return '待确认'
  return '正式'
}
function custTag(row: PlanRecord) {
  const cs = row.customer_status as string
  if (cs === 'TEMP') return 'info'
  if (cs === 'PENDING') return 'warning'
  if (cs === 'ACTIVE') return 'success'
  if (cs === 'INVALID') return 'danger'
  const s = row.plan_status
  if (s === '09') return 'danger'
  if (s === '01') return 'success'
  return 'info'
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
onMounted(() => { loadData(); loadModels() })

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

  // 当前设备：对齐 PB d_plan_bom_dtl，按 pos_eid 分组成树形
  deviceLoading.value = true
  try {
    const r = await request.get(`/sales/plans/${row.planno}/devices/current`) as any
    const rows = (r?.data || []) as any[]
    // 按 pos_eid 分组，POS 为父行，配件为子行
    const posMap = new Map<string, { pos: any; accessories: any[] }>()
    for (const d of rows) {
      const key = d.pos_eid || '__nopos__'
      if (!posMap.has(key)) {
        posMap.set(key, {
          pos: { eid: d.pos_eid, itemcd: d.pos_itemcd, itemnm: d.pos_itemnm, useflg: d.pos_useflg, upddate: d.upddate },
          accessories: [],
        })
      }
      if (d.acc_eid && d.acc_useflg === '1') {
        posMap.get(key)!.accessories.push({ eid: d.acc_eid, itemcd: d.acc_itemcd, itemnm: d.acc_itemnm || '', useflg: d.acc_useflg, upddate: d.upddate })
      }
    }
    // 构建树形数据
    const tree: any[] = []
    let id = 0
    for (const [, v] of posMap) {
      const parent = { _id: ++id, eid: v.pos.eid, itemcd: v.pos.itemcd, itemnm: v.pos.itemnm, isPos: true, useflg: v.pos.useflg, upddate: v.pos.upddate, children: [] as any[], hasChildren: v.accessories.length > 0 }
      for (const acc of v.accessories) {
        parent.children.push({ _id: ++id, eid: acc.eid, itemcd: acc.itemcd, itemnm: acc.itemnm, isPos: false, useflg: acc.useflg, upddate: acc.upddate })
      }
      tree.push(parent)
    }
    custDevices.value = tree
  } catch { custDevices.value = [] }
  finally { deviceLoading.value = false }

  // 历史设备：对齐 PB d_plan_bom_lst（tmm35_cust_pos_rl 所有记录含失效）
  historyLoading.value = true
  try {
    const r = await request.get(`/sales/plans/${row.planno}/devices/history`) as any
    deviceHistory.value = (r?.data || []).map((d: any) => ({
      itemcd: d.itemcd, itemnm: d.itemnm, eid: d.eid,
      sysinfo: d.sysinfo, softinfo: d.softinfo, posinfo: d.posinfo,
      upddate: d.upddate, useflg: d.useflg,
    }))
  } catch { deviceHistory.value = [] }
  finally { historyLoading.value = false }
}

// 状态操作
async function doRequestServe(row: PlanRecord) {
  try {
    const res = await createPlanServe(row.planno, { servetyp: '1', serve_task: `预计划呼出-${row.planno}` })
    ElMessage.success(`呼出单已创建`)
    loadData()
  } catch { ElMessage.error('请求呼出失败') }
}
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
