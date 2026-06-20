<template>
    <div class="page">
        <div class="page-header">
            <h2>仓库报表</h2>
        </div>
        <el-tabs v-model="activeTab" type="border-card">
            <!-- Tab 1: 收发存汇总 -->
            <el-tab-pane label="收发存汇总" name="summary">
                <div class="tab-content">
                    <div class="search-bar">
                        <div class="field">
                            <label>月份</label>
                            <el-month-picker v-model="summaryMonth" value-format="YYYY-MM" size="small" style="width:160px" clearable />
                        </div>
                        <div class="field">
                            <label>仓库</label>
                            <el-select v-model="summaryWhcd" size="small" style="width:160px" clearable>
                                <el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd" />
                            </el-select>
                        </div>
                        <el-button type="primary" size="small" @click="doSummarySearch">查询</el-button>
                        <el-button size="small" @click="exportCsv('/warehouse/reports/inventory-summary', summarySearchParams, '收发存汇总')">导出 CSV</el-button>
                    </div>
                    <el-table :data="summaryItems" v-loading="summaryLoading" stripe size="small" style="margin-top:12px">
                        <el-table-column label="仓库" width="120">
                            <template #default="{ row }">{{ row.whnm || row.whcd }}</template>
                        </el-table-column>
                        <el-table-column prop="itemcd" label="物料编码" width="100" />
                        <el-table-column prop="item_nm" label="物料名称" min-width="140" show-overflow-tooltip />
                        <el-table-column prop="begin_qty" label="期初库存" width="100" align="right" />
                        <el-table-column prop="in_qty" label="本期入库" width="100" align="right" />
                        <el-table-column prop="out_qty" label="本期出库" width="100" align="right" />
                        <el-table-column prop="end_qty" label="期末库存" width="100" align="right" />
                    </el-table>
                    <AppPagination v-model:current-page="summaryPage" v-model:page-size="summaryPerPage" :total="summaryTotal"
                        style="margin-top:12px;justify-content:flex-end" />
                </div>
            </el-tab-pane>

            <!-- Tab 2: 库存日报 -->
            <el-tab-pane label="库存日报" name="daily">
                <div class="tab-content">
                    <div class="search-bar">
                        <div class="field">
                            <label>日期</label>
                            <el-date-picker v-model="dailyDate" type="date" value-format="YYYY-MM-DD" size="small"
                                style="width:160px" clearable />
                        </div>
                        <div class="field">
                            <label>仓库</label>
                            <el-select v-model="dailyWhcd" size="small" style="width:160px" clearable>
                                <el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd" />
                            </el-select>
                        </div>
                        <el-button type="primary" size="small" @click="doDailySearch">查询</el-button>
                        <el-button size="small" @click="exportCsv('/warehouse/reports/daily-snapshot', dailySearchParams, '库存日报')">导出 CSV</el-button>
                    </div>
                    <el-table :data="dailyItems" v-loading="dailyLoading" stripe size="small" style="margin-top:12px">
                        <el-table-column label="仓库" width="120">
                            <template #default="{ row }">{{ row.whnm || row.whcd }}</template>
                        </el-table-column>
                        <el-table-column prop="itemcd" label="物料编码" width="100" />
                        <el-table-column prop="item_nm" label="物料名称" min-width="140" show-overflow-tooltip />
                        <el-table-column prop="in_qty" label="当日入库" width="100" align="right" />
                        <el-table-column prop="out_qty" label="当日出库" width="100" align="right" />
                        <el-table-column prop="snapshot_qty" label="当前库存" width="100" align="right" />
                    </el-table>
                    <AppPagination v-model:current-page="dailyPage" v-model:page-size="dailyPerPage" :total="dailyTotal"
                        style="margin-top:12px;justify-content:flex-end" />
                </div>
            </el-tab-pane>

            <!-- Tab 3: 库龄分析 -->
            <el-tab-pane label="库龄分析" name="aging">
                <div class="tab-content">
                    <div class="search-bar">
                        <div class="field">
                            <label>仓库</label>
                            <el-select v-model="agingWhcd" size="small" style="width:160px" clearable>
                                <el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd" />
                            </el-select>
                        </div>
                        <el-button type="primary" size="small" @click="doAgingSearch">查询</el-button>
                        <el-button size="small" @click="exportCsv('/warehouse/reports/aging', agingSearchParams, '库龄分析')">导出 CSV</el-button>
                    </div>
                    <el-table :data="agingItems" v-loading="agingLoading" stripe size="small" style="margin-top:12px">
                        <el-table-column label="仓库" width="120">
                            <template #default="{ row }">{{ row.whnm || row.whcd }}</template>
                        </el-table-column>
                        <el-table-column prop="itemcd" label="物料编码" width="100" />
                        <el-table-column prop="item_nm" label="物料名称" min-width="140" show-overflow-tooltip />
                        <el-table-column prop="itemqty" label="库存数量" width="100" align="right" />
                        <el-table-column prop="first_in" label="最早入库" width="120" />
                        <el-table-column label="在库天数" width="100" align="right">
                            <template #default="{ row }">
                                <span v-if="row.age_days != null"
                                    :style="{
                                        color: row.age_days < 30 ? '#67c23a' : row.age_days <= 90 ? '#e6a23c' : '#f56c6c',
                                        fontWeight: 'bold'
                                    }">
                                    {{ row.age_days }}
                                </span>
                                <span v-else style="color:#909399">-</span>
                            </template>
                        </el-table-column>
                    </el-table>
                    <AppPagination v-model:current-page="agingPage" v-model:page-size="agingPerPage" :total="agingTotal"
                        style="margin-top:12px;justify-content:flex-end" />
                </div>
            </el-tab-pane>
        </el-tabs>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import request from '@/api/request'
