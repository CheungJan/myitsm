<template>
    <div class="dispatch-notify-editor">
        <el-form label-width="80px" size="small">
            <el-form-item label="收件人">
                <el-input :model-value="recipientLabel" disabled />
            </el-form-item>
            <el-form-item label="通知模板">
                <el-select v-model="templateId" style="width:100%" placeholder="选择派工通知模板" @change="onTemplateChange">
                    <el-option v-for="t in visibleTemplates" :key="t.template_id" :label="t.template_name + (t.is_default==='1'?'（默认）':'')" :value="t.template_id" />
                </el-select>
            </el-form-item>
            <el-form-item label="渠道">
                <el-select v-model="channel" style="width:100%" @change="onChannelChange">
                    <el-option v-for="c in channels" :key="c.channel" :label="c.label" :value="c.channel" :disabled="!c.enabled" />
                </el-select>
            </el-form-item>
            <el-form-item label="标题">
                <el-input v-model="subject" placeholder="通知标题" />
            </el-form-item>
            <el-form-item label="正文">
                <el-input v-model="body" type="textarea" :rows="8" placeholder="通知正文（Jinja2 渲染后）" />
            </el-form-item>
            <el-form-item v-if="!hideActions" label="操作">
                <el-button type="primary" :loading="sending" @click="handleSend">发送</el-button>
                <el-button @click="handleReset">重置为模板</el-button>
            </el-form-item>
        </el-form>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchNotifTemplates, fetchChannels, previewNotifTemplate } from '@/api/notification'
import { sendDispatchNotification } from '@/api/itsm'
import type { ChannelInfo, NotifTemplate } from '@/api/notification'

const props = defineProps<{
    dispatchId: number | null
    recipient: string
    recipientName?: string
    maintenanceId?: string
    storeId?: string
    faultType?: string
    defaultChannel?: string
    /** 隐藏内置操作按钮（新增派工时由父组件控制发送） */
    hideActions?: boolean
}>()

const emit = defineEmits<{ (e: 'sent', data: Record<string, unknown>): void }>()

const channels = ref<ChannelInfo[]>([])
const templates = ref<NotifTemplate[]>([])
const templateId = ref('')
const channel = ref(props.defaultChannel || 'internal')
const subject = ref('')
const body = ref('')
const sending = ref(false)

const recipientLabel = computed(() => {
    const nm = props.recipientName || ''
    return nm ? `${nm} (${props.recipient})` : props.recipient
})

/** 模板下拉按当前渠道筛选：同 channel 优先，无匹配则显示全部 */
const visibleTemplates = computed(() => {
    const matched = templates.value.filter(t => (t.channel || '') === channel.value)
    return matched.length > 0 ? matched : templates.value
})

onMounted(async () => {
    try { const res = await fetchChannels(); channels.value = res.data.channels } catch { channels.value = [] }
    await loadTemplates()
})

watch(() => props.dispatchId, () => loadTemplates())

async function loadTemplates() {
    try {
        const res = await fetchNotifTemplates({ ref_type: 'dispatch' })
        const all = (res.data.items as unknown as NotifTemplate[]) || []
        templates.value = all
        await selectTemplateForChannel(channel.value, all)
    } catch {
        ElMessage.warning('加载派工通知模板失败')
    }
}

/** 按当前渠道筛选模板：同 channel 优先，无则回退到默认/第一个 */
async function selectTemplateForChannel(ch: string, list?: NotifTemplate[]) {
    const all = list || templates.value
    const matched = all.filter(t => (t.channel || '') === ch)
    const pool = matched.length > 0 ? matched : all
    const def = pool.find(t => t.is_default === '1')
    const target = def || pool[0]
    if (target) {
        templateId.value = target.template_id as string
        await renderTemplate(target)
    } else {
        templateId.value = ''
        subject.value = ''
        body.value = ''
    }
}

async function onChannelChange() {
    await selectTemplateForChannel(channel.value)
}

async function renderTemplate(tpl: NotifTemplate) {
    const context: Record<string, string> = {
        maintenance_id: props.maintenanceId || '',
        store_id: props.storeId || '',
        accpectder_name: props.recipientName || props.recipient || '',
        accpectd_group: '',
        fault_type: props.faultType || '',
    }
    const pv = await previewNotifTemplate({ subject: tpl.subject || '', body: tpl.body || '', context })
    subject.value = pv.data.subject || ''
    body.value = pv.data.body || ''
}

async function onTemplateChange(id: string) {
    const tpl = templates.value.find(t => t.template_id === id)
    if (tpl) await renderTemplate(tpl)
}

function handleReset() { 
    const tpl = templates.value.find(t => t.template_id === templateId.value)
    if (tpl) renderTemplate(tpl)
}

async function handleSend() {
    if (!props.dispatchId) {
        ElMessage.warning('派工记录未保存，无法发送')
        return
    }
    sending.value = true
    try {
        const res = await sendDispatchNotification(props.dispatchId, {
            channel: channel.value,
            subject: subject.value,
            body: body.value,
            template_id: templateId.value,
        })
        ElMessage.success('发送成功')
        emit('sent', res.data || {})
    } catch {
        ElMessage.error('发送失败')
    } finally {
        sending.value = false
    }
}

defineExpose({ channel, subject, body, templateId })
</script>

<style scoped>
.dispatch-notify-editor { padding: 0 }
</style>
