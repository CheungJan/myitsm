<template>
    <div class="login-wrapper">
        <el-card class="login-card">
            <h2 class="login-title">myitsm 设备运营管理平台</h2>
            <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
                <el-form-item prop="userId">
                    <el-input v-model="form.userId" placeholder="用户名" />
                </el-form-item>
                <el-form-item prop="password">
                    <el-input v-model="form.password" type="password" placeholder="密码"
                        @keyup.enter="handleLogin" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" :loading="loading" @click="handleLogin" style="width:100%">
                        登录
                    </el-button>
                </el-form-item>
            </el-form>
            <p v-if="errorMsg" class="login-error">{{ errorMsg }}</p>
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ userId: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

const rules = {
    userId: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
    loading.value = true
    errorMsg.value = ''
    try {
        await authStore.doLogin(form.userId, form.password)
        router.push('/')
    } catch {
        errorMsg.value = '登录失败，请检查用户名和密码'
    } finally {
        loading.value = false
    }
}
</script>

<style lang="scss" scoped>
.login-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f0f2f5;
}
.login-card {
    width: 400px;
}
.login-title {
    text-align: center;
    margin-bottom: 24px;
    color: #303133;
}
.login-error {
    color: #f56c6c;
    text-align: center;
    margin: 0;
}
</style>
