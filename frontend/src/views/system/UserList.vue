<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>用户管理</span>
                    <el-button type="primary" size="small">新增用户</el-button>
                </div>
            </template>
            <el-table :data="users" v-loading="loading" stripe>
                <el-table-column prop="user_cd" label="用户编码" width="120" />
                <el-table-column prop="user_nm" label="用户名" width="120" />
                <el-table-column prop="dept_cd" label="部门" width="100" />
                <el-table-column prop="phone" label="电话" width="140" />
                <el-table-column prop="email" label="邮箱" width="180" />
                <el-table-column prop="useflg" label="状态" width="80" />
                <el-table-column prop="created_at" label="创建时间" min-width="160" />
                <el-table-column label="操作" width="150" fixed="right">
                    <template #default>
                        <el-button type="primary" link size="small">编辑</el-button>
                        <el-button type="danger" link size="small">禁用</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination
                v-model:current-page="page"
                :total="total"
                :page-size="20"
                layout="total, prev, pager, next"
                @current-change="loadUsers"
                style="margin-top: 16px; justify-content: flex-end"
            />
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { fetchUsers, type UserItem } from '@/api/system'

const users = ref<UserItem[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

onMounted(() => loadUsers())

async function loadUsers() {
    loading.value = true
    try {
        const res = await fetchUsers({ page: String(page.value), per_page: '20' })
        users.value = res.data || []
        total.value = res.total || 0
    } finally {
        loading.value = false
    }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
