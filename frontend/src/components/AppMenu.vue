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
                    :index="child.exe_path || '/' + child.menu_cd"
                >
                    {{ child.menu_nm }}
                </el-menu-item>
            </el-sub-menu>
            <el-menu-item v-else :index="item.exe_path || '/' + item.menu_cd">
                <el-icon><Document /></el-icon>
                <span>{{ item.menu_nm }}</span>
            </el-menu-item>
        </template>
    </el-menu>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchMenus } from '@/api/system'

defineProps<{ isCollapse: boolean }>()

const route = useRoute()
const activeMenu = computed(() => route.path)

interface FlatMenu {
    menu_cd: string; menu_nm: string
    parent: string | null; exe_path?: string; ordno?: number
}
interface TreeMenu extends FlatMenu { children?: TreeMenu[] }

const menuTree = ref<TreeMenu[]>([])

function buildTree(flat: FlatMenu[]): TreeMenu[] {
    const map = new Map<string, TreeMenu>()
    const roots: TreeMenu[] = []
    for (const item of flat) {
        map.set(item.menu_cd, { ...item, children: [] })
    }
    for (const item of map.values()) {
        if (item.parent && map.has(item.parent)) {
            map.get(item.parent)!.children!.push(item)
        } else {
            roots.push(item)
        }
    }
    return roots.filter(r => r.children!.length > 0 || r.exe_path)
}

onMounted(async () => {
    try {
        const res = await fetchMenus()
        const flat = (res.data || []) as FlatMenu[]
        menuTree.value = buildTree(flat)
    } catch {
        menuTree.value = []
    }
})
</script>
