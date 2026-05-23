<template>
  <div class="page">
    <div class="page-header"><h2>采购需求</h2><el-button type="primary" size="small" @click="openCreate">新建需求</el-button></div>

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
        <el-table-column label="计划日期" width="160"><template #default="{row}">{{ formatDateTime(row.plandate) || '-' }}</template></el-table-column>
        <el-table-column label="操作员" width="80"><template #default="{row}">{{ userName(row.opercd) }}</template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <el-dialog :title="'需求详情 — '+(detail?.pcplanid||'')" v-model="drawer" width="550px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="计划号">{{ detail.pcplanid }}</el-descriptions-item>
          <el-descriptions-item label="采购类型">{{ puLabel(detail.pctyp) }}</el-descriptions-item>
          <el-descriptions-item label="销售单号">{{ detail.slbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="计划日期">{{ formatDateTime(detail.plandate) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审批状态"><el-tag :type="detail.auditflg==='2'?'success':detail.auditflg==='1'?'warning':'info'" size="small">{{ afLabel(detail.auditflg) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ formatDateTime(detail.gendate) }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ userName(detail.opercd) }}</el-descriptions-item>
          <el-descriptions-item label="审批人">{{ detail.auditman || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审批日期">{{ formatDateTime(detail.auditdate) }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo || detail.checkmemo || '-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">采购明细</h4>
        <el-table :data="detail.details||[]" size="small" stripe>
          <el-table-column prop="itemcd" label="物料编码" width="100"/>
          <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
          <el-table-column prop="rgstqty" label="登记数量" width="80"/>
          <el-table-column prop="units" label="单位" width="60"/>
          <el-table-column prop="storeqty" label="库存量" width="80"/>
          <el-table-column prop="auditqty" label="审核数量" width="80"/>
        </el-table>
      </template>
    </el-dialog>

    <el-dialog title="新建采购需求" v-model="creating" width="500px" @closed="resetForm">
      <el-form :model="form" label-width="80px" size="small">
        <el-form-item label="采购类型"><el-select v-model="form.pctyp" style="width:100%"><el-option v-for="(nm,cd) in puMap" :key="cd" :label="nm" :value="cd"/></el-select></el-form-item>
        <el-form-item label="销售单号"><el-input v-model="form.slbillid"/></el-form-item>
        <el-form-item label="计划日期"><el-date-picker v-model="form.plandate" type="date" style="width:100%" value-format="YYYY-MM-DD"/></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.memo" type="textarea" :rows="2"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="creating=false">取消</el-button><el-button type="primary" @click="doCreate" :loading="saving">创建</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">import {ref,reactive} from 'vue';import {ElMessage} from 'element-plus';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useUserNames} from '@/composables/useUserNames';import {useDict} from '@/composables/useDict';import {fetchRequisitions,fetchRequisitionDetail,createRequisition,type ProcRecord} from '@/api/procurement'

const{userName}=useUserNames()
const{dictMap:afMap,dictLabel:afLabel}=useDict('AF')
const{dictMap:puMap,dictLabel:puLabel}=useDict('PU')

const{items,loading,page,perPage,total,onSearch}=useListPage<ProcRecord>(fetchRequisitions)

// 格式化日期时间
function formatDateTime(dateStr:any){
  if(!dateStr)return'-'
  return String(dateStr).replace('T',' ')
}

// 筛选条件
const searchPctyp=ref('')
const searchAuditflg=ref('')
const searchStartDate=ref('')
const searchEndDate=ref('')

function doSearch(){
  const p:Record<string,string>={}
  if(searchPctyp.value)p.pctyp=searchPctyp.value
  if(searchAuditflg.value)p.auditflg=searchAuditflg.value
  if(searchStartDate.value)p.start_date=searchStartDate.value
  if(searchEndDate.value)p.end_date=searchEndDate.value
  onSearch(p)
}
function doReset(){
  searchPctyp.value=''
  searchAuditflg.value=''
  searchStartDate.value=''
  searchEndDate.value=''
  onSearch({})
}

// 详情
const drawer=ref(false);const detail=ref<ProcRecord|null>(null)
async function openDetail(row:ProcRecord){drawer.value=true;try{const r=await fetchRequisitionDetail(row.pcplanid as string);detail.value=r.data}catch{detail.value=row}}

// 新建
const creating=ref(false);const saving=ref(false)
const form=reactive({pctyp:'10',slbillid:'',plandate:'',memo:''})
function openCreate(){creating.value=true}
function resetForm(){form.pctyp='10';form.slbillid='';form.plandate='';form.memo=''}
async function doCreate(){saving.value=true;try{await createRequisition({...form});ElMessage.success('创建成功');creating.value=false;doSearch()}catch(e:any){ElMessage.error(e?.response?.data?.message||'创建失败')}finally{saving.value=false}}
</script>
<style scoped>
.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}
.search-bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.search-bar .field{display:flex;align-items:center;gap:6px}.search-bar .field label{font-size:13px;color:#606266;white-space:nowrap}
</style>
