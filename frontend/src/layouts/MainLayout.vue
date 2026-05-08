<template>
    <el-container class="main-layout">
        <el-aside :width="isCollapse ? '64px' : '220px'">
            <div class="logo">myitsm</div>
            <el-menu
                :collapse="isCollapse"
                :default-active="activeMenu"
                router
                background-color="#304156"
                text-color="#bfcbd9"
                active-text-color="#409eff"
            >
                <el-menu-item index="/dashboard">
                    <el-icon><HomeFilled /></el-icon>
                    <span>首页</span>
                </el-menu-item>
            </el-menu>
        </el-aside>
        <el-container>
            <el-header class="layout-header">
                <div class="header-left">
                    <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
                        <Fold v-if="!isCollapse" />
                        <Expand v-else />
                    </el-icon>
                </div>
                <div class="header-right">
                    <span class="user-name">{{ userName }}</span>
                    <el-button text @click="handleLogout">退出</el-button>
                </div>
            </el-header>
            <el-main>
                <router-view />
            </el-main>
        </el-container>
    </el-container>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapse = ref(false)
const activeMenu = computed(() => route.path)
const userName = computed(() => authStore.userName || authStore.userCode)

function handleLogout() {
    authStore.logout()
    router.push('/login')
}
</script>

<style lang="scss" scoped>
.main-layout {
    height: 100vh;
}
.el-aside {
    background-color: #304156;
    overflow: hidden;
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
}
.header-left {
    display: flex;
    align-items: center;
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
