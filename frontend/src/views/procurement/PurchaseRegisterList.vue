<template>
  <div class="page">
    <div class="page-header"><h2>采购订单</h2><div style="display:flex;gap:8px"><el-button type="warning" size="small" plain @click="quickFilter('1')">待审核</el-button><el-button type="success" size="small" @click="handleMergePreview" :loading="mergeLoading">智能合并</el-button><el-button type="primary" size="small" @click="openCreate">新建订单</el-button></div></div>

    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>订单号</label><el-input v-model="searchRgstbillid" size="small" style="width:130px" clearable placeholder="模糊搜索" @keyup.enter="doSearch" @clear="doSearch"/></div>
        <div class="field"><label>需求号</label><el-input v-model="searchRefPcplanid" size="small" style="width:130px" clearable placeholder="模糊搜索" @keyup.enter="doSearch" @clear="doSearch"/></div>
        <div class="field"><label>审批状态</label><el-select v-model="searchAuditflg" size="small" style="width:130px" clearable @change="doSearch"><el-option v-for="(nm,cd) in afMap" :key="cd" :label="nm" :value="cd"/></el-select></div>
        <div class="field"><label>执行状态</label><el-select v-model="searchExecStatus" size="small" style="width:130px" clearable @change="doSearch"><el-option label="未入库" value="未入库"/><el-option label="部分入库" value="部分入库"/><el-option label="已完成" value="已完成"/></el-select></div>
        <el-button size="small" @click="searchShowVoided = !searchShowVoided; doSearch()" :type="searchShowVoided ? 'danger' : ''">{{ searchShowVoided ? '返回正常单据' : '作废单据' }}</el-button>
        <el-button size="small" @click="doReset" style="margin-left:auto">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open">
        <el-table-column prop="rgstbillid" label="订单号" width="110"/>
        <el-table-column prop="ref_pcplanids" label="需求号" width="140" show-overflow-tooltip/>
        <el-table-column label="采购员" width="80"><template #default="{row}">{{ userName(row.pcrep) }}</template></el-table-column>
        <el-table-column prop="rgstamt" label="金额" width="100" align="right"/>
        <el-table-column label="审批" width="80"><template #default="{row}"><el-tag v-if="row.useflg==='9'" type="danger" size="small">已作废</el-tag><el-tag v-else :type="row.auditflg==='2'?'success':'warning'" size="small">{{ afLabel(row.auditflg) }}</el-tag></template></el-table-column>
        <el-table-column label="执行状态" width="80"><template #default="{row}"><el-tag :type="row.execution_status==='已完成'?'success':row.execution_status==='未入库'?'info':'warning'" size="small">{{ row.execution_status||'未入库' }}</el-tag></template></el-table-column>
        <el-table-column label="日期" width="150"><template #default="{row}">{{ formatDate(row.gendate) }}</template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
        <el-table-column label="操作员" width="80"><template #default="{row}">{{ userName(row.opercd) }}</template></el-table-column>
        <el-table-column label="操作" width="160" fixed="right"><template #default="{row}">
          <template v-if="row.useflg!=='9'">
            <el-button v-if="row.auditflg==='0'" link type="primary" size="small" @click.stop="doSubmit(row)">送审</el-button>
            <el-button v-if="row.auditflg==='1'" link type="warning" size="small" @click.stop="openAudit(row)">审核</el-button>
            <el-button v-if="row.auditflg==='9'" link type="primary" size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button v-if="row.auditflg==='9'" link type="primary" size="small" @click.stop="doSubmit(row)">重新送审</el-button>
            <el-button v-if="['0','9'].includes(row.auditflg)" link type="danger" size="small" @click.stop="openVoid(row)">作废</el-button>
          </template>
        </template></el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <el-dialog :title="'采购订单 — '+(detail?.rgstbillid||'')" v-model="drawer" width="820px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="订单号">{{ detail.rgstbillid }}</el-descriptions-item>
          <el-descriptions-item label="采购员">{{ userName(detail.pcrep as string) }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ (detail as any).supp_nm||detail.suppliercd||'-' }}</el-descriptions-item>
          <el-descriptions-item label="审批人">{{ detail.auditman||'-' }}</el-descriptions-item>
          <el-descriptions-item label="金额">{{ detail.rgstamt||'-' }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ formatDate(detail.gendate as string) }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo||'-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">采购明细</h4>
        <el-table :data="(detail.details as any[])||[]" size="small" stripe>
          <el-table-column prop="lineno" label="行号" width="60"/>
          <el-table-column prop="itemcd" label="物料编码" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="150" show-overflow-tooltip/>
          <el-table-column prop="rgsqty" label="采购数量" width="80" align="right"/>
          <el-table-column label="审核数量" width="80" align="right"><template #default="{row}">{{ (row.auditqty > 0) ? row.auditqty : '-' }}</template></el-table-column>
          <el-table-column prop="rgstprice" label="单价" width="90" align="right"/>
          <el-table-column prop="units" label="单位" width="60"/>
          <el-table-column label="来源需求单" min-width="120"><template #default="{row}"><span v-if="row.ref_pcplanid" style="color:#409eff;font-size:12px">{{ row.ref_pcplanid }}-{{ row.ref_pclineno }}</span><span v-else style="color:#c0c4cc">-</span></template></el-table-column>
        </el-table>
      </template>
    </el-dialog>

    <el-dialog title="审核采购订单" v-model="auditing" width="600px" @closed="auditTarget=null;auditMemo=''">
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small"><el-descriptions-item label="订单号">{{ auditTarget.rgstbillid }}</el-descriptions-item><el-descriptions-item label="供应商">{{ (auditTarget as any).supp_nm||auditTarget.suppliercd||'-' }}</el-descriptions-item></el-descriptions>
        <h4 style="margin:12px 0 8px">审核明细</h4>
        <el-table :data="auditTarget.details||[]" size="small" stripe>
          <el-table-column prop="lineno" label="行号" width="60"/>
          <el-table-column prop="itemcd" label="物料编码" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="150" show-overflow-tooltip/>
          <el-table-column prop="rgsqty" label="采购数量" width="80" align="right"/>
