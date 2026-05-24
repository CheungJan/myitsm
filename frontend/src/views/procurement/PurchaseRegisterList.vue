<template>
  <div class="page">
    <div class="page-header"><h2>采购订单</h2><div style="display:flex;gap:8px"><el-button type="warning" size="small" plain @click="quickFilter('1')">待审核</el-button><el-button type="primary" size="small" @click="openCreate">新建订单</el-button></div></div>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open">
        <el-table-column prop="rgstbillid" label="订单号" width="110"/>
        <el-table-column label="采购员" width="80"><template #default="{row}">{{ userName(row.pcrep) }}</template></el-table-column>
        <el-table-column prop="rgstamt" label="金额" width="100" align="right"/>
        <el-table-column label="审批" width="70"><template #default="{row}"><el-tag :type="row.auditflg==='2'?'success':'warning'" size="small">{{ afLabel(row.auditflg) }}</el-tag></template></el-table-column>
        <el-table-column prop="gendate" label="日期" width="100"/>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
        <el-table-column label="操作员" width="80"><template #default="{row}">{{ userName(row.opercd) }}</template></el-table-column>
        <el-table-column label="操作" width="100" fixed="right"><template #default="{row}"><el-button v-if="row.auditflg==='0'" link type="primary" size="small" @click.stop="doSubmit(row)">送审</el-button><el-button v-if="row.auditflg==='1'" link type="warning" size="small" @click.stop="openAudit(row)">审核</el-button><el-button v-if="row.auditflg==='9'" link type="primary" size="small" @click.stop="doSubmit(row)">重新送审</el-button></template></el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <el-dialog :title="'采购订单 — '+(detail?.rgstbillid||'')" v-model="drawer" width="500px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="订单号">{{ detail.rgstbillid }}</el-descriptions-item>
          <el-descriptions-item label="采购员">{{ userName(detail.pcrep) }}</el-descriptions-item>
          <el-descriptions-item label="金额">{{ detail.rgstamt }}</el-descriptions-item>
          <el-descriptions-item label="审批人">{{ detail.auditman||'-' }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ detail.gendate }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo||'-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>

    <el-dialog title="审核采购订单" v-model="auditing" width="600px" @closed="Object.keys(auditQtys).forEach(k=>delete auditQtys[k as any]);_auditTick.value++">
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small"><el-descriptions-item label="订单号">{{ auditTarget.rgstbillid }}</el-descriptions-item><el-descriptions-item label="供应商">{{ auditTarget.suppliercd||'-' }}</el-descriptions-item></el-descriptions>
        <h4 style="margin:12px 0 8px">审核明细</h4>
        <el-table :data="auditTarget.details||[]" size="small" stripe>
          <el-table-column prop="lineno" label="行号" width="60"/>
          <el-table-column prop="itemcd" label="物料编码" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="120"/>
          <el-table-column prop="rgsqty" label="采购数量" width="80"/>
          <el-table-column label="审核数量" width="120"><template #default="{row}"><el-input-number :model-value="getAuditQty(row.lineno)" @update:model-value="(v:number|null)=>setAuditQty(row.lineno,v)" :min="0" :max="row.rgsqty||0" size="small" style="width:100px"/></template></el-table-column>
        </el-table>
        <el-input v-model="auditMemo" type="textarea" :rows="2" placeholder="审核备注" style="margin-top:12px"/>
      </template>
      <template #footer>
        <el-button @click="auditing=false">取消</el-button>
        <el-button type="danger" @click="doAudit('9')" :loading="auditLoading">退回</el-button>
        <el-button type="success" @click="doAudit('2')" :loading="auditLoading">审核通过</el-button>
      </template>
    </el-dialog>

    <el-dialog title="新建采购订单" v-model="creating" width="700px" @closed="resetForm">
      <el-form :model="form" label-width="90px" size="small">
        <!-- 步骤1：选择需求单 -->
        <el-form-item label="来源需求">
          <div style="display:flex;gap:8px;width:100%">
            <el-input v-model="selectedReqName" placeholder="点击选择已审批的采购需求" readonly style="flex:1">
              <template #append><el-button @click="openReqSelector">选择</el-button></template>
            </el-input>
            <el-button v-if="form.ref_pcplanid" type="warning" size="small" @click="clearReq">清除</el-button>
          </div>
        </el-form-item>
        <!-- 步骤2：选择供应商（根据需求单配件过滤） -->
        <el-form-item label="供应商">
          <el-select v-model="form.suppliercd" style="width:100%" filterable placeholder="选择供应商" :disabled="!form.ref_pcplanid || filteredSuppliers.length===0">
            <el-option v-for="s in filteredSuppliers" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd"/>
          </el-select>
          <el-alert v-if="form.ref_pcplanid && filteredSuppliers.length===0 && !suppLoading" title="该需求单无匹配的供应商" type="warning" :closable="false" show-icon style="margin-top:8px"/>
        </el-form-item>
        <el-form-item label="采购员"><el-input v-model="form.pcrep" placeholder="采购代表"/></el-form-item>
        <el-form-item label="下单日期"><el-date-picker v-model="form.rgstdate" type="date" style="width:100%" value-format="YYYY-MM-DD"/></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.memo" type="textarea" :rows="2"/></el-form-item>
        <!-- 步骤3：加载商品（根据需求单+供应商） -->
        <el-form-item label="采购明细">
          <div style="width:100%">
            <el-alert v-if="!form.suppliercd" title="请先选择来源需求和供应商" type="info" :closable="false" show-icon style="margin-bottom:8px"/>
            <el-button v-else size="small" @click="loadAvailableItems" :loading="availLoading" style="margin-bottom:8px">加载可采购商品</el-button>
            <el-table v-if="availItems.length>0" :data="availItems" size="small" max-height="300" @selection-change="onAvailSelect" style="margin-bottom:8px">
              <el-table-column type="selection" width="40"/>
              <el-table-column prop="itemcd" label="物料编码" width="90"/>
              <el-table-column prop="itemnm" label="物料名称" min-width="100"/>
              <el-table-column prop="available_for_order" label="可购余额" width="80"/>
              <el-table-column label="采购数量" width="100"><template #default="{row}"><el-input-number v-model="row._qty" :min="0" :max="Number(row.available_for_order)||0" size="small" style="width:80px"/></template></el-table-column>
              <el-table-column label="单价" width="90"><template #default="{row}"><el-input-number v-model="row._price" :min="0" :precision="2" size="small" style="width:80px"/></template></el-table-column>
              <el-table-column prop="wunit" label="单位" width="60"/>
            </el-table>
            <el-button v-if="availItems.length>0" size="small" type="primary" @click="addAvailItems" style="margin-bottom:8px">添加到订单</el-button>
            <el-table v-if="formDetails.length>0" :data="formDetails" size="small" style="margin-top:8px">
              <el-table-column prop="itemcd" label="物料编码" width="90"/>
              <el-table-column prop="itemnm" label="物料名称" min-width="100"/>
              <el-table-column prop="ref_pcplanid" label="来源需求" width="90"/>
              <el-table-column prop="rgsqty" label="数量" width="60"/>
              <el-table-column prop="rgstprice" label="单价" width="70"/>
              <el-table-column label="拆单" width="70"><template #default="{row}"><el-button v-if="!isSplit(detailKey(row))" link type="warning" size="small" @click="handleSplit(row)">拆单</el-button></template></el-table-column>
              <el-table-column label="操作" width="60"><template #default="{row,$index}"><el-button link type="danger" size="small" @click="removeFormDetail($index,row)">删除</el-button></template></el-table-column>
            </el-table>
            <!-- 拆分子行 -->
            <template v-for="row in formDetails" :key="detailKey(row)">
              <template v-if="isSplit(detailKey(row))">
                <div v-for="line in getSplitLines(detailKey(row))" :key="line.id" style="padding:4px 0 4px 24px;display:flex;gap:8px;align-items:center;background:#fafafa;">
                  <span style="font-size:12px;color:#909399;white-space:nowrap;">├ 拆分: {{ row.itemnm }}</span>
                  <el-input-number v-model="line.rgsqty" :min="1" size="small" style="width:100px;" controls-position="right" />
                  <el-select v-model="line.suppliercd" size="small" style="width:160px;" placeholder="选择供应商" filterable>
                    <el-option v-for="s in filteredSuppliers" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd" />
                  </el-select>
                  <el-input-number v-model="line.unitprice" :min="0" :precision="2" size="small" style="width:100px;" controls-position="right" placeholder="单价" />
                  <el-button link type="danger" size="small" @click="removeSplitLine(detailKey(row), line.id)">删除</el-button>
                </div>
                <div style="padding:4px 24px;">
                  <el-button link type="primary" size="small" @click="addSplitLine(detailKey(row))">+ 添加拆分行</el-button>
                </div>
              </template>
            </template>
          </div>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="creating=false">取消</el-button><el-button type="primary" @click="handleBatchSubmit" :loading="saving">创建</el-button></template>
    </el-dialog>

    <!-- 需求单选择弹窗 -->
    <el-dialog title="选择采购需求单" v-model="reqSelectorOpen" width="750px">
      <el-table :data="reqList" v-loading="reqLoading" size="small" stripe highlight-current-row @row-click="selectReq">
        <el-table-column prop="pcplanid" label="需求单号" width="110"/>
        <el-table-column label="采购类型" width="80"><template #default="{row}">{{ puLabel(row.pctyp) }}</template></el-table-column>
        <el-table-column prop="slbillid" label="销售单号" width="100"/>
        <el-table-column label="计划日期" width="100"><template #default="{row}">{{ formatDate(row.plandate) }}</template></el-table-column>
        <el-table-column label="操作员" width="80"><template #default="{row}">{{ userName(row.opercd) }}</template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
      </el-table>
      <template #footer><el-button @click="reqSelectorOpen=false">取消</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">import {ref,reactive,onMounted} from 'vue';import {ElMessage} from 'element-plus';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {useUserNames} from '@/composables/useUserNames';import {useDict} from '@/composables/useDict';import {fetchOrders,fetchAvailableItems,fetchRequisitions} from '@/api/procurement';import type {ProcRecord} from '@/api/procurement';import {fetchSuppliersByRequisition,batchCreateOrders,validateBatchOrders} from '@/api/master';import request from '@/api/request'

