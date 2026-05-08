<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>仓库管理</span>
                    <el-button type="primary" size="small">新增仓库</el-button>
                </div>
            </template>
            <el-table :data="warehouses" v-loading="loading" stripe>
                <el-table-column prop="wh_cd" label="仓库编码" width="100" />
                <el-table-column prop="wh_nm" label="仓库名称" width="200" />
                <el-table-column prop="address" label="地址" min-width="200" />
                <el-table-column prop="phone" label="电话" width="140" />
                <el-table-column prop="leader" label="负责人" width="100" />
                <el-table-column prop="useflg" label="状态" width="80" />
                <el-table-column label="操作" width="120" fixed="right">
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
import { fetchWarehouses, type WarehouseRecord } from '@/api/warehouse'

const warehouses = ref<WarehouseRecord[]>([])
const loading = ref(false)

onMounted(async () => {
    loading.value = true
    try {
        const res = await fetchWarehouses()
        warehouses.value = res.data || []
    } finally {
        loading.value = false
    }
})
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