<el-table-column label="审核数量" width="100" align="right"><template #default="{row}"><el-input-number v-model="row.auditqty" :min="0" :max="row.rgsqty" size="small" controls-position="right" style="width:90px"/></template></el-table-column>
          <el-table-column prop="rgstprice" label="单价" width="80" align="right"/>
          <el-table-column prop="units" label="单位" width="60"/>
        </el-table>
        <el-input v-model="auditMemo" type="textarea" :rows="2" placeholder="审核备注" style="margin-top:12px"/>
      </template>
      <template #footer>
        <el-button @click="auditing=false">取消</el-button>
        <el-button type="danger" @click="doAudit('9')" :loading="auditLoading">退回</el-button>
        <el-button type="success" @click="doAudit('2')" :loading="auditLoading">审核通过</el-button>
      </template>
    </el-dialog>

    <el-dialog title="作废采购订单" v-model="voiding" width="400px">
      <template v-if="voidTarget">
        <p>确认作废订单 <strong>{{ voidTarget.rgstbillid }}</strong> 吗？关联的需求余额将被释放。</p>
      </template>
      <template #footer>
        <el-button @click="voiding=false">取消</el-button>
        <el-button type="danger" @click="doVoid" :loading="voidLoading">确认作废</el-button>
      </template>
    </el-dialog>

    <el-dialog title="编辑采购订单" v-model="editing" width="700px" @closed="editTarget=null;editDetails.length=0">
      <template v-if="editTarget">
        <el-descriptions :column="2" border size="small"><el-descriptions-item label="订单号">{{ editTarget.rgstbillid }}</el-descriptions-item></el-descriptions>
        <el-form :model="editForm" label-width="80px" size="small" style="margin-top:12px">
          <el-form-item label="供应商"><el-input v-model="editForm.suppliercd" disabled/></el-form-item>
          <el-form-item label="采购员"><el-input v-model="editForm.pcrep"/></el-form-item>
          <el-form-item label="备注"><el-input v-model="editForm.memo" type="textarea" :rows="2"/></el-form-item>
        </el-form>
        <h4 style="margin:12px 0 8px">明细（数量可调减，不可调增）</h4>
        <el-table :data="editDetails" size="small" stripe>
          <el-table-column prop="lineno" label="行号" width="60"/>
          <el-table-column prop="itemcd" label="物料编码" width="100"/>
          <el-table-column prop="itemnm" label="物料名称" min-width="120"/>
          <el-table-column label="数量" width="120"><template #default="{$index}"><el-input-number v-model="editDetails[$index].rgsqty" :min="1" :max="editDetails[$index]._origQty" size="small" style="width:100px" @change="(v:number|undefined)=>onEditQtyChange($index, v||1)"/></template></el-table-column>
          <el-table-column label="审核数量" width="80" align="right"><template #default="{row}">{{ (row.auditqty > 0) ? row.auditqty : '-' }}</template></el-table-column>
          <el-table-column label="单价" width="140"><template #default="{$index}"><el-input-number v-model="editDetails[$index].rgstprice" :min="0" :precision="2" size="small" style="width:130px" @change="(v:number|undefined)=>onEditPriceChange($index, v||0)"/></template></el-table-column>
          <el-table-column prop="units" label="单位" width="60"/>
        </el-table>
      </template>
      <template #footer>
        <el-button @click="editing=false">取消</el-button>
        <el-button type="primary" @click="handleEditSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog title="新建采购订单" v-model="creating" width="900px" @closed="resetForm">
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
        <el-form-item label="采购员"><el-input :model-value="userName(form.pcrep||'admin')" disabled placeholder="当前登录用户"/></el-form-item>
        <el-form-item label="下单日期"><el-date-picker v-model="form.rgstdate" type="date" style="width:100%" value-format="YYYY-MM-DD"/></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.memo" type="textarea" :rows="2"/></el-form-item>
        <!-- 步骤3：加载商品（根据需求单+供应商） -->
        <el-form-item label="采购明细">
          <div style="width:100%">
            <el-alert v-if="!form.suppliercd" title="请先选择供应商" type="info" :closable="false" show-icon style="margin-bottom:8px"/>
            <el-table v-if="formDetails.length>0" :data="formDetails" size="small" style="margin-top:8px">
              <el-table-column prop="itemcd" label="物料编码" width="90"/>
              <el-table-column prop="itemnm" label="物料名称" min-width="100"/>
              <el-table-column prop="ref_pcplanid" label="来源需求" width="90"/>
              <el-table-column label="数量" width="110"><template #default="{$index}"><el-input-number v-model="formDetails[$index].rgsqty" :min="1" size="small" style="width:100px" @change="onQtyChangeFd($index)"/></template></el-table-column>
              <el-table-column label="单价" width="140"><template #default="{$index}"><el-input-number v-model="formDetails[$index].rgstprice" :min="0" :precision="2" size="small" style="width:130px" @change="(v:number|undefined)=>onPriceChangeFd($index, v||0)"/></template></el-table-column>
              <el-table-column label="拆单" width="70"><template #default="{row}"><el-button v-if="!isSplit(detailKey(row))" link type="warning" size="small" @click="handleSplit(row)">拆单</el-button></template></el-table-column>
              <el-table-column label="操作" width="60"><template #default="{row,$index}"><el-button link type="danger" size="small" @click="removeFormDetail($index,row)">删除</el-button></template></el-table-column>
            </el-table>
            <!-- 拆分子行 -->
            <template v-for="row in formDetails" :key="detailKey(row)">
              <template v-if="isSplit(detailKey(row))">
                <div v-for="line in getSplitLines(detailKey(row))" :key="line.id" style="padding:4px 0 4px 24px;display:flex;gap:8px;align-items:center;background:#fafafa;">
                  <span style="font-size:12px;color:#909399;white-space:nowrap;">├ 拆分: {{ row.itemnm }}</span>
                  <el-input-number v-model="line.rgsqty" :min="1" size="small" style="width:100px;" controls-position="right" @change="async (v:number|undefined)=>{if(v&&v>0)line.unitprice=await resolveSplitPrice(line.itemcd,line.suppliercd||form.suppliercd,v)}" />
                  <el-select v-model="line.suppliercd" size="small" style="width:160px;" placeholder="选择供应商" filterable @change="async (v:string)=>{if(v)line.unitprice=await resolveSplitPrice(line.itemcd,v,line.rgsqty||1)}">
                    <el-option v-for="s in (itemSuppliersMap.get(line.itemcd) || [])" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd" />
                  </el-select>
                  <el-input-number v-model="line.unitprice" :min="0" :precision="2" size="small" style="width:100px;" controls-position="right" placeholder="单价" @change="(v:number|undefined)=>onPriceChange({_resolvedPrice:line._resolvedPrice||line.unitprice,_priceSource:'系统解析'},v||0)"/>
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
        <el-button @click="handleMergePreview" :loading="mergeLoading" plain>刷新数据</el-button>
        <el-button type="primary" @click="handleMergeConfirm" :disabled="mergeGroups.filter((g:any)=>g.checked).length===0">确认合并</el-button>
      </template>
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
<script setup lang="ts">import {ref,reactive,watch} from 'vue';import {ElMessage,ElMessageBox} from 'element-plus';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {useUserNames} from '@/composables/useUserNames';import {useDict} from '@/composables/useDict';import {fetchOrders,fetchAvailableItems,fetchRequisitions,fetchOrderDetail} from '@/api/procurement';import type {ProcRecord} from '@/api/procurement';import {fetchSuppliersByRequisition,fetchItemSuppliers,batchCreateOrders,validateBatchOrders,fetchPriceResolve,getMergePreview} from '@/api/master';import request from '@/api/request'