const{userName}=useUserNames()
const{dictLabel:afLabel}=useDict('AF')
const{dictLabel:puLabel}=useDict('PU')
const{items,loading,page,perPage,total,load,onSearch}=useListPage<ProcRecord>(fetchOrders)
const{drawer,detail,open}=useDetailDrawer<ProcRecord>()

function quickFilter(flg:string){onSearch({auditflg:flg})}

// 审核
const auditing=ref(false);const auditLoading=ref(false);const auditTarget=ref<ProcRecord|null>(null)
const auditMemo=ref('')
const auditQtys:Record<number,number>={};const _auditTick=ref(0)
function getAuditQty(lineno:number):number{void _auditTick.value;return auditQtys[lineno]??0}
function setAuditQty(lineno:number,val:number|null){auditQtys[lineno]=val??0;_auditTick.value++}
async function openAudit(row:ProcRecord){
  auditTarget.value=row;auditMemo.value=''
  for(const k of Object.keys(auditQtys))delete auditQtys[k as any];_auditTick.value++
  if(auditTarget.value?.details){
    for(const d of auditTarget.value.details as any[]){auditQtys[d.lineno]=d.rgstqty||0}
    _auditTick.value++
  }
  auditing.value=true
}
async function doSubmit(row:ProcRecord){
  try{await request.post('/procurement/orders/'+row.rgstbillid+'/audit',{auditflg:'1'});ElMessage.success('已送审');load()}catch(e:any){ElMessage.error(e?.response?.data?.message||'送审失败')}
}
async function doAudit(flg:string){
  auditLoading.value=true
  try{
    const details=Object.entries(auditQtys).map(([lineno,auditqty])=>({lineno:Number(lineno),auditqty}))
    await request.post('/procurement/orders/'+auditTarget.value!.rgstbillid+'/audit',{auditflg:flg,checkmemo:auditMemo.value,details})
    ElMessage.success(flg==='2'?'审核通过':'已退回');auditing.value=false;load()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'审核失败')}finally{auditLoading.value=false}
}

