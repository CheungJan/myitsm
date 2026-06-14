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
            <el-tag v-if="(row as any).has_replenish" type="warning" size="small" style="margin-left:4px">补料中</el-tag>
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
          <el-table :data="detailMaterials" size="small" stripe :row-class-name="({row}: any) => row._sep ? 'consume-sep-row' : ''">
            <el-table-column prop="item_cd" label="物料" width="90"><template #default="{row}"><span v-if="row._sep" style="color:#1677ff;font-weight:600">{{ row._label }}</span><span v-else>{{ row.item_cd }}</span></template></el-table-column>
            <el-table-column label="类型" width="80"><template #default="{row}"><span v-if="!row._sep">{{ consumeTypeLabel(row.consume_type) }}</span></template></el-table-column>
            <el-table-column prop="actual_qty" label="实耗" width="60" align="right"><template #default="{row}"><span v-if="!row._sep">{{ row.actual_qty }}</span></template></el-table-column>
            <el-table-column prop="plan_qty" label="计划" width="60" align="right"><template #default="{row}"><span v-if="!row._sep">{{ row.plan_qty }}</span></template></el-table-column>
            <el-table-column label="仓库" width="70"><template #default="{row}"><span v-if="!row._sep">{{ whnm(row.warehouse_cd) }}</span></template></el-table-column>
            <el-table-column label="关联号" width="100"><template #default="{row}"><span v-if="!row._sep">{{ row.ref_bill_id || '-' }}</span></template></el-table-column>
            <el-table-column prop="consume_date" label="日期" width="90"><template #default="{row}"><span v-if="!row._sep">{{ row.consume_date }}</span></template></el-table-column>
          </el-table>
        </template>

        <!-- 物料更换 -->
        <template v-if="detail.status==='QC_PENDING'||detail.status==='IN_PROGRESS'||detail.status==='COMPLETED'">
          <el-divider style="margin:16px 0 12px"/>
          <div style="display:flex;align-items:center;gap:8px">
            <h4 style="font-size:13px;color:#303133;margin:0">物料更换</h4>
            <el-button v-if="detail.status!=='COMPLETED'" size="small" type="primary" @click="openReplaceDialog" :disabled="!fqcDefectiveItems.length">更换</el-button>
          </div>
          <div v-if="replenishItems.length" style="margin-top:8px;font-size:12px;color:#606266">
            补料单 {{ replenishOvBillid }}：<span v-for="(ri,i) in replenishItems" :key="ri.itemcd">{{ i>0?'、':'' }}{{ ri.itemcd }}×{{ ri.qty }}</span>，合计{{ replenishTotalQty }}件
          </div>
          <div v-if="fqcDefectiveItems.length" style="margin-top:8px">
            <div style="font-size:12px;color:#606266;margin-bottom:4px">FQC不良品明细</div>
            <div v-for="item in fqcDefectiveItems" :key="item._key" style="display:flex;align-items:center;gap:8px;padding:3px 8px;background:#fef0f0;border:1px solid #fbc4c4;border-radius:4px;margin-bottom:2px;font-size:12px">
              <span style="color:#606266">{{ item.label }}</span>
              <el-tag size="small" :type="item.judgment==='BF'?'danger':item.judgment==='BH'?'warning':'info'">{{ item.judgment }}</el-tag>
            </div>
          </div>
          <div v-if="replaceHistory.length" style="margin-top:12px">
            <div style="font-size:12px;color:#606266;margin-bottom:4px">更换历史</div>
            <template v-for="(rec, ri) in replaceHistory" :key="rec.id ?? ri">
              <el-divider v-if="ri>0 && rec.replace_date?.substring(0,10) !== replaceHistory[ri-1]?.replace_date?.substring(0,10)" style="margin:6px 0" content-position="left"><span style="font-size:11px;color:#909399">{{ rec.replace_date?.substring(0,10) }}</span></el-divider>
              <div style="padding:3px 8px;background:#f5f7fa;border-radius:4px;margin-bottom:2px;font-size:12px">
                <span style="color:#909399">{{ (rec.replace_date||'').substring(11,16) }}</span>
                {{ rec.old_eid||rec.old_batch_no||'-' }} → {{ rec.new_eid||rec.new_batch_no||'-' }} | {{ rec.operator_name }}
                <span v-if="rec.memo" style="color:#606266"> — {{ rec.memo }}</span>
              </div>
            </template>
          </div>
        </template>

        <!-- 更换对话框：逐行匹配旧→新，批量提交 -->
        <el-dialog v-model="replaceDialogVisible" title="物料更换" width="700px">
          <el-table :data="replaceRows" size="small" border>
            <el-table-column prop="itemcd" label="物料" width="90"/>
            <el-table-column label="旧(不良品)" min-width="180">
              <template #default="{row}"><el-select v-model="row._old" filterable clearable size="small" style="width:100%" placeholder="选择不良品EID/批次"><el-option v-for="d in fqcDefectiveItems.filter(d => d.itemcd === row.itemcd)" :key="d._key" :label="d.label" :value="d._key"/></el-select></template>
            </el-table-column>
            <el-table-column label="新(补料)" width="240">
              <template #default="{row}"><el-select v-model="row._new" filterable clearable size="small" style="width:100%" placeholder="选择补料批次"><el-option v-for="d in replenishDetails.filter(r => r.itemcd === row.itemcd)" :key="d._key" :label="d.eid ? `${d.itemcd} EID:${d.eid}` : `${d.itemcd} 批次${(d.prddate||'').substring(0,10)}`" :value="d._key"/></el-select></template>
            </el-table-column>
            <el-table-column label="备注" width="120">
              <template #default="{row}"><el-input v-model="row._memo" size="small" placeholder="原因"/></template>
            </el-table-column>
            <el-table-column width="50"><template #default="{$index}"><el-button size="small" link type="danger" @click="replaceRows.splice($index,1)">✕</el-button></template></el-table-column>
          </el-table>
          <div style="margin-top:8px;display:flex;gap:8px">
            <el-button size="small" @click="autoFillReplaceRows">自动填充不良品</el-button>
            <span style="font-size:12px;color:#909399;line-height:24px">共 {{ replaceRows.length }} 行</span>
          </div>
          <template #footer>
            <el-button @click="replaceDialogVisible=false">取消</el-button>
            <el-button type="primary" :loading="replaceSaving" @click="doBatchReplace">批量更换</el-button>
          </template>
        </el-dialog>

        <!-- FQC 结果 -->
        <template v-if="detail.fqc_qcstatus">
          <el-divider style="margin:16px 0 12px"/>
          <h4 style="font-size:13px;color:#303133;margin:0 0 8px">FQC 结果 — {{ (qcMap as any)[(detail as any).fqc_qcstatus]||(detail as any).fqc_qcstatus }}</h4>
          <div v-for="(item, idx) in ((detail as any).fqc_products||[])" :key="idx" style="margin-bottom:4px">
            <div v-if="item.product" style="display:flex;flex-wrap:wrap;gap:4px">
              <el-tag v-for="eid in item.product.split(', ')" :key="eid" size="small" type="success">{{ eid }}</el-tag>
            </div>
          </div>
        </template>

        <!-- 最终出入库单据 -->
        <template v-if="finalWhDocs.length">
          <el-divider style="margin:16px 0 12px"/>
          <h4 style="font-size:13px;color:#303133;margin:0 0 8px">最终出入库单据</h4>
          <div v-for="doc in finalWhDocs" :key="doc.billid" style="display:flex;gap:8px;align-items:center;padding:3px 8px;background:#f5f7fa;margin-bottom:2px;font-size:12px">
            <el-tag :type="doc.invtyp==='8'?'success':doc.invtyp==='7'?'danger':doc.invtyp==='9'?'warning':'info'" size="small">{{ doc.typeLabel }}</el-tag>
            <span style="font-family:monospace;color:#409eff">#{{ doc.index }}</span>
            <span style="font-family:monospace">{{ doc.billid }}</span>
            <span>{{ doc.items }}</span>
            <span style="margin-left:auto">{{ doc.memo||'' }}</span>
          </div>
        </template>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { fetchWorkOrders, createWorkOrder, transitionWorkOrder, deleteWorkOrder, fetchMaterialConsumes, replaceWorkOrderAsset, fetchReplaceRecords, fetchAvailableReplenish } from '@/api/mes'
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
    try { const r = await fetchMaterialConsumes(row.wo_id as string); const raw = ((r.data as any)||[]).filter((d:any) => !['3','4','5'].includes(d.consume_type)).sort((a:any,b:any) => (a.consume_type||0)-(b.consume_type||0)); const grouped: any[] = []; let lastType = ''; raw.forEach((d:any) => { if (d.consume_type !== lastType) { grouped.push({ _sep: true, _label: consumeTypeLabel(d.consume_type) }); lastType = d.consume_type } grouped.push(d) }); detailMaterials.value = grouped } catch { /* */ }
    // 加载 BOM
    if (row.item_cd) { try { const r = await fetchBom(row.item_cd as string); const bom = r.data as any; detailBom.value = bom?.details || []; detailBomNm.value = bom?.bomnm || '' } catch { detailBomNm.value = '' } }
    // 加载更换历史（补料信息依赖它判断是否用完）
    await loadReplaceHistory()
    await loadFqcDefectiveItems()
    await loadReplenishInfo()
    await loadFinalWhDocs()
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
const fqcDefectiveItems = ref<Array<{ itemcd: string; item_nm: string; eid: string; judgment: string; _key: string; label: string }>>([])
const replaceHistory = ref<Array<{ id?: number; wo_id: string; old_eid: string; new_eid: string; itemcd: string; old_batch_no: string; new_batch_no: string; memo: string; replace_date: string; operator_cd: string; operator_name: string }>>([])
const replenishItems = ref<Array<{ itemcd: string; qty: number; prddate?: string; itemtyp?: string }>>([])
const replenishDetails = ref<Array<{ itemcd: string; qty: number; prddate: string; itemtyp: string; _key: string; eid?: string }>>([])
const replenishOvBillid = ref('')
const replenishTotalQty = computed(() => replenishItems.value.reduce((s, i) => s + i.qty, 0))
const replacedKeys = ref(new Set<string>())
const finalWhDocs = ref<Array<{ billid: string; invtyp: string; typeLabel: string; items: string; memo: string; index: number }>>([])
const replaceRows = ref<Array<{ itemcd: string; _old: string; _new: string; _memo: string }>>([])

