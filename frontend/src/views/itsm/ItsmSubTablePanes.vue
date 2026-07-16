<template>
  <el-tab-pane label="派工" name="dispatch">
    <ItsmSubTablePane :maintenance-id="maintenanceId" title="派工" :fetch-fn="fetchDispatch" :create-fn="createDispatch" :update-fn="updateDispatch" :rules="dispatchRules" :row-edit-disabled="isDispatchSent" :create-disabled="isClosed" :default-form="dispatchDefaultForm">
      <template #columns>
        <el-table-column prop="business_operation_id" label="流水号" width="70"/>
        <el-table-column label="操作人" width="80"><template #default="{row}">{{ row.operator_nm || row.operator || '-' }}</template></el-table-column>
        <el-table-column label="分派组" width="80"><template #default="{row}">{{ row.accpectd_group_nm || row.accpectd_group || '-' }}</template></el-table-column>
        <el-table-column label="分派人" width="80"><template #default="{row}">{{ row.accpectder_nm || row.accpectder || '-' }}</template></el-table-column>
        <el-table-column prop="dispatch_time" label="分派时间" width="120"/>
        <el-table-column label="创建人" width="80"><template #default="{row}">{{ row.creator_nm || row.creator || '-' }}</template></el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="120"/>
        <el-table-column label="更新人" width="80"><template #default="{row}">{{ row.updator_nm || row.updator || '-' }}</template></el-table-column>
        <el-table-column prop="update_time" label="更新时间" width="120"/>
        <el-table-column label="通知状态" width="120"><template #default="{row}">
          <el-tag size="small" :type="row.notify_status==='sent'?'success':row.notify_status==='failed'?'danger':'info'">{{ notifyStatusLabel(row.notify_status as string) }}</el-tag>
          <el-tag v-if="row.notify_status==='sent' && row.notify_read==='Y'" size="small" type="success" style="margin-left:4px">已读</el-tag>
          <el-tag v-else-if="row.notify_status==='sent' && row.notify_read==='N'" size="small" type="warning" style="margin-left:4px">未读</el-tag>
          <el-button v-if="row.notify_status==='pending'" size="small" link type="primary" style="margin-left:4px" @click="goEditNotify(row)">编辑通知</el-button>
          <el-button v-else-if="row.notify_data!=='Y' && row.notify_status!=='sent'" size="small" link type="warning" style="margin-left:4px" @click="goGenNotify(row)">生成通知</el-button>
        </template></el-table-column>
        <el-table-column label="通知数据" width="80"><template #default="{row}">{{ row.notify_data==='Y'?'已产生':'未产生' }}</template></el-table-column>
      </template>
      <template #form="{ form }">
        <el-form-item label="操作人">
          <el-select v-model="form.operator" filterable style="width:100%" placeholder="选择操作人">
            <el-option v-for="u in userOptions" :key="u.user_cd" :label="`${u.user_nm} (${u.user_cd})`" :value="u.user_cd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="分派组">
          <el-select v-model="form.accpectd_group" filterable style="width:100%" placeholder="选择分派组">
            <el-option v-for="g in groupOptions" :key="g.group_cd as string" :label="(g.group_nm as string) || (g.group_cd as string)" :value="g.group_cd as string"/>
          </el-select>
        </el-form-item>
        <el-form-item label="分派人">
          <el-select v-model="form.accpectder" filterable clearable style="width:100%" placeholder="选择分派人（按区域过滤）">
            <el-option v-for="u in dispatchCandidates" :key="u.user_cd" :label="`${u.user_nm} (${u.user_cd})`" :value="u.user_cd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="派工时间"><el-date-picker v-model="form.dispatch_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择派工时间" style="width:100%"/></el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
  <el-tab-pane label="上门服务" name="d2d">
    <ItsmSubTablePane :maintenance-id="maintenanceId" title="上门" :fetch-fn="fetchD2D" :create-fn="createD2D" :update-fn="updateD2D" :rules="d2dRules">
      <template #columns>
        <el-table-column label="类型" width="80"><template #default="{row}">{{ d2dTypeLabel(row.d2d_type as string) }}</template></el-table-column>
        <el-table-column label="工程师" width="80"><template #default="{row}">{{ row.d2d_engineer_nm || row.d2d_engineer || '-' }}</template></el-table-column>
        <el-table-column prop="d2d_phone" label="电话" width="100" show-overflow-tooltip/>
        <el-table-column label="到达" width="120"><template #default="{row}">{{ row.arrive_time||'-' }}</template></el-table-column>
        <el-table-column label="离开" width="120"><template #default="{row}">{{ row.leave_time||'-' }}</template></el-table-column>
        <el-table-column label="解决" width="70"><template #default="{row}"><el-tag size="small" :type="row.jjbz==='1'?'success':'info'">{{ row.jjbz==='1'?'是':'否' }}</el-tag></template></el-table-column>
        <el-table-column prop="d2d_descripiton" label="描述" min-width="120" show-overflow-tooltip/>
      </template>
      <template #form="{ form }">
        <el-form-item label="类型"><el-select v-model="form.d2d_type" style="width:100%"><el-option label="到店" value="1"/><el-option label="离店" value="2"/><el-option label="催单" value="3"/><el-option label="记录" value="4"/></el-select></el-form-item>
        <el-form-item label="工程师"><el-input v-model="form.d2d_engineer"/></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.d2d_phone"/></el-form-item>
        <el-form-item label="到达时间"><el-date-picker v-model="form.arrive_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择到达时间" style="width:100%"/></el-form-item>
        <el-form-item label="离开时间"><el-date-picker v-model="form.leave_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择离开时间" style="width:100%"/></el-form-item>
        <el-form-item label="是否解决"><el-select v-model="form.jjbz" style="width:100%"><el-option label="是" value="1"/><el-option label="否" value="0"/></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.d2d_descripiton" type="textarea"/></el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
  <el-tab-pane label="回访" name="rv">
    <ItsmSubTablePane :maintenance-id="maintenanceId" title="回访" :fetch-fn="fetchRV" :create-fn="createRV" :update-fn="updateRV" :rules="rvRules">
      <template #columns>
        <el-table-column label="回访人" width="80"><template #default="{row}">{{ row.rv_operator_nm || row.rv_operator || '-' }}</template></el-table-column>
        <el-table-column prop="rv_time" label="回访时间" width="120"/>
        <el-table-column label="满意度" width="70"><template #default="{row}">{{ row.satisfaction_nm || row.satisfaction || '-' }}</template></el-table-column>
        <el-table-column prop="feedback" label="反馈" min-width="120" show-overflow-tooltip/>
      </template>
      <template #form="{ form }">
        <el-form-item label="回访人"><el-input v-model="form.rv_operator"/></el-form-item>
        <el-form-item label="回访时间"><el-date-picker v-model="form.rv_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择回访时间" style="width:100%"/></el-form-item>
        <el-form-item label="满意度"><el-input v-model="form.satisfaction"/></el-form-item>
        <el-form-item label="反馈"><el-input v-model="form.feedback" type="textarea"/></el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
  <el-tab-pane label="配件更新" name="acc">
    <ItsmSubTablePane :maintenance-id="maintenanceId" title="配件更新" :fetch-fn="fetchAccessories" :create-fn="createAccessories" :update-fn="updateAccessories">
      <template #columns>
        <el-table-column prop="store_id" label="门店" width="100"/>
        <el-table-column prop="device_id" label="整机" width="130" show-overflow-tooltip/>
        <el-table-column prop="old_accessories_id" label="旧配件" width="120" show-overflow-tooltip/>
        <el-table-column prop="new_accessories_id" label="新配件" width="120" show-overflow-tooltip/>
        <el-table-column prop="accessories_type" label="配件类型" width="120" show-overflow-tooltip/>
        <el-table-column label="操作" width="80"><template #default="{row}">{{ cTypeLabel(row.c_type as string) }}</template></el-table-column>
        <el-table-column prop="price" label="价格" width="80" align="right"/>
        <el-table-column label="工程师" width="80"><template #default="{row}">{{ row.engineer_id_nm || row.engineer_id || '-' }}</template></el-table-column>
        <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip/>
      </template>
      <template #form="{ form }">
        <el-form-item label="门店"><el-input v-model="form.store_id"/></el-form-item>
        <el-form-item label="整机"><el-input v-model="form.device_id"/></el-form-item>
        <el-form-item label="旧配件"><el-input v-model="form.old_accessories_id"/></el-form-item>
        <el-form-item label="新配件"><el-input v-model="form.new_accessories_id"/></el-form-item>
        <el-form-item label="配件类型"><el-input v-model="form.accessories_type"/></el-form-item>
        <el-form-item label="操作"><el-select v-model="form.c_type" style="width:100%"><el-option label="维修" value="1"/><el-option label="购买" value="2"/></el-select></el-form-item>
        <el-form-item label="价格"><el-input v-model="form.price" type="number"/></el-form-item>
        <el-form-item label="工程师"><el-input v-model="form.engineer_id"/></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea"/></el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
  <el-tab-pane label="收费" name="pay">
    <ItsmSubTablePane :maintenance-id="maintenanceId" title="收费" :fetch-fn="fetchPayList" :create-fn="createPayList" :update-fn="updatePayList" :rules="payRules">
      <template #columns>
        <el-table-column prop="store_id" label="门店" width="100"/>
        <el-table-column label="工程师" width="80"><template #default="{row}">{{ row.engineer_id_nm || row.engineer_id || '-' }}</template></el-table-column>
        <el-table-column prop="paytype" label="收费类型" width="100" show-overflow-tooltip/>
        <el-table-column prop="payje" label="金额" width="80" align="right"/>
        <el-table-column prop="paydate" label="收款日期" width="120"/>
        <el-table-column prop="receipt_id" label="收据号" width="90"/>
        <el-table-column prop="delivery_id" label="送货单" width="90"/>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
      </template>
      <template #form="{ form }">
        <el-form-item label="门店"><el-input v-model="form.store_id"/></el-form-item>
        <el-form-item label="工程师"><el-input v-model="form.engineer_id"/></el-form-item>
        <el-form-item label="收费类型"><el-input v-model="form.paytype"/></el-form-item>
        <el-form-item label="金额"><el-input v-model="form.payje" type="number"/></el-form-item>
        <el-form-item label="收款日期"><el-date-picker v-model="form.paydate" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择收款日期" style="width:100%"/></el-form-item>
        <el-form-item label="收据号"><el-input v-model="form.receipt_id"/></el-form-item>
        <el-form-item label="送货单"><el-input v-model="form.delivery_id"/></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.memo" type="textarea"/></el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
  <el-tab-pane label="关单记录" name="close">
    <ItsmSubTablePane :maintenance-id="maintenanceId" title="关单记录" :fetch-fn="fetchCloseBills" :create-fn="createCloseBill" :update-fn="updateCloseBill">
      <template #columns>
        <el-table-column prop="close_time" label="关单时间" width="120"/>
        <el-table-column prop="close_type" label="类型" width="80"/>
        <el-table-column label="补关单" width="80"><template #default="{row}">{{ row.is_old==='Y'?'是':'否' }}</template></el-table-column>
        <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip/>
      </template>
      <template #form="{ form }">
        <el-form-item label="关单时间"><el-date-picker v-model="form.close_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择关单时间" style="width:100%"/></el-form-item>
        <el-form-item label="关单类型"><el-input v-model="form.close_type"/></el-form-item>
        <el-form-item label="是否补关"><el-select v-model="form.is_old" style="width:100%"><el-option label="是" value="Y"/><el-option label="否" value="N"/></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea"/></el-form-item>
      </template>
    </ItsmSubTablePane>
  </el-tab-pane>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ItsmSubTablePane from './ItsmSubTablePane.vue'