// 新建 — 从可用商品选择（关联来源需求单）
const creating=ref(false);const saving=ref(false)
const form=reactive({suppliercd:'',pcrep:'',rgstdate:'',memo:'',ref_pcplanid:'',ref_pclineno:0})
const formDetails=reactive<{itemcd:string;itemnm:string;rgsqty:number;rgstprice:number;units:string;ref_pcplanid:string;ref_pclineno:number}[]>([])

// ---- 拆单数据结构与辅助 ----
interface SplitLine {
  id: string
  suppliercd: string
  suppliernm: string
  rgsqty: number
  unitprice: number
  ref_pcplanid: string
  ref_pclineno: number
  itemcd: string
}
const splitGroups = ref<Map<string, SplitLine[]>>(new Map())
function generateId() { return Date.now().toString(36) + Math.random().toString(36).slice(2) }
function detailKey(row: Record<string,any>) { return `${row.ref_pcplanid}_${row.ref_pclineno}_${row.itemcd}` }
function isSplit(key: string): boolean { const lines = splitGroups.value.get(key); return !!lines && lines.length > 1 }
function getSplitLines(key: string): SplitLine[] { return splitGroups.value.get(key) || [] }
function handleSplit(detail: Record<string,any>) {
  const key = detailKey(detail)
  if (splitGroups.value.has(key)) return
  const total = (Number(detail.rgsqty) || 0)
  if (total <= 0) return
  const half1 = Math.ceil(total / 2)
  const half2 = total - half1
  splitGroups.value.set(key, [
    { id: generateId(), suppliercd: '', suppliernm: '', rgsqty: half1, unitprice: 0, ref_pcplanid: detail.ref_pcplanid, ref_pclineno: detail.ref_pclineno, itemcd: detail.itemcd },
    { id: generateId(), suppliercd: '', suppliernm: '', rgsqty: half2, unitprice: 0, ref_pcplanid: detail.ref_pcplanid, ref_pclineno: detail.ref_pclineno, itemcd: detail.itemcd },
  ])
}
function addSplitLine(key: string) {
  const lines = splitGroups.value.get(key)
  if (!lines || lines.length === 0) return
  const first = lines[0]
  lines.push({ id: generateId(), suppliercd: '', suppliernm: '', rgsqty: 0, unitprice: 0, ref_pcplanid: first.ref_pcplanid, ref_pclineno: first.ref_pclineno, itemcd: first.itemcd })
}
function removeSplitLine(key: string, lineId: string) {
  const lines = splitGroups.value.get(key)
  if (!lines) return
  const idx = lines.findIndex(l => l.id === lineId)
  if (idx < 0) return
  lines.splice(idx, 1)
  if (lines.length <= 1) { splitGroups.value.delete(key) }
}
function removeFormDetail(index: number, row: Record<string,any>) {
  const key = detailKey(row)
  splitGroups.value.delete(key)
  formDetails.splice(index, 1)
}
function buildBatchOrders(): { orders: Record<string,any>[] } {
  const orders: Record<string, Record<string,any>> = {}
  const splitKeys = new Set(splitGroups.value.keys())
  // 从拆分组构建订单
  splitGroups.value.forEach((lines) => {
    lines.forEach(line => {
      if (!line.suppliercd || line.rgsqty <= 0) return
      const sKey = line.suppliercd
      if (!orders[sKey]) orders[sKey] = { suppliercd: line.suppliercd, memo: form.memo || '拆单', details: [] }
      orders[sKey].details.push({
        itemcd: line.itemcd, rgsqty: line.rgsqty, unitprice: line.unitprice,
        ref_pcplanid: line.ref_pcplanid, ref_pclineno: line.ref_pclineno,
      })
    })
  })
  // 从未拆分明细构建订单（使用主表单供应商）
  formDetails.forEach(d => {
    const key = detailKey(d)
    if (splitKeys.has(key)) return
    if (!form.suppliercd) return
    const sKey = form.suppliercd
    if (!orders[sKey]) orders[sKey] = { suppliercd: form.suppliercd, memo: form.memo, details: [] }
    orders[sKey].details.push({
      itemcd: d.itemcd, rgsqty: d.rgsqty, unitprice: d.rgstprice,
      ref_pcplanid: d.ref_pcplanid, ref_pclineno: d.ref_pclineno,
    })
  })
  return { orders: Object.values(orders) }
}

