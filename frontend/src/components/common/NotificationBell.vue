<template>
  <el-popover :visible="popVisible" placement="bottom-end" :width="360" trigger="click" @show="loadNotifications">
    <template #reference>
      <el-badge :value="unreadCount" :hidden="unreadCount===0" :max="99" class="bell-badge">
        <el-button size="small" circle :icon="Bell" @click="popVisible=!popVisible" />
      </el-badge>
    </template>
    <div style="max-height:400px;overflow:auto">
      <div v-if="notifications.length===0" style="text-align:center;padding:20px;color:#999">暂无通知</div>
      <div v-for="n in notifications" :key="n.id" class="notify-item" :class="{unread:n.read_status!=='read'}" style="padding:10px;border-bottom:1px solid #eee;cursor:pointer" @click="markRead(n)">
        <div style="font-size:13px;font-weight:600;margin-bottom:4px">{{ n.subject || '系统通知' }}</div>
        <div style="font-size:12px;color:#666;margin-bottom:4px">{{ n.body || '' }}</div>
        <div style="font-size:11px;color:#999">{{ n.gendate || '' }} · {{ n.ref_type || '' }}</div>
      </div>
    </div>
    <div style="text-align:center;padding:8px;border-top:1px solid #eee" v-if="notifications.length>0">
      <el-button size="small" text @click="markAllRead">全部已读</el-button>
    </div>
  </el-popover>
</template>
<script setup lang="ts">import {ref,onMounted} from 'vue';import {Bell} from '@element-plus/icons-vue';import request from '@/api/request';import {fetchUnreadCount,markNotificationRead} from '@/api/notification'
const popVisible=ref(false)
interface NotifyItem {id:number;subject?:string;body?:string;send_status?:string;read_status?:string;ref_type?:string;ref_id?:string;gendate?:string}
const notifications=ref<NotifyItem[]>([])
const unreadCount=ref(0)
async function loadUnreadCount(){try{const r=await fetchUnreadCount();unreadCount.value=r.data?.count||0}catch{}}
async function loadNotifications(){try{const r=await request.get('/notification/notifications',{params:{page:1,per_page:50,channel:'internal',send_status:'sent'}});notifications.value=(r.data?.items||[]) as NotifyItem[];await loadUnreadCount()}catch{}}
async function markRead(n:NotifyItem){if(n.read_status==='read')return;try{await markNotificationRead(n.id);n.read_status='read';unreadCount.value=Math.max(0,unreadCount.value-1)}catch{}}
async function markAllRead(){for(const n of notifications.value.filter(x=>x.read_status!=='read')){await markRead(n)}}
onMounted(()=>{loadUnreadCount();setInterval(loadUnreadCount,60000)})
</script>
<style scoped>.bell-badge{margin-right:4px}.notify-item.unread{background:#f0f7ff}.notify-item:hover{background:#f5f7fa}</style>
