<template>
  <el-dialog v-model="visible" title="全局搜索" width="650px" @keydown.ctrl.k.prevent="visible=!visible" :close-on-click-modal="false">
    <el-input v-model="keyword" placeholder="搜索客户/工单/物料/EID..." size="large" clearable @keyup.enter="doSearch" ref="inputRef">
      <template #prefix><span style="font-size:14px">🔍</span></template>
    </el-input>
    <div style="margin-top:12px">
      <el-tabs v-model="activeTab" @tab-change="doSearch">
        <el-tab-pane label="客户" name="cust"/>
        <el-tab-pane label="工单" name="itsm"/>
        <el-tab-pane label="物料" name="item"/>
        <el-tab-pane label="设备" name="eid"/>
      </el-tabs>
      <el-table :data="results" v-loading="searching" stripe size="small" style="margin-top:8px" max-height="350">
        <el-table-column prop="title" label="结果" min-width="180">
          <template #default="{row}"><el-link type="primary" @click="navigateTo(row)" :underline="false">{{ row.title }}</el-link></template>
        </el-table-column>
        <el-table-column prop="subtitle" label="描述" min-width="200" show-overflow-tooltip/>
      </el-table>
      <el-empty v-if="!searching && keyword && results.length===0" description="未找到结果" :image-size="60"/>
    </div>
  </el-dialog>
</template>
<script setup lang="ts">
import {ref, nextTick} from 'vue'
import {useRouter} from 'vue-router'
import request from '@/api/request'

const visible=ref(false);const keyword=ref('');const activeTab=ref('cust')
const results=ref<{title:string;subtitle:string;path?:string}[]>([]);const searching=ref(false)
const inputRef=ref();const router=useRouter()

async function doSearch(){
  if(!keyword.value.trim()){results.value=[];return}
  searching.value=true
  try{
    const q=keyword.value.trim()
    let data:any[]=[]
    if(activeTab.value==='cust'){
      const r=await request.get('/system/customers',{params:{search:q,per_page:10}})
      data=((r as any)?.data?.items||[]).map((c:any)=>({title:c.cust_nm||c.cust_cd,subtitle:`客户编码: ${c.cust_cd||'-'} | 磁卡号: ${c.cust_card||'-'}`,path:`/master/customers`}))
    }else if(activeTab.value==='itsm'){
      const r=await request.get('/itsm/maintenance-daily',{params:{maintenance_id:q,per_page:10}})
      data=((r as any)?.data?.items||[]).map((m:any)=>({title:`工单 ${m.maintenance_id}`,subtitle:`${m.short_description||'-'} | 门店: ${m.store_id||'-'}`,path:`/itsm/maintenance`}))
    }else if(activeTab.value==='item'){
      const r=await request.get('/system/items',{params:{search:q,per_page:10}})
      data=((r as any)?.data?.items||[]).map((i:any)=>({title:i.item_nm||i.item_cd,subtitle:`物料编码: ${i.item_cd||'-'} | 规格: ${i.spec||'-'}`,path:`/master/items`}))
    }else if(activeTab.value==='eid'){
      const r=await request.get('/system/eid',{params:{search:q,per_page:10}})
      data=((r as any)?.data?.items||[]).map((e:any)=>({title:e.eid,subtitle:`物料: ${e.item_nm||e.itemcd||'-'} | 类型: ${e.etyp||'-'}`,path:`/master/eid`}))
    }
    results.value=data
  }catch{results.value=[]}
  finally{searching.value=false}
}

function navigateTo(row:any){
  visible.value=false
  if(row.path)router.push(row.path)
}

function open(){
  visible.value=true;keyword.value='';results.value=[]
  nextTick(()=>{if(inputRef.value)inputRef.value.focus()})
}

defineExpose({open})
</script>