import { fetchInventorySummary, fetchDailySnapshot, fetchInventoryAging, fetchWarehouses } from '@/api/warehouse'

const activeTab = ref('summary')
const whOptions = ref<{ whcd: string; whnm: string }[]>([])

// ---- 收发存汇总 ----
const summaryMonth = ref('')
const summaryWhcd = ref('')
const summaryItems = ref<Record<string,unknown>[]>([])
const summaryLoading = ref(false)
const summaryPage = ref(1)
const summaryPerPage = ref(20)
const summaryTotal = ref(0)
const summarySearchParams = ref<Record<string,string>>({})

watch(summaryPage, () => loadSummary())
watch(summaryPerPage, () => { summaryPage.value = 1; loadSummary() })

async function loadSummary() {
    summaryLoading.value = true
    try {
        const params: Record<string, string> = { page: String(summaryPage.value), per_page: String(summaryPerPage.value), ...summarySearchParams.value }
        const res = await fetchInventorySummary(params)
        summaryItems.value = (res.data?.items || []) as Record<string,unknown>[]
        summaryTotal.value = res.data?.total || 0
    } finally {
        summaryLoading.value = false
    }
}
function doSummarySearch() {
    const p: Record<string, string> = {}
    if (summaryMonth.value) p.period = summaryMonth.value
    if (summaryWhcd.value) p.whcd = summaryWhcd.value
    summarySearchParams.value = p
    if (summaryPage.value === 1) loadSummary()
    else summaryPage.value = 1
}

// ---- 库存日报 ----
const dailyDate = ref('')
const dailyWhcd = ref('')
const dailyItems = ref<Record<string,unknown>[]>([])
const dailyLoading = ref(false)
const dailyPage = ref(1)
const dailyPerPage = ref(20)
const dailyTotal = ref(0)
const dailySearchParams = ref<Record<string,string>>({})

watch(dailyPage, () => loadDaily())
watch(dailyPerPage, () => { dailyPage.value = 1; loadDaily() })

async function loadDaily() {
    dailyLoading.value = true
    try {
        const params: Record<string, string> = { page: String(dailyPage.value), per_page: String(dailyPerPage.value), ...dailySearchParams.value }
        const res = await fetchDailySnapshot(params)
        dailyItems.value = (res.data?.items || []) as Record<string,unknown>[]
        dailyTotal.value = res.data?.total || 0
    } finally {
        dailyLoading.value = false
    }
}
function doDailySearch() {
    const p: Record<string, string> = {}
    if (dailyDate.value) p.date = dailyDate.value
    if (dailyWhcd.value) p.whcd = dailyWhcd.value
    dailySearchParams.value = p
    if (dailyPage.value === 1) loadDaily()
    else dailyPage.value = 1
}

// ---- 库龄分析 ----
const agingWhcd = ref('')
const agingItems = ref<Record<string,unknown>[]>([])
const agingLoading = ref(false)
const agingPage = ref(1)
const agingPerPage = ref(20)
const agingTotal = ref(0)
const agingSearchParams = ref<Record<string,string>>({})

watch(agingPage, () => loadAging())
watch(agingPerPage, () => { agingPage.value = 1; loadAging() })

async function loadAging() {
    agingLoading.value = true
    try {
        const params: Record<string, string> = { page: String(agingPage.value), per_page: String(agingPerPage.value), ...agingSearchParams.value }
        const res = await fetchInventoryAging(params)
        agingItems.value = (res.data?.items || []) as Record<string,unknown>[]
        agingTotal.value = res.data?.total || 0
    } finally {
        agingLoading.value = false
    }
}
function doAgingSearch() {
    const p: Record<string, string> = {}
    if (agingWhcd.value) p.whcd = agingWhcd.value
    agingSearchParams.value = p
    if (agingPage.value === 1) loadAging()
    else agingPage.value = 1
}

onMounted(async () => {
    try {
        const r = await fetchWarehouses()
        whOptions.value = r.data || []
    } catch { /* ignore */ }
    loadSummary()
})
async function exportCsv(url: string, params: Record<string,string>, name: string) {
    try {
        const r = await request.get(url, { params: { ...params, per_page: '99999' } } as any)
        const items = (r as any)?.data?.items || []
        if (!items.length) { ElMessage.warning('暂无数据'); return }
        const XLSX = await import('xlsx')
        const ws = XLSX.utils.json_to_sheet(items)
        const wb = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, name)
        XLSX.writeFile(wb, `${name}_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success(`导出 ${items.length} 条`)
    } catch { ElMessage.error('导出失败') }
}
</script>

<style scoped>
.page { padding: 0; }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0; }
.tab-content { padding: 8px 0; }
.search-bar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.field { display: flex; align-items: center; gap: 6px; }
.field label { font-size: 13px; color: #606266; white-space: nowrap; }
</style>
