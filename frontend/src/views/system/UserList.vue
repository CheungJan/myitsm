<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>用户管理（共 {{ total }} 条）</span>
                    <div class="filter-bar">
                        <el-input v-model="search" placeholder="搜索用户名" clearable style="width:180px" @keyup.enter="loadData" />
                        <el-button type="primary" size="small" style="margin-left:8px" @click="loadData">查询</el-button>
                    </div>
                </div>
            </template>
            <el-table :data="users" v-loading="loading" stripe>
                <el-table-column prop="user_cd" label="编码" width="100" />
                <el-table-column prop="user_nm" label="姓名" width="120" />
                <el-table-column prop="dept_cd" label="部门" width="100" />
                <el-table-column prop="phone" label="电话" width="130" />
                <el-table-column prop="email" label="邮箱" width="160" />
                <el-table-column prop="status" label="状态" width="80" />
                <el-table-column prop="created_at" label="创建时间" min-width="150" />
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchUsers } from '@/api/system'

const users = ref<Record<string,unknown>[]>([])
const loading = ref(false); const search = ref(''); const page = ref(1); const perPage = ref(20); const total = ref(0)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchUsers()
        let list = (res.data || []) as never[]
        if (search.value) {
            const q = search.value.toLowerCase()
            list = list.filter(r => (r as Record<string,string>).user_nm?.toLowerCase().includes(q))
        }
        total.value = list.length
        const start = (page.value - 1) * 20
        users.value = list.slice(start, start + 20)
    } finally { loading.value = false }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.filter-bar { display: flex; align-items: center; }
</style>
