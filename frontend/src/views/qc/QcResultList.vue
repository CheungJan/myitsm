<template><div class="page"><div class="page-header"><h2>质检结果</h2></div>

  <el-card shadow="never" style="margin-bottom:16px"><div class="search-bar"><div class="field"><label>搜索</label><el-input v-model="s.search" placeholder="批次号/来源单" size="small" style="width:160px" clearable @keyup.enter="doSearch"/></div><el-input v-model="s.eid" placeholder="EID" size="small" style="width:140px;margin-left:8px" clearable @keyup.enter="doSearch"/><el-date-picker v-model="s.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" size="small" style="width:240px;margin-left:8px" value-format="YYYY-MM-DD" @change="doSearch"/><el-select v-model="s.auditflg" placeholder="审核状态" size="small" style="width:120px;margin-left:8px" clearable @change="doSearch"><el-option label="草稿" value="0"/><el-option label="已审核" value="1"/><el-option label="已退回" value="8"/><el-option label="已作废" value="V"/></el-select><el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button></div></el-card>

  <!-- 统计面板 -->
  <el-card shadow="never" style="margin-bottom:16px" v-if="stats.length"><div style="display:flex;gap:16px;flex-wrap:wrap"><div v-for="st in stats" :key="st.qcstatus" style="text-align:center;padding:8px 16px;background:#f5f7fa;border-radius:6px"><div style="font-size:20px;font-weight:600;color:#409eff">{{st.cnt}}</div><div style="font-size:12px;color:#909399">{{qcLabel(st.qcstatus)}}</div></div></div></el-card>

  <!-- OV5 看板 -->
  <el-card shadow="never" style="margin-bottom:16px"><div style="display:flex;gap:16px;flex-wrap:wrap"><el-card shadow="hover" @click="drillOvw('pending')" style="cursor:pointer;flex:1;min-width:120px"><div style="text-align:center"><div style="font-size:24px;font-weight:600;color:#1677ff">{{comp.pending_ov5}}</div><div style="font-size:12px;color:#909399;margin-top:4px">待质检 OV=5</div></div></el-card><el-card shadow="hover" @click="drillOvw('done')" style="cursor:pointer;flex:1;min-width:120px"><div style="text-align:center"><div style="font-size:24px;font-weight:600;color:#52c41a">{{comp.total_ov5-comp.pending_ov5}}</div><div style="font-size:12px;color:#909399;margin-top:4px">已完成 OV=5</div></div></el-card><el-card shadow="hover" @click="drillOvw('iv11')" style="cursor:pointer;flex:1;min-width:120px"><div style="text-align:center"><div style="font-size:24px;font-weight:600;color:#fa8c16">{{comp.iv11_count}}</div><div style="font-size:12px;color:#909399;margin-top:4px">IV=11 入库单</div></div></el-card><el-card shadow="hover" @click="drillOvw('ovout')" style="cursor:pointer;flex:1;min-width:120px"><div style="text-align:center"><div style="font-size:24px;font-weight:600;color:#ff4d4f">{{comp.ov_out_count}}</div><div style="font-size:12px;color:#909399;margin-top:4px">不合格出库单</div></div></el-card></div></el-card>

  <!-- 批次表 -->
  <el-card shadow="never"><el-table :data="items" v-loading="loading" stripe size="small" @expand-change="onExpand" row-key="batch_id">
    <el-table-column type="index" label="#" width="50" :index="(i:number)=>(page-1)*perPage+i+1"/><el-table-column type="expand"><template #default="{row}">
      <div v-if="(row._records||[]).length===1" style="padding:8px 24px">
        <h4 style="margin:8px 0">子记录: {{row._records[0].qcbillid}}</h4>
        <div style="display:flex;gap:8px;align-items:center"><span style="color:#909399;font-size:12px">来源: {{row.refbillid}}</span><span v-if="row._records[0].wh_bill" style="color:#409eff;font-size:12px">{{row._records[0].wh_bill}}</span><span v-if="refInbill(row._records[0])" style="color:#909399;font-size:12px">入库: {{refInbill(row._records[0])}}</span><el-tag :type="qcTagType(row._records[0].qcstatus)" size="small">{{qcLabel(row._records[0].qcstatus)}}</el-tag></div>
        <template v-if="(row._records[0].details||[]).length"><h4 style="margin:12px 0 4px">明细（按产品）</h4><el-table :data="row._records[0].details" size="small" border><el-table-column type="index" label="#" width="45"/><el-table-column label="判定" width="80"><template #default="{row:r}">{{qcLabel(r.qcstatus||row._records[0].qcstatus)}}</template></el-table-column><el-table-column prop="itemcd" label="物料编码" width="90"/><el-table-column prop="item_nm" label="物料名称" min-width="120"><template #default="{row:r}">{{r.item_nm||'-'}}</template></el-table-column><el-table-column prop="qcqty" label="质检数" width="70"/><el-table-column prop="inqty" label="入库数" width="70"/><el-table-column label="批次日期" width="100"><template #default="{row:r}">{{r.prddate||'-'}}</template></el-table-column><el-table-column label="商品属性" width="80"><template #default="{row:r}">{{r.itemtyp?qcLabel(r.itemtyp):'-'}}</template></el-table-column><el-table-column prop="fault_desc" label="不良原因" width="120"/></el-table></template>
        <template v-if="(row._records[0].eid_details||[]).length"><h4 style="margin:12px 0 4px">明细（按EID）</h4><el-table :data="row._records[0].eid_details" size="small" border><el-table-column type="index" label="#" width="45"/><el-table-column label="判定" width="80"><template #default="{row:r}">{{qcLabel(r.qcstatus||row._records[0].qcstatus)}}</template></el-table-column><el-table-column prop="itemcd" label="物料编码" width="90"/><el-table-column prop="item_nm" label="物料名称" min-width="100"><template #default="{row:r}">{{r.item_nm||'-'}}</template></el-table-column><el-table-column prop="eid" label="EID" width="140"><template #default="{row:r}"><span :style="s.eid&&r.eid===s.eid?'background:#fff3cd;padding:2px 6px;border-radius:3px;font-weight:600':''">{{r.eid}}</span></template></el-table-column><el-table-column prop="manuf_seq" label="原厂序号" width="120"/><el-table-column prop="qcqty" label="质检数" width="70"/><el-table-column prop="inqty" label="入库数" width="70"/><el-table-column label="商品属性" width="80"><template #default="{row:r}">{{r.itemtyp?qcLabel(r.itemtyp):'-'}}</template></el-table-column><el-table-column prop="fault_desc" label="不良原因" width="120"/></el-table></template>
      </div>
      <!-- 多条子记录：显示子记录表，明细直接展开在下方 -->
      <div v-else-if="(row._records||[]).length>1" style="padding:4px 24px">
        <div v-for="sub in row._records" :key="sub.qcbillid" style="margin-bottom:12px;border:1px solid #eee;border-radius:4px;padding:8px">
          <div style="display:flex;gap:12px;align-items:center;margin-bottom:8px">
            <span style="font-weight:600">{{sub.qcbillid}}</span>
            <span style="color:#909399;font-size:12px">来源: {{row.refbillid}}</span>
            <span v-if="refInbill(sub)" style="color:#909399;font-size:12px">入库: {{refInbill(sub)}}</span>
            <span v-if="sub.wh_bill" style="color:#409eff;font-size:12px">{{sub.wh_bill}}</span>
            <el-tag :type="qcTagType(sub.qcstatus)" size="small">{{qcLabel(sub.qcstatus)}}</el-tag>
            <el-tag :type="sub.auditflg==='1'?'success':sub.auditflg==='8'?'danger':sub.auditflg==='V'?'info':'warning'" size="small">{{sub.auditflg==='1'?'已审':sub.auditflg==='8'?'已退回':sub.auditflg==='V'?'已作废':'待审'}}</el-tag>
            <span style="color:#909399;font-size:12px">{{formatDate(sub.gendate)}}</span>
          </div>
          <template v-if="(sub.details||[]).length">
            <h4 style="margin:4px 0;font-size:13px">明细（按产品）</h4>
            <el-table :data="sub.details" size="small" border><el-table-column type="index" label="#" width="45"/><el-table-column label="判定" width="80"><template #default="{row:r}">{{qcLabel(r.qcstatus||sub.qcstatus)}}</template></el-table-column><el-table-column prop="itemcd" label="物料编码" width="90"/><el-table-column prop="item_nm" label="物料名称" min-width="120"><template #default="{row:r}">{{r.item_nm||'-'}}</template></el-table-column><el-table-column prop="qcqty" label="质检数" width="70"/><el-table-column prop="inqty" label="入库数" width="70"/><el-table-column label="批次日期" width="100"><template #default="{row:r}">{{r.prddate||'-'}}</template></el-table-column><el-table-column label="商品属性" width="80"><template #default="{row:r}">{{r.itemtyp?qcLabel(r.itemtyp):'-'}}</template></el-table-column><el-table-column prop="fault_desc" label="不良原因" width="120"/></el-table>
          </template>
          <template v-if="(sub.eid_details||[]).length">
            <h4 style="margin:4px 0;font-size:13px">明细（按EID）</h4>
            <el-table :data="sub.eid_details" size="small" border><el-table-column type="index" label="#" width="45"/><el-table-column label="判定" width="80"><template #default="{row:r}">{{qcLabel(r.qcstatus||sub.qcstatus)}}</template></el-table-column><el-table-column prop="itemcd" label="物料编码" width="90"/><el-table-column prop="item_nm" label="物料名称" min-width="100"><template #default="{row:r}">{{r.item_nm||'-'}}</template></el-table-column><el-table-column prop="eid" label="EID" width="140"><template #default="{row:r}"><span :style="s.eid&&r.eid===s.eid?'background:#fff3cd;padding:2px 6px;border-radius:3px;font-weight:600':''">{{r.eid}}</span></template></el-table-column><el-table-column prop="manuf_seq" label="原厂序号" width="120"/><el-table-column prop="qcqty" label="质检数" width="70"/><el-table-column prop="inqty" label="入库数" width="70"/><el-table-column label="商品属性" width="80"><template #default="{row:r}">{{r.itemtyp?qcLabel(r.itemtyp):'-'}}</template></el-table-column><el-table-column prop="fault_desc" label="不良原因" width="120"/></el-table>
          </template>
        </div>
      </div>
    </template></el-table-column>
    <el-table-column prop="batch_id" label="批次号" width="110"/>
    <el-table-column prop="refbillid" label="来源单据" width="120"/>
    <el-table-column label="判定汇总" min-width="200"><template #default="{row}"><el-tag v-if="row.ga_count" type="success" size="small">GA:{{row.ga_count}}</el-tag><el-tag v-if="row.gb_count" type="success" size="small">GB:{{row.gb_count}}</el-tag><el-tag v-if="row.gc_count" type="success" size="small">GC:{{row.gc_count}}</el-tag><el-tag v-if="row.bf_count" type="danger" size="small">BF:{{row.bf_count}}</el-tag><el-tag v-if="row.bh_count" type="warning" size="small">BH:{{row.bh_count}}</el-tag><el-tag v-if="row.th_count" type="info" size="small">TH:{{row.th_count}}</el-tag></template></el-table-column>
    <el-table-column prop="total_count" label="总数" width="60"/>
    <el-table-column label="审核状态" width="80"><template #default="{row}"><el-tag v-if="row.auditflg==='1'" type="success" size="small">已审核</el-tag><el-tag v-else-if="row.auditflg==='8'" type="danger" size="small">已退回</el-tag><el-tag v-else-if="row.auditflg==='V'" type="info" size="small">已作废</el-tag><el-tag v-else type="warning" size="small">草稿</el-tag></template></el-table-column>
    <el-table-column label="日期" width="140"><template #default="{row}">{{formatDate(row.gendate)}}</template></el-table-column>
    <el-table-column label="操作员" width="80"><template #default="{row}">{{userName(row.opercd)}}</template></el-table-column>
    <el-table-column label="审核人" width="80"><template #default="{row}">{{userName(row.auditman)}}</template></el-table-column>
    <!-- 审核操作列（仅权限用户可见） -->
    <el-table-column v-if="canAudit" label="操作" width="220" fixed="right"><template #default="{row}"><el-button v-if="row.auditflg!=='1'&&row.auditflg!=='V'" link type="primary" size="small" @click.stop="doAudit(row.batch_id)">审核通过</el-button><el-button v-if="row.auditflg!=='1'&&row.auditflg!=='V'" link type="danger" size="small" @click.stop="doReject(row.batch_id)">审核退回</el-button><el-button v-if="row.auditflg!=='1'&&row.auditflg!=='V'" link type="danger" size="small" @click.stop="handleVoid(row)">作废</el-button><el-button v-if="row.auditflg==='1'" link type="warning" size="small" @click.stop="doUnaudit(row)">反审核</el-button></template></el-table-column>
  </el-table><AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/></el-card>

