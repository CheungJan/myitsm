<template>
  <div class="d2d-operation-tab">
    <!-- 4 个操作按钮 -->
    <div class="d2d-actions">
      <el-button
        size="small"
        type="primary"
        @click="openArrive"
      >
        到店登记
      </el-button>
      <el-button
        size="small"
        type="success"
        @click="openLeave"
      >
        离店登记
      </el-button>
      <el-button
        size="small"
        type="warning"
        @click="openUrge"
      >
        催单
      </el-button>
      <el-button
        size="small"
        type="info"
        @click="openRecord"
      >
        记录
      </el-button>
    </div>

    <!-- d2d 记录列表 -->
    <el-table
      :data="list"
      size="small"
      empty-text="暂无上门服务记录"
      max-height="400"
    >
      <el-table-column
        label="类型"
        width="80"
      >
        <template #default="{ row }">
          <el-tag
            size="small"
            :type="d2dTypeTag(row.d2d_type as string)"
          >
            {{ d2dTypeLabel(row.d2d_type as string) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="工程师"
        width="80"
      >
        <template #default="{ row }">
          {{ row.d2d_engineer_nm || row.d2d_engineer || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="d2d_phone"
        label="电话"
        width="100"
        show-overflow-tooltip
      />
      <el-table-column
        label="到达"
        width="120"
      >
        <template #default="{ row }">
          {{ row.arrive_time || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        label="离开"
        width="120"
      >
        <template #default="{ row }">
          {{ row.leave_time || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        label="结果"
        width="100"
      >
        <template #default="{ row }">
          {{ row.d2d_result_nm || row.d2d_result || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="gzdm"
        label="故障代码"
        width="100"
        show-overflow-tooltip
      />
      <el-table-column
        prop="d2d_descripiton"
        label="描述"
        min-width="150"
        show-overflow-tooltip
      />
      <el-table-column
        prop="create_time"
        label="创建时间"
        width="120"
      />
    </el-table>

    <!-- 到店登记弹窗 -->
    <el-dialog
      v-model="arriveVisible"
      title="到店登记"
      width="480px"
      append-to-body
    >
      <el-form
        ref="arriveFormRef"
        :model="arriveForm"
        :rules="arriveRules"
        label-width="90px"
        size="small"
      >
        <el-form-item
          label="工程师"
          prop="d2d_engineer"
        >
          <el-select
            v-model="arriveForm.d2d_engineer"
            filterable
            style="width:100%"
            placeholder="选择上门工程师"
          >
            <el-option
              v-for="u in engineerOptions"
              :key="u.user_cd"
              :label="`${u.user_nm} (${u.user_cd})`"
              :value="u.user_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="到达时间">
          <el-date-picker
            v-model="arriveForm.arrive_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="默认当前时间"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="arriveForm.d2d_phone" />
        </el-form-item>
        <el-form-item label="到场说明">
          <el-input
            v-model="arriveForm.d2d_descripiton"
            type="textarea"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button
          size="small"
          @click="arriveVisible = false"
        >
          取消
        </el-button>
        <el-button
          size="small"
          type="primary"
          @click="submitArrive"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 离店登记弹窗（四要素 + 故障代码级联 + 设备/配件） -->
    <el-dialog
      v-model="leaveVisible"
      title="离店登记"
      width="720px"
      append-to-body
    >
      <el-form
        ref="leaveFormRef"
        :model="leaveForm"
        :rules="leaveRules"
        label-width="90px"
        size="small"
      >
        <el-divider content-position="left">
          基本信息
        </el-divider>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item
              label="工程师"
              prop="d2d_engineer"
            >
              <el-select
                v-model="leaveForm.d2d_engineer"
                filterable
                style="width:100%"
                placeholder="选择上门工程师"
              >
                <el-option
                  v-for="u in engineerOptions"
                  :key="u.user_cd"
                  :label="`${u.user_nm} (${u.user_cd})`"
                  :value="u.user_cd"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="离店时间">
              <el-date-picker
                v-model="leaveForm.leave_time"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                placeholder="默认当前时间"
                style="width:100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">
          故障代码
        </el-divider>
        <el-form-item label="故障代码">
          <FaultCodeCascader
            :model-value="(leaveForm.gzdm as string) || ''"
            :store-id="(mainInfo.store_id as string) || ''"
            :fault-type="leaveFaultType"
            placeholder="级联选择故障代码"
            @update:model-value="(v:string) => leaveForm.gzdm = v"
          />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="处理设备">
              <el-input
                v-model="leaveForm.device_id"
                placeholder="本次处理设备ID"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="处理配件">
              <el-input
                v-model="leaveForm.accessories_id"
                placeholder="本次处理配件ID"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">
          四要素
        </el-divider>
        <el-form-item label="实际现象">
          <el-input
            v-model="leaveForm.d2d_phenomenon"
            type="textarea"
            :rows="2"
            placeholder="自动带出报修简述，可补充"
          />
        </el-form-item>
        <el-form-item label="原因">
          <el-select
            v-model="leaveForm.d2d_reason"
            filterable
            allow-create
            default-first-option
            style="width:100%"
            placeholder="选择或输入原因"
          >
            <el-option
              v-for="r in reasonHistory"
              :key="r"
              :label="r"
              :value="r"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="处理过程">
          <el-input
            v-model="leaveForm.d2d_handling"
            type="textarea"
            :rows="2"
            placeholder="工程师补充处理过程"
          />
        </el-form-item>
        <el-form-item
          label="结果"
          prop="d2d_result"
        >
          <el-select
            v-model="leaveForm.d2d_result"
            style="width:100%"
            placeholder="选择离店结果"
            @change="onResultChange"
          >
            <el-option
              label="已解决"
              value="5"
            />
            <el-option
              label="未解决"
              value="4"
            />
            <el-option
              label="转修"
              value="6"
            />
            <el-option
              label="待配件"
              value="7"
            />
            <el-option
              label="关闭"
              value="3"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          v-if="leaveForm.d2d_result === '3'"
          label="关闭原因"
          prop="closure_reason"
        >
          <el-select
            v-model="leaveForm.closure_reason"
            style="width:100%"
            placeholder="选择关闭原因"
          >
            <el-option
              v-for="o in closureReasonOptions"
              :key="o.value"
              :label="o.label"
              :value="o.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="其他补充">
          <el-input
            v-model="leaveForm.d2d_note"
            type="textarea"
            :rows="2"
          />
        </el-form-item>

        <el-divider content-position="left">
          POS 状态
        </el-divider>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="POS主状态">
              <el-input
                v-model="leaveForm.posstatus"
                placeholder="默认01=正常"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="POS子状态">
              <el-input
                v-model="leaveForm.posstatus1"
                placeholder="默认11=正常使用"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button
          size="small"
          @click="leaveVisible = false"
        >
          取消
        </el-button>
        <el-button
          size="small"
          type="primary"
          @click="submitLeave"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 催单弹窗 -->
    <el-dialog
      v-model="urgeVisible"
      title="催单"
      width="480px"
      append-to-body
    >
      <el-form
        ref="urgeFormRef"
        :model="urgeForm"
        :rules="urgeRules"
        label-width="90px"
        size="small"
      >
        <el-form-item
          label="工程师"
          prop="d2d_engineer"
        >
          <el-select
            v-model="urgeForm.d2d_engineer"
            filterable
            style="width:100%"
            placeholder="选择工程师"
          >
            <el-option
              v-for="u in engineerOptions"
              :key="u.user_cd"
              :label="`${u.user_nm} (${u.user_cd})`"
              :value="u.user_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="urgeForm.d2d_phone" />
        </el-form-item>
        <el-form-item label="催单说明">
          <el-input
            v-model="urgeForm.d2d_descripiton"
            type="textarea"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button
          size="small"
          @click="urgeVisible = false"
        >
          取消
        </el-button>
        <el-button
          size="small"
          type="primary"
          @click="submitUrge"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 记录弹窗 -->
    <el-dialog
      v-model="recordVisible"
      title="自由记录"
      width="480px"
      append-to-body
    >
      <el-form
        ref="recordFormRef"
        :model="recordForm"
        :rules="recordRules"
        label-width="90px"
        size="small"
      >
        <el-form-item
          label="工程师"
          prop="d2d_engineer"
        >
          <el-select
            v-model="recordForm.d2d_engineer"
            filterable
            clearable
            style="width:100%"
            placeholder="选择工程师（可留空）"
          >
            <el-option
              v-for="u in engineerOptions"
              :key="u.user_cd"
              :label="`${u.user_nm} (${u.user_cd})`"
              :value="u.user_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="recordForm.d2d_phone" />
        </el-form-item>
        <el-form-item
          label="记录内容"
          prop="d2d_descripiton"
        >
          <el-input
            v-model="recordForm.d2d_descripiton"
            type="textarea"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button
          size="small"
          @click="recordVisible = false"
        >
          取消
        </el-button>
        <el-button
          size="small"
          type="primary"
          @click="submitRecord"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import FaultCodeCascader from './FaultCodeCascader.vue'
import {
  fetchD2D, arriveStoreD2D, leaveStoreD2D, urgeD2D, recordD2D,
  fetchMaintenanceDailyDetail, fetchD2DDefaultEngineer,
} from '@/api/itsm'
import { fetchUsers, fetchEidInfo } from '@/api/system'
import type { UserItem } from '@/api/system'
import type { SubRecord } from '@/api/itsm'
import { useAuthStore } from '@/stores/auth'
import { useDict } from '@/composables/useDict'

const { dictOptions: closureReasonOptions } = useDict('CLO_REASON')
const { dictLabel: gzLabel } = useDict('GZ')

// B4：离店登记故障代码预过滤（device_id→itemcd→fault_type）
const leaveFaultType = ref('')
async function refreshLeaveFaultType(deviceId: string): Promise<void> {
  if (!deviceId) { leaveFaultType.value = ''; return }
  try {
    const r = await fetchEidInfo(deviceId)
    const itemcd = (r?.data?.itemcd as string) || ''
    leaveFaultType.value = itemcd.slice(0, 2)
  } catch {
    leaveFaultType.value = ''
  }
}

const props = defineProps<{
  maintenanceId: string
  /** 主表记录（可选，用于预填现象/设备等）。不传则按 maintenanceId 拉取日常维护单详情 */
  mainRecord?: Record<string, unknown>
}>()

const emit = defineEmits<{ saved: [type: string] }>()

const authStore = useAuthStore()

// ---- 工程师候选 ----
const engineerOptions = ref<UserItem[]>([])
async function loadEngineers(): Promise<void> {
  try {
    const r = await fetchUsers({ useflg: '1' })
    engineerOptions.value = r?.data || []
  } catch { engineerOptions.value = [] }
}

// ---- 主表预填数据（报修简述/故障类型/设备） ----
const mainInfo = ref<Record<string, unknown>>({})
async function loadMainInfo(): Promise<void> {
  if (props.mainRecord && Object.keys(props.mainRecord).length) {
    mainInfo.value = props.mainRecord
    return
  }
  if (!props.maintenanceId) return
  try {
    const r = await fetchMaintenanceDailyDetail(props.maintenanceId)
    mainInfo.value = r?.data || {}
  } catch { mainInfo.value = {} }
}

// ---- d2d 列表 ----
const list = ref<SubRecord[]>([])
async function loadList(): Promise<void> {
  if (!props.maintenanceId) return
  try {
    const r = await fetchD2D(props.maintenanceId)
    list.value = r?.data || []
  } catch { list.value = [] }
}

onMounted(() => { loadEngineers(); loadList(); loadMainInfo() })
watch(() => props.maintenanceId, () => { loadList(); loadMainInfo() })
watch(() => props.mainRecord, () => { loadMainInfo() }, { deep: true })
// B4：离店表单 device_id 变化时重新反查 itemcd 预过滤故障代码
// 注：watch 移至 leaveForm 声明之后，避免 TDZ（Cannot access 'leaveForm' before initialization）

// ---- 类型/标签映射 ----
const d2dTypeMap: Record<string, string> = { '1': '到店', '2': '离店', '3': '催单', '4': '记录' }
function d2dTypeLabel(v: string): string { return d2dTypeMap[v] || v || '-' }
function d2dTypeTag(v: string): 'primary' | 'success' | 'warning' | 'info' {
  return ({ '1': 'primary', '2': 'success', '3': 'warning', '4': 'info' } as const)[v as '1' | '2' | '3' | '4'] || 'info'
}

// ---- 原因最近 10 条快捷选择（从历史 d2d 记录提取） ----
const reasonHistory = computed<string[]>(() => {
  const set = new Set<string>()
  for (const r of list.value) {
    const reason = (r.d2d_reason as string) || ''
    if (reason) set.add(reason)
    if (set.size >= 10) break
  }
  return Array.from(set).slice(0, 10)
})

// ---- 当前时间字符串 ----
function nowStr(): string {
  return new Date().toISOString().slice(0, 19).replace('T', ' ')
}

// ---- 到店登记 ----
const arriveVisible = ref(false)
const arriveFormRef = ref()
const arriveForm = ref<Record<string, unknown>>({})
const arriveRules = {
  d2d_engineer: [{ required: true, message: '请选择工程师', trigger: 'change' }],
}
async function openArrive(): Promise<void> {
  arriveForm.value = {
    d2d_engineer: await defaultEngineer(),
    arrive_time: nowStr(),
    d2d_phone: '',
    d2d_descripiton: '',
  }
  arriveVisible.value = true
}
async function submitArrive(): Promise<void> {
  if (!arriveFormRef.value) return
  try { await arriveFormRef.value.validate() } catch { return }
  try {
    await arriveStoreD2D(props.maintenanceId, cleanData(arriveForm.value))
    ElMessage.success('到店登记成功')
    arriveVisible.value = false
    await loadList()
    emit('saved', 'arrive')
  } catch { ElMessage.error('到店登记失败') }
}

// ---- 离店登记 ----
const leaveVisible = ref(false)
const leaveFormRef = ref()
const leaveForm = ref<Record<string, unknown>>({})
// B4：离店表单 device_id 变化时重新反查 itemcd 预过滤故障代码
watch(() => leaveForm.value.device_id, (v) => { refreshLeaveFaultType((v as string) || '') })
const leaveRules = {
  d2d_engineer: [{ required: true, message: '请选择工程师', trigger: 'change' }],
  d2d_result: [{ required: true, message: '请选择离店结果', trigger: 'change' }],
  closure_reason: [{ required: true, message: '请选择关闭原因', trigger: 'change' }],
}
async function openLeave(): Promise<void> {
  const shortDesc = (mainInfo.value.short_description as string) || ''
  const faultTypeCd = (mainInfo.value.fault_type as string) || ''
  // 故障类型码值翻译为名称（GZ 字典），拼入现象：报修简述 / 故障类型名称
  const faultTypeNm = faultTypeCd ? gzLabel(faultTypeCd) : ''
  const phenomenon = [shortDesc, faultTypeNm].filter(Boolean).join(' / ')
  leaveForm.value = {
    d2d_engineer: await defaultEngineer(),
    leave_time: nowStr(),
    gzdm: '',
    device_id: (mainInfo.value.device_id as string) || '',
    accessories_id: '',
    d2d_phenomenon: phenomenon,
    d2d_reason: '',
    d2d_handling: '',
    d2d_result: '',
    closure_reason: '',
    d2d_note: '',
    posstatus: '01',
    posstatus1: '11',
    version: 1,
  }
  // B4：按 device_id 反查 itemcd 前两位预过滤故障代码
  await refreshLeaveFaultType(leaveForm.value.device_id as string)
  leaveVisible.value = true
}
function onResultChange(v: string): void {
  // 结果联动：非关闭时清空关闭原因
  if (v !== '3') leaveForm.value.closure_reason = ''
}
async function submitLeave(): Promise<void> {
  if (!leaveFormRef.value) return
  try { await leaveFormRef.value.validate() } catch { return }
  try {
    await leaveStoreD2D(props.maintenanceId, cleanData(leaveForm.value))
    ElMessage.success('离店登记成功')
    leaveVisible.value = false
    await loadList()
    emit('saved', 'leave')
  } catch { ElMessage.error('离店登记失败') }
}

// ---- 催单 ----
const urgeVisible = ref(false)
const urgeFormRef = ref()
const urgeForm = ref<Record<string, unknown>>({})
const urgeRules = {
  d2d_engineer: [{ required: true, message: '请选择工程师', trigger: 'change' }],
}
async function openUrge(): Promise<void> {
  urgeForm.value = {
    d2d_engineer: await defaultEngineer(),
    d2d_phone: '',
    d2d_descripiton: '',
  }
  urgeVisible.value = true
}
async function submitUrge(): Promise<void> {
  if (!urgeFormRef.value) return
  try { await urgeFormRef.value.validate() } catch { return }
  try {
    await urgeD2D(props.maintenanceId, cleanData(urgeForm.value))
    ElMessage.success('催单成功')
    urgeVisible.value = false
    await loadList()
    emit('saved', 'urge')
  } catch { ElMessage.error('催单失败') }
}

// ---- 记录 ----
const recordVisible = ref(false)
const recordFormRef = ref()
const recordForm = ref<Record<string, unknown>>({})
const recordRules = {
  d2d_descripiton: [{ required: true, message: '请输入记录内容', trigger: 'blur' }],
}
async function openRecord(): Promise<void> {
  recordForm.value = {
    d2d_engineer: await defaultEngineer(),
    d2d_phone: '',
    d2d_descripiton: '',
  }
  recordVisible.value = true
}
async function submitRecord(): Promise<void> {
  if (!recordFormRef.value) return
  try { await recordFormRef.value.validate() } catch { return }
  try {
    await recordD2D(props.maintenanceId, cleanData(recordForm.value))
    ElMessage.success('记录成功')
    recordVisible.value = false
    await loadList()
    emit('saved', 'record')
  } catch { ElMessage.error('记录失败') }
}

// ---- 工具函数 ----
async function defaultEngineer(): Promise<string> {
  // 对齐文档 §5.1.1：最新派工人 → 区域负责人 → 当前登录用户
  try {
    const r = await fetchD2DDefaultEngineer(props.maintenanceId)
    if (r?.data?.engineer) return r.data.engineer
  } catch { /* 忽略，兜底当前用户 */ }
  return authStore.userCode || ''
}

function cleanData(data: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(data)) {
    if (v === '' || v === null || v === undefined) continue
    out[k] = v
  }
  return out
}

defineExpose({ loadList })
</script>

<style scoped>
.d2d-operation-tab { display: flex; flex-direction: column; gap: 8px; }
.d2d-actions { padding: 4px 0; border-bottom: 1px solid #e4e7ed; display: flex; gap: 8px; }
</style>
