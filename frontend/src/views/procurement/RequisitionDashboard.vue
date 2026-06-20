<template>
  <div class="page">
    <div class="page-header"><h2>采购看板</h2></div>

    <h4 style="margin:8px 0;color:#606266">采购需求统计</h4>
    <el-row :gutter="16" style="margin-bottom:8px">
      <el-col :span="4"><el-tooltip content="系统中所有有效需求单的总数" placement="top"><el-card shadow="hover"><div class="stat"><div class="stat-val">{{ stats.total||0 }}</div><div class="stat-label">需求总数</div></div></el-card></el-tooltip></el-col>
      <el-col :span="5"><el-tooltip content="全部明细行均已到货入库的需求单数" placement="top"><el-card shadow="hover" @click="drillRequisition('已完成')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#67c23a">{{ stats.completed||0 }}</div><div class="stat-label">已完成</div></div></el-card></el-tooltip></el-col>
      <el-col :span="5"><el-tooltip content="已生成订单但尚未入库的需求单数（所有行均为已下单状态）" placement="top"><el-card shadow="hover" @click="drillRequisition('已下单')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#e6a23c">{{ stats.ordered||0 }}</div><div class="stat-label">已下单</div></div></el-card></el-tooltip></el-col>
      <el-col :span="5"><el-tooltip content="明细行状态不一致的需求单数（如部分已完成+部分未开始等混合情况，或行级为执行中）" placement="top"><el-card shadow="hover" @click="drillRequisition('执行中')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#e6a23c">{{ stats.executing||0 }}</div><div class="stat-label">执行中</div></div></el-card></el-tooltip></el-col>
      <el-col :span="4"><el-tooltip content="全部明细行均未生成任何订单的需求单数" placement="top"><el-card shadow="hover" @click="drillRequisition('未开始')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#909399">{{ stats.not_started||0 }}</div><div class="stat-label">未开始</div></div></el-card></el-tooltip></el-col>
      <el-col :span="4"><el-tooltip content="已作废的需求单数（手动作废，不参与任何业务流转）" placement="top"><el-card shadow="hover" @click="drillRequisition('voided')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#f56c6c">{{ stats.voided||0 }}</div><div class="stat-label">已作废</div></div></el-card></el-tooltip></el-col>
    </el-row>
    <div style="font-size:12px;color:#909399;margin-bottom:16px">四个状态互斥，每个需求单只属于其中一种：<b>已完成</b>=全部入库 · <b>已下单</b>=全部已下单未入库 · <b>执行中</b>=混合状态 · <b>未开始</b>=全部未下单</div>

    <h4 style="margin:16px 0 8px;color:#606266">采购订单统计</h4>
    <el-row :gutter="16" style="margin-bottom:8px">
      <el-col :span="6"><el-tooltip content="所有未作废的采购订单总数" placement="top"><el-card shadow="hover"><div class="stat"><div class="stat-val">{{ orderStats.total||0 }}</div><div class="stat-label">订单总数</div></div></el-card></el-tooltip></el-col>
      <el-col :span="6"><el-tooltip content="全部明细行的入库量≥订单量的订单数" placement="top"><el-card shadow="hover" @click="drillOrderStatus('已完成')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#67c23a">{{ orderStats.completed||0 }}</div><div class="stat-label">已完成入库</div></div></el-card></el-tooltip></el-col>
      <el-col :span="6"><el-tooltip content="部分明细行已到货但尚未全部入库的订单数" placement="top"><el-card shadow="hover" @click="drillOrderStatus('部分入库')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#e6a23c">{{ orderStats.partial||0 }}</div><div class="stat-label">部分入库</div></div></el-card></el-tooltip></el-col>
      <el-col :span="6"><el-tooltip content="所有明细行均未到货的订单数" placement="top"><el-card shadow="hover" @click="drillOrderStatus('未入库')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#909399">{{ orderStats.not_received||0 }}</div><div class="stat-label">未入库</div></div></el-card></el-tooltip></el-col>
    </el-row>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6"><el-tooltip content="审批状态为'待审核'的订单数（已送审等待审批人处理）" placement="top"><el-card shadow="hover" @click="drillOrderAudit('1')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#409eff">{{ orderAudit.pending||0 }}</div><div class="stat-label">待审核</div></div></el-card></el-tooltip></el-col>
      <el-col :span="6"><el-tooltip content="审批状态为'退回'的订单数（被审批人驳回，需修改后重新送审）" placement="top"><el-card shadow="hover" @click="drillOrderAudit('9')" style="cursor:pointer"><div class="stat"><div class="stat-val" style="color:#f56c6c">{{ orderAudit.rejected||0 }}</div><div class="stat-label">已退回</div></div></el-card></el-tooltip></el-col>
      <el-col :span="6"><el-tooltip content="已作废的订单数（手动作废，关联需求余额已释放）" placement="top"><el-card shadow="hover"><div class="stat"><div class="stat-val" style="color:#909399">{{ orderAudit.voided||0 }}</div><div class="stat-label">已作废</div></div></el-card></el-tooltip></el-col>
    </el-row>

    <el-card shadow="never" style="margin-bottom:16px">
      <template #header><span style="font-weight:600">Top 10 物料执行</span></template>
      <el-table :data="topItems" size="small" stripe highlight-current-row @row-click="showItemDetail">
        <el-table-column prop="itemcd" label="物料编码" width="100"/>
        <el-table-column label="物料名称" min-width="120"><template #default="{row}">{{ row.itemnm||row.itemcd }}</template></el-table-column>
        <el-table-column prop="total_plan" label="计划量" width="70"/>
        <el-table-column prop="total_ordered" label="已下单" width="70"/>
        <el-table-column prop="total_received" label="已入库" width="70"/>
        <el-table-column label="已退货" width="70"><template #default="{row}"><span :style="{color:row.return_rate>10?'#f56c6c':''}">{{ row.total_returned||0 }}</span></template></el-table-column>
        <el-table-column label="退货率" width="80"><template #default="{row}"><span :style="{color:row.return_rate>10?'#f56c6c':''}">{{ (row.return_rate||0)+'%' }}</span></template></el-table-column>
        <el-table-column label="完成率" width="100"><template #default="{row}"><el-progress :percentage="row.execution_rate||0" :status="row.execution_rate>=100?'success':''"/></template></el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header><div style="display:flex;align-items:center;gap:12px"><span style="font-weight:600;color:#f56c6c">采购需求逾期预警（计划日期超过7天未完成，共{{ overdueTotal }}条{{ overdueStatusFilter ? '，筛选：'+filteredOverdue.length+'条' : '' }}）</span><el-select v-model="overdueStatusFilter" size="small" style="width:110px" clearable placeholder="状态筛选" @change="filterOverdue"><el-option label="未开始" value="未开始"/><el-option label="已下单" value="已下单"/><el-option label="执行中" value="执行中"/></el-select></div></template>
      <el-table :data="filteredOverdue" size="small" stripe>
        <el-table-column prop="pcplanid" label="需求单号" width="110"/>
        <el-table-column prop="plandate" label="计划日期" width="110"/>
        <el-table-column label="当前日期" width="110"><template #default="{row}">{{ row.today }}</template></el-table-column>
        <el-table-column label="逾期天数" width="90" align="center"><template #default="{row}"><el-tag type="danger" size="small">{{ row.overdue_days }}天</el-tag></template></el-table-column>
        <el-table-column label="采购类型" width="80"><template #default="{row}">{{ row.pctyp||'-' }}</template></el-table-column>
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.execution_status==='已完成'?'success':row.execution_status==='未开始'?'info':'warning'" size="small">{{ row.execution_status }}</el-tag></template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
      </el-table>
    </el-card>

    <el-dialog :title="'物料执行明细 — ' + itemDetailItem" v-model="itemDetailVisible" width="800px">
      <el-table :data="itemDetails" v-loading="itemDetailLoading" size="small" stripe>
        <el-table-column prop="pcplanid" label="需求单号" width="110"/>
        <el-table-column prop="lineno" label="行号" width="60"/>
        <el-table-column prop="plan_qty" label="计划量" width="70"/>
        <el-table-column prop="ordered_qty" label="已下单" width="70"/>
        <el-table-column prop="received_qty" label="已入库" width="70"/>
        <el-table-column label="完成率" width="100"><template #default="{row}"><el-progress :percentage="row.execution_rate||0" :status="row.execution_rate>=100?'success':''"/></template></el-table-column>
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.execution_status==='已完成'?'success':'warning'" size="small">{{ row.execution_status }}</el-tag></template></el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog :title="drillTitle" v-model="drillVisible" width="800px">
      <el-table :data="drillData" v-loading="drillLoading" size="small" stripe>
        <el-table-column prop="pcplanid" label="需求单号" width="110" v-if="drillMode==='requisition'"/>
        <el-table-column prop="rgstbillid" label="订单号" width="110" v-if="drillMode==='order'"/>
        <el-table-column prop="suppliercd" label="供应商" width="90" v-if="drillMode==='order'"/>
        <el-table-column label="审批" width="80" v-if="drillMode==='order'"><template #default="{row}"><el-tag :type="row.auditflg==='2'?'success':'warning'" size="small">{{ row.auditflg }}</el-tag></template></el-table-column>
        <el-table-column prop="plandate" label="计划日期" width="100" v-if="drillMode==='requisition'"/>
        <el-table-column prop="gendate" label="日期" width="160" v-if="drillMode==='order'"/>
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.execution_status==='已完成'?'success':'warning'" size="small">{{ row.execution_status }}</el-tag></template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
      </el-table>
    </el-dialog>

    <el-card shadow="never" style="margin-top:16px">
      <template #header><span style="font-weight:600;color:#f56c6c">采购订单逾期预警（共{{ orderOverdue.length }}条）</span></template>
      <div v-if="orderOverdue.length===0" style="text-align:center;color:#909399;padding:20px">暂无逾期订单</div>
      <el-table v-else :data="orderOverdue" size="small" stripe>
        <el-table-column prop="rgstbillid" label="订单号" width="110"/>
        <el-table-column prop="suppliercd" label="供应商" width="90"/>
        <el-table-column label="审批" width="70"><template #default="{row}"><el-tag :type="row.auditflg==='2'?'success':'warning'" size="small">{{ row.auditflg==='1'?'待审核':row.auditflg }}</el-tag></template></el-table-column>
        <el-table-column label="类型" width="90"><template #default="{row}"><el-tag :type="row.type==='交付逾期'?'danger':'warning'" size="small">{{ row.type }}</el-tag></template></el-table-column>
        <el-table-column prop="gendate" label="相关日期" width="110"/>
        <el-table-column label="逾期天数" width="90" align="center"><template #default="{row}"><el-tag type="danger" size="small">{{ row.overdue_days }}天</el-tag></template></el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
