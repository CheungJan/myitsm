<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>客户管理（共 {{ customers.length }} 条）</span>
                    <el-button type="primary" size="small" @click="handleAdd">新增客户</el-button>
                </div>
            </template>
            <el-table :data="customers" v-loading="loading" stripe>
                <el-table-column prop="cust_cd" label="客户编码" width="120" />
                <el-table-column prop="cust_nm" label="客户名称" width="200" />
                <el-table-column prop="class_cd" label="分类" width="100" />
                <el-table-column prop="busi_typ" label="业务类型" width="100" />
                <el-table-column prop="phone_no" label="电话" width="140" />
                <el-table-column prop="contactor" label="联系人" width="100" />
                <el-table-column prop="address" label="地址" min-width="180" />
                <el-table-column prop="useflg" label="状态" width="80" />
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
import { fetchCustomers } from '@/api/master'

const customers = ref<Record<string,unknown>[]>([])
const loading = ref(false)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchCustomers()
        customers.value = (res.data || []) as never[]
    } finally { loading.value = false }
}
function handleAdd() { ElMessage.info('新增功能待实现') }
function handleEdit(row: unknown) { ElMessage.info(`编辑: ${(row as Record<string,string>).cust_cd}`) }
function handleDelete(row: unknown) { ElMessage.info(`删除: ${(row as Record<string,string>).cust_cd}`) }
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
