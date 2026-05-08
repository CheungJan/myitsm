<template>
    <el-menu
        :collapse="isCollapse"
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
    >
        <template v-for="item in menuTree" :key="item.menu_cd">
            <el-sub-menu v-if="item.children && item.children.length" :index="item.menu_cd">
                <template #title>
                    <el-icon><Folder /></el-icon>
                    <span>{{ item.menu_nm }}</span>
                </template>
                <el-menu-item
                    v-for="child in item.children"
                    :key="child.menu_cd"
                    :index="child.path || '/' + child.menu_cd"
                >
                    {{ child.menu_nm }}
                </el-menu-item>
            </el-sub-menu>
            <el-menu-item v-else :index="item.path || '/' + item.menu_cd">
                <el-icon><Document /></el-icon>
                <span>{{ item.menu_nm }}</span>
            </el-menu-item>
        </template>
    </el-menu>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { FRONTEND_MENUS } from '@/config/menu'

defineProps<{ isCollapse: boolean }>()

const route = useRoute()
const activeMenu = computed(() => route.path)
const menuTree = FRONTEND_MENUS
</script>
