<template>
  <div class="page">
    <div class="page-header"><h2>采购需求</h2><div style="display:flex;gap:8px"><el-button type="warning" size="small" plain @click="quickFilter('1')">待审核</el-button><el-button type="warning" size="small" @click="handleMergePreview" :loading="mergeLoading">智能合并</el-button><el-button type="primary" size="small" @click="openCreate">新建需求</el-button></div></div>

    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>采购类型</label><el-select v-model="searchPctyp" size="small" style="width:130px" clearable><el-option v-for="(nm,cd) in puMap" :key="cd" :label="nm" :value="cd"/></el-select></div>
        <div class="field"><label>审批标记</label><el-select v-model="searchAuditflg" size="small" style="width:130px" clearable><el-option v-for="(nm,cd) in afMap" :key="cd" :label="nm" :value="cd"/></el-select></div>
        <div class="field"><label>计划日期</label><el-date-picker v-model="searchStartDate" type="date" size="small" style="width:130px" placeholder="开始" value-format="YYYY-MM-DD" clearable/></div>
        <div class="field"><label>至</label><el-date-picker v-model="searchEndDate" type="date" size="small" style="width:130px" placeholder="结束" value-format="YYYY-MM-DD" clearable/></div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
        <el-button size="small" @click="doReset">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDetail">
        <el-table-column prop="pcplanid" label="计划号" width="110"/>
        <el-table-column label="采购类型" width="80"><template #default="{row}">{{ puLabel(row.pctyp) }}</template></el-table-column>
        <el-table-column prop="slbillid" label="销售单号" width="110"/>
        <el-table-column label="审批状态" width="80"><template #default="{row}"><el-tag :type="row.auditflg==='2'?'success':row.auditflg==='1'?'warning':'info'" size="small">{{ afLabel(row.auditflg) }}</el-tag></template></el-table-column>
        <el-table-column label="生成时间" width="160"><template #default="{row}">{{ formatDateTime(row.gendate) }}</template></el-table-column>
        <el-table-column label="计划日期" width="110"><template #default="{row}">{{ formatDate(row.plandate) }}</template></el-table-column>
        <el-table-column label="操作员" width="80"><template #default="{row}">{{ userName(row.opercd) }}</template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
        <el-table-column label="操作" width="140" fixed="right"><template #default="{row}"><el-button v-if="row.auditflg==='0'" link type="primary" size="small" @click.stop="doSubmit(row)">送审</el-button><el-button v-if="row.auditflg==='1'" link type="warning" size="small" @click.stop="openAudit(row)">审核</el-button><el-button v-if="row.auditflg==='9' && row.useflg!=='9'" link type="primary" size="small" @click.stop="doSubmit(row)">重新送审</el-button><el-button v-if="['0','1'].includes(row.auditflg)" link type="danger" size="small" @click.stop="openVoid(row)">作废</el-button></template></el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <el-dialog :title="'需求详情 — '+(detail?.pcplanid||'')" v-model="drawer" width="800px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="计划号">{{ detail.pcplanid }}</el-descriptions-item>
          <el-descriptions-item label="采购类型">{{ puLabel(detail.pctyp as string) }}</el-descriptions-item>
          <el-descriptions-item label="销售单号">{{ detail.slbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="计划日期">{{ formatDate(detail.plandate as string) }}</el-descriptions-item>
          <el-descriptions-item label="审批状态"><el-tag :type="detail.auditflg==='2'?'success':detail.auditflg==='1'?'warning':'info'" size="small">{{ afLabel(detail.auditflg as string) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ formatDateTime(detail.gendate as string) }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ userName(detail.opercd as string) }}</el-descriptions-item>
          <el-descriptions-item label="审批人">{{ detail.auditman || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审批日期">{{ formatDateTime(detail.auditdate as string) }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo || detail.checkmemo || '-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">采购明细及执行跟踪</h4>
        <el-table :data="detail.details||[]" size="small" stripe>
          <el-table-column prop="itemcd" label="物料编码" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="200" show-overflow-tooltip/>
          <el-table-column prop="rgstqty" label="计划数量" width="70"/>
          <el-table-column prop="auditqty" label="审核数量" width="70"/>
          <el-table-column label="已下单" width="70"><template #default="{row}">{{ row.ordered_qty||0 }}</template></el-table-column>
          <el-table-column label="已入库" width="70"><template #default="{row}">{{ row.received_qty||0 }}</template></el-table-column>
          <el-table-column label="可用余额" width="80"><template #default="{row}">{{ row.available_qty||0 }}</template></el-table-column>
          <el-table-column label="执行状态" width="80"><template #default="{row}"><el-tag :type="row.execution_status==='已完成'?'success':row.execution_status==='未开始'?'info':'warning'" size="small">{{ row.execution_status||'未开始' }}</el-tag></template></el-table-column>
        </el-table>
      </template>
    </el-dialog>

    <el-dialog title="审核采购需求" v-model="auditing" width="600px" @closed="resetAudit">
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small"><el-descriptions-item label="需求单号">{{ auditTarget.pcplanid }}</el-descriptions-item><el-descriptions-item label="采购类型">{{ puLabel(auditTarget.pctyp as string) }}</el-descriptions-item></el-descriptions>
        <h4 style="margin:12px 0 8px">审核明细</h4>
        <el-table :data="auditDetailList" size="small" stripe>
          <el-table-column prop="lineno" label="行号" width="60"/>
          <el-table-column prop="itemcd" label="物料编码" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="120"/>
          <el-table-column prop="rgstqty" label="申请数量" width="80"/>
          <el-table-column label="审核数量" width="120"><template #default="{$index}"><el-input-number :model-value="auditDetailList[$index].audit_qty" @update:model-value="(v:number|null)=>setAuditQty($index,v)" :min="1" size="small" style="width:100px"/></template></el-table-column>
        </el-table>
        <el-input v-model="auditMemo" type="textarea" :rows="2" placeholder="审核备注" style="margin-top:12px"/>
      </template>
      <template #footer>
        <el-button @click="auditing=false">取消</el-button>
        <el-button type="danger" @click="doAudit('9')" :loading="auditLoading">退回</el-button>
        <el-button type="success" @click="doAudit('2')" :loading="auditLoading">审核通过</el-button>
      </template>
    </el-dialog>

    <el-dialog title="作废采购需求" v-model="voiding" width="400px">
      <template v-if="voidTarget">
        <p>确认作废需求单 <strong>{{ voidTarget.pcplanid }}</strong> 吗？</p>
        <el-input v-model="voidReason" type="textarea" :rows="2" placeholder="作废原因（可选）" style="margin-top:12px"/>
        <p style="color:#f56c6c;font-size:12px;margin-top:8px">⚠️ 作废后不可恢复，已生成订单的需求单无法作废</p>
      </template>
      <template #footer>
        <el-button @click="voiding=false">取消</el-button>
        <el-button type="danger" @click="doVoid" :loading="voidLoading">确认作废</el-button>
      </template>
    </el-dialog>

    <el-dialog title="新建采购需求" v-model="creating" width="650px" @closed="resetForm">
      <el-form :model="form" label-width="80px" size="small">
        <el-form-item label="采购类型"><el-select v-model="form.pctyp" style="width:100%"><el-option v-for="(nm,cd) in puMap" :key="cd" :label="nm" :value="cd"/></el-select></el-form-item>
        <el-form-item label="销售单号"><el-input v-model="form.slbillid" :disabled="form.pctyp==='12'" :placeholder="form.pctyp==='12'?'订单采购自动关联预计划单号':''"/></el-form-item>
        <el-form-item label="计划日期"><el-date-picker v-model="form.plandate" type="date" style="width:100%" value-format="YYYY-MM-DD"/></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.memo" type="textarea" :rows="2"/></el-form-item>
        <el-form-item label="采购明细">
          <div style="width:100%">
            <div style="margin-bottom:8px;display:flex;gap:8px">
              <el-input v-model="itemSearch" size="small" placeholder="搜索配件..." style="width:200px" clearable @input="filterTree"/>
              <el-button size="small" @click="addSelectedItems">添加选中配件</el-button>
            </div>
            <el-tree ref="treeRef" :data="partTree" node-key="class_cd" show-checkbox check-strictly :filter-node-method="filterNode" :props="{label:'class_nm',children:'children'}" style="max-height:200px;overflow:auto;border:1px solid #dcdfe6;border-radius:4px;padding:8px"/>
            <el-table v-if="formDetails.length>0" :data="formDetails" size="small" style="margin-top:8px">
              <el-table-column prop="itemcd" label="物料编码" width="100"/>
              <el-table-column prop="itemnm" label="物料名称" min-width="120"/>
              <el-table-column label="数量" width="100"><template #default="{$index}"><el-input-number v-model="formDetails[$index].rgstqty" :min="1" size="small" style="width:80px"/></template></el-table-column>
              <el-table-column label="用途" width="110"><template #default="{$index}"><el-select v-model="formDetails[$index].item_usage" size="small" style="width:100px"><el-option label="销售备货" value="sale"/><el-option label="维护消耗" value="maintenance"/><el-option label="内部使用" value="internal"/></el-select></template></el-table-column>
              <el-table-column prop="units" label="单位" width="60"/>
              <el-table-column label="操作" width="60"><template #default="{$index}"><el-button link type="danger" size="small" @click="formDetails.splice($index,1)">删除</el-button></template></el-table-column>
            </el-table>
          </div>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="creating=false">取消</el-button><el-button type="primary" @click="doCreate" :loading="saving">创建</el-button></template>
    </el-dialog>

    <el-dialog title="智能合并推荐" v-model="mergeDialogVisible" width="700px" :close-on-click-modal="false">
      <div v-if="mergeGroups.length > 0">
        <h4 style="margin-bottom:12px;">以下商品可合并采购（同类商品多个需求）</h4>
        <div v-for="g in mergeGroups" :key="g.itemcd" style="padding:10px;margin-bottom:8px;border:1px solid #e0e0e0;border-radius:6px;">
          <el-checkbox v-model="g.checked">
            <strong>{{ g.itemcd }} {{ g.itemnm }}</strong> — {{ g.source_count }}个需求单 共{{ g.total_qty }}个
          </el-checkbox>
          <div style="margin-left:24px;color:#909399;font-size:12px;">
            来源：{{ (g.source_lines || []).map((l:any) => `${l.pcplanid}(${l.qty})`).join(' + ') }}
          </div>
          <div style="margin-left:24px;margin-top:6px;">
            选择供应商：
            <el-select v-model="g.selectedSupplier" size="small" style="width:220px;" :disabled="!g.checked">
              <el-option v-for="s in g.suggested_suppliers" :key="s.supp_cd" :label="`${s.supp_nm} (¥${s.itemprice})`" :value="s.supp_cd" />
            </el-select>
          </div>
        </div>
      </div>
      <div v-if="unmergeableItems.length > 0">
        <h4 style="margin-bottom:8px;color:#909399;">以下商品无可合并（仅1个需求单）</h4>
        <div v-for="u in unmergeableItems" :key="u.itemcd" style="padding:6px;color:#909399;font-size:13px;">
          ○ {{ u.itemcd }} {{ u.itemnm }} — {{ (u.source_lines || [])[0]?.pcplanid || '-' }}
        </div>
      </div>
      <div v-if="mergeGroups.length === 0 && unmergeableItems.length === 0" style="text-align:center;color:#909399;padding:20px;">
        暂无可合并的需求单
      </div>
      <div v-if="mergeGroups.length > 0" style="margin-top:12px;padding:8px;background:#f5f5f5;border-radius:4px;text-align:right;">
        将生成 <strong>{{ mergeGroups.filter((g:any) => g.checked).length }}</strong> 个采购订单
      </div>
      <template #footer>
        <el-button @click="mergeDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="handleMergeConfirm" :disabled="mergeGroups.filter((g:any)=>g.checked).length===0">确认合并</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">import {ref,reactive,onMounted} from 'vue';import {ElMessage,ElTree} from 'element-plus';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useUserNames} from '@/composables/useUserNames';import {useDict} from '@/composables/useDict';import {fetchRequisitions,fetchRequisitionDetail,createRequisition,type ProcRecord} from '@/api/procurement';import {fetchBomClassTree,getMergePreview,batchCreateOrders} from '@/api/master';import type {ItemClassNode} from '@/api/master';import request from '@/api/request'

const{userName}=useUserNames()
const{dictMap:afMap,dictLabel:afLabel}=useDict('AF')
const{dictMap:puMap,dictLabel:puLabel}=useDict('PU')

const{items,loading,page,perPage,total,onSearch}=useListPage<ProcRecord>(fetchRequisitions)

// 智能合并
const mergeDialogVisible=ref(false)
const mergeGroups=ref<any[]>([])
const unmergeableItems=ref<any[]>([])
const mergeLoading=ref(false)

async function handleMergePreview(){
    mergeLoading.value=true
    try{
        const res=await getMergePreview()
        const d=res.data as any
        mergeGroups.value=(d.mergeable||[]).map((g:any)=>({
            ...g,
            checked:true,
            selectedSupplier:g.suggested_suppliers?.[0]?.supp_cd||''
        }))
        unmergeableItems.value=d.unmergeable||[]
        mergeDialogVisible.value=true
    }catch{ElMessage.error('加载失败')}
    finally{mergeLoading.value=false}
}

async function handleMergeConfirm(){
    const selected=mergeGroups.value.filter((g:any)=>g.checked&&g.selectedSupplier)
    if(selected.length===0){ElMessage.warning('请至少选择一个合并组并指定供应商');return}

    const orders=selected.map((g:any)=>({
        suppliercd:g.selectedSupplier,
        memo:`合并采购 — ${g.itemnm}`,
        details:g.source_lines.map((l:any)=>({
            itemcd:g.itemcd,
            rgsqty:l.qty,
            ref_pcplanid:l.pcplanid,
            ref_pclineno:l.pclineno,
        }))
    }))

    try{
        const res=await batchCreateOrders({orders})
        ElMessage.success(`成功创建 ${(res.data as any).count} 个订单`)
        mergeDialogVisible.value=false
        doSearch()
    }catch(e:any){ElMessage.error(e?.response?.data?.message||'创建失败')}
}

// 审核
const auditing=ref(false);const auditLoading=ref(false);const auditTarget=ref<ProcRecord|null>(null)
const auditMemo=ref('')
const auditDetailList=reactive<any[]>([])
function setAuditQty(index:number,val:number|null){
  const row=auditDetailList[index]
  if(!row)return
  const qty=Number(val)||0
  if(qty<1){
    ElMessage.warning('审核数量必须大于0')
    row.audit_qty=1
    return
  }
  row.audit_qty=qty
}
async function openAudit(row:ProcRecord){
  auditTarget.value=row;auditMemo.value=''
  auditDetailList.splice(0,auditDetailList.length)
  try{const r=await fetchRequisitionDetail(row.pcplanid as string);auditTarget.value=r.data}catch{/* use row data */}
  if(auditTarget.value?.details){
    for(const d of auditTarget.value.details as any[]){
      auditDetailList.push({...d,audit_qty:Number(d.rgstqty)||0})
    }
    console.log('[openAudit] auditDetailList=',JSON.stringify(auditDetailList))
  }
  auditing.value=true
}
async function doSubmit(row:ProcRecord){
  try{await request.post('/procurement/requisitions/'+row.pcplanid+'/audit',{auditflg:'1'});ElMessage.success('已送审');doSearch()}catch(e:any){ElMessage.error(e?.response?.data?.message||'送审失败')}
}
async function doAudit(flg:string){
  auditLoading.value=true
  try{
    const details=auditDetailList.map((d:any)=>({lineno:Number(d.lineno),auditqty:Number(d.audit_qty)||0}))
    const invalid=details.find(d=>d.auditqty<1)
    if(invalid){ElMessage.warning('审核数量必须大于0');return}
    console.log('[doAudit] 提交details=',JSON.stringify(details))
    await request.post('/procurement/requisitions/'+auditTarget.value!.pcplanid+'/audit',{auditflg:flg,checkmemo:auditMemo.value,details})
    ElMessage.success(flg==='2'?'审核通过':'已退回');auditing.value=false;doSearch()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'审核失败')}finally{auditLoading.value=false}
}
function resetAudit(){
  auditTarget.value=null;auditMemo.value=''
  auditDetailList.splice(0,auditDetailList.length)
}

// 作废
const voiding=ref(false);const voidTarget=ref<ProcRecord|null>(null);const voidReason=ref('');const voidLoading=ref(false)
function openVoid(row:ProcRecord){voidTarget.value=row;voidReason.value='';voiding.value=true}
async function doVoid(){
  if(!voidTarget.value)return
  voidLoading.value=true
  try{
    await request.post('/procurement/requisitions/'+voidTarget.value.pcplanid+'/void',{reason:voidReason.value})
    ElMessage.success('作废成功');voiding.value=false;doSearch()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'作废失败')}finally{voidLoading.value=false}
}

