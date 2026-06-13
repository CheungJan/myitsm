<template>
  <div class="page">
    <div class="page-header">
      <h2>生产工单</h2>
      <el-button type="primary" size="small" @click="openCreate">新建</el-button>
    </div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>状态</label>
          <el-select v-model="filterStatus" size="small" style="width:140px" clearable @change="doSearch">
            <el-option v-for="s in allStatuses" :key="s.value" :label="s.label" :value="s.value"/>
          </el-select>
        </div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDetail">
        <el-table-column prop="wo_id" label="工单编号" width="120"/>
        <el-table-column prop="item_cd" label="产品编码" width="100"/>
<el-table-column label="产品名称" min-width="160"><template #default="{row}">{{ (row as any).item_nm || '-' }}</template></el-table-column>
        <el-table-column label="类型" width="70">
          <template #default="{row}">{{ (row as any).wo_type === 'RENOVATION' ? '翻新' : '生产' }}</template>
        </el-table-column>
        <el-table-column prop="plan_qty" label="计划数" width="75" align="right"/>
        <el-table-column prop="actual_qty" label="完成数" width="75" align="right"/>
        <el-table-column label="状态" width="90">
          <template #default="{row}">
            <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标仓库" width="90"><template #default="{row}">{{ whnm(row.warehouse_cd) }}</template></el-table-column>
        <el-table-column label="计划开始" width="100">
          <template #default="{row}">{{ row.plan_start || '-' }}</template>
        </el-table-column>
        <el-table-column label="计划完成" width="100">
          <template #default="{row}">{{ row.plan_end || '-' }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="140">
          <template #default="{row}">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{row}">
            <template v-for="btn in nextButtons(row.status)" :key="btn.target">
              <el-button :type="btn.type as any" link size="small"
                @click.stop="handleTransition(row, btn.target)"
                :loading="transitioning === row.wo_id + btn.target">{{ btn.label }}</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <!-- 新建工单弹窗 -->
    <el-dialog v-model="creating" title="新建生产工单" width="450px" @closed="resetCreateForm">
      <el-form label-width="80px" size="small">
        <el-form-item label="产品编码" required>
          <el-tree-select v-model="createForm.item_cd" :data="bomTreeData" :props="{label:'class_nm',value:'class_cd',children:'children',disabled:isBomNodeDisabled}" node-key="class_cd" filterable clearable check-strictly size="small" style="width:100%" placeholder="选择产品（按BOM分类浏览或搜索）" :filter-node-method="filterBomNode"/>
        </el-form-item>
        <el-form-item label="计划数量" required>
          <el-input-number v-model="createForm.plan_qty" :min="1" :max="99999" style="width:100%"/>
        </el-form-item>
        <el-form-item label="工单类型" required>
          <el-radio-group v-model="createForm.wo_type">
            <el-radio value="PRODUCTION">新机生产</el-radio>
            <el-radio value="RENOVATION">旧机翻新</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="领料仓库">
          <el-select v-model="createForm.pick_whcd" filterable style="width:100%" placeholder="BOM子件出库仓库">
            <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="成品仓库">
          <el-select v-model="createForm.warehouse_cd" filterable style="width:100%" placeholder="成品入库仓库">
            <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="计划开始">
          <el-date-picker v-model="createForm.plan_start" type="date" value-format="YYYY-MM-DD" style="width:100%"/>
        </el-form-item>
        <el-form-item label="计划完成">
          <el-date-picker v-model="createForm.plan_end" type="date" value-format="YYYY-MM-DD" style="width:100%"/>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.remark"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="creating = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="createSaving">创建</el-button>
      </template>
    </el-dialog>

    <!-- 工单详情抽屉 -->
    <el-drawer v-model="drawer" title="工单详情" size="520px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small" :label-style="{width:'100px'}">
          <el-descriptions-item label="工单编号">{{ detail.wo_id }}</el-descriptions-item>
          <el-descriptions-item label="产品" :span="2">{{ detail.item_cd||'-' }}{{ (detail as any).item_nm ? ' — '+(detail as any).item_nm : '' }}</el-descriptions-item>
          <el-descriptions-item label="计划数量">{{ detail.plan_qty||0 }}</el-descriptions-item>
          <el-descriptions-item label="实际完成">{{ detail.actual_qty||0 }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detail.status as string)" size="small">{{ statusLabel(detail.status as string) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="领料仓库">{{ whnm(detail.pick_whcd as string)||'-' }}</el-descriptions-item>
          <el-descriptions-item label="成品仓库">{{ whnm(detail.warehouse_cd as string)||'-' }}</el-descriptions-item>
          <el-descriptions-item label="实际开始">{{ detail.actual_start||'-' }}</el-descriptions-item>
          <el-descriptions-item label="实际完成">{{ detail.actual_end||'-' }}</el-descriptions-item>
          <el-descriptions-item label="计划开始">{{ detail.plan_start||'-' }}</el-descriptions-item>
          <el-descriptions-item label="计划完成">{{ detail.plan_end||'-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(detail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.remark||'-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 状态流转操作 -->
        <div v-if="nextButtons(detail.status as string).length > 0"
             style="margin-top:16px;display:flex;gap:8px;align-items:center">
          <span style="font-size:13px;color:#606266">操作：</span>
          <template v-for="btn in nextButtons(detail.status as string)" :key="btn.target">
            <el-button :type="btn.type as any" size="small"
              @click="handleTransition(detail as WoRecord, btn.target)"
              :loading="transitioning === (detail as WoRecord).wo_id + btn.target">{{ btn.label }}</el-button>
          </template>
        </div>

        <!-- BOM 物料清单 -->
        <template v-if="detailBom.length > 0">
          <el-divider style="margin:16px 0 12px"/>
          <h4 style="font-size:13px;color:#303133;margin:0 0 8px">BOM 物料清单 (×{{ detail.plan_qty || 1 }})</h4>
          <el-table :data="detailBom" size="small" stripe>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column label="单件用量" width="80" align="right"><template #default="{row}">{{ row.bomqty }}</template></el-table-column>
            <el-table-column label="需求总量" width="80" align="right"><template #default="{row}">{{ (row.bomqty||1) * (detail.plan_qty||1) }}</template></el-table-column>
          </el-table>
        </template>

        <!-- 物料消耗 -->
        <template v-if="detailMaterials.length > 0">
          <el-divider style="margin:16px 0 12px"/>
          <h4 style="font-size:13px;color:#303133;margin:0 0 8px">物料消耗（TMS04）</h4>
          <el-table :data="detailMaterials" size="small" stripe>
            <el-table-column prop="item_cd" label="物料" width="100"/>
            <el-table-column prop="actual_qty" label="实耗" width="70" align="right"/>
            <el-table-column prop="plan_qty" label="计划" width="70" align="right"/>
            <el-table-column prop="warehouse_cd" label="仓库" width="80"/>
            <el-table-column prop="consume_date" label="日期" width="100"/>
          </el-table>
        </template>

        <!-- 物料更换 -->
        <template v-if="detail.status==='QC_PENDING'||detail.status==='IN_PROGRESS'">
          <el-divider style="margin:16px 0 12px"/>
          <div style="display:flex;align-items:center;gap:8px">
            <h4 style="font-size:13px;color:#303133;margin:0">物料更换</h4>
            <el-button size="small" type="primary" @click="openReplaceDialog">更换</el-button>
          </div>

          <!-- FQC不良品待更换 -->
          <div v-if="fqcDefectiveItems.length > 0" style="margin-top:12px">
            <div style="font-size:12px;color:#606266;margin-bottom:8px">FQC不良品待更换（点击可快速填充）</div>
            <div v-for="item in fqcDefectiveItems" :key="item.eid"
              style="display:flex;align-items:center;gap:8px;padding:6px 8px;background:#fef0f0;border:1px solid #fbc4c4;border-radius:4px;margin-bottom:4px">
              <span style="font-size:12px;color:#303133">{{ item.itemcd }}</span>
              <span style="font-size:12px;color:#909399">|</span>
              <span style="font-size:12px;color:#303133">{{ item.eid }}</span>
              <el-tag size="small" :type="item.judgment === 'BF' ? 'danger' : item.judgment === 'BH' ? 'warning' : 'info'">{{ item.judgment }}</el-tag>
              <el-button size="small" link type="primary" @click="quickReplace(item)">快速更换</el-button>
            </div>
          </div>

          <!-- 更换历史 -->
          <div v-if="replaceHistory.length > 0" style="margin-top:12px">
            <div style="font-size:12px;color:#606266;margin-bottom:8px">更换历史</div>
            <div v-for="rec in replaceHistory" :key="rec.replace_date"
              style="padding:6px 8px;background:#f5f7fa;border-radius:4px;margin-bottom:4px;font-size:12px">
              <div style="color:#909399">{{ rec.replace_date }}</div>
              <div style="color:#303133;margin-top:2px">
                {{ rec.itemcd || '-' }} | 
                <span v-if="rec.old_eid">{{ rec.old_eid }}</span>
                <span v-else-if="rec.old_batch_no">批次:{{ rec.old_batch_no }}</span>
                <span v-else>-</span>
                → 
                <span v-if="rec.new_eid">{{ rec.new_eid }}</span>
                <span v-else-if="rec.new_batch_no">批次:{{ rec.new_batch_no }}</span>
                <span v-else>-</span>
                | {{ rec.operator_name }}
              </div>
              <div v-if="rec.memo" style="color:#606266;margin-top:2px">{{ rec.memo }}</div>
            </div>
          </div>
        </template>

        <!-- 更换对话框 -->
        <el-dialog v-model="replaceDialogVisible" title="物料更换" width="480px">
          <el-form :model="replaceForm" label-width="90px" size="small">
            <el-form-item label="物料类型">
              <el-radio-group v-model="replaceForm.materialType" @change="onMaterialTypeChange">
                <el-radio value="eid">EID类型</el-radio>
                <el-radio value="batch">批次类型</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="replaceForm.materialType === 'eid'" label="旧物料EID"><el-input v-model="replaceForm.old_eid" placeholder="被更换的EID"/></el-form-item>
            <el-form-item v-if="replaceForm.materialType === 'batch'" label="旧批次号"><el-input v-model="replaceForm.old_batch_no" placeholder="被更换的批次号"/></el-form-item>
            <el-form-item v-if="replaceForm.materialType === 'eid'" label="新物料EID"><el-input v-model="replaceForm.new_eid" placeholder="更换后的EID"/></el-form-item>
            <el-form-item v-if="replaceForm.materialType === 'batch'" label="新批次号"><el-input v-model="replaceForm.new_batch_no" placeholder="更换后的批次号"/></el-form-item>
            <el-form-item label="物料编码"><el-input v-model="replaceForm.itemcd" placeholder="必填"/></el-form-item>
            <el-form-item label="备注"><el-input v-model="replaceForm.memo" type="textarea" :rows="2" placeholder="更换原因"/></el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="replaceDialogVisible=false">取消</el-button>
            <el-button type="primary" :loading="replaceSaving" @click="doReplace">确认更换</el-button>
          </template>
        </el-dialog>

        <!-- FQC 结果 -->
        <template v-if="detail.fqc_qcstatus">
          <h4 style="font-size:13px;color:#303133;margin:12px 0 8px">FQC 结果 — {{ (qcMap as any)[(detail as any).fqc_qcstatus]||(detail as any).fqc_qcstatus }}</h4>
          <div v-for="(item, idx) in ((detail as any).fqc_products||[])" :key="idx"
            style="display:flex;gap:12px;align-items:flex-start;padding:4px 8px;background:#f5f7fa;border-radius:4px;margin-bottom:4px">
            <div style="min-width:120px">
              <el-tag size="small" type="success">{{ (item as any).product || '配件' }}</el-tag>
            </div>
            <div style="flex:1;display:flex;flex-wrap:wrap;gap:4px">
              <el-tag v-for="eid in (item as any).parts" :key="eid" size="small" type="info">{{ eid }}</el-tag>
            </div>
          </div>
        </template>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { fetchWorkOrders, createWorkOrder, transitionWorkOrder, deleteWorkOrder, fetchMaterialConsumes, replaceWorkOrderAsset, fetchReplaceRecords } from '@/api/mes'
import request from '@/api/request'
import { fetchWarehouses, fetchBomClassTree, fetchBom, type ItemClassNode } from '@/api/master'
import { useDict } from '@/composables/useDict'
import type { MesRecord } from '@/api/mes'

interface WoRecord { wo_id: string; item_cd?: string; plan_qty?: number; status?: string; [key:string]: unknown }

const { items, loading, page, perPage, total, onSearch, load } = useListPage<MesRecord>(fetchWorkOrders)
const filterStatus = ref('')
const { dictMap: qcMap } = useDict('QC')
const drawer = ref(false)
const detail = ref<WoRecord | null>(null)
const detailMaterials = ref<any[]>([])
const detailBom = ref<any[]>([])
const detailBomNm = ref('')
const transitioning = ref('')

const allStatuses = [
    { value: 'DRAFT', label: '草稿' },
    { value: 'RELEASED', label: '已下达' },
    { value: 'PICKING', label: '领料中' },
    { value: 'IN_PROGRESS', label: '生产中' },
    { value: 'QC_PENDING', label: '待最终检' },
    { value: 'COMPLETED', label: '已完工' },
    { value: 'CANCELLED', label: '已取消' },
]

function statusTag(s: string) {
    const m: Record<string, string> = { DRAFT: 'info', RELEASED: 'primary', PICKING: 'warning', IN_PROGRESS: 'warning', QC_PENDING: 'primary', COMPLETED: 'success', CANCELLED: 'danger' }
    return m[s] || 'info'
}
function statusLabel(s: string) {
    const m: Record<string, string> = { DRAFT: '草稿', RELEASED: '已下达', PICKING: '领料中', IN_PROGRESS: '生产中', QC_PENDING: '待最终检', COMPLETED: '已完工', CANCELLED: '已取消' }
    return m[s] || s || 'DRAFT'
}
function nextButtons(status: string) {
    const map: Record<string, { target: string; label: string; type: string }[]> = {
        DRAFT: [
            { target: 'RELEASED', label: '下达', type: 'primary' },
            { target: 'DELETE', label: '删除', type: 'danger' },
        ],
        RELEASED: [
            { target: 'CANCELLED', label: '取消', type: 'danger' },
        ],
        PICKING: [
            { target: 'CANCELLED', label: '取消', type: 'danger' },
        ],
        IN_PROGRESS: [
            { target: 'QC_PENDING', label: '完工待检', type: 'success' },
            { target: 'CANCELLED', label: '取消', type: 'danger' },
        ],
        QC_PENDING: [
            { target: 'CANCELLED', label: '取消', type: 'danger' },
        ],
    }
    return map[status] || []
}

async function openDetail(row: WoRecord) {
    drawer.value = true
    // 从详情API获取完整数据（含FQC信息）
    try { const r = await request.get(`/mes/work-orders/${row.wo_id}`) as any; detail.value = r?.data || row } catch { detail.value = row }
    detailMaterials.value = []
    detailBom.value = []
    try { const r = await fetchMaterialConsumes(row.wo_id as string); detailMaterials.value = (r.data as any) || [] } catch { /* */ }
    // 加载 BOM
    if (row.item_cd) { try { const r = await fetchBom(row.item_cd as string); const bom = r.data as any; detailBom.value = bom?.details || []; detailBomNm.value = bom?.bomnm || '' } catch { detailBomNm.value = '' } }
    // 加载FQC不良品和更换历史
    await loadFqcDefectiveItems()
    await loadReplaceHistory()
}

async function handleTransition(row: WoRecord, target: string) {
    if (target === 'DELETE') {
        try { await ElMessageBox.confirm(`确认删除草稿工单 ${row.wo_id}？`, '确认删除', { type: 'warning' }) } catch { return }
        transitioning.value = (row.wo_id as string) + 'DELETE'
        try { await deleteWorkOrder(row.wo_id as string); ElMessage.success('已删除'); load(); if (detail.value?.wo_id === row.wo_id) detail.value = null }
        catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
        finally { transitioning.value = '' }
        return
    }
    const labels: Record<string, string> = { RELEASED: '下达', QC_PENDING: '完工待检', CANCELLED: '取消' }
    const msg = target === 'QC_PENDING'
        ? `确认完工？工单将进入待最终检状态，FQC通过后才会完工。`
        : `确认${labels[target] || target}工单 ${row.wo_id}？`
    try { await ElMessageBox.confirm(msg, '确认', { type: 'warning' }) } catch { return }
    transitioning.value = (row.wo_id as string) + target
    try {
        await transitionWorkOrder(row.wo_id as string, target)
        ElMessage.success(`工单已${labels[target] || target}`)
        load()
        if (detail.value?.wo_id === row.wo_id) detail.value = { ...detail.value, status: target }
    } catch (e: any) { ElMessage.error(e?.response?.data?.message || '操作失败') }
    finally { transitioning.value = '' }
}

// ---- 新建工单 ----
const creating = ref(false)
const createSaving = ref(false)
const createForm = reactive({ wo_type: 'PRODUCTION', item_cd: '', plan_qty: 1, warehouse_cd: '', pick_whcd: '', plan_start: new Date().toISOString().substring(0,10), plan_end: '', remark: '' })
const bomTreeData = ref<ItemClassNode[]>([])
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
function whnm(cd: string) { return whOptions.value.find(w => w.whcd === cd)?.whnm || cd }
onMounted(async () => {
    try { const r = await fetchWarehouses(); whOptions.value = r.data || [] } catch { /* */ }
    try { bomTreeData.value = (await fetchBomClassTree('1')).data || [] } catch { /* */ }
})

function isBomNodeDisabled(data: ItemClassNode) {
    return (data as any).type !== 'item'
}
function filterBomNode(value: string, data: ItemClassNode) {
    if (!value) return true
    return (data.class_nm || data.class_cd).toLowerCase().includes(value.toLowerCase())
}

function openCreate() { creating.value = true }
function resetCreateForm() {
    createForm.item_cd = ''; createForm.plan_qty = 1; createForm.warehouse_cd = ''; createForm.pick_whcd = ''
    createForm.plan_start = ''; createForm.plan_end = ''; createForm.remark = ''
}

async function handleCreate() {
    if (!createForm.item_cd) { ElMessage.warning('请选择产品编码'); return }
    if (!createForm.pick_whcd) { ElMessage.warning('请选择领料仓库'); return }
    if (createForm.plan_start) {
        const today = new Date().toISOString().substring(0, 10)
        if (createForm.plan_start < today) { ElMessage.warning('计划开始时间不能早于当天'); return }
    }
    if (createForm.plan_start && createForm.plan_end && createForm.plan_end < createForm.plan_start) {
        ElMessage.warning('计划完成时间不能早于计划开始时间'); return
    }
    createSaving.value = true
    try {
        await createWorkOrder({ ...createForm })
        ElMessage.success('工单创建成功')
        creating.value = false
        resetCreateForm()
        load()
    } catch (e: any) { ElMessage.error(e?.response?.data?.message || '创建失败') }
    finally { createSaving.value = false }
}

const replaceDialogVisible = ref(false)
const replaceSaving = ref(false)
const replaceForm = reactive({ old_eid: '', new_eid: '', itemcd: '', memo: '', materialType: 'eid', old_batch_no: '', new_batch_no: '' })
const fqcDefectiveItems = ref<Array<{ itemcd: string; item_nm: string; eid: string; judgment: string }>>([])
const replaceHistory = ref<Array<{ wo_id: string; old_eid: string; new_eid: string; itemcd: string; old_batch_no: string; new_batch_no: string; memo: string; replace_date: string; operator_cd: string; operator_name: string }>>([])

function openReplaceDialog() {
  replaceForm.old_eid = ''
  replaceForm.new_eid = ''
  replaceForm.itemcd = ''
  replaceForm.memo = ''
  replaceForm.materialType = 'eid'
  replaceForm.old_batch_no = ''
  replaceForm.new_batch_no = ''
  replaceDialogVisible.value = true
}

function onMaterialTypeChange() {
  // 切换物料类型时清空对应字段
  if (replaceForm.materialType === 'eid') {
    replaceForm.old_batch_no = ''
    replaceForm.new_batch_no = ''
  } else {
    replaceForm.old_eid = ''
    replaceForm.new_eid = ''
  }
}

function quickReplace(item: { itemcd: string; eid: string }) {
  replaceForm.old_eid = item.eid
  replaceForm.itemcd = item.itemcd
  replaceDialogVisible.value = true
}

async function doReplace() {
  if (!replaceForm.itemcd) {
    ElMessage.warning('请填写物料编码'); return
  }
  if (replaceForm.materialType === 'eid' && (!replaceForm.old_eid || !replaceForm.new_eid)) {
    ElMessage.warning('请填写旧EID和新EID'); return
  }
  if (replaceForm.materialType === 'batch' && (!replaceForm.old_batch_no || !replaceForm.new_batch_no)) {
    ElMessage.warning('请填写旧批次号和新批次号'); return
  }
  if (!detail.value?.wo_id) {
    ElMessage.error('工单信息无效'); return
  }
  replaceSaving.value = true
  try {
    const body: any = {
      itemcd: replaceForm.itemcd,
      memo: replaceForm.memo
    }
    if (replaceForm.materialType === 'eid') {
      body.old_eid = replaceForm.old_eid
      body.new_eid = replaceForm.new_eid
    } else {
      body.old_batch_no = replaceForm.old_batch_no
      body.new_batch_no = replaceForm.new_batch_no
    }
    await replaceWorkOrderAsset(detail.value.wo_id, body)
    ElMessage.success('更换记录已保存')
    replaceDialogVisible.value = false
    await loadReplaceHistory()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '更换失败') }
  finally { replaceSaving.value = false }
}

async function loadFqcDefectiveItems() {
  if (!detail.value?.wo_id) {
    fqcDefectiveItems.value = []
    return
  }
  try {
    const res = await request.get(`/qc/batches?refbillid=${detail.value.wo_id}&status=DRAFT`) as any
    const batches = res?.data?.items || []
    const defective: Array<{ itemcd: string; item_nm: string; eid: string; judgment: string }> = []
    for (const batch of batches) {
      const detailRes = await request.get(`/qc/batches/${batch.batch_id}/details`) as any
      const details = detailRes?.data || []
      details.forEach((d: any) => {
        if (['BF', 'BH', 'TH'].includes(d.judgment) && d.eid) {
          defective.push({ itemcd: d.itemcd, item_nm: d.item_nm, eid: d.eid, judgment: d.judgment })
        }
      })
    }
    fqcDefectiveItems.value = defective
  } catch { fqcDefectiveItems.value = [] }
}

async function loadReplaceHistory() {
  if (!detail.value?.wo_id) {
    replaceHistory.value = []
    return
  }
  try {
    const res = await fetchReplaceRecords(detail.value.wo_id) as any
    replaceHistory.value = res?.data || []
  } catch { replaceHistory.value = [] }
}

function formatDate(d: any) { if (!d) return '-'; const s = String(d); return s.replace('T', ' ').substring(0, 19) }
function doSearch() {
    const p: Record<string, string> = {}
    if (filterStatus.value) p.status = filterStatus.value
    onSearch(p)
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0 }
.search-bar { display: flex; gap: 12px; align-items: center }
.field { display: flex; align-items: center; gap: 6px }
.field label { font-size: 13px; color: #606266 }
</style>