const availItems=ref<Record<string,any>[]>([])
const availLoading=ref(false)
// 步骤1：选择需求单
const reqSelectorOpen=ref(false)
const reqLoading=ref(false)
const reqList=ref<ProcRecord[]>([])
const selectedReqName=ref('')
// 步骤2：根据需求单配件过滤供应商
const filteredSuppliers=ref<{supp_cd:string;supp_nm:string}[]>([])
const suppLoading=ref(false)

function formatDate(val:string|undefined){if(!val)return'-';return val.split('T')[0]}

// 打开需求单选择弹窗
async function openReqSelector(){
  reqLoading.value=true;reqSelectorOpen.value=true
  try{
    const r=await fetchRequisitions({auditflg:'2',per_page:'100'})
    reqList.value=r.data?.items||[]
  }catch{ElMessage.error('加载需求单失败')}
  finally{reqLoading.value=false}
}
// 选择需求单
async function selectReq(row:ProcRecord){
  form.ref_pcplanid=row.pcplanid as string
  selectedReqName.value=`${row.pcplanid} (${puLabel(row.pctyp as string)})`
  reqSelectorOpen.value=false
  form.suppliercd='' // 重置供应商
  // 加载匹配该需求单的供应商（老PB逻辑：有available_qty>0的商品）
  await loadSuppliersByRequisition(row.pcplanid as string)
}
// 清除选择
function clearReq(){
  form.ref_pcplanid=''
  form.ref_pclineno=0
  selectedReqName.value=''
  form.suppliercd=''
  filteredSuppliers.value=[]
}
// 根据需求单号加载供应商（老PB逻辑）
async function loadSuppliersByRequisition(pcplanid:string){
  suppLoading.value=true
  try{
    const r=await fetchSuppliersByRequisition(pcplanid)
    filteredSuppliers.value=r.data||[]
    if(filteredSuppliers.value.length===0){
      ElMessage.warning('无供应商可提供该需求单中有余额的商品')
    }
  }catch{ElMessage.error('加载供应商失败')}
  finally{suppLoading.value=false}
}