function openReplaceDialog() {
  replaceRows.value = []
  replaceDialogVisible.value = true
}
function autoFillReplaceRows() {
  const rows: typeof replaceRows.value = []
  const usedRp = new Set<string>()
  fqcDefectiveItems.value.forEach(d => {
    if (replacedKeys.value.has(d._key)) return  // 已更换，跳过
    const match = replenishDetails.value.find(r => r.itemcd === d.itemcd && !usedRp.has(r._key))
    if (match) {
      usedRp.add(match._key)
      rows.push({ itemcd: d.itemcd, _old: d._key, _new: match._key, _memo: '' })
    }
  })
  if (!rows.length) {
    if (replenishPendingBillids.value.length > 0) {
      ElMessage.warning(`补料单 ${replenishPendingBillids.value.join('、')} 尚未审核，暂无可用补料`)
    } else {
      ElMessage.warning('所有不良品已更换或无匹配补料')
    }
    return
  }
  replaceRows.value = rows
}
async function doBatchReplace() {
  if (!replaceRows.value.length) { ElMessage.warning('请添加更换行'); return }
  if (!detail.value?.wo_id) { ElMessage.error('工单信息无效'); return }
  replaceSaving.value = true
  try {
    for (const row of replaceRows.value) {
      if (!row._old || !row._new) continue
      const oldItem = fqcDefectiveItems.value.find(d => d._key === row._old)
      const newItem = replenishDetails.value.find(d => d._key === row._new)
      const hasEid = !!(oldItem?.eid)
      const newEid = newItem?.eid || ''
      const prodLabel = (oldItem?.label||'').match(/成品#\d+/)?.[0] || ''
      await replaceWorkOrderAsset(detail.value.wo_id, {
        itemcd: row.itemcd,
        old_eid: hasEid ? oldItem!.eid : '',
        new_eid: newEid,
        old_batch_no: hasEid ? '' : `${oldItem!.itemcd}(${oldItem!.judgment})`,
        new_batch_no: newEid ? '' : `${newItem!.itemcd} ${(newItem!.prddate||'').substring(0,10)}`,
        memo: row._memo || (prodLabel ? `${prodLabel}` : '')
      })
    }
    ElMessage.success('更换完成')
    replaceRows.value.forEach(r => replacedKeys.value.add(r._old))
    replaceDialogVisible.value = false
    loadReplaceHistory()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '更换失败') }
  finally { replaceSaving.value = false }
}

