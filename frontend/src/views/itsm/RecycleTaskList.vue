<template>
  <div class="page">
    <ItsmDetailLayout>
      <template #search>
        <div class="page-header"><h2>回收任务</h2></div>
      </template>
      <template #list>
        <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open" row-key="recycle_id">
          <el-table-column prop="recycle_id" label="回收单号" width="110"/>
          <el-table-column prop="cust_cd" label="门店" width="90"/>
          <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="statusTag(row.task_status as string)" size="small">{{ statusLabel(row.task_status as string) }}</el-tag></template></el-table-column>
          <el-table-column prop="asset_count" label="设备数" width="70" align="right"/>
          <el-table-column prop="create_time" label="创建日期" width="110"/>
          <el-table-column prop="completed_date" label="完成日期" width="110"/>
        </el-table>
        <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
      </template>
      <template #summary>
        <el-descriptions v-if="detail" :column="2" border size="small">
          <el-descriptions-item label="单号">{{ detail.recycle_id }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.task_status as string)" size="small">{{ statusLabel(detail.task_status as string) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="门店">{{ detail.cust_cd || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预计划">{{ detail.plan_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="应回收数">{{ detail.asset_count }}</el-descriptions-item>
          <el-descriptions-item label="实际回收数">{{ detail.actual_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="目标仓库">{{ detail.target_warehouse || '-' }}</el-descriptions-item>
          <el-descriptions-item label="分配人">{{ detail.assigned_to || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建">{{ detail.create_time }}</el-descriptions-item>
          <el-descriptions-item label="完成">{{ detail.completed_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template #actions>
        <div class="action-bar" v-if="detail">
          <el-button size="small" type="primary" @click="openEdit(detail)">编辑</el-button>
          <el-button size="small" type="primary" @click="doTransition(detail,'2')" v-if="detail.task_status==='1'">分配</el-button>
          <el-button size="small" type="success" @click="doTransition(detail,'5')" v-if="detail.task_status==='2'">已解决</el-button>
          <el-button size="small" type="warning" @click="doTransition(detail,'4')" v-if="detail.task_status==='2'">未解决</el-button>
          <el-button size="small" type="primary" @click="doTransition(detail,'2')" v-if="detail.task_status==='4'">重新分配</el-button>
          <el-button size="small" @click="doTransition(detail,'3')" v-if="detail.task_status==='5'||detail.task_status==='4'">关单</el-button>
          <el-button size="small" type="danger" @click="doTransition(detail,'9')" v-if="['1','2','4','5'].includes(detail.task_status as string)">作废</el-button>
        </div>
      </template>
      <template #tabs>
        <el-tabs v-if="detail" v-model="activeTab" type="border-card" size="small">
          <el-tab-pane label="客户信息" name="customer">
            <CustomerInfoTab :store-id="(detail.cust_cd as string) || ''" business-type="recycle" :current-record-id="(detail.recycle_id as string) || ''" />
          </el-tab-pane>
          <el-tab-pane label="回收明细" name="dtl">
            <div style="text-align:right;margin-bottom:8px">
              <el-button size="small" type="primary" @click="showAddDtl=true">新增回收明细</el-button>
            </div>
            <el-table :data="dtlList" size="small" v-loading="dtlLoading" empty-text="暂无">
              <el-table-column prop="asset_id" label="资产ID" width="140"/>
              <el-table-column prop="asset_type" label="类型" width="80"/>
              <el-table-column label="操作" width="50"><template #default="{row}"><el-button size="small" type="danger" @click="delDtl(row)">删</el-button></template></el-table-column>
            </el-table>
          </el-tab-pane>
          <ItsmSubTablePanes :maintenance-id="(detail.recycle_id as string) || ''" :area-cd="((detail as any).area_cd as string) || ''" :current-status="((detail as any).task_status as string) || ''" :main-record="detail" />
          <el-tab-pane label="设备资产" name="asset">
            <AssetTab :store-id="(detail.cust_cd as string) || ''" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </ItsmDetailLayout>
    <el-dialog title="新增回收明细" v-model="showAddDtl" width="400px" :close-on-click-modal="false">
      <el-form :model="dtlForm" label-width="80px" size="small">
        <el-form-item label="资产ID"><el-input v-model="dtlForm.asset_id"/></el-form-item>
        <el-form-item label="类型"><el-input v-model="dtlForm.asset_type" placeholder="OLD"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showAddDtl=false">取消</el-button>
        <el-button size="small" type="primary" @click="doAddDtl">确定</el-button>
      </template>
    </el-dialog>
    <el-dialog title="编辑回收任务" v-model="showEdit" width="450px" :close-on-click-modal="false">
      <el-form :model="editForm" label-width="80px" size="small">
        <el-form-item label="分配人"><el-input v-model="editForm.assigned_to"/></el-form-item>
        <el-form-item label="目标仓库"><el-input v-model="editForm.target_warehouse"/></el-form-item>
        <el-form-item label="备注"><el-input v-model="editForm.remark" type="textarea"/></el-form-item>
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
import {fetchRecycleTask, transitionRecycleTask, updateRecycleTask, fetchRecycleDetails, addRecycleDetail, deleteRecycleDetail} from '@/api/itsm'
import type {MntRecord} from '@/api/itsm'
import {ref} from 'vue'
import {ElMessage} from 'element-plus'
import ItsmDetailLayout from './ItsmDetailLayout.vue'
import CustomerInfoTab from './CustomerInfoTab.vue'
import AssetTab from './AssetTab.vue'
import ItsmSubTablePanes from './ItsmSubTablePanes.vue'

const {items,loading,page,perPage,total,onSearch} = useListPage<MntRecord>(fetchRecycleTask)

const detail = ref<MntRecord | null>(null)
const activeTab = ref('customer')

function statusTag(s:string){const m:Record<string,string>={'1':'info','2':'primary','3':'success','4':'warning','5':'primary','9':'danger'};return m[s]||'info'}
function statusLabel(s:string){const m:Record<string,string>={'1':'新建','2':'分配','3':'关闭','4':'未解决','5':'已解决','9':'作废'};return m[s]||s}

function open(row: MntRecord) {
  detail.value = row
  activeTab.value = 'customer'
  loadDtl()
}

const dtlLoading = ref(false)
const showAddDtl = ref(false)
const dtlForm = ref({asset_id:'', asset_type:'OLD'})
const dtlList = ref<Record<string,unknown>[]>([])
const showEdit = ref(false)
const editForm = ref<Record<string,unknown>>({})

async function loadDtl() {
  if (!detail.value?.recycle_id) return
  dtlLoading.value = true
  try {
    const r = await fetchRecycleDetails(detail.value.recycle_id as string)
    dtlList.value = (r as any)?.data || []
  } catch {
    dtlList.value = []
  } finally {
    dtlLoading.value = false
  }
}

function openEdit(row:MntRecord) {
  editForm.value = { assigned_to: row.assigned_to || '', target_warehouse: row.target_warehouse || '', remark: row.remark || '' }
  showEdit.value = true
}
async function doEdit() {
  try {
    await updateRecycleTask(detail.value?.recycle_id as string, editForm.value)
    ElMessage.success('已保存')
    showEdit.value = false
    onSearch({})
  } catch {
    ElMessage.error('保存失败')
  }
}
async function doAddDtl() {
  try {
    await addRecycleDetail(detail.value?.recycle_id as string, dtlForm.value)
    ElMessage.success('已添加')
    showAddDtl.value = false
    dtlForm.value = {asset_id:'', asset_type:'OLD'}
    loadDtl()
  } catch {
    ElMessage.error('添加失败')
  }
}
async function delDtl(row:any) {
  try {
    await deleteRecycleDetail(detail.value?.recycle_id as string, row.asset_id as string)
    ElMessage.success('已删除')
    loadDtl()
  } catch {
    ElMessage.error('删除失败')
  }
}
async function doTransition(row:MntRecord,toStatus:string) {
  try {
    await transitionRecycleTask(row.recycle_id as string, {to_status: toStatus})
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
