<template>
  <div class="page"><div class="page-header"><h2>日常维修工单</h2></div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>工单号</label><el-input v-model="search.id" placeholder="工单号" size="small" style="width:140px" clearable/></div>
        <div class="field"><label>状态</label><el-select v-model="search.status" size="small" style="width:110px" clearable><el-option label="待分派" value="0"/><el-option label="维修中" value="1"/><el-option label="待关单" value="2"/><el-option label="已完成" value="3"/></el-select></div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open">
        <el-table-column prop="maintenance_id" label="工单号" width="120"/><el-table-column prop="store_id" label="门店" width="90"/>
        <el-table-column prop="short_description" label="故障简述" min-width="140" show-overflow-tooltip/>
        <el-table-column label="优先级" width="70"><template #default="{row}">{{ row.priority || '-' }}</template></el-table-column>
        <el-table-column label="状态" width="80" align="center"><template #default="{row}"><el-tag :type="statusTag(row.current_status)" size="small">{{ statusLabel(row.current_status) }}</el-tag></template></el-table-column>
        <el-table-column label="故障类型" width="80"><template #default="{row}">{{ row.fault_type || '-' }}</template></el-table-column>
        <el-table-column prop="firstor" label="维修员" width="80"/>
        <el-table-column label="请求日期" width="100"><template #default="{row}">{{ row.request_time || row.create_time || '-' }}</template></el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <el-dialog :title="'工单详情 — '+(detail?.maintenance_id||'')" v-model="drawer" width="650px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="工单号">{{ detail.maintenance_id }}</el-descriptions-item>
          <el-descriptions-item label="门店">{{ detail.store_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="故障简述" :span="2">{{ detail.short_description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="故障类型">{{ detail.fault_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ detail.priority || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.current_status)" size="small">{{ statusLabel(detail.current_status) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="维修员">{{ detail.firstor || '-' }}</el-descriptions-item>
          <el-descriptions-item label="请求日期">{{ detail.request_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="完成日期">{{ detail.close_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.detail_description || detail.memo || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">import {reactive} from 'vue';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {fetchMaintenanceDaily} from '@/api/itsm';import type {MntRecord} from '@/api/itsm'
const{items,loading,page,perPage,total,onSearch}=useListPage<MntRecord>(fetchMaintenanceDaily)
const{drawer,detail,open}=useDetailDrawer<MntRecord>()
const search=reactive({id:'',status:''})
function statusTag(s:unknown){const m:Record<string,string>={'0':'warning','1':'primary','2':'info','3':'success'};return m[s as string]||'info'}
function statusLabel(s:unknown){const m:Record<string,string>={'0':'待分派','1':'维修中','2':'待关单','3':'已完成'};return m[s as string]||s as string}
function doSearch(){const p:Record<string,string>={};if(search.id)p.maintenance_id=search.id;if(search.status)p.current_status=search.status;onSearch(p)}</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}.search-bar{display:flex;gap:12px;align-items:center}.field{display:flex;align-items:center;gap:6px}.field label{font-size:13px;color:#606266}</style>