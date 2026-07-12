<template>
  <div style="margin-top:16px">
    <el-divider content-position="left">业务附表</el-divider>
    <el-tabs v-model="activeTab" type="card" size="small">
      <el-tab-pane label="上门服务" name="d2d">
        <div style="text-align:right;margin-bottom:8px">
          <el-button size="small" type="primary" @click="openForm('d2d')">新增上门</el-button>
        </div>
        <el-table :data="d2dList" size="small" empty-text="暂无">
          <el-table-column label="类型" width="80"><template #default="{row}">{{ d2dTypeLabel(row.d2d_type as string) }}</template></el-table-column>
          <el-table-column prop="d2d_engineer" label="工程师" width="80"/>
          <el-table-column prop="d2d_phone" label="电话" width="100" show-overflow-tooltip/>
          <el-table-column label="到达" width="120"><template #default="{row}">{{ row.arrive_time||'-' }}</template></el-table-column>
          <el-table-column label="离开" width="120"><template #default="{row}">{{ row.leave_time||'-' }}</template></el-table-column>
          <el-table-column label="解决" width="70"><template #default="{row}"><el-tag size="small" :type="row.jjbz==='1'?'success':'info'">{{ row.jjbz==='1'?'是':'否' }}</el-tag></template></el-table-column>
          <el-table-column prop="d2d_descripiton" label="描述" min-width="120" show-overflow-tooltip/>
          <el-table-column prop="create_time" label="创建时间" width="120"/>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="回访" name="rv">
        <div style="text-align:right;margin-bottom:8px">
          <el-button size="small" type="primary" @click="openForm('rv')">新增回访</el-button>
        </div>
        <el-table :data="rvList" size="small" empty-text="暂无">
          <el-table-column prop="rv_operator" label="回访人" width="80"/>
          <el-table-column prop="rv_time" label="回访时间" width="120"/>
          <el-table-column prop="satisfaction" label="满意度" width="70"/>
          <el-table-column prop="feedback" label="反馈" min-width="120" show-overflow-tooltip/>
          <el-table-column prop="create_time" label="创建时间" width="120"/>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="配件更新" name="acc">
        <div style="text-align:right;margin-bottom:8px">
          <el-button size="small" type="primary" @click="openForm('acc')">新增配件</el-button>
        </div>
        <el-table :data="accList" size="small" empty-text="暂无">
          <el-table-column prop="store_id" label="门店" width="100"/>
          <el-table-column prop="device_id" label="整机" width="130" show-overflow-tooltip/>
          <el-table-column prop="old_accessories_id" label="旧配件" width="120" show-overflow-tooltip/>
          <el-table-column prop="new_accessories_id" label="新配件" width="120" show-overflow-tooltip/>
          <el-table-column prop="accessories_type" label="配件类型" width="120" show-overflow-tooltip/>
          <el-table-column label="操作" width="80"><template #default="{row}">{{ cTypeLabel(row.c_type as string) }}</template></el-table-column>
          <el-table-column prop="price" label="价格" width="80" align="right"/>
          <el-table-column prop="engineer_id" label="工程师" width="80"/>
          <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip/>
          <el-table-column prop="create_time" label="创建时间" width="120"/>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="收费" name="pay">
        <div style="text-align:right;margin-bottom:8px">
          <el-button size="small" type="primary" @click="openForm('pay')">新增收费</el-button>
        </div>
        <el-table :data="payList" size="small" empty-text="暂无">
          <el-table-column prop="store_id" label="门店" width="100"/>
          <el-table-column prop="engineer_id" label="工程师" width="80"/>
          <el-table-column prop="paytype" label="收费类型" width="100" show-overflow-tooltip/>
          <el-table-column prop="payje" label="金额" width="80" align="right"/>
          <el-table-column prop="paydate" label="收款日期" width="120"/>
          <el-table-column prop="receipt_id" label="收据号" width="90"/>
          <el-table-column prop="delivery_id" label="送货单" width="90"/>
          <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
          <el-table-column prop="create_time" label="创建时间" width="120"/>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="派工" name="dispatch">
        <div style="text-align:right;margin-bottom:8px">
          <el-button size="small" type="primary" @click="openForm('dispatch')">新增派工</el-button>
        </div>
        <el-table :data="dispList" size="small" empty-text="暂无">
          <el-table-column prop="maintenance_type" label="维护类型" width="90"/>
          <el-table-column prop="operator" label="操作人" width="80"/>
          <el-table-column prop="accpectd_group" label="分派组" width="80"/>
          <el-table-column prop="accpectder" label="分派人" width="80"/>
          <el-table-column prop="dispatch_time" label="派工时间" width="120"/>
          <el-table-column prop="create_time" label="创建" width="120"/>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="关单记录" name="close">
        <div style="text-align:right;margin-bottom:8px">
          <el-button size="small" type="primary" @click="openForm('close')">新增关单</el-button>
        </div>
        <el-table :data="closeList" size="small" empty-text="暂无">
          <el-table-column prop="close_time" label="关单时间" width="120"/>
          <el-table-column prop="close_type" label="类型" width="80"/>
          <el-table-column label="补关单" width="80"><template #default="{row}">{{ row.is_old==='Y'?'是':'否' }}</template></el-table-column>
          <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip/>
          <el-table-column prop="create_time" label="创建" width="120"/>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="dialogVisible" :title="formTitle" width="650px">
      <el-form :model="form" label-width="90px" size="small">
        <template v-if="formType==='d2d'">
          <el-form-item label="类型"><el-select v-model="form.d2d_type" style="width:100%"><el-option label="到店" value="1"/><el-option label="离店" value="2"/><el-option label="催单" value="3"/><el-option label="记录" value="4"/></el-select></el-form-item>
          <el-form-item label="工程师"><el-input v-model="form.d2d_engineer"/></el-form-item>
          <el-form-item label="电话"><el-input v-model="form.d2d_phone"/></el-form-item>
          <el-form-item label="到达时间"><el-date-picker v-model="form.arrive_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择到达时间" style="width:100%"/></el-form-item>
          <el-form-item label="离开时间"><el-date-picker v-model="form.leave_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择离开时间" style="width:100%"/></el-form-item>
          <el-form-item label="是否解决"><el-select v-model="form.jjbz" style="width:100%"><el-option label="是" value="1"/><el-option label="否" value="0"/></el-select></el-form-item>
          <el-form-item label="描述"><el-input v-model="form.d2d_descripiton" type="textarea"/></el-form-item>
        </template>
        <template v-if="formType==='rv'">
          <el-form-item label="回访人"><el-input v-model="form.rv_operator"/></el-form-item>
          <el-form-item label="回访时间"><el-date-picker v-model="form.rv_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择回访时间" style="width:100%"/></el-form-item>
          <el-form-item label="满意度"><el-input v-model="form.satisfaction"/></el-form-item>
          <el-form-item label="反馈"><el-input v-model="form.feedback" type="textarea"/></el-form-item>
        </template>
        <template v-if="formType==='acc'">
          <el-form-item label="门店"><el-input v-model="form.store_id"/></el-form-item>
          <el-form-item label="整机"><el-input v-model="form.device_id"/></el-form-item>
          <el-form-item label="旧配件"><el-input v-model="form.old_accessories_id"/></el-form-item>
          <el-form-item label="新配件"><el-input v-model="form.new_accessories_id"/></el-form-item>
          <el-form-item label="配件类型"><el-input v-model="form.accessories_type"/></el-form-item>
          <el-form-item label="操作"><el-select v-model="form.c_type" style="width:100%"><el-option label="维修" value="1"/><el-option label="购买" value="2"/></el-select></el-form-item>
          <el-form-item label="价格"><el-input v-model="form.price" type="number"/></el-form-item>
          <el-form-item label="工程师"><el-input v-model="form.engineer_id"/></el-form-item>
          <el-form-item label="描述"><el-input v-model="form.description" type="textarea"/></el-form-item>
        </template>
        <template v-if="formType==='pay'">
          <el-form-item label="门店"><el-input v-model="form.store_id"/></el-form-item>
          <el-form-item label="工程师"><el-input v-model="form.engineer_id"/></el-form-item>
          <el-form-item label="收费类型"><el-input v-model="form.paytype"/></el-form-item>
          <el-form-item label="金额"><el-input v-model="form.payje" type="number"/></el-form-item>
          <el-form-item label="收款日期"><el-date-picker v-model="form.paydate" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择收款日期" style="width:100%"/></el-form-item>
          <el-form-item label="收据号"><el-input v-model="form.receipt_id"/></el-form-item>
          <el-form-item label="送货单"><el-input v-model="form.delivery_id"/></el-form-item>
          <el-form-item label="备注"><el-input v-model="form.memo" type="textarea"/></el-form-item>
        </template>
        <template v-if="formType==='dispatch'">
          <el-form-item label="维护类型"><el-input v-model="form.maintenance_type"/></el-form-item>
          <el-form-item label="操作人"><el-input v-model="form.operator"/></el-form-item>
          <el-form-item label="分派组"><el-input v-model="form.accpectd_group"/></el-form-item>
          <el-form-item label="分派人"><el-input v-model="form.accpectder"/></el-form-item>
          <el-form-item label="派工时间"><el-date-picker v-model="form.dispatch_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择派工时间" style="width:100%"/></el-form-item>
        </template>
        <template v-if="formType==='close'">
          <el-form-item label="关单时间"><el-date-picker v-model="form.close_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择关单时间" style="width:100%"/></el-form-item>
          <el-form-item label="关单类型"><el-input v-model="form.close_type"/></el-form-item>
          <el-form-item label="是否补关"><el-select v-model="form.is_old" style="width:100%"><el-option label="是" value="Y"/><el-option label="否" value="N"/></el-select></el-form-item>
          <el-form-item label="描述"><el-input v-model="form.description" type="textarea"/></el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button size="small" @click="dialogVisible=false">取消</el-button>
        <el-button size="small" type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { fetchD2D, fetchRV, fetchAccessories, fetchPayList, fetchDispatch, fetchCloseBills, createD2D, createRV, createAccessories, createPayList, createDispatch, createCloseBill } from '@/api/itsm'
