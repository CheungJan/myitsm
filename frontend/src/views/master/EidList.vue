<template>
    <div class="page">
        <el-card>
            <template #header><span>EID 设备管理</span></template>
            <el-table :data="eids" v-loading="loading" stripe>
                <el-table-column prop="eid" label="设备 SN" width="160" />
                <el-table-column prop="item_cd" label="物料编码" width="120" />
                <el-table-column prop="etyp" label="类型" width="80" />
                <el-table-column prop="whcd" label="仓库" width="80" />
                <el-table-column prop="sflg" label="状态" width="80" />
                <el-table-column prop="gendate" label="创建日期" width="160" />
                <el-table-column label="操作" width="120" fixed="right">
                    <template #default>
                        <el-button type="primary" link size="small">追踪</el-button>
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
import { fetchEidList, type EidRecord } from '@/api/master'

const eids = ref<EidRecord[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchEidList({ page: String(page.value), per_page: '20' })
        eids.value = (res.data as unknown as EidRecord[]) || []
        total.value = (res as never as { total: number }).total || 0
    } finally {
        loading.value = false
    }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
</style>
