<template>
    <div class="page">
        <div class="page-header">
            <h2>库存流水</h2>
        </div>
        <el-card shadow="never" style="margin-bottom:16px">
            <div class="search-bar">
                <div class="field">
                    <label>开始日期</label>
                    <el-date-picker v-model="search.start_date" type="date" value-format="YYYY-MM-DD"
                        placeholder="开始日期" size="small" style="width:140px" />
                </div>
                <div class="field">
                    <label>结束日期</label>
                    <el-date-picker v-model="search.end_date" type="date" value-format="YYYY-MM-DD"
                        placeholder="结束日期" size="small" style="width:140px" />
                </div>
                <div class="field">
                    <label>仓库</label>
                    <el-select v-model="search.whcd" size="small" style="width:140px" clearable>
                        <el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd" />
                    </el-select>
                </div>
                <div class="field">
                    <label>物料</label>
                    <el-input v-model="search.itemcd" placeholder="物料编码" size="small" style="width:140px" clearable />
                </div>
                <div class="field">
                    <label>单据号</label>
                    <el-input v-model="search.billid" placeholder="单据号" size="small" style="width:140px" clearable />
                </div>
                <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
            </div>
        </el-card>
        <el-card shadow="never">
            <el-table :data="items" v-loading="loading" stripe size="small">
                <el-table-column label="时间" width="150">
                    <template #default="{ row }">{{ formatDate(row.gendate as string) }}</template>
                </el-table-column>
                <el-table-column prop="billid" label="单据号" width="110" />
                <el-table-column label="仓库" width="110">
                    <template #default="{ row }">{{ row.whnm || row.whcd }}</template>
                </el-table-column>
                <el-table-column prop="itemcd" label="物料编码" width="100" />
                <el-table-column prop="item_nm" label="物料名称" min-width="120" show-overflow-tooltip />
                <el-table-column label="变动量" width="80" align="right">
                    <template #default="{ row }">{{ row.itemqty }}</template>
                </el-table-column>
                <el-table-column label="方向" width="60" align="center">
                    <template #default="{ row }">
                        <el-tag :type="row.iotyp === '1' ? 'success' : 'danger'" size="small" effect="plain">
                            {{ row.iotyp === '1' ? '入库' : '出库' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="类型" width="110" align="center">
                    <template #default="{ row }">{{ typeLabel(row) }}</template>
                </el-table-column>
                <el-table-column label="库存余量" width="90" align="right">
                    <template #default="{ row }">{{ row.storeqty }}</template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total"
                style="margin-top:12px;justify-content:flex-end" />
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useDict } from '@/composables/useDict'
import { fetchStockMovements, fetchWarehouses, type StockMovement } from '@/api/warehouse'

const { items, loading, page, perPage, total, onSearch } = useListPage<StockMovement>(fetchStockMovements)
const { dictLabel: ivLabel } = useDict('IV')
const { dictLabel: ovLabel } = useDict('OV')
const search = reactive({ whcd: '', itemcd: '', start_date: '', end_date: '', billid: '' })
const whOptions = ref<{ whcd: string; whnm: string }[]>([])

onMounted(async () => {
    try {
        const r = await fetchWarehouses()
        whOptions.value = r.data || []
    } catch { /* ignore */ }
})

function formatDate(val: string | undefined): string {
    if (!val) return '-'
    return val.replace('T', ' ').substring(0, 19)
}

function typeLabel(row: StockMovement): string {
    const invtyp = (row as any).invtyp || ''
    const iotyp = (row as any).iotyp || ''
    if (iotyp === '1') {
        const label = ivLabel(invtyp)
        return label !== invtyp ? label : ovLabel(invtyp)  // IV没命中试OV
    }
    if (iotyp === '2' || iotyp === '0') {
        const label = ovLabel(invtyp)
        return label !== invtyp ? label : ivLabel(invtyp)  // OV没命中试IV
    }
    // 未知iotyp：两个字典都试试
    const label = ivLabel(invtyp)
    return label !== invtyp ? label : ovLabel(invtyp)
}

function doSearch() {
    const p: Record<string, string> = {}
    if (search.whcd) p.whcd = search.whcd
    if (search.itemcd) p.itemcd = search.itemcd
    if (search.start_date) p.start_date = search.start_date
    if (search.end_date) p.end_date = search.end_date
    if (search.billid) p.billid = search.billid
    onSearch(p)
}
</script>

<style scoped>
.page {
    padding: 0;
}
.page-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
}
.page-header h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
}
.search-bar {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
}
.field {
    display: flex;
    align-items: center;
    gap: 6px;
}
.field label {
    font-size: 13px;
    color: #606266;
}
</style>