const replenishPendingBillids = ref<string[]>([])
async function loadReplenishInfo() {
  replenishItems.value = []; replenishDetails.value = []; replenishOvBillid.value = ''
  replenishPendingBillids.value = []
  if (!detail.value?.wo_id) return
  try {
    // 获取 FQC 不良品关联的、且已审核的补料明细
    const res = await fetchAvailableReplenish(detail.value.wo_id as string)
    const data = res?.data || { items: [], audited_billids: [], pending_billids: [] }

    // 记录未审核补料单（供自动填充时提示）
    replenishPendingBillids.value = data.pending_billids || []

    if (data.audited_billids.length > 0) {
      replenishOvBillid.value = data.audited_billids[0]
    }

    // 转换明细格式
    const expanded: typeof replenishDetails.value = []
    const seen = new Set<string>(); let di = 0

    data.items.forEach((item: any) => {
      const uk = `${item.itemcd}|${item.eid || ''}|${item.prddate || ''}`
      if (seen.has(uk)) return; seen.add(uk)
      expanded.push({
        itemcd: item.itemcd,
        qty: 1,
        prddate: item.prddate ? item.prddate.substring(0, 10) : '',
        itemtyp: item.itemtyp || '',
        _key: `rp_${di++}`,
        eid: item.eid || ''
      })
    })
    replenishDetails.value = expanded

    // 构建汇总信息（按物料统计）
    const itemMap = new Map<string, number>()
    data.items.forEach((item: any) => {
      itemMap.set(item.itemcd, (itemMap.get(item.itemcd) || 0) + 1)
    })
    replenishItems.value = Array.from(itemMap.entries()).map(([itemcd, qty]) => ({ itemcd, qty }))
  } catch { /* */ }
}