async function loadAvailableItems(){
  if(!form.suppliercd||!form.ref_pcplanid)return
  availLoading.value=true
  try{
    // 根据供应商+需求单过滤可采购商品
    const r=await fetchAvailableItems({suppliercd:form.suppliercd})
    let items=(r.data||[]) as any[]
    // 只保留来自所选需求单的商品
    items=items.filter((it:any)=>(it.plan_details||'').includes(form.ref_pcplanid))
    for(const it of items){it._qty=0;it._price=0}
    availItems.value=items
    if(items.length===0){
      ElMessage.info('该供应商无匹配的可采购商品')
    }
  }catch{ElMessage.error('加载可采购商品失败')}finally{availLoading.value=false}
}

function onAvailSelect(rows:any[]){/* 由checkbox自动处理 */}

function addAvailItems(){
  for(const it of availItems.value){
    if(it._qty>0){
      const pd=JSON.parse((it.plan_details||'[{}]')[0])||{}
      formDetails.push({
        itemcd:it.itemcd,itemnm:it.itemnm,
        rgsqty:it._qty,rgstprice:it._price||0,
        units:it.wunit||'',
        ref_pcplanid:pd.pcplanid||'',ref_pclineno:pd.pclineno||0
      })
    }
  }
}

function openCreate(){creating.value=true}
function resetForm(){form.suppliercd='';form.pcrep='';form.rgstdate='';form.memo='';form.ref_pcplanid='';form.ref_pclineno=0;formDetails.length=0;availItems.value=[];selectedReqName.value='';filteredSuppliers.value=[];splitGroups.value.clear()}
async function handleBatchSubmit(){
  const data = buildBatchOrders()
  if (data.orders.length === 0) { ElMessage.warning('请至少分配一个供应商'); return }

  try { await validateBatchOrders(data) } catch (e: any) { ElMessage.error(e?.response?.data?.message || '校验失败'); return }

  saving.value = true
  try {
    const res = await batchCreateOrders(data)
    ElMessage.success(`成功创建 ${(res.data as any).count} 个订单`)
    creating.value = false; load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '创建失败') }
  finally { saving.value = false }
}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
