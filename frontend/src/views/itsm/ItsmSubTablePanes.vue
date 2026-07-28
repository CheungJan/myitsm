<template>
  <el-tab-pane
    label="派工"
    name="dispatch"
  >
    <ItsmSubTablePane
      :maintenance-id="maintenanceId"
      title="派工"
      :fetch-fn="fetchDispatch"
      :create-fn="createDispatch"
      :update-fn="updateDispatch"
      :rules="dispatchRules"
      :row-edit-disabled="isDispatchSent"
      :create-disabled="isClosed"
      :default-form="dispatchDefaultForm"
    >
      <template #columns>
        <el-table-column
          prop="business_operation_id"
          label="流水号"
          width="70"
        />
        <el-table-column
          label="操作人"
          width="80"
        >
          <template #default="{row}">
            {{ row.operator_nm || row.operator || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          label="分派组"
          width="80"
        >
          <template #default="{row}">
            {{ row.accpectd_group_nm || row.accpectd_group || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          label="分派人"
          width="80"
        >
          <template #default="{row}">
            {{ row.accpectder_nm || row.accpectder || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="dispatch_time"
          label="分派时间"
          width="120"
        />
        <el-table-column
          label="创建人"
          width="80"
        >
          <template #default="{row}">
            {{ row.creator_nm || row.creator || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="create_time"
          label="创建时间"
          width="120"
        />
        <el-table-column
          label="更新人"
          width="80"
        >
          <template #default="{row}">
            {{ row.updator_nm || row.updator || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="update_time"
          label="更新时间"
          width="120"
        />
        <el-table-column
          label="通知状态"
          width="120"
        >
          <template #default="{row}">
            <el-tag
              size="small"
              :type="row.notify_status==='sent'?'success':row.notify_status==='failed'?'danger':'info'"
            >
              {{ notifyStatusLabel(row.notify_status as string) }}
            </el-tag>
            <el-tag
              v-if="row.notify_status==='sent' && row.notify_read==='Y'"
              size="small"
              type="success"
              style="margin-left:4px"
            >
              已读
            </el-tag>
            <el-tag
              v-else-if="row.notify_status==='sent' && row.notify_read==='N'"
              size="small"
              type="warning"
              style="margin-left:4px"
            >
              未读
            </el-tag>
            <el-button
              v-if="row.notify_status==='pending'"
              size="small"
              link
              type="primary"
              style="margin-left:4px"
              @click="goEditNotify(row)"
            >
              编辑通知
            </el-button>
            <el-button
              v-else-if="row.notify_data!=='Y' && row.notify_status!=='sent'"
              size="small"
              link
              type="warning"
              style="margin-left:4px"
              @click="goGenNotify(row)"
            >
              生成通知
            </el-button>
          </template>
        </el-table-column>
        <el-table-column
          label="通知数据"
          width="80"
        >
          <template #default="{row}">
            {{ row.notify_data==='Y'?'已产生':'未产生' }}
          </template>
        </el-table-column>
      </template>
      <template #form="{ form }">
        <el-form-item label="操作人">
          <el-select
            v-model="form.operator"
            filterable
            style="width:100%"
            placeholder="选择操作人"
          >
            <el-option
              v-for="u in userOptions"
              :key="u.user_cd"
              :label="`${u.user_nm} (${u.user_cd})`"
              :value="u.user_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分派组">
          <el-select
            v-model="form.accpectd_group"
            filterable
            style="width:100%"
            placeholder="选择分派组"
          >
            <el-option
              v-for="g in groupOptions"
              :key="g.group_cd as string"
              :label="(g.group_nm as string) || (g.group_cd as string)"
              :value="g.group_cd as string"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分派人">
          <el-select
            v-model="form.accpectder"
            filterable
            clearable
            style="width:100%"
            placeholder="选择分派人（按区域过滤）"
          >
            <el-option
              v-for="u in dispatchCandidates"
              :key="u.user_cd"
              :label="`${u.user_nm} (${u.user_cd})`"
              :value="u.user_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="派工时间">
          <el-date-picker
            v-model="form.dispatch_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择派工时间"
            style="width:100%"
          />
        </el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
  <el-tab-pane
    label="上门服务"
    name="d2d"
  >
    <D2DOperationTab
      :maintenance-id="maintenanceId"
      :main-record="mainRecord"
    />
  </el-tab-pane>
  <el-tab-pane
    label="回访"
    name="rv"
  >
    <ItsmSubTablePane
      :maintenance-id="maintenanceId"
      title="回访"
      :fetch-fn="fetchRV"
      :create-fn="createRV"
      :update-fn="updateRV"
      :rules="rvRules"
    >
      <template #columns>
        <el-table-column
          label="回访人"
          width="80"
        >
          <template #default="{row}">
            {{ row.rv_operator_nm || row.rv_operator || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="rv_time"
          label="回访时间"
          width="120"
        />
        <el-table-column
          label="满意度"
          width="70"
        >
          <template #default="{row}">
            {{ row.satisfaction_nm || row.satisfaction || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="feedback"
          label="反馈"
          min-width="120"
          show-overflow-tooltip
        />
      </template>
      <template #form="{ form }">
        <el-form-item label="回访人">
          <el-input v-model="form.rv_operator" />
        </el-form-item>
        <el-form-item label="回访时间">
          <el-date-picker
            v-model="form.rv_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择回访时间"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="满意度">
          <el-input v-model="form.satisfaction" />
        </el-form-item>
        <el-form-item label="反馈">
          <el-input
            v-model="form.feedback"
            type="textarea"
          />
        </el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
  <el-tab-pane
    label="物料与收费"
    name="mc"
  >
    <MaterialChargePane
      :maintenance-id="maintenanceId"
      :current-status="currentStatus"
      :store-id="((mainRecord?.store_id as string) || '')"
      :engineer-id="((mainRecord?.engineer_id as string) || '')"
    />
  </el-tab-pane>
  <el-tab-pane
    label="关单记录"
    name="close"
  >
    <ItsmSubTablePane
      :maintenance-id="maintenanceId"
      title="关单记录"
      :fetch-fn="fetchCloseBills"
      :create-fn="createCloseBill"
      :update-fn="updateCloseBill"
    >
      <template #columns>
        <el-table-column
          prop="close_time"
          label="关单时间"
          width="120"
        />
        <el-table-column
          prop="close_type"
          label="类型"
          width="80"
        />
        <el-table-column
          label="补关单"
          width="80"
        >
          <template #default="{row}">
            {{ row.is_old==='Y'?'是':'否' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          label="描述"
          min-width="120"
          show-overflow-tooltip
        />
      </template>
      <template #form="{ form }">
        <el-form-item label="关单时间">
          <el-date-picker
            v-model="form.close_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择关单时间"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="关单类型">
          <el-input v-model="form.close_type" />
        </el-form-item>
        <el-form-item label="是否补关">
          <el-select
            v-model="form.is_old"
            style="width:100%"
          >
            <el-option
              label="是"
              value="Y"
            /><el-option
              label="否"
              value="N"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
          />
        </el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ItsmSubTablePane from './ItsmSubTablePane.vue'
import D2DOperationTab from './D2DOperationTab.vue'
import MaterialChargePane from './MaterialChargePane.vue'
import { fetchRV, createRV, updateRV, fetchDispatch, createDispatch, updateDispatch, fetchCloseBills, createCloseBill, updateCloseBill } from '@/api/itsm'
import { fetchAreaUsers } from '@/api/master'
import { fetchGroups, fetchUsers } from '@/api/system'
import type { UserItem } from '@/api/system'
import { useAuthStore } from '@/stores/auth'
import type { AreaUserRecord } from '@/api/master'

const props = defineProps<{ maintenanceId: string; areaCd?: string; currentStatus?: string; mainRecord?: Record<string, unknown> }>()

const authStore = useAuthStore()

// 操作员候选：全部有效用户（useflg='1'）
const userOptions = ref<UserItem[]>([])
async function loadUsers() {
  try {
    const r = await fetchUsers({ useflg: '1' })
    userOptions.value = r?.data || []
  } catch { userOptions.value = [] }
}

// 分派组候选
const groupOptions = ref<Record<string, unknown>[]>([])
async function loadGroups() {
  try {
    const r = await fetchGroups()
    groupOptions.value = (r?.data || []) as Record<string, unknown>[]
  } catch { groupOptions.value = [] }
}

onMounted(() => { loadUsers(); loadGroups() })

// 派工候选工程师：按 areaCd 过滤（tit06_userarea choose=1 的用户）
const dispatchCandidates = ref<AreaUserRecord[]>([])
watch(() => props.areaCd || '', async (cd) => {
  dispatchCandidates.value = []
  if (!cd) return
  try {
    const r = await fetchAreaUsers(cd)
    dispatchCandidates.value = (r?.data || []).filter(u => u.choose === 1)
  } catch { dispatchCandidates.value = [] }
}, { immediate: true })

// 派工新建默认值：操作员=当前登录用户，分派组=A1 兜底
const dispatchDefaultForm = computed(() => ({
  operator: authStore.userCode || '',
  accpectd_group: 'A1',
  dispatch_time: new Date().toISOString().slice(0,19).replace('T',' '),
}))

// 已发送通知的派工行不可编辑
function isDispatchSent(row: Record<string, unknown>): boolean {
  return row.notify_status === 'sent'
}

// 已关单（状态 3=关单 / 9=作废）不可新增派工
const isClosed = computed(() => ['3', '9'].includes(props.currentStatus || ''))

// 通知状态标签（重构 PB fxbz 飞信状态）
const notifyStatusMap:Record<string,string>={sent:'已发',pending:'未发',failed:'失败',N:'未发'}
function notifyStatusLabel(v:string){return notifyStatusMap[v]||'未发'}

// 跳转通知记录页：pending 跳编辑，未产生跳生成
const router = useRouter()
function goEditNotify(row: Record<string, unknown>) {
  router.push({ name: 'NotificationList', query: { ref_type: 'dispatch', ref_id: String(row.maintenance_id || ''), action: 'edit' } })
}
function goGenNotify(row: Record<string, unknown>) {
  router.push({ name: 'NotificationList', query: { ref_type: 'dispatch', ref_id: String(row.maintenance_id || ''), action: 'create' } })
}

// 子表校验规则（对齐 PB 必填校验）
const rvRules={rv_operator:[{required:true,message:'请输入回访人',trigger:'blur'}],rv_time:[{required:true,message:'请选择回访时间',trigger:'change'}]}
const dispatchRules={accpectd_group:[{required:true,message:'请选择分派组',trigger:'change'}],accpectder:[{required:true,message:'请选择分派人',trigger:'change'}],dispatch_time:[{required:true,message:'请选择派工时间',trigger:'change'}]}
</script>
