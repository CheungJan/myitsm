<template>
  <div class="page">
    <ItsmDetailLayout>
      <template #search>
        <div class="page-header"><h2>旧机翻新</h2></div>
      </template>
      <template #list>
        <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open" row-key="renew_id">
          <el-table-column prop="renew_id" label="翻新单号" width="110"/>
          <el-table-column label="公司" width="120"><template #default="{row}">{{ className(row.company_id) }}</template></el-table-column>
          <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="statusTag(row.current_status)" size="small">{{ statusLabel(row.current_status) }}</el-tag></template></el-table-column>
          <el-table-column label="负责人" width="80"><template #default="{row}">{{ userName(row.firstor) }}</template></el-table-column>
          <el-table-column label="创建日期" width="100"><template #default="{row}">{{ row.create_time || '-' }}</template></el-table-column>
          <el-table-column label="完成日期" width="100"><template #default="{row}">{{ row.close_time || '-' }}</template></el-table-column>
        </el-table>
        <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
      </template>
      <template #summary>
        <el-descriptions v-if="detail" :column="2" border size="small">
          <el-descriptions-item label="单号">{{ detail.renew_id }}</el-descriptions-item>
          <el-descriptions-item label="公司">{{ className(detail.company_id as string) }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.current_status as string)" size="small">{{ statusLabel(detail.current_status as string) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="负责人">{{ userName(detail.firstor as string) }}</el-descriptions-item>
          <el-descriptions-item label="请求时间">{{ detail.request_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="考核时间">{{ detail.expected_completion_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.create_time }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ detail.close_time||'-' }}</el-descriptions-item>
          <el-descriptions-item label="回访时间">{{ detail.revisit_time||'-' }}</el-descriptions-item>
          <el-descriptions-item label="是否补单">{{ detail.is_old==='Y'?'是':'否' }}</el-descriptions-item>
          <el-descriptions-item label="成功标志">{{ detail.is_success==='1'?'成功':'-' }}</el-descriptions-item>
          <el-descriptions-item label="是否入库">{{ detail.is_back==='Y'?'是':'否' }}</el-descriptions-item>
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
            <CustomerInfoTab :store-id="(detail.store_id as string) || ''" business-type="renovate" :current-record-id="(detail.renew_id as string) || ''" />
          </el-tab-pane>
          <el-tab-pane label="设备明细" name="equip">
            <div style="text-align:right;margin-bottom:8px">
              <el-button size="small" type="primary" @click="showAddRenEq=true">新增翻新设备</el-button>
            </div>
            <el-table :data="renEqList" size="small" v-loading="eqLoading" empty-text="暂无">
              <el-table-column prop="device_id" label="旧机EID" width="140"/>
              <el-table-column prop="new_device_id" label="新机EID" width="140"/>
              <el-table-column label="操作" width="50"><template #default="{row}"><el-button size="small" type="danger" @click="delRenEq(row)">删</el-button></template></el-table-column>
            </el-table>
          </el-tab-pane>
          <ItsmSubTablePanes :maintenance-id="(detail.renew_id as string) || ''" :area-cd="((detail as any).area_cd as string) || ''" :current-status="((detail as any).current_status as string) || ''" :main-record="detail" />
          <el-tab-pane label="设备资产" name="asset">
            <AssetTab :store-id="(detail.store_id as string) || ''" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </ItsmDetailLayout>
    <el-dialog title="新增翻新设备" v-model="showAddRenEq" width="400px" :close-on-click-modal="false">
      <el-form :model="renEqForm" label-width="90px" size="small">
        <el-form-item label="旧机EID"><el-input v-model="renEqForm.device_id"/></el-form-item>
        <el-form-item label="新机EID"><el-input v-model="renEqForm.new_device_id"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showAddRenEq=false">取消</el-button>
        <el-button size="small" type="primary" @click="doAddRenEq">确定</el-button>
      </template>
    </el-dialog>
    <el-dialog title="编辑翻新单" v-model="showEdit" width="450px" :close-on-click-modal="false">
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
import {fetchMaintenanceRenovate, transitionMaintenanceRenovate, updateMaintenanceRenovate, fetchRenovateEquipments, addRenovateEquipment, deleteRenovateEquipment} from '@/api/itsm'
import type {MntRecord} from '@/api/itsm'
import {ref} from 'vue'
import {ElMessage} from 'element-plus'
import ItsmDetailLayout from './ItsmDetailLayout.vue'
import CustomerInfoTab from './CustomerInfoTab.vue'
import AssetTab from './AssetTab.vue'
import ItsmSubTablePanes from './ItsmSubTablePanes.vue'

const {items,loading,page,perPage,total,onSearch} = useListPage<MntRecord>(fetchMaintenanceRenovate)
const {userName} = useUserNames()
const {className} = useCustClass()

const detail = ref<MntRecord | null>(null)
const activeTab = ref('customer')
const renEqList = ref<Record<string,unknown>[]>([])
const eqLoading = ref(false)
const showAddRenEq = ref(false)
const renEqForm = ref({device_id:'', new_device_id:''})
const showEdit = ref(false)
const editForm = ref<Record<string,unknown>>({})

function statusTag(s:string){const m:Record<string,string>={'1':'info','2':'primary','3':'success','4':'warning','5':'primary','9':'danger'};return m[s]||'info'}
function statusLabel(s:string){const m:Record<string,string>={'1':'新建','2':'分配','3':'关闭','4':'未解决','5':'已解决','9':'作废'};return m[s]||s}

function open(row: MntRecord) {
  detail.value = row
  activeTab.value = 'customer'
  loadEquip()
}

async function loadEquip() {
  if (!detail.value?.renew_id) return
  eqLoading.value = true
  try {
    const r = await fetchRenovateEquipments(detail.value.renew_id as string)
    renEqList.value = (r as any)?.data || []
  } catch {
    renEqList.value = []
  } finally {
    eqLoading.value = false
  }
}

function openEdit(row:MntRecord) {
  editForm.value = { firstor: row.firstor || '', detail_description: row.detail_description || '' }
  showEdit.value = true
}
async function doEdit() {
  try {
    await updateMaintenanceRenovate(detail.value?.renew_id as string, editForm.value)
    ElMessage.success('已保存')
    showEdit.value = false
    onSearch({})
  } catch {
    ElMessage.error('保存失败')
  }
}
async function doAddRenEq() {
  try {
    await addRenovateEquipment(detail.value?.renew_id as string, renEqForm.value)
    ElMessage.success('已添加')
    showAddRenEq.value = false
    renEqForm.value = {device_id:'', new_device_id:''}
    loadEquip()
  } catch {
    ElMessage.error('添加失败')
  }
}
async function delRenEq(row:any) {
  try {
    await deleteRenovateEquipment(detail.value?.renew_id as string, row.id as number)
    ElMessage.success('已删除')
    loadEquip()
  } catch {
    ElMessage.error('删除失败')
  }
}
async function doTransition(row:MntRecord,toStatus:string) {
  try {
    await transitionMaintenanceRenovate(row.renew_id as string, {to_status: toStatus})
    ElMessage.success('流转成功')
    onSearch({})
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