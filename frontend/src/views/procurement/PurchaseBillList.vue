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
          <el-descriptions-item label="仓库">{{ detail.whcd || '-' }}</el-descriptions-item>
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
        </el-table>
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
            {{ auditTarget.whcd || '-' }}
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
        </el-table>
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
} from '@/api/procurement'
import type { SettlementRecord, SettlementDetail } from '@/api/procurement'
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

// ---- 供应商/仓库选项 ----
const supplierOptions = ref<{ supp_cd: string; supp_nm: string }[]>([])
const supplierNameMap = ref<Record<string, string>>({})
const warehouseOptions = ref<{ whcd: string; whnm: string }[]>([])

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
        warehouseOptions.value = (r.data as { whcd: string; whnm: string }[]) || []
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

function doSearch() {
    const p: Record<string, string> = {}
    if (searchSuppliercd.value) p.suppliercd = searchSuppliercd.value
    if (searchAuditflg.value) p.auditflg = searchAuditflg.value
    if (searchPayType.value) p.pay_type = searchPayType.value
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
    fetchSettlementDetail(row.pcbillid)
        .then((r) => { detail.value = r.data })
        .catch(() => { /* keep row data */ })
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
const editForm = reactive({ pay_type: 'COD', invoice_no: '', invoice_date: '', pcdate: '', whcd: [] as string[], memo: '' })
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
    [key: string]: unknown
}

const settleableItems = ref<SettleableLine[]>([])
const settleableLoading = ref(false)

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
                        })
                    }
                } catch {
                    /* skip orders that fail */
                }
            }
            settleableItems.value = allLines
            // 自动关联入库仓库
            const whSet = new Set<string>()
            for (const l of allLines) {
                const w = (l as any).receiving_whcd as string
                if (w) whSet.add(w)
            }
            if (whSet.size >= 1) {
                createForm.whcd = [...whSet] // 自动全选所有关联仓库
            }
            // 初始化 createDetails，结算数量默认=可结算数量，单价默认来自订单单价
            for (let i = 0; i < allLines.length; i++) {
                createDetails.push({
                    ref_rgstbillid: allLines[i].ref_rgstbillid,
                    ref_rgstlineno: allLines[i].ref_rgstlineno,
                    itemcd: allLines[i].itemcd,
                    settle_qty: allLines[i].remain_qty,
                    settle_price: allLines[i].unit_price,
                })
            }
        } catch (e: any) {
            ElMessage.error(e?.response?.data?.message || '加载可结算明细失败')
        } finally {
            settleableLoading.value = false
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