import { fetchD2D, createD2D, updateD2D, fetchRV, createRV, updateRV, fetchAccessories, createAccessories, updateAccessories, fetchPayList, createPayList, updatePayList, fetchDispatch, createDispatch, updateDispatch, fetchCloseBills, createCloseBill, updateCloseBill } from '@/api/itsm'
import { fetchAreaUsers } from '@/api/master'
import { fetchGroups, fetchUsers } from '@/api/system'
import type { UserItem } from '@/api/system'
import { useAuthStore } from '@/stores/auth'
import type { AreaUserRecord } from '@/api/master'

const props = defineProps<{ maintenanceId: string; areaCd?: string; currentStatus?: string }>()

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

const d2dTypeMap: Record<string, string> = { '1': '到店', '2': '离店', '3': '催单', '4': '记录' }
const cTypeMap: Record<string, string> = { '1': '维修', '2': '购买' }
function d2dTypeLabel(v: string) { return d2dTypeMap[v] || v || '-' }
function cTypeLabel(v: string) { return cTypeMap[v] || v || '-' }

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
const d2dRules={d2d_engineer:[{required:true,message:'请输入工程师',trigger:'blur'}],arrive_time:[{required:true,message:'请选择到达时间',trigger:'change'}]}
const rvRules={rv_operator:[{required:true,message:'请输入回访人',trigger:'blur'}],rv_time:[{required:true,message:'请选择回访时间',trigger:'change'}]}
const dispatchRules={accpectd_group:[{required:true,message:'请选择分派组',trigger:'change'}],accpectder:[{required:true,message:'请选择分派人',trigger:'change'}],dispatch_time:[{required:true,message:'请选择派工时间',trigger:'change'}]}
const payRules={payje:[{required:true,message:'请输入金额',trigger:'blur'}],paytype:[{required:true,message:'请输入收费类型',trigger:'blur'}]}
</script>
