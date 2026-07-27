<template>
  <el-button size="small" @click="doExport" :loading="loading">导出</el-button>
</template>
<script setup lang="ts">
import {ref} from 'vue'
import {ElMessage} from 'element-plus'

const props=defineProps<{apiFn:()=>Promise<any>;filename?:string}>()
const loading=ref(false)

async function doExport(){
  loading.value=true
  try{
    const res=await props.apiFn()
    const data=JSON.stringify((res as any)?.data?.items||res)
    const blob=new Blob([data],{type:'application/json'})
    const url=URL.createObjectURL(blob)
    const a=document.createElement('a')
    a.href=url;a.download=props.filename||'export.json';a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  }catch{ElMessage.error('导出失败')}
  finally{loading.value=false}
}
</script>
