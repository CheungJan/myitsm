<template>
  <div class="page">
    <div class="page-header"><h2>呼出管理</h2><div class="header-tip">主行 = 计划公有信息（不重复），展开 = 呼出记录明细（类型标签区分）</div></div>

    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>呼出类型</label><el-select v-model="searchServetyp" size="small" style="width:130px" clearable placeholder="全部">
          <el-option label="预计划呼出" value="1" /><el-option label="实施任务呼出" value="2" /></el-select></div>
        <div class="field"><label>计划单号</label><el-input v-model="searchPlanno" placeholder="输入单号" size="small" style="width:140px" clearable /></div>
        <div class="field"><label>客户名称</label><el-input v-model="searchCustnm" placeholder="输入客户" size="small" style="width:140px" clearable /></div>
        <div class="field"><label>磁卡号</label><el-input v-model="searchCustcard" placeholder="输入磁卡号" size="small" style="width:140px" clearable /></div>
        <div class="field"><label>呼出状态</label><el-select v-model="searchServeStatus" size="small" style="width:110px" clearable placeholder="全部">
          <el-option label="待呼出" value="00" /><el-option label="已呼出" value="01" /></el-select></div>
        <div class="field"><label>分配呼出人</label><el-select v-model="searchServeErcd" size="small" style="width:160px" clearable filterable placeholder="全部">
          <el-option v-for="u in userOptions" :key="u.user_cd" :label="`${u.user_cd} - ${u.user_nm}`" :value="u.user_cd" /></el-select></div>
        <div class="field"><label>计划状态</label><el-select v-model="searchPlanStatus" size="small" style="width:110px" clearable placeholder="全部">
          <el-option label="计划中" value="00" /><el-option label="计划完成" value="01" />
          <el-option label="分派中" value="02" /><el-option label="实施完成" value="03" />
          <el-option label="实施中" value="04" /><el-option label="计划退回" value="08" /></el-select></div>
        <el-button type="primary" size="small" @click="onSearch">查询</el-button>
        <el-button size="small" @click="onReset">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" row-key="planno" :expand-row-keys="expandedKeys" @expand-change="onExpandChange">
        <el-table-column type="expand">
          <template #default="{row}">
            <div class="expand-wrap">
              <el-table :data="rowServes(row.planno)" size="small" v-loading="serveLoading" empty-text="暂无呼出记录" style="width:100%">
                <el-table-column label="类型" width="100"><template #default="{row:s}">
                  <el-tag size="small" :type="s.servetyp==='1'?'warning':s.servetyp==='2'?'success':'info'">{{ ['客户确认','预计划呼出','实施任务'][Number(s.servetyp)]||s.servetyp }}</el-tag>
                </template></el-table-column>
                <el-table-column prop="serve_task" label="计划要求" width="160" show-overflow-tooltip />
                <el-table-column label="呼出状态" width="76"><template #default="{row:s}"><el-tag :type="s.status==='01'?'success':s.status==='09'?'danger':'warning'" size="small">{{ ({'00':'待呼出','01':'已呼出','09':'已作废'} as Record<string, string>)[s.status] }}</el-tag></template></el-table-column>
                <el-table-column label="反馈结果" width="70"><template #default="{row:s}"><el-tag v-if="s.serve_back" size="small" :type="({Y:'success',N:'danger',O:'warning'} as Record<string, string>)[s.serve_back]||'info'">{{ ({Y:'同意',N:'不同意',O:'未接通'} as Record<string, string>)[s.serve_back]||s.serve_back }}</el-tag><span v-else style="color:#c0c4cc">-</span></template></el-table-column>
                <el-table-column prop="serve_mark" label="客户反馈" width="200" show-overflow-tooltip />
                <el-table-column label="请求人" width="80"><template #default="{row:s}">{{ (s.genercd_nm as string) || (s.genercd as string) || '-' }}</template></el-table-column>
                <el-table-column label="操作员" width="80"><template #default="{row:s}">{{ (s.opercd_nm as string) || (s.opercd as string) || '-' }}</template></el-table-column>
                <el-table-column label="创建日期" width="120"><template #default="{row:s}">{{ fmtDateTime(s.gendate as string) }}</template></el-table-column>
                <el-table-column label="操作" width="170" fixed="right">
                  <template #default="{row:s}">
                    <el-button v-if="s.status==='00' && row.serve_ercd" link type="primary" size="small" @click="openFeedback(s)">录入反馈</el-button>
                    <el-button v-if="s.status==='01' && row.serve_ercd" link type="primary" size="small" @click="openFeedback(s)">编辑反馈</el-button>
                    <el-button v-if="s.status==='00' && row.serve_ercd" link type="success" size="small" @click="doMarkDone(s)">标记已呼出</el-button>
                    <el-button v-if="s.status==='00'" link type="danger" size="small" @click="doVoid(s)">作废</el-button>
                    <span v-if="(s.status==='00' || s.status==='01') && !row.serve_ercd" style="color:#e6a23c;font-size:12px">未分配呼出人</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="次数" width="130" class-name="count-col">
          <template #default="{row}">
            <div class="count-cell">
              <el-badge v-if="row.pre_count>0" :value="row.pre_count" type="warning" :hidden="row.pre_count===0"><span class="badge-label">预</span></el-badge>
              <el-badge v-if="row.imp_count>0" :value="row.imp_count" type="success" :hidden="row.imp_count===0"><span class="badge-label">施</span></el-badge>
              <span v-if="(row.pre_count||0)===0 && (row.imp_count||0)===0" style="color:#c0c4cc">-</span>
            </div>
            <div class="count-sub">
              <span v-if="row.pre_pending>0" class="sub-pending">预待 {{ row.pre_pending }}</span>
              <span v-if="row.imp_pending>0" class="sub-pending">施待 {{ row.imp_pending }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="分配呼出人" width="110"><template #default="{row}">{{ row.serve_ercd ? userLabel(row.serve_ercd) : '-' }}</template></el-table-column>
        <el-table-column prop="planno" label="计划单号" width="120" />
        <el-table-column label="计划类型" width="80"><template #default="{row}">{{ plLabel(row.plantyp) }}</template></el-table-column>
        <el-table-column prop="custcard" label="磁卡号" width="110" />
        <el-table-column prop="custcd" label="客户代码" width="90" />
        <el-table-column prop="custnm" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column label="有限公司" width="100"><template #default="{row}">{{ classLabel(row.classcd as string) }}</template></el-table-column>
        <el-table-column label="是否合同" width="80"><template #default="{row}">{{ row.is_contract==='Y'?'是':'否' }}</template></el-table-column>
        <el-table-column label="客户属性" width="90"><template #default="{row}">{{ pptLabel(row.pptcode as string) }}</template></el-table-column>
        <el-table-column prop="pos_item" label="计划机型" width="100" />
        <el-table-column label="计划状态" width="80"><template #default="{row}"><el-tag :type="statusTag(row.plan_status)" size="small">{{ statusLabel(row.plan_status) }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{row}">
            <el-button v-if="!row.serve_ercd && ((row.pre_pending||0)>0 || (row.imp_pending||0)>0)" link type="primary" size="small" @click="openAssign(row)">分配呼出</el-button>
            <el-button v-else-if="row.serve_ercd" link type="info" size="small" @click="openAssign(row)">更换呼出人</el-button>
            <el-button v-else link type="info" size="small" disabled>待呼出中</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <!-- 分配呼出人对话框 -->
    <el-dialog v-model="assignVisible" title="分配呼出人" width="480px">
      <el-form :model="assignForm" label-width="90px">
        <el-form-item label="预计划"><el-input :model-value="assignForm.planno" disabled /></el-form-item>
        <el-form-item label="客户"><el-input :model-value="assignForm.custnm" disabled /></el-form-item>
        <el-form-item label="呼出人"><el-select v-model="assignForm.serve_ercd" filterable clearable placeholder="选择话务员" style="width:100%"><el-option v-for="u in userOptions" :key="u.user_cd" :label="`${u.user_cd} - ${u.user_nm}`" :value="u.user_cd" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="assignVisible=false">取消</el-button><el-button type="primary" :loading="assignSaving" @click="doAssign">分配</el-button></template>
    </el-dialog>

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
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useDict } from '@/composables/useDict'
import request from '@/api/request'
import { fetchGroupMembers } from '@/api/system'
import {
  fetchServeOverview, assignServeErcd,
  fetchPlanServes, updatePlanServe, transitionPlanServe,
  type ServeOverviewRecord, type ServeRecord,
} from '@/api/sales'