const{userName}=useUserNames()
const{dictLabel:afLabel,dictMap:afMap}=useDict('AF')
const{dictLabel:puLabel}=useDict('PU')
const{items,loading,page,perPage,total,load,onSearch}=useListPage<ProcRecord>(fetchOrders)
const{drawer,detail}=useDetailDrawer<ProcRecord>()
async function open(row:ProcRecord){
  drawer.value=true
  try{const r=await fetchOrderDetail(row.rgstbillid as string);detail.value=r.data}catch{detail.value=row}
}

function quickFilter(flg:string){onSearch({auditflg:flg})}

const searchRgstbillid = ref('')
const searchRefPcplanid = ref('')
const searchAuditflg = ref('')
const searchExecStatus = ref('')
const searchShowVoided = ref(false)
function doSearch() {
  const p: Record<string,string> = {}
  if (searchRgstbillid.value) p.rgstbillid = searchRgstbillid.value
  if (searchRefPcplanid.value) p.ref_pcplanid = searchRefPcplanid.value
  if (searchAuditflg.value) p.auditflg = searchAuditflg.value
  if (searchExecStatus.value) p.execution_status = searchExecStatus.value
  if (searchShowVoided.value) p.show_voided = 'true'
  onSearch(p)
}
function doReset() {
  searchRgstbillid.value = ''
  searchRefPcplanid.value = ''
  searchAuditflg.value = ''
  searchExecStatus.value = ''
  searchShowVoided.value = false
  onSearch({})
}

