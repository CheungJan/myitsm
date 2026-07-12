<template>
  <div class="page">
    <ItsmDetailLayout>
      <template #search>
        <div class="search-bar">
          <div class="field"><label>工单号</label><el-input v-model="search.id" placeholder="工单号" size="small" style="width:140px" clearable/></div>
          <div class="field"><label>状态</label><el-select v-model="search.status" size="small" style="width:110px" clearable><el-option label="新建" value="1"/><el-option label="分配" value="2"/><el-option label="已解决" value="5"/><el-option label="关闭" value="3"/><el-option label="作废" value="9"/></el-select></div>
          <div class="field"><label>故障类型</label><el-select v-model="search.fault_type" size="small" style="width:120px" clearable><el-option v-for="f in faultTypes" :key="f.code_cd" :label="f.code_nm" :value="f.code_cd"/></el-select></div>
          <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
          <h2 style="margin:0 0 0 auto;font-size:16px;font-weight:600">日常维修工单</h2>
        </div>
      </template>

      <template #list>
        <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open" row-key="maintenance_id" max-height="calc(100vh - 200px)">
          <el-table-column prop="maintenance_id" label="工单号" width="120"/>
          <el-table-column label="门店" width="80"><template #default="{row}">{{ row.store_cust_card || custCard(row.store_id as string) }}</template></el-table-column>
          <el-table-column prop="short_description" label="故障简述" min-width="120" show-overflow-tooltip/>
          <el-table-column label="状态" width="70" align="center"><template #default="{row}"><el-tag :type="statusTag(row.current_status)" size="small">{{ statusLabel(row.current_status) }}</el-tag></template></el-table-column>
          <el-table-column label="紧急" width="55"><template #default="{row}">{{ elLabel(row.emergency_level) }}</template></el-table-column>
          <el-table-column label="工程师" width="70"><template #default="{row}">{{ userName(row.firstor) }}</template></el-table-column>
          <el-table-column label="考核时间" width="100"><template #default="{row}">{{ row.expected_completion_time || '-' }}</template></el-table-column>
          <el-table-column label="创建" width="100"><template #default="{row}">{{ row.create_time || '-' }}</template></el-table-column>
        </el-table>
        <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:8px;justify-content:flex-end"/>
      </template>

      <template #summary v-if="detail">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="工单号">{{ detail.maintenance_id }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.current_status)" size="small">{{ statusLabel(detail.current_status) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="门店">{{ detail.store_cust_card || custCard(detail.store_id as string) }}</el-descriptions-item>
          <el-descriptions-item label="故障简述" :span="2">{{ detail.short_description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="设备">{{ detail.device_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="故障类型">{{ flLabel(detail.fault_type) }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">{{ svLabel(detail.servrity) }}</el-descriptions-item>
          <el-descriptions-item label="紧急程度">{{ elLabel(detail.emergency_level) }}</el-descriptions-item>
          <el-descriptions-item label="工程师">{{ userName(detail.firstor) }}</el-descriptions-item>
          <el-descriptions-item label="考核时间">{{ detail.expected_completion_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关单时间">{{ detail.close_time || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>

      <template #actions v-if="detail">
        <div style="display:flex;gap:8px">
          <el-button size="small" type="primary" @click="doTransition(detail,'2')" v-if="detail.current_status==='1'">分派</el-button>
          <el-button size="small" type="success" @click="doTransition(detail,'5')" v-if="detail.current_status==='2'">完成维修</el-button>
          <el-button size="small" type="warning" @click="doTransition(detail,'3')" v-if="detail.current_status==='5'">关单</el-button>
          <el-button size="small" type="danger" @click="doTransition(detail,'9')" v-if="['1','2','4','5'].includes(detail.current_status as string)">作废</el-button>
        </div>
      </template>

      <template #tabs v-if="detail">
        <el-tabs v-model="activeTab" type="border-card" size="small">
          <el-tab-pane label="客户信息" name="customer">
            <CustomerInfoTab :store-id="(detail.store_id as string) || ''" business-type="daily" :current-record-id="(detail.maintenance_id as string) || ''" />
          </el-tab-pane>
          <el-tab-pane label="设备资产" name="asset">
            <AssetTab :store-id="(detail.store_id as string) || ''" />
          </el-tab-pane>
          <el-tab-pane label="业务附表" name="sub">
            <ItsmSubTables :maintenance-id="(detail.maintenance_id as string) || ''" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </ItsmDetailLayout>
  </div>
</template>
<script setup lang="ts">import {reactive,ref,onMounted} from 'vue';import {fetchSyscodes} from '@/api/master';import {ElMessage} from 'element-plus';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {useUserNames} from '@/composables/useUserNames';import {useCustomerCards} from '@/composables/useCustomerCards';import {fetchMaintenanceDaily, transitionMaintenanceDaily} from '@/api/itsm';import type {MntRecord} from '@/api/itsm';import {useDict} from '@/composables/useDict';import ItsmDetailLayout from './ItsmDetailLayout.vue';import CustomerInfoTab from './CustomerInfoTab.vue';import AssetTab from './AssetTab.vue';import ItsmSubTables from './ItsmSubTables.vue'
const{items,loading,page,perPage,total,onSearch}=useListPage<MntRecord>(fetchMaintenanceDaily)
const{detail,open}=useDetailDrawer<MntRecord>()
const{userName}=useUserNames();const{custCard}=useCustomerCards()
const{dictLabel:svLabel}=useDict('SV');const{dictLabel:elLabel}=useDict('EL');const{dictLabel:flLabel}=useDict('FL')
const activeTab=ref('customer')
const search=reactive({id:'',status:'',fault_type:''});const faultTypes=ref<{code_cd:string;code_nm:string}[]>([])
onMounted(async()=>{try{const r=await fetchSyscodes('FL');faultTypes.value=r.data||[]}catch{}})
function statusTag(s:unknown){const m:Record<string,string>={'1':'info','2':'primary','3':'success','4':'warning','5':'primary','9':'danger'};return m[s as string]||'info'}
function statusLabel(s:unknown){const m:Record<string,string>={'1':'新建','2':'分配','3':'关闭','4':'未解决','5':'已解决','9':'作废'};return m[s as string]||s as string}
function doSearch(){const p:Record<string,string>={};if(search.id)p.maintenance_id=search.id;if(search.status)p.current_status=search.status;if(search.fault_type)p.fault_type=search.fault_type;onSearch(p)}
async function doTransition(row:MntRecord,toStatus:string){try{await transitionMaintenanceDaily(row.maintenance_id as string,{to_status:toStatus});ElMessage.success('流转成功');onSearch({})}catch{ElMessage.error('流转失败')}}</script>
<style scoped>.page{padding:0}.search-bar{display:flex;gap:12px;align-items:center}.field{display:flex;align-items:center;gap:6px}.field label{font-size:13px;color:#606266}</style>
