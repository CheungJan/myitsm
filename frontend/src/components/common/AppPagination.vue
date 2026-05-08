<template>
    <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="pageSizes"
        :total="total"
        :layout="layout"
        :disabled="disabled"
        @update:current-page="$emit('update:currentPage', $event)"
        @update:page-size="$emit('update:pageSize', $event)"
        @size-change="$emit('sizeChange', $event)"
    />
</template>

<script lang="ts" setup>
withDefaults(defineProps<{
    currentPage?: number; pageSize?: number
    pageSizes?: number[]; total?: number
    layout?: string; disabled?: boolean
}>(), {
    currentPage: 1, pageSize: 20,
    pageSizes: () => [10, 20, 50, 100],
    total: 0, disabled: false,
    layout: 'total, sizes, prev, pager, next, jumper'
})

defineEmits<{
    'update:currentPage': [page: number]
    'update:pageSize': [size: number]
    sizeChange: [size: number]
}>()
</script>