// 审核
const auditing=ref(false);const auditLoading=ref(false);const auditTarget=ref<ProcRecord|null>(null)
const auditMemo=ref('')
async function openAudit(row:ProcRecord){
  auditTarget.value=row;auditMemo.value=''
  try{const r=await fetchOrderDetail(row.rgstbillid as string);auditTarget.value=r.data}catch{/* use row */}
  // 审核数量默认填充采购数量（后端返回的auditqty=0时）
  const details = (auditTarget.value as any)?.details || []
  details.forEach((d: any) => { if (!d.auditqty || d.auditqty <= 0) d.auditqty = d.rgsqty || 0 })
  auditing.value=true
}
async function doSubmit(row:ProcRecord){
  try{await request.post('/procurement/orders/'+row.rgstbillid+'/audit',{auditflg:'1'});ElMessage.success('已送审');load()}catch(e:any){ElMessage.error(e?.response?.data?.message||'送审失败')}
}
async function doAudit(flg:string){
  auditLoading.value=true
  try{
    await request.post('/procurement/orders/'+auditTarget.value!.rgstbillid+'/audit',{auditflg:flg,checkmemo:auditMemo.value})
    ElMessage.success(flg==='2'?'审核通过':'已退回');auditing.value=false;load()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'审核失败')}finally{auditLoading.value=false}
}

