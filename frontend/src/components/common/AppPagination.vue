<template>
    <el-pagination
        v-model:current-page="currentPageModel"
        v-model:page-size="pageSizeModel"
        :page-sizes="pageSizes"
        :total="total"
        :layout="layout"
        :disabled="disabled"
    />
</template>

<script lang="ts" setup>
import { computed } from 'vue'

const props = withDefaults(defineProps<{
    currentPage?: number; pageSize?: number
    pageSizes?: number[]; total?: number
    layout?: string; disabled?: boolean
}>(), {
    currentPage: 1, pageSize: 20,
    pageSizes: () => [10, 20, 50, 100],
    total: 0, disabled: false,
    layout: 'total, sizes, prev, pager, next, jumper'
})

const emit = defineEmits<{
    'update:current-page': [page: number]
    'update:page-size': [size: number]
}>()

const currentPageModel = computed({
    get: () => props.currentPage,
    set: (v: number) => emit('update:current-page', v)
})
const pageSizeModel = computed({
    get: () => props.pageSize,
    set: (v: number) => emit('update:page-size', v)
})
</script>
