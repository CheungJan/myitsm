<template>
<div class="page">
  <div class="page-header"><h2>质检录入</h2></div>

  <!-- 来源选择 -->
  <el-card shadow="never" style="margin-bottom:16px">
    <el-form inline size="small">
      <el-form-item label="来源类型">
        <el-radio-group v-model="sourceType" @change="onSourceTypeChange">
          <el-radio value="qc_out">质检出库</el-radio>
          <el-radio value="work_order">生产工单</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item v-if="sourceType==='work_order'" label="质检类型">
        <el-radio-group v-model="qcType" @change="onQcTypeChange">
          <el-radio value="FQC">最终检(FQC)</el-radio>
          <el-radio value="IPQC">过程检(IPQC)</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="来源单据">
        <el-select v-model="selectedBillId" filterable placeholder="选择单据" @change="onBillSelect" style="width:300px">
          <template v-if="sourceType==='qc_out'">
            <el-option v-for="o in stockOutOptions" :key="o.outbillid" :label="`${o.outbillid} ← ${o.refbillid||'-'} (${o.whnm||o.whcd}仓)`" :value="o.outbillid"/>
          </template>
          <template v-else>
            <el-option v-for="w in filteredWoOptions" :key="w.wo_id" :label="`${w.wo_id} ${w.item_cd||''} (${woStatusMap[w.status||'']||'?'})`" :value="w.wo_id"/>
          </template>
        </el-select>
      </el-form-item>
    </el-form>
  </el-card>

  <!-- 明细表格 -->
  <el-card shadow="never" v-if="detailRows.length">
    <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center">
      <span>明细: {{ detailRows.length }} 行</span>
      <el-button size="small" @click="setAllJudgment('GA')">全部合格</el-button>
      <el-button size="small" @click="setAllJudgment('BF')">全部报废</el-button>
      <el-button size="small" type="primary" @click="batchGenerateLabels" :loading="batchGenLoading">批量生成标签</el-button>
      <el-button size="small" type="warning" @click="replenishAll">申请补料</el-button>
      <el-button size="small" @click="expandAll">全部展开</el-button>
      <el-button size="small" @click="collapseAll">全部折叠</el-button>
    </div>

    <el-table ref="detailTable" :data="detailRows" row-key="_id" :tree-props="{children:'children'}" :indent="0" :row-class-name="({row}:any) => row.isBom ? 'product-row' : ''" border stripe size="small" style="width:100%" class="qc-input-table">
      <el-table-column label="序号" width="45" align="center"><template #default="{row}"><span v-if="row.isBom && row._prodSeq" style="color:#1677ff;font-weight:600">#{{ row._prodSeq }}</span></template></el-table-column>
      <el-table-column prop="itemcd" label="物料编码" width="100" align="left" class-name="itemcd-column">
        <template #default="{row}">
          <span v-if="row.children" style="display:inline-block;padding-left:0">{{ row.itemcd }}</span>
          <span v-else style="display:inline-block;padding-left:0">{{ row.itemcd }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="item_nm" label="物料名称" min-width="120" />
      <el-table-column label="来源入库单" width="110">
        <template #default="{row}">{{ row.refInbillid || '-' }}</template>
      </el-table-column>
      <el-table-column label="批次日期" width="100">
        <template #default="{row}">{{ row.prddate || '-' }}</template>
      </el-table-column>
      <el-table-column label="物料属性" width="70">
        <template #default="{row}">{{ row.isConsumable ? '耗材' : row.isBom ? '成品' : '配件' }}</template>
      </el-table-column>
      <el-table-column label="物料状态" width="80">
        <template #default="{row}">{{ itemtypLabel(row.itemtyp) }}</template>
      </el-table-column>
      <el-table-column prop="outqty" label="出库数量" width="80" />
      <el-table-column label="质检数量" width="80">
        <template #default="{row}">
          <el-input-number v-model="row.qcqty" :min="0" :max="row.outqty" size="small" controls-position="right" style="width:80px" @change="onQtyChange(row)"/>
        </template>
      </el-table-column>
      <el-table-column label="不良数量" width="80">
        <template #default="{row}">{{ row.defectQty }}</template>
      </el-table-column>
      <el-table-column label="不良原因" width="140">
        <template #default="{row}">
          <el-input v-model="row.faultDesc" size="small" placeholder="不良原因" :disabled="['GA','GB','GC'].includes(row.judgment)"/>
        </template>
      </el-table-column>
      <el-table-column label="EID/标签" width="220">
        <template #header>
          <div style="display:flex;align-items:center;gap:4px">EID/标签<el-input v-model="labelSign" size="small" maxlength="1" style="width:36px" title="成品标签标识符（默认L）"/><span style="font-size:11px;color:#909399">+</span></div>
        </template>
        <template #default="{row}">
          <template v-if="row.eid">
            <el-tag size="small" type="success" style="user-select:text;cursor:pointer" @click="copyEid(row.eid)">{{ row.eid }}</el-tag>
          </template>
          <template v-else-if="row.isConsumable">
            <span style="color:#909399;font-size:12px">无需标签</span>
          </template>
          <template v-else>
            <div style="display:flex;gap:4px;align-items:center">
              <template v-if="row.selectedEid && !(row as any)._editingEid">
                <el-tag size="small" type="success" style="user-select:text;cursor:pointer;max-width:130px;overflow:hidden;text-overflow:ellipsis" @click="copyEid(row.selectedEid)">{{ row.selectedEid }}</el-tag>
                <el-button size="small" link @click="(row as any)._editingEid=true" title="更换标签">✎</el-button>
              </template>
              <el-select v-else v-model="row.selectedEid" filterable clearable size="small" style="width:120px" placeholder="选择标签" @change="(row as any)._editingEid=false">
                <el-option-group v-if="(ovEidPool[row.itemcd]||[]).length" label="领料EID">
                  <el-option v-for="lbl in ovEidPool[row.itemcd]" :key="lbl.labelid" :label="lbl.labelid" :value="lbl.labelid"/>
                </el-option-group>
                <el-option-group label="未激活标签">
                  <el-option v-for="lbl in row.availableLabels" :key="lbl.labelid" :label="lbl.labelid" :value="lbl.labelid"/>
                </el-option-group>
              </el-select>
              <el-button size="small" circle @click="generateLabelForRow(row)" :loading="row.generatingLabel" title="生成标签">+</el-button>
            </div>
          </template>
        </template>
      </el-table-column>
      <el-table-column label="原厂序列号" width="130">
        <template #default="{row}">
          <el-input v-model="row.manufSeq" size="small" placeholder="选填" :disabled="row.isConsumable"/>
        </template>
      </el-table-column>
      <el-table-column label="质检判定" width="110">
        <template #default="{row}">
          <el-select v-model="row.judgment" size="small" @change="onJudgmentChange(row)">
            <el-option v-for="o in row._opts" :key="o[0]" :label="o[1]" :value="o[0]"/>
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{row}">
          <el-button v-if="row.outqty > 1" size="small" link type="primary" @click="splitRow(row)">拆分</el-button>
          <el-button v-if="['BF','BH','TH'].includes(row.judgment) && !row.replenishOvBillid" size="small" link type="warning" @click="handleReplenish(row)">申请补料</el-button>
          <el-tag v-else-if="row.replenishOvBillid" size="small" :type="row.replenishStatus === 'completed' ? 'success' : 'info'">{{ row.replenishStatus === 'completed' ? '已补料' : '补料中' }}</el-tag>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top:16px;display:flex;gap:8px;align-items:flex-start">
      <el-input v-model="globalMemo" type="textarea" :rows="2" placeholder="全局备注（所有质检单共享）" style="flex:1"/>
      <el-button @click="doBatchSubmit('save')" :loading="saving">暂存</el-button>
      <el-button type="primary" @click="doBatchSubmit('submit')" :loading="saving">提交质检</el-button>
    </div>
  </el-card>

  <!-- 补料数量编辑对话框 -->
  <el-dialog v-model="replenishDialogVisible" title="申请补料" width="480px">
    <el-table :data="replenishForm.items" size="small" border>
      <el-table-column prop="itemcd" label="物料编码" width="100"/>
      <el-table-column prop="item_nm" label="物料名称" min-width="100"/>
      <el-table-column label="补料数量" width="120">
        <template #default="{row}">
          <el-input-number v-model="row.adjustQty" :min="1" :max="999" size="small" controls-position="right" style="width:100px"/>
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button @click="replenishDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="replenishSaving" @click="doReplenish">确认申请</el-button>
    </template>
  </el-dialog>
</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createQcResult, getQcBatch, listQcBatches, getQcEidsByRefbillid, replenishQcBatch, type QcDetailItem, type QcEidDetailItem, type QcBatchItem } from '@/api/qc'
import { fetchQcOutOrders, fetchStockOutDetail } from '@/api/warehouse'
import { fetchWorkOrders } from '@/api/mes'
import { fetchAvailableLabels, generateLabels } from '@/api/inventory'
import { useDict } from '@/composables/useDict'
import request from '@/api/request'

