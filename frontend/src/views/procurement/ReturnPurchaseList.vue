<template>
  <div class="page">
    <div class="page-header">
      <h2>采购退货单</h2>
      <div style="display:flex;gap:8px">
        <el-button type="warning" size="small" plain @click="quickFilter('0')">未审核</el-button>
        <el-button type="primary" size="small" @click="openCreate">新建退货单</el-button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field">
          <label>来源订单</label>
          <el-select
            v-model="searchOrder"
            size="small"
            style="width:180px"
            clearable
            filterable
            placeholder="选择订单"
            @change="doSearch"
          >
            <el-option
              v-for="o in orderOptions"
              :key="o.rgstbillid"
              :label="o.rgstbillid"
              :value="o.rgstbillid"
            />
          </el-select>
        </div>
        <div class="field">
          <label>退货原因</label>
          <el-select
            v-model="searchReason"
            size="small"
            style="width:140px"
            clearable
            @change="doSearch"
          >
            <el-option
              v-for="(nm, cd) in reasonMap"
              :key="cd"
              :label="nm"
              :value="cd"
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
        <el-table-column prop="pcbillid" label="退货单号" width="120" />
        <el-table-column prop="ref_rgstbillid" label="来源订单" width="100" />
        <el-table-column label="退货原因" width="110">
          <template #default="{ row }">
            {{ reasonMap[row.return_reason as string] || row.return_reason || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="退货金额" width="110" align="right">
          <template #default="{ row }">
            {{ row.pcamt != null ? Number(row.pcamt).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="审批" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.auditflg === '2' ? 'success' : row.auditflg === '9' ? 'danger' : 'warning'"
              size="small"
            >
              {{ auditMap[row.auditflg as string] || '未审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="退货日期" width="110">
          <template #default="{ row }">
            {{ formatDate(row.pcdate || row.gendate) }}
          </template>
        </el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column prop="whcd" label="仓库" width="70" />
        <el-table-column label="操作员" width="80">
          <template #default="{ row }">
            {{ userName(row.opercd) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="row.auditflg !== '9'">
              <el-button
                v-if="row.auditflg === '0'"
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
      :title="'退货单 — ' + (detail?.pcbillid || '')"
      v-model="drawer"
      width="820px"
    >
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="退货单号">{{ detail.pcbillid }}</el-descriptions-item>
          <el-descriptions-item label="来源订单">
            {{ detail.ref_rgstbillid || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退货原因">
            {{ reasonMap[detail.return_reason as string] || detail.return_reason || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退货金额">
            {{ detail.pcamt != null ? Number(detail.pcamt).toLocaleString() : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退货日期">
            {{ formatDate(detail.pcdate || detail.gendate) }}
          </el-descriptions-item>
          <el-descriptions-item label="仓库">{{ detail.whcd || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审批人">{{ detail.auditman || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审批日期">
            {{ formatDate(detail.auditdate) }}
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">
            {{ detail.memo || '-' }}
          </el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">退货明细</h4>
        <el-table
          :data="(detail.details as ReturnPurchaseDetail[]) || []"
          size="small"
          stripe
        >
          <el-table-column prop="itemcd" label="物料编码" width="100" />
          <el-table-column prop="rpcqty" label="退货数量" width="90" align="right" />
          <el-table-column label="退货单价" width="90" align="right">
            <template #default="{ row }">
              {{ row.return_price != null ? Number(row.return_price).toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="退货金额" width="100" align="right">
            <template #default="{ row }">
              {{ row.return_amt != null ? Number(row.return_amt).toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="eid" label="设备EID" width="140" />
          <el-table-column prop="line_reason" label="行级原因" min-width="120" show-overflow-tooltip />
        </el-table>
      </template>
    </el-dialog>

    <!-- 审核弹窗 -->
    <el-dialog
      title="审核退货单"
      v-model="auditing"
      width="600px"
      @closed="auditTarget = null; auditMemo = ''"
    >
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="退货单号">
            {{ auditTarget.pcbillid }}
          </el-descriptions-item>
          <el-descriptions-item label="来源订单">
            {{ auditTarget.ref_rgstbillid || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退货原因">
            {{ reasonMap[auditTarget.return_reason as string] || auditTarget.return_reason || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退货金额">
            {{ auditTarget.pcamt != null ? Number(auditTarget.pcamt).toLocaleString() : '-' }}
          </el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:12px 0 8px">退货明细</h4>
        <el-table
          :data="(auditTarget.details as ReturnPurchaseDetail[]) || []"
          size="small"
          stripe
        >
          <el-table-column prop="itemcd" label="物料编码" width="100" />
          <el-table-column prop="rpcqty" label="退货数量" width="90" align="right" />
          <el-table-column label="退货单价" width="90" align="right">
            <template #default="{ row }">
              {{ row.return_price != null ? Number(row.return_price).toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="退货金额" width="100" align="right">
            <template #default="{ row }">
              {{ row.return_amt != null ? Number(row.return_amt).toFixed(2) : '-' }}
            </template>
          </el-table-column>
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
          退回
        </el-button>
        <el-button type="success" @click="doAudit('2')" :loading="auditLoading">
          审核通过
        </el-button>
      </template>
    </el-dialog>

    <!-- 作废弹窗 -->
    <el-dialog title="作废退货单" v-model="voiding" width="400px">
      <template v-if="voidTarget">
        <p>
          确认作废退货单 <strong>{{ voidTarget.pcbillid }}</strong> 吗？
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

    <!-- 新建退货单 -->
    <el-dialog
      title="新建采购退货单"
      v-model="creating"
      width="950px"
      @closed="resetCreateForm"
    >
      <el-form :model="createForm" label-width="100px" size="small">
        <el-form-item label="来源订单">
          <el-select
            v-model="createForm.ref_rgstbillid"
            style="width:100%"
            filterable
            placeholder="选择已审核的采购订单"
          >
            <el-option
              v-for="o in auditedOrderOptions"
              :key="o.rgstbillid"
              :label="o.rgstbillid"
              :value="o.rgstbillid"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="退货原因">
          <el-select v-model="createForm.return_reason" style="width:100%">
            <el-option
              v-for="(nm, cd) in reasonMap"
              :key="cd"
              :label="nm"
              :value="cd"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="退货日期">
          <el-date-picker
            v-model="createForm.pcdate"
            type="date"
            style="width:100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="仓库">
          <el-input
            v-model="createForm.whcd"
            placeholder="仓库编码"
            maxlength="2"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="createForm.memo"
            type="textarea"
            :rows="2"
          />
        </el-form-item>

        <el-form-item label="退货明细">
          <div style="width:100%">
            <el-alert
              v-if="!createForm.ref_rgstbillid"
              title="请先选择来源订单"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom:8px"
            />
            <el-alert
              v-if="createForm.ref_rgstbillid && returnableLoading"
              title="正在加载可退货明细..."
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom:8px"
            />
            <el-alert
              v-if="
                createForm.ref_rgstbillid &&
                  !returnableLoading &&
                  returnableItems.length === 0
              "
              title="该订单没有可退货的商品明细"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom:8px"
            />
            <el-table
              v-if="returnableItems.length > 0"
              :data="returnableItems"
              size="small"
              @selection-change="onReturnableSelectionChange"
            >
              <el-table-column type="selection" width="50" />
              <el-table-column prop="itemcd" label="物料编码" width="100" />
              <el-table-column prop="itemnm" label="物料名称" min-width="120" show-overflow-tooltip />
              <el-table-column prop="received_qty" label="已收货" width="80" align="right" />
              <el-table-column prop="already_returned" label="已退货" width="80" align="right" />
              <el-table-column prop="returnable_qty" label="可退货" width="90" align="right" />
              <el-table-column label="退货数量" width="110">
                <template #default="{ row, $index }">
                  <el-input-number
                    :model-value="createDetails[$index]?.rpcqty"
                    @update:model-value="
                      (v: number | undefined) =>
                        onReturnQtyChange($index, v || 0)
                    "
                    :min="0"
                    :max="Number(row.returnable_qty) || 0"
                    size="small"
                    style="width:100px"
                    controls-position="right"
                  />
                </template>
              </el-table-column>
              <el-table-column label="退货单价" width="120">
                <template #default="{ row, $index }">
                  <el-input-number
                    :model-value="createDetails[$index]?.return_price"
                    @update:model-value="
                      (v: number | undefined) =>
                        onReturnPriceChange($index, v || 0)
                    "
                    :min="0"
                    :precision="2"
                    size="small"
                    style="width:110px"
                    controls-position="right"
                  />
                </template>
              </el-table-column>
              <el-table-column label="退货金额" width="100" align="right">
                <template #default="{ $index }">
                  {{ calcReturnAmt($index) }}
                </template>
              </el-table-column>
              <el-table-column label="行级原因" width="140">
                <template #default="{ $index }">
                  <el-input
                    :model-value="createDetails[$index]?.line_reason"
                    @update:model-value="
                      (v: string | undefined) =>
                        onLineReasonChange($index, v || '')
                    "
                    size="small"
                    placeholder="可选"
                    maxlength="100"
                  />
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
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useDetailDrawer } from '@/composables/useDetailDrawer'
import { useUserNames } from '@/composables/useUserNames'
import {
    fetchReturns,
    fetchReturnDetail,
    createReturn,
    auditReturn,
    voidReturn,
    fetchReturnableItems,
    fetchOrders,
} from '@/api/procurement'
import type { ReturnPurchaseRecord, ReturnPurchaseDetail } from '@/api/procurement'

// ---- 字典映射 ----
const reasonMap: Record<string, string> = {
    quality: '质量问题',
    quantity: '数量不符',
    spec: '规格错误',
    other: '其他',
}
const auditMap: Record<string, string> = {
    '0': '未审核',
    '2': '已审核',
    '9': '已作废',
}

// ---- composables ----
const { userName } = useUserNames()
const { items, loading, page, perPage, total, load, onSearch } =
    useListPage<ReturnPurchaseRecord>(fetchReturns)
const { drawer, detail } = useDetailDrawer<ReturnPurchaseRecord>()

// ---- 订单选项（筛选 + 新建共用） ----
interface OrderOption {
    rgstbillid: string
}
const orderOptions = ref<OrderOption[]>([])
const auditedOrderOptions = ref<OrderOption[]>([])

onMounted(async () => {
    try {
        // 加载全部订单用于筛选下拉
        const allRes = await fetchOrders({ per_page: '100' })
        const allList = (allRes.data?.items || []) as Record<string, unknown>[]
        orderOptions.value = allList.map((o) => ({
            rgstbillid: o.rgstbillid as string,
        }))
        // 加载已审核订单用于新建下拉
        const auditedRes = await fetchOrders({ auditflg: '2', per_page: '100' })
        const auditedList = (auditedRes.data?.items || []) as Record<string, unknown>[]
        auditedOrderOptions.value = auditedList.map((o) => ({
            rgstbillid: o.rgstbillid as string,
        }))
    } catch {
        /* ignore */
    }
})

// ---- 筛选 ----
const searchOrder = ref('')
const searchReason = ref('')
const searchAuditflg = ref('')

function doSearch() {
    const p: Record<string, string> = {}
    if (searchOrder.value) p.ref_rgstbillid = searchOrder.value
    if (searchReason.value) p.return_reason = searchReason.value
    if (searchAuditflg.value) p.auditflg = searchAuditflg.value
    onSearch(p)
}

function doReset() {
    searchOrder.value = ''
    searchReason.value = ''
    searchAuditflg.value = ''
    onSearch({})
}

function quickFilter(flg: string) {
    searchAuditflg.value = flg
    doSearch()
}

// ---- 打开详情 ----
function handleRowClick(row: ReturnPurchaseRecord) {
    drawer.value = true
    detail.value = row
    fetchReturnDetail(row.pcbillid)
        .then((r) => { detail.value = r.data })
        .catch(() => { /* keep row data */ })
}

// ---- 审核 ----
const auditing = ref(false)
const auditLoading = ref(false)
const auditTarget = ref<ReturnPurchaseRecord | null>(null)
const auditMemo = ref('')

async function doSubmit(row: ReturnPurchaseRecord) {
    try {
        await auditReturn(row.pcbillid, '1')
        ElMessage.success('已送审')
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '送审失败')
    }
}

async function openAudit(row: ReturnPurchaseRecord) {
    auditTarget.value = row
    auditMemo.value = ''
    try {
        const r = await fetchReturnDetail(row.pcbillid)
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
        await auditReturn(auditTarget.value.pcbillid, flg)
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
const voidTarget = ref<ReturnPurchaseRecord | null>(null)
const voidLoading = ref(false)

function openVoid(row: ReturnPurchaseRecord) {
    voidTarget.value = row
    voiding.value = true
}

async function doVoid() {
    if (!voidTarget.value) return
    voidLoading.value = true
    try {
        await voidReturn(voidTarget.value.pcbillid)
        ElMessage.success('作废成功')
        voiding.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '作废失败')
    } finally {
        voidLoading.value = false
    }
}

// ---- 新建退货单 ----
const creating = ref(false)
const saving = ref(false)
const today = () => new Date().toISOString().split('T')[0]

const createForm = reactive({
    ref_rgstbillid: '',
    return_reason: 'quality',
    pcdate: today(),
    whcd: '',
    memo: '',
})

// 可退货明细（选中订单下的可退货行）
interface ReturnableLine {
    itemcd: string
    itemnm: string
    lineno: number
    rgsqty: number
    rgstprice: number
    received_qty: number
    already_returned: number
    returnable_qty: number
    units: string
    [key: string]: unknown
}

const returnableItems = ref<ReturnableLine[]>([])
const returnableLoading = ref(false)

// 用户填写的退货明细（与 returnableItems 一一对应）
interface CreateDetail {
    itemcd: string
    ref_rgstlineno: number
    rpcqty: number
    return_price: number
    units: string
    line_reason: string
}

const createDetails = reactive<CreateDetail[]>([])
const selectedReturnableRows = ref<ReturnableLine[]>([])

function onReturnableSelectionChange(rows: ReturnableLine[]) {
    selectedReturnableRows.value = rows
}

function onReturnQtyChange(index: number, qty: number) {
    const row = returnableItems.value[index]
    if (!row) return
    if (!createDetails[index]) {
        createDetails[index] = {
            itemcd: row.itemcd,
            ref_rgstlineno: row.lineno,
            rpcqty: 0,
            return_price: Number(row.rgstprice) || 0,
            units: row.units || '',
            line_reason: '',
        }
    }
    createDetails[index].rpcqty = qty
}

function onReturnPriceChange(index: number, price: number) {
    if (!createDetails[index]) return
    createDetails[index].return_price = price
}

function onLineReasonChange(index: number, reason: string) {
    if (!createDetails[index]) return
    createDetails[index].line_reason = reason
}

function calcReturnAmt(index: number): string {
    const d = createDetails[index]
    if (!d) return '-'
    const amt = (d.rpcqty || 0) * (d.return_price || 0)
    return amt > 0 ? amt.toFixed(2) : '-'
}

// 选择订单后自动加载可退货明细
watch(
    () => createForm.ref_rgstbillid,
    async (val) => {
        if (!val) {
            returnableItems.value = []
            createDetails.length = 0
            return
        }
        returnableLoading.value = true
        returnableItems.value = []
        createDetails.length = 0
        try {
            const r = await fetchReturnableItems(val)
            const lines = (r.data || []) as Record<string, unknown>[]
            returnableItems.value = lines.map((line) => ({
                itemcd: (line.itemcd as string) || '',
                itemnm: (line.itemnm as string) || (line.itemcd as string) || '',
                lineno: Number(line.lineno) || 0,
                rgsqty: Number(line.rgsqty) || 0,
                rgstprice: Number(line.rgstprice) || 0,
                received_qty: Number(line.received_qty) || 0,
                already_returned: Number(line.already_returned) || 0,
                returnable_qty: Number(line.returnable_qty) || 0,
                units: (line.units as string) || '',
            }))

            // 初始化 createDetails，默认单价取 rgstprice
            for (let i = 0; i < returnableItems.value.length; i++) {
                const item = returnableItems.value[i]
                createDetails.push({
                    itemcd: item.itemcd,
                    ref_rgstlineno: item.lineno,
                    rpcqty: 0,
                    return_price: item.rgstprice,
                    units: item.units,
                    line_reason: '',
                })
            }
        } catch (e: any) {
            ElMessage.error(e?.response?.data?.message || '加载可退货明细失败')
        } finally {
            returnableLoading.value = false
        }
    }
)

function openCreate() {
    creating.value = true
}

function resetCreateForm() {
    createForm.ref_rgstbillid = ''
    createForm.return_reason = 'quality'
    createForm.pcdate = today()
    createForm.whcd = ''
    createForm.memo = ''
    returnableItems.value = []
    createDetails.length = 0
    selectedReturnableRows.value = []
}

async function handleCreate() {
    if (!createForm.ref_rgstbillid) {
        ElMessage.warning('请选择来源订单')
        return
    }
    if (!createForm.return_reason) {
        ElMessage.warning('请选择退货原因')
        return
    }

    // 收集选中的退货明细
    const selectedIndices = selectedReturnableRows.value
        .map((row) =>
            returnableItems.value.findIndex(
                (item) =>
                    item.itemcd === row.itemcd &&
                    item.lineno === row.lineno
            )
        )
        .filter((i) => i >= 0 && i < createDetails.length)

    if (selectedIndices.length === 0) {
        ElMessage.warning('请勾选要退货的明细')
        return
    }

    const detailsToSubmit = selectedIndices
        .map((i) => {
            const d = createDetails[i]
            if (!d || !d.rpcqty || d.rpcqty <= 0) return null
            return {
                itemcd: d.itemcd,
                ref_rgstlineno: d.ref_rgstlineno,
                rpcqty: d.rpcqty,
                return_price: d.return_price || 0,
                units: d.units,
                line_reason: d.line_reason || undefined,
            }
        })
        .filter(Boolean) as {
        itemcd: string
        ref_rgstlineno: number
        rpcqty: number
        return_price: number
        units: string
        line_reason?: string
    }[]

    if (detailsToSubmit.length === 0) {
        ElMessage.warning('请填写退货数量')
        return
    }

    saving.value = true
    try {
        await createReturn({
            ref_rgstbillid: createForm.ref_rgstbillid,
            return_reason: createForm.return_reason,
            pcdate: createForm.pcdate,
            whcd: createForm.whcd || undefined,
            memo: createForm.memo || undefined,
            details: detailsToSubmit,
        })
        ElMessage.success('退货单创建成功')
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