<el-dialog :title="drillTitle" v-model="drillVisible" width="750px"><el-table :data="drillItems" size="small" stripe v-loading="drillLoading" max-height="420"><el-table-column prop="billid" :label="drillColLabel" width="120"/><el-table-column prop="type" label="类型" width="130"/><el-table-column prop="whcd" label="仓库" width="80"/><el-table-column label="审核" width="60"><template #default="{row}"><el-tag :type="row.audited?'success':'info'" size="small">{{row.audited?'已审':'待审'}}</el-tag></template></el-table-column><el-table-column label="日期" width="140"><template #default="{row}">{{formatDate(row.gendate)}}</template></el-table-column></el-table></el-dialog></div></template>

<script setup lang="ts">import {ref,reactive,onMounted,watch,computed} from 'vue';import {ElMessage,ElMessageBox} from 'element-plus';import AppPagination from '@/components/common/AppPagination.vue';import {useUserNames} from '@/composables/useUserNames';import {listQcBatches,getQcBatch,auditQcBatch,voidQcBatch,unauditQcResult,fetchQcStats,fetchQcCompletion,type QcBatchItem} from '@/api/qc';
import {fetchStockOut,fetchStockIn,fetchQcOutOrders} from '@/api/warehouse';import {useDict} from '@/composables/useDict'
const{userName}=useUserNames();const{dictLabel:qcLabel}=useDict('QC')
const items=ref<(QcBatchItem&{_records?:any[]})[]>([]);const loading=ref(false)
const page=ref(1);const perPage=ref(20);const total=ref(0)
const s=reactive({search:'',auditflg:'',eid:'',dateRange:null as [string,string]|null})
function qcTagType(s:string):string{const m:Record<string,string>={GA:'success',BF:'danger',DJ:'warning',GC:'info'};return m[s]||'info'}
function formatDate(d:string):string{if(!d)return'-';return d.replace('T',' ').substring(0,19)}
function refInbill(sub:any):string{const dets=sub.details||[];const eids=sub.eid_details||[];return dets[0]?.ref_rgstbillid||eids[0]?.ref_rgstbillid||''}
// 权限：管理员或审批人
const canAudit=computed(()=>!!localStorage.getItem('token'))  // 前端显示按钮，后端 auditor_required 做实际校验

