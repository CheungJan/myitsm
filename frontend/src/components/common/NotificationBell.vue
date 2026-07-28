<template>
  <div class="bell-wrapper">
    <el-badge :value="unreadCount" :hidden="unreadCount===0" :max="99" class="bell-badge">
      <el-button size="small" circle :icon="Bell" @click="toggleBell" />
    </el-badge>
    <!-- 手动实现的通知下拉面板，避免 el-popover 内部事件拦截 -->
    <div v-if="popVisible" class="bell-dropdown" @click.stop>
      <div style="max-height:400px;overflow:auto">
        <div v-if="notifications.length===0" style="text-align:center;padding:20px;color:#999">暂无通知</div>
        <div
          v-for="n in notifications" :key="n.id"
          class="notify-item" :class="{unread:n.read_status!=='read'}"
          style="padding:10px;border-bottom:1px solid #eee;cursor:pointer"
          @click="handleClick(n)"
        >
          <div style="font-size:13px;font-weight:600;margin-bottom:4px">{{ n.subject || '系统通知' }}</div>
          <div style="font-size:12px;color:#666;margin-bottom:4px">{{ n.body || '' }}</div>
          <div style="font-size:11px;color:#999">{{ n.gendate || '' }} · {{ n.ref_type || '' }}</div>
        </div>
      </div>
      <div style="text-align:center;padding:8px;border-top:1px solid #eee" v-if="notifications.length>0">
        <el-button size="small" text @click="markAllRead">全部已读</el-button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Bell } from '@element-plus/icons-vue'
import request from '@/api/request'
import { fetchUnreadCount, markNotificationRead } from '@/api/notification'

const router = useRouter()
const popVisible = ref(false)

interface NotifyItem {
    id: number; subject?: string; body?: string; send_status?: string
    read_status?: string; ref_type?: string; ref_id?: string; gendate?: string
}
const notifications = ref<NotifyItem[]>([])
const unreadCount = ref(0)

async function loadUnreadCount() {
    try { const r = await fetchUnreadCount(); unreadCount.value = r.data?.count || 0 } catch {}
}
async function loadNotifications() {
    try {
        const r = await request.get('/notification/notifications', {
            params: { page: 1, per_page: 50, channel: 'internal', send_status: 'sent', order: 'desc' }
        })
        notifications.value = (r.data?.items || []) as NotifyItem[]
        await loadUnreadCount()
    } catch {}
}

function toggleBell() {
    popVisible.value = !popVisible.value
    if (popVisible.value) loadNotifications()
}

// 点击外部关闭下拉面板
function onClickOutside(e: MouseEvent) {
    const wrapper = document.querySelector('.bell-wrapper')
    if (wrapper && !wrapper.contains(e.target as Node)) {
        popVisible.value = false
    }
}

async function handleClick(n: NotifyItem) {
    popVisible.value = false
    if (n.read_status !== 'read') {
        try {
            await markNotificationRead(n.id)
            n.read_status = 'read'
            unreadCount.value = Math.max(0, unreadCount.value - 1)
        } catch {}
    }
    if (n.ref_type === 'dispatch' && n.ref_id) {
        router.push({ path: '/itsm/maintenance', query: { maintenance_id: n.ref_id, tab: 'notify' } })
    } else if (n.ref_type && n.ref_id) {
        router.push({ path: '/notification', query: { ref_type: n.ref_type, ref_id: n.ref_id } })
    }
}

async function markRead(n: NotifyItem) {
    if (n.read_status === 'read') return
    try {
        await markNotificationRead(n.id)
        n.read_status = 'read'
        unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch {}
}
async function markAllRead() {
    for (const n of notifications.value.filter(x => x.read_status !== 'read')) { await markRead(n) }
}

onMounted(() => {
    loadUnreadCount()
    setInterval(loadUnreadCount, 60000)
    document.addEventListener('click', onClickOutside)
})
onBeforeUnmount(() => {
    document.removeEventListener('click', onClickOutside)
})
</script>
<style scoped>
.bell-wrapper { position: relative; display: inline-block }
.bell-badge { margin-right: 4px }
.bell-dropdown {
    position: absolute; right: 0; top: 100%; margin-top: 4px;
    width: 360px; background: #fff; border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0,0,0,.12); z-index: 2000;
}
.notify-item.unread { background: #f0f7ff }
.notify-item:hover { background: #f5f7fa }
</style>
