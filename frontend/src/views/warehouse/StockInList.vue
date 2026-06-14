<template>
  <div class="page">
    <div class="page-header"><h2>入库单管理</h2><el-button type="primary" size="small" @click="openCreate">新建</el-button></div>

    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field">
          <label>单号</label>
          <el-input v-model="s.bill" placeholder="单号" size="small" style="width:140px" clearable @keyup.enter="doSearch"/>
        </div>
        <div class="field">
          <label>仓库</label>
          <el-select v-model="s.whcd" size="small" style="width:130px" clearable>
            <el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd"/>
          </el-select>
        </div>
        <div class="field">
          <label>类型</label>
          <el-select v-model="s.invtyp" size="small" style="width:130px" clearable>
            <el-option v-for="o in invtypOptions" :key="o.value" :label="o.label" :value="o.value"/>
          </el-select>
        </div>
        <div class="field">
          <label>状态</label>
          <el-select v-model="s.auditflg" size="small" style="width:100px" clearable>
            <el-option v-for="(label, code) in auditMap" :key="code" :label="label" :value="code"/>
          </el-select>
        </div>
        <div class="field">
          <label>入库日期</label>
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至"
            start-placeholder="开始" end-placeholder="结束" size="small"
            style="width:240px" value-format="YYYY-MM-DD"
            @change="onDateChange" />
        </div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDrawer">
        <el-table-column prop="inbillid" label="入库单号" width="110"/>
        <el-table-column prop="refbillid" label="关联单据" width="100"/>
        <el-table-column label="仓库" width="120">
          <template #default="{ row }">
            <span v-if="!row.whcd" style="color:#e6a23c;font-size:12px">⚠ 待填仓库</span>
            <span v-else>{{ row.whnm || row.whcd }}</span>
          </template>
        </el-table-column>
        <el-table-column label="入库类型" width="100">
          <template #default="{ row }">{{ ivLabel(row.invtyp as string) }}</template>
        </el-table-column>
        <el-table-column label="入库日期" width="130">
          <template #default="{ row }">{{ formatDate(row.indate as string || row.gendate) }}</template>
        </el-table-column>
        <el-table-column prop="memo" label="备注" min-width="100" show-overflow-tooltip/>
        <el-table-column label="操作员" width="80">
          <template #default="{ row }">{{ userName(row.opercd as string) }}</template>
        </el-table-column>
        <el-table-column label="审批" width="70">
          <template #default="{ row }">
            <el-tag :type="auditTag(row.auditflg as string)" size="small">{{ auditLabel(row.auditflg as string) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.auditflg === '0' || row.auditflg === '8'" link type="primary" size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button v-if="row.auditflg === '0'" link type="warning" size="small" @click.stop="openAudit(row)">审核</el-button>
            <el-button v-if="row.auditflg === '2'" link type="warning" size="small" @click.stop="handleUnaudit(row)">反审核</el-button>
            <el-button v-if="row.auditflg === '0' || row.auditflg === '8'" link type="danger" size="small" @click.stop="handleVoid(row)">作废</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <!-- 审核弹窗 -->
    <el-dialog title="审核入库单" v-model="auditing" width="620px" @closed="auditTarget = null; auditWhcd = ''; auditMemo = ''">
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ (auditTarget as any).inbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ (auditTarget as any).refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="入库类型">{{ ivLabel((auditTarget as any).invtyp) }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ (auditTarget as any).suppcd || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-form style="margin-top:14px" label-width="80px" size="small">
          <el-form-item v-if="((auditTarget as any).details||[]).length > 0" label="入库仓库" required>
            <el-select v-model="auditWhcd" placeholder="请选择入库仓库" style="width:220px" filterable>
              <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
            </el-select>
            <span v-if="!(auditTarget as any).whcd" style="margin-left:8px;color:#e6a23c;font-size:12px">
              系统自动生成草稿，请选择实际入库仓库
            </span>
          </el-form-item>
        </el-form>
        <template v-if="auditDetailPrd.length > 0">
          <h4 style="margin:8px 0 8px">入库明细</h4>
          <el-table :data="auditDetailPrd" size="small" stripe>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column label="批次时间" width="100">
              <template #default="{row}">{{ row.prddate ? formatDate(row.prddate).substring(0,10) : '-' }}</template>
            </el-table-column>
            <el-table-column prop="inqty" label="数量" width="70"/>
          </el-table>
        </template>
        <template v-if="auditDetailEid.length > 0">
          <h4 style="margin:8px 0 8px">入库明细(EID)</h4>
          <el-table :data="auditDetailEid" size="small" stripe>
            <el-table-column prop="eid" label="EID" min-width="140"/>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column prop="inqty" label="数量" width="70"/>
          </el-table>
        </template>
        <el-input v-model="auditMemo" type="textarea" :rows="2" placeholder="审核备注" style="margin-top:12px"/>
      </template>
      <template #footer>
        <el-button @click="auditing = false">取消</el-button>
        <el-button type="warning" @click="handleAuditReject" :loading="auditLoading">审核退回</el-button>
        <el-button type="success" @click="handleAudit('2')" :loading="auditLoading" :disabled="((auditTarget as any)?.details||[]).length > 0 && !auditWhcd">审核通过</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer" title="入库单详情" size="580px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small" :label-style="{width:'80px'}">
          <el-descriptions-item label="单号">{{ (detail as any).inbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ (detail as any).refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库">
            <span v-if="!(detail as any).whcd" style="color:#e6a23c">待填仓库</span>
            <span v-else>{{ (detail as any).whnm || (detail as any).whcd }}</span>
          </el-descriptions-item>
          <el-descriptions-item v-if="(detail as any).invtyp === '4' && sourceWhcd" label="来源仓库">
            {{ sourceWhNm || sourceWhcd }}
          </el-descriptions-item>
          <el-descriptions-item v-else label="入库类型">{{ ivLabel((detail as any).invtyp) }}</el-descriptions-item>
          <el-descriptions-item label="日期" :span="2">{{ formatDate((detail as any).indate || (detail as any).gendate) }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ userName((detail as any).opercd) }}</el-descriptions-item>
          <el-descriptions-item label="审批状态">
            <el-tag :type="auditTag((detail as any).auditflg)" size="small">{{ auditLabel((detail as any).auditflg) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ (detail as any).memo || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="(detail as any).auditmemo" label="审核备注" :span="2">{{ (detail as any).auditmemo }}</el-descriptions-item>
        </el-descriptions>
        <template v-if="detailPrd.length > 0">
          <h4 style="margin:16px 0 8px">入库明细</h4>
          <el-table :data="detailPrd" size="small" stripe>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column label="批次时间" width="100">
              <template #default="{row}">{{ row.prddate ? formatDate(row.prddate).substring(0,10) : '-' }}</template>
            </el-table-column>
            <el-table-column prop="inqty" label="数量" width="70"/>
          </el-table>
        </template>
        <template v-if="detailEid.length > 0">
          <h4 style="margin:16px 0 8px">入库明细(EID)</h4>
          <el-table :data="detailEid" size="small" stripe>
            <el-table-column prop="eid" label="EID" min-width="140"/>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column prop="inqty" label="数量" width="70"/>
          </el-table>
        </template>
        <template v-if="skipInfo.length > 0">
          <h4 style="margin:16px 0 8px;color:#e6a23c">不入库明细</h4>
          <el-table :data="skipInfo" size="small" stripe>
            <el-table-column prop="eid" label="EID" width="140"/>
            <el-table-column prop="reason" label="不入库原因" min-width="200"/>
          </el-table>
        </template>
      </template>
    </el-drawer>

    <!-- 新建/编辑 入库单 -->
    <el-dialog :title="editing ? '编辑入库单' : '新建入库单'" v-model="creating" width="750px" @closed="resetCreateForm">
      <el-form :model="createForm" label-width="90px" size="small">
        <el-form-item label="入库类型" required>
          <el-select v-model="createForm.invtyp" style="width:100%" @change="onInvtypChange" :disabled="editing">
            <el-option v-for="o in invtypOptions" :key="o.value" :label="o.label" :value="o.value"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="!editing || createDetails.length > 0" label="入库仓库" required>
          <el-select v-model="createForm.whcd" style="width:100%" filterable placeholder="选择仓库">
            <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item v-else label="仓库">
          <span style="color:#909399;line-height:32px">{{ createForm.whcd }}（不入库单据无需仓库）</span>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='4' && sourceWhcd" label="来源仓库">
          <span style="color:#303133">{{ sourceWhNm || sourceWhcd }}</span>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='1'" label="采购订单" required>
          <el-select v-if="!editing" v-model="selectedOrderId" style="width:100%" filterable placeholder="选择已审核的采购订单" @change="onOrderSelect" :loading="orderLoading">
            <el-option v-for="o in receivableOrders" :key="o.rgstbillid" :label="`${o.rgstbillid}  ${o.supp_nm||''} (${o.total_receivable}件待入)`" :value="o.rgstbillid"/>
          </el-select>
          <div v-else>
            <span style="color:#303133;line-height:32px">{{ createForm.refbillid || '-' }}</span>
            <el-tag size="small" type="info" style="margin-left:8px">不可修改</el-tag>
          </div>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='1' && selectedOrderId" label="供应商">
          <span style="color:#303133">{{ selectedOrderSuppNm }}</span>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='3'" label="ITSM工单" required>
          <el-select v-if="!editing" v-model="selectedItsmId" style="width:100%" filterable placeholder="选择有自有资产旧配件需返还的ITSM工单" @change="onItsmSelect" :loading="itsmLoading">
            <el-option v-for="o in serviceReturnable" :key="o.maintenance_id" :label="`${o.maintenance_id} ${o.changetype||''} (${o.items.length}件待返还)`" :value="o.maintenance_id"/>
          </el-select>
          <div v-else>
            <span style="color:#303133;line-height:32px">{{ createForm.refbillid || '-' }}</span>
            <el-tag size="small" type="info" style="margin-left:8px">不可修改</el-tag>
          </div>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='3' && createDetails.length > 0" label="不入库">
          <div v-for="(d, idx) in createDetails" :key="idx" style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <el-checkbox v-model="skipFlags[idx]" :disabled="editing">{{ d.eid || d.itemcd }}</el-checkbox>
            <el-input v-if="skipFlags[idx]" v-model="skipReasons[idx]" size="small" placeholder="不入库原因（必填）" style="width:200px"/>
          </div>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='4'" label="调拨出库单" required>
          <el-select v-model="selectedTransferId" style="width:100%" filterable placeholder="选择已审核的调拨出库单" @change="onTransferSelect" :loading="transferLoading" :disabled="editing">
            <el-option v-for="o in transferableOrders" :key="o.outbillid" :label="`${o.outbillid} ${o.source_whcd}→${o.target_whcd} (${o.pending}件待入)`" :value="o.outbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='4' && selectedTransferId" label="调拨信息">
          <span style="color:#303133">{{ selectedTransferInfo }}</span>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='5'" label="借出出库单" required>
          <el-select v-model="selectedLendId" style="width:100%" filterable placeholder="选择已审核的借出出库单" @change="onLendSelect" :loading="lendLoading" :disabled="editing">
            <el-option v-for="o in lendableOrders" :key="o.outbillid" :label="`${o.outbillid} (已借${o.total_out}件, 待还${o.pending}件)`" :value="o.outbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='6'" label="翻新出库单" required>
          <el-select v-model="selectedRenovationReturnId" style="width:100%" filterable placeholder="选择已审核的翻新出库单" @change="onRenovationReturnSelect" :loading="renovationReturnLoading" :disabled="editing">
            <el-option v-for="o in renovationReturnableOrders" :key="o.outbillid" :label="`${o.outbillid} (已出${o.total_out}件, 待入${o.pending}件)`" :value="o.outbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='9'" label="返修出库单" required>
          <el-select v-model="selectedRepairReturnId" style="width:100%" filterable placeholder="选择已审核的返修出库单" @change="onRepairReturnSelect" :loading="repairReturnLoading" :disabled="editing">
            <el-option v-for="o in repairReturnableOrders" :key="o.outbillid" :label="`${o.outbillid} (已出${o.total_out}件, 待入${o.pending}件)`" :value="o.outbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='8'" label="生产出库单" required>
          <el-select v-model="selectedProductionReturnId" style="width:100%" filterable placeholder="选择已审核的生产出库单" @change="onProductionReturnSelect" :loading="productionReturnLoading" :disabled="editing">
            <el-option v-for="o in productionReturnableOrders" :key="o.outbillid" :label="`${o.outbillid} (已出${o.total_out}件, 待入${o.pending}件)`" :value="o.outbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='11'" label="质检出库单" required>
          <el-select v-model="selectedQcReturnId" style="width:100%" filterable placeholder="选择已审核的质检出库单" @change="onQcReturnSelect" :loading="qcReturnLoading" :disabled="editing">
            <el-option v-for="o in qcReturnableOrders" :key="o.outbillid" :label="`${o.outbillid} (已出${o.total_out}件, 待入${o.pending}件)`" :value="o.outbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='2'" label="销售出库单" required>
          <el-select v-model="selectedSalesReturnId" style="width:100%" filterable placeholder="选择已审核的销售出库单" @change="onSalesReturnSelect" :loading="salesReturnLoading" :disabled="editing">
            <el-option v-for="o in salesReturnableOrders" :key="o.outbillid" :label="`${o.outbillid} (已出${o.total_out}件, 待退${o.pending}件)`" :value="o.outbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="showRefBillid" label="关联单据号">
          <el-input v-model="createForm.refbillid" :placeholder="refBillidPlaceholder" :disabled="editing"/>
        </el-form-item>
        <el-form-item label="入库日期">
          <el-date-picker v-model="createForm.indate" type="date" style="width:100%" value-format="YYYY-MM-DD"/>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.memo" type="textarea" :rows="2"/>
        </el-form-item>
        <el-form-item label="入库明细">
          <div style="width:100%">
            <!-- 返修入库：按批次/EID分组显示 -->
            <template v-if="createForm.invtyp === '9'">
              <template v-if="createDetailsPrd.length > 0">
                <h4 style="margin:0 0 8px;font-size:13px;color:#303133">批次物料</h4>
                <el-table :data="createDetailsPrd" size="small" stripe>
                  <el-table-column label="物料" min-width="180">
                    <template #default="{row}">
                      <el-select v-model="row.itemcd" filterable remote reserve-keyword :remote-method="(q:string)=>searchItems(q)" :loading="itemSearching" style="width:100%" size="small" placeholder="搜索物料" clearable>
                        <el-option v-for="it in itemOptions" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd"/>
                      </el-select>
                    </template>
                  </el-table-column>
                  <el-table-column label="批次时间" width="110">
                    <template #default="{row}">
                      <span style="font-size:12px;color:#606266">{{ row.prddate ? row.prddate.substring(0,10) : '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="数量" width="100">
                    <template #default="{row}">
                      <el-input-number v-model="row.inqty" :min="1" :max="row.max_qty || 99999" size="small" style="width:90px"/>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="60">
                    <template #default="{row}">
                      <el-button link type="danger" size="small" @click="removeDetail(createDetails.indexOf(row))">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </template>
              <template v-if="createDetailsEid.length > 0">
                <h4 style="margin:16px 0 8px;font-size:13px;color:#303133">EID物料</h4>
                <el-table :data="createDetailsEid" size="small" stripe>
                  <el-table-column label="EID" width="160">
                    <template #default="{row}">
                      <el-input v-model="row.eid" size="small" style="width:150px" placeholder="设备序列号"/>
                    </template>
                  </el-table-column>
                  <el-table-column label="物料" min-width="180">
                    <template #default="{row}">
                      <el-select v-model="row.itemcd" filterable remote reserve-keyword :remote-method="(q:string)=>searchItems(q)" :loading="itemSearching" style="width:100%" size="small" placeholder="搜索物料" clearable>
                        <el-option v-for="it in itemOptions" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd"/>
                      </el-select>
                    </template>
                  </el-table-column>
                  <el-table-column label="数量" width="100">
                    <template #default="{row}">
                      <el-input-number v-model="row.inqty" :min="1" :max="1" :disabled="true" size="small" style="width:90px"/>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="60">
                    <template #default="{row}">
                      <el-button link type="danger" size="small" @click="removeDetail(createDetails.indexOf(row))">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </template>
            </template>
            <!-- 其他入库类型：统一表格 -->
            <template v-else>
              <el-table :data="createDetails" size="small" stripe :row-class-name="rowClassName">
                <el-table-column label="物料" min-width="180">
                  <template #default="{$index}">
                    <el-select v-model="createDetails[$index].itemcd" filterable remote reserve-keyword :remote-method="(q:string)=>searchItems(q)" :loading="itemSearching" style="width:100%" size="small" placeholder="搜索物料" clearable>
                      <el-option v-for="it in itemOptions" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd"/>
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="EID" width="150">
                  <template #default="{$index}">
                    <el-input v-model="createDetails[$index].eid" size="small" style="width:140px" placeholder="设备序列号（可选）"/>
                  </template>
                </el-table-column>
                <el-table-column label="数量" width="100">
                  <template #default="{$index}">
                    <el-input-number v-model="createDetails[$index].inqty" :min="1" :max="createDetails[$index].eid ? 1 : (createDetails[$index].max_qty || 99999)" :disabled="!!createDetails[$index].eid" size="small" style="width:90px"/>
                  </template>
                </el-table-column>
                <el-table-column label="批次日期" width="120">
                  <template #default="{$index}">
                    <el-date-picker v-model="createDetails[$index].prddate" type="date" value-format="YYYY-MM-DD" size="small" style="width:110px" placeholder="生产日期"/>
                  </template>
                </el-table-column>
                <el-table-column label="物料类型" width="90">
                  <template #default="{$index}">
                    <el-select v-model="createDetails[$index].itemtyp" size="small" style="width:80px" clearable>
                      <el-option v-for="(nm, cd) in qcMap" :key="cd" :label="nm" :value="cd"/>
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="关联行号" width="90">
                  <template #default="{$index}">
                    <span v-if="createForm.invtyp==='1'" style="font-size:13px;color:#909399">{{ createDetails[$index].reflineno }}</span>
                    <el-input-number v-else v-model="createDetails[$index].reflineno" :min="0" size="small" style="width:80px"/>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="60">
                  <template #default="{$index}">
                    <el-button link type="danger" size="small" @click="removeDetail($index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </template>
            <el-button type="primary" link size="small" @click="addDetail" style="margin-top:8px">+ 添加明细</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="creating = false">取消</el-button>
        <el-button v-if="editing" type="primary" @click="handleUpdate" :loading="createSaving">保存修改</el-button>
        <el-button v-else type="primary" @click="handleCreate" :loading="createSaving">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useUserNames } from '@/composables/useUserNames'
import { useDict } from '@/composables/useDict'
import request from '@/api/request'
import { fetchSyscodes, fetchItems, type ItemRecord } from '@/api/master'
import { fetchStockIn, fetchStockInDetail, fetchStockOutDetail, fetchWarehouses, createStockIn, updateStockIn, auditStockIn, voidStockIn, unauditStockIn, fetchReceivableOrders, fetchReceivableOrderLines, fetchServiceReturnable, fetchTransferableOrders, fetchLendableOrders, fetchLendableOrderLines, fetchRepairReturnableOrders, fetchRepairReturnableLines, fetchProductionReturnableOrders, fetchProductionReturnableLines, fetchRenovationReturnableOrders, fetchRenovationReturnableLines, fetchQcReturnableOrders, fetchQcReturnableLines, fetchSalesReturnableOrders, fetchSalesReturnableLines, type StockInRecord, type ReceivableOrder, type ReceivableOrderLine, type ServiceReturnableOrder, type TransferableOrder, type LendableOrder, type RepairReturnableOrder, type ProductionReturnableOrder, type RenovationReturnableOrder, type QcReturnableOrder, type SalesReturnableOrder } from '@/api/warehouse'

const { userName } = useUserNames()
const { dictMap: ivMap, dictLabel: ivLabel } = useDict('IV')
const { dictMap: _ssMap } = useDict('SS')
const { dictMap: qcMap } = useDict('QC')
const { items, loading, page, perPage, total, onSearch, load } = useListPage<StockInRecord>(fetchStockIn)

const s = reactive({ bill: '', whcd: '', auditflg: '', invtyp: '', indate_from: '', indate_to: '' })
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
const drawer = ref(false)
const detail = ref<StockInRecord | null>(null)
// 入库明细按有无EID分组
const detailPrd = computed(() => ((detail.value as any)?.details || []).filter((d: any) => !d.eid))
const detailEid = computed(() => ((detail.value as any)?.details || []).filter((d: any) => d.eid))
const sourceWhcd = ref('')
const sourceWhNm = ref('')
const skipInfo = ref<{eid:string; reason:string}[]>([])
const auditMap = ref<Record<string, string>>({})

// ---- 新建入库单 ----
const invtypOptions = computed(() =>
    Object.entries(ivMap.value)
        .map(([value, label]) => ({ value, label }))
        .sort((a, b) => a.value.localeCompare(b.value))
)
const creating = ref(false)
const createSaving = ref(false)
const createForm = reactive({ invtyp: '', whcd: '', refbillid: '', suppcd: '', indate: '', memo: '' })
interface DetailRow { itemcd: string; inqty: number; eid: string; reflineno: number | undefined; itemtyp: string; prddate?: string; max_qty?: number }
const createDetails = reactive<DetailRow[]>([])
// 新建/编辑模式明细按有无EID分组
const createDetailsPrd = computed(() => createDetails.filter(d => !d.eid))
const createDetailsEid = computed(() => createDetails.filter(d => !!d.eid))
const itemOptions = ref<ItemRecord[]>([])
const itemSearching = ref(false)

// ---- 采购入库：选择订单自动填充 ----
const receivableOrders = ref<ReceivableOrder[]>([])
const orderLoading = ref(false)
const selectedOrderId = ref('')
const selectedOrderSuppNm = ref('')

async function loadReceivableOrders() {
    orderLoading.value = true
    try {
        const r = await fetchReceivableOrders()
        receivableOrders.value = r.data || []
    } catch { /* ignore */ }
    finally { orderLoading.value = false }
}

// ---- 服务返还：选择ITSM工单 ----
const serviceReturnable = ref<ServiceReturnableOrder[]>([])
const itsmLoading = ref(false)
const selectedItsmId = ref('')

// ---- 调拨入库：选择调拨出库单 ----
const transferableOrders = ref<TransferableOrder[]>([])
const transferLoading = ref(false)
const selectedTransferId = ref('')
const selectedTransferInfo = ref('')

async function loadTransferableOrders() {
    transferLoading.value = true
    try {
        const r = await fetchTransferableOrders()
        transferableOrders.value = r.data || []
    } catch { /* ignore */ }
    finally { transferLoading.value = false }
}

async function onTransferSelect(outbillid: string) {
    if (!outbillid) { selectedTransferInfo.value = ''; return }
    const order = transferableOrders.value.find(o => o.outbillid === outbillid)
    if (!order) return
    createForm.refbillid = order.outbillid
    createForm.whcd = order.target_whcd
    const srcNm = whOptions.value.find(w => w.whcd === order.source_whcd)?.whnm || order.source_whcd
    const tgtNm = whOptions.value.find(w => w.whcd === order.target_whcd)?.whnm || order.target_whcd
    selectedTransferInfo.value = `${srcNm} → ${tgtNm}`
    // 加载出库单明细
    try {
        const r = await fetchStockOutDetail(outbillid)
        const od = r.data as any
        createDetails.length = 0
        ;(od.details_prd || []).forEach((d: any) => {
            createDetails.push({ itemcd: d.itemcd, inqty: d.outqty || 1, eid: '', reflineno: d.lineno, itemtyp: d.itemtyp || '' })
        })
        ;(od.details_eid || []).forEach((d: any) => {
            createDetails.push({ itemcd: d.itemcd, inqty: d.outqty || 1, eid: d.eid || '', reflineno: d.lineno, itemtyp: d.itemtyp || '' })
        })
    } catch { /* ignore */ }
}

// ---- 借出归还入库：选择借出出库单 ----
const lendableOrders = ref<LendableOrder[]>([])
const lendLoading = ref(false)
const selectedLendId = ref('')

async function loadLendableOrders() {
    lendLoading.value = true
    try {
        const r = await fetchLendableOrders()
        lendableOrders.value = r.data || []
    } catch { /* ignore */ }
    finally { lendLoading.value = false }
}

async function onLendSelect(outbillid: string) {
    if (!outbillid) return
    const order = lendableOrders.value.find(o => o.outbillid === outbillid)
    if (order) createForm.refbillid = order.outbillid
    try {
        const r = await fetchLendableOrderLines(outbillid)
        const lines = (r.data || []) as any[]
        createDetails.length = 0
        lines.forEach((l: any) => {
            createDetails.push({
                itemcd: l.itemcd,
                inqty: l.pending || 1,
                eid: l.eid || '',
                reflineno: l.lineno,
                itemtyp: '',
            })
        })
    } catch { /* ignore */ }
}

// ---- 返修入库：选择返修出库单 ----
const repairReturnableOrders = ref<RepairReturnableOrder[]>([])
const repairReturnLoading = ref(false)
const selectedRepairReturnId = ref('')

async function loadRepairReturnableOrders() {
    repairReturnLoading.value = true
    try {
        const r = await fetchRepairReturnableOrders()
        repairReturnableOrders.value = r.data || []
    } catch { /* ignore */ }
    finally { repairReturnLoading.value = false }
}

async function onRepairReturnSelect(outbillid: string) {
    if (!outbillid) return
    const order = repairReturnableOrders.value.find(o => o.outbillid === outbillid)
    if (order) {
        createForm.refbillid = order.outbillid
        if (order.whcd) createForm.whcd = order.whcd
    }
    try {
        const r = await fetchRepairReturnableLines(outbillid)
        const lines = (r.data || []) as any[]
        createDetails.length = 0
        lines.forEach((l: any, idx: number) => {
            createDetails.push({
                itemcd: l.itemcd || '',
                inqty: l.pending || 1,
                eid: l.eid || '',
                reflineno: l.lineno || idx + 1,
                itemtyp: l.itemtyp || '',
                prddate: l.prddate || '',
            })
        })
    } catch { /* ignore */ }
}

// ---- 翻新入库：选择翻新出库单（IV=6） ----
const renovationReturnableOrders = ref<RenovationReturnableOrder[]>([])
const renovationReturnLoading = ref(false)
const selectedRenovationReturnId = ref('')

async function loadRenovationReturnableOrders() {
    renovationReturnLoading.value = true
    try {
        const r = await fetchRenovationReturnableOrders()
        renovationReturnableOrders.value = r.data || []
    } catch { /* ignore */ }
    finally { renovationReturnLoading.value = false }
}

async function onRenovationReturnSelect(outbillid: string) {
    if (!outbillid) return
    const order = renovationReturnableOrders.value.find(o => o.outbillid === outbillid)
    if (order) {
        createForm.refbillid = order.outbillid
        if (order.whcd) createForm.whcd = order.whcd
    }
    try {
        const r = await fetchRenovationReturnableLines(outbillid)
        const lines = (r.data || []) as any[]
        createDetails.length = 0
        lines.forEach((l: any, idx: number) => {
            createDetails.push({
                itemcd: l.itemcd || '',
                inqty: l.pending || 1,
                eid: l.eid || '',
                reflineno: l.lineno || idx + 1,
                itemtyp: l.itemtyp || '',
                prddate: l.prddate || '',
            })
        })
    } catch { /* ignore */ }
}

// ---- 质检入库：选择质检出库单（IV=11） ----
const qcReturnableOrders = ref<QcReturnableOrder[]>([])
const qcReturnLoading = ref(false)
const selectedQcReturnId = ref('')

async function loadQcReturnableOrders() {
    qcReturnLoading.value = true
    try {
        const r = await fetchQcReturnableOrders()
        qcReturnableOrders.value = r.data || []
    } catch { /* ignore */ }
    finally { qcReturnLoading.value = false }
}

async function onQcReturnSelect(outbillid: string) {
    if (!outbillid) return
    const order = qcReturnableOrders.value.find(o => o.outbillid === outbillid)
    if (order) {
        createForm.refbillid = order.outbillid
        if (order.whcd) createForm.whcd = order.whcd
    }
    try {
        const r = await fetchQcReturnableLines(outbillid)
        const lines = (r.data || []) as any[]
        createDetails.length = 0
        lines.forEach((l: any, idx: number) => {
            createDetails.push({
                itemcd: l.itemcd || '',
                inqty: l.pending || 1,
                eid: l.eid || '',
                reflineno: l.lineno || idx + 1,
                itemtyp: l.itemtyp || '',
                prddate: l.prddate || '',
            })
        })
    } catch { /* ignore */ }
}

// ---- 销售退货入库：选择销售出库单（IV=2） ----
const salesReturnableOrders = ref<SalesReturnableOrder[]>([])
const salesReturnLoading = ref(false)
const selectedSalesReturnId = ref('')

async function loadSalesReturnableOrders() {
    salesReturnLoading.value = true
    try {
        const r = await fetchSalesReturnableOrders()
        salesReturnableOrders.value = r.data || []
    } catch { /* ignore */ }
    finally { salesReturnLoading.value = false }
}

async function onSalesReturnSelect(outbillid: string) {
    if (!outbillid) return
    const order = salesReturnableOrders.value.find(o => o.outbillid === outbillid)
    if (order) {
        createForm.refbillid = order.outbillid
        if (order.whcd) createForm.whcd = order.whcd
    }
    try {
        const r = await fetchSalesReturnableLines(outbillid)
        const lines = (r.data || []) as any[]
        createDetails.length = 0
        lines.forEach((l: any, idx: number) => {
            createDetails.push({
                itemcd: l.itemcd || '',
                inqty: l.pending || 1,
                eid: l.eid || '',
                reflineno: l.lineno || idx + 1,
                itemtyp: l.itemtyp || '',
                prddate: l.prddate || '',
            })
        })
    } catch { /* ignore */ }
}

// ---- 生产入库：选择生产出库单 ----
const productionReturnableOrders = ref<ProductionReturnableOrder[]>([])
const productionReturnLoading = ref(false)
const selectedProductionReturnId = ref('')

async function loadProductionReturnableOrders() {
    productionReturnLoading.value = true
    try {
        const r = await fetchProductionReturnableOrders()
        productionReturnableOrders.value = r.data || []
    } catch { /* ignore */ }
    finally { productionReturnLoading.value = false }
}

async function onProductionReturnSelect(outbillid: string) {
    if (!outbillid) return
    const order = productionReturnableOrders.value.find(o => o.outbillid === outbillid)
    if (order) {
        createForm.refbillid = order.outbillid
        createForm.whcd = ''  // 成品仓留空待选
    }
    try {
        const r = await fetchProductionReturnableLines(outbillid)
        const lines = (r.data || []) as any[]
        createDetails.length = 0
        lines.forEach((l: any, idx: number) => {
            createDetails.push({
                itemcd: l.itemcd || '',
                inqty: l.pending || 1,
                eid: l.eid || '',
                reflineno: l.lineno || idx + 1,
                itemtyp: l.itemtyp || '',
                prddate: l.prddate || '',
            })
        })
    } catch { /* ignore */ }
}

async function loadServiceReturnable() {
    itsmLoading.value = true
    try {
        const r = await fetchServiceReturnable()
        serviceReturnable.value = r.data || []
    } catch { /* ignore */ }
    finally { itsmLoading.value = false }
}

const skipFlags = reactive<Record<number, boolean>>({})
const skipReasons = reactive<Record<number, string>>({})
const rowClassName = ({rowIndex}: any) => skipFlags[rowIndex] ? 'row-skipped' : ''

async function onItsmSelect(maintenanceId: string) {
    if (!maintenanceId) return
    const order = serviceReturnable.value.find(o => o.maintenance_id === maintenanceId)
    if (!order) return
    createForm.refbillid = order.maintenance_id
    createDetails.length = 0
    Object.keys(skipFlags).forEach(k => delete skipFlags[Number(k)])
    Object.keys(skipReasons).forEach(k => delete skipReasons[Number(k)])
    order.items.forEach(it => {
        createDetails.push({
            itemcd: it.itemcd,
            inqty: 1,
            eid: it.eid || '',
            reflineno: undefined,
            itemtyp: '',
        })
    })
}

async function onOrderSelect(rgstbillid: string) {
    if (!rgstbillid) { selectedOrderSuppNm.value = ''; return }
    const order = receivableOrders.value.find(o => o.rgstbillid === rgstbillid)
    if (order) {
        createForm.refbillid = order.rgstbillid
        createForm.suppcd = order.suppliercd
        selectedOrderSuppNm.value = order.supp_nm
    }
    const r = await fetchReceivableOrderLines(rgstbillid)
    const lines = (r.data || []) as ReceivableOrderLine[]
    createDetails.length = 0
    lines.forEach(l => {
        createDetails.push({
            itemcd: l.itemcd,
            inqty: l.receivable_qty,
            eid: '',
            reflineno: l.lineno,
            itemtyp: 'DJ',
            max_qty: l.receivable_qty,
        })
    })
}

const showRefBillid = computed(() => {
    if (['1','3','4','5','8','9'].includes(createForm.invtyp)) return false
    return true
})
const refBillidPlaceholder = computed(() => '关联单据号')

onMounted(async () => {
    try { const r = await fetchWarehouses(); whOptions.value = r.data || [] } catch { /* 忽略 */ }
    try {
        const r = await fetchSyscodes('AF')
        ;(r.data || []).forEach((c: { code_cd: string; code_nm: string }) => {
            auditMap.value[c.code_cd] = c.code_nm
        })
    } catch { /* 忽略 */ }
})

function formatDate(val: string | undefined): string {
    if (!val) return '-'
    const s = val.replace('T', ' ').substring(0, 19)
    // 时间部分全是 0 时只显示日期
    return s.endsWith(' 00:00:00') ? s.substring(0, 10) : s
}

function auditTag(cd: string) {
    const m: Record<string, string> = { '0': 'info', '1': 'warning', '2': 'success', '8': 'danger', '9': 'danger', 'S': 'warning' }
    return m[cd] || 'info'
}

function auditLabel(cd: string) { return auditMap.value[cd] || cd }

const dateRange = ref<[string, string] | null>(null)

function onDateChange(val: [string, string] | null) {
    s.indate_from = val?.[0] || ''
    s.indate_to = val?.[1] || ''
}

function doSearch() {
    const p: Record<string, string> = {}
    if (s.bill) p.inbillid = s.bill
    if (s.whcd) p.whcd = s.whcd
    if (s.auditflg) p.auditflg = s.auditflg
    if (s.invtyp) p.invtyp = s.invtyp
    if (s.indate_from) p.indate_from = s.indate_from
    if (s.indate_to) p.indate_to = s.indate_to
    onSearch(p)
}

async function resolveSourceWarehouse(detailData: any) {
    sourceWhcd.value = ''
    sourceWhNm.value = ''
    if (detailData.invtyp === '4' && detailData.refbillid) {
        try {
            const r = await fetchStockOutDetail(detailData.refbillid)
            const d = r.data as any
            sourceWhcd.value = d?.whcd || ''
            sourceWhNm.value = d?.whnm || ''
            // 如果whnm没返回，从whOptions查找
            if (sourceWhcd.value && !sourceWhNm.value) {
                const w = whOptions.value.find(o => o.whcd === sourceWhcd.value)
                if (w) sourceWhNm.value = w.whnm
            }
        } catch { /* ignore */ }
    }
}

async function openDrawer(row: StockInRecord) {
    drawer.value = true
    sourceWhcd.value = ''; sourceWhNm.value = ''
    skipInfo.value = []
    try { const r = await fetchStockInDetail(row.inbillid); detail.value = r.data as any; await resolveSourceWarehouse(r.data as any) } catch { detail.value = row }
    // 服务返还入库：加载不入库明细
    if ((detail.value as any)?.invtyp === '3' && (detail.value as any)?.refbillid) {
        try {
            const r = await request.get(`/warehouse/stock-in/service-skip-info/${(detail.value as any).refbillid}`)
            skipInfo.value = (r as any)?.data || []
        } catch { /* ignore */ }
    }
}

// ---- 新建入库单 ----
function openCreate() {
    editing.value = false
    editingId.value = ''
    creating.value = true
    loadReceivableOrders()
    loadServiceReturnable()
    loadTransferableOrders()
}

function onInvtypChange() {
    createForm.refbillid = ''
    createForm.suppcd = ''
    selectedOrderId.value = ''
    selectedOrderSuppNm.value = ''
    selectedItsmId.value = ''
    selectedTransferId.value = ''
    selectedTransferInfo.value = ''
    selectedLendId.value = ''
    selectedRenovationReturnId.value = ''
    selectedRepairReturnId.value = ''
    selectedProductionReturnId.value = ''
    selectedQcReturnId.value = ''
    selectedSalesReturnId.value = ''
    createDetails.length = 0
    if (createForm.invtyp === '5') loadLendableOrders()
    if (createForm.invtyp === '6') loadRenovationReturnableOrders()
    if (createForm.invtyp === '9') loadRepairReturnableOrders()
    if (createForm.invtyp === '8') loadProductionReturnableOrders()
    if (createForm.invtyp === '11') loadQcReturnableOrders()
    if (createForm.invtyp === '2') loadSalesReturnableOrders()
}

async function searchItems(query: string) {
    if (!query || query.length < 1) { itemOptions.value = []; return }
    itemSearching.value = true
    try {
        const r = await fetchItems({ search: query, per_page: 20 })
        itemOptions.value = r.data?.items || []
    } catch { /* 忽略 */ }
    finally { itemSearching.value = false }
}

function addDetail() {
    createDetails.push({ itemcd: '', inqty: 1, eid: '', reflineno: undefined, itemtyp: '' })
}

function removeDetail(index: number) {
    createDetails.splice(index, 1)
}

function resetCreateForm() {
    editing.value = false
    editingId.value = ''
    createForm.invtyp = ''
    createForm.whcd = ''
    createForm.refbillid = ''
    createForm.suppcd = ''
    createForm.indate = ''
    createForm.memo = ''
    selectedOrderId.value = ''
    selectedOrderSuppNm.value = ''
    selectedItsmId.value = ''
    selectedTransferId.value = ''
    selectedTransferInfo.value = ''
    selectedLendId.value = ''
    selectedRenovationReturnId.value = ''
    selectedRepairReturnId.value = ''
    selectedProductionReturnId.value = ''
    selectedQcReturnId.value = ''
    selectedSalesReturnId.value = ''
    createDetails.length = 0
}

async function handleCreate() {
    if (!createForm.whcd || !createForm.invtyp) { ElMessage.warning('请填写入库类型和入库仓库'); return }
    // 服务返还入库：处理不入库勾选
    if (createForm.invtyp === '3') {
        const allSkipped = createDetails.every((_, i) => skipFlags[i])
        // 勾了不入库必须填原因
        for (let i = 0; i < createDetails.length; i++) {
            if (skipFlags[i] && !skipReasons[i]) {
                ElMessage.warning(`第${i+1}行勾选了不入库但未填写原因`); return
            }
        }
        const skipItems = createDetails.filter((_, i) => skipFlags[i])
        if (skipItems.length > 0 && createForm.refbillid) {
            createSaving.value = true
            try {
                const skipEids = skipItems.map(d => d.eid).filter(Boolean)
                await request.post('/warehouse/stock-in/service-return-skip', {
                    maintenance_id: createForm.refbillid,
                    eids: skipEids,
                    reason: createForm.memo || skipReasons[Object.keys(skipReasons)[0] as any] || '不入库',
                })
            } catch (e: any) {
                ElMessage.error(e?.response?.data?.message || '操作失败')
                createSaving.value = false; return
            }
            createSaving.value = false
        }
        // 全部不入库：备注必填，创建一条无明细草稿记录便于追溯
        if (allSkipped) {
            if (!createForm.memo) { ElMessage.warning('全部不入库请填写备注说明原因'); return }
            createSaving.value = true
            try {
                const eidList = createDetails.map((d,i) => `${d.eid||d.itemcd}:${skipReasons[i]||'未填原因'}`).join('; ')
                await request.post('/warehouse/stock-in', {
                    whcd: '--',
                    invtyp: createForm.invtyp,
                    refbillid: createForm.refbillid,
                    memo: `[全部不入库] ${createForm.memo} | ${eidList}`,
                    details: [],
                })
            } catch(e: any) { /* 无明细可能创建失败，忽略 */ }
            createSaving.value = false
            creating.value = false; load(); return
        }
        // 部分/正常入库：过滤掉不入库项，明细必须填写
        const validDetails = createDetails.filter((_, i) => !skipFlags[i])
        createDetails.length = 0
        validDetails.forEach(d => createDetails.push(d))
    }
    if (createDetails.length === 0 || createDetails.some(d => !d.itemcd || !d.inqty)) { ElMessage.warning('请完善入库明细'); return }
    // 批次日期默认填入库日期
    const defaultPrd = createForm.indate || new Date().toISOString().substring(0, 10)
    createDetails.forEach(d => { if (!d.prddate) d.prddate = defaultPrd })
    createSaving.value = true
    try {
        const body: Record<string, unknown> = {
            whcd: createForm.whcd,
            invtyp: createForm.invtyp,
            details: createDetails.map(d => ({
                itemcd: d.itemcd,
                inqty: d.inqty,
                ...(d.eid ? { eid: d.eid } : {}),
                ...(d.reflineno != null ? { reflineno: d.reflineno } : {}),
                ...(d.itemtyp ? { itemtyp: d.itemtyp } : {}),
                ...(d.prddate ? { prddate: d.prddate } : {}),
            })),
        }
        if (createForm.indate) body.indate = createForm.indate
        if (createForm.refbillid) body.refbillid = createForm.refbillid
        if (createForm.suppcd) body.suppcd = createForm.suppcd
        if (createForm.memo) body.memo = createForm.memo
        // 借出归还：检查是否已有草稿，提示更新而非新建
        if (createForm.invtyp === '5' && createForm.refbillid) {
            const existing = (items.value as any[]).find(
                (r: any) => r.refbillid === createForm.refbillid && r.invtyp === '5' && r.auditflg === '0'
            )
            if (existing) {
                try {
                    await ElMessageBox.confirm(
                        `该借出单已有草稿归还单 ${existing.inbillid}，将更新此草稿而非新建。`,
                        '确认更新草稿',
                        { confirmButtonText: '更新草稿', cancelButtonText: '取消', type: 'warning' }
                    )
                } catch { createSaving.value = false; return }
            }
        }
        await createStockIn(body)
        ElMessage.success('入库单创建成功')
        creating.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '创建失败')
    } finally { createSaving.value = false }
}

// ---- 审核 ----
const auditing = ref(false)
const auditTarget = ref<StockInRecord | null>(null)
// 审核弹窗明细按有无EID分组
const auditDetailPrd = computed(() => ((auditTarget.value as any)?.details || []).filter((d: any) => !d.eid))
const auditDetailEid = computed(() => ((auditTarget.value as any)?.details || []).filter((d: any) => d.eid))
const auditLoading = ref(false)
const auditWhcd = ref('')
const auditMemo = ref('')

async function openAudit(row: StockInRecord) {
    auditTarget.value = row
    auditWhcd.value = (row as any).whcd || ''
    auditMemo.value = ''
    auditing.value = true
    try {
        const r = await fetchStockInDetail(row.inbillid)
        auditTarget.value = r.data as any
        auditWhcd.value = (r.data as any).whcd || ''
    } catch { /* use row data */ }
}

async function handleAudit(auditflg: string) {
    if (!auditTarget.value) return
    if (auditflg !== '8' && !auditWhcd.value) return
    auditLoading.value = true
    try {
        await auditStockIn((auditTarget.value as any).inbillid, auditWhcd.value, auditMemo.value || undefined, auditflg)
        ElMessage.success(auditflg === '2' ? '审核通过' : '已退回')
        auditing.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '审核失败')
    } finally { auditLoading.value = false }
}

async function handleUnaudit(row: StockInRecord) {
    try {
        await ElMessageBox.confirm(
            `反审核将回退库存并作废下游出库草稿，确定反审核 ${row.inbillid} 吗？`,
            '确认反审核', { type: 'warning' }
        )
        await unauditStockIn(row.inbillid)
        ElMessage.success('已反审核，可重新审核')
        load()
    } catch { /* 取消 */ }
}

async function handleVoid(row: StockInRecord) {
    try {
        await ElMessageBox.confirm(`确定作废入库单 ${row.inbillid} 吗？`, '确认作废', { type: 'warning' })
        await voidStockIn(row.inbillid)
        ElMessage.success('已作废')
        load()
    } catch { /* 取消 */ }
}

async function handleAuditReject() {
    if (!auditMemo.value) { ElMessage.warning('退回请填写审核备注说明原因'); return }
    await handleAudit('8')
}

// ---- 编辑 ----
const editing = ref(false)
const editingId = ref('')

async function openEdit(row: StockInRecord) {
    editingId.value = row.inbillid
    editing.value = true
    creating.value = true
    if (row.invtyp) {
        createForm.invtyp = row.invtyp
        if (row.invtyp === '1') {
            selectedOrderId.value = (row as any).refbillid || ''
            selectedOrderSuppNm.value = ''
            loadReceivableOrders()
        }
        if (row.invtyp === '5') {
            selectedLendId.value = (row as any).refbillid || ''
            loadLendableOrders()
        }
    }
    try {
        const r = await fetchStockInDetail(row.inbillid)
        const detail = r.data as any
        createForm.whcd = detail.whcd || ''
        createForm.refbillid = detail.refbillid || ''
        // 服务返还编辑：加载不入库信息（仅展示，不可修改）
        if (detail.invtyp === '3' && detail.refbillid) {
            try {
                const r = await request.get(`/warehouse/stock-in/service-skip-info/${detail.refbillid}`)
                const skips = (r as any)?.data || []
                // 不入库的 EID 集合
                const skipEids = new Set(skips.map((s: any) => s.eid))
                createDetails.forEach((d, i) => {
                    if (skipEids.has(d.eid)) skipFlags[i] = true
                })
            } catch { /* ignore */ }
        }
        createForm.suppcd = detail.suppcd || ''
        createForm.indate = detail.indate || ''
        createForm.memo = (detail.memo || '').replace(' [手动更新]', '')
        await resolveSourceWarehouse(detail)
        createDetails.length = 0
        ;(detail.details || []).forEach((d: any) => {
            createDetails.push({
                itemcd: d.itemcd,
                inqty: d.inqty || 1,
                eid: d.eid || '',
                reflineno: d.reflineno,
                itemtyp: d.itemtyp || '',
                prddate: d.prddate || '',
            })
        })
    } catch { /* use row data */ }
}

async function handleUpdate() {
    const isAllSkipped = (createForm.memo || '').includes('[全部不入库]')
    if (!isAllSkipped && !createForm.whcd) { ElMessage.warning('请选择仓库'); return }
    if (!isAllSkipped && (createDetails.length === 0 || createDetails.some(d => !d.itemcd || !d.inqty))) { ElMessage.warning('请完善入库明细'); return }
    const defaultPrd = createForm.indate || new Date().toISOString().substring(0, 10)
    createDetails.forEach(d => { if (!d.prddate) d.prddate = defaultPrd })
    createSaving.value = true
    try {
        const body: Record<string, unknown> = {
            whcd: createForm.whcd,
            details: createDetails.map(d => ({
                itemcd: d.itemcd,
                inqty: d.inqty,
                ...(d.eid ? { eid: d.eid } : {}),
                ...(d.reflineno != null ? { reflineno: d.reflineno } : {}),
                ...(d.itemtyp ? { itemtyp: d.itemtyp } : {}),
                ...(d.prddate ? { prddate: d.prddate } : {}),
            })),
        }
        if (createForm.indate) body.indate = createForm.indate
        if (createForm.memo) body.memo = createForm.memo
        await updateStockIn(editingId.value, body)
        ElMessage.success('更新成功')
        creating.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '更新失败')
    } finally { createSaving.value = false }
}
</script>

<style scoped>
:deep(.row-skipped) { opacity: 0.4; text-decoration: line-through; }
.page { padding: 0 }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0 }
.search-bar { display: flex; gap: 12px; align-items: center }
.field { display: flex; align-items: center; gap: 6px }
.field label { font-size: 13px; color: #606266 }
</style>