const { dictMap: qcMap } = useDict('QC')
const woStatusMap: Record<string, string> = { DRAFT: '草稿', RELEASED: '已下达', PICKING: '领料中', IN_PROGRESS: '生产中', QC_PENDING: '待最终检', COMPLETED: '已完工', CANCELLED: '已取消' }

const sourceType = ref<'qc_out' | 'work_order'>('qc_out')
const qcType = ref<'FQC' | 'IPQC'>('FQC')
const selectedBillId = ref('')
const stockOutOptions = ref<any[]>([])
const woOptions = ref<any[]>([])
// IPQC 只显示 IN_PROGRESS，FQC 只显示 QC_PENDING
const filteredWoOptions = computed(() => woOptions.value.filter((w:any) => qcType.value === 'FQC' ? w.status === 'QC_PENDING' : w.status === 'IN_PROGRESS'))
const globalMemo = ref('')
const batchNo = ref('')
const saving = ref(false)
const detailTable = ref<any>(null)
function expandAll() { flattenRows(detailRows.value).filter(r => r.children?.length).forEach(r => { detailTable.value?.toggleRowExpansion(r, true) }) }
function collapseAll() { detailRows.value.forEach(r => { detailTable.value?.toggleRowExpansion(r, false) }) }

const batchGenLoading = ref(false)
const replenishDialogVisible = ref(false)
const replenishSaving = ref(false)
const replenishForm = reactive<{ items: { itemcd: string; item_nm: string; qty: number; adjustQty: number }[] }>({ items: [] })
const ovEidPool = ref<Record<string, { labelid: string; classcd: string }[]>>({})  // OV=8 领料 EID 池，始终可选
const labelSign = ref('L')  // 成品标签标识符，默认L
interface QcRow {
  _id: string
  itemcd: string; item_nm: string; refInbillid: string; prddate: string; itemtyp: string
  outqty: number; eid: string; lineno: number; reflineno: number
  isConsumable: boolean; isBom: boolean; classCd: string; whcd: string
  qcqty: number; defectQty: number; judgment: string; faultDesc: string
  selectedEid: string; manufSeq: string; remark: string
  availableLabels: { labelid: string; classcd: string }[]
  _allLabels: { labelid: string; classcd: string }[]
  generatingLabel: boolean
  _opts: [string, string][]
  isReplaced?: boolean
  isReplacement?: boolean
  replenishOvBillid?: string
  replenishStatus?: string
  _prodSeq?: number
  children?: QcRow[]
}
const detailRows = ref<QcRow[]>([])

onMounted(async () => {
  try {
    const r = await fetchQcOutOrders()
    stockOutOptions.value = (r.data || []) as any[]
  } catch { /* */ }
  try {
    const r = await fetchWorkOrders()
    woOptions.value = ((r.data?.items || []) as any[]).filter(
      (w: any) => w.status === 'QC_PENDING' || w.status === 'IN_PROGRESS'
    )
  } catch { /* */ }
})

function onSourceTypeChange() {
  selectedBillId.value = ''
  detailRows.value = []
}
function onQcTypeChange() {
  selectedBillId.value = ''
  detailRows.value = []
}

async function onBillSelect(billId: string) {
  if (!billId) { detailRows.value = []; return }
  if (sourceType.value === 'qc_out') {
    await loadQcOutDetails(billId)
  } else {
    await loadWoMaterials(billId)
  }
  // 加载已保存的草稿 QC 数据回显
  await overlaySavedQcData(billId)
}

// 草稿状态下回显时记录旧批次号，重新提交时覆盖旧记录
const savingBatchId = ref('')