// 作废
const voiding = ref(false); const voidTarget = ref<ProcRecord|null>(null); const voidLoading = ref(false)
function openVoid(row: ProcRecord) { voidTarget.value = row; voiding.value = true }
async function doVoid() {
  if (!voidTarget.value) return
  voidLoading.value = true
  try {
    await request.post('/procurement/orders/' + voidTarget.value.rgstbillid + '/void')
    ElMessage.success('作废成功'); voiding.value = false; load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '作废失败') }
  finally { voidLoading.value = false }
}

// 编辑驳回订单
const editing = ref(false); const editTarget = ref<ProcRecord|null>(null)
const editForm = reactive({suppliercd:'', pcrep:'', rgstdate:'', memo:''})
const editDetails = reactive<{lineno:number; itemcd:string; itemnm:string; rgsqty:number; auditqty:number; _origQty:number; _origPrice:number; rgstprice:number; units:string}[]>([])

async function openEdit(row: ProcRecord) {
  editTarget.value = row
  try {
    const r = await fetchOrderDetail(row.rgstbillid as string)
    const d = r.data as any
    editForm.suppliercd = d.suppliercd || ''
    editForm.pcrep = d.pcrep || ''
    editForm.rgstdate = d.rgstdate || ''
    editForm.memo = d.memo || ''
    editDetails.length = 0
    if (d.details) {
      for (const dt of d.details) {
        editDetails.push({
          lineno: dt.lineno,
          itemcd: dt.itemcd,
          itemnm: dt.item_nm || dt.itemcd,
          rgsqty: Number(dt.rgsqty) || 0,
          auditqty: Number(dt.auditqty) || 0,
          _origQty: Number(dt.rgsqty) || 0,
          rgstprice: Number(dt.rgstprice) || 0,
          _origPrice: Number(dt.rgstprice) || 0,
          units: dt.units || ''
        })
      }
    }
    editing.value = true
  } catch { ElMessage.error('加载订单详情失败') }
}

async function handleEditSave() {
  // 价格偏离检查：用动态解析价（供应商报价>标准采购价）做基准
  const warnings: string[] = []
  for (const d of editDetails) {
    if (!d.rgstprice || d.rgstprice <= 0) continue
    try {
      const pr = await fetchPriceResolve(d.itemcd, editForm.suppliercd, d.rgsqty || 1)
      const refPrice = (pr as any).data?.price
      if (refPrice && refPrice > 0) {
        const pct = Math.abs(d.rgstprice - refPrice) / refPrice * 100
        if (pct > 20) warnings.push(`${d.itemcd} 单价¥${d.rgstprice} 偏离参考价¥${refPrice}(${(pr as any).data.source_name}) ${pct.toFixed(0)}%`)
      }
    } catch { /* skip */ }
  }
  if (warnings.length > 0) {
    try {
      await ElMessageBox.confirm(warnings.join('<br>') + '<br><br>确认继续保存？', '价格偏离警告', { type: 'warning', dangerouslyUseHTMLString: true, confirmButtonText: '确认保存', cancelButtonText: '取消' })
    } catch { return }
  }
  try {
    await request.put('/procurement/orders/' + editTarget.value!.rgstbillid, {
      suppliercd: editForm.suppliercd,
      pcrep: editForm.pcrep,
      rgstdate: editForm.rgstdate,
      memo: editForm.memo,
      details: editDetails.map(d => ({ lineno: d.lineno, rgsqty: d.rgsqty, rgstprice: d.rgstprice }))
    })
    ElMessage.success('修改成功，已重置为未送审状态')
    editing.value = false
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '修改失败') }
}

