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
      <el-table :data="items" v-loading="loading" stripe size="small">
        <el-table-column prop="maintenance_id" label="工单号" width="110"/><el-table-column prop="custnm" label="客户" min-width="140" show-overflow-tooltip/>
        <el-table-column prop="fault_desc" label="故障描述" min-width="150" show-overflow-tooltip/>
        <el-table-column label="状态" width="80" align="center"><template #default="{row}"><el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="gendate" label="创建日期" width="110"/>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>
  </div>
</template>
<script setup lang="ts">import {reactive} from 'vue';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {fetchMaintenanceDaily} from '@/api/itsm';import type {MntRecord} from '@/api/itsm'
const{items,loading,page,perPage,total,onSearch}=useListPage<MntRecord>(fetchMaintenanceDaily)
const search=reactive({id:'',status:''})
function statusTag(s:unknown){const m:Record<string,string>={'0':'warning','1':'primary','2':'info','3':'success'};return m[s as string]||'info'}
function statusLabel(s:unknown){const m:Record<string,string>={'0':'待分派','1':'维修中','2':'待关单','3':'已完成'};return m[s as string]||s as string}
function doSearch(){const p:Record<string,string>={};if(search.id)p.maintenance_id=search.id;if(search.status)p.status=search.status;onSearch(p)}</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}.search-bar{display:flex;gap:12px;align-items:center}.field{display:flex;align-items:center;gap:6px}.field label{font-size:13px;color:#606266}</style>