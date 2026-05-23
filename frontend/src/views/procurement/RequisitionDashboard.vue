<template>
  <div class="page">
    <div class="page-header"><h2>执行看板</h2></div>

    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6"><el-card shadow="hover"><div class="stat"><div class="stat-val">{{ stats.total||0 }}</div><div class="stat-label">需求总数</div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="stat"><div class="stat-val" style="color:#67c23a">{{ stats.completed||0 }}</div><div class="stat-label">已完成</div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="stat"><div class="stat-val" style="color:#e6a23c">{{ stats.in_progress||0 }}</div><div class="stat-label">执行中</div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="stat"><div class="stat-val" style="color:#909399">{{ stats.not_started||0 }}</div><div class="stat-label">未开始</div></div></el-card></el-col>
    </el-row>

    <el-card shadow="never" style="margin-bottom:16px">
      <template #header><span style="font-weight:600">Top 10 物料执行</span></template>
      <el-table :data="topItems" size="small" stripe>
        <el-table-column prop="itemcd" label="物料编码" width="100"/>
        <el-table-column prop="itemnm" label="物料名称" min-width="140"/>
        <el-table-column prop="total_plan" label="计划量" width="80"/>
        <el-table-column prop="total_ordered" label="已下单" width="80"/>
        <el-table-column prop="total_received" label="已入库" width="80"/>
        <el-table-column label="完成率" width="120"><template #default="{row}"><el-progress :percentage="row.execution_rate||0" :status="row.execution_rate>=100?'success':''"/></template></el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header><span style="font-weight:600;color:#f56c6c">逾期预警（计划日期超过7天未完成）</span></template>
      <el-table :data="overdue" size="small" stripe>
        <el-table-column prop="pcplanid" label="需求单号" width="110"/>
        <el-table-column prop="itemcd" label="物料编码" width="100"/>
        <el-table-column prop="itemnm" label="物料名称" min-width="140"/>
        <el-table-column prop="plandate" label="计划日期" width="100"/>
        <el-table-column prop="plan_qty" label="计划量" width="70"/>
        <el-table-column prop="ordered_qty" label="已下单" width="70"/>
        <el-table-column prop="received_qty" label="已入库" width="70"/>
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.execution_status==='已完成'?'success':row.execution_status==='未开始'?'info':'warning'" size="small">{{ row.execution_status }}</el-tag></template></el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
<script setup lang="ts">import {ref,onMounted} from 'vue';import request from '@/api/request'

const stats=ref<Record<string,number>>({})
const topItems=ref<Record<string,unknown>[]>([])
const overdue=ref<Record<string,unknown>[]>([])

onMounted(async()=>{
  try{
    const r=await request.get('/procurement/dashboard/requisition')
    const d=(r as any).data||{}
    stats.value=d.stats||{}
    topItems.value=d.top_items||[]
    overdue.value=d.overdue||[]
  }catch{/* */}
})
</script>
<style scoped>
.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}
.stat{text-align:center;padding:8px 0}.stat-val{font-size:28px;font-weight:700}.stat-label{font-size:13px;color:#909399;margin-top:4px}
</style>
