<template>
  <div class="material-charge-pane">
    <!-- 顶部 c_type 筛选 -->
    <div class="mc-filter">
      <el-select
        v-model="filterCType"
        placeholder="全部类型"
        clearable
        size="small"
        style="width:160px"
      >
        <el-option
          v-for="opt in cTypeOptions"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>
    </div>

    <ItsmSubTablePane
      :maintenance-id="maintenanceId"
      title="物料与收费"
      :fetch-fn="fetchFn"
      :create-fn="createAccessories"
      :update-fn="updateAccessories"
      :create-disabled="isClosed"
    >
      <template #columns>
        <el-table-column
          label="类型"
          width="90"
        >
          <template #default="{row}">
            <el-tag :type="cTypeTag(row.c_type as string)" size="small">
              {{ cTypeLabel(row.c_type as string) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="device_id"
          label="整机"
          width="130"
          show-overflow-tooltip
        />
        <el-table-column
          prop="old_accessories_id"
          label="旧配件"
          width="120"
          show-overflow-tooltip
        />
        <el-table-column
          prop="new_accessories_id"
          label="新配件"
          width="120"
          show-overflow-tooltip
        />
        <el-table-column
          prop="accessories_type"
          label="配件/项目"
          width="120"
          show-overflow-tooltip
        />
        <el-table-column
          prop="paytype"
          label="收费类型"
          width="100"
          show-overflow-tooltip
        >
          <template #default="{row}">
            {{ paytypeLabel(row) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="price"
          label="配件价格"
          width="90"
          align="right"
        />
        <el-table-column
          prop="payje"
          label="收款金额"
          width="90"
          align="right"
        />
        <el-table-column
          label="工程师"
          width="80"
        >
          <template #default="{row}">
            {{ row.engineer_id_nm || row.engineer_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          label="描述"
          min-width="120"
          show-overflow-tooltip
        />
      </template>
      <template #form="{ form }">
        <el-form-item label="操作类型">
          <el-select
            v-model="form.c_type"
            style="width:100%"
            placeholder="选择操作类型"
          >
            <el-option
              v-for="opt in cTypeOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <!-- 公共：门店/工程师 -->
        <el-form-item label="门店">
          <el-input v-model="form.store_id" />
        </el-form-item>
        <el-form-item label="工程师">
          <el-input v-model="form.engineer_id" />
        </el-form-item>

        <!-- c_type=1 配件更换：设备+旧/新配件+故障代码+价格 -->
        <template v-if="form.c_type === '1'">
          <el-form-item label="整机">
            <el-input v-model="form.device_id" />
          </el-form-item>
          <el-form-item label="旧配件">
            <el-select
              v-model="form.old_accessories_id"
              filterable
              remote
              :remote-method="loadOldCandidates"
              :loading="oldLoading"
              placeholder="选择门店有效资产"
              style="width:100%"
            >
              <el-option
                v-for="opt in oldCandidates"
                :key="opt.eid as string"
                :label="(opt.eid as string) + ' / ' + (opt.itemcd as string)"
                :value="opt.eid as string"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="新配件">
            <el-select
              v-model="form.new_accessories_id"
              filterable
              remote
              :remote-method="loadNewCandidates"
              :loading="newLoading"
              placeholder="默认仓 + 工程师仓"
              style="width:100%"
              @change="(v:string) => onNewAccSelect(form, v)"
            >
              <el-option
                v-for="opt in newCandidates"
                :key="opt.eid as string"
                :label="(opt.eid as string) + ' / ' + (opt.itemcd as string) + (opt.source==='engineer'?' [工程师仓]':' [默认仓]')"
                :value="opt.eid as string"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="配件编码">
            <el-input
              v-model="form.itemcd"
              placeholder="配件编码（前两位过滤故障现象）"
              @change="() => onItemcdChange(form)"
            />
          </el-form-item>
          <el-form-item label="故障代码">
            <FaultCodeCascader
              :model-value="(form.fault_cd as string) || ''"
              :fault-type="(form.itemcd as string || '').slice(0, 2)"
              :store-id="(form.store_id as string) || ''"
              placeholder="按配件类型自动过滤"
              @update:model-value="(v:string) => form.fault_cd = v"
            />
          </el-form-item>
          <el-form-item label="配件类型">
            <el-input v-model="form.accessories_type" />
          </el-form-item>
          <el-form-item label="配件价格">
            <el-input
              v-model="form.price"
              type="number"
            />
          </el-form-item>
          <el-form-item label="收款金额">
            <el-input
              v-model="form.payje"
              type="number"
              placeholder="与配件价格同步"
            />
          </el-form-item>
          <el-form-item label="是否入库">
            <el-select v-model="form.in_wh" style="width:100%">
              <el-option label="是" value="1" />
              <el-option label="否" value="0" />
            </el-select>
          </el-form-item>
        </template>

        <!-- c_type=2 购买：新配件+配件类型+价格 -->
        <template v-else-if="form.c_type === '2'">
          <el-form-item label="新配件">
            <el-select
              v-model="form.new_accessories_id"
              filterable
              remote
              :remote-method="loadNewCandidates"
              :loading="newLoading"
              placeholder="默认仓 + 工程师仓"
              style="width:100%"
              @change="(v:string) => onNewAccSelect(form, v)"
            >
              <el-option
                v-for="opt in newCandidates"
                :key="opt.eid as string"
                :label="(opt.eid as string) + ' / ' + (opt.itemcd as string) + (opt.source==='engineer'?' [工程师仓]':' [默认仓]')"
                :value="opt.eid as string"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="配件编码">
            <el-input
              v-model="form.itemcd"
              placeholder="配件编码（前两位过滤故障现象）"
              @change="() => onItemcdChange(form)"
            />
          </el-form-item>
          <el-form-item label="故障代码">
            <FaultCodeCascader
              :model-value="(form.fault_cd as string) || ''"
              :fault-type="(form.itemcd as string || '').slice(0, 2)"
              :store-id="(form.store_id as string) || ''"
              placeholder="按配件类型自动过滤"
              @update:model-value="(v:string) => form.fault_cd = v"
            />
          </el-form-item>
          <el-form-item label="配件类型">
            <el-input v-model="form.accessories_type" />
          </el-form-item>
          <el-form-item label="配件价格">
            <el-input
              v-model="form.price"
              type="number"
            />
          </el-form-item>
          <el-form-item label="收款金额">
            <el-input
              v-model="form.payje"
              type="number"
              placeholder="与配件价格同步"
            />
          </el-form-item>
          <el-form-item label="是否入库">
            <el-select v-model="form.in_wh" style="width:100%">
              <el-option label="是" value="1" />
              <el-option label="否" value="0" />
            </el-select>
          </el-form-item>
        </template>

        <!-- c_type=3 纯服务费：收费类型+金额+收款日期 -->
        <template v-else-if="form.c_type === '3'">
          <el-form-item label="收费类型">
            <el-select
              v-model="form.paytype"
              style="width:100%"
              placeholder="选择收费类型"
            >
              <el-option
                v-for="opt in paySvcOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="收款金额">
            <el-input
              v-model="form.payje"
              type="number"
            />
          </el-form-item>
          <el-form-item label="收款日期">
            <el-date-picker
              v-model="form.paydate"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="选择收款日期"
              style="width:100%"
            />
          </el-form-item>
          <el-form-item label="收据号">
            <el-input v-model="form.receipt_id" />
          </el-form-item>
          <el-form-item label="送货单">
            <el-input v-model="form.delivery_id" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="form.memo"
              type="textarea"
            />
          </el-form-item>
        </template>

        <!-- c_type=4 整机更换：设备+新配件+posflg+价格 -->
        <template v-else-if="form.c_type === '4'">
          <el-form-item label="整机">
            <el-input v-model="form.device_id" />
          </el-form-item>
          <el-form-item label="新配件">
            <el-select
              v-model="form.new_accessories_id"
              filterable
              remote
              :remote-method="loadNewCandidates"
              :loading="newLoading"
              placeholder="默认仓 + 工程师仓"
              style="width:100%"
              @change="(v:string) => onNewAccSelect(form, v)"
            >
              <el-option
                v-for="opt in newCandidates"
                :key="opt.eid as string"
                :label="(opt.eid as string) + ' / ' + (opt.itemcd as string) + (opt.source==='engineer'?' [工程师仓]':' [默认仓]')"
                :value="opt.eid as string"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="配件编码">
            <el-input
              v-model="form.itemcd"
              placeholder="配件编码（前两位过滤故障现象）"
              @change="() => onItemcdChange(form)"
            />
          </el-form-item>
          <el-form-item label="故障代码">
            <FaultCodeCascader
              :model-value="(form.fault_cd as string) || ''"
              :fault-type="(form.itemcd as string || '').slice(0, 2)"
              :store-id="(form.store_id as string) || ''"
              placeholder="按配件类型自动过滤"
              @update:model-value="(v:string) => form.fault_cd = v"
            />
          </el-form-item>
          <el-form-item label="配件类型">
            <el-input v-model="form.accessories_type" />
          </el-form-item>
          <el-form-item label="配件价格">
            <el-input
              v-model="form.price"
              type="number"
            />
          </el-form-item>
          <el-form-item label="收款金额">
            <el-input
              v-model="form.payje"
              type="number"
              placeholder="与配件价格同步"
            />
          </el-form-item>
          <el-form-item label="是否入库">
            <el-select v-model="form.in_wh" style="width:100%">
              <el-option label="是" value="1" />
              <el-option label="否" value="0" />
            </el-select>
          </el-form-item>
        </template>

        <!-- c_type=5 耗材/线材：配件类型（填名称）+金额 -->
        <template v-else-if="form.c_type === '5'">
          <el-form-item label="耗材/线材">
            <el-select
              v-model="form.paytype"
              style="width:100%"
              placeholder="选择耗材/线材"
              filterable
              allow-create
            >
              <el-option
                v-for="opt in payConsOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="名称">
            <el-input
              v-model="form.accessories_type"
              placeholder="耗材/线材名称"
            />
          </el-form-item>
          <el-form-item label="收款金额">
            <el-input
              v-model="form.payje"
              type="number"
            />
          </el-form-item>
          <el-form-item label="收款日期">
            <el-date-picker
              v-model="form.paydate"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="选择收款日期"
              style="width:100%"
            />
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="form.memo"
              type="textarea"
            />
          </el-form-item>
        </template>

        <!-- 公共：描述 -->
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
          />
        </el-form-item>
      </template>
    </ItsmSubTablePane>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import ItsmSubTablePane from './ItsmSubTablePane.vue'
import FaultCodeCascader from './FaultCodeCascader.vue'
import { fetchAccessories, createAccessories, updateAccessories, fetchNewAccessoriesCandidates, fetchOldAccessoriesCandidates, resolveEntitlement, fetchItemPrice } from '@/api/itsm'
import type { SubRecord } from '@/api/itsm'
import { useDict } from '@/composables/useDict'

const props = defineProps<{
  maintenanceId: string
  currentStatus?: string
  storeId?: string
  engineerId?: string
}>()

const isClosed = computed(() => ['3', '5', '9'].includes(props.currentStatus || ''))

// C_TYPE 字典：1维修/2购买/3纯服务费/4整机更换/5耗材线材
const { dictOptions: cTypeOptions, dictLabel: cTypeDictLabel } = useDict('C_TYPE')
// PAY_SVC：纯服务费收费类型（c_type=3）
const { dictOptions: paySvcOptions, dictLabel: paySvcLabel } = useDict('PAY_SVC')
// PAY_CONS：耗材/线材收费类型（c_type=5）
const { dictOptions: payConsOptions, dictLabel: payConsLabel } = useDict('PAY_CONS')

function cTypeLabel(v: string): string { return cTypeDictLabel(v) }
function cTypeTag(v: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  return ({
    '1': 'primary', '2': 'success', '3': 'warning', '4': 'danger', '5': 'info',
  } as const)[v as '1' | '2' | '3' | '4' | '5'] || 'info'
}

/** 收费类型翻译：按 c_type 级联 PAY_SVC/PAY_CONS */
function paytypeLabel(row: Record<string, unknown>): string {
  const ct = (row.c_type as string) || ''
  const pt = (row.paytype as string) || ''
  if (!pt) return '-'
  if (ct === '3') return paySvcLabel(pt)
  if (ct === '5') return payConsLabel(pt)
  return pt
}

// 顶部筛选
const filterCType = ref('')
/** fetchFn 包装：按 c_type 筛选本地列表 */
async function fetchFn(mid: string): Promise<{ data?: SubRecord[] }> {
  const r = await fetchAccessories(mid)
  if (!filterCType.value) return r
  const items = (r?.data || []).filter(it => (it.c_type as string) === filterCType.value)
  return { data: items }
}

// C4：新配件候选（默认仓 + 工程师虚拟仓双来源）
const newCandidates = ref<SubRecord[]>([])
const newLoading = ref(false)
async function loadNewCandidates(query: string) {
  newLoading.value = true
  try {
    const r = await fetchNewAccessoriesCandidates({
      engineer_id: props.engineerId || '',
      accessories_type: query || undefined,
    })
    newCandidates.value = r?.data || []
  } finally {
    newLoading.value = false
  }
}
/** 新配件选中后联动 itemcd + 带出价格 */
function onNewAccSelect(form: Record<string, unknown>, eid: string) {
  const opt = newCandidates.value.find(o => (o.eid as string) === eid)
  if (opt) {
    form.itemcd = opt.itemcd
    form.accessories_type = opt.itemcd // 兼容显示
    // C9：带出价格
    fetchItemPriceForForm(form, opt.itemcd as string)
  }
}

/** C9：按 itemcd 带出价格（销售价），同步 payje（c_type=1/2/4） */
async function fetchItemPriceForForm(form: Record<string, unknown>, itemcd: string) {
  if (!itemcd || !props.storeId) return
  try {
    const r = await fetchItemPrice(props.storeId, itemcd)
    const price = r?.data?.price
    if (price != null) {
      form.price = price
      const ct = (form.c_type as string) || ''
      if (['1', '2', '4'].includes(ct)) {
        form.payje = price
      }
    }
  } catch {
    // 静默失败
  }
}

/** 手动输入/修改 itemcd 时带出价格 */
function onItemcdChange(form: Record<string, unknown>) {
  const itemcd = (form.itemcd as string) || ''
  if (itemcd) {
    fetchItemPriceForForm(form, itemcd)
  }
}

// C4：旧配件候选（门店有效资产）
const oldCandidates = ref<SubRecord[]>([])
const oldLoading = ref(false)
async function loadOldCandidates(_query: string) {
  if (!props.storeId) {
    oldCandidates.value = []
    return
  }
  oldLoading.value = true
  try {
    const r = await fetchOldAccessoriesCandidates({ store_id: props.storeId })
    oldCandidates.value = r?.data || []
  } finally {
    oldLoading.value = false
  }
}

// 1a C8：c_type 推荐规则（按资产属性+权益自动推荐，用户可覆盖）
const entitlementLoading = ref(false)
const entitlementInfo = ref<{ free: boolean; reason: string } | null>(null)

/** 按 device_id + store_id 查询权益+推荐 c_type */
async function recommendCType(form: Record<string, unknown>) {
  const eid = (form.device_id as string) || ''
  if (!eid) {
    entitlementInfo.value = null
    return
  }
  entitlementLoading.value = true
  try {
    const r = await resolveEntitlement(eid, props.storeId)
    const data = r?.data
    if (data) {
      entitlementInfo.value = data.entitlement
      // 仅当用户未手动选择 c_type 时自动推荐
      if (!form.c_type) {
        form.c_type = data.recommended_c_type
      }
    }
  } catch {
    // 静默失败，不影响表单
    entitlementInfo.value = null
  } finally {
    entitlementLoading.value = false
  }
}

/** 表单打开时触发推荐（由 ItsmSubTablePane 的 form 初始化调用） */
function onFormInit(form: Record<string, unknown>) {
  if (form.device_id && !form.c_type) {
    recommendCType(form)
  }
}
defineExpose({ onFormInit, recommendCType })
</script>

<style scoped>
.material-charge-pane { width: 100%; }
.mc-filter { margin-bottom: 8px; display: flex; justify-content: flex-end; }
</style>
