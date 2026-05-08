<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>客户管理</span>
                    <el-button type="primary" size="small">新增客户</el-button>
                </div>
            </template>
            <el-table :data="customers" v-loading="loading" stripe>
                <el-table-column prop="cust_cd" label="客户编码" width="120" />
                <el-table-column prop="cust_nm" label="客户名称" width="200" />
                <el-table-column prop="class_cd" label="分类" width="100" />
                <el-table-column prop="contact_name" label="联系人" width="120" />
                <el-table-column prop="phone_no" label="电话" width="140" />
                <el-table-column prop="address" label="地址" min-width="200" />
                <el-table-column prop="useflg" label="状态" width="80" />
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
import { fetchCustomers, type CustomerRecord } from '@/api/master'

const customers = ref<CustomerRecord[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchCustomers({ page: String(page.value), per_page: '20' })
        customers.value = (res.data as unknown as CustomerRecord[]) || []
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
