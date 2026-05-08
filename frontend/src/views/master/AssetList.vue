<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>资产台账（共 {{ assets.length }} 条）</span>
                    <el-button type="primary" size="small" @click="handleAdd">新增记录</el-button>
                </div>
            </template>
            <el-table :data="assets" v-loading="loading" stripe>
                <el-table-column prop="eid" label="设备 SN" width="160" />
                <el-table-column prop="custcd" label="客户编码" width="120" />
                <el-table-column prop="itemcd" label="物料编码" width="120" />
                <el-table-column prop="status" label="状态" width="80" />
                <el-table-column prop="asset_type" label="资产类型" width="100" />
                <el-table-column prop="area" label="区域" width="80" />
                <el-table-column prop="startdate" label="开通日期" width="120" />
                <el-table-column label="操作" width="180" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
                        <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchAssets } from '@/api/master'

const assets = ref<Record<string,unknown>[]>([])
const loading = ref(false)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchAssets()
        assets.value = (res.data || []) as never[]
    } finally { loading.value = false }
}
function handleAdd() { ElMessage.info('新增功能待实现') }
function handleEdit(row: unknown) { ElMessage.info(`编辑: ${(row as Record<string,string>).eid}`) }
function handleDelete(row: unknown) { ElMessage.info(`删除: ${(row as Record<string,string>).eid}`) }
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
