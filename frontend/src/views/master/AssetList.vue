<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>资产台账</span>
                    <el-input v-model="searchQuery" placeholder="搜索设备或客户" style="width:240px" clearable />
                </div>
            </template>
            <el-table :data="assets" v-loading="loading" stripe>
                <el-table-column prop="eid" label="设备 SN" width="160" />
                <el-table-column prop="custcd" label="客户编码" width="120" />
                <el-table-column prop="itemcd" label="物料编码" width="120" />
                <el-table-column prop="status" label="设备状态" width="100" />
                <el-table-column prop="asset_type" label="资产类型" width="100" />
                <el-table-column prop="startdate" label="开通日期" width="120" />
                <el-table-column label="操作" width="120" fixed="right">
                    <template #default>
                        <el-button type="primary" link size="small">详情</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination
                v-model:current-page="page" :total="total" :page-size="20"
                layout="total, prev, pager, next" @current-change="loadData"
                style="margin-top: 16px; justify-content: flex-end"
            />
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'

const assets = ref<Record<string,unknown>[]>([])
const loading = ref(false)
const searchQuery = ref('')
const page = ref(1)
const total = ref(0)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        assets.value = []
        total.value = 0
    } finally {
        loading.value = false
    }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
