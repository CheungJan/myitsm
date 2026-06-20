<template><div class="page"><div class="page-header"><h2>工单工序</h2></div><el-card shadow="never"><el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open"><el-table-column prop="wo_id" label="工单编号" width="110"/><el-table-column prop="process_cd" label="工序" width="100"/><el-table-column prop="seq_no" label="序号" width="60"/><el-table-column label="计划数" width="70"><template #default="{row}">{{ row.plan_qty||0 }}</template></el-table-column><el-table-column label="完成数" width="70"><template #default="{row}">{{ row.actual_qty||0 }}</template></el-table-column><el-table-column label="不良品" width="70"><template #default="{row}"><span :style="{color: (row.defect_qty||0) > 0 ? '#f56c6c' : ''}">{{ row.defect_qty||0 }}</span></template></el-table-column><el-table-column label="状态" width="90"><template #default="{row}"><el-tag :type="wpStatusTag(row.status)" size="small">{{ row.status||'PENDING' }}</el-tag></template></el-table-column><el-table-column prop="worker_cd" label="操作工" width="70"/><el-table-column label="操作" width="160" fixed="right"><template #default="{row}"><el-button link type="primary" size="small" @click.stop="openEdit(row)">记录</el-button><template v-for="btn in wpButtons(row.status)" :key="btn.target"><el-button link :type="btn.type as any" size="small" @click.stop="handleWpTransition(row, btn.target)">{{ btn.label }}</el-button></template></template></el-table-column></el-table><AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/></el-card>

<el-dialog :title="`工序详情 — ${(detail?.process_cd as string) || ''}`" v-model="drawer" width="500px"><template v-if="detail"><el-descriptions :column="2" border size="small"><el-descriptions-item label="工单编号">{{ detail.wo_id }}</el-descriptions-item><el-descriptions-item label="工序编码">{{ detail.process_cd||'-' }}</el-descriptions-item><el-descriptions-item label="序号">{{ detail.seq_no }}</el-descriptions-item><el-descriptions-item label="状态"><el-tag :type="wpStatusTag((detail.status as string)||'PENDING')" size="small">{{ detail.status||'PENDING' }}</el-tag></el-descriptions-item><el-descriptions-item label="计划数">{{ detail.plan_qty||0 }}</el-descriptions-item><el-descriptions-item label="完成数">{{ detail.actual_qty||0 }}</el-descriptions-item><el-descriptions-item label="不良品">{{ detail.defect_qty||0 }}</el-descriptions-item><el-descriptions-item label="操作工">{{ detail.worker_cd||'-' }}</el-descriptions-item><el-descriptions-item label="开始时间">{{ detail.start_time||'-' }}</el-descriptions-item><el-descriptions-item label="结束时间">{{ detail.end_time||'-' }}</el-descriptions-item><el-descriptions-item label="备注" :span="2">{{ detail.remark||'-' }}</el-descriptions-item></el-descriptions></template></el-dialog>

<!-- 工序记录弹窗 -->
<el-dialog v-model="editing" title="工序记录" width="400px">
  <el-form v-if="editRow" label-width="80px" size="small">
    <el-form-item label="完成数"><el-input-number v-model="editForm.actual_qty" :min="0" style="width:100%"/></el-form-item>
    <el-form-item label="不良品"><el-input-number v-model="editForm.defect_qty" :min="0" style="width:100%"/></el-form-item>
    <el-form-item label="备注"><el-input v-model="editForm.remark"/></el-form-item>
  </el-form>
  <template #footer><el-button @click="editing=false">取消</el-button><el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button></template>
</el-dialog>
</div></template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useDetailDrawer } from '@/composables/useDetailDrawer'
import { fetchAllWorkProcesses, updateWorkProcess, deleteWorkProcess } from '@/api/mes'
import type { MesRecord } from '@/api/mes'

const { items, loading, page, perPage, total, load } = useListPage<MesRecord>((p?: Record<string, string>) => fetchAllWorkProcesses(p))
const { drawer, detail, open } = useDetailDrawer<MesRecord>()

const editing = ref(false); const saving = ref(false)
const editRow = ref<MesRecord | null>(null)
const editForm = reactive({ actual_qty: 0, defect_qty: 0, remark: '' })

function wpStatusTag(s: string) { const m: Record<string, string> = { PENDING: 'info', IN_PROGRESS: 'warning', COMPLETED: 'success', SKIPPED: 'info' }; return m[s] || 'info' }

function wpButtons(status: string) {
    const map: Record<string, { target: string; label: string; type: string }[]> = {
        PENDING: [
            { target: 'IN_PROGRESS', label: '开始', type: 'warning' },
            { target: 'DELETE', label: '删除', type: 'danger' },
        ],
        IN_PROGRESS: [
            { target: 'COMPLETED', label: '完成', type: 'success' },
            { target: 'SKIPPED', label: '跳过', type: 'info' },
        ],
    }
    return map[status] || []
}

async function handleWpTransition(row: MesRecord, target: string) {
    if (target === 'DELETE') {
        try {
            await ElMessageBox.confirm(`确认删除工序 ${row.process_cd}？`, '确认删除', { type: 'warning' })
            await deleteWorkProcess((row as any).id)
            ElMessage.success('已删除')
            load()
        } catch (e: any) {
            if (e !== 'cancel') ElMessage.error(e?.response?.data?.message || '删除失败')
        }
        return
    }
    try {
        await ElMessageBox.confirm(`确认将工序流转至「${target}」？`, '确认', { type: 'warning' })
        await updateWorkProcess((row as any).id, { status: target })
        ElMessage.success(`已${target}`)
        load()
    } catch { /* */ }
}

function openEdit(row: MesRecord) {
    editRow.value = row
    editForm.actual_qty = (row.actual_qty as number) || 0
    editForm.defect_qty = (row.defect_qty as number) || 0
    editForm.remark = (row.remark as string) || ''
    editing.value = true
}

async function saveEdit() {
    saving.value = true
    try {
        await updateWorkProcess((editRow.value as any).id, {
            actual_qty: editForm.actual_qty,
            defect_qty: editForm.defect_qty,
            remark: editForm.remark || undefined,
        })
        ElMessage.success('保存成功'); editing.value = false; load()
    } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
    finally { saving.value = false }
}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
