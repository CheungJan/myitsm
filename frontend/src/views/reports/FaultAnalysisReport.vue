<template>
    <div class="page">
        <div class="page-header">
            <h2>故障分析报表</h2>
        </div>
        <el-tabs v-model="activeTab" type="border-card">
            <!-- Tab 1: 型号故障率 -->
            <el-tab-pane label="型号故障率" name="model-rate">
                <div class="tab-content">
                    <div class="search-bar">
                        <div class="field">
                            <label>开始日期</label>
                            <el-date-picker v-model="params.start_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" clearable />
                        </div>
                        <div class="field">
                            <label>结束日期</label>
                            <el-date-picker v-model="params.end_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" clearable />
                        </div>
                        <div class="field">
                            <label>单据类型</label>
                            <el-select v-model="params.bill_type" size="small" style="width:140px" clearable placeholder="全部">
                                <el-option label="日常维护" value="MD" />
                                <el-option label="新机开通" value="MO" />
                                <el-option label="旧机翻新" value="MR" />
                                <el-option label="设备变更" value="BG" />
                                <el-option label="日常保养" value="BY" />
                            </el-select>
                        </div>
                        <div class="field">
                            <label>故障类型</label>
                            <el-tree-select
                                v-model="params.fault_type_cd"
                                :data="modelClassTree"
                                :props="{ label: 'class_nm', value: 'class_cd', children: 'children' }"
                                node-key="class_cd"
                                size="small"
                                style="width:200px"
                                clearable
                                check-strictly
                                :render-after-expand="false"
                                placeholder="选择整机分类"
                                :filter-method="filterClassNode"
                                filterable
                            />
                        </div>
                        <el-button type="primary" size="small" @click="loadModelRate">查询</el-button>
                    </div>
                    <el-table :data="modelRateRows" v-loading="modelRateLoading" stripe size="small" style="margin-top:12px">
                        <el-table-column type="index" label="排名" width="60" align="center" />
                        <el-table-column prop="itemcd" label="设备物料编码" width="140" />
                        <el-table-column prop="item_nm" label="物料名称" min-width="180" show-overflow-tooltip />
                        <el-table-column prop="fault_count" label="故障次数" width="100" align="right" sortable />
                        <el-table-column prop="distinct_device" label="涉及设备数" width="110" align="right" sortable />
                    </el-table>
                    <el-empty v-if="!modelRateLoading && modelRateRows.length === 0" description="暂无数据" :image-size="80" style="margin-top:20px" />
                </div>
            </el-tab-pane>

            <!-- Tab 2: 配件更换频次 -->
            <el-tab-pane label="配件更换频次" name="accessory-frequency">
                <div class="tab-content">
                    <div class="search-bar">
                        <div class="field">
                            <label>开始日期</label>
                            <el-date-picker v-model="params.start_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" clearable />
                        </div>
                        <div class="field">
                            <label>结束日期</label>
                            <el-date-picker v-model="params.end_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" clearable />
                        </div>
                        <div class="field">
                            <label>配件分类</label>
                            <el-tree-select
                                v-model="params.fault_type_cd"
                                :data="accessoryClassTree"
                                :props="{ label: 'class_nm', value: 'class_cd', children: 'children' }"
                                node-key="class_cd"
                                size="small"
                                style="width:200px"
                                clearable
                                check-strictly
                                :render-after-expand="false"
                                placeholder="选择配件分类"
                                :filter-method="filterClassNode"
                                filterable
                            />
                        </div>
                        <el-button type="primary" size="small" @click="loadAccessoryFrequency">查询</el-button>
                    </div>
                    <el-table :data="accessoryRows" v-loading="accessoryLoading" stripe size="small" style="margin-top:12px">
                        <el-table-column type="index" label="排名" width="60" align="center" />
                        <el-table-column prop="itemcd" label="配件编码" width="140" />
                        <el-table-column prop="item_nm" label="配件名称" min-width="180" show-overflow-tooltip />
                        <el-table-column prop="replace_count" label="更换次数" width="100" align="right" sortable />
                        <el-table-column prop="distinct_maintenance" label="涉及工单数" width="110" align="right" sortable />
                    </el-table>
                    <el-empty v-if="!accessoryLoading && accessoryRows.length === 0" description="暂无数据" :image-size="80" style="margin-top:20px" />
                </div>
            </el-tab-pane>

            <!-- Tab 3: 修复时长 -->
            <el-tab-pane label="修复时长" name="repair-duration">
                <div class="tab-content">
                    <div class="search-bar">
                        <div class="field">
                            <label>开始日期</label>
                            <el-date-picker v-model="params.start_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" clearable />
                        </div>
                        <div class="field">
                            <label>结束日期</label>
                            <el-date-picker v-model="params.end_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" clearable />
                        </div>
                        <div class="field">
                            <label>单据类型</label>
                            <el-select v-model="params.bill_type" size="small" style="width:140px" clearable placeholder="全部">
                                <el-option label="日常维护" value="MD" />
                                <el-option label="新机开通" value="MO" />
                                <el-option label="旧机翻新" value="MR" />
                                <el-option label="设备变更" value="BG" />
                                <el-option label="日常保养" value="BY" />
                            </el-select>
                        </div>
                        <div class="field">
                            <label>故障类型</label>
                            <el-tree-select
                                v-model="params.fault_type_cd"
                                :data="fullClassTree"
                                :props="{ label: 'class_nm', value: 'class_cd', children: 'children' }"
                                node-key="class_cd"
                                size="small"
                                style="width:200px"
                                clearable
                                check-strictly
                                :render-after-expand="false"
                                placeholder="选择物料分类"
                                :filter-method="filterClassNode"
                                filterable
                            />
                        </div>
                        <el-button type="primary" size="small" @click="loadRepairDuration">查询</el-button>
                    </div>
                    <el-table :data="repairRows" v-loading="repairLoading" stripe size="small" style="margin-top:12px">
                        <el-table-column label="单据类型" width="120">
                            <template #default="{ row }">{{ billTypeLabel(row.bill_type) }}</template>
                        </el-table-column>
                        <el-table-column prop="count" label="样本数" width="100" align="right" />
                        <el-table-column prop="avg_minutes" label="平均时长(分钟)" width="140" align="right" sortable />
                        <el-table-column prop="median_minutes" label="中位时长(分钟)" width="140" align="right" sortable />
                        <el-table-column prop="max_minutes" label="最大时长(分钟)" width="140" align="right" sortable />
                    </el-table>
                    <el-empty v-if="!repairLoading && repairRows.length === 0" description="暂无数据" :image-size="80" style="margin-top:20px" />
                </div>
            </el-tab-pane>
        </el-tabs>
    </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { fetchModelFaultRate, fetchAccessoryFrequency, fetchRepairDuration } from '@/api/reports'
