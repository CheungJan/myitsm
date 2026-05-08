<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>部门管理</span>
                    <el-button type="primary" size="small">新增部门</el-button>
                </div>
            </template>
            <el-table :data="depts" v-loading="loading" stripe row-key="dept_cd">
                <el-table-column prop="dept_cd" label="编码" width="120" />
                <el-table-column prop="dept_nm" label="名称" width="200" />
                <el-table-column prop="parent_cd" label="上级部门" width="120" />
                <el-table-column label="操作" width="120">
                    <template #default>
                        <el-button type="primary" link size="small">编辑</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { fetchDepartments, type DeptItem } from '@/api/system'

const depts = ref<DeptItem[]>([])
const loading = ref(false)

onMounted(async () => {
    loading.value = true
    try {
        const res = await fetchDepartments()
        depts.value = res.data || []
    } finally {
        loading.value = false
    }
})
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
