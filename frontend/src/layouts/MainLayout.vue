<template>
    <el-container class="main-layout">
        <el-aside :width="isCollapse ? '64px' : '220px'">
            <div class="logo">myitsm</div>
            <AppMenu :is-collapse="isCollapse" />
        </el-aside>
        <el-container>
            <el-header class="layout-header">
                <div class="header-left">
                    <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
                        <Fold v-if="!isCollapse" />
                        <Expand v-else />
                    </el-icon>
                    <el-breadcrumb separator="/">
                        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
                        <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
                    </el-breadcrumb>
                </div>
                <div class="header-right">
                    <span class="user-name">{{ userName }}</span>
                    <el-button text @click="handleLogout">退出</el-button>
                </div>
            </el-header>
            <AppTabs />
            <el-main>
                <router-view />
            </el-main>
        </el-container>
    </el-container>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppMenu from '@/components/AppMenu.vue'
import AppTabs from '@/components/AppTabs.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapse = ref(false)
const userName = computed(() => authStore.userName || authStore.userCode)

onMounted(async () => {
    await authStore.fetchSession()
})

async function handleLogout() {
    await authStore.logout()
    router.push('/login')
}
</script>

<style lang="scss" scoped>
.main-layout {
    height: 100vh;
}
.el-aside {
    background-color: #304156;
    overflow: hidden auto;
}
.logo {
    height: 60px;
    line-height: 60px;
    text-align: center;
    color: #fff;
    font-size: 18px;
    font-weight: bold;
    background-color: #263445;
}
.layout-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fff;
    border-bottom: 1px solid #e6e6e6;
    height: 50px;
}
.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}
.collapse-btn {
    font-size: 20px;
    cursor: pointer;
}
.header-right {
    display: flex;
    align-items: center;
    gap: 12px;
}
.user-name {
    color: #606266;
}
.el-main {
    background-color: #f0f2f5;
}
</style>
