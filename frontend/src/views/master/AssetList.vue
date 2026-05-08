<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>资产台账（共 {{ total }} 条）</span>
                    <div class="filter-bar">
                        <el-input v-model="search" placeholder="搜索设备 SN 或客户" clearable style="width:200px" @keyup.enter="loadData" />
                        <el-button type="primary" size="small" style="margin-left:8px" @click="loadData">查询</el-button>
                    </div>
                </div>
            </template>
            <el-table :data="assets" v-loading="loading" stripe>
                <el-table-column prop="eid" label="设备 SN" width="160" />
                <el-table-column prop="cust_cd" label="客户编码" width="120" />
                <el-table-column prop="asset_type" label="资产类型" width="100" />
                <el-table-column prop="asset_status" label="资产状态" width="100" />
                <el-table-column prop="install_date" label="安装日期" width="120" />
            </el-table>
            <el-pagination v-model:current-page="page" :total="total" :page-size="20"
                layout="total, prev, pager, next" @current-change="loadData" style="margin-top:16px;justify-content:flex-end" />
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { fetchAssets } from '@/api/master'

const assets = ref<Record<string,unknown>[]>([])
const loading = ref(false); const search = ref(''); const page = ref(1); const total = ref(0)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchAssets({ page: String(page.value), per_page: '20' })
        const data = res.data as { items: Record<string,unknown>[], total: number }
        assets.value = data.items || []
        total.value = data.total || 0
    } finally { loading.value = false }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.filter-bar { display: flex; align-items: center; }
</style>
