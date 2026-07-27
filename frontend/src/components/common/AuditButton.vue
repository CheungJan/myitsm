<template>
  <el-popconfirm title="确认审核通过？" @confirm="$emit('audit')" v-if="auditflg!=='1'">
    <template #reference><el-button type="success" size="small" :loading="loading">审核</el-button></template>
  </el-popconfirm>
  <el-tag v-else type="success" size="small">已审核</el-tag>
</template>
<script setup lang="ts">
defineProps<{auditflg?:string;loading?:boolean}>()
defineEmits<{audit:[]}>()
</script>
