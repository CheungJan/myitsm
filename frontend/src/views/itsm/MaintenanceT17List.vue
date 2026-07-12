<template>
  <div class="page">
    <ItsmDetailLayout>
      <template #search>
        <div class="search-bar">
          <div class="field"><label>状态</label><el-select v-model="searchStatus" size="small" style="width:110px" clearable @change="doSearch"><el-option label="新建" value="1"/><el-option label="分配" value="2"/><el-option label="已解决" value="5"/><el-option label="关闭" value="3"/></el-select></div>
          <el-button type="primary" size="small" @click="doSearch">查询</el-button>
          <h2 style="margin:0 0 0 auto;font-size:16px;font-weight:600">保养工单</h2>
        </div>
      </template>

      <template #list>
        <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open" row-key="daily_maintenance_id" max-height="calc(100vh - 200px)">
          <el-table-column prop="daily_maintenance_id" label="保养单号" width="110"/>
          <el-table-column label="门店" width="90"><template #default="{row}">{{ row.store_cust_card || custCard(row.store_id) }}</template></el-table-column>
          <el-table-column prop="short_description" label="简述" min-width="140" show-overflow-tooltip/>
          <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="statusTag(row.current_status)" size="small">{{ statusLabel(row.current_status) }}</el-tag></template></el-table-column>
          <el-table-column label="工程师" width="80"><template #default="{row}">{{ userName(row.firstor) }}</template></el-table-column>
          <el-table-column label="请求时间" width="110"><template #default="{row}">{{ row.request_time || '-' }}</template></el-table-column>
          <el-table-column label="关单时间" width="110"><template #default="{row}">{{ row.close_time || '-' }}</template></el-table-column>
        </el-table>
        <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:8px;justify-content:flex-end"/>
      </template>

      <template #summary v-if="detail">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="保养单号">{{ detail.daily_maintenance_id }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.current_status)" size="small">{{ statusLabel(detail.current_status) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="门店">{{ detail.store_cust_card || custCard(detail.store_id) }}</el-descriptions-item>
          <el-descriptions-item label="简述" :span="2">{{ detail.short_description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="工程师">{{ userName(detail.firstor) }}</el-descriptions-item>
          <el-descriptions-item label="请求时间">{{ detail.request_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关单时间">{{ detail.close_time || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>

      <template #actions v-if="detail">
        <div style="display:flex;gap:8px">
          <el-button size="small" type="primary" @click="doTransition(detail,'2')" v-if="detail.current_status==='1'">分派</el-button>
          <el-button size="small" type="success" @click="doTransition(detail,'5')" v-if="detail.current_status==='2'">完成</el-button>
          <el-button size="small" type="warning" @click="doTransition(detail,'3')" v-if="detail.current_status==='5'">关单</el-button>
        </div>
      </template>

      <template #tabs v-if="detail">
        <el-tabs v-model="activeTab" type="border-card" size="small">
          <el-tab-pane label="客户信息" name="customer">
            <CustomerInfoTab :store-id="(detail.store_id as string) || ''" business-type="maintenance" :current-record-id="(detail.daily_maintenance_id as string) || ''" />
          </el-tab-pane>
          <el-tab-pane label="设备资产" name="asset">
            <AssetTab :store-id="(detail.store_id as string) || ''" />
          </el-tab-pane>
          <el-tab-pane label="业务附表" name="sub">
            <ItsmSubTables :maintenance-id="(detail.daily_maintenance_id as string) || ''" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </ItsmDetailLayout>
  </div>
</template>
<script setup lang="ts">import {ref} from 'vue';import {ElMessage} from 'element-plus';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {useUserNames} from '@/composables/useUserNames';import {useCustomerCards} from '@/composables/useCustomerCards';import {fetchMaintenanceT17, transitionMaintenanceT17} from '@/api/itsm';import type {MntRecord} from '@/api/itsm';import ItsmDetailLayout from './ItsmDetailLayout.vue';import CustomerInfoTab from './CustomerInfoTab.vue';import AssetTab from './AssetTab.vue';import ItsmSubTables from './ItsmSubTables.vue'
const{items,loading,page,perPage,total,onSearch}=useListPage<MntRecord>(fetchMaintenanceT17)
const{detail,open}=useDetailDrawer<MntRecord>()
const{userName}=useUserNames();const{custCard}=useCustomerCards()
const activeTab=ref('customer');const searchStatus=ref('')
function statusTag(s:string){const m:Record<string,string>={'1':'info','2':'primary','3':'success','4':'warning','5':'primary','9':'danger'};return m[s]||'info'}
function statusLabel(s:string){const m:Record<string,string>={'1':'新建','2':'分配','3':'关闭','4':'未解决','5':'已解决','9':'作废'};return m[s]||s}
function doSearch(){const p:Record<string,string>={};if(searchStatus.value)p.current_status=searchStatus.value;onSearch(p)}
async function doTransition(row:MntRecord,toStatus:string){try{await transitionMaintenanceT17(row.daily_maintenance_id as string,{to_status:toStatus});ElMessage.success('流转成功');onSearch({})}catch{ElMessage.error('流转失败')}}</script>
<style scoped>.page{padding:0}.search-bar{display:flex;gap:12px;align-items:center}.field{display:flex;align-items:center;gap:6px}.field label{font-size:13px;color:#606266}</style>