import type { SubRecord } from '@/api/itsm'
import { ElMessage } from 'element-plus'

const props = defineProps<{ maintenanceId: string }>()
const activeTab = ref('d2d')
const d2dList = ref<SubRecord[]>([])
const rvList = ref<SubRecord[]>([])
const accList = ref<SubRecord[]>([])
const payList = ref<SubRecord[]>([])
const dispList = ref<SubRecord[]>([])
const closeList = ref<SubRecord[]>([])

const dialogVisible = ref(false)
const formType = ref<string>('')
const form = ref<Record<string, unknown>>({})

const formTitle = computed(() => {
  const map: Record<string, string> = { d2d: '新增上门', rv: '新增回访', acc: '新增配件', pay: '新增收费', dispatch: '新增派工', close: '新增关单' }
  return map[formType.value] || '新增'
})

const d2dTypeMap: Record<string, string> = { '1': '到店', '2': '离店', '3': '催单', '4': '记录' }
const cTypeMap: Record<string, string> = { '1': '维修', '2': '购买' }
function d2dTypeLabel(v: string) { return d2dTypeMap[v] || v || '-' }
function cTypeLabel(v: string) { return cTypeMap[v] || v || '-' }

function openForm(type: string) {
  formType.value = type
  form.value = { maintenance_id: props.maintenanceId }
  dialogVisible.value = true
}