async function load(){loading.value=true;try{const params:Record<string,string>={page:String(page.value),per_page:String(perPage.value)};if(s.search)params.search=s.search;if(s.auditflg)params.auditflg=s.auditflg;if(s.eid)params.eid=s.eid;if(s.dateRange){params.start_date=s.dateRange[0];params.end_date=s.dateRange[1]};const r=await listQcBatches(params);items.value=(r.data?.items||[]) as any[];total.value=r.data?.total||0}catch{items.value=[];total.value=0}finally{loading.value=false}}
function doSearch(){page.value=1;load()}
watch([page,perPage],()=>{load()})
const stats=ref<{qcstatus:string;cnt:number}[]>([])
const comp=ref<{total_ov5:number;done_ov5:number;pending_ov5:number;iv11_count:number;ov_out_count:number}>({total_ov5:0,done_ov5:0,pending_ov5:0,iv11_count:0,ov_out_count:0})
onMounted(async()=>{load();try{const r=await fetchQcStats();stats.value=r.data||[]}catch{};try{const r=await fetchQcCompletion();comp.value=r.data||comp.value}catch{}})

// 展开批次 → 加载子记录（含明细）
async function onExpand(row:any,_rows:any[]){if(!row._records){try{const r=await getQcBatch(row.batch_id);const recs=(r.data as any)?.records||[];row._records=recs}catch{row._records=[]}}}
// 子记录详情已在 _records 返回时包含，无需额外加载

