<template>
    <div class="page">
        <el-card header="系统参数（当前已生效）">
            <el-form :model="form" label-width="140px" style="max-width:600px">
                <el-divider content-position="left">仓储配置</el-divider>
                <el-form-item label="成本核算方式">
                    <el-select v-model="form.costtype" style="width:240px">
                        <el-option label="移动加权" value="1" />
                        <el-option label="先进先出" value="2" />
                    </el-select>
                </el-form-item>
                <el-form-item label="中心仓库编码">
                    <el-input v-model="form.centralwarehouse" style="width:240px" />
                </el-form-item>

                <el-divider content-position="left">采购/销售配置</el-divider>
                <el-form-item label="采购计划失效天数">
                    <el-input-number v-model="form.poinvaliddays" :min="1" :max="365" />
                </el-form-item>
                <el-form-item label="销售单失效天数">
                    <el-input-number v-model="form.soinvaliddays" :min="1" :max="365" />
                </el-form-item>
                <el-form-item label="门店单据类型">
                    <el-input-number v-model="form.shopbilltype" :min="0" :max="99" />
                </el-form-item>

                <el-divider content-position="left">系统安全</el-divider>
                <el-form-item label="允许多点登录">
                    <el-switch v-model="form.allowmultilogon" active-value="1" inactive-value="0" />
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchSysparms, updateSysparm } from '@/api/system'

const form = reactive({
    costtype: '1', centralwarehouse: '', poinvaliddays: 1,
    soinvaliddays: 1, shopbilltype: '1', allowmultilogon: '1',
})
const saving = ref(false)

onMounted(async () => {
    try {
        const res = await fetchSysparms()
        const list = (res.data || []) as Record<string,unknown>[]
        if (list.length > 0) {
            const r = list[0]
            form.costtype = (r.costtype as string) || '1'
            form.centralwarehouse = (r.centralwarehouse as string) || ''
            form.poinvaliddays = Number(r.poinvaliddays) || 1
            form.soinvaliddays = Number(r.soinvaliddays) || 1
            form.shopbilltype = (r.shopbilltype as string) || '1'
            form.allowmultilogon = (r.allowmultilogon as string) || '1'
        }
    } catch { /* */ }
})

async function handleSave() {
    saving.value = true
    try {
        await updateSysparm('SYSPARM', { ...form })
        ElMessage.success('保存成功')
    } finally { saving.value = false }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
</style>