function cleanData(data: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(data)) {
    if (v === '') continue
    if (['price', 'payje'].includes(k) && v !== undefined && v !== null) {
      const n = Number(v)
      out[k] = Number.isNaN(n) ? v : n
    } else {
      out[k] = v
    }
  }
  return out
}

async function submitForm() {
  if (!props.maintenanceId) return
  const data = cleanData({ ...form.value, maintenance_id: props.maintenanceId })
  try {
    if (formType.value === 'd2d') await createD2D(data)
    else if (formType.value === 'rv') await createRV(data)
    else if (formType.value === 'acc') await createAccessories(data)
    else if (formType.value === 'pay') await createPayList(data)
    else if (formType.value === 'dispatch') await createDispatch(data)
    else if (formType.value === 'close') await createCloseBill(data)
    ElMessage.success('新增成功')
    dialogVisible.value = false
    await loadAll()
  } catch {
    ElMessage.error('新增失败')
  }
}

async function loadAll() {
  if (!props.maintenanceId) return
  const mid = props.maintenanceId
  try { const r = await fetchD2D(mid); d2dList.value = (r as any)?.data || [] } catch { d2dList.value = [] }
  try { const r = await fetchRV(mid); rvList.value = (r as any)?.data || [] } catch { rvList.value = [] }
  try { const r = await fetchAccessories(mid); accList.value = (r as any)?.data || [] } catch { accList.value = [] }
  try { const r = await fetchPayList(mid); payList.value = (r as any)?.data || [] } catch { payList.value = [] }
  try { const r = await fetchDispatch(mid); dispList.value = (r as any)?.data || [] } catch { dispList.value = [] }
  try { const r = await fetchCloseBills(mid); closeList.value = (r as any)?.data || [] } catch { closeList.value = [] }
}

watch(() => props.maintenanceId, loadAll, { immediate: true })
</script>
