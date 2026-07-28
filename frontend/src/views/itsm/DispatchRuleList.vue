<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>派单规则配置（共 {{ rules.length }} 条）</span>
                    <el-button v-if="authStore.hasPerm('dispatch-rules','create')" type="success" size="small" @click="openDialog()">新增规则</el-button>
                </div>
            </template>
            <el-table :data="rules" v-loading="loading" stripe>
                <el-table-column prop="priority" label="优先级" width="70" />
                <el-table-column label="自动" width="60"><template #default="{row}"><el-tag :type="row.auto_dispatch!=='0'?'success':'info'" size="small">{{ row.auto_dispatch!=='0'?'是':'否' }}</el-tag></template></el-table-column>
                <el-table-column prop="rule_name" label="规则名称" width="160" />
                <el-table-column label="故障类型" width="100">
                    <template #default="{ row }">
                        {{ row.fault_type ? faultTypeLabel(row.fault_type) : '全匹配' }}
                    </template>
                </el-table-column>
                <el-table-column label="目标" width="160">
                    <template #default="{ row }">
                        {{ targetTypeLabel(row.target_type) }}{{ (row.target_type==='group_leader'||row.target_type==='load_balance') && row.target_value ? ' / ' + row.target_value : '' }}
                    </template>
                </el-table-column>
                <el-table-column label="一级兜底" width="160">
                    <template #default="{ row }">
                        {{ targetTypeLabel(row.fallback_type) }}{{ (row.fallback_type==='group_leader'||row.fallback_type==='load_balance') && row.fallback_value ? ' / ' + row.fallback_value : '' }}
                    </template>
                </el-table-column>
                <el-table-column label="最终兜底" width="160">
                    <template #default="{ row }">
                        {{ targetTypeLabel(row.ultimate_fallback_type) }}{{ (row.ultimate_fallback_type==='group_leader'||row.ultimate_fallback_type==='load_balance') && row.ultimate_fallback_value ? ' / ' + row.ultimate_fallback_value : '' }}
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="160" fixed="right">
                    <template #default="{ row }">
                        <el-button v-if="authStore.hasPerm('dispatch-rules','edit')" type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button v-if="authStore.hasPerm('dispatch-rules','delete')" type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog :title="editing ? '编辑规则' : '新增规则'" v-model="dialogVisible" width="640px">
            <el-form :model="form" label-width="100px">
                <el-form-item label="规则名称" required>
                    <el-input v-model="form.rule_name" />
                </el-form-item>
                <el-form-item label="优先级">
                    <el-input-number v-model="form.priority" :min="1" :max="999" />
                    <span class="hint">数字越小越优先</span>
                </el-form-item>
                <el-form-item label="故障类型">
                    <el-select v-model="form.fault_type" clearable placeholder="空=全匹配" style="width:100%">
                        <el-option v-for="o in faultTypeOptions" :key="o.code_cd" :label="o.code_nm" :value="o.code_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="门店编码">
                    <el-input v-model="form.store_id" placeholder="留空=全门店" />
                </el-form-item>
                <el-form-item label="自动派单">
                    <el-switch v-model="form.auto_dispatch" active-value="1" inactive-value="0" />
                    <span class="hint">关闭后该规则不自动生成派工，需手动派单</span>
                </el-form-item>
                <el-form-item label="目标类型">
                    <el-select v-model="form.target_type" style="width:100%">
                        <el-option label="区域负责人" value="area_manager" />
                        <el-option label="组长" value="group_leader" />
                        <el-option label="负载均衡" value="load_balance" />
                        <el-option label="手动派单" value="manual" />
                    </el-select>
                </el-form-item>
                <el-form-item label="目标值" v-if="form.target_type==='group_leader'||form.target_type==='load_balance'">
                    <el-select v-model="form.target_value" filterable placeholder="选择组" style="width:100%">
                        <el-option v-for="g in groupOptions" :key="g.group_cd" :label="`${g.group_nm} (${g.group_cd})`" :value="g.group_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="一级兜底">
                    <el-select v-model="form.fallback_type" clearable style="width:100%">
                        <el-option label="区域负责人" value="area_manager" />
                        <el-option label="组长" value="group_leader" />
                        <el-option label="负载均衡" value="load_balance" />
                        <el-option label="手动派单" value="manual" />
                    </el-select>
                </el-form-item>
                <el-form-item label="一级兜底值" v-if="form.fallback_type==='group_leader'||form.fallback_type==='load_balance'">
                    <el-select v-model="form.fallback_value" filterable placeholder="选择组" style="width:100%">
                        <el-option v-for="g in groupOptions" :key="g.group_cd" :label="`${g.group_nm} (${g.group_cd})`" :value="g.group_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="最终兜底">
                    <el-select v-model="form.ultimate_fallback_type" clearable style="width:100%">
                        <el-option label="区域负责人" value="area_manager" />
                        <el-option label="组长" value="group_leader" />
                        <el-option label="负载均衡" value="load_balance" />
                        <el-option label="手动派单" value="manual" />
                    </el-select>
                </el-form-item>
                <el-form-item label="最终兜底值" v-if="form.ultimate_fallback_type==='group_leader'||form.ultimate_fallback_type==='load_balance'">
                    <el-select v-model="form.ultimate_fallback_value" filterable placeholder="选择组" style="width:100%">
                        <el-option v-for="g in groupOptions" :key="g.group_cd" :label="`${g.group_nm} (${g.group_cd})`" :value="g.group_cd" />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { fetchDispatchRules, createDispatchRule, updateDispatchRule, deleteDispatchRule, type DispatchRule } from '@/api/itsm'
