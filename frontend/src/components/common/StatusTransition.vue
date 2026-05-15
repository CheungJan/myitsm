<template>
  <div style="display:flex;gap:8px">
    <el-button v-for="s in transitions" :key="s.to" :type="s.type||'primary'" size="small" @click="$emit('transition',s.to)">{{ s.label }}</el-button>
  </div>
</template>
<script setup lang="ts">
export interface TransitionOption {to:string;label:string;type?:string}
defineProps<{transitions:TransitionOption[]}>()
defineEmits<{transition:[to:string]}>()
</script>