async function loadFqcDefectiveItems() {
  if (!detail.value?.wo_id) {
    fqcDefectiveItems.value = []
    return
  }
  try {
    const res = await request.get(`/qc/batches?search=${detail.value.wo_id}`) as any
    const batches = res?.data?.items || []
    let seq = 0
    const defective: Array<{ itemcd: string; item_nm: string; eid: string; judgment: string; _key: string; label: string }> = []
    for (const batch of batches) {
      if (batch.auditflg !== '0' && batch.auditflg !== '8') continue
      const detailRes = await request.get(`/qc/batches/${batch.batch_id}`) as any
      const records = detailRes?.data?.records || []
      for (const rec of records) {
        const eids = rec.eid_details || []
        const dts = rec.details || []
        for (const d of eids) {
          if (['BF', 'BH', 'TH'].includes(d.qcstatus)) {
            const pn = d.prod_seq ? `成品#${d.prod_seq}` : `#${seq+1}`
            seq++; defective.push({ itemcd: d.itemcd, item_nm: d.item_nm||'', eid: d.eid||'', judgment: d.qcstatus, _key: `v_${seq}`, label: `${pn} ${d.itemcd} ${d.eid||''} (${d.qcstatus})` })
          }
        }
        for (const d of dts) {
          if (['BF', 'BH', 'TH'].includes(d.qcstatus)) {
            const pn = d.prod_seq ? `成品#${d.prod_seq}` : `#${seq+1}`
            seq++; defective.push({ itemcd: d.itemcd, item_nm: d.item_nm||'', eid: '', judgment: d.qcstatus, _key: `v_${seq}`, label: `${pn} ${d.itemcd} (${d.qcstatus})` })
          }
        }
      }
    }
    fqcDefectiveItems.value = defective
  } catch { fqcDefectiveItems.value = [] }
}

