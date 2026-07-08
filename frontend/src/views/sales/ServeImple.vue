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
      <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
        <span style="color:#606266;font-size:13px">批量出库：勾选多个商用仓库且待出库的预计划，合并生成一个 OV=1 出库单（方案B）</span>
        <el-button type="primary" size="small" :disabled="batchPicked.length===0" @click="openBatchOutbound">批量出库（{{ batchPicked.length }}）</el-button>
      </div>
      <el-table :data="items" v-loading="loading" stripe size="small" @selection-change="onSelectionChange" :row-key="(r: PlanRecord) => r.planno">
        <el-table-column type="selection" width="45" :selectable="canOutbound" reserve-selection />
        <el-table-column prop="planno" label="计划单号" width="110" />
        <el-table-column prop="custnm" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="custcard" label="磁卡号" width="100" />
        <el-table-column prop="contactor" label="联系人" width="80" />
        <el-table-column prop="phoneno" label="电话" width="110" />
        <el-table-column label="计划类型" width="80"><template #default="{row}">{{ plLabel(row.plantyp) }}</template></el-table-column>
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="statusTag(row.plan_status)" size="small">{{ statusLabel(row.plan_status) }}</el-tag></template></el-table-column>
        <el-table-column prop="imple_date" label="实施日期" width="100" :formatter="dateFmt" />
        <el-table-column prop="send_date" label="配送日期" width="100" :formatter="dateFmt" />
        <el-table-column prop="train_date" label="培训日期" width="100" :formatter="dateFmt" />
        <el-table-column label="呼出状态" width="90" align="center">
          <template #default="{row}">
            <el-tag v-if="row.latest_serve" :type="serveStatusTag(row.latest_serve.serve_status)" size="small">{{ serveStatusLabel(row.latest_serve.serve_status) }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="呼出要求" min-width="160" show-overflow-tooltip>
          <template #default="{row}">
            {{ row.latest_serve?.serve_task || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="呼出结果" width="90" align="center">
          <template #default="{row}">
            <el-tag v-if="row.latest_serve?.serve_back" :type="serveBackTag(row.latest_serve.serve_back)" size="small">{{ serveBackLabel(row.latest_serve.serve_back) }}</el-tag>
            <span v-else-if="row.latest_serve">-</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="反馈备注" min-width="160" show-overflow-tooltip>
          <template #default="{row}">
            {{ row.latest_serve?.serve_mark || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="出库标志" width="90" align="center">
          <template #default="{row}">
            <el-tag :type="outflagTag(row.is_outflag)" size="small">{{ outflagLabel(row.is_outflag) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{row}">
            <el-tooltip v-if="['02','04'].includes(row.plan_status)" :content="planBtnTip(row)" :disabled="!planBtnTip(row)" placement="top">
              <span class="impl-btn-wrap">
                <el-button link type="primary" size="small" :disabled="!canPlan(row)" @click="openPlan(row)">{{ planBtnLabel(row) }}</el-button>
              </span>
            </el-tooltip>
            <el-tooltip v-if="row.plan_status==='02'" :content="implBtnTip(row)" :disabled="!implBtnTip(row)" placement="top">
              <span class="impl-btn-wrap">
                <el-button link type="warning" size="small" :disabled="!canImplement(row)" @click="doImplement(row)">实施确认</el-button>
              </span>
            </el-tooltip>
            <el-button v-if="canOutbound(row)" link type="primary" size="small" @click="doOutbound(row)">出库</el-button>
            <el-button v-if="['00','02','04'].includes(row.plan_status)" link type="info" size="small" @click="openRequestServe(row)">请求呼出</el-button>
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

    <!-- 请求呼出对话框（计划任务呼出，servetyp=2，实施部） -->
    <el-dialog v-model="requestVisible" title="请求呼出（计划任务）" width="480px">
      <el-form :model="requestForm" label-width="90px">
        <el-form-item label="计划单号"><el-input :model-value="requestForm.planno" disabled /></el-form-item>
        <el-form-item label="呼出任务"><el-input v-model="requestForm.serve_task" type="textarea" :rows="2" placeholder="如:确认实施时间/配送地址" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="requestVisible=false">取消</el-button><el-button type="primary" :loading="requestSaving" @click="doRequestServe">请求呼出</el-button></template>
    </el-dialog>

    <!-- 方案 B：出库前 EID 选择对话框 -->
    <el-dialog :title="`选择出库设备 - 预计划 ${outboundEidPlanno}`" v-model="outboundEidDialog" width="800px">
      <div style="margin-bottom:10px;color:#606266;font-size:13px">
        机型：<b>{{ outboundEidModel }}</b>，请勾选要出库的设备 EID（方案 B：发货时绑定）
      </div>
      <el-table :data="outboundEidList" stripe size="small" max-height="400" @selection-change="(rows: any[]) => outboundEidPicked = rows.map(r => r.eid)">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="eid" label="设备 EID" width="160" />
        <el-table-column prop="whnm" label="所在仓库" width="120" />
        <el-table-column prop="asset_type_nm" label="资产类型" width="90" />
        <el-table-column prop="itemtyp_nm" label="品级" width="80" />
        <el-table-column prop="sflg" label="状态" width="60" />
      </el-table>
      <template #footer>
        <el-button @click="cancelOutboundEids">取消</el-button>
        <el-button type="primary" @click="confirmOutboundEids">确认出库</el-button>
      </template>
    </el-dialog>

    <!-- 批量出库对话框 -->
    <el-dialog v-model="batchDialog" title="批量出库" width="560px">
      <div style="margin-bottom:10px;color:#606266;font-size:13px">
        将以下 {{ batchPicked.length }} 个预计划合并生成一个 OV=1 销售出库草稿，出库明细行各自记 ref_planno。
      </div>
      <el-table :data="batchPicked" stripe size="small" max-height="300">
        <el-table-column prop="planno" label="计划单号" width="120" />
        <el-table-column prop="custnm" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column label="机型" width="80"><template #default="{row}">{{ row.pos_item || '-' }}</template></el-table-column>
        <el-table-column label="EID" min-width="120"><template #default="{row}">{{ row.posid || '未选（需在预计划中选定）' }}</template></el-table-column>
      </el-table>
      <div style="margin-top:10px;color:#e6a23c;font-size:12px">
        提示：批量出库仅支持已选 posid 的预计划（方案A预绑定）。未选 posid 的请单独出库并手动选 EID。
      </div>
      <template #footer>
        <el-button @click="batchDialog=false">取消</el-button>
        <el-button type="primary" :loading="batchSaving" @click="doBatchOutbound">确认批量出库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useDict } from '@/composables/useDict'
import { fetchPlans, updatePlan, implementPlan, createPlanServe, createOutbound, batchCreateOutbound, fetchAvailableEids, type PlanRecord, type AvailableEid } from '@/api/sales'

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
// 呼出单状态（00待呼出/01已呼出/09作废）
function serveStatusLabel(s: string) {
  const m: Record<string, string> = { '00': '待呼出', '01': '已呼出', '09': '作废' }
  return m[s] || s
}
function serveStatusTag(s: string) {
  const m: Record<string, string> = { '00': 'warning', '01': 'success', '09': 'info' }
  return m[s] || 'info'
}
// 呼出反馈结果（Y=同意/N=不同意/O=未接通）
function serveBackLabel(s: string) {
  const m: Record<string, string> = { Y: '同意', N: '不同意', O: '未接通' }
  return m[s] || s
}
function serveBackTag(s: string) {
  const m: Record<string, string> = { Y: 'success', N: 'danger', O: 'warning' }
  return m[s] || 'info'
}
// 出库标志三态（N/A=非商用仓库不适用 / 0=待出库 / 1=已出库）
function outflagLabel(v: unknown) {
  const s = String(v ?? '')
  const m: Record<string, string> = { 'N/A': '不适用', '0': '待出库', '1': '已出库' }
  return m[s] ?? (s || '-')
}
function outflagTag(v: unknown) {
  const s = String(v ?? '')
  const m: Record<string, string> = { 'N/A': 'info', '0': 'warning', '1': 'success' }
  return m[s] ?? 'info'
}
// 出库按钮可用：实施中(04) + 商用仓库来源(pos_from='00') + 待出库(is_outflag='0')
function canOutbound(row: PlanRecord) {
  return row.plan_status === '04'
    && String(row.pos_from ?? '') === '00'
    && String(row.is_outflag ?? '') === '0'
}

// 批量出库选择
const batchPicked = ref<PlanRecord[]>([])
const batchDialog = ref(false)
const batchSaving = ref(false)
function onSelectionChange(rows: PlanRecord[]) {
  batchPicked.value = rows
}
function openBatchOutbound() {
  if (batchPicked.value.length === 0) {
    ElMessage.warning('请至少选择一个预计划')
    return
  }
  // 校验：所有选中行必须已选 posid（方案A预绑定）
  const missing = batchPicked.value.filter(r => !r.posid)
  if (missing.length > 0) {
    ElMessage.warning(`以下预计划未选 posid，无法批量出库：${missing.map(r => r.planno).join(', ')}`)
    return
  }
  batchDialog.value = true
}
async function doBatchOutbound() {
  batchSaving.value = true
  try {
    const items = batchPicked.value.map(r => ({ planno: r.planno }))
    const res = await batchCreateOutbound('04', items)
    const obid = (res.data as any)?.outbillid || ''
    const cnt = (res.data as any)?.planno_count || 0
    ElMessage.success(`出库单 ${obid} 已创建，含 ${cnt} 个预计划`)
    batchDialog.value = false
    batchPicked.value = []
    loadData()
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || '批量出库失败'
    ElMessage.error(msg)
  } finally { batchSaving.value = false }
}

watch(page, () => loadData()); watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, string> = { page: String(page.value), per_page: String(perPage.value) }
    // 计划实施管理只显示已确认（02及之后）的单据，排除 00 计划中（仍在预计划管理阶段）
    params.exclude_plan_status = '00'
    if (searchStatus.value) params.plan_status = searchStatus.value
    if (searchPlanno.value) params.planno = searchPlanno.value
    if (searchCustNm.value) params.custnm = searchCustNm.value
    const res = await fetchPlans(params)
    items.value = res.data.items || []; total.value = res.data.total || 0
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function onSearch() { page.value = 1; loadData() }

// 日期格式化：截取 yyyy-mm-dd（后端返回 ISO 格式 2026-07-08T00:00:00）
function dateFmt(_row: any, _col: any, cellValue: unknown) {
  if (!cellValue) return '-'
  const s = String(cellValue)
  return s.length >= 10 ? s.slice(0, 10) : s
}

// 制定计划/实施确认 按钮文案与禁用规则
function planBtnLabel(row: PlanRecord) {
  return row.imple_date ? '修改计划' : '制定计划'
}
function planBtnTip(row: PlanRecord) {
  if (row.has_pending_imp_serve) return '存在未完成的实施请求呼出单，请先在呼出管理中完成反馈'
  if (!row.imple_date) return '请先填写实施日期后再进行实施确认'
  return ''
}
function canPlan(row: PlanRecord) {
  // 制定计划可用：无未完成的实施请求呼出单
  return !row.has_pending_imp_serve
}
function canImplement(row: PlanRecord) {
  // 实施确认可用：imple_date 已填 且 无未完成的实施请求呼出单
  return !!row.imple_date && !row.has_pending_imp_serve
}
function implBtnTip(row: PlanRecord) {
  if (row.has_pending_imp_serve) return '存在未完成的实施请求呼出单，请先在呼出管理中完成反馈'
  if (!row.imple_date) return '请先完成"制定计划"填写实施日期后再进行实施确认'
  return ''
}

// 制定计划
const planVisible = ref(false); const planForm = ref({ planno: '', imple_date: '', send_date: '', train_date: '', imple_mark: '' }); const planSaving = ref(false)
function openPlan(row: PlanRecord) {
  planForm.value = {
    planno: row.planno,
    imple_date: (row.imple_date as string) || '',
    send_date: (row.send_date as string) || '',
    train_date: (row.train_date as string) || '',
    imple_mark: (row.imple_mark as string) || '',
  }
  planVisible.value = true
}
async function doSavePlan() {
  planSaving.value = true
  try {
    await updatePlan(planForm.value.planno, { imple_date: planForm.value.imple_date, send_date: planForm.value.send_date, train_date: planForm.value.train_date, imple_mark: planForm.value.imple_mark })
    planVisible.value = false; loadData(); ElMessage.success('已保存')
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || '保存失败'
    ElMessage.error(msg)
  } finally { planSaving.value = false }
}

// 请求呼出（计划任务呼出，servetyp=2，实施部）
const requestVisible = ref(false)
const requestForm = ref({ planno: '', serve_task: '' })
const requestSaving = ref(false)
function openRequestServe(row: PlanRecord) {
  requestForm.value = {
    planno: row.planno,
    serve_task: `实施任务呼出-${row.planno}`,
  }
  requestVisible.value = true
}
async function doRequestServe() {
  if (!requestForm.value.serve_task.trim()) { ElMessage.warning('请输入呼出任务'); return }
  requestSaving.value = true
  try {
    await createPlanServe(requestForm.value.planno, {
      servetyp: '2',
      serve_task: requestForm.value.serve_task,
    })
    requestVisible.value = false
    loadData()
    ElMessage.success('已生成计划任务呼出单')
  } catch { ElMessage.error('请求呼出失败') }
  finally { requestSaving.value = false }
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

// 出库：生成 OV=1 销售出库草稿
async function doOutbound(row: PlanRecord) {
  try {
    await ElMessageBox.confirm(`为预计划 ${row.planno} 生成 OV=1 销售出库草稿？`, '生成出库单', { type: 'info' })
    // 方案 A（posid 已选）：直接创建出库单，后端从 posid 自动带 EID
    // 方案 B（posid 未选）：弹出 EID 选择对话框，由仓库人扫码选择
    let eids: string[] | undefined
    if (!row.posid && row.pos_item) {
      const picked = await pickEidsForOutbound(row.pos_item, row.planno)
      if (!picked) return  // 用户取消
      eids = picked
    }
    const res = await createOutbound(row.planno, '04', eids)
    const obid = (res.data as any)?.outbillid || ''
    ElMessage.success(`出库单已创建: ${obid}`)
    loadData()
  } catch { /* 取消 */ }
}

// 方案 B：出库前 EID 选择对话框
const outboundEidDialog = ref(false)
const outboundEidList = ref<AvailableEid[]>([])
const outboundEidPicked = ref<string[]>([])
const outboundEidPlanno = ref('')
const outboundEidModel = ref('')
async function pickEidsForOutbound(modelCd: string, planno: string): Promise<string[] | null> {
  outboundEidPlanno.value = planno
  outboundEidModel.value = modelCd
  outboundEidPicked.value = []
  outboundEidDialog.value = true
  // 加载该机型可用 EID
  try {
    const r = await fetchAvailableEids({ model_cd: modelCd, per_page: 200 })
    outboundEidList.value = (r?.data?.items || []) as any
  } catch { outboundEidList.value = [] }
  // 等待用户确认/取消（通过 Promise + 闭包变量模拟同步）
  return new Promise((resolve) => {
    const check = setInterval(() => {
      if (!outboundEidDialog.value) {
        clearInterval(check)
        resolve(outboundEidPicked.value.length > 0 ? [...outboundEidPicked.value] : null)
      }
    }, 200)
  })
}
function confirmOutboundEids() {
  if (outboundEidPicked.value.length === 0) {
    ElMessage.warning('请至少选择一台设备')
    return
  }
  outboundEidDialog.value = false
}
function cancelOutboundEids() {
  outboundEidPicked.value = []
  outboundEidDialog.value = false
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