// 新建 — 从可用商品选择（关联来源需求单）
const creating=ref(false);const saving=ref(false)
const today=()=>new Date().toISOString().split('T')[0]
const form=reactive({suppliercd:'',pcrep:'',rgstdate:today(),memo:'',ref_pcplanid:'',ref_pclineno:0})
const formDetails=reactive<{itemcd:string;itemnm:string;rgsqty:number;rgstprice:number;units:string;ref_pcplanid:string;ref_pclineno:number;_resolvedPrice?:number}[]>([])

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
  _resolvedPrice?: number
  _priceSource?: string
}
const splitGroups = ref<Map<string, SplitLine[]>>(new Map())
const itemSuppliersMap = ref<Map<string, {supp_cd:string;supp_nm:string}[]>>(new Map())
function generateId() { return Date.now().toString(36) + Math.random().toString(36).slice(2) }
function detailKey(row: Record<string,any>) { return `${row.ref_pcplanid}_${row.ref_pclineno}_${row.itemcd}` }
function isSplit(key: string): boolean { const lines = splitGroups.value.get(key); return !!lines && lines.length > 1 }
function getSplitLines(key: string): SplitLine[] { return splitGroups.value.get(key) || [] }
async function resolveSplitPrice(itemcd: string, suppliercd: string, qty: number): Promise<number> {
  if(!suppliercd||qty<=0)return 0
  try{const pr=await fetchPriceResolve(itemcd,suppliercd,qty);return (pr as any).data?.price||0}catch{return 0}
}
async function handleSplit(detail: Record<string,any>) {
  const key = detailKey(detail)
  if (splitGroups.value.has(key)) return
  const total = (Number(detail.rgsqty) || 0)
  if (total <= 0) return
  const half1 = Math.ceil(total / 2)
  const half2 = total - half1
  const suppCd = form.suppliercd
  // 加载该物料专属供应商
  if (!itemSuppliersMap.value.has(detail.itemcd)) {
    try {
      const r = await fetchItemSuppliers(detail.itemcd)
      itemSuppliersMap.value.set(detail.itemcd, (r.data || []).map((s: any) => ({ supp_cd: s.custcd || s.supp_cd, supp_nm: s.supp_nm })))
    } catch { itemSuppliersMap.value.set(detail.itemcd, []) }
  }
  const [p1, p2] = await Promise.all([
    resolveSplitPrice(detail.itemcd, suppCd, half1),
    resolveSplitPrice(detail.itemcd, suppCd, half2)
  ])
  splitGroups.value.set(key, [
    { id: generateId(), suppliercd: suppCd, suppliernm: '', rgsqty: half1, unitprice: p1, ref_pcplanid: detail.ref_pcplanid, ref_pclineno: detail.ref_pclineno, itemcd: detail.itemcd },
    { id: generateId(), suppliercd: suppCd, suppliernm: '', rgsqty: half2, unitprice: p2, ref_pcplanid: detail.ref_pcplanid, ref_pclineno: detail.ref_pclineno, itemcd: detail.itemcd },
  ])
}
async function addSplitLine(key: string) {
  const lines = splitGroups.value.get(key)
  if (!lines || lines.length === 0) return
  const first = lines[0]
  const suppCd = form.suppliercd
  // 确保物料供应商已加载
  if (!itemSuppliersMap.value.has(first.itemcd)) {
    try {
      const r = await fetchItemSuppliers(first.itemcd)
      itemSuppliersMap.value.set(first.itemcd, (r.data || []).map((s: any) => ({ supp_cd: s.custcd || s.supp_cd, supp_nm: s.supp_nm })))
    } catch { itemSuppliersMap.value.set(first.itemcd, []) }
  }
  const price = await resolveSplitPrice(first.itemcd, suppCd, 1)
  lines.push({ id: generateId(), suppliercd: suppCd, suppliernm: '', rgsqty: 0, unitprice: price, ref_pcplanid: first.ref_pcplanid, ref_pclineno: first.ref_pclineno, itemcd: first.itemcd })
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

function formatDate(val:string|undefined){if(!val)return'-';return val.replace('T',' ').substring(0,19)}

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
    mergeGroups.value=(d.mergeable||[]).map((g:any)=>({...g,checked:true,selectedSupplier:g.suggested_suppliers?.[0]?.supp_cd||''}))
    unmergeableItems.value=d.unmergeable||[]
    mergeDialogVisible.value=true
  }catch{ElMessage.error('加载失败')}
  finally{mergeLoading.value=false}
}
async function handleMergeConfirm(){
  const selected=mergeGroups.value.filter((g:any)=>g.checked&&g.selectedSupplier)
  if(selected.length===0){ElMessage.warning('请至少选择一个合并组并指定供应商');return}
  const priceCache:Record<string,number|null>={}
  await Promise.all(selected.map(async(g:any)=>{
    const cacheKey=`${g.itemcd}__${g.selectedSupplier}`
    if(priceCache[cacheKey]!==undefined)return
    try{
      const pr=await request.get('/prices/resolve',{params:{itemcd:g.itemcd,supp_cd:g.selectedSupplier,qty:g.total_qty||1}})
      priceCache[cacheKey]=(pr as any).data?.price??null
    }catch{priceCache[cacheKey]=null}
  }))
  const orders=selected.map((g:any)=>({
    suppliercd:g.selectedSupplier,
    memo:`合并采购 — ${g.itemnm}`,
    details:g.source_lines.map((l:any)=>({
      itemcd:g.itemcd,rgsqty:l.qty,ref_pcplanid:l.pcplanid,ref_pclineno:l.pclineno,
      unitprice:priceCache[`${g.itemcd}__${g.selectedSupplier}`]??undefined,
    }))
  }))
  try{
    const res=await batchCreateOrders({orders})
    ElMessage.success(`成功创建 ${(res.data as any).count} 个订单`)
    mergeDialogVisible.value=false;load()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'创建失败')}
}

