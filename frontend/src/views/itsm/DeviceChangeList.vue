<template>
  <div class="page">
    <ItsmDetailLayout>
      <template #search>
        <div class="page-header"><h2>磁卡号变更</h2></div>
      </template>
      <template #list>
        <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open" row-key="device_change_id">
          <el-table-column prop="device_change_id" label="变更单号" width="120"/>
          <el-table-column label="变更类型" width="90"><template #default="{row}">{{ ktLabel(row.change_type as string) }}</template></el-table-column>
          <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="statusTag(row.current_status as string)" size="small">{{ statusLabel(row.current_status as string) }}</el-tag></template></el-table-column>
          <el-table-column label="负责人" width="80"><template #default="{row}">{{ userName(row.firstor as string) }}</template></el-table-column>
          <el-table-column label="创建日期" width="100"><template #default="{row}">{{ row.create_time || '-' }}</template></el-table-column>
          <el-table-column label="完成日期" width="100"><template #default="{row}">{{ row.close_time || '-' }}</template></el-table-column>
        </el-table>
        <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
      </template>
      <template #summary>
        <el-descriptions v-if="detail" :column="2" border size="small">
          <el-descriptions-item label="单号">{{ detail.device_change_id }}</el-descriptions-item>
          <el-descriptions-item label="变更类型">{{ ktLabel(detail.change_type as string) }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.current_status as string)" size="small">{{ statusLabel(detail.current_status as string) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="负责人">{{ userName(detail.firstor as string) }}</el-descriptions-item>
          <el-descriptions-item label="原门店">{{ detail.store_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="新门店">{{ detail.new_store_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="新磁卡号">{{ detail.new_store_card || '-' }}</el-descriptions-item>
          <el-descriptions-item label="新联系人">{{ detail.new_contactor || '-' }}</el-descriptions-item>
          <el-descriptions-item label="新电话">{{ detail.new_tel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="新地址" :span="2">{{ detail.new_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="设备ID">{{ detail.device_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="请求时间">{{ detail.request_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="考核时间">{{ detail.expected_completion_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.create_time }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ detail.close_time||'-' }}</el-descriptions-item>
          <el-descriptions-item label="回访时间">{{ detail.revisit_time||'-' }}</el-descriptions-item>
          <el-descriptions-item label="是否补单">{{ detail.is_old==='Y'?'是':'否' }}</el-descriptions-item>
          <el-descriptions-item label="成功标志">{{ detail.is_success==='1'?'成功':'-' }}</el-descriptions-item>
          <el-descriptions-item label="店内移机">{{ detail.is_store_inside_change==='Y'?'是':'否' }}</el-descriptions-item>
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
            <CustomerInfoTab :store-id="(detail.store_id as string) || ''" business-type="device-change" :current-record-id="(detail.device_change_id as string) || ''" />
          </el-tab-pane>
          <ItsmSubTablePanes :maintenance-id="(detail.device_change_id as string) || ''" :area-cd="((detail as any).area_cd as string) || ''" :current-status="((detail as any).current_status as string) || ''" :main-record="detail" />
          <el-tab-pane label="设备资产" name="asset">
            <AssetTab :store-id="(detail.store_id as string) || ''" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </ItsmDetailLayout>
    <el-dialog title="编辑磁卡号变更" v-model="showEdit" width="450px" :close-on-click-modal="false">
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
import {fetchDeviceChange, transitionDeviceChange, updateDeviceChange} from '@/api/itsm'
import type {MntRecord} from '@/api/itsm'
import {useDict} from '@/composables/useDict'
import {ElMessage} from 'element-plus'
import {ref} from 'vue'
import ItsmDetailLayout from './ItsmDetailLayout.vue'
import CustomerInfoTab from './CustomerInfoTab.vue'
import AssetTab from './AssetTab.vue'
import ItsmSubTablePanes from './ItsmSubTablePanes.vue'

const {items,loading,page,perPage,total,onSearch} = useListPage<MntRecord>(fetchDeviceChange)
const {userName} = useUserNames()
const {dictLabel:ktLabel} = useDict('PL')

const detail = ref<MntRecord | null>(null)
const activeTab = ref('customer')

function statusTag(s:string){const m:Record<string,string>={'1':'info','2':'primary','3':'success','4':'warning','5':'primary','9':'danger'};return m[s]||'info'}
function statusLabel(s:string){const m:Record<string,string>={'1':'新建','2':'分配','3':'关闭','4':'未解决','5':'已解决','9':'作废'};return m[s]||s}

function open(row: MntRecord) {
  detail.value = row
  activeTab.value = 'customer'
}

const showEdit = ref(false)
const editForm = ref<Record<string,unknown>>({})
function openEdit(row:MntRecord) {
  editForm.value = { firstor: row.firstor || '', detail_description: row.detail_description || '' }
  showEdit.value = true
}
async function doEdit() {
  try {
    await updateDeviceChange(detail.value?.device_change_id as string, editForm.value)
    ElMessage.success('已保存')
    showEdit.value = false
    onSearch({})
  } catch {
    ElMessage.error('保存失败')
  }
}
async function doTransition(row:MntRecord,toStatus:string) {
  try {
    await transitionDeviceChange(row.device_change_id as string, {to_status: toStatus})
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