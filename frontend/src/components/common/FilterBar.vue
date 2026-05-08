<template>
    <div class="filter-bar">
        <!-- 分类下拉 -->
        <el-select
            v-if="classOptions && classOptions.length"
            :model-value="classValue"
            :placeholder="classPlaceholder"
            clearable
            style="width:140px"
            @update:model-value="$emit('update:classValue', $event)"
            @change="$emit('filter')"
        >
            <el-option v-for="c in classOptions" :key="c" :label="c" :value="c" />
        </el-select>
        <!-- 搜索框 -->
        <el-input
            v-model="searchModel"
            :placeholder="searchPlaceholder"
            clearable
            style="width:200px"
            @keyup.enter="$emit('filter')"
        />
        <el-button type="primary" size="small" @click="$emit('filter')">查询</el-button>
        <!-- 操作按钮插槽 -->
        <slot name="actions" />
    </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

const props = defineProps<{
    searchValue?: string
    classValue?: string
    classOptions?: string[]
    classPlaceholder?: string
    searchPlaceholder?: string
}>()

defineEmits<{
    'update:searchValue': [value: string]
    'update:classValue': [value: string]
    filter: []
}>()

const searchModel = computed({
    get: () => props.searchValue || '',
    set: (v: string) => { /* handled by v-model on parent via update:searchValue */ }
})
</script>

<style lang="scss" scoped>
.filter-bar {
    display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
}
</style>
