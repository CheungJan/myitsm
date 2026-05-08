<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>物料管理（共 {{ items.length }} 条）</span>
                    <el-button type="primary" size="small" @click="handleAdd">新增物料</el-button>
                </div>
            </template>
            <el-table :data="items" v-loading="loading" stripe>
                <el-table-column prop="item_cd" label="物料编码" width="120" />
                <el-table-column prop="item_nm" label="物料名称" width="180" />
                <el-table-column prop="class_cd" label="分类编码" width="100" />
                <el-table-column prop="item_anm" label="别名" width="120" />
                <el-table-column prop="unit" label="单位" width="80" />
                <el-table-column prop="useflg" label="状态" width="80" />
                <el-table-column prop="created_at" label="创建时间" width="160" />
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
import { fetchItems } from '@/api/master'

const items = ref<Record<string,unknown>[]>([])
const loading = ref(false)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchItems()
        items.value = (res.data || []) as never[]
    } finally { loading.value = false }
}
function handleAdd() { ElMessage.info('新增功能待实现') }
function handleEdit(row: unknown) { ElMessage.info(`编辑: ${(row as Record<string,string>).item_cd}`) }
function handleDelete(row: unknown) { ElMessage.info(`删除: ${(row as Record<string,string>).item_cd}`) }
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