import { fetchBomClassTree, fetchItemClassTree } from '@/api/master'
import type { ModelFaultRateRow, AccessoryFrequencyRow, RepairDurationRow, FaultAnalysisParams } from '@/api/reports'
import type { ItemClassNode } from '@/api/master'

const activeTab = ref('model-rate')
const params = reactive<FaultAnalysisParams>({
    start_date: '',
    end_date: '',
    bill_type: '',
    fault_type_cd: '',
})

// 成品分类树（型号故障率筛选，typflg=1）
const modelClassTree = ref<ItemClassNode[]>([])
// 配件分类树（配件更换频次筛选，typflg=0）
const accessoryClassTree = ref<ItemClassNode[]>([])
// 完整分类树（修复时长筛选，整机+配件，故障解决方式包含整机更换与配件更换）
const fullClassTree = ref<ItemClassNode[]>([])
// 过滤掉物料叶子节点，只保留分类节点
function filterClassNode(value: string, data?: ItemClassNode): boolean {
    if (!data) return false
    if (data.type === 'item') return false
    if (!value) return true
    return (data.class_nm || '').toLowerCase().includes(value.toLowerCase())
        || (data.class_cd || '').toLowerCase().includes(value.toLowerCase())
}

// 型号故障率
const modelRateRows = ref<ModelFaultRateRow[]>([])
const modelRateLoading = ref(false)
async function loadModelRate() {
    modelRateLoading.value = true
    try {
        const r = await fetchModelFaultRate(params)
        modelRateRows.value = r?.data || []
    } finally {
        modelRateLoading.value = false
    }
}

// 配件更换频次
const accessoryRows = ref<AccessoryFrequencyRow[]>([])
const accessoryLoading = ref(false)
async function loadAccessoryFrequency() {
    accessoryLoading.value = true
    try {
        const r = await fetchAccessoryFrequency(params)
        accessoryRows.value = r?.data || []
    } finally {
        accessoryLoading.value = false
    }
}

// 修复时长
const repairRows = ref<RepairDurationRow[]>([])
const repairLoading = ref(false)
async function loadRepairDuration() {
    repairLoading.value = true
    try {
        const r = await fetchRepairDuration(params)
        repairRows.value = r?.data || []
    } finally {
        repairLoading.value = false
    }
}

// 单据类型翻译
function billTypeLabel(code: string): string {
    const map: Record<string, string> = {
        MD: '日常维护',
        MO: '新机开通',
        MR: '旧机翻新',
        BG: '设备变更',
        BY: '日常保养',
    }
    return map[code] || code || '-'
}

// 加载分类树：成品（typflg=1）用于型号故障率，配件（typflg=0）用于配件更换频次，完整树用于修复时长
async function loadClassTrees() {
    try {
        const [m, a, f] = await Promise.all([
            fetchBomClassTree('1'),
            fetchBomClassTree('0'),
            fetchItemClassTree(),
        ])
        modelClassTree.value = m?.data || []
        accessoryClassTree.value = a?.data || []
        fullClassTree.value = f?.data || []
    } catch {
        modelClassTree.value = []
        accessoryClassTree.value = []
        fullClassTree.value = []
    }
}

onMounted(() => {
    loadClassTrees()
})

// 初始加载
loadModelRate()
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

.tab-content {
    padding: 8px;
}

.search-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
}

.field {
    display: flex;
    align-items: center;
    gap: 4px;
}

.field label {
    font-size: 13px;
    color: #606266;
    white-space: nowrap;
}
</style>
