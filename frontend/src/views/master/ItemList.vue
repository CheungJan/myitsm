<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>物料管理</span>
                    <el-button type="primary" size="small">新增物料</el-button>
                </div>
            </template>
            <el-table :data="items" v-loading="loading" stripe>
                <el-table-column prop="item_cd" label="物料编码" width="120" />
                <el-table-column prop="item_nm" label="物料名称" width="180" />
                <el-table-column prop="class_cd" label="分类" width="100" />
                <el-table-column prop="spec" label="规格" width="150" />
                <el-table-column prop="unit" label="单位" width="80" />
                <el-table-column prop="useflg" label="状态" width="80" />
                <el-table-column prop="created_at" label="创建时间" min-width="160" />
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
import { fetchItems, type ItemRecord } from '@/api/master'

const items = ref<ItemRecord[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchItems({ page: String(page.value), per_page: '20' })
        items.value = (res.data as unknown as ItemRecord[]) || []
        total.value = (res as never as { total: number }).total || 0
    } finally {
        loading.value = false
    }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
