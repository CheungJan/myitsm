<template>
  <div class="page">
    <div class="page-header"><h2>采购订单</h2><el-button type="primary" size="small" @click="openCreate">新建订单</el-button></div>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open">
        <el-table-column prop="rgstbillid" label="订单号" width="110"/>
        <el-table-column label="采购员" width="80"><template #default="{row}">{{ userName(row.pcrep) }}</template></el-table-column>
        <el-table-column prop="rgstamt" label="金额" width="100" align="right"/>
        <el-table-column label="审批" width="70"><template #default="{row}"><el-tag :type="row.auditflg==='2'?'success':'warning'" size="small">{{ afLabel(row.auditflg) }}</el-tag></template></el-table-column>
        <el-table-column prop="gendate" label="日期" width="100"/>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
        <el-table-column label="操作员" width="80"><template #default="{row}">{{ userName(row.opercd) }}</template></el-table-column>
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

    <el-dialog title="新建采购订单" v-model="creating" width="650px" @closed="resetForm">
      <el-form :model="form" label-width="80px" size="small">
        <el-form-item label="供应商"><el-input v-model="form.suppliercd" placeholder="供应商编码"/></el-form-item>
        <el-form-item label="采购员"><el-input v-model="form.pcrep" placeholder="采购代表"/></el-form-item>
        <el-form-item label="下单日期"><el-date-picker v-model="form.rgstdate" type="date" style="width:100%" value-format="YYYY-MM-DD"/></el-form-item>
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
              <el-table-column label="数量" width="120"><template #default="{row,$index}"><el-input-number v-model="formDetails[$index].rgsqty" :min="1" size="small" style="width:100px"/></template></el-table-column>
              <el-table-column prop="units" label="单位" width="60"/>
              <el-table-column label="操作" width="60"><template #default="{$index}"><el-button link type="danger" size="small" @click="formDetails.splice($index,1)">删除</el-button></template></el-table-column>
            </el-table>
          </div>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="creating=false">取消</el-button><el-button type="primary" @click="doCreate" :loading="saving">创建</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">import {ref,reactive,onMounted} from 'vue';import {ElMessage,ElTree} from 'element-plus';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {useUserNames} from '@/composables/useUserNames';import {useDict} from '@/composables/useDict';import {fetchOrders,createOrder} from '@/api/procurement';import type {ProcRecord} from '@/api/procurement';import {fetchBomClassTree} from '@/api/master';import type {ItemClassNode} from '@/api/master'

const{userName}=useUserNames()
const{dictLabel:afLabel}=useDict('AF')
const{items,loading,page,perPage,total,load}=useListPage<ProcRecord>(fetchOrders)
const{drawer,detail,open}=useDetailDrawer<ProcRecord>()

// 新建 — 配件树（typflg='0' = 仅配件）
const creating=ref(false);const saving=ref(false)
const form=reactive({suppliercd:'',pcrep:'',rgstdate:'',memo:''})
const formDetails=reactive<{itemcd:string;itemnm:string;rgsqty:number;units:string}[]>([])
const partTree=ref<ItemClassNode[]>([])
const treeRef=ref<InstanceType<typeof ElTree>>()
const itemSearch=ref('')

onMounted(async()=>{try{const r=await fetchBomClassTree('0');partTree.value=r.data||[]}catch{}})

function filterNode(value:string,data:ItemClassNode){if(!value)return true;return (data.class_nm||'').toLowerCase().includes(value.toLowerCase())}
function filterTree(){if(treeRef.value)(treeRef.value as any).filter(itemSearch.value)}

function addSelectedItems(){
  const nodes=(treeRef.value as any)?.getCheckedNodes(false)||[]
  for(const node of nodes){
    if(!node.children||node.children.length===0){
      if(!formDetails.find(d=>d.itemcd===node.class_cd)){
        formDetails.push({itemcd:node.class_cd,itemnm:node.class_nm,rgsqty:1,units:''})
      }
    }
  }
}

function openCreate(){creating.value=true}
function resetForm(){form.suppliercd='';form.pcrep='';form.rgstdate='';form.memo='';formDetails.length=0}
async function doCreate(){
  saving.value=true
  try{
    await createOrder({...form,details:formDetails.map(d=>({itemcd:d.itemcd,rgsqty:d.rgsqty,units:d.units}))})
    ElMessage.success('创建成功');creating.value=false;load()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'创建失败')}finally{saving.value=false}
}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
