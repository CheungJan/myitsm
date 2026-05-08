<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>EID 设备管理（共 {{ eids.length }} 条）</span>
                    <el-button type="primary" size="small" @click="handleAdd">新增设备</el-button>
                </div>
            </template>
            <el-table :data="eids" v-loading="loading" stripe>
                <el-table-column prop="eid" label="设备 SN" width="160" />
                <el-table-column prop="item_cd" label="物料编码" width="120" />
                <el-table-column prop="etyp" label="类型" width="80" />
                <el-table-column prop="whcd" label="仓库" width="80" />
                <el-table-column prop="sflg" label="状态" width="80" />
                <el-table-column prop="new_old" label="新旧" width="80" />
                <el-table-column prop="useflg" label="有效" width="80" />
                <el-table-column prop="prddate" label="生产日期" width="120" />
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
import { fetchEidList } from '@/api/master'

const eids = ref<Record<string,unknown>[]>([])
const loading = ref(false)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchEidList()
        eids.value = (res.data || []) as never[]
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