const { dictLabel: plLabel } = useDict('PL')
const { dictLabel: pptLabel } = useDict('YB')
const classOptions = ref<{ class_cd: string; class_nm: string }[]>([])
async function loadClassOptions() {
  try {
    const r = await request.get<never, { data: any[] }>('/custclasses')
    classOptions.value = (r?.data || []).map((c: any) => ({ class_cd: c.class_cd, class_nm: c.class_nm }))
  } catch { classOptions.value = [] }
}
// 日期时间格式化：将 ISO 格式 (2026-07-04T10:26:08.629613) 转为 yyyy-mm-dd hh:mm:ss
function fmtDateTime(v: string | undefined | null): string {
  if (!v) return '-'
  const s = String(v)
  // 已是 yyyy-mm-dd hh:mm:ss 格式直接返回
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(s)) return s.slice(0, 19)
  // ISO 格式：替换 T 为空格，截取到秒
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(s)) return s.replace('T', ' ').slice(0, 19)
  return s
}

function classLabel(classcd: string) {
  const c = classOptions.value.find(x => x.class_cd === classcd)
  return c ? c.class_nm : (classcd || '-')
}

// 服务台用户组编码（18）：分配呼出人下拉只显示该组有效成员
const SERVE_GROUP_CD = '18'
// 系统用户列表（用于分配呼出人下拉与编码→姓名映射）
const userOptions = ref<{ user_cd: string; user_nm: string }[]>([])
async function loadUserOptions() {
  try {
    const r = await fetchGroupMembers(SERVE_GROUP_CD, { active_only: '1' })
    // 后端已按 active_only=1 过滤，这里兜底再过滤一次 status
    userOptions.value = ((r?.data as any[]) || [])
      .filter((u: any) => u.status === '1' || u.status === undefined)
      .map((u: any) => ({ user_cd: u.user_cd, user_nm: u.user_nm || '' }))
  } catch { userOptions.value = [] }
}
function userLabel(code: string) {
  if (!code) return '-'
  const u = userOptions.value.find(x => x.user_cd === code)
  return u ? `${u.user_nm || u.user_cd}` : code
}