// 审核操作
async function doAudit(bid:string){loading.value=true;try{await auditQcBatch(bid,'1');ElMessage.success('批次审核通过');load()}catch(e:any){ElMessage.error(e?.response?.data?.message||'审核失败')}finally{loading.value=false}}
async function doReject(bid:string){try{const{value:memo}=await ElMessageBox.prompt('请输入退回原因','审核退回',{confirmButtonText:'确认退回',cancelButtonText:'取消',type:'warning'});loading.value=true;await auditQcBatch(bid,'8',memo||'');ElMessage.success('已退回');load()}catch{/*取消*/}finally{loading.value=false}}
async function handleVoid(row:QcBatchItem){try{await ElMessageBox.confirm(`确定作废批次 ${row.batch_id} 吗？`,'确认作废',{type:'warning'});loading.value=true;await voidQcBatch(row.batch_id);ElMessage.success('已作废');load()}catch{/*取消*/}finally{loading.value=false}}
async function doUnaudit(row:QcBatchItem){try{await ElMessageBox.confirm(`确定反审核批次 ${row.batch_id} 吗？下游草稿单据将同时作废。`,'反审核',{type:'warning'});loading.value=true;const r=await getQcBatch(row.batch_id);const recs=(r.data as any)?.records||[];for(const sub of recs){await unauditQcResult(sub.qcbillid)};ElMessage.success('已反审核');load()}catch{/*取消*/}finally{loading.value=false}}