// 筛选条件
const searchPctyp=ref('');const searchAuditflg=ref('');const searchStartDate=ref('');const searchEndDate=ref('')
function doSearch(){const p:Record<string,string>={};if(searchPctyp.value)p.pctyp=searchPctyp.value;if(searchAuditflg.value)p.auditflg=searchAuditflg.value;if(searchStartDate.value)p.start_date=searchStartDate.value;if(searchEndDate.value)p.end_date=searchEndDate.value;onSearch(p)}
function doReset(){searchPctyp.value='';searchAuditflg.value='';searchStartDate.value='';searchEndDate.value='';onSearch({})}
function quickFilter(flg:string){searchAuditflg.value=flg;doSearch()}

// 详情
const drawer=ref(false);const detail=ref<ProcRecord|null>(null)
async function openDetail(row:ProcRecord){drawer.value=true;try{const r=await fetchRequisitionDetail(row.pcplanid as string);detail.value=r.data}catch{detail.value=row}}

// 新建 — 配件树（typflg='0' = 仅配件）
const creating=ref(false);const saving=ref(false)
const form=reactive({pctyp:'10',slbillid:'',plandate:'',memo:''})
const formDetails=reactive<{itemcd:string;itemnm:string;rgstqty:number;units:string;item_usage:string}[]>([])
const partTree=ref<ItemClassNode[]>([])
const treeRef=ref<InstanceType<typeof ElTree>>()
const itemSearch=ref('')