<script setup lang="ts">import {ref,onMounted} from 'vue';import request from '@/api/request'

const stats=ref<Record<string,number>>({})
const topItems=ref<Record<string,unknown>[]>([])
const overdue=ref<Record<string,unknown>[]>([])
const overdueStatusFilter=ref('');const filteredOverdue=ref<Record<string,unknown>[]>([]);const overdueTotal=ref(0)
function filterOverdue() {
  if (overdueStatusFilter.value) {
    filteredOverdue.value=overdue.value.filter(r=>r.execution_status===overdueStatusFilter.value)
  } else {
    filteredOverdue.value=overdue.value
  }
}
const orderStats=ref<Record<string,number>>({})
const orderAudit=ref<Record<string,number>>({})
const itemDetailVisible=ref(false);const itemDetailItem=ref('');const itemDetails=ref<any[]>([]);const itemDetailLoading=ref(false)
async function showItemDetail(row: any) {
  itemDetailItem.value = row.itemcd + ' ' + (row.itemnm||'')
  itemDetailVisible.value = true; itemDetailLoading.value = true
  try {
    const r = await request.get('/procurement/dashboard/item-detail', { params: { itemcd: row.itemcd } })
    itemDetails.value = (r as any).data || []
  } catch { itemDetails.value = [] }
  finally { itemDetailLoading.value = false }
}
const drillVisible=ref(false);const drillLoading=ref(false);const drillTitle=ref('');const drillData=ref<any[]>([]);const drillMode=ref('')
const orderOverdue=ref<any[]>([])
async function drillRequisition(status: string) {
  drillMode.value='requisition';drillTitle.value='需求下钻 — '+status;drillVisible.value=true;drillLoading.value=true
  try { const r=await request.get('/procurement/dashboard/requisition-drill',{params:{status}}); drillData.value=(r as any).data||[] } catch { drillData.value=[] }
  finally { drillLoading.value=false }
}
async function drillOrderStatus(status: string) {
  drillMode.value='order';drillTitle.value='订单下钻 — '+status;drillVisible.value=true;drillLoading.value=true
  try { const r=await request.get('/procurement/dashboard/order-drill',{params:{status}}); drillData.value=(r as any).data||[] } catch { drillData.value=[] }
  finally { drillLoading.value=false }
}
async function drillOrderAudit(auditflg: string) {
  drillMode.value='order';drillTitle.value='订单下钻 — 待审核';drillVisible.value=true;drillLoading.value=true
  try { const r=await request.get('/procurement/dashboard/order-drill',{params:{auditflg}}); drillData.value=(r as any).data||[] } catch { drillData.value=[] }
  finally { drillLoading.value=false }
}

onMounted(async()=>{
  try{
    const r=await request.get('/procurement/dashboard/requisition')
    const d=(r as any).data||{}
    stats.value={...d.stats,voided:d.voided||0}
    topItems.value=d.top_items||[]
    overdue.value=d.overdue||[];filteredOverdue.value=overdue.value;overdueTotal.value=overdue.value.length
  }catch{/* */}
  try{
    const r=await request.get('/procurement/dashboard/order')
    const d=(r as any).data||{}
    orderStats.value=d.stats||{}
    orderAudit.value=d.audit_stats||{}
  }catch{/* */}
  try{
    const r=await request.get('/procurement/dashboard/order-overdue')
    orderOverdue.value=(r as any).data||[]
  }catch{/* */}
})
</script>
<style scoped>
.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}
.stat{text-align:center;padding:8px 0}.stat-val{font-size:28px;font-weight:700}.stat-label{font-size:13px;color:#909399;margin-top:4px}
</style>
