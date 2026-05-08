<template>
    <div class="page">
        <el-card>
            <template #header>
                <span>用户组管理</span>
            </template>
            <el-table :data="groups" v-loading="loading" stripe>
                <el-table-column prop="group_cd" label="组编码" width="120" />
                <el-table-column prop="group_nm" label="组名称" width="200" />
                <el-table-column label="操作" width="120">
                    <template #default>
                        <el-button type="primary" link size="small">成员管理</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchGroups } from '@/api/system'

const groups = ref<Record<string,unknown>[]>([])
const loading = ref(false); const page = ref(1); const perPage = ref(20); const total = ref(0)

onMounted(async () => {
    loading.value = true
    try {
        const res = await fetchGroups()
        const list = (res.data || []) as never[]; total.value = list.length; groups.value = list.slice((page.value-1)*perPage.value, page.value*perPage.value)
    } finally {
        loading.value = false
    }
})
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
</style>