onMounted(async()=>{try{const r=await fetchBomClassTree('0');partTree.value=r.data||[]}catch{}})

function filterNode(value:string,data:any){if(!value)return true;return (data.class_nm||'').toLowerCase().includes(value.toLowerCase())}
function formatDateTime(val:string|undefined){if(!val)return'-';const s=val.replace('T',' ');if(s.includes('.')){return s.split('.')[0]}return s}
function formatDate(val:string|undefined){if(!val)return'-';return val.split('T')[0]}
function filterTree(){if(treeRef.value)(treeRef.value as any).filter(itemSearch.value)}

function addSelectedItems(){
  const nodes=(treeRef.value as any)?.getCheckedNodes(false)||[]
  for(const node of nodes){
    if(!node.children||node.children.length===0){
      if(!formDetails.find(d=>d.itemcd===node.class_cd)){
        formDetails.push({itemcd:node.class_cd,itemnm:node.class_nm,rgstqty:1,units:'',item_usage:'sale'})
      }
    }
  }
}

function openCreate(){creating.value=true}
function resetForm(){form.pctyp='10';form.slbillid='';form.plandate='';form.memo='';formDetails.length=0}
async function doCreate(){
  if(formDetails.length===0){ElMessage.warning('请至少添加一条采购明细');return}
  const invalid=formDetails.find(d=>!d.itemcd||d.rgstqty==null||Number(d.rgstqty)<1)
  if(invalid){ElMessage.warning('物料编码和数量为必填项，数量不能小于1');return}
  saving.value=true
  try{
    await createRequisition({...form,details:formDetails.map(d=>({itemcd:d.itemcd,rgstqty:d.rgstqty,units:d.units,item_usage:d.item_usage}))})
    ElMessage.success('创建成功');creating.value=false;doSearch()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'创建失败')}finally{saving.value=false}
}
</script>
<style scoped>
.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}
.search-bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.search-bar .field{display:flex;align-items:center;gap:6px}.search-bar .field label{font-size:13px;color:#606266;white-space:nowrap}
</style>
