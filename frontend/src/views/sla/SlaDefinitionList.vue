<template>
  <div class="page">
    <div class="page-header">
      <h2>SLA 定义</h2>
      <el-button type="primary" @click="openCreate">＋ 新建 SLA</el-button>
    </div>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open">
        <el-table-column prop="sla_id" label="SLA编号" width="100" />
        <el-table-column prop="sla_name" label="SLA名称" min-width="140" />
        <el-table-column label="优先级" width="70">
          <template #default="{ row }">{{ row.priority || '-' }}</template>
        </el-table-column>
        <el-table-column prop="levels" label="关联等级" width="80" />
        <el-table-column prop="response_minutes" label="响应时限(分)" width="110" />
        <el-table-column prop="resolve_minutes" label="解决时限(分)" width="110" />
        <el-table-column prop="escalation_minutes" label="升级时限(分)" width="110" />
        <el-table-column label="仅工作时间" width="90">
          <template #default="{ row }">
            <el-tag :type="row.business_hours_only ? 'success' : 'info'" size="small">{{ row.business_hours_only ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click.stop="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <el-dialog v-model="formVisible" :title="isEdit ? '编辑 SLA' : '新建 SLA'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" size="small">
        <el-form-item label="SLA名称" prop="sla_name"><el-input v-model="form.sla_name" /></el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="form.priority" style="width:100%">
            <el-option label="1 - 高" value="1" /><el-option label="2 - 中" value="2" /><el-option label="3 - 低" value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联等级"><el-input v-model="form.levels" placeholder="对应 TIT01.LEVELS" /></el-form-item>
        <el-form-item label="响应时限(分)" prop="response_minutes"><el-input-number v-model="form.response_minutes" :min="1" style="width:100%" /></el-form-item>
        <el-form-item label="解决时限(分)" prop="resolve_minutes"><el-input-number v-model="form.resolve_minutes" :min="1" style="width:100%" /></el-form-item>
        <el-form-item label="升级时限(分)"><el-input-number v-model="form.escalation_minutes" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="仅工作时间"><el-switch v-model="form.business_hours_only" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="formVisible = false">取消</el-button>
        <el-button size="small" type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog :title="'SLA — ' + (detail?.sla_id || '')" v-model="drawer" width="500px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="SLA编号">{{ detail.sla_id }}</el-descriptions-item>
          <el-descriptions-item label="SLA名称">{{ detail.sla_name }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ detail.priority }}</el-descriptions-item>
          <el-descriptions-item label="关联等级">{{ detail.levels || '-' }}</el-descriptions-item>
          <el-descriptions-item label="响应时限">{{ detail.response_minutes }}分钟</el-descriptions-item>
          <el-descriptions-item label="解决时限">{{ detail.resolve_minutes }}分钟</el-descriptions-item>
          <el-descriptions-item label="升级时限">{{ detail.escalation_minutes || '-' }}分钟</el-descriptions-item>
          <el-descriptions-item label="仅工作时间">{{ detail.business_hours_only ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useDetailDrawer } from '@/composables/useDetailDrawer'
import { fetchSlaDefinitions, createSlaDefinition, updateSlaDefinition } from '@/api/sla'
import type { SlaRecord } from '@/api/sla'

const { items, loading, page, perPage, total, onSearch: refresh } = useListPage<SlaRecord>(fetchSlaDefinitions)
const { drawer, detail, open } = useDetailDrawer<SlaRecord>()

const formVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const form = reactive<Record<string, unknown>>({
  sla_name: '', priority: '2', levels: '', response_minutes: 60,
  resolve_minutes: 240, escalation_minutes: 0, business_hours_only: false, description: '',
})
const rules = {
  sla_name: [{ required: true, message: '请输入SLA名称', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级' }],
  response_minutes: [{ required: true, message: '请输入响应时限' }],
  resolve_minutes: [{ required: true, message: '请输入解决时限' }],
}

function openCreate() {
  isEdit.value = false
  Object.assign(form, { sla_name: '', priority: '2', levels: '', response_minutes: 60, resolve_minutes: 240, escalation_minutes: 0, business_hours_only: false, description: '' })
  formVisible.value = true
}

function openEdit(row: SlaRecord) {
  isEdit.value = true
  Object.assign(form, row)
  formVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  try { await formRef.value.validate() } catch { return }
  try {
    const data = { ...form, priority: String(form.priority || '2') }
    if (isEdit.value) {
      await updateSlaDefinition(form.sla_id as string, data)
      ElMessage.success('更新成功')
    } else {
      await createSlaDefinition(data)
      ElMessage.success('创建成功')
    }
    formVisible.value = false
    refresh({})
  } catch { ElMessage.error('操作失败') }
}
</script>

<style scoped>
.page { padding: 0; }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0; }
</style>
