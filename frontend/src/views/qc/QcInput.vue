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
    </div>

    <el-table :data="detailRows" border stripe size="small" style="width:100%">
      <el-table-column prop="itemcd" label="物料编码" width="100" />
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
      <el-table-column label="EID/标签" width="200">
        <template #default="{row}">
          <template v-if="row.eid">
            <el-tag size="small" type="success">{{ row.eid }}</el-tag>
          </template>
          <template v-else-if="row.isConsumable">
            <span style="color:#909399;font-size:12px">无需标签</span>
          </template>
          <template v-else>
            <div style="display:flex;gap:4px;align-items:center">
              <el-select v-model="row.selectedEid" filterable clearable size="small" style="width:120px" placeholder="选择标签">
                <el-option v-for="lbl in row.availableLabels" :key="lbl.labelid" :label="lbl.labelid" :value="lbl.labelid"/>
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
      <el-table-column label="操作" width="60" fixed="right">
        <template #default="{row, $index}">
          <el-button v-if="row.outqty > 1" size="small" link type="primary" @click="splitRow($index)">拆分</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top:16px;display:flex;gap:8px;align-items:flex-start">
      <el-input v-model="globalMemo" type="textarea" :rows="2" placeholder="全局备注（所有质检单共享）" style="flex:1"/>
      <el-button type="primary" @click="doBatchSubmit" :loading="saving">提交质检</el-button>
    </div>
  </el-card>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createQcResult, getQcBatch, listQcBatches, voidQcBatch, type QcDetailItem, type QcEidDetailItem, type QcBatchItem } from '@/api/qc'
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
interface QcRow {
  itemcd: string; item_nm: string; refInbillid: string; prddate: string; itemtyp: string
  outqty: number; eid: string; lineno: number; reflineno: number
  isConsumable: boolean; isBom: boolean; classCd: string; whcd: string
  qcqty: number; defectQty: number; judgment: string; faultDesc: string
  selectedEid: string; manufSeq: string; remark: string
  availableLabels: { labelid: string; classcd: string }[]
  _allLabels: { labelid: string; classcd: string }[]
  generatingLabel: boolean
  _opts: [string, string][]
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
        row.selectedEid = d.eid || ''
        row.manufSeq = d.manuf_seq || ''
        newRows.push(row)
      }
    }
    // 重建后触发判定变更 + 加载可用标签
    newRows.forEach(r => { r._opts = buildOpts(r); onJudgmentChange(r) })
    detailRows.value = newRows
    preloadLabels(newRows)
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
    rows.forEach(r => { r._opts = buildOpts(r) })
    await preloadLabels(rows)
  } catch { detailRows.value = [] }
}

async function loadWoMaterials(woId: string) {
  try {
    const wo = woOptions.value.find(w => w.wo_id === woId)
    const rows: QcRow[] = []
    if (qcType.value === 'FQC') {
      // FQC: 只判定成品整机
      if (wo?.item_cd) {
        try {
          const r = await request.get(`/mes/work-orders/${woId}`) as any
          const detail = r?.data || {}
          rows.push(makeRow({ itemcd: wo.item_cd, item_nm: detail.item_nm || wo.item_cd, outqty: detail.actual_qty || detail.plan_qty || 1, itemtyp: '', prddate: '', eid: null, lineno: 0, reflineno: 0, ref_inbillid: '', consume: '', class_cd: '' }, 'prd', ''))
        } catch {
          rows.push(makeRow({ itemcd: wo.item_cd, item_nm: wo.item_cd, outqty: 1, itemtyp: '', prddate: '', eid: null, lineno: 0, reflineno: 0, ref_inbillid: '', consume: '', class_cd: '' }, 'prd', ''))
        }
      }
    } else {
      // IPQC: 显示 BOM 子件（用于过程检选择异常物料）
      if (wo?.item_cd) {
        try {
          const bomR = await request.get(`/bom/${wo.item_cd}/expand`, { params: { qty: 1 } }) as any
          const materials = (bomR?.data || []) as any[]
          materials.forEach((m: any) => {
            rows.push(makeRow({ itemcd: m.itemcd, item_nm: m.item_nm || m.itemcd, outqty: m.bomqty || 1, itemtyp: m.itemtyp || '', prddate: '', eid: null, lineno: 0, reflineno: 0, ref_inbillid: '', consume: m.consume || '', class_cd: '' }, 'prd', ''))
          })
        } catch { /* BOM 展开失败，无子件 */ }
      }
    }
    detailRows.value = rows
    rows.forEach(r => { r._opts = buildOpts(r) })
    await preloadLabels(rows)
  } catch { detailRows.value = [] }
}

