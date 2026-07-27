<template>
    <GlobalSearch ref="globalSearchRef" />
    <router-view />
</template>
<script setup lang="ts">
import {ref,onMounted,onBeforeUnmount} from 'vue'
import GlobalSearch from '@/components/GlobalSearch.vue'
const globalSearchRef=ref<InstanceType<typeof GlobalSearch>>()
function onKeydown(e:KeyboardEvent){if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();globalSearchRef.value?.open()}}
onMounted(()=>document.addEventListener('keydown',onKeydown))
onBeforeUnmount(()=>document.removeEventListener('keydown',onKeydown))
</script>
