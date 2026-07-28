<template>
    <div class="app-tabs">
        <el-tag
            v-for="tab in tabs"
            :key="tab.path"
            :type="tab.path === activeTab ? '' : 'info'"
            :closable="tab.path !== '/dashboard'"
            class="tab-item"
            @click="router.push(tab.path)"
            @close="removeTab(tab.path)"
        >
            {{ tab.title }}
        </el-tag>
    </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const activeTab = computed(() => route.path)

const tabs = computed(() => {
    return [
        { path: '/dashboard', title: '首页' }
    ]
})

function removeTab(path: string) {
    if (tabs.value.length <= 1) return
    const idx = tabs.value.findIndex(t => t.path === path)
    if (idx === -1) return
    tabs.value.splice(idx, 1)
    if (path === activeTab.value) {
        router.push(tabs.value[Math.min(idx, tabs.value.length - 1)].path)
    }
}
</script>

<style lang="scss" scoped>
.app-tabs {
    display: flex;
    gap: 6px;
    padding: 8px 12px;
    background: #fff;
    border-bottom: 1px solid #e6e6e6;
    flex-wrap: wrap;
}
.tab-item {
    cursor: pointer;
}
</style>
