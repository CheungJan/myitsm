<template>
    <div class="dashboard">
        <h2>欢迎使用 myitsm 设备运营管理平台</h2>
        <p>当前用户: {{ authStore.userName || authStore.userCode }}</p>
    </div>
</template>

<script lang="ts" setup>
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
</script>