// 打开需求单选择弹窗
async function openReqSelector(){
  reqLoading.value=true;reqSelectorOpen.value=true
  try{
    const r=await fetchRequisitions({auditflg:'2',per_page:'100',exclude_completed:'true',hide_unavailable:'true'})
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
  formDetails.length=0
  availItems.value=[]
  splitGroups.value.clear()
  itemSuppliersMap.value.clear()
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
    // 只保留来自所选需求单的商品，数量取该需求单行的审核余额
    items=items.filter((it:any)=>{
      const pd=it.plan_details;if(!pd)return false
      if(typeof pd==='string')return pd.includes(form.ref_pcplanid)
      return Array.isArray(pd)&&pd.some((p:any)=>p.pcplanid===form.ref_pcplanid)
    })
    for(const it of items){
      // 取当前需求单行的审核可用数量，而非全局汇总
      let lineQty=0;const pd=it.plan_details
      if(Array.isArray(pd)){
        const m=pd.find((p:any)=>p.pcplanid===form.ref_pcplanid)
        if(m)lineQty=Number(m.available_qty)||0
      }
      it._qty=lineQty;it._price=0;it._priceSource=''
      // 先解析价格再显示
      try{
        const pr=await fetchPriceResolve(it.itemcd, form.suppliercd, 1)
        if((pr as any).data?.price){
          it._price = (pr as any).data.price
          it._resolvedPrice = (pr as any).data.price
          it._priceSource = (pr as any).data.source_name
        }
      }catch(e:any){console.warn('价格解析失败',it.itemcd,e?.message||e)}
    }
    availItems.value=items
    // 自动添加到采购明细（先清空旧数据）
    formDetails.length=0
    addAvailItems()
    if(items.length===0){
      ElMessage.info('该供应商无匹配的可采购商品')
    }
  }catch{ElMessage.error('加载可采购商品失败')}finally{availLoading.value=false}
}

function onPriceChange(row: any, newPrice: number){
  const refPrice = row._resolvedPrice
  if(!refPrice||refPrice<=0||newPrice<=0)return
  const pct = Math.abs(newPrice - refPrice) / refPrice * 100
  if(pct > 20){
    ElMessage.warning(`单价 ¥${newPrice} 与参考价 ¥${refPrice}(${row._priceSource||'系统解析'}) 偏差 ${pct.toFixed(0)}%，请确认`)
  }
}
async function onEditQtyChange(index: number, qty: number){
  const d=editDetails[index];if(!d||qty<=0)return
  try{
    const pr=await fetchPriceResolve(d.itemcd, editForm.suppliercd, qty)
    if((pr as any).data?.price){
      d.rgstprice=(pr as any).data.price;(d as any)._origPrice=(pr as any).data.price
    }
  }catch(e:any){console.warn('价格重查失败',d.itemcd,e?.message)}
}
async function onEditPriceChange(index: number, newPrice: number){
  const d=editDetails[index] as any
  if(!d||newPrice<=0)return
  try{
    const pr=await fetchPriceResolve(d.itemcd, editForm.suppliercd, d.rgsqty||1)
    const refPrice=(pr as any).data?.price
    if(refPrice&&refPrice>0){
      const pct=Math.abs(newPrice-refPrice)/refPrice*100
      if(pct>20)ElMessage.warning(`单价 ¥${newPrice} 与参考价 ¥${refPrice}(${(pr as any).data.source_name}) 偏差 ${pct.toFixed(0)}%，请确认`)
    }
  }catch{/* skip */}
}
function onPriceChangeFd(index: number, newPrice: number){
  const d=formDetails[index] as any
  const refPrice=d._resolvedPrice
  if(!refPrice||refPrice<=0||newPrice<=0)return
  const pct=Math.abs(newPrice-refPrice)/refPrice*100
  if(pct>20)ElMessage.warning(`单价 ¥${newPrice} 与参考价 ¥${refPrice} 偏差 ${pct.toFixed(0)}%，请确认`)
}
async function onQtyChangeFd(index: number){
  const d = formDetails[index]
  if(!d||!form.suppliercd||d.rgsqty<=0)return
  try{
    const pr=await fetchPriceResolve(d.itemcd, form.suppliercd, d.rgsqty)
    if((pr as any).data?.price){
      d.rgstprice = (pr as any).data.price
      ;(d as any)._resolvedPrice = (pr as any).data.price
    }
  }catch(e:any){console.warn('价格重查失败',d.itemcd,e?.message)}
}

