<template>
  <div class="sub-table-pane">
    <el-table :data="list" size="small" empty-text="暂无">
      <slot name="columns" />
      <el-table-column prop="create_time" label="创建时间" width="120"/>
      <el-table-column v-if="updateFn" label="操作" width="80">
        <template #default="{ row }">
          <el-button v-if="!isRowEditDisabled(row)" size="small" link type="primary" @click="openEdit(row)">编辑</el-button>
          <span v-else style="color:#909399">-</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 底部公用操作栏（对齐 PB 布局） -->
    <div class="sub-table-footer">
      <el-button v-if="!createDisabled" size="small" type="primary" @click="openForm">新增{{ title }}</el-button>
    </div>

    <el-dialog v-model="dialogVisible" :title="(editId ? '编辑' : '新增') + title" width="650px">
      <el-form :model="form" label-width="90px" size="small" :rules="rules" ref="formRef">
        <slot name="form" :form="form" />
      </el-form>
      <DispatchNotifyEditor
        v-if="notifyContext && !editId"
        ref="notifyEditorRef"
        :dispatch-id="null"
        :recipient="(notifyContext.accpectder as string) || ''"
        :recipient-name="(notifyContext.accpectder_name as string) || ''"
        :maintenance-id="(notifyContext.maintenance_id as string) || ''"
        :store-id="(notifyContext.store_id as string) || ''"
        :fault-type="(notifyContext.fault_type as string) || ''"
        hide-actions
      />
      <template #footer>
        <el-button size="small" @click="dialogVisible=false">取消</el-button>
        <el-button v-if="notifyContext && !editId" size="small" @click="submitForm">仅保存</el-button>
        <el-button size="small" type="primary" @click="submitAndSend" v-if="notifyContext && !editId">保存并发送</el-button>
        <el-button v-else size="small" type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { SubRecord } from '@/api/itsm'
import { sendDispatchNotification } from '@/api/itsm'
import DispatchNotifyEditor from './DispatchNotifyEditor.vue'

const props = defineProps<{
  maintenanceId: string
  title: string
  fetchFn: (mid: string) => Promise<{ data?: SubRecord[] }>
  createFn: (data: Record<string, unknown>) => Promise<unknown>
  updateFn?: (recordId: number, data: Record<string, unknown>) => Promise<unknown>
  rules?: Record<string, Array<{ required?: boolean; message?: string; trigger?: string }>>
  /** 行级编辑禁用判断（返回 true 时该行不显示编辑按钮） */
  rowEditDisabled?: (row: Record<string, unknown>) => boolean
  /** 整表禁用新增（如已关单） */
  createDisabled?: boolean
  /** 新建表单初始默认值 */
  defaultForm?: Record<string, unknown>
  /** 通知上下文（派工表单专用：提供后显示消息编辑器+"保存并发送"按钮） */
  notifyContext?: Record<string, unknown>
}>()

const emit = defineEmits<{ saved: [data: Record<string, unknown>]; sent: [data: Record<string, unknown>] }>()

function isRowEditDisabled(row: Record<string, unknown>): boolean {
  return !!props.rowEditDisabled && props.rowEditDisabled(row)
}

const list = ref<SubRecord[]>([])
const dialogVisible = ref(false)
const form = ref<Record<string, unknown>>({})
const editId = ref<number | null>(null)
const formRef = ref()

function openForm() {
  editId.value = null
  form.value = { maintenance_id: props.maintenanceId, ...(props.defaultForm || {}) }
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editId.value = (row.id as number) || null
  form.value = { ...row, maintenance_id: props.maintenanceId }
  dialogVisible.value = true
}

function cleanData(data: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(data)) {
    if (v === '') continue
    if (['price', 'payje'].includes(k) && v !== undefined && v !== null) {
      const n = Number(v)
      out[k] = Number.isNaN(n) ? v : n
    } else {
      out[k] = v
    }
  }
  return out
}

async function submitForm(): Promise<Record<string, unknown> | null> {
  if (!props.maintenanceId) return null
  // 校验
  if (props.rules && formRef.value) {
    try { await formRef.value.validate() } catch { return null }
  }
  const data = cleanData({ ...form.value, maintenance_id: props.maintenanceId })
  const isEdit = !!editId.value
  try {
    let result: Record<string, unknown> = data
    if (isEdit && props.updateFn && editId.value !== null) {
      await props.updateFn(editId.value, data)
    } else {
      const r = await props.createFn(data) as { data?: Record<string, unknown> }
      result = r?.data || data
    }
    ElMessage.success(isEdit ? '编辑成功' : '新增成功')
    dialogVisible.value = false
    await load()
    emit('saved', result)
    return result
  } catch {
    ElMessage.error(isEdit ? '编辑失败' : '新增失败')
    return null
  }
}

const notifyEditorRef = ref<InstanceType<typeof DispatchNotifyEditor> | null>(null)
async function submitAndSend(){
  // 先读取编辑器内容，再保存派工
  const editor = notifyEditorRef.value
  const channel = editor?.channel || 'internal'
  const subject = editor?.subject || ''
  const body = editor?.body || ''
  const template_id = editor?.templateId || ''
  const created = await submitForm()
  if(!created) return
  const id = created.id as number | undefined
  if(!id){ ElMessage.warning('未拿到派工记录ID，无法发送通知'); return }
  try{
    await sendDispatchNotification(id, { channel, subject, body, template_id })
    await load() // 刷新列表以显示最新通知状态
    ElMessage.success('已保存并发送通知')
    emit('sent', created)
  }catch{ ElMessage.error('发送通知失败') }
}

async function load() {
  if (!props.maintenanceId) return
  try {
    const r = await props.fetchFn(props.maintenanceId)
    list.value = r?.data || []
  } catch {
    list.value = []
  }
}

watch(() => props.maintenanceId, load, { immediate: true })

defineExpose({ load })
</script>

<style scoped>
.sub-table-pane { margin-top:8px; display:flex; flex-direction:column; gap:8px; }
.sub-table-footer { padding:4px 0; border-top:1px solid #e4e7ed; text-align:left; }
</style>
