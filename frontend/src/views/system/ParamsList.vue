<template>
    <div class="page">
        <el-card header="全局系统参数" v-loading="loading">
            <el-form v-if="!loading" :model="form" label-width="160px" style="max-width:600px">
                <el-divider content-position="left">认证安全</el-divider>
                <el-form-item label="允许多点登录">
                    <el-switch v-model="form.allowmultilogon" active-value="1" inactive-value="0" />
                </el-form-item>
                <el-form-item label="JWT会话超时(秒)">
                    <el-input-number v-model="form.jwt_expiration_seconds" :min="60" :step="3600" />
                </el-form-item>

                <el-divider content-position="left">系统运维</el-divider>
                <el-form-item label="日志保留天数">
                    <el-input-number v-model="form.log_retention_days" :min="1" :max="365" />
                </el-form-item>
                <el-form-item label="文件上传限制(MB)">
                    <el-input-number v-model="form.max_upload_size_mb" :min="1" :max="1024" />
                </el-form-item>

                <el-divider content-position="left">路径配置</el-divider>
                <el-form-item label="自动备份路径">
                    <el-input v-model="form.autobackpath" style="width:300px" />
                </el-form-item>
                <el-form-item label="发票共享路径">
                    <el-input v-model="form.invoicesharepath" style="width:300px" />
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
    allowmultilogon: '1', jwt_expiration_seconds: 28800,
    log_retention_days: 30, max_upload_size_mb: 10,
    autobackpath: '', invoicesharepath: '',
})
const saving = ref(false)
const loading = ref(true)

onMounted(async () => {
    try {
        const res = await fetchSysparms()
        const list = (res.data || []) as Record<string,unknown>[]
        if (list.length > 0) {
            const r = list[0]
            form.allowmultilogon = (r.allowmultilogon as string) || '1'
            form.jwt_expiration_seconds = Number(r.jwt_expiration_seconds) || 28800
            form.log_retention_days = Number(r.log_retention_days) || 30
            form.max_upload_size_mb = Number(r.max_upload_size_mb) || 10
            form.autobackpath = (r.autobackpath as string) || ''
            form.invoicesharepath = (r.invoicesharepath as string) || ''
        }
    } catch { /* */ }
    finally { loading.value = false }
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
