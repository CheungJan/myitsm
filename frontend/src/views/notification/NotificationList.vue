<template>
    <div class="page">
        <div class="page-header">
            <h2>通知记录</h2>
            <div class="filter-bar">
                <el-radio-group v-model="filter.view" size="small" @change="doSearch">
                    <el-radio-button label="inbox">收件箱</el-radio-button>
                    <el-radio-button label="all" v-if="isAdmin">全量</el-radio-button>
                </el-radio-group>
                <el-select v-model="filter.channel" placeholder="渠道" clearable size="small" style="width:120px" @change="doSearch">
                    <el-option v-for="c in channels" :key="c.channel" :label="c.label" :value="c.channel" />
                </el-select>
                <el-select v-model="filter.send_status" placeholder="发送状态" clearable size="small" style="width:120px" @change="doSearch">
                    <el-option label="未发" value="pending" />
                    <el-option label="已发" value="sent" />
                    <el-option label="失败" value="failed" />
                </el-select>
                <el-input v-model="filter.ref_type" placeholder="关联类型" clearable size="small" style="width:120px" @keyup.enter="doSearch" />
                <el-input v-model="filter.ref_id" placeholder="关联ID" clearable size="small" style="width:140px" @keyup.enter="doSearch" />
                <el-button type="primary" size="small" @click="doSearch">查询</el-button>
                <el-button size="small" @click="doReset">重置</el-button>
                <el-button size="small" type="warning" @click="markAllRead" style="margin-left:auto">全部已读</el-button>
                <el-button v-if="selectedIds.length>0" size="small" type="success" @click="markSelectedRead">已读选中({{ selectedIds.length }})</el-button>
            </div>
        </div>
        <el-card shadow="never">
            <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDetail" @selection-change="onSelectionChange">
                <el-table-column prop="dispatch_id" width="70" label="流水号" />
                <el-table-column type="selection" width="40" />
                <el-table-column prop="template_id" label="模板ID" width="100" />
                <el-table-column prop="recipient" label="接收方" width="140" />
                <el-table-column label="渠道" width="70">
                    <template #default="{ row }"><el-tag size="small" :type="row.channel==='fetion'?'info':''">{{ row.channel==='fetion'?'飞信(历史)':row.channel }}</el-tag></template>
                </el-table-column>
                <el-table-column prop="ref_type" label="关联类型" width="100" />
                <el-table-column prop="ref_id" label="关联ID" width="100" />
                <el-table-column label="发送状态" width="90">
                    <template #default="{ row }"><el-tag :type="sendStatusTag(row.send_status)" size="small">{{ row.send_status || 'pending' }}</el-tag></template>
                </el-table-column>
                <el-table-column label="已读" width="70">
                    <template #default="{ row }">
                        <el-tag v-if="row.channel === 'internal'" :type="row.read_status === 'read' ? 'success' : 'info'" size="small">{{ row.read_status === 'read' ? '已读' : '未读' }}</el-tag>
                        <span v-else>-</span>
                    </template>
                </el-table-column>
                <el-table-column prop="send_time" label="发送时间" width="130" />
                <el-table-column label="操作" width="160" fixed="right">
                    <template #default="{ row }">
                        <el-button v-if="row.send_status !== 'sent' && row.channel !== 'fetion'" type="primary" link size="small" @click.stop="handleSend(row)">发送</el-button>
                        <el-button v-if="row.send_status === 'failed' && row.channel !== 'fetion'" type="warning" link size="small" @click.stop="handleSend(row)">重试</el-button>
                        <el-button v-if="row.channel === 'internal' && row.send_status === 'sent' && row.read_status !== 'read'" type="success" link size="small" @click.stop="handleRead(row)">标为已读</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
        </el-card>
        <el-dialog :title="'通知详情'" v-model="drawer" width="700px" @close="doSearch">
            <template v-if="detail">
                <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="模板ID">{{ detail.template_id || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="渠道">{{ detail.channel }}</el-descriptions-item>
                    <el-descriptions-item label="接收方">{{ detail.recipient }}</el-descriptions-item>
                    <el-descriptions-item label="发送状态"><el-tag :type="sendStatusTag(detail.send_status)" size="small">{{ detail.send_status || 'pending' }}</el-tag></el-descriptions-item>
                    <el-descriptions-item label="关联类型">{{ detail.ref_type || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="关联ID">{{ detail.ref_id || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="发送时间">{{ detail.send_time || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="重试次数">{{ detail.retry_count || 0 }}</el-descriptions-item>
                    <el-descriptions-item label="错误信息" :span="2">{{ detail.error_msg || '无' }}</el-descriptions-item>
                    <el-descriptions-item label="标题" :span="2">{{ detail.subject || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="正文" :span="2"><div class="notif-body">{{ detail.body || '-' }}</div></el-descriptions-item>
                </el-descriptions>
            </template>
            <template #footer>
                <el-button v-if="detail && detail.send_status !== 'sent'" type="primary" @click="handleSend(detail)">发送</el-button>
                <el-button @click="drawer = false">关闭</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useDetailDrawer } from '@/composables/useDetailDrawer'
import { useAuthStore } from '@/stores/auth'
import { fetchNotifications, sendNotification, markNotificationRead, fetchChannels } from '@/api/notification'
import type { NotifRecord, ChannelInfo } from '@/api/notification'

const route = useRoute()
const authStore = useAuthStore()
const channels = ref<ChannelInfo[]>([])
const { items, loading, page, perPage, total, onSearch } = useListPage<NotifRecord>(fetchNotifications)
const { drawer, detail, open } = useDetailDrawer<NotifRecord>()

// 管理员判断：组99 或有 notification:all 权限
const isAdmin = computed(() => authStore.permList.some(p => p.startsWith('99:') || p === 'notification:all'))

onMounted(async () => {
    try { const res = await fetchChannels(); channels.value = res.data.channels } catch { channels.value = [] }
})

const filter = reactive({ view: 'inbox', channel: '', send_status: '', ref_type: '', ref_id: '' })
const selectedIds = ref<number[]>([])
function onSelectionChange(rows: NotifRecord[]){ selectedIds.value = rows.map(r => r.id as number).filter(Boolean) }
async function markAllRead(){
  const unreads = items.value.filter(it => it.channel==='internal' && it.send_status==='sent' && it.read_status!=='read')
  for(const n of unreads){ try{ await markNotificationRead(n.id as number); n.read_status='read' }catch{} }
  ElMessage.success(`已标记 ${unreads.length} 条为已读`)
  doSearch()
}
async function markSelectedRead(){
  for(const id of selectedIds.value){ try{ await markNotificationRead(id) }catch{} }
  ElMessage.success(`已标记 ${selectedIds.value.length} 条为已读`)
  selectedIds.value = []
  doSearch()
}

function sendStatusTag(s: unknown) {
    const m: Record<string, string> = { pending: 'info', sent: 'success', failed: 'danger' }
    return m[String(s)] || 'info'
}

function buildParams(): Record<string, string> {
    const p: Record<string, string> = { view: filter.view }
    if (filter.channel) p.channel = filter.channel
    if (filter.send_status) p.send_status = filter.send_status
    if (filter.ref_type) p.ref_type = filter.ref_type
    if (filter.ref_id) p.ref_id = filter.ref_id
    return p
}

function doSearch() { onSearch(buildParams()) }
function doReset() {
    filter.channel = ''; filter.send_status = ''; filter.ref_type = ''; filter.ref_id = ''
    doSearch()
}

async function handleSend(row: NotifRecord) {
    const nid = row.id as number
    if (!nid) return
    try { await sendNotification(nid); ElMessage.success('发送成功'); doSearch() } catch { ElMessage.error('发送失败') }
}

async function handleRead(row: NotifRecord) {
    const nid = row.id as number
    if (!nid) return
    try {
        await markNotificationRead(nid)
        ElMessage.success('已标记为已读')
        // 立即更新本地行，避免列表刷新后仍显示未读
        row.read_status = 'read'
        if (detail.value && (detail.value.id as number) === nid) {
            detail.value.read_status = 'read'
        }
        doSearch()
    } catch {
        ElMessage.error('操作失败')
    }
}

function openDetail(row: NotifRecord) {
    open(row)
}

// 弹窗打开时自动标记站内通知为已读
watch(drawer, async (visible) => {
    if (visible && detail.value && detail.value.channel === 'internal' && detail.value.read_status !== 'read') {
        await handleRead(detail.value as NotifRecord)
    }
})

onMounted(() => {
    const q = route.query
    if (q.ref_type) filter.ref_type = String(q.ref_type)
    if (q.ref_id) filter.ref_id = String(q.ref_id)
    if (q.send_status) filter.send_status = String(q.send_status)
    if (q.view) filter.view = String(q.view)
    doSearch()
    if (q.action === 'edit' || q.action === 'create') {
        setTimeout(() => { if (items.value.length > 0) openDetail(items.value[0]) }, 300)
    }
})
</script>

<style scoped>
.page { padding: 0 }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0 }
.filter-bar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap }
.notif-body { white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow: auto; line-height: 1.6 }
:deep(.el-descriptions__body) { table-layout: fixed }
:deep(.el-descriptions__label) { width: 80px; white-space: nowrap }
</style>
