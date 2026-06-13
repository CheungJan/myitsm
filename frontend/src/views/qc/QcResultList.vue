<template><div class="page"><div class="page-header"><h2>质检结果</h2></div>

  <el-card shadow="never" style="margin-bottom:16px"><div class="search-bar"><div class="field"><label>搜索</label><el-input v-model="s.search" placeholder="批次号/来源单" size="small" style="width:160px" clearable @keyup.enter="doSearch"/></div><el-input v-model="s.eid" placeholder="EID" size="small" style="width:140px;margin-left:8px" clearable @keyup.enter="doSearch"/><el-date-picker v-model="s.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" size="small" style="width:240px;margin-left:8px" value-format="YYYY-MM-DD" @change="doSearch"/><el-select v-model="s.auditflg" placeholder="审核状态" size="small" style="width:120px;margin-left:8px" clearable @change="doSearch"><el-option label="草稿" value="0"/><el-option label="已审核" value="1"/><el-option label="已退回" value="8"/><el-option label="已作废" value="V"/></el-select><el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button></div></el-card>

  <!-- 统计面板 -->
  <el-card shadow="never" style="margin-bottom:16px" v-if="stats.length"><div style="display:flex;gap:16px;flex-wrap:wrap"><div v-for="st in stats" :key="st.qcstatus" style="text-align:center;padding:8px 16px;background:#f5f7fa;border-radius:6px"><div style="font-size:20px;font-weight:600;color:#409eff">{{st.cnt}}</div><div style="font-size:12px;color:#909399">{{qcLabel(st.qcstatus)}}</div></div></div></el-card>

  <!-- OV5 看板 -->
  <el-card shadow="never" style="margin-bottom:16px"><div style="display:flex;gap:16px;flex-wrap:wrap"><el-card shadow="hover" @click="drillOvw('pending')" style="cursor:pointer;flex:1;min-width:120px"><div style="text-align:center"><div style="font-size:24px;font-weight:600;color:#1677ff">{{comp.pending_ov5}}</div><div style="font-size:12px;color:#909399;margin-top:4px">待质检 OV=5</div></div></el-card><el-card shadow="hover" @click="drillOvw('done')" style="cursor:pointer;flex:1;min-width:120px"><div style="text-align:center"><div style="font-size:24px;font-weight:600;color:#52c41a">{{comp.total_ov5-comp.pending_ov5}}</div><div style="font-size:12px;color:#909399;margin-top:4px">已完成 OV=5</div></div></el-card><el-card shadow="hover" @click="drillOvw('iv11')" style="cursor:pointer;flex:1;min-width:120px"><div style="text-align:center"><div style="font-size:24px;font-weight:600;color:#fa8c16">{{comp.iv11_count}}</div><div style="font-size:12px;color:#909399;margin-top:4px">IV=11 入库单</div></div></el-card><el-card shadow="hover" @click="drillOvw('ovout')" style="cursor:pointer;flex:1;min-width:120px"><div style="text-align:center"><div style="font-size:24px;font-weight:600;color:#ff4d4f">{{comp.ov_out_count}}</div><div style="font-size:12px;color:#909399;margin-top:4px">不合格出库单</div></div></el-card></div></el-card>

  <!-- 批次表 -->
  <el-card shadow="never"><el-table :data="items" v-loading="loading" stripe size="small" @expand-change="onExpand" row-key="batch_id">
    <el-table-column type="index" label="#" width="50" :index="(i:number)=>(page-1)*perPage+i+1"/><el-table-column type="expand"><template #default="{row}">
      <!-- 单子记录：暂存=全树形，提交=入库树+出库汇总 -->
      <div v-if="(row._records||[]).length===1" style="padding:8px 24px">
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
          <span style="font-weight:600">{{row._records[0].qcbillid}}</span>
          <span style="color:#909399;font-size:12px">来源: {{row.refbillid}}</span>
          <span v-if="row._records[0].wh_bill" style="color:#409eff;font-size:12px">{{row._records[0].wh_bill}}</span>
          <el-tag :type="qcTagType(row._records[0].qcstatus)" size="small">{{qcLabel(row._records[0].qcstatus)}}</el-tag>
        </div>
        <!-- 暂存草稿：全树形（同录入页） -->
        <template v-if="row._records[0].draft_type==='S'||(!row._records[0].draft_type&&row._records[0].auditflg==='0')">
          <div v-for="(t, idx) in buildDetailTree(row._records[0], row.refbillid, false).tree" :key="`st_${idx}`" style="margin-bottom:6px;border:1px solid #e4e7ed;border-radius:4px;overflow:hidden">
            <div style="display:flex;gap:8px;align-items:center;padding:6px 10px;background:#e6f7ff;font-weight:600">
              <span style="color:#1677ff;width:40px;flex-shrink:0">{{t.typeLabel}}</span><span style="width:90px;flex-shrink:0">{{t.itemcd}}</span>
              <span v-if="t.item_nm" style="color:#606266;font-size:12px;width:130px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{t.item_nm}}</span>
              <span v-if="t.eid" style="font-family:monospace;color:#52c41a;width:130px;flex-shrink:0">{{t.eid}}</span>
              <el-tag :type="qcTagType(t.qcstatus)" size="small">{{qcLabel(t.qcstatus)}}</el-tag>
            </div>
            <div v-if="t.children.length" style="padding:4px 10px">
              <div v-for="(ch, ci) in t.children" :key="`sch_${ci}`" style="display:flex;gap:8px;align-items:center;padding:3px 8px;margin-left:20px;border-left:2px solid #e4e7ed">
                <span style="color:#909399;width:40px;font-size:12px;flex-shrink:0">{{ch.typeLabel}}</span><span style="width:90px;flex-shrink:0">{{ch.itemcd}}</span>
                <span v-if="ch.item_nm" style="width:130px;color:#606266;font-size:12px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ch.item_nm}}</span>
                <span v-if="ch.eid" style="font-family:monospace;color:#52c41a;width:130px;flex-shrink:0">{{ch.eid}}</span>
                <el-tag :type="qcTagType(ch.qcstatus)" size="small">{{qcLabel(ch.qcstatus)}}</el-tag>
              </div>
            </div>
          </div>
        </template>
        <!-- 提交/已审：入库树形 + 出库分组 -->
        <template v-else>
          <template v-for="(t, idx) in buildDetailTree(row._records[0], row.refbillid).tree" :key="`t_${idx}`">
            <div style="margin-bottom:6px;border:1px solid #e4e7ed;border-radius:4px;overflow:hidden">
              <div style="display:flex;gap:8px;align-items:center;padding:6px 10px;background:#e6f7ff;font-weight:600">
                <span style="color:#1677ff;width:40px;flex-shrink:0">{{t.typeLabel}}</span><span style="width:90px;flex-shrink:0">{{t.itemcd}}</span>
                <span v-if="t.item_nm" style="color:#606266;font-size:12px;width:130px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{t.item_nm}}</span>
                <span v-if="t.eid" style="font-family:monospace;color:#52c41a;width:130px;flex-shrink:0">{{t.eid}}</span>
                <el-tag :type="qcTagType(t.qcstatus)" size="small">{{qcLabel(t.qcstatus)}}</el-tag>
              </div>
              <div v-if="t.children.length" style="padding:4px 10px">
                <div v-for="(ch, ci) in t.children" :key="`ch_${ci}`" style="display:flex;gap:8px;align-items:center;padding:3px 8px;margin-left:20px;border-left:2px solid #e4e7ed">
                  <span style="color:#909399;width:40px;font-size:12px;flex-shrink:0">{{ch.typeLabel}}</span><span style="width:90px;flex-shrink:0">{{ch.itemcd}}</span>
                  <span v-if="ch.item_nm" style="width:130px;color:#606266;font-size:12px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ch.item_nm}}</span>
                  <span v-if="ch.eid" style="font-family:monospace;color:#52c41a;width:130px;flex-shrink:0">{{ch.eid}}</span>
                  <el-tag :type="qcTagType(ch.qcstatus)" size="small">{{qcLabel(ch.qcstatus)}}</el-tag>
                </div>
              </div>
            </div>
          </template>
          <template v-if="buildDetailTree(row._records[0], row.refbillid).outbound.length">
            <div style="margin-top:8px;padding:8px;background:#fff7e6;border-radius:4px">
              <div style="font-size:12px;color:#fa8c16;margin-bottom:4px">【出库待处理】</div>
              <div v-for="(ob, oi) in buildDetailTree(row._records[0], row.refbillid).outbound" :key="`ob_${oi}`" style="display:flex;gap:6px;align-items:center;padding:3px 8px;background:#fff;border-radius:2px;margin-bottom:2px">
                <span style="color:#909399;width:40px;font-size:12px;flex-shrink:0">{{ob.typeLabel}}</span><span style="width:90px;flex-shrink:0">{{ob.itemcd}}</span>
                <span v-if="ob.item_nm" style="width:130px;color:#606266;font-size:12px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ob.item_nm}}</span>
                <span v-if="ob.eid" style="font-family:monospace;color:#ff4d4f;width:130px;flex-shrink:0">{{ob.eid}}</span>
                <el-tag :type="qcTagType(ob.qcstatus)" size="small">{{qcLabel(ob.qcstatus)}}</el-tag>
              </div>
            </div>
          </template>
        </template>
      </div>
      <!-- 多条子记录：每张卡片 = 一个 QC 子记录，展示 details 和 eid_details -->
      <div v-else-if="(row._records||[]).length>1" style="padding:4px 24px">
        <div v-for="sub in row._records" :key="sub.qcbillid" style="margin-bottom:10px;border:1px solid #eee;border-radius:4px;padding:8px">
          <div style="display:flex;gap:10px;align-items:center;margin-bottom:6px">
            <span style="font-weight:600">{{sub.qcbillid}}</span>
            <span style="color:#909399;font-size:12px">来源: {{row.refbillid}}</span>
            <span v-if="sub.wh_bill" style="color:#409eff;font-size:12px">{{sub.wh_bill}}</span>
            <span v-if="refInbill(sub)" style="color:#909399;font-size:12px">入库: {{refInbill(sub)}}</span>
            <el-tag :type="qcTagType(sub.qcstatus)" size="small">{{qcLabel(sub.qcstatus)}}</el-tag>
            <el-tag :type="sub.auditflg==='1'?'success':sub.auditflg==='8'?'danger':sub.auditflg==='V'?'info':'warning'" size="small">{{sub.auditflg==='1'?'已审':sub.auditflg==='8'?'已退回':sub.auditflg==='V'?'已作废':'待审'}}</el-tag>
            <span style="color:#909399;font-size:12px">{{formatDate(sub.gendate)}}</span>
          </div>
          <!-- 批次物料明细 (details) -->
          <div v-if="(sub.details||[]).length" style="margin-top:4px">
            <div v-for="(dt, idx) in sub.details" :key="`dt_${sub.qcbillid}_${idx}`" style="display:flex;gap:6px;align-items:center;padding:3px 8px;border-left:2px solid #e4e7ed;margin-bottom:2px">
              <span style="color:#909399;min-width:44px">{{getItemTypeLabel(dt)}}</span>
              <span style="min-width:80px">{{dt.itemcd}}</span>
              <span v-if="dt.item_nm" style="min-width:120px;color:#606266">{{dt.item_nm}}</span>
              <el-tag :type="qcTagType(dt.qcstatus||sub.qcstatus)" size="small">{{qcLabel(dt.qcstatus||sub.qcstatus)}}</el-tag>
              <span style="color:#909399;font-size:12px">质检数: {{dt.qcqty||'-'}}</span>
              <span style="color:#909399;font-size:12px">入库数: {{dt.inqty||'-'}}</span>
              <span v-if="dt.prddate" style="color:#909399;font-size:12px">批次: {{dt.prddate}}</span>
              <span v-if="dt.ref_rgstbillid" style="color:#909399;font-size:12px">关联: {{dt.ref_rgstbillid}}</span>
            </div>
          </div>
          <!-- 序列号明细 (eid_details) -->
          <div v-if="(sub.eid_details||[]).length" style="margin-top:4px">
            <div v-for="(ce, idx) in sub.eid_details" :key="`eid_${sub.qcbillid}_${ce.eid||'noeid'}_${ce.lineno||idx}`" style="display:flex;gap:6px;align-items:center;padding:3px 8px;border-left:2px solid #e4e7ed;margin:0 0 2px 4px">
              <span v-if="ce.is_replacement" style="color:#52c41a;min-width:44px;font-size:11px">[新件]</span>
              <span v-else-if="ce.is_replaced" style="color:#909399;min-width:44px;font-size:11px;text-decoration:line-through">[已更换]</span>
              <span v-else style="color:#909399;min-width:44px">{{getItemTypeLabel(ce)}}</span>
              <span style="min-width:80px">{{ce.itemcd}}</span>
              <span v-if="ce.item_nm" style="min-width:120px;color:#606266">{{ce.item_nm}}</span>
              <span style="font-family:monospace;min-width:138px">{{ce.eid||'-'}}</span>
              <span v-if="ce.manuf_seq" style="color:#909399;font-size:12px">原厂: {{ce.manuf_seq}}</span>
              <el-tag :type="qcTagType(ce.qcstatus||sub.qcstatus)" size="small">{{qcLabel(ce.qcstatus||sub.qcstatus)}}</el-tag>
              <span style="color:#909399;font-size:12px">质检数: {{ce.qcqty||'-'}}</span>
              <span v-if="ce.fault_desc" style="color:#ff4d4f;font-size:12px">{{ce.fault_desc}}</span>
            </div>
          </div>
        </div>
      </div>
    </template></el-table-column>
    <el-table-column prop="batch_id" label="批次号" width="110"/>
    <el-table-column prop="refbillid" label="来源单据" width="120"/>
    <el-table-column label="判定汇总" min-width="200"><template #default="{row}"><el-tag v-if="row.ga_count" type="success" size="small">GA:{{row.ga_count}}</el-tag><el-tag v-if="row.gb_count" type="success" size="small">GB:{{row.gb_count}}</el-tag><el-tag v-if="row.gc_count" type="success" size="small">GC:{{row.gc_count}}</el-tag><el-tag v-if="row.bf_count" type="danger" size="small">BF:{{row.bf_count}}</el-tag><el-tag v-if="row.bh_count" type="warning" size="small">BH:{{row.bh_count}}</el-tag><el-tag v-if="row.th_count" type="info" size="small">TH:{{row.th_count}}</el-tag></template></el-table-column>
    <el-table-column prop="total_count" label="总数" width="60"/>
    <el-table-column label="审核状态" width="110"><template #default="{row}"><el-tag v-if="row.auditflg==='1'" type="success" size="small">已审核</el-tag><el-tag v-else-if="row.auditflg==='8'" type="danger" size="small">已退回</el-tag><el-tag v-else-if="row.auditflg==='V'" type="info" size="small">已作废</el-tag><el-tag v-else-if="row.draft_type==='S'" type="info" size="small">暂存中</el-tag><el-tag v-else type="warning" size="small">草稿</el-tag><el-tag v-if="row.has_pending_replenish" type="warning" size="small" style="margin-left:4px">补料中</el-tag></template></el-table-column>
    <el-table-column label="日期" width="140"><template #default="{row}">{{formatDate(row.gendate)}}</template></el-table-column>
    <el-table-column label="操作员" width="80"><template #default="{row}">{{userName(row.opercd)}}</template></el-table-column>
    <el-table-column label="审核人" width="80"><template #default="{row}">{{userName(row.auditman)}}</template></el-table-column>
    <!-- 审核操作列（仅权限用户可见） -->
    <el-table-column v-if="canAudit" label="操作" width="220" fixed="right"><template #default="{row}"><el-button v-if="row.auditflg!=='1'&&row.auditflg!=='8'&&row.auditflg!=='V'&&row.draft_type!=='S'" link type="primary" size="small" @click.stop="doAudit(row.batch_id)">审核通过</el-button><el-button v-if="row.auditflg!=='1'&&row.auditflg!=='8'&&row.auditflg!=='V'&&row.draft_type!=='S'" link type="danger" size="small" @click.stop="doReject(row.batch_id)">审核退回</el-button><el-button v-if="row.auditflg!=='1'&&row.auditflg!=='8'&&row.auditflg!=='V'" link type="danger" size="small" @click.stop="handleVoid(row)">作废</el-button><el-button v-if="row.auditflg==='1'" link type="warning" size="small" @click.stop="doUnaudit(row)">反审核</el-button></template></el-table-column>
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

