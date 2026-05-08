<template>
    <div class="page">
        <el-card>
            <template #header><span>部门管理（共 {{ total }} 条）</span></template>
            <el-table :data="depts" v-loading="loading" stripe>
                <el-table-column prop="dept_cd" label="编码" width="120" />
                <el-table-column prop="dept_nm" label="名称" width="200" />
                <el-table-column prop="parent_cd" label="上级部门" width="120" />
                <el-table-column prop="useflg" label="状态" width="80" />
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchDepartments } from '@/api/system'

const depts = ref<Record<string,unknown>[]>([])
const loading = ref(false); const page = ref(1); const perPage = ref(20); const total = ref(0)

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchDepartments()
        const list = (res.data || []) as never[]
        total.value = list.length
        depts.value = list.slice((page.value-1)*perPage.value, page.value*perPage.value)
    } finally { loading.value = false }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
</style>