function makeRow(d: any, src: string, whcd: string): QcRow {
  const consume = d.consume || ''
  return {
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

// 任何行的 selectedEid 变化时，过滤其他行下拉（排除已选）
watch(() => detailRows.value.map(r => r.selectedEid), () => {
  const used = new Set(detailRows.value.filter(r => r.selectedEid).map(r => r.selectedEid))
  detailRows.value.forEach(r => {
    r.availableLabels = (r._allLabels || r.availableLabels).filter(l => !used.has(l.labelid))
  })
}, { deep: true })

function buildOpts(row: QcRow): [string, string][] {
  const opts: [string, string][] = []
  for (const [cd, nm] of Object.entries(qcMap.value || {})) {
    if (cd === 'QA' || cd === 'DJ') continue
    if (cd === 'GC' && !row.isBom) continue
    if (row.isConsumable && ['BH', 'GB', 'GC'].includes(cd)) continue
    opts.push([cd, nm])
  }
  return opts
}

async function preloadLabels(rows: QcRow[]) {
  const itemCds = [...new Set(rows.filter(r => !r.eid && !r.isConsumable).map(r => r.itemcd))]
  const usedInGrid = new Set(rows.filter(r => r.selectedEid).map(r => r.selectedEid))
  for (const cd of itemCds) {
    try {
      const r = await fetchAvailableLabels(cd, 200)
      let labels = (r.data || []) as { labelid: string; classcd: string }[]
      labels = labels.filter(l => !usedInGrid.has(l.labelid))
      rows.filter(r => r.itemcd === cd).forEach(r => {
        const filtered = labels.filter(l => r.isBom ? /^\d{8}/.test(l.labelid) : l.labelid.startsWith(r.itemcd))
        r._allLabels = filtered  // 缓存全量，watch时用来排除已选
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
    const usedInGrid = new Set(detailRows.value.filter(r => r.selectedEid).map(r => r.selectedEid))
    // 先查已有未激活标签
    let lblR = await fetchAvailableLabels(row.itemcd, 200)
    let allLabels = (lblR.data || []) as { labelid: string; classcd: string }[]
    // 排除当前表格已选 + 按格式过滤（配件=itemcd开头，成品=日期开头）
    allLabels = allLabels.filter(l => !usedInGrid.has(l.labelid) && (row.isBom ? /^\d{8}/.test(l.labelid) : l.labelid.startsWith(row.itemcd)))
    const existing = allLabels.length
    let genNew = 0
    // 不够再补生成
    if (existing < needQty) {
      const short = needQty - existing
      const typflg = row.isBom ? '1' : '0'
      const sign = row.isBom ? 'L' : undefined
      const r = await generateLabels({ classcd: row.itemcd, typflg, count: short, ...(sign ? { sign } : {}) })
      genNew = r.data?.inserted || 0
      lblR = await fetchAvailableLabels(row.itemcd, 200)
      allLabels = (lblR.data || []) as { labelid: string; classcd: string }[]
    }
    row.availableLabels = allLabels
    row._allLabels = allLabels
    // 数量>1：自动拆分，每行一个EID
    if (needQty > 1 && allLabels.length >= needQty) {
      const rowIdx = detailRows.value.indexOf(row)
      row.outqty = 1; row.qcqty = 1; row.selectedEid = allLabels[0].labelid
      row.generatingLabel = false
      for (let i = 1; i < needQty; i++) {
        const newRow = { ...row, availableLabels: [...allLabels], generatingLabel: false }
        newRow.selectedEid = allLabels[i]?.labelid || ''
        newRow._opts = buildOpts(newRow)
        detailRows.value.splice(rowIdx + i, 0, newRow)
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
  row.defectQty = ['GA','GB','GC'].includes(row.judgment) ? 0 : row.qcqty
  // 不合格时清空 EID 标签
  if (!['GA','GB','GC'].includes(row.judgment)) {
    row.selectedEid = ''
    row.manufSeq = ''
  }
}
function onQtyChange(row: QcRow) {
  onJudgmentChange(row)
}

function setAllJudgment(judgment: string) {
  detailRows.value.forEach(r => { r.judgment = judgment; onJudgmentChange(r) })
}

function itemtypLabel(v: string) {
  const m: Record<string, string> = { DJ: '待检', GA: '合格', BF: '报废', BH: '坏件' }
  return m[v] || v || '-'
}

async function splitRow(idx: number) {
  import('element-plus').then(m => {
    const row = detailRows.value[idx]
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
      // 插入新行
      newRow._opts = buildOpts(newRow)
      detailRows.value.splice(idx + 1, 0, newRow)
      ElMessage.success(`已拆分：${splitQty} / ${newRow.outqty}`)
    }).catch(() => {})
  })
}

async function doBatchSubmit() {
  for (const row of detailRows.value) {
    if (!row.judgment) { ElMessage.warning(`物料 ${row.itemcd} 未设置质检判定`); return }
    const needEid = ['GA','GB','GC'].includes(row.judgment)
    if (needEid && !row.eid && !row.isConsumable && !row.selectedEid) {
      ElMessage.warning(`物料 ${row.itemcd} 判定为 ${qcMap.value?.[row.judgment] || row.judgment}，需要选择或生成EID标签`); return
    }
    // EID 模式下每个标签最多对应 1 台设备
    if ((row.selectedEid || row.eid) && row.qcqty > 1) {
      ElMessage.warning(`物料 ${row.itemcd} EID ${row.selectedEid} 质检数量为 ${row.qcqty}，每台设备应单独一行。请使用拆分功能`); return
    }
  }
  const groups = new Map<string, QcRow[]>()
  detailRows.value.forEach(r => {
    const k = r.judgment
    if (!groups.has(k)) groups.set(k, [])
    groups.get(k)!.push(r)
  })

  saving.value = true
  const now = new Date()
  const tag = `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}`
  batchNo.value = tag
  let created = 0
  let batchId = ''
  try {
    // 草稿重新录入：先清旧批次，循环内直接建新（无竞态）
    if (savingBatchId.value) {
      await voidQcBatch(savingBatchId.value)
    }
    for (const [optyp, rows] of groups) {
      const details: QcDetailItem[] = []
      const eid_details: QcEidDetailItem[] = []
      rows.forEach(r => {
        const hasEid = !!(r.eid || r.selectedEid)
        const base = {
          itemcd: r.itemcd,
          qcqty: r.qcqty,
          qcstatus: r.judgment,
          inqty: ['GA','GB','GC'].includes(r.judgment) ? r.qcqty : 0,
          itemtyp: r.itemtyp || undefined,
          prddate: r.prddate || undefined,
          fault_desc: r.faultDesc || undefined,
          lineno: r.lineno || undefined,
          ref_rgstbillid: r.refInbillid || undefined,
        }
        if (hasEid) {
          eid_details.push({ ...base, eid: r.selectedEid || r.eid, prddate: r.prddate || base.prddate, manuf_seq: r.manufSeq || '' })
        } else {
          details.push(base)
        }
      })
      if (details.length || eid_details.length) {
        const body: Record<string, unknown> = {
          refbillid: selectedBillId.value,
          optyp,
          itemcd: rows[0].itemcd,
          qcstatus: rows[0].judgment,
          memo: globalMemo.value ? `${globalMemo.value}#${batchNo.value}` : `QC#${batchNo.value}`,
          details: details.length ? details : undefined,
          eid_details: eid_details.length ? eid_details : undefined,
        }
        // 同批次共享 batch_id
        if (batchId) body.batch_id = batchId
        const res = await createQcResult(body)
        if (!batchId) batchId = (res.data as any)?.batch_id || ''
        created++
      }
    }
    ElMessage.success(`录入成功，批次号 ${batchId}，创建 ${created} 条质检单`)
    detailRows.value = []
    selectedBillId.value = ''
    globalMemo.value = ''
    savingBatchId.value = ''
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '录入失败') }
  finally { saving.value = false }
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0 }
</style>