// 根据 typflg 和 consume 判断物料类型
function getItemTypeLabel(item: any): string {
    if (item.consume === '1') return '耗材'
    if (item.typflg === '1') return '成品'
    return '配件'
}
// 将扁平明细重建为成品→配件树形结构
interface DetailNode { itemcd: string; item_nm?: string; qcstatus: string; qcqty?: number; inqty?: number; eid?: string; typeLabel: string; prddate?: string; fault_desc?: string; replenish_ov_billid?: string }
interface TreeNode { itemcd: string; item_nm?: string; qcstatus: string; eid?: string; typeLabel: string; children: DetailNode[] }
function buildDetailTree(record: any, batchRefbillid: string, splitOutbound: boolean = true): { tree: TreeNode[]; outbound: DetailNode[] } {
  const details: DetailNode[] = (record.details||[]).map((d:any)=>({...d,typeLabel:getItemTypeLabel(d)}))
  const eidDetails: DetailNode[] = (record.eid_details||[]).map((d:any)=>({...d,typeLabel:getItemTypeLabel(d)}))
  const productCd = record.itemcd || ''
  const tree: TreeNode[] = []
  const outbound: DetailNode[] = []

  // 按物码分桶（dt + eid）
  const dtByCd: Record<string, DetailNode[]> = {}; const eidByCd: Record<string, DetailNode[]> = {}
  details.forEach(d => { if (!dtByCd[d.itemcd]) dtByCd[d.itemcd] = []; dtByCd[d.itemcd].push(d) })
  eidDetails.forEach(d => { if (!eidByCd[d.itemcd]) eidByCd[d.itemcd] = []; eidByCd[d.itemcd].push(d) })

  // 取产品数量 = dt 中成品行数 + eid 中成品行数
  const productDtCount = (dtByCd[productCd] || []).length
  const productEidCount = (eidByCd[productCd] || []).length
  const totalProducts = Math.max(productDtCount + productEidCount, 1)

  for (let pi = 0; pi < totalProducts; pi++) {
    // 取成品行：eid + dt 合并（eid 取值、dt 取判定，避免 eid 行判定过时）
    const pEid = (eidByCd[productCd] || [])[0]
    const pDt = (dtByCd[productCd] || [])[0]
    if (!pEid && !pDt) continue
    const pRow = { ...(pEid || pDt), eid: pEid?.eid || pDt?.eid }
    if (pEid) eidByCd[productCd]!.shift()
    else if (pDt) dtByCd[productCd]!.shift()

    const isOutbound = splitOutbound && ['BF','BH','TH'].includes(pRow.qcstatus||'')
    const node: TreeNode = { itemcd: pRow.itemcd, item_nm: pRow.item_nm, qcstatus: pRow.qcstatus||'', eid: pRow.eid, typeLabel: pRow.typeLabel, children: [] }

    // 取配件/耗材子行：eid+dt 合并（即使成品是出库型，子行也要消费避免遗留）
    const childCds = Object.keys({...dtByCd, ...eidByCd}).filter(cd => cd !== productCd)
    for (const cd of childCds) {
      const cEid = (eidByCd[cd] || [])[0]
      const cDt = (dtByCd[cd] || [])[0]
      if (!cEid && !cDt) continue
      const cRow = { ...(cEid || cDt), eid: cEid?.eid || cDt?.eid }
      if (cEid) eidByCd[cd]!.shift()
      else if (cDt) dtByCd[cd]!.shift()

      const childOutbound = splitOutbound && ['BF','BH','TH'].includes(cRow.qcstatus||'')
      if (childOutbound || isOutbound) { outbound.push(cRow); continue }
      node.children.push(cRow)
    }
    if (isOutbound) { outbound.push(pRow) }
    else { tree.push(node) }
  }
  return { tree, outbound }
}

