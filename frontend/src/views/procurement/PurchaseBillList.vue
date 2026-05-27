<template>
  <div class="page">
    <div class="page-header">
      <h2>采购结算单</h2>
      <div style="display:flex;gap:8px">
        <el-button type="warning" size="small" plain @click="quickFilter('0')">未审核</el-button>
        <el-button type="primary" size="small" @click="openCreate">新建结算单</el-button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field">
          <label>供应商</label>
          <el-select
            v-model="searchSuppliercd"
            size="small"
            style="width:180px"
            clearable
            filterable
            placeholder="选择供应商"
            @change="doSearch"
          >
            <el-option
              v-for="s in supplierOptions"
              :key="s.supp_cd"
              :label="s.supp_nm"
              :value="s.supp_cd"
            />
          </el-select>
        </div>
        <div class="field">
          <label>审批状态</label>
          <el-select
            v-model="searchAuditflg"
            size="small"
            style="width:120px"
            clearable
            @change="doSearch"
          >
            <el-option
              v-for="(nm, cd) in auditMap"
              :key="cd"
              :label="nm"
              :value="cd"
            />
          </el-select>
        </div>
        <div class="field">
          <label>付款方式</label>
          <el-select
            v-model="searchPayType"
            size="small"
            style="width:130px"
            clearable
            @change="doSearch"
          >
            <el-option
              v-for="(nm, cd) in payTypeMap"
              :key="cd"
              :label="nm"
              :value="cd"
            />
          </el-select>
        </div>
        <el-button size="small" @click="searchShowVoided = !searchShowVoided; doSearch()" :type="searchShowVoided ? 'danger' : ''">{{ searchShowVoided ? '返回正常单据' : '作废单据' }}</el-button>
        <el-button size="small" type="primary" @click="doSearch" style="margin-left:auto">
          查询
        </el-button>
        <el-button size="small" @click="doReset">重置</el-button>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table
        :data="items"
        v-loading="loading"
        stripe
        size="small"
        highlight-current-row
        @row-click="handleRowClick"
      >
        <el-table-column prop="pcbillid" label="结算单号" width="120" />
        <el-table-column label="供应商" width="140">
          <template #default="{ row }">
            {{ getSupplierName(row.suppliercd) }}
          </template>
        </el-table-column>
        <el-table-column label="付款方式" width="100">
          <template #default="{ row }">
            {{ payTypeMap[row.pay_type as string] || row.pay_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="结算金额" width="110" align="right">
          <template #default="{ row }">
            {{ row.total_settle_amt != null ? Number(row.total_settle_amt).toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="审批" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.auditflg === '2' ? 'success' : row.auditflg === 'V' ? 'danger' : 'warning'"
              size="small"
            >
              {{ auditMap[row.auditflg as string] || '未审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="日期" width="110">
          <template #default="{ row }">
            {{ formatDate(row.pcdate || row.gendate) }}
          </template>
        </el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作员" width="80">
          <template #default="{ row }">
            {{ userName(row.opercd) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="row.auditflg !== 'V'">
              <el-button
                v-if="row.auditflg === '0' || row.auditflg === '9'"
                link
                type="success"
                size="small"
                @click.stop="openEdit(row)"
              >
                编辑
              </el-button>
              <el-button
                v-if="row.auditflg === '0' || row.auditflg === '9'"
                link
                type="primary"
                size="small"
                @click.stop="doSubmit(row)"
              >
                送审
              </el-button>
              <el-button
                v-if="row.auditflg === '1'"
                link
                type="warning"
                size="small"
                @click.stop="openAudit(row)"
              >
                审核
              </el-button>
              <el-button
                link
                type="danger"
                size="small"
                @click.stop="openVoid(row)"
              >
                作废
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        style="margin-top:12px;justify-content:flex-end"
      />
    </el-card>

    <!-- 详情抽屉 -->
    <el-dialog
      :title="'结算单 — ' + (detail?.pcbillid || '')"
      v-model="drawer"
      width="820px"
    >
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="结算单号">{{ detail.pcbillid }}</el-descriptions-item>
          <el-descriptions-item label="供应商">
            {{ getSupplierName(detail.suppliercd) }}
          </el-descriptions-item>
          <el-descriptions-item label="付款方式">
            {{ payTypeMap[detail.pay_type as string] || detail.pay_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.settlement_period" label="结算月份">{{ detail.settlement_period }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.settle_stage" label="结算阶段">
            <el-tag :type="detail.settle_stage === 'deposit' ? 'warning' : 'success'" size="small">{{ detail.settle_stage === 'deposit' ? '预付款' : '尾款' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.pay_type === 'INS'" label="分期信息">
            第 {{ detail.installment_no }} 期 / 共 {{ detail.total_installments }} 期
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.pay_type === 'DEP' && getSettleRatio(detail) !== null" label="结算比例">
            {{ getSettleRatio(detail) }}%
          </el-descriptions-item>
          <el-descriptions-item label="结算金额">
            {{ detail.total_settle_amt != null ? Number(detail.total_settle_amt).toFixed(2) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="发票号">
            {{ detail.invoice_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="发票日期">
            {{ formatDate(detail.invoice_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="审批人">{{ detail.auditman || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审批日期">
            {{ formatDate(detail.auditdate) }}
          </el-descriptions-item>
          <el-descriptions-item label="仓库">{{ getWarehouseNames(detail.whcd as string) }}</el-descriptions-item>
          <el-descriptions-item label="发票">
            <el-tag
              :type="detail.invoiceflg === '1' ? 'success' : 'info'"
              size="small"
            >
              {{ detail.invoiceflg === '1' ? '已开' : '未开' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">
            {{ detail.memo || '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="(detail as any).settlement_period"
            label="结算月份"
          >
            {{ (detail as any).settlement_period || '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="['DEP', 'INS'].includes(detail.pay_type as string) && (detail as any).settle_stage"
            label="结算阶段"
          >
            {{ (detail as any).settle_stage === 'deposit' ? '预付款' : (detail as any).settle_stage === 'final' ? '尾款' : (detail as any).settle_stage || '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="(detail as any).installment_no"
            label="分期信息"
          >
            第{{ (detail as any).installment_no }}期 / 共{{ (detail as any).total_installments || '-' }}期
          </el-descriptions-item>
          <el-descriptions-item
            v-if="['MON', 'INS', 'DEP'].includes(detail.pay_type as string)"
            label="付款到期日"
          >
            {{ (detail as any).due_date ? formatDate((detail as any).due_date) : '-' }}
          </el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">结算明细</h4>
        <el-table
          :data="(detail.details as SettlementDetail[]) || []"
          size="small"
          stripe
        >
          <el-table-column prop="ref_rgstbillid" label="来源订单" width="120" />
          <el-table-column prop="itemcd" label="物料编码" width="100" />
          <el-table-column prop="order_qty" label="订单数量" width="80" align="right" />
          <el-table-column prop="received_qty" label="已收货" width="80" align="right" />
          <el-table-column prop="already_settled" label="已结算" width="80" align="right" />
          <el-table-column prop="settle_qty" label="本次结算数量" width="100" align="right" />
          <el-table-column prop="settle_price" label="结算单价" width="90" align="right" />
          <el-table-column prop="settle_amt" label="结算金额" width="100" align="right" />
          <el-table-column label="结算比例" width="80" align="right">
            <template #default="{ row }">{{ Number(row.order_qty) > 0 ? Math.round(Number(row.settle_qty)/Number(row.order_qty)*100) + '%' : '-' }}</template>
          </el-table-column>
        </el-table>
        <div style="margin-top:8px;padding:8px;background:#f5f5f5;border-radius:4px;display:flex;gap:16px;font-size:13px">
          <span>订单金额: <strong>¥{{ calcDetailOrderAmt() }}</strong></span>
          <span>已结算: <strong>¥{{ calcDetailSettled() }}</strong></span>
          <span>本次结算: <strong>¥{{ calcDetailCurrent() }}</strong></span>
          <span>剩余: <strong>¥{{ calcDetailRemaining() }}</strong></span>
        </div>
        <h4 style="margin:16px 0 8px">应付信息</h4>
        <el-descriptions v-if="payableInfo" :column="3" border size="small">
          <el-descriptions-item label="应付金额">{{ Number(payableInfo.amount).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="已付金额">{{ Number(payableInfo.paid_amount).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="余额">{{ Number(payableInfo.balance).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="到期日">{{ payableInfo.due_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag
              :type="payableInfo.status === 'PAID' ? 'success' : payableInfo.status === 'PARTIAL' ? 'warning' : payableInfo.status === 'OVERDUE' ? 'danger' : 'info'"
              size="small"
            >
              {{ payableInfo.status === 'PAID' ? '已付清' : payableInfo.status === 'PARTIAL' ? '部分付款' : payableInfo.status === 'OVERDUE' ? '已逾期' : payableInfo.status === 'CANCELLED' ? '已取消' : '未付' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-alert v-else title="暂无应付记录（审核通过后自动生成）" type="info" :closable="false" show-icon />
      </template>
    </el-dialog>

    <!-- 审核弹窗 -->
    <el-dialog
      title="审核结算单"
      v-model="auditing"
      width="600px"
      @closed="auditTarget = null; auditMemo = ''"
    >
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="结算单号">
            {{ auditTarget.pcbillid }}
          </el-descriptions-item>
          <el-descriptions-item label="供应商">
            {{ getSupplierName(auditTarget.suppliercd) }}
          </el-descriptions-item>
          <el-descriptions-item label="结算金额">
            {{ auditTarget.total_settle_amt != null ? Number(auditTarget.total_settle_amt).toFixed(2) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="付款方式">
            {{ payTypeMap[auditTarget.pay_type as string] || auditTarget.pay_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="入库仓库">
            {{ getWarehouseNames(auditTarget.whcd as string) }}
          </el-descriptions-item>
          <el-descriptions-item label="发票号">
            {{ auditTarget.invoice_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="发票日期">
            {{ formatDate(auditTarget.invoice_date) }}
          </el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:12px 0 8px">结算明细</h4>
        <el-table
          :data="(auditTarget.details as SettlementDetail[]) || []"
          size="small"
          stripe
        >
          <el-table-column prop="ref_rgstbillid" label="来源订单" width="110" />
          <el-table-column prop="itemcd" label="物料编码" width="100" />
          <el-table-column prop="settle_qty" label="结算数量" width="90" align="right" />
          <el-table-column prop="settle_price" label="结算单价" width="90" align="right" />
          <el-table-column prop="settle_amt" label="结算金额" width="100" align="right" />
        </el-table>
        <el-input
          v-model="auditMemo"
          type="textarea"
          :rows="2"
          placeholder="审核备注"
          style="margin-top:12px"
        />
      </template>
      <template #footer>
        <el-button @click="auditing = false">取消</el-button>
        <el-button type="danger" @click="doAudit('9')" :loading="auditLoading">
          驳回（退回修改）
        </el-button>
        <el-button type="success" @click="doAudit('2')" :loading="auditLoading">
          审核通过
        </el-button>
      </template>
    </el-dialog>

    <!-- 作废弹窗 -->
    <el-dialog title="作废结算单" v-model="voiding" width="400px">
      <template v-if="voidTarget">
        <p>
          确认作废结算单 <strong>{{ voidTarget.pcbillid }}</strong> 吗？
        </p>
        <p style="color:#f56c6c;font-size:12px;margin-top:8px">
          作废后不可恢复
        </p>
      </template>
      <template #footer>
        <el-button @click="voiding = false">取消</el-button>
        <el-button type="danger" @click="doVoid" :loading="voidLoading">
          确认作废
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑结算单弹窗 -->
    <el-dialog title="编辑结算单" v-model="editing" width="700px" @closed="resetEditForm">
      <el-form :model="editForm" label-width="90px" size="small" v-if="editDetail">
        <el-form-item label="供应商">{{ editDetail.suppliercd }}</el-form-item>
        <el-form-item label="付款方式">
          <el-select v-model="editForm.pay_type" style="width:200px">
            <el-option v-for="(nm,k) in payTypeMap" :key="k" :label="nm" :value="k"/>
          </el-select>
        </el-form-item>

        <!-- 月结周期 (only when pay_type=MON) -->
        <el-form-item v-if="editForm.pay_type === 'MON'" label="结算月份">
          <el-date-picker
            v-model="editForm.settlement_period"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择月份"
            style="width:200px"
          />
        </el-form-item>

        <!-- 预付/尾款 (only when pay_type=DEP) -->
        <el-form-item v-if="editForm.pay_type === 'DEP'" label="结算阶段">
          <el-select v-model="editForm.settle_stage" style="width:200px">
            <el-option label="预付款" value="deposit" />
            <el-option label="尾款" value="final" />
          </el-select>
        </el-form-item>

        <!-- 分期信息 (only when pay_type=INS) -->
        <el-form-item v-if="editForm.pay_type === 'INS'" label="分期信息">
          <span style="display:flex;gap:8px;align-items:center">
            第
            <el-input-number
              v-model="editForm.installment_no"
              :min="1"
              size="small"
              style="width:80px"
            />
            期 / 共
            <el-input-number
              v-model="editForm.total_installments"
              :min="1"
              size="small"
              style="width:80px"
            />
            期
          </span>
        </el-form-item>

        <!-- 付款到期日 (for MON/INS/DEP) -->
        <el-form-item
          v-if="['MON', 'INS', 'DEP'].includes(editForm.pay_type)"
          label="付款到期日"
        >
          <el-date-picker
            v-model="editForm.due_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择到期日"
            style="width:200px"
          />
        </el-form-item>

        <el-form-item label="发票号"><el-input v-model="editForm.invoice_no"/></el-form-item>
        <el-form-item label="发票日期"><el-date-picker v-model="editForm.invoice_date" type="date" value-format="YYYY-MM-DD" style="width:200px"/></el-form-item>
        <el-form-item label="结算日期"><el-date-picker v-model="editForm.pcdate" type="date" value-format="YYYY-MM-DD" style="width:200px"/></el-form-item>
        <el-form-item label="仓库">
          <el-select v-model="editForm.whcd" multiple clearable filterable placeholder="选择仓库" style="width:280px">
            <el-option v-for="w in warehouseOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="editForm.memo" type="textarea" :rows="2"/></el-form-item>

        <el-divider content-position="left">结算明细</el-divider>
        <el-table :data="editDetails" size="small" stripe>
          <el-table-column prop="ref_rgstbillid" label="来源订单" width="90"/>
          <el-table-column prop="itemcd" label="物料" width="80"/>
          <el-table-column label="结算数量" width="130">
            <template #default="{ $index }">
              <el-input-number v-model="editDetails[$index].settle_qty" :min="1" size="small" style="width:110px" controls-position="right"/>
            </template>
          </el-table-column>
          <el-table-column label="结算单价" width="130">
            <template #default="{ $index }">
              <el-input-number v-model="editDetails[$index].settle_price" :min="0" :precision="2" size="small" style="width:110px" controls-position="right"/>
            </template>
          </el-table-column>
          <el-table-column label="金额" width="100">
            <template #default="{ $index }">{{ ((editDetails[$index].settle_qty||0) * (editDetails[$index].settle_price||0)).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="结算比例" width="80" align="right">
            <template #default="{ $index }">
              {{ calcEditLineRatio($index) }}
            </template>
          </el-table-column>
        </el-table>
        <div v-if="calcEditRatio() !== null" style="font-size:13px;color:#909399;margin-top:4px">全局结算比例: {{ calcEditRatio() }}%</div>
        <div style="margin-top:8px;padding:8px;background:#f5f5f5;border-radius:4px;display:flex;gap:16px;font-size:13px">
          <span>订单金额: <strong>¥{{ calcEditOrderAmt() }}</strong></span>
          <span>已结算: <strong>¥{{ calcEditSettled() }}</strong></span>
          <span>本次结算: <strong>¥{{ calcEditCurrent() }}</strong></span>
          <span>剩余: <strong>¥{{ calcEditRemaining() }}</strong></span>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="editing=false">取消</el-button>
        <el-button type="primary" @click="doEdit" :loading="editLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建结算单 -->
    <el-dialog
      title="新建采购结算单"
      v-model="creating"
      width="900px"
      @closed="resetCreateForm"
    >
      <el-form :model="createForm" label-width="100px" size="small">
        <el-form-item label="供应商">
          <el-select
            v-model="createForm.suppliercd"
            style="width:100%"
            filterable
            placeholder="选择供应商"
          >
            <el-option
              v-for="s in supplierOptions"
              :key="s.supp_cd"
              :label="s.supp_nm"
              :value="s.supp_cd"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="付款方式">
          <el-select v-model="createForm.pay_type" style="width:100%">
            <el-option
              v-for="(nm, cd) in payTypeMap"
              :key="cd"
              :label="nm"
              :value="cd"
            />
          </el-select>
        </el-form-item>

        <!-- 月结周期 (only when pay_type=MON) -->
        <el-form-item v-if="createForm.pay_type === 'MON'" label="结算月份">
          <el-date-picker
            v-model="createForm.settlement_period"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择月份"
            style="width:100%"
          />
        </el-form-item>

        <!-- 预付/尾款 (only when pay_type=DEP) -->
        <el-form-item v-if="createForm.pay_type === 'DEP'" label="结算阶段">
          <el-select v-model="createForm.settle_stage" style="width:100%">
            <el-option label="预付款" value="deposit" />
            <el-option label="尾款" value="final" />
          </el-select>
        </el-form-item>

        <!-- 分期信息 (only when pay_type=INS) -->
        <el-form-item v-if="createForm.pay_type === 'INS'" label="分期信息">
          <span style="display:flex;gap:8px;align-items:center">
            第
            <el-input-number
              v-model="createForm.installment_no"
              :min="1"
              size="small"
              style="width:80px"
            />
            期 / 共
            <el-input-number
              v-model="createForm.total_installments"
              :min="1"
              size="small"
              style="width:80px"
            />
            期
          </span>
        </el-form-item>

        <!-- 付款到期日 (for MON/INS/DEP) -->
        <el-form-item
          v-if="['MON', 'INS', 'DEP'].includes(createForm.pay_type)"
          label="付款到期日"
        >
          <el-date-picker
            v-model="createForm.due_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择到期日"
            style="width:100%"
          />
        </el-form-item>

        <el-form-item label="结算日期">
          <el-date-picker
            v-model="createForm.pcdate"
            type="date"
            style="width:100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="发票号">
          <el-input v-model="createForm.invoice_no" placeholder="选填" style="width:100%" />
        </el-form-item>

        <el-form-item label="发票日期">
          <el-date-picker
            v-model="createForm.invoice_date"
            type="date"
            style="width:100%"
            value-format="YYYY-MM-DD"
            placeholder="选填"
          />
        </el-form-item>

        <el-form-item label="入库仓库">
          <el-select v-model="createForm.whcd" multiple clearable filterable placeholder="自动关联，可多选" style="width:280px">
            <el-option v-for="w in warehouseOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="createForm.memo"
            type="textarea"
            :rows="2"
          />
        </el-form-item>

        <el-form-item label="结算明细">
          <div style="width:100%">
            <!-- 预付/分期：全局比例设置 -->
            <div v-if="['DEP','INS'].includes(createForm.pay_type) && settleableItems.length > 0" style="margin-bottom:8px;display:flex;gap:8px;align-items:center">
              <span style="font-size:13px;white-space:nowrap">结算比例</span>
              <el-input-number v-model="globalRatio" :min="0" :max="100" size="small" style="width:100px"/> <span style="font-size:13px">%</span>
              <el-button size="small" @click="applyGlobalRatio">应用</el-button>
              <span style="font-size:12px;color:#909399">勾选行按比例自动计算结算数量</span>
            </div>
            <el-alert
              v-if="!createForm.suppliercd"
              title="请先选择供应商"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom:8px"
            />
            <el-alert
              v-if="createForm.suppliercd && settleableLoading"
              title="正在加载可结算明细..."
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom:8px"
            />
            <el-alert
              v-if="
                createForm.suppliercd &&
                  !settleableLoading &&
                  settleableItems.length === 0
              "
              title="该供应商没有可结算的订单明细"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom:8px"
            />
            <el-table
              v-if="settleableItems.length > 0"
              :data="settleableItems"
              size="small"
              @selection-change="onSettleableSelectionChange"
            >
              <el-table-column type="selection" width="50" />
              <el-table-column prop="ref_rgstbillid" label="来源订单" width="120" />
              <el-table-column prop="itemcd" label="物料编码" width="100" />
              <el-table-column prop="item_nm" label="物料名称" min-width="120" show-overflow-tooltip />
              <el-table-column prop="order_qty" label="订单数量" width="80" align="right" />
              <el-table-column prop="received_qty" label="已收货" width="80" align="right" />
              <el-table-column prop="already_settled" label="已结算" width="80" align="right" />
              <el-table-column prop="remain_qty" label="可结算" width="90" align="right" />
              <el-table-column label="本次结算数量" width="110">
                <template #default="{ row, $index }">
                  <el-input-number
                    :model-value="createDetails[$index]?.settle_qty"
                    @update:model-value="
                      (v: number | undefined) =>
                        onSettleQtyChange($index, v || 0)
                    "
                    :min="0"
                    :max="Number(row.remain_qty) || Number(row.order_qty)"
                    size="small"
                    style="width:100px"
                    controls-position="right"
                  />
                </template>
              </el-table-column>
              <el-table-column label="结算单价" width="120">
                <template #default="{ $index }">
                  <el-input-number
                    :model-value="createDetails[$index]?.settle_price"
                    @update:model-value="
                      (v: number | undefined) =>
                        onSettlePriceChange($index, v || 0)
                    "
                    :min="0"
                    :precision="2"
                    size="small"
                    style="width:110px"
                    controls-position="right"
                  />
                </template>
              </el-table-column>
              <el-table-column label="结算金额" width="100" align="right">
                <template #default="{ $index }">
                  {{
                    calcSettleAmt($index)
                  }}
                </template>
              </el-table-column>
            </el-table>
            <div v-if="selectedSettleableRows.length > 0" style="margin-top:8px;padding:8px;background:#f5f5f5;border-radius:4px;display:flex;gap:16px;font-size:13px">
              <span>订单金额: <strong>¥{{ calcCreateOrderAmt() }}</strong></span>
              <span>已结算: <strong>¥{{ calcCreateSettled() }}</strong></span>
              <span>本次结算: <strong>¥{{ calcCreateCurrent() }}</strong></span>
              <span>剩余: <strong>¥{{ calcCreateRemaining() }}</strong></span>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="creating = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="saving">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useDetailDrawer } from '@/composables/useDetailDrawer'
import { useUserNames } from '@/composables/useUserNames'
import {
    fetchSettlements,
    fetchSettlementDetail,
    createSettlement,
    updateSettlement,
    auditSettlement,
    voidSettlement,
    fetchSettleableItems,
    fetchOrders,
    fetchSettlementPayable,
    fetchMonthlyReceiving,
} from '@/api/procurement'
import type { SettlementRecord, SettlementDetail, PayableRecord } from '@/api/procurement'
import { useDict } from '@/composables/useDict'
import { fetchSuppliersSimple, fetchWarehouses } from '@/api/master'

// ---- 字典映射 ----
const { dictMap: payTypeMap } = useDict('PYMT')
const { dictMap: auditMap } = useDict('AF')

// ---- composables ----
const { userName } = useUserNames()
const { items, loading, page, perPage, total, load, onSearch } =
    useListPage<SettlementRecord>(fetchSettlements)
const { drawer, detail } = useDetailDrawer<SettlementRecord>()
const payableInfo = ref<PayableRecord | null>(null)

// ---- 供应商/仓库选项 ----
const supplierOptions = ref<{ supp_cd: string; supp_nm: string }[]>([])
const supplierNameMap = ref<Record<string, string>>({})
const warehouseOptions = ref<{ whcd: string; whnm: string }[]>([])
const warehouseNameMap = ref<Record<string, string>>({})

function getWarehouseNames(whcd: string | undefined | null): string {
    if (!whcd) return '-'
    return whcd.split(',').map(c => warehouseNameMap.value[c] ? `${c} ${warehouseNameMap.value[c]}` : c).join(', ')
}

function getSettleRatio(d: SettlementRecord | null): number | null {
    if (!d?.details?.length) return null
    const lines = d.details as SettlementDetail[]
    const ratios = lines.filter(l => Number(l.order_qty) > 0).map(l => Math.round(Number(l.settle_qty) / Number(l.order_qty) * 100))
    if (ratios.length === 0) return null
    return ratios.every(r => r === ratios[0]) ? ratios[0] : null
}

function calcEditLineRatio(index: number): string {
    const d = editDetails[index]
    if (!d || !editDetail.value?.details) return '-'
    const orig = (editDetail.value.details as SettlementDetail[])[index]
    const oq = Number(orig?.order_qty || 0)
    if (oq <= 0) return '-'
    return Math.round((d.settle_qty || 0) / oq * 100) + '%'
}

function calcEditRatio(): number | null {
    if (editDetails.length === 0) return null
    const orderQtys = (editDetail.value?.details as SettlementDetail[] || [])
    const ratios = editDetails.map((d, i) => {
        const oq = Number(orderQtys[i]?.order_qty || 0)
        return oq > 0 ? Math.round((d.settle_qty || 0) / oq * 100) : 0
    }).filter(r => r > 0)
    if (ratios.length === 0) return null
    return ratios.every(r => r === ratios[0]) ? ratios[0] : null
}

onMounted(async () => {
    try {
        const r = await fetchSuppliersSimple()
        const list = (r.data as { supp_cd: string; supp_nm: string }[]) || []
        supplierOptions.value = list
        for (const s of list) {
            supplierNameMap.value[s.supp_cd] = s.supp_nm
        }
    } catch {
        /* ignore */
    }
    try {
        const r = await fetchWarehouses()
        const list = (r.data as { whcd: string; whnm: string }[]) || []
        warehouseOptions.value = list
        for (const w of list) {
            warehouseNameMap.value[w.whcd] = w.whnm
        }
    } catch {
        /* ignore */
    }
})

function getSupplierName(cd: string): string {
    return supplierNameMap.value[cd] || cd || '-'
}

// ---- 筛选 ----
const searchSuppliercd = ref('')
const searchAuditflg = ref('')
const searchPayType = ref('')
const searchShowVoided = ref(false)

function doSearch() {
    const p: Record<string, string> = {}
    if (searchSuppliercd.value) p.suppliercd = searchSuppliercd.value
    if (searchAuditflg.value) p.auditflg = searchAuditflg.value
    if (searchPayType.value) p.pay_type = searchPayType.value
    if (searchShowVoided.value) p.show_voided = 'true'
    onSearch(p)
}

function doReset() {
    searchSuppliercd.value = ''
    searchAuditflg.value = ''
    searchPayType.value = ''
    onSearch({})
}

function quickFilter(flg: string) {
    searchAuditflg.value = flg
    doSearch()
}

// ---- 打开详情 ----
function handleRowClick(row: SettlementRecord) {
    drawer.value = true
    detail.value = row
    payableInfo.value = null
    fetchSettlementDetail(row.pcbillid)
        .then((r) => { detail.value = r.data })
        .catch(() => { /* keep row data */ })
    fetchSettlementPayable(row.pcbillid)
        .then((r) => { payableInfo.value = r.data ?? null })
        .catch(() => { payableInfo.value = null })
}

// ---- 审核 ----
const auditing = ref(false)
const auditLoading = ref(false)
const auditTarget = ref<SettlementRecord | null>(null)
const auditMemo = ref('')

async function doSubmit(row: SettlementRecord) {
    try {
        await auditSettlement(row.pcbillid, '1')
        ElMessage.success('已送审')
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '送审失败')
    }
}

async function openAudit(row: SettlementRecord) {
    auditTarget.value = row
    auditMemo.value = ''
    try {
        const r = await fetchSettlementDetail(row.pcbillid)
        auditTarget.value = r.data
    } catch {
        /* use row data */
    }
    auditing.value = true
}

async function doAudit(flg: string) {
    if (!auditTarget.value) return
    auditLoading.value = true
    try {
        await auditSettlement(auditTarget.value.pcbillid, flg)
        ElMessage.success(flg === '2' ? '审核通过' : '已退回')
        auditing.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '审核失败')
    } finally {
        auditLoading.value = false
    }
}

// ---- 作废 ----
const voiding = ref(false)
const voidTarget = ref<SettlementRecord | null>(null)
const voidLoading = ref(false)

function openVoid(row: SettlementRecord) {
    voidTarget.value = row
    voiding.value = true
}

async function doVoid() {
    if (!voidTarget.value) return
    voidLoading.value = true
    try {
        await voidSettlement(voidTarget.value.pcbillid)
        ElMessage.success('作废成功')
        voiding.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '作废失败')
    } finally {
        voidLoading.value = false
    }
}

// ---- 编辑结算单 ----
const editing = ref(false)
const editLoading = ref(false)
const editDetail = ref<SettlementRecord | null>(null)
const editForm = reactive({
    pay_type: 'COD',
    invoice_no: '',
    invoice_date: '',
    pcdate: '',
    whcd: [] as string[],
    memo: '',
    settlement_period: '',
    settle_stage: 'final',
    installment_no: null as number | null,
    total_installments: null as number | null,
    due_date: '',
})
const editDetails = reactive<{ ref_rgstbillid: string; ref_rgstlineno: number; itemcd: string; settle_qty: number; settle_price: number }[]>([])

async function openEdit(row: SettlementRecord) {
    try {
        const r = await fetchSettlementDetail(row.pcbillid)
        editDetail.value = r.data as SettlementRecord
        const d = editDetail.value
        editForm.pay_type = (d.pay_type as string) || 'COD'
        editForm.invoice_no = (d.invoice_no as string) || ''
        editForm.invoice_date = (d.invoice_date as string) || ''
        editForm.pcdate = (d.pcdate as string) || ''
        editForm.whcd = ((d.whcd as string) || '').split(',').filter(Boolean)
        // 如果 whcd 为空，从订单入库记录自动补全
        if (editForm.whcd.length === 0) {
            const orderIds = [...new Set((d.details as SettlementDetail[] || []).map(l => l.ref_rgstbillid).filter(Boolean))]
            const whSet = new Set<string>()
            for (const oid of orderIds) {
                try {
                    const r = await fetchSettleableItems(oid)
                    for (const l of (r.data || []) as any[]) {
                        if (l.receiving_whcd) whSet.add(l.receiving_whcd)
                    }
                } catch { /* skip */ }
            }
            if (whSet.size > 0) editForm.whcd = [...whSet]
        }
        editForm.memo = (d.memo as string) || ''
        editForm.settlement_period = (d.settlement_period as string) || ''
        editForm.settle_stage = (d.settle_stage as string) || 'final'
        editForm.installment_no = (d as any).installment_no != null ? Number((d as any).installment_no) : null
        editForm.total_installments = (d as any).total_installments != null ? Number((d as any).total_installments) : null
        editForm.due_date = (d as any).due_date ? (d as any).due_date.split('T')[0] : ''
        editDetails.length = 0
        const lines = (d.details || []) as SettlementDetail[]
        for (const l of lines) {
            editDetails.push({
                ref_rgstbillid: l.ref_rgstbillid,
                ref_rgstlineno: l.ref_rgstlineno,
                itemcd: l.itemcd,
                settle_qty: l.settle_qty,
                settle_price: l.settle_price,
            })
        }
        editing.value = true
    } catch { ElMessage.error('加载结算单详情失败') }
}

async function doEdit() {
    if (!editDetail.value) return
    const details = editDetails.filter(d => (d.settle_qty || 0) > 0)
    if (details.length === 0) { ElMessage.warning('请至少保留一行结算明细'); return }
    editLoading.value = true
    try {
        await updateSettlement(editDetail.value.pcbillid, {
            ...editForm,
            whcd: (editForm.whcd || []).join(','),
            details: details.map(d => ({
                ref_rgstbillid: d.ref_rgstbillid,
                ref_rgstlineno: d.ref_rgstlineno,
                itemcd: d.itemcd,
                settle_qty: d.settle_qty,
                settle_price: d.settle_price,
            })),
        })
        ElMessage.success('保存成功')
        editing.value = false
        load()
    } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
    finally { editLoading.value = false }
}

function resetEditForm() {
    editDetail.value = null
    editDetails.length = 0
}

// ---- 新建结算单 ----
const creating = ref(false)
const saving = ref(false)
const today = () => new Date().toISOString().split('T')[0]

const createForm = reactive({
    suppliercd: '',
    pay_type: 'COD',
    pcdate: today(),
    invoice_no: '',
    invoice_date: '',
    whcd: [] as string[],
    memo: '',
    settlement_period: '',
    settle_stage: 'final',
    installment_no: null as number | null,
    total_installments: null as number | null,
    due_date: '',
})

// 可结算明细（供应商下所有订单的可结算行）
interface SettleableLine {
    ref_rgstbillid: string
    ref_rgstlineno: number
    itemcd: string
    item_nm: string
    order_qty: number
    received_qty: number
    already_settled: number
    remain_qty: number
    unit_price: number
    receiving_whcd: string
    [key: string]: unknown
}

const settleableItems = ref<SettleableLine[]>([])
const settleableLoading = ref(false)
const globalRatio = ref(100)

function applyGlobalRatio() {
    const ratio = (globalRatio.value || 0) / 100
    if (ratio <= 0 || ratio > 1) return
    for (let i = 0; i < settleableItems.value.length; i++) {
        const row = settleableItems.value[i]
        const qty = Math.round(row.remain_qty * ratio)
        if (qty <= 0) continue
        if (!createDetails[i]) {
            createDetails[i] = {
                ref_rgstbillid: row.ref_rgstbillid,
                ref_rgstlineno: row.ref_rgstlineno,
                itemcd: row.itemcd,
                settle_qty: 0,
                settle_price: 0,
            }
        }
        createDetails[i].settle_qty = qty
        createDetails[i].settle_price = row.unit_price
    }
}

// 用户填写的结算明细（与 settleableItems 一一对应，通过 checkbox 选中）
interface CreateDetail {
    ref_rgstbillid: string
    ref_rgstlineno: number
    itemcd: string
    settle_qty: number
    settle_price: number
}

const createDetails = reactive<CreateDetail[]>([])
const selectedSettleableRows = ref<SettleableLine[]>([])

function onSettleableSelectionChange(rows: SettleableLine[]) {
    selectedSettleableRows.value = rows
    const whSet = new Set<string>()
    for (const row of rows) {
        if (row.receiving_whcd) whSet.add(row.receiving_whcd)
    }
    createForm.whcd = [...whSet]
}

function onSettleQtyChange(index: number, qty: number) {
    const row = settleableItems.value[index]
    if (!row) return
    if (!createDetails[index]) {
        createDetails[index] = {
            ref_rgstbillid: row.ref_rgstbillid,
            ref_rgstlineno: row.ref_rgstlineno,
            itemcd: row.itemcd,
            settle_qty: row.remain_qty,
            settle_price: row.unit_price,
        }
    }
    createDetails[index].settle_qty = qty
    // 单价兜底：仍为 0 时用订单单价
    if (!createDetails[index].settle_price) {
        createDetails[index].settle_price = row.unit_price
    }
}

function onSettlePriceChange(index: number, price: number) {
    if (!createDetails[index]) return
    createDetails[index].settle_price = price
}

function calcSettleAmt(index: number): string {
    const d = createDetails[index]
    if (!d) return '-'
    const amt = (d.settle_qty || 0) * (d.settle_price || 0)
    return amt > 0 ? amt.toFixed(2) : '-'
}

// 选择供应商后自动加载可结算明细
watch(
    () => createForm.suppliercd,
    async (val) => {
        if (!val) {
            settleableItems.value = []
            createDetails.length = 0
            return
        }
        settleableLoading.value = true
        settleableItems.value = []
        createDetails.length = 0
        try {
            // 获取该供应商的订单列表
            const ordersRes = await fetchOrders({
                suppliercd: val,
                auditflg: '2',
                per_page: '100',
            })
            const orders = (ordersRes.data?.items ||
                []) as Record<string, unknown>[]

            // 逐订单加载可结算明细
            const allLines: SettleableLine[] = []
            for (const order of orders) {
                const rgstbillid = order.rgstbillid as string
                if (!rgstbillid) continue
                try {
                    const r = await fetchSettleableItems(rgstbillid)
                    const lines = (r.data || []) as Record<string, unknown>[]
                    for (const line of lines) {
                        allLines.push({
                            ref_rgstbillid: rgstbillid,
                            ref_rgstlineno: Number(line.lineno) || 0,
                            itemcd: (line.itemcd as string) || '',
                            item_nm: (line.item_nm as string) || (line.itemcd as string) || '',
                            order_qty: Number(line.rgsqty) || 0,
                            received_qty: Number(line.received_qty) || 0,
                            already_settled: Number(line.already_settled) || 0,
                            remain_qty:
                                Number(line.remain_qty) ||
                                Math.max(
                                    0,
                                    (Number(line.received_qty) || 0) -
                                        (Number(line.already_settled) || 0)
                                ),
                            unit_price: Number(line.rgstprice) || 0,
                            receiving_whcd: (line as any).receiving_whcd as string || '',
                        })
                    }
                } catch {
                    /* skip orders that fail */
                }
            }
            const validLines = allLines.filter(l => l.remain_qty > 0)
            settleableItems.value = validLines
            createForm.whcd = []
            selectedSettleableRows.value = []
            // 初始化 createDetails，结算数量默认=可结算数量，单价默认来自订单单价
            for (let i = 0; i < validLines.length; i++) {
                createDetails.push({
                    ref_rgstbillid: validLines[i].ref_rgstbillid,
                    ref_rgstlineno: validLines[i].ref_rgstlineno,
                    itemcd: validLines[i].itemcd,
                    settle_qty: validLines[i].remain_qty,
                    settle_price: validLines[i].unit_price,
                })
            }
        } catch (e: any) {
            ElMessage.error(e?.response?.data?.message || '加载可结算明细失败')
        } finally {
            settleableLoading.value = false
        }
    }
)

// MON 月结：选择月份后过滤仅该月入库的订单
watch(
    () => [createForm.pay_type, createForm.settlement_period, createForm.suppliercd] as const,
    async ([payType, period, suppCd]) => {
        if (payType !== 'MON' || !period || !suppCd) return
        // 重新加载可结算明细，只包含该月入库的订单
        settleableLoading.value = true
        try {
            const monthlyRes = await fetchMonthlyReceiving(suppCd, period)
            const monthlyOrders = new Set(
                (monthlyRes.data || []).map((r: { rgstbillid: string }) => r.rgstbillid)
            )
            if (monthlyOrders.size === 0) {
                settleableItems.value = []
                createDetails.length = 0
                ElMessage.info(`供应商 ${suppCd} 在 ${period} 无入库记录`)
                return
            }
            // 只加载本月有入库的订单
            const allLines: SettleableLine[] = []
            for (const rgstbillid of monthlyOrders) {
                try {
                    const r = await fetchSettleableItems(rgstbillid)
                    const lines = (r.data || []) as Record<string, unknown>[]
                    for (const line of lines) {
                        allLines.push({
                            ref_rgstbillid: rgstbillid,
                            ref_rgstlineno: Number(line.lineno) || 0,
                            itemcd: (line.itemcd as string) || '',
                            item_nm: (line.item_nm as string) || (line.itemcd as string) || '',
                            order_qty: Number(line.rgsqty) || 0,
                            received_qty: Number(line.received_qty) || 0,
                            already_settled: Number(line.already_settled) || 0,
                            remain_qty:
                                Number(line.remain_qty) ||
                                Math.max(
                                    0,
                                    (Number(line.received_qty) || 0) -
                                        (Number(line.already_settled) || 0)
                                ),
                            unit_price: Number(line.rgstprice) || 0,
                            receiving_whcd: (line as any).receiving_whcd as string || '',
                        })
                    }
                } catch {
                    /* skip */
                }
            }
            const validLines = allLines.filter(l => l.remain_qty > 0)
            settleableItems.value = validLines
            createForm.whcd = []
            selectedSettleableRows.value = []
            createDetails.length = 0
            for (let i = 0; i < validLines.length; i++) {
                createDetails.push({
                    ref_rgstbillid: validLines[i].ref_rgstbillid,
                    ref_rgstlineno: validLines[i].ref_rgstlineno,
                    itemcd: validLines[i].itemcd,
                    settle_qty: validLines[i].remain_qty,
                    settle_price: validLines[i].unit_price,
                })
            }
        } catch (e: any) {
            ElMessage.error(e?.response?.data?.message || '加载月结明细失败')
        } finally {
            settleableLoading.value = false
        }
    }
)

// INS 分期：自动计算结算阶段（最后一期=尾款）—— 创建表单
watch(
    () => [createForm.pay_type, createForm.installment_no, createForm.total_installments] as const,
    ([payType, instNo, totalInst]) => {
        if (payType === 'INS' && instNo != null && totalInst != null && instNo > 0 && totalInst > 0) {
            createForm.settle_stage = instNo === totalInst ? 'final' : 'deposit'
        }
    }
)

// INS 分期：自动计算结算阶段（最后一期=尾款）—— 编辑表单
watch(
    () => [editForm.pay_type, editForm.installment_no, editForm.total_installments] as const,
    ([payType, instNo, totalInst]) => {
        if (payType === 'INS' && instNo != null && totalInst != null && instNo > 0 && totalInst > 0) {
            editForm.settle_stage = instNo === totalInst ? 'final' : 'deposit'
        }
    }
)

function openCreate() {
    creating.value = true
}

function resetCreateForm() {
    createForm.suppliercd = ''
    createForm.pay_type = 'COD'
    createForm.pcdate = today()
    createForm.invoice_no = ''
    createForm.invoice_date = ''
    createForm.whcd = []
    createForm.memo = ''
    createForm.settlement_period = ''
    createForm.settle_stage = 'final'
    createForm.installment_no = null
    createForm.total_installments = null
    createForm.due_date = ''
    settleableItems.value = []
    createDetails.length = 0
    selectedSettleableRows.value = []
}

async function handleCreate() {
    if (!createForm.suppliercd) {
        ElMessage.warning('请选择供应商')
        return
    }

    // 收集选中的结算明细
    const selectedIndices = selectedSettleableRows.value
        .map((row) =>
            settleableItems.value.findIndex(
                (item) =>
                    item.ref_rgstbillid === row.ref_rgstbillid &&
                    item.ref_rgstlineno === row.ref_rgstlineno &&
                    item.itemcd === row.itemcd
            )
        )
        .filter((i) => i >= 0 && i < createDetails.length)

    if (selectedIndices.length === 0) {
        ElMessage.warning('请勾选要结算的明细')
        return
    }

    const detailsToSubmit = selectedIndices
        .map((i) => {
            const d = createDetails[i]
            if (!d || !d.settle_qty || d.settle_qty <= 0) return null
            return {
                ref_rgstbillid: d.ref_rgstbillid,
                ref_rgstlineno: d.ref_rgstlineno,
                itemcd: d.itemcd,
                settle_qty: d.settle_qty,
                settle_price: d.settle_price || 0,
            }
        })
        .filter(Boolean) as {
        ref_rgstbillid: string
        ref_rgstlineno: number
        itemcd: string
        settle_qty: number
        settle_price: number
    }[]

    if (detailsToSubmit.length === 0) {
        ElMessage.warning('请填写结算数量和单价')
        return
    }

    // 检查是否有未填单价的
    const noPrice = detailsToSubmit.find(
        (d) => !d.settle_price || d.settle_price <= 0
    )
    if (noPrice) {
        try {
            await ElMessageBox.confirm(
                '存在未填写单价的明细，确认继续？',
                '提示',
                {
                    type: 'warning',
                    confirmButtonText: '确认',
                    cancelButtonText: '取消',
                }
            )
        } catch {
            return
        }
    }

    saving.value = true
    try {
        await createSettlement({
            suppliercd: createForm.suppliercd,
            pay_type: createForm.pay_type,
            pcdate: createForm.pcdate,
            invoice_no: createForm.invoice_no,
            invoice_date: createForm.invoice_date,
            whcd: (createForm.whcd || []).join(','),
            memo: createForm.memo,
            settlement_period: createForm.settlement_period || undefined,
            settle_stage: createForm.settle_stage || undefined,
            installment_no: createForm.installment_no ?? undefined,
            total_installments: createForm.total_installments ?? undefined,
            due_date: createForm.due_date || undefined,
            details: detailsToSubmit,
        })
        ElMessage.success('结算单创建成功')
        creating.value = false
        resetCreateForm()
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '创建失败')
    } finally {
        saving.value = false
    }
}

// ---- 创建：金额汇总 ----
function calcCreateOrderAmt(): string {
    const amt = selectedSettleableRows.value.reduce((s, r) => s + (r.order_qty || 0) * (r.unit_price || 0), 0)
    return amt.toFixed(2)
}
function calcCreateSettled(): string {
    const amt = selectedSettleableRows.value.reduce((s, r) => s + (r.already_settled || 0) * (r.unit_price || 0), 0)
    return amt.toFixed(2)
}
function calcCreateCurrent(): string {
    const amt = selectedSettleableRows.value.reduce((s, row) => {
        const idx = settleableItems.value.findIndex(
            i => i.ref_rgstbillid === row.ref_rgstbillid && i.ref_rgstlineno === row.ref_rgstlineno && i.itemcd === row.itemcd
        )
        if (idx < 0 || !createDetails[idx]) return s
        return s + (createDetails[idx].settle_qty || 0) * (createDetails[idx].settle_price || 0)
    }, 0)
    return amt.toFixed(2)
}
function calcCreateRemaining(): string {
    const orderAmt = selectedSettleableRows.value.reduce((s, r) => s + (r.order_qty || 0) * (r.unit_price || 0), 0)
    const settled = selectedSettleableRows.value.reduce((s, r) => s + (r.already_settled || 0) * (r.unit_price || 0), 0)
    const current = selectedSettleableRows.value.reduce((s, row) => {
        const idx = settleableItems.value.findIndex(
            i => i.ref_rgstbillid === row.ref_rgstbillid && i.ref_rgstlineno === row.ref_rgstlineno && i.itemcd === row.itemcd
        )
        if (idx < 0 || !createDetails[idx]) return s
        return s + (createDetails[idx].settle_qty || 0) * (createDetails[idx].settle_price || 0)
    }, 0)
    return Math.max(0, orderAmt - settled - current).toFixed(2)
}

// ---- 编辑：金额汇总 ----
function calcEditOrderAmt(): string {
    if (!editDetail.value?.details) return '0.00'
    const details = editDetail.value.details as SettlementDetail[]
    const amt = details.reduce((s, d) => s + (d.order_qty || 0) * (d.settle_price || 0), 0)
    return amt.toFixed(2)
}
function calcEditSettled(): string {
    if (!editDetail.value?.details) return '0.00'
    const details = editDetail.value.details as SettlementDetail[]
    const amt = details.reduce((s, d) => s + (d.already_settled || 0) * (d.settle_price || 0), 0)
    return amt.toFixed(2)
}
function calcEditCurrent(): string {
    const amt = editDetails.reduce((s, d) => s + (d.settle_qty || 0) * (d.settle_price || 0), 0)
    return amt.toFixed(2)
}
function calcEditRemaining(): string {
    if (!editDetail.value?.details) return '0.00'
    const details = editDetail.value.details as SettlementDetail[]
    const orderAmt = details.reduce((s, d) => s + (d.order_qty || 0) * (d.settle_price || 0), 0)
    const settled = details.reduce((s, d) => s + (d.already_settled || 0) * (d.settle_price || 0), 0)
    const current = editDetails.reduce((s, d) => s + (d.settle_qty || 0) * (d.settle_price || 0), 0)
    return Math.max(0, orderAmt - settled - current).toFixed(2)
}

// ---- 详情：金额汇总 ----
function calcDetailOrderAmt(): string {
    if (!detail.value?.details) return '0.00'
    const details = detail.value.details as SettlementDetail[]
    const amt = details.reduce((s, d) => s + (d.order_qty || 0) * (d.settle_price || 0), 0)
    return amt.toFixed(2)
}
function calcDetailSettled(): string {
    if (!detail.value?.details) return '0.00'
    const details = detail.value.details as SettlementDetail[]
    const amt = details.reduce((s, d) => s + (d.already_settled || 0) * (d.settle_price || 0), 0)
    return amt.toFixed(2)
}
function calcDetailCurrent(): string {
    if (!detail.value?.details) return '0.00'
    const details = detail.value.details as SettlementDetail[]
    const amt = details.reduce((s, d) => s + (d.settle_amt || 0), 0)
    return amt.toFixed(2)
}
function calcDetailRemaining(): string {
    if (!detail.value?.details) return '0.00'
    const details = detail.value.details as SettlementDetail[]
    const orderAmt = details.reduce((s, d) => s + (d.order_qty || 0) * (d.settle_price || 0), 0)
    const settled = details.reduce((s, d) => s + (d.already_settled || 0) * (d.settle_price || 0), 0)
    const current = details.reduce((s, d) => s + (d.settle_amt || 0), 0)
    return Math.max(0, orderAmt - settled - current).toFixed(2)
}

// ---- 工具函数 ----
function formatDate(val: string | undefined): string {
    if (!val) return '-'
    return val.split('T')[0]
}
</script>

<style scoped>
.page {
    padding: 0;
}
.page-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
}
.page-header h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
}
.search-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.search-bar .field {
    display: flex;
    align-items: center;
    gap: 6px;
}
.search-bar .field label {
    font-size: 13px;
    color: #606266;
    white-space: nowrap;
}
</style>
