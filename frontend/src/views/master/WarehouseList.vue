<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>仓库管理（共 {{ total }} 条）</span>
                    <el-button type="primary" size="small" @click="openDialog()">新增仓库</el-button>
                </div>
            </template>
            <el-table :data="warehouses" v-loading="loading" stripe>
                <el-table-column prop="wh_cd" label="编码" width="100" />
                <el-table-column prop="wh_nm" label="名称" width="200" />
                <el-table-column prop="address" label="地址" min-width="200" />
                <el-table-column prop="phone" label="电话" width="140" />
                <el-table-column prop="leader" label="负责人" width="100" />
                <el-table-column prop="useflg" label="状态" width="80" />
                <el-table-column label="操作" width="160" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" :total="total"
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchWarehouses } from '@/api/warehouse'

const warehouses = ref<Record<string,unknown>[]>([])
const loading = ref(false); const page = ref(1); const total = ref(0)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchWarehouses()
        const list = (res.data || []) as never[]
        total.value = list.length
        warehouses.value = list.slice((page.value-1)*20, page.value*20)
    } finally { loading.value = false }
}

function openDialog(_row?: unknown) { /* TODO */ }
function handleDelete(_row: unknown) { /* TODO */ }
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