const items = ref<ServeOverviewRecord[]>([]); const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const searchPlanno = ref(''); const searchCustnm = ref(''); const searchCustcard = ref('')
const searchServetyp = ref(''); const searchServeStatus = ref(''); const searchPlanStatus = ref('')
const searchServeErcd = ref('')

// 展开行 & 呼出记录缓存
const expandedKeys = ref<string[]>([])
const serveCache = ref<Record<string, ServeRecord[]>>({})
const serveLoading = ref(false)

function statusLabel(s: string) {
  const m: Record<string, string> = { '00': '计划中', '01': '计划完成', '02': '分派中', '03': '实施完成', '04': '实施中', '08': '计划退回', '09': '计划作废' }
  return m[s] || s
}
function statusTag(s: string) {
  const m: Record<string, string> = { '00': 'info', '01': 'success', '02': 'warning', '03': 'primary', '04': '', '08': 'danger', '09': 'danger' }
  return m[s] || 'info'
}

watch(page, () => loadData()); watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => { loadClassOptions(); loadUserOptions(); loadData() })

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, string> = { page: String(page.value), per_page: String(perPage.value) }
    if (searchPlanno.value) params.planno = searchPlanno.value
    if (searchCustnm.value) params.custnm = searchCustnm.value
    if (searchCustcard.value) params.custcard = searchCustcard.value
    if (searchServetyp.value) params.servetyp = searchServetyp.value
    if (searchServeStatus.value) params.serve_status = searchServeStatus.value
    if (searchServeErcd.value) params.serve_ercd = searchServeErcd.value
    if (searchPlanStatus.value) params.plan_status = searchPlanStatus.value
    const res = await fetchServeOverview(params)
    items.value = res.data.items || []; total.value = res.data.total || 0
    // 重置展开缓存
    expandedKeys.value = []
    serveCache.value = {}
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function onSearch() { page.value = 1; loadData() }
function onReset() {
  searchPlanno.value = ''; searchCustnm.value = ''; searchCustcard.value = ''
  searchServetyp.value = ''; searchServeStatus.value = ''; searchPlanStatus.value = ''
  searchServeErcd.value = ''
  page.value = 1; loadData()
}