// 获取最终有效的 EID（排除已更换的）
function getActiveEids(record: any): any[] {
  return (record.eid_details || []).filter((e: any) => !e.is_replaced)
}

// 检查是否有更换历史
function hasReplacementHistory(record: any): boolean {
  const eids = record.eid_details || []
  return eids.some((e: any) => e.is_replacement || e.is_replaced)
}

// 获取更换历史时间线（按时间排序）
function getHistoryTimeline(records: any[]): any[] {
  return records
    .map((r: any) => ({
      qcbillid: r.qcbillid,
      gendate: r.gendate,
      qcstatus: r.qcstatus,
      details: r.details || [],
      eid_details: r.eid_details || []
    }))
    .sort((a: any, b: any) => a.gendate.localeCompare(b.gendate))
}

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
      const typeMap: Record<string,string>={6:'退换',7:'报废',9:'返修'}
      drillItems.value=all.filter((o:any)=>o.refbillid?.startsWith('QC')).map((o:any)=>({billid:o.outbillid,type:'OV='+o.invtyp+(typeMap[o.invtyp]||''),whcd:o.whcd||o.whnm||'',audited:o.auditflg==='2',gendate:o.gendate?.substring(0,10)||''}))}catch{}}
  drillLoading.value=false}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}.search-bar{display:flex;gap:12px;align-items:center}.field{display:flex;align-items:center;gap:6px}.field label{font-size:13px;color:#606266}</style>