import { fetchGroups } from '@/api/system'
import { fetchSyscodes } from '@/api/master'
import { useDict } from '@/composables/useDict'

const authStore = useAuthStore()
const { dictLabel: gzLabel } = useDict('GZ')

const rules = ref<DispatchRule[]>([])
const loading = ref(false)
const groupOptions = ref<{ group_cd: string; group_nm: string }[]>([])
const faultTypeOptions = ref<{ code_cd: string; code_nm: string }[]>([])

const dialogVisible = ref(false)
const editing = ref<DispatchRule | null>(null)
const saving = ref(false)
const form = reactive({
    rule_name: '',
    priority: 99,
    fault_type: '' as string,
    store_id: '' as string,
    target_type: 'area_manager',
    target_value: '' as string,
    fallback_type: 'group_leader',
    fallback_value: '' as string,
    ultimate_fallback_type: 'manual',
    ultimate_fallback_value: '' as string,
    auto_dispatch: '1' as string,
})

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const [r, g, f] = await Promise.all([fetchDispatchRules(), fetchGroups(), fetchSyscodes('GZ')])
        rules.value = (r.data || []) as DispatchRule[]
        groupOptions.value = (g.data || []) as { group_cd: string; group_nm: string }[]
        faultTypeOptions.value = (f.data || []) as { code_cd: string; code_nm: string }[]
    } catch {
        ElMessage.error('加载派单规则失败')
    } finally { loading.value = false }
}

function faultTypeLabel(cd: string): string { return gzLabel(cd) || cd }
function targetTypeLabel(t?: string | null): string {
    if (t === 'area_manager') return '区域负责人'
    if (t === 'group_leader') return '组长'
    if (t === 'load_balance') return '负载均衡'
    if (t === 'manual') return '手动'
    return t || '-'
}

function openDialog(row?: DispatchRule) {
    editing.value = row || null
    if (row) {
        form.rule_name = row.rule_name || ''
        form.priority = row.priority || 99
        form.fault_type = row.fault_type || ''
        form.store_id = row.store_id || ''
        form.target_type = row.target_type || 'area_manager'
        form.target_value = row.target_value || ''
        form.fallback_type = row.fallback_type || ''
        form.fallback_value = row.fallback_value || ''
        form.ultimate_fallback_type = row.ultimate_fallback_type || ''
        form.ultimate_fallback_value = row.ultimate_fallback_value || ''
        form.auto_dispatch = row.auto_dispatch || '1'
    } else {
        form.rule_name = ''
        form.priority = 99
        form.fault_type = ''
        form.store_id = ''
        form.target_type = 'area_manager'
        form.target_value = ''
        form.fallback_type = 'group_leader'
        form.fallback_value = ''
        form.ultimate_fallback_type = 'manual'
        form.ultimate_fallback_value = ''
        form.auto_dispatch = '1'
    }
    dialogVisible.value = true
}

async function handleSave() {
    if (!form.rule_name) { ElMessage.warning('规则名称为必填项'); return }
    saving.value = true
    try {
        const payload: Record<string, unknown> = {
            rule_name: form.rule_name,
            priority: form.priority,
            fault_type: form.fault_type || null,
            store_id: form.store_id || null,
            target_type: form.target_type || null,
            target_value: form.target_value || null,
            fallback_type: form.fallback_type || null,
            fallback_value: form.fallback_value || null,
            ultimate_fallback_type: form.ultimate_fallback_type || null,
            ultimate_fallback_value: form.ultimate_fallback_value || null,
            auto_dispatch: form.auto_dispatch || '1',
        }
        if (editing.value && editing.value.rule_id) {
            await updateDispatchRule(editing.value.rule_id, payload)
            ElMessage.success('更新成功')
        } else {
            await createDispatchRule(payload)
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } finally { saving.value = false }
}

async function handleDelete(row: DispatchRule) {
    try {
        await ElMessageBox.confirm(`确定删除规则 "${row.rule_name}"？`, '确认删除')
        await deleteDispatchRule(row.rule_id as number)
        ElMessage.success('已删除')
        loadData()
    } catch (e: unknown) {
        if (e !== 'cancel') {
            const err = e as { response?: { data?: { message?: string } } }
            ElMessage.error(err?.response?.data?.message || '删除失败')
        }
    }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.hint { margin-left: 8px; color: #909399; font-size: 12px; }
</style>
