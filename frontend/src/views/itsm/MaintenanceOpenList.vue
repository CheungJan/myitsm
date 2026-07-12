<template>
  <div class="page">
    <ItsmDetailLayout>
      <template #search>
        <div class="page-header"><h2>新机开通</h2></div>
      </template>
      <template #list>
        <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open" row-key="new_opening_id">
          <el-table-column prop="new_opening_id" label="开通单号" width="120"/>
          <el-table-column label="公司" width="120"><template #default="{row}">{{ className(row.company_id as string) }}</template></el-table-column>
          <el-table-column prop="store_id" label="门店" width="90"/>
          <el-table-column prop="device_id" label="主设备EID" width="150" show-overflow-tooltip/>
          <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="statusTag(row.current_status as string)" size="small">{{ statusLabel(row.current_status as string) }}</el-tag></template></el-table-column>
          <el-table-column label="负责人" width="80"><template #default="{row}">{{ userName(row.firstor as string) }}</template></el-table-column>
          <el-table-column label="创建日期" width="100"><template #default="{row}">{{ row.create_time || '-' }}</template></el-table-column>
          <el-table-column label="完成日期" width="100"><template #default="{row}">{{ row.close_time || '-' }}</template></el-table-column>
          <el-table-column prop="count" label="数量" width="60" align="right"/>
        </el-table>
        <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
      </template>
      <template #summary>
        <el-descriptions v-if="detail" :column="2" border size="small">
          <el-descriptions-item label="单号">{{ detail.new_opening_id }}</el-descriptions-item>
          <el-descriptions-item label="公司">{{ className(detail.company_id as string) }}</el-descriptions-item>
          <el-descriptions-item label="门店">{{ detail.store_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.current_status as string)" size="small">{{ statusLabel(detail.current_status as string) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="主设备EID" :span="2">{{ detail.device_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="数量">{{ detail.count }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ userName(detail.firstor as string) }}</el-descriptions-item>
          <el-descriptions-item label="请求时间">{{ detail.request_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="考核时间">{{ detail.expected_completion_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建">{{ detail.create_time }}</el-descriptions-item>
          <el-descriptions-item label="完成">{{ detail.close_time||'-' }}</el-descriptions-item>
          <el-descriptions-item label="回访">{{ detail.revisit_time||'-' }}</el-descriptions-item>
          <el-descriptions-item label="是否补单">{{ detail.is_old==='Y'?'是':'否' }}</el-descriptions-item>
          <el-descriptions-item label="成功标志">{{ detail.is_success==='1'?'成功':'-' }}</el-descriptions-item>
          <el-descriptions-item label="简述" :span="2">{{ detail.short_description||'-' }}</el-descriptions-item>
          <el-descriptions-item label="详情" :span="2">{{ detail.detail_description||'-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template #actions>
        <div class="action-bar" v-if="detail">
          <el-button size="small" type="primary" @click="openEdit(detail)">编辑</el-button>
          <el-button size="small" type="primary" @click="doTransition(detail,'2')" v-if="detail.current_status==='1'">分配</el-button>
          <el-button size="small" type="success" @click="doTransition(detail,'5')" v-if="detail.current_status==='2'">已解决</el-button>
          <el-button size="small" type="warning" @click="doTransition(detail,'4')" v-if="detail.current_status==='2'">未解决</el-button>
          <el-button size="small" type="primary" @click="doTransition(detail,'2')" v-if="detail.current_status==='4'">重新分配</el-button>
          <el-button size="small" @click="doTransition(detail,'3')" v-if="detail.current_status==='5'||detail.current_status==='4'">关单</el-button>
          <el-button size="small" type="danger" @click="doTransition(detail,'9')" v-if="['1','2','4','5'].includes(detail.current_status as string)">作废</el-button>
        </div>
      </template>
      <template #tabs>
        <el-tabs v-if="detail" v-model="activeTab" type="border-card" size="small">
          <el-tab-pane label="客户信息" name="customer">
            <CustomerInfoTab :store-id="detail.store_id as string" business-type="open" :current-record-id="detail.new_opening_id as string" />
          </el-tab-pane>
          <el-tab-pane label="设备明细" name="equip">
            <div style="text-align:right;margin-bottom:8px">
              <el-button size="small" type="primary" @click="showAddEq=true">新增设备</el-button>
            </div>
            <el-table :data="detailEquipments" size="small" v-loading="detailLoading" empty-text="暂无设备明细">
              <el-table-column prop="device_id" label="设备 EID" width="160" show-overflow-tooltip/>
              <el-table-column prop="delivery_id" label="送货单号" width="100"/>
              <el-table-column label="是否完成" width="70"><template #default="{row}"><el-tag size="small" :type="row.is_finish==='Y'?'success':'info'">{{ row.is_finish==='Y'?'完成':'未完成' }}</el-tag></template></el-table-column>
              <el-table-column label="是否换机" width="70"><template #default="{row}"><el-tag size="small" :type="row.is_change==='Y'?'warning':'info'">{{ row.is_change==='Y'?'换机':'否' }}</el-tag></template></el-table-column>
              <el-table-column prop="change_eid" label="换机EID" width="150" show-overflow-tooltip/>
              <el-table-column prop="from_custcard" label="来源磁卡号" width="110"/>
              <el-table-column prop="from_posid" label="来源POS" width="120" show-overflow-tooltip/>
              <el-table-column label="操作" width="60"><template #default="{row}"><el-button size="small" type="danger" @click="delEquipment(row)">删</el-button></template></el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="设备资产" name="asset">
            <AssetTab :store-id="(detail.store_id as string) || ''" />
          </el-tab-pane>
          <el-tab-pane label="业务附表" name="sub">
            <ItsmSubTables :maintenance-id="(detail.new_opening_id as string) || ''" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </ItsmDetailLayout>
    <el-dialog title="新增设备" v-model="showAddEq" width="400px" :close-on-click-modal="false">
      <el-form :model="eqForm" label-width="80px" size="small">
        <el-form-item label="设备EID"><el-input v-model="eqForm.device_id"/></el-form-item>
        <el-form-item label="送货单号"><el-input v-model="eqForm.delivery_id"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showAddEq=false">取消</el-button>
        <el-button size="small" type="primary" @click="doAddEq">确定</el-button>
      </template>
    </el-dialog>
    <el-dialog title="编辑开通单" v-model="showEdit" width="450px" :close-on-click-modal="false">
      <el-form :model="editForm" label-width="80px" size="small">
        <el-form-item label="负责人"><el-input v-model="editForm.firstor"/></el-form-item>
        <el-form-item label="详情"><el-input v-model="editForm.detail_description" type="textarea"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showEdit=false">取消</el-button>
        <el-button size="small" type="primary" @click="doEdit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import AppPagination from '@/components/common/AppPagination.vue'
import {useListPage} from '@/composables/useListPage'
import {useUserNames} from '@/composables/useUserNames'
import {useCustClass} from '@/composables/useCustClass'
import {fetchMaintenanceOpen, fetchMaintenanceOpenDetail, transitionMaintenanceOpen, updateMaintenanceOpen, addOpenEquipment, deleteOpenEquipment} from '@/api/itsm'
import type {MntRecord} from '@/api/itsm'
import {ref} from 'vue'
import {ElMessage} from 'element-plus'
import ItsmDetailLayout from './ItsmDetailLayout.vue'
import CustomerInfoTab from './CustomerInfoTab.vue'
import AssetTab from './AssetTab.vue'
import ItsmSubTables from './ItsmSubTables.vue'

const {items,loading,page,perPage,total,onSearch} = useListPage<MntRecord>(fetchMaintenanceOpen)
const {userName} = useUserNames()
const {className} = useCustClass()

const detail = ref<MntRecord | null>(null)
const activeTab = ref('customer')
const detailEquipments = ref<Record<string,unknown>[]>([])
const detailLoading = ref(false)

function open(row: MntRecord) {
  detail.value = row
  activeTab.value = 'customer'
  loadDetail()
}

async function loadDetail() {
  if (!detail.value?.new_opening_id) return
  detailLoading.value = true
  try {
    const r = await fetchMaintenanceOpenDetail(detail.value.new_opening_id as string)
    const data = (r as any)?.data || {}
    detail.value = data
    detailEquipments.value = (data.equipments || []) as any
  } catch {
    detailEquipments.value = []
  } finally {
    detailLoading.value = false
  }
}

function statusTag(s:string){const m:Record<string,string>={'1':'info','2':'primary','3':'success','4':'warning','5':'primary','9':'danger'};return m[s]||'info'}
function statusLabel(s:string){const m:Record<string,string>={'1':'新建','2':'分配','3':'关闭','4':'未解决','5':'已解决','9':'作废'};return m[s]||s}

const showAddEq = ref(false)
const eqForm = ref({device_id:'', delivery_id:''})
const showEdit = ref(false)
const editForm = ref<Record<string,unknown>>({})

function openEdit(row:MntRecord) {
  editForm.value = { firstor: row.firstor || '', detail_description: row.detail_description || '' }
  showEdit.value = true
}
async function doEdit() {
  try {
    await updateMaintenanceOpen(detail.value?.new_opening_id as string, editForm.value)
    ElMessage.success('已保存')
    showEdit.value = false
    onSearch({} as any)
    loadDetail()
  } catch {
    ElMessage.error('保存失败')
  }
}
async function doAddEq() {
  try {
    await addOpenEquipment(detail.value?.new_opening_id as string, eqForm.value)
    ElMessage.success('已添加')
    showAddEq.value = false
    eqForm.value = {device_id:'', delivery_id:''}
    loadDetail()
  } catch {
    ElMessage.error('添加失败')
  }
}
async function delEquipment(row:any) {
  try {
    await deleteOpenEquipment(detail.value?.new_opening_id as string, row.id as number)
    ElMessage.success('已删除')
    loadDetail()
  } catch {
    ElMessage.error('删除失败')
  }
}
async function doTransition(row:MntRecord,toStatus:string) {
  try {
    await transitionMaintenanceOpen(row.new_opening_id as string, {to_status: toStatus})
    ElMessage.success('流转成功')
    onSearch({} as any)
    loadDetail()
  } catch {
    ElMessage.error('流转失败')
  }
}
</script>
<style scoped>
.page{padding:0;display:flex;flex-direction:column;height:calc(100vh - 110px)}
.page-header{display:flex;justify-content:space-between;margin-bottom:0}
.page-header h2{font-size:18px;font-weight:600;margin:0}
.action-bar{display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;margin:8px 0}
</style>