async function loadFinalWhDocs() {
  finalWhDocs.value = []
  if (!detail.value?.wo_id) return
  try {
    const typeMap: Record<string,string> = {'8':'成品入库','7':'报废出库','9':'返修出库','6':'退货出库'}
    // 查 FQC QC 单号，再查其关联的 IV/OV
    const qcRes = await request.get(`/qc?per_page=10`) as any
    const qcBills = (qcRes?.data?.items||[]).filter((q: any) => q.refbillid === detail.value?.wo_id && q.auditflg === '1')
    const docs: typeof finalWhDocs.value = []
    let idx = 0
    for (const qc of qcBills) {
      const [ivRes, ovRes] = await Promise.all([
        request.get(`/warehouse/stock-in?per_page=50`),
        request.get(`/warehouse/stock-out?per_page=50`)
      ])
      const related = [
        ...(ivRes?.data?.items||[]).filter((d: any) => d.refbillid === qc.qcbillid && d.auditflg === '2'),
        ...(ovRes?.data?.items||[]).filter((d: any) => d.refbillid === qc.qcbillid && d.auditflg === '2')
      ]
      for (const d of related) {
        const detailRes = d.inbillid
          ? await request.get(`/warehouse/stock-in/${d.inbillid}`)
          : await request.get(`/warehouse/stock-out/${d.outbillid}`)
        const detail = detailRes?.data || {}
        const prds = (detail.details_prd||[]).map((i: any) => `${i.itemcd}×${i.outqty||i.inqty}`).join(' + ')
        const eids = (detail.details_eid||[]).map((i: any) => `${i.itemcd}(${i.eid})`).join(' + ')
        const items = [prds, eids].filter(Boolean).join(' + ') || '-'
        docs.push({ billid: d.inbillid||d.outbillid, invtyp: d.invtyp, typeLabel: typeMap[d.invtyp]||d.invtyp, items, memo: detail.memo||d.memo||'', index: ++idx })
      }
    }
    finalWhDocs.value = docs
  } catch { /* */ }
}

async function loadReplaceHistory() {
  if (!detail.value?.wo_id) {
    replaceHistory.value = []
    return
  }
  try {
    const res = await fetchReplaceRecords(detail.value.wo_id) as any
    replaceHistory.value = res?.data || []
    // 从历史记录重建已更换标记
    replacedKeys.value = new Set()
    fqcDefectiveItems.value.forEach(d => {
      const found = replaceHistory.value.some(r => r.itemcd === d.itemcd && r.old_batch_no?.includes(d.judgment))
      if (found) replacedKeys.value.add(d._key)
    })
  } catch { replaceHistory.value = [] }
}

const ctLabels: Record<string, string> = { '1':'定额领料','2':'不良补料','3':'报废出库','4':'返修出库','5':'退料入库' }
function consumeTypeLabel(t: string) { return ctLabels[t] || t || '-' }
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
.consume-sep-row td { background: #e6f7ff !important; font-weight: 600; color: #1677ff; border-bottom: 1px solid #91d5ff !important; }
</style>