// 看板钻取
const drillVisible=ref(false);const drillLoading=ref(false);const drillTitle=ref('');const drillColLabel=ref('单号');const drillItems=ref<any[]>([])
async function drillOvw(kind:string){drillVisible.value=true;drillLoading.value=true
  if(kind==='pending'){drillTitle.value='待质检 OV=5 出库单';drillColLabel.value='出库单号'
    try{const r=await fetchQcOutOrders();drillItems.value=(r.data||[]).map((o:any)=>({billid:o.outbillid,type:'OV=5质检出库',whcd:o.whcd||'',audited:true,gendate:o.gendate?.substring(0,10)||''}))}catch{}}
  else if(kind==='done'){drillTitle.value='已全部QC完成的 OV=5';drillColLabel.value='出库单号'
    try{const pendingR=await fetchQcOutOrders();const pendingIds=new Set((pendingR.data||[]).map((o:any)=>o.outbillid))
      const allR=await fetchStockOut({invtyp:'5',auditflg:'2',per_page:'100'} as any)
      drillItems.value=((allR.data?.items||[]) as any[]).filter((o:any)=>!pendingIds.has(o.outbillid)).map((o:any)=>({billid:o.outbillid,type:'OV=5质检出库',whcd:o.whcd||o.whnm||'',audited:true,gendate:o.gendate?.substring(0,10)||''}))}catch{}}
  else if(kind==='iv11'){drillTitle.value='QC生成的 IV=11 质检入库单';drillColLabel.value='入库单号'
    try{const r=await fetchStockIn({invtyp:'11',per_page:'100'} as any)
      drillItems.value=((r.data?.items||[]) as any[]).map((i:any)=>({billid:i.inbillid,type:'IV=11质检入库',whcd:i.whcd||i.whnm||'',audited:i.auditflg==='2',gendate:i.gendate?.substring(0,10)||''}))}catch{}}
  else if(kind==='ovout'){drillTitle.value='QC生成的不合格出库单 (OV=6/7/9)';drillColLabel.value='出库单号'
    try{const types=['6','7','9'];let all:any[]=[];for(const t of types){const r=await fetchStockOut({invtyp:t,per_page:'100'} as any);all.push(...((r.data?.items||[]) as any[]))}
      drillItems.value=all.filter((o:any)=>o.refbillid?.startsWith('QC')).map((o:any)=>({billid:o.outbillid,type:'OV='+o.invtyp+({6:'退换',7:'报废',9:'返修'}[o.invtyp]||''),whcd:o.whcd||o.whnm||'',audited:o.auditflg==='2',gendate:o.gendate?.substring(0,10)||''}))}catch{}}
  drillLoading.value=false}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}.search-bar{display:flex;gap:12px;align-items:center}.field{display:flex;align-items:center;gap:6px}.field label{font-size:13px;color:#606266}</style>