function rowServes(planno: string): ServeRecord[] {
  return serveCache.value[planno] || []
}

async function onExpandChange(row: ServeOverviewRecord, expanded: ServeOverviewRecord[]) {
  const isExpand = expanded.some(r => r.planno === row.planno)
  if (!isExpand) return
  if (serveCache.value[row.planno]) return
  serveLoading.value = true
  try {
    const res = await fetchPlanServes(row.planno)
    serveCache.value[row.planno] = res.data || []
  } catch { ElMessage.error('加载呼出记录失败') }
  finally { serveLoading.value = false }
}

// 分配呼出人
const assignVisible = ref(false)
const assignForm = ref({ planno: '', custnm: '', serve_ercd: '' })
const assignSaving = ref(false)
function openAssign(row: ServeOverviewRecord) {
  assignForm.value = { planno: row.planno, custnm: row.custnm || '', serve_ercd: row.serve_ercd || '' }
  assignVisible.value = true
}
async function doAssign() {
  if (!assignForm.value.serve_ercd.trim()) { ElMessage.warning('请输入呼出人编码'); return }
  assignSaving.value = true
  try {
    await assignServeErcd(assignForm.value.planno, assignForm.value.serve_ercd.trim())
    assignVisible.value = false; loadData(); ElMessage.success('分配成功')
  } catch { ElMessage.error('分配失败') }
  finally { assignSaving.value = false }
}

// 反馈
const feedbackVisible = ref(false)
const fbForm = ref({ dtlid: 0, serve_back: 'Y', serve_mark: '' })
const fbSaving = ref(false)
function openFeedback(row: ServeRecord) {
  fbForm.value = { dtlid: row.dtlid, serve_back: row.serve_back || 'Y', serve_mark: row.serve_mark || '' }
  feedbackVisible.value = true
}
async function doFeedback() {
  fbSaving.value = true
  try {
    await updatePlanServe(fbForm.value.dtlid, { serve_back: fbForm.value.serve_back, serve_mark: fbForm.value.serve_mark })
    feedbackVisible.value = false
    // 刷新当前展开行
    const planno = items.value.find(r => rowServes(r.planno).some(s => s.dtlid === fbForm.value.dtlid))?.planno
    if (planno) { delete serveCache.value[planno]; await onExpandChange({ planno } as ServeOverviewRecord, [{ planno } as ServeOverviewRecord]) }
    loadData(); ElMessage.success('已保存')
  } catch { ElMessage.error('保存失败') }
  finally { fbSaving.value = false }
}
async function doMarkDone(row: ServeRecord) {
  try {
    await transitionPlanServe(row.dtlid, '01')
    const planno = items.value.find(r => rowServes(r.planno).some(s => s.dtlid === row.dtlid))?.planno
    if (planno) delete serveCache.value[planno]
    loadData(); ElMessage.success('已标记为已呼出')
  } catch { ElMessage.error('操作失败') }
}
async function doVoid(row: ServeRecord) {
  try {
    await ElMessageBox.confirm('确认作废该呼出单？', '作废确认', { type: 'warning' })
    await transitionPlanServe(row.dtlid, '09')
    const planno = items.value.find(r => rowServes(r.planno).some(s => s.dtlid === row.dtlid))?.planno
    if (planno) delete serveCache.value[planno]
    loadData(); ElMessage.success('已作废')
  } catch { /* 取消 */ }
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px }
.page-header h2 { font-size:18px; font-weight:600; margin:0 }
.header-tip { font-size:12px; color:#909399 }
.search-bar { display:flex; gap:12px; flex-wrap:wrap; align-items:center }
.field { display:flex; align-items:center; gap:6px }
.field label { font-size:13px; color:#606266; white-space:nowrap }
.expand-wrap { padding:12px 20px; background:#fafafa }
.count-cell { display:flex; gap:12px; align-items:center; padding-top:4px }
.badge-label { font-size:12px; padding:2px 6px; background:#f0f0f0; border-radius:3px }
.count-sub { font-size:11px; color:#e6a23c; margin-top:2px }
.sub-pending { margin-right:6px }
:deep(.count-col .cell) { overflow: visible; }
</style>