async function overlaySavedQcData(refbillid: string) {
  try {
    const r = await listQcBatches({ per_page: '50' })
    const batches = (r.data?.items || []) as QcBatchItem[]
    const draft = batches.find((b: QcBatchItem) =>
      b.refbillid === refbillid && (b.auditflg === '0' || b.auditflg === '8')
    )
    if (!draft) { savingBatchId.value = ''; return }
    savingBatchId.value = draft.batch_id
    const det = await getQcBatch(draft.batch_id)
    const records = (det.data as any)?.records || []

    // 显示退回备注
    const firstRec = records[0]
    if (firstRec?.auditflg === '8' && firstRec?.memo) {
      globalMemo.value = firstRec.memo
    }

    // 用草稿数据重建明细行（逐个 item），保留来源单据里的物料名称等
    const itemMap = new Map<string, any>()
    for (const src of detailRows.value) {
      const k = `${src.itemcd}|${src.eid || ''}|${src.prddate || ''}|${src.itemtyp || ''}`
      if (!itemMap.has(k)) itemMap.set(k, src)
    }
    const newRows: QcRow[] = []
    for (const rec of records) {
      const dets = rec.details || []
      const eids = rec.eid_details || []
      for (const d of dets) {
        const k = `${d.itemcd}||${d.prddate || ''}|${d.itemtyp || ''}`
        const src = itemMap.get(k) || detailRows.value.find(r => r.itemcd === d.itemcd)
        const base = {
          itemcd: d.itemcd,
          item_nm: src?.item_nm || d.item_nm || '',
          ref_inbillid: d.ref_rgstbillid || src?.refInbillid || '',
          prddate: d.prddate || src?.prddate || '',
          itemtyp: d.itemtyp || src?.itemtyp || '',
          class_cd: src?.classCd || '',
          consume: src?.isConsumable ? '1' : '0',
          outqty: d.qcqty || 1,
          lineno: d.lineno || 0,
          eid: '',  // 空：走可编辑下拉
        }
        const row = makeRow(base, 'prd', src?.whcd || '')
        row.judgment = rec.qcstatus || 'GA'
        row.qcqty = d.qcqty || 1
        row.faultDesc = d.fault_desc || ''
        row.replenishOvBillid = d.replenish_ov_billid || ''
        row.replenishStatus = d.replenish_status || ''
        newRows.push(row)
      }
      for (const d of eids) {
        const k = `${d.itemcd}|${d.eid || ''}|${d.prddate || ''}|${d.itemtyp || ''}`
        const src = itemMap.get(k)
        const base = {
          itemcd: d.itemcd,
          item_nm: src?.item_nm || '',
          ref_inbillid: d.ref_rgstbillid || src?.refInbillid || '',
          prddate: d.prddate || src?.prddate || '',
          itemtyp: d.itemtyp || src?.itemtyp || '',
          class_cd: src?.classCd || '',
          consume: src?.isConsumable ? '1' : '0',
          outqty: d.qcqty || 1,
          lineno: d.lineno || 0,
          eid: '',  // 空：走可编辑下拉，而非锁定标签
        }
        const row = makeRow(base, 'prd', src?.whcd || '')  // prd 而非 eid：让 selectedEid 可编辑
        row.judgment = rec.qcstatus || 'GA'
        row.qcqty = d.qcqty || 1
        row.faultDesc = d.fault_desc || ''
        row.replenishOvBillid = d.replenish_ov_billid || ''
        row.replenishStatus = d.replenish_status || ''
        row.selectedEid = d.eid || ''
        row.manufSeq = d.manuf_seq || ''
        newRows.push(row)
      }
    }
    // FQC：复用当前树形结构，仅回填判定/EID/补料信息
    if (qcType.value === 'FQC') {
      // 构建已存数据的物码→数据映射（按出现顺序消费）
      const savedDt: any[] = []
      const savedEid: any[] = []
      for (const rec of records) {
        savedDt.push(...(rec.details || []))
        savedEid.push(...(rec.eid_details || []))
      }
      // 按 prod_seq 建索引，精确匹配产品行
      const seqMap: Record<number, Record<string, any>> = {}
      savedDt.forEach((d: any) => { const s = d.prod_seq || 0; if (!seqMap[s]) seqMap[s] = {}; seqMap[s][d.itemcd] = d })
      savedEid.forEach((d: any) => { const s = d.prod_seq || 0; if (!seqMap[s]) seqMap[s] = {}; seqMap[s][d.itemcd] = d })
      const walkAndFill = (rws: QcRow[]) => {
        for (const row of rws) {
          const rowData = seqMap[row._prodSeq || 0]
          const d = rowData ? (rowData[row.itemcd] || null) : null
          if (d) {
            row.judgment = d.qcstatus || 'GA'
            if (d.eid) row.selectedEid = d.eid
            row.replenishOvBillid = d.replenish_ov_billid || ''
            row.replenishStatus = d.replenish_status || ''
            row.qcqty = d.qcqty || 1
          }
          row._opts = buildOpts(row)
          // 回显时不触发联动，避免覆盖已恢复的判定
          if (row.children) walkAndFill(row.children)
        }
      }
      walkAndFill(detailRows.value)
      // 从工单更换记录自动回填补料 EID（按成品序号精确匹配）
      try {
        const replRes = await request.get(`/mes/work-orders/${refbillid}/replace-records`) as any
        const replRecords = replRes?.data || []
        // memo 字段含"成品#N"，提取序号
        const getProdSeq = (memo: string) => { const m = memo.match(/成品#(\d+)/); return m ? parseInt(m[1]) : 0 }
        const fillFromReplace = (rws: QcRow[]) => {
          for (const row of rws) {
            if (['BF','BH','TH'].includes(row.judgment)) {
              const seq = row._prodSeq || 0
              const match = replRecords.find((rr: any) =>
                rr.itemcd === row.itemcd && getProdSeq(rr.memo||'') === seq && !(rr as any)._used
              )
              if (match) {
                (match as any)._used = true
                if (match.new_eid) {
                  ;(row as any)._autoFilledEid = match.new_eid
                  row.selectedEid = match.new_eid
                } else if (match.new_batch_no) {
                  ;(row as any)._autoFilledEid = ''
                  row.selectedEid = ''
                }
              }
            }
            if (row.children) fillFromReplace(row.children)
          }
        }
        fillFromReplace(detailRows.value)
      } catch { /* 更换记录查询失败不阻塞 */ }
    } else {
      newRows.forEach(r => { r._opts = buildOpts(r); onJudgmentChange(r) })
      detailRows.value = newRows
    }
    preloadLabels(detailRows.value)
  } catch { savingBatchId.value = '' }
}

async function loadQcOutDetails(outbillid: string) {
  try {
    const r = await fetchStockOutDetail(outbillid) as any
    const data = r?.data || {}
    const whcd = data.whcd || ''
    const prdRows = (data.details_prd || []) as any[]
    const eidRows = (data.details_eid || []) as any[]

    const rows: QcRow[] = []
    // 批次行
    prdRows.forEach((d: any) => {
      rows.push(makeRow(d, 'prd', whcd))
    })
    // EID行
    eidRows.forEach((d: any) => {
      rows.push(makeRow(d, 'eid', whcd))
    })

    detailRows.value = rows
    const initTree = (rws: QcRow[]) => rws.forEach(r => { r._opts = buildOpts(r); if (r.children) initTree(r.children) })
    initTree(rows)
    await preloadLabels(rows)
    // 补充 OV=8 领料 EID 到下拉池
    try {
      const ovAllRes = await request.get(`/warehouse/stock-out?invtyp=8&per_page=100`) as any
      const refBillId = selectedBillId.value || ''
      const ovBills = refBillId ? (ovAllRes?.data?.items || []).filter((o: any) => o.refbillid === refBillId) : []
      const ovEidMap: Record<string, { labelid: string; classcd: string }[]> = {}
      ovEidPool.value = {}
      for (const ov of ovBills) {
        const ovDetail = await request.get(`/warehouse/stock-out/${ov.outbillid}`) as any
        for (const d of (ovDetail?.data?.details_eid || [])) {
          if (d.eid) {
            if (!ovEidMap[d.itemcd]) ovEidMap[d.itemcd] = []
            if (!ovEidMap[d.itemcd].some(l => l.labelid === d.eid)) ovEidMap[d.itemcd].push({ labelid: d.eid, classcd: d.itemcd })
          }
        }
      }
      ovEidPool.value = ovEidMap
      const mergeOvEid = (rws: QcRow[]) => rws.forEach(r => {
        if (ovEidMap[r.itemcd]) r._allLabels = [...r._allLabels.filter((l: any) => !ovEidMap[r.itemcd]?.some(o => o.labelid === l.labelid)), ...ovEidMap[r.itemcd]]
        if (r.children) mergeOvEid(r.children)
      })
      mergeOvEid(rows)
      // 用 _allLabels 重建 availableLabels
      const rebuildAvail = (rws: QcRow[]) => { const allR = flattenRows(rws); const used = new Set(allR.filter(r => r.selectedEid).map(r => r.selectedEid)); allR.forEach(r => { r.availableLabels = r._allLabels.filter(l => !used.has(l.labelid)) }) }
      rebuildAvail(rows)
    } catch { /* */ }
  } catch { detailRows.value = [] }
}

async function loadWoMaterials(woId: string) {
  try {
    const wo = woOptions.value.find(w => w.wo_id === woId)
    const rows: QcRow[] = []
    if (qcType.value === 'FQC') {
      // FQC: 每成品一行父行 + BOM配件作为子行（树形层级）
      if (wo?.item_cd) {
        const today = new Date().toISOString().substring(0, 10)
        let itemName = wo.item_cd
        let planQty = 1
        try {
          const woRes = await request.get(`/mes/work-orders/${woId}`) as any
          const detail = woRes?.data || {}
          itemName = detail.item_nm || wo.item_cd
          planQty = detail.plan_qty || 1
        } catch { /* 降级 */ }

        // 加载 BOM 配件信息
        const whcd = wo.pick_whcd || wo.warehouse_cd || '01'
        let bomDetails: any[] = []
        let stockMap: Record<string, any> = {}
        let ipqcEids: Record<string, string[]> = {}
        try {
          const bomDetail = await request.get(`/bom/${wo.item_cd}`) as any
          bomDetails = bomDetail?.data?.details || []
        } catch { /* */ }
        try {
          const bomR = await request.get(`/bom/${wo.item_cd}/expand`, { params: { qty: 1, whcd } }) as any
          ;((bomR as any)?.data?.lines || []).forEach((l: any) => {
            if (!stockMap[l.itemcd] || (l.prddate && l.prddate > (stockMap[l.itemcd]?.prddate||'')))
              stockMap[l.itemcd] = l
          })
        } catch { /* */ }
        try {
          const eidR = await getQcEidsByRefbillid(woId) as any
          ;(eidR?.data || []).forEach((e: any) => {
            if (!ipqcEids[e.itemcd]) ipqcEids[e.itemcd] = []
            ipqcEids[e.itemcd].push(e.eid)
          })
        } catch { /* */ }
        // 补充 OV=8 领料出库的 EID 物料
        try {
          const ovRes = await request.get(`/warehouse/stock-out?invtyp=8&per_page=100`) as any
          const ovList = (ovRes?.data?.items || []).filter((o: any) => o.refbillid === woId)
          for (const ov of ovList) {
            const dtRes = await request.get(`/warehouse/stock-out/${ov.outbillid}`) as any
            for (const d of (dtRes?.data?.details_eid || [])) {
              if (!ipqcEids[d.itemcd]) ipqcEids[d.itemcd] = []
              if (d.eid && !ipqcEids[d.itemcd].includes(d.eid)) ipqcEids[d.itemcd].push(d.eid)
            }
          }
        } catch { /* */ }
        // 为每台成品创建父行 + 子行
        const eidIdxMap: Record<string, number> = {}
        for (let pi = 0; pi < planQty; pi++) {
          const parent = makeRow({
            itemcd: wo.item_cd, item_nm: itemName,
            outqty: 1,  // 每成品 1 台
            itemtyp: '', prddate: today, eid: null, lineno: 0, reflineno: 0,
            ref_inbillid: '', consume: '', class_cd: '',
            is_bom: true,
          }, 'prd', '')
          parent.children = []
          parent._prodSeq = pi + 1

          for (const m of bomDetails) {
            const s = stockMap[m.itemcd] || {}
            const eids = ipqcEids[m.itemcd] || []
            if (!eidIdxMap[m.itemcd]) eidIdxMap[m.itemcd] = 0
            const qty = m.bomqty || 1  // 每台成品用几个该配件
            for (let ci = 0; ci < qty; ci++) {
              const eidIdx = eidIdxMap[m.itemcd]
              const eid = eidIdx < eids.length ? eids[eidIdx] : null
              if (eid) eidIdxMap[m.itemcd] = eidIdx + 1
              const child = makeRow({
                itemcd: m.itemcd, item_nm: s.item_nm || m.item_nm || '',
                outqty: 1,  // 每行 1 个
                itemtyp: s.itemtyp || '', prddate: (s.prddate||'').replace('T',' ').substring(0,10),
                eid: null,  // 用 selectedEid 而非 eid，保持可编辑下拉
                lineno: 0, reflineno: 0,
                ref_inbillid: s.ref_inbillid || '', consume: s.consume || '', class_cd: '',
              }, 'prd', '')
              if (eid) child.selectedEid = eid  // 预填 OV=8 领料 EID，preloadLabels 后追加
              child._prodSeq = parent._prodSeq
              parent.children!.push(child)
            }
          }
          rows.push(parent)
        }
      }
    } else {
      // IPQC: BOM 明细 + expand 取最新批次信息（不拆分FIFO，一行一物料）
      if (wo?.item_cd) {
        try {
          const whcd = wo.pick_whcd || wo.warehouse_cd || '01'
          const bomDetail = await request.get(`/bom/${wo.item_cd}`) as any
          const details = bomDetail?.data?.details || []
          // expand 获取库存批次信息（含来源入库单号）
          let stockMap: Record<string, any> = {}
          try {
            const bomR = await request.get(`/bom/${wo.item_cd}/expand`, { params: { qty: 1, whcd } }) as any
            ;((bomR as any)?.data?.lines || []).forEach((l: any) => {
              if (!stockMap[l.itemcd] || (l.prddate && l.prddate > (stockMap[l.itemcd]?.prddate||'')))
                stockMap[l.itemcd] = l
            })
          } catch { /* 无库存信息不阻塞 */ }
          details.forEach((m: any) => {
            const s = stockMap[m.itemcd] || {}
            rows.push(makeRow({
              itemcd: m.itemcd, item_nm: s.item_nm || '', outqty: m.bomqty || 1,
              itemtyp: s.itemtyp || '', prddate: (s.prddate||'').replace('T',' ').substring(0,10),
              eid: null, lineno: 0, reflineno: 0, ref_inbillid: s.ref_inbillid || '', consume: s.consume || '', class_cd: '',
            }, 'prd', ''))
          })
        } catch {
          rows.push(makeRow({ itemcd: wo.item_cd, item_nm: wo.item_nm || wo.item_cd, outqty: 1, itemtyp: '', prddate: '', eid: null, lineno: 0, reflineno: 0, ref_inbillid: '', consume: '', class_cd: '' }, 'prd', ''))
        }
      }
    }
    detailRows.value = rows
    const initTree = (rws: QcRow[]) => rws.forEach(r => { r._opts = buildOpts(r); if (r.children) initTree(r.children) })
    initTree(rows)
    await preloadLabels(rows)
    // 补充 OV=8 领料 EID 到下拉池
    try {
      const ovAllRes = await request.get(`/warehouse/stock-out?invtyp=8&per_page=100`) as any
      const refBillId = selectedBillId.value || ''
      const ovBills = refBillId ? (ovAllRes?.data?.items || []).filter((o: any) => o.refbillid === refBillId) : []
      const ovEidMap: Record<string, { labelid: string; classcd: string }[]> = {}
      ovEidPool.value = {}
      for (const ov of ovBills) {
        const ovDetail = await request.get(`/warehouse/stock-out/${ov.outbillid}`) as any
        for (const d of (ovDetail?.data?.details_eid || [])) {
          if (d.eid) {
            if (!ovEidMap[d.itemcd]) ovEidMap[d.itemcd] = []
            if (!ovEidMap[d.itemcd].some(l => l.labelid === d.eid)) ovEidMap[d.itemcd].push({ labelid: d.eid, classcd: d.itemcd })
          }
        }
      }
      ovEidPool.value = ovEidMap
      const mergeOvEid = (rws: QcRow[]) => rws.forEach(r => {
        if (ovEidMap[r.itemcd]) r._allLabels = [...r._allLabels.filter((l: any) => !ovEidMap[r.itemcd]?.some(o => o.labelid === l.labelid)), ...ovEidMap[r.itemcd]]
        if (r.children) mergeOvEid(r.children)
      })
      mergeOvEid(rows)
      // 用 _allLabels 重建 availableLabels
      const rebuildAvail = (rws: QcRow[]) => { const allR = flattenRows(rws); const used = new Set(allR.filter(r => r.selectedEid).map(r => r.selectedEid)); allR.forEach(r => { r.availableLabels = r._allLabels.filter(l => !used.has(l.labelid)) }) }
      rebuildAvail(rows)
    } catch { /* */ }
  } catch { detailRows.value = [] }
}

// 树形辅助：扁平化
function flattenRows(roots: QcRow[]): QcRow[] {
  const out: QcRow[] = []
  const w = (rws: QcRow[]) => { rws.forEach(r => { out.push(r); if (r.children) w(r.children) }) }
  w(roots)
  return out
}

let _rowIdCounter = 0
function nextRowId() { return `r${++_rowIdCounter}` }

function makeRow(d: any, src: string, whcd: string): QcRow {
  const consume = d.consume || ''
  return {
    _id: nextRowId(),
    itemcd: d.itemcd,
    item_nm: d.item_nm || '',
    refInbillid: d.ref_inbillid || '',
    prddate: d.prddate || '',
    itemtyp: d.itemtyp || '',
    outqty: d.outqty || 0,
    eid: d.eid || '',
    lineno: d.lineno || 0,
    reflineno: d.reflineno || 0,
    isConsumable: consume === '1',
    isBom: !!(d.is_bom),
    classCd: d.class_cd || '',
    whcd,
    qcqty: d.outqty || 0,
    defectQty: 0,
    judgment: Object.keys(qcMap.value || { GA: '合格' })[0] || 'GA',
    faultDesc: '',
    selectedEid: src === 'eid' ? (d.eid || '') : '',
    manufSeq: '',
    remark: '',
    availableLabels: [],
    _allLabels: [],
    generatingLabel: false,
    _opts: [],
  }
}

// 字典加载后更新所有行的判定选项
watch(() => qcMap.value, () => {
  detailRows.value.forEach(r => { r._opts = buildOpts(r) })
})

// 任何行的 selectedEid 变化时，过滤其他行下拉（排除已选）+ 检测自动关联变更
watch(() => detailRows.value.map(r => r.selectedEid), () => {
  const allR = flattenRows(detailRows.value)
  const used = new Set(allR.filter(r => r.selectedEid).map(r => r.selectedEid))
  allR.forEach(r => {
    r.availableLabels = (r._allLabels || r.availableLabels).filter(l => !used.has(l.labelid))
    // OV=8 领料 EID 始终可选
    const ovPool = ovEidPool.value[r.itemcd] || []
    for (const lbl of ovPool) {
      if (!r.availableLabels.some((l: any) => l.labelid === lbl.labelid) && !used.has(lbl.labelid)) {
        r.availableLabels.push(lbl)
      }
    }
    // 检测自动关联 EID 被手动修改
    const autoEid = (r as any)._autoFilledEid
    if (autoEid && r.selectedEid && r.selectedEid !== autoEid && !(r as any)._warnedAutoChange) {
      ;(r as any)._warnedAutoChange = true
      ;(r as any)._eidChangeNote = `[变更] ${r.itemcd} 更换记录EID=${autoEid}→${r.selectedEid}`
      ElMessage.warning(`物料 ${r.itemcd} 更换记录为新EID ${autoEid}，已改为 ${r.selectedEid}`)
    }
  })
}, { deep: true })

function buildOpts(row: QcRow): [string, string][] {
  const opts: [string, string][] = []
  for (const [cd, nm] of Object.entries(qcMap.value || {})) {
    if (cd === 'QA') continue
    // 成品：GA/GB/GC/DJ/BF/BH（不含TH退换，成品不退换）
    if (row.isBom && cd === 'TH') continue
    // DJ/GC 仅成品可选
    if (cd === 'DJ' && !row.isBom) continue
    if (cd === 'GC' && !row.isBom) continue
    // 耗材：GA/GB/BF/TH（不返修BH/不降级GC/无待检DJ）
    if (row.isConsumable && ['BH', 'GC', 'DJ'].includes(cd)) continue
    opts.push([cd, nm])
  }
  return opts
}

async function preloadLabels(rows: QcRow[]) {
  const flat = flattenRows(rows)
  const itemCds = [...new Set(flat.filter(r => !r.eid && !r.isConsumable).map(r => r.itemcd))]
  const usedInGrid = new Set(rows.filter(r => r.selectedEid).map(r => r.selectedEid))
  for (const cd of itemCds) {
    try {
      const r = await fetchAvailableLabels(cd, 200)
      let labels = (r.data || []) as { labelid: string; classcd: string }[]
      labels = labels.filter(l => !usedInGrid.has(l.labelid))
      flat.filter(r => r.itemcd === cd).forEach(r => {
        const filtered = labels.filter(l => l.labelid.startsWith(r.itemcd) || (r.isBom && /^\d{8}/.test(l.labelid)))
        r._allLabels = filtered
        r.availableLabels = filtered
      })
    } catch { /* */ }
  }
}

async function generateLabelForRow(row: QcRow) {
  row.generatingLabel = true
  try {
    const needQty = row.qcqty || 1
    // 收集当前明细已选的EID（排除它们避免冲突）
    const usedInGrid = new Set(flattenRows(detailRows.value).filter(r => r.selectedEid).map(r => r.selectedEid))
    // 先查已有未激活标签
    let lblR = await fetchAvailableLabels(row.itemcd, 200)
    let allLabels = (lblR.data || []) as { labelid: string; classcd: string }[]
    // 排除当前表格已选 + 按格式过滤（配件=itemcd开头，成品=日期开头）
    allLabels = allLabels.filter(l => !usedInGrid.has(l.labelid) && (row.isBom ? /^\d{8}/.test(l.labelid) && l.labelid.substring(8, 9) === labelSign.value : l.labelid.startsWith(row.itemcd)))
    const existing = allLabels.length
    let genNew = 0
    // 不够再补生成
    if (existing < needQty) {
      const short = needQty - existing
      const typflg = row.isBom ? '1' : '0'
      const sign = row.isBom ? labelSign.value : undefined
      const r = await generateLabels({ classcd: row.itemcd, typflg, count: short, ...(sign ? { sign } : {}) })
      genNew = r.data?.inserted || 0
      lblR = await fetchAvailableLabels(row.itemcd, 200)
      allLabels = ((lblR.data || []) as { labelid: string; classcd: string }[]).filter(
        l => !usedInGrid.has(l.labelid) && (row.isBom ? /^\d{8}/.test(l.labelid) && l.labelid.substring(8,9) === labelSign.value : l.labelid.startsWith(row.itemcd))
      )
    }
    row.availableLabels = allLabels
    row._allLabels = allLabels
    // 数量>1：自动拆分，每行一个EID
    if (needQty > 1 && allLabels.length >= needQty) {
      const parentArr = findRowParent(row, detailRows.value)
      const rowIdx = parentArr ? parentArr.indexOf(row) : -1
      row.outqty = 1; row.qcqty = 1; row.selectedEid = allLabels[0].labelid
      row.generatingLabel = false
      for (let i = 1; i < needQty; i++) {
        const newRow = { ...row, _id: nextRowId(), availableLabels: [...allLabels], generatingLabel: false }
        newRow.selectedEid = allLabels[i]?.labelid || ''
        newRow._opts = buildOpts(newRow)
        if (rowIdx >= 0) { parentArr!.splice(rowIdx + i, 0, newRow) }
      }
      const msg = genNew > 0 ? `使用 ${existing} 个已有 + 新生成 ${genNew} 个，拆为 ${needQty} 行` : `使用 ${needQty} 个已有标签，拆为 ${needQty} 行`
      ElMessage.success(msg)
    } else if (needQty === 1 && allLabels.length > 0) {
      row.selectedEid = allLabels[0].labelid
      ElMessage.success(`已选择标签 ${allLabels[0].labelid}`)
    }
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '生成失败') }
  finally { row.generatingLabel = false }
}

function onJudgmentChange(row: QcRow) {
  row.defectQty = ['GA','GB','GC','DJ'].includes(row.judgment) ? 0 : row.qcqty
  if (!['GA','GB','GC','DJ'].includes(row.judgment)) {
    // 不合格时保留 EID 标签显示（方便追溯），只清空原厂序列号
    row.manufSeq = ''
  }
  // 子行变 BF/BH/TH → 父成品自动标 DJ（配件不合格时成品待定）
  if (['BF','BH','TH'].includes(row.judgment) && !row.isBom) {
    const parent = findParentRow(row, detailRows.value)
    if (parent && parent.isBom) {
      parent.judgment = 'DJ'
      parent.defectQty = 0
    }
  }
}
function onQtyChange(row: QcRow) {
  onJudgmentChange(row)
}

function setAllJudgment(judgment: string) {
  const walk = (rows: QcRow[]) => rows.forEach(r => {
    r.judgment = judgment; onJudgmentChange(r)
    if (r.children) walk(r.children)
  })
  walk(detailRows.value)
}

function findRowParent(target: QcRow, roots: QcRow[]): QcRow[] | null {
  if (roots.includes(target)) return roots
  for (const r of roots) {
    if (r.children) {
      const found = findRowParent(target, r.children)
      if (found) return found
    }
  }
  return null
}

function findParentRow(child: QcRow, roots: QcRow[]): QcRow | null {
  for (const r of roots) {
    if (r.children?.includes(child)) return r
    if (r.children) {
      const found = findParentRow(child, r.children)
      if (found) return found
    }
  }
  return null
}

function copyEid(eid: string) {
  const ta = document.createElement('textarea')
  ta.value = eid; ta.style.position = 'fixed'; ta.style.opacity = '0'
  document.body.appendChild(ta); ta.select()
  try { document.execCommand('copy'); ElMessage.success(`已复制 ${eid}`) } catch { /* */ }
  document.body.removeChild(ta)
}

function itemtypLabel(v: string) {
  const m: Record<string, string> = { DJ: '待检', GA: '合格', BF: '报废', BH: '坏件' }
  return m[v] || v || '-'
}

async function splitRow(row: QcRow) {
  import('element-plus').then(m => {
    const totalQty = row.outqty
    m.ElMessageBox.prompt('拆分数量（剩余将自动生成新行）', '拆分明细行', {
      inputType: 'number',
      inputValue: String(Math.floor(totalQty / 2)),
      inputValidator: (v: string) => {
        const n = parseInt(v)
        if (isNaN(n) || n <= 0 || n >= totalQty) return '数量需在 1 到 ' + (totalQty - 1) + ' 之间'
        return true
      }
    }).then(({ value: qtyStr }) => {
      const splitQty = parseInt(qtyStr || '1')
      // 新行：剩余数量，复制原行属性
      const newRow = { ...row, availableLabels: [...row.availableLabels] }
      newRow.outqty = totalQty - splitQty
      newRow.qcqty = newRow.outqty
      newRow.defectQty = 0
      newRow.judgment = 'GA'
      newRow.selectedEid = ''
      newRow.manufSeq = ''
      newRow.faultDesc = ''
      // 原行：拆分数量
      row.outqty = splitQty
      row.qcqty = splitQty
      row.defectQty = 0
      row.judgment = 'GA'
      // 找到 row 所在的数组并插入新行
      const parentArr = findRowParent(row, detailRows.value)
      const rowIdx = parentArr ? parentArr.indexOf(row) : -1
      newRow._opts = buildOpts(newRow)
      if (rowIdx >= 0) { parentArr!.splice(rowIdx + 1, 0, newRow) }
      ElMessage.success(`已拆分：${splitQty} / ${newRow.outqty}`)
    }).catch(() => {})
  })
}

async function batchGenerateLabels() {
  const allR = flattenRows(detailRows.value)
  // 统计每种物料需要标签的行数（GA/GB/GC判定、无EID无标签、非耗材）
  const needMap: Record<string, { itemcd: string; count: number; isBom: boolean }> = {}
  allR.forEach(r => {
    if (!['GA','GB','GC','DJ'].includes(r.judgment)) return
    if (r.eid || r.selectedEid || r.isConsumable) return
    if (!needMap[r.itemcd]) needMap[r.itemcd] = { itemcd: r.itemcd, count: 0, isBom: r.isBom }
    needMap[r.itemcd].count++
  })
  const needList = Object.values(needMap)
  if (!needList.length) { ElMessage.info('所有合格行已有标签'); return }

  batchGenLoading.value = true
  const usedInGrid = new Set(allR.filter(r => r.selectedEid).map(r => r.selectedEid))
  const summaries: string[] = []
  try {
    for (const item of needList) {
      // 获取已有未激活标签
      let lblR = await fetchAvailableLabels(item.itemcd, 200)
      const lblFilter = (l: { labelid: string; classcd: string }) =>
        !usedInGrid.has(l.labelid) &&
        (item.isBom ? /^\d{8}/.test(l.labelid) && l.labelid.substring(8,9) === labelSign.value : l.labelid.startsWith(item.itemcd))
      let pool = ((lblR.data || []) as { labelid: string; classcd: string }[]).filter(lblFilter)

      const need = item.count
      const existing = pool.length
      let genNew = 0
      if (existing < need) {
        const short = need - existing
        const typflg = item.isBom ? '1' : '0'
        const sign = item.isBom ? labelSign.value : undefined
        const genR = await generateLabels({ classcd: item.itemcd, typflg, count: short, ...(sign ? { sign } : {}) })
        genNew = genR.data?.inserted || 0
        // 重新拉取
        lblR = await fetchAvailableLabels(item.itemcd, 200)
        pool = ((lblR.data || []) as { labelid: string; classcd: string }[]).filter(lblFilter)
      }
      // 分配给各行
      let assigned = 0
      allR.forEach(r => {
        if (assigned >= pool.length) return
        if (r.itemcd !== item.itemcd) return
        if (!['GA','GB','GC','DJ'].includes(r.judgment)) return
        if (r.eid || r.selectedEid || r.isConsumable) return
        r.selectedEid = pool[assigned].labelid
        usedInGrid.add(pool[assigned].labelid)
        assigned++
      })
      const msg = genNew > 0
        ? `${item.itemcd}: 使用${existing}个已有 + 新生成${genNew}个`
        : `${item.itemcd}: 使用${existing}个已有标签`
      summaries.push(msg)
    }
    ElMessage.success(`批量标签完成：${summaries.join('；')}`)
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '批量生成失败') }
  finally { batchGenLoading.value = false }
}