function addAvailItems(){
  for(const it of availItems.value){
    if(it._qty>0){
      let pd:any=it.plan_details
      if(typeof pd==='string')pd=JSON.parse(pd||'[{}]')
      // 取当前选中需求单的行，而非第一条
      if(Array.isArray(pd))pd=pd.find((p:any)=>p.pcplanid===form.ref_pcplanid)||pd[0]||{}
      formDetails.push({
        itemcd:it.itemcd,itemnm:it.itemnm,
        rgsqty:it._qty,rgstprice:it._price||0,_resolvedPrice:it._price||0,
        units:it.wunit||'',
        ref_pcplanid:pd.pcplanid||'',ref_pclineno:pd.pclineno||0
      })
    }
  }
}

function openCreate(){creating.value=true}
// 选择供应商后自动加载可采购商品
watch(()=>form.suppliercd,(val)=>{if(val&&form.ref_pcplanid)loadAvailableItems()})

function resetForm(){form.suppliercd='';form.pcrep='';form.rgstdate=today();form.memo='';form.ref_pcplanid='';form.ref_pclineno=0;formDetails.length=0;availItems.value=[];selectedReqName.value='';filteredSuppliers.value=[];splitGroups.value.clear();itemSuppliersMap.value.clear()}
async function handleBatchSubmit(){
  if (formDetails.length === 0 || formDetails.every(d => !d.rgsqty || d.rgsqty <= 0)) {
    ElMessage.warning('请添加采购明细并设置数量'); return
  }
  if (formDetails.some(d => d.rgsqty > 0 && !d.rgstprice)) {
    ElMessage.warning('采购明细中存在未填写单价的商品，请补充单价'); return
  }
  // 价格偏离检查
  const warnings: string[] = []
  for (const d of formDetails) {
    const ref = (d as any)._resolvedPrice
    if (ref && ref > 0 && d.rgstprice && d.rgstprice > 0) {
      const pct = Math.abs(d.rgstprice - ref) / ref * 100
      if (pct > 20) warnings.push(`${d.itemcd} 单价¥${d.rgstprice} 偏离参考价¥${ref} ${pct.toFixed(0)}%`)
    }
  }
  if (warnings.length > 0) {
    try {
      await ElMessageBox.confirm(warnings.join('<br>') + '<br><br>确认继续保存？', '价格偏离警告', { type: 'warning', dangerouslyUseHTMLString: true, confirmButtonText: '确认保存', cancelButtonText: '取消' })
    } catch { return }
  }
  const data = buildBatchOrders()
  if (data.orders.length === 0) { ElMessage.warning('请至少分配一个供应商'); return }

  try { await validateBatchOrders(data as any) } catch (e: any) { ElMessage.error(e?.response?.data?.message || '校验失败'); return }

  saving.value = true
  try {
    const res = await batchCreateOrders(data as any)
    ElMessage.success(`成功创建 ${(res.data as any).count} 个订单`)
    creating.value = false; load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '创建失败') }
  finally { saving.value = false }
}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}.search-bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.search-bar .field{display:flex;align-items:center;gap:6px}.search-bar .field label{font-size:13px;color:#606266;white-space:nowrap}</style>
