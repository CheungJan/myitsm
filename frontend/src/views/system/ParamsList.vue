<template>
    <div class="page">
        <el-card>
            <template #header><span>系统参数</span></template>
            <el-table :data="params" v-loading="loading" stripe>
                <el-table-column prop="parm_cd" label="参数编码" width="180" />
                <el-table-column prop="parm_nm" label="参数名称" width="200" />
                <el-table-column prop="parm_val" label="参数值" min-width="200" />
            </el-table>
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { fetchSysparms } from '@/api/system'

const params = ref<Record<string,unknown>[]>([])
const loading = ref(false)

onMounted(async () => {
    loading.value = true
    try {
        const res = await fetchSysparms()
        params.value = res.data || []
    } finally {
        loading.value = false
    }
})
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
</style>