async function replenishAll() {
  if (!savingBatchId.value) {
    await doBatchSubmit('save')
    if (!savingBatchId.value) { ElMessage.error('请先保存质检数据'); return }
  }
  const nonPassRows = flattenRows(detailRows.value).filter(
    r => ['BF', 'BH', 'TH'].includes(r.judgment) && !r.replenishOvBillid
  )
  if (!nonPassRows.length) { ElMessage.warning('没有需要补料的物料'); return }
  const agg: Record<string, { itemcd: string; item_nm: string; qty: number }> = {}
  nonPassRows.forEach(r => {
    if (!agg[r.itemcd]) agg[r.itemcd] = { itemcd: r.itemcd, item_nm: r.item_nm, qty: 0 }
    agg[r.itemcd].qty += r.qcqty
  })
  replenishForm.items = Object.values(agg).map(i => ({ ...i, adjustQty: i.qty }))
  replenishDialogVisible.value = true
}

async function handleReplenish(row: QcRow) {
  if (!['BF', 'BH', 'TH'].includes(row.judgment)) return
  await replenishAll()
}

async function doReplenish() {
  replenishSaving.value = true
  try {
    const qtyMap: Record<string, number> = {}
    replenishForm.items.forEach(i => { qtyMap[i.itemcd] = i.adjustQty })
    const res = await replenishQcBatch(savingBatchId.value, qtyMap)
    const data = (res as any)?.data || {}
    const ovBillid = data.ov_billid || ''
    flattenRows(detailRows.value).forEach(r => {
      if (['BF', 'BH', 'TH'].includes(r.judgment) && !r.replenishOvBillid) {
        r.replenishOvBillid = ovBillid
        r.replenishStatus = 'pending'
      }
    })
    ElMessage.success(`补料出库单 ${ovBillid} 已生成，共 ${data.item_count || 0} 种物料`)
    replenishDialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '补料申请失败')
  } finally { replenishSaving.value = false }
}

async function doBatchSubmit(mode: 'submit' | 'save' = 'submit') {
  const isSubmit = mode === 'submit'
  const allRows = flattenRows(detailRows.value)
  // 暂存不校验，直接保存已有数据；提交时完整校验
  if (isSubmit) {
    for (const row of allRows) {
      if (!row.judgment) { ElMessage.warning(`物料 ${row.itemcd} 未设置质检判定`); return }
      const needEid = ['GA','GB','GC','DJ'].includes(row.judgment)
      if (needEid && !row.eid && !row.isConsumable && !row.selectedEid) {
        ElMessage.warning(`物料 ${row.itemcd} 判定为 ${qcMap.value?.[row.judgment] || row.judgment}，需要选择或生成EID标签`); return
      }
      if ((row.selectedEid || row.eid) && row.qcqty > 1) {
        ElMessage.warning(`物料 ${row.itemcd} EID ${row.selectedEid} 质检数量为 ${row.qcqty}，每台设备应单独一行。请使用拆分功能`); return
      }
    }
  }
  // 提交时检查补料提醒；暂存跳过
  if (isSubmit) {
    const pendingReplenish = allRows.filter(
      r => ['BF', 'BH', 'TH'].includes(r.judgment) && !r.replenishOvBillid
    )
    if (pendingReplenish.length > 0) {
      try {
        await ElMessageBox.confirm(
          `有 ${pendingReplenish.length} 个不通过行未申请补料。建议先申请补料后再审核。是否继续提交？`,
          '补料提醒',
          { confirmButtonText: '继续提交', cancelButtonText: '去申请补料', type: 'warning',
            distinguishCancelAndClose: true }
        )
      } catch {
        return
      }
    }
  }

  // 扁平化树形数据
  const groups = new Map<string, QcRow[]>()
  if (qcType.value === 'FQC') {
    groups.set('FQ', allRows)
  } else {
    // IPQC / 质检出库: 按判定分组
    detailRows.value.forEach(r => {
      const k = r.judgment
      if (!groups.has(k)) groups.set(k, [])
      groups.get(k)!.push(r)
    })
  }

  saving.value = true
  const now = new Date()
  const tag = `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}`
  batchNo.value = tag
  let created = 0
  let batchId = ''
  try {
    for (const [optyp, rows] of groups) {
      const details: QcDetailItem[] = []
      const eid_details: QcEidDetailItem[] = []
      rows.forEach(r => {
        const hasEid = !!(r.eid || r.selectedEid)
        const eidNote = (r as any)._eidChangeNote || ''
        const base = {
          itemcd: r.itemcd,
          qcqty: r.qcqty,
          qcstatus: r.judgment,
          inqty: ['GA','GB','GC'].includes(r.judgment) ? r.qcqty : 0,
          itemtyp: r.itemtyp || undefined,
          prddate: r.prddate || undefined,
          fault_desc: r.faultDesc || eidNote || undefined,
          lineno: r.lineno || undefined,
          ref_rgstbillid: r.refInbillid || undefined,
        }
        if (hasEid) {
          eid_details.push({ ...base, eid: r.selectedEid || r.eid, prddate: r.prddate || base.prddate, manuf_seq: r.manufSeq || '', prod_seq: r._prodSeq })
        } else {
          details.push({ ...base, prod_seq: r._prodSeq })
        }
      })
      if (details.length || eid_details.length) {
        // FQC 用成品物料编码和判定作为主记录
        let primaryItemCd = rows[0]?.itemcd || ''
        let primaryJudgment = rows[0]?.judgment || 'GA'
        if (qcType.value === 'FQC') {
          const productRow = rows.find((r: QcRow) => r.isBom)
          if (productRow) {
            primaryItemCd = productRow.itemcd
            primaryJudgment = productRow.judgment || 'GA'
          }
        }
        const body: Record<string, unknown> = {
          refbillid: selectedBillId.value,
          optyp,
          itemcd: primaryItemCd,
          qcstatus: primaryJudgment,
          draft_type: isSubmit ? 'C' : 'S',
          memo: globalMemo.value ? `${globalMemo.value}#${batchNo.value}` : `QC#${batchNo.value}`,
          details: details.length ? details : undefined,
          eid_details: eid_details.length ? eid_details : undefined,
        }
        // 首条传 old_batch_id 实现原子替换，后续共享 batch_id
        if (savingBatchId.value && !batchId) body.old_batch_id = savingBatchId.value
        else if (batchId) body.batch_id = batchId
        const res = await createQcResult(body)
        if (!batchId) batchId = (res.data as any)?.batch_id || ''
        created++
      }
    }
    ElMessage.success(isSubmit ? `提交成功，批次号 ${batchId}` : `已暂存，批次号 ${batchId}`)
    savingBatchId.value = batchId
    if (isSubmit) {
      detailRows.value = []
      selectedBillId.value = ''
      globalMemo.value = ''
      savingBatchId.value = ''
    }
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '录入失败') }
  finally { saving.value = false }
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0 }
</style>

<style>
/* 成品行深色背景 */
.qc-input-table .product-row > td { background-color: #e6f2ff !important; font-weight: 500; }
/* 强制覆盖树形表格子行的物料编码列缩进 - 使用最高权重 */
.qc-input-table .el-table__row--level-1 .itemcd-column .cell {
  padding-left: 0 !important;
}
.qc-input-table .el-table__row--level-2 .itemcd-column .cell {
  padding-left: 0 !important;
}
.qc-input-table .el-table__row--level-3 .itemcd-column .cell {
  padding-left: 0 !important;
}
</style>