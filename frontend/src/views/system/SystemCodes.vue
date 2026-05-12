<template>
    <div class="codes-page">
        <div class="tree-panel">
            <el-card shadow="never">
                <template #header>
                    <div class="tree-header">
                        <span>字典类型</span>
                        <el-button type="primary" size="small" @click="openTypeDialog()">新增类型</el-button>
                    </div>
                </template>
                <el-input v-model="treeFilter" placeholder="过滤类型" clearable size="small" style="margin-bottom:4px" />
                <el-tree
                    ref="treeRef"
                    :data="treeData"
                    :props="{ label: 'label', children: 'children' }"
                    node-key="code_cd"
                    highlight-current
                    :filter-node-method="filterTree"
                    @node-click="onTreeClick"
                >
                    <template #default="{ data }">
                        <span class="tree-node">
                            <span class="tree-node-label">{{ data.label }}</span>
                            <span class="tree-node-actions">
                                <el-button link size="small" @click.stop="openTypeDialog(data)">编辑</el-button>
                                <el-button link size="small" type="danger" @click.stop="handleDeleteType(data)">删除</el-button>
                            </span>
                        </span>
                    </template>
                </el-tree>
            </el-card>
        </div>

        <div class="table-panel">
            <el-card>
                <template #header>
                    <div class="page-header">
                        <span><template v-if="selectedTyp">{{ selectedLabel }}（{{ codes.length }} 条）</template><template v-else>请选择左侧字典类型</template></span>
                        <div>
                            <el-button v-if="selectedTyp" type="primary" size="small" @click="openDialog()">新增编码</el-button>
                        </div>
                    </div>
                </template>
                <el-table :data="codes" v-loading="loading" stripe>
                    <el-table-column prop="code_cd" label="编码" width="120" />
                    <el-table-column prop="code_nm" label="名称" min-width="150" />
                    <el-table-column prop="memo" label="备注" width="150" />
                    <el-table-column label="排序" width="60">
                        <template #default="{ row }">{{ row.sort_no ?? '' }}</template>
                    </el-table-column>
                    <el-table-column label="操作" width="120" fixed="right">
                        <template #default="{ row }">
                            <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-card>
        </div>

        <!-- 编码编辑弹窗 -->
        <el-dialog :title="editing ? '编辑编码' : '新增编码'" v-model="dialogVisible" width="500px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="类型" required>
                    <el-input :model-value="form.code_typ" disabled />
                </el-form-item>
                <el-form-item label="编码" required>
                    <el-input v-model="form.code_cd" :disabled="!!editing" />
                </el-form-item>
                <el-form-item label="名称" required>
                    <el-input v-model="form.code_nm" />
                </el-form-item>
                <el-form-item label="备注">
                    <el-input v-model="form.memo" />
                </el-form-item>
                <el-form-item label="排序">
                    <el-input-number v-model="form.sort_no" :min="0" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
            </template>
        </el-dialog>

        <!-- 类型新增弹窗 -->
        <el-dialog :title="typeEditingId ? '编辑字典类型' : '新增字典类型'" v-model="typeDialogVisible" width="450px">
            <el-form :model="typeForm" label-width="80px">
                <el-form-item label="类型编码" required>
                    <el-input v-model="typeForm.code_cd" placeholder="如 ZT, GZ" />
                </el-form-item>
                <el-form-item label="类型名称" required>
                    <el-input v-model="typeForm.code_nm" placeholder="如 单据状态" />
                </el-form-item>
                <el-form-item label="排序">
                    <el-input-number v-model="typeForm.sort_no" :min="0" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="typeDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSaveType" :loading="typeSaving">保存</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchSyscodes } from '@/api/master'
import { createSyscode, updateSyscode, deleteSyscode, fetchAllSyscodes } from '@/api/system'

interface TreeNode {
    code_cd: string
    label: string
    sort_no: number
    _id?: number
    children?: TreeNode[]
}

const treeData = ref<TreeNode[]>([])
const treeFilter = ref('')
const treeRef = ref()
const selectedTyp = ref('')
const selectedLabel = ref('')

const codes = ref<Record<string,unknown>[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const editing = ref<Record<string,unknown>|null>(null)
const saving = ref(false)
const form = reactive({ code_typ: '', code_cd: '', code_nm: '', memo: '', sort_no: 0 })

const typeDialogVisible = ref(false)
const typeSaving = ref(false)
const typeForm = reactive({ code_cd: '', code_nm: '', sort_no: 0 })

onMounted(() => loadTree())
watch(treeFilter, (v) => treeRef.value?.filter(v))

async function loadTree() {
    try {
        const allRes = await fetchAllSyscodes()
        const all = (allRes.data || []) as Record<string,unknown>[]
        // 动态提取所有类型
        const typeSet = new Map<string, string>()
        for (const r of all) {
            const typ = r.code_typ as string
            if (typ && typ !== 'SY' && !typeSet.has(typ)) typeSet.set(typ, r.code_nm as string || '')
        }
        // 补充 SY 中的中文名
        const syList = all.filter(r => r.code_typ === 'SY')
        for (const sy of syList) {
            const cd = sy.code_cd as string
            if (typeSet.has(cd)) typeSet.set(cd, (sy.code_nm as string) || typeSet.get(cd) || '')
            else typeSet.set(cd, sy.code_nm as string || '')
        }
        treeData.value = Array.from(typeSet.entries())
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map(([cd, nm]) => ({
                code_cd: cd,
                label: nm ? `${nm}（${cd}）` : cd,
                sort_no: 0,
            }))
    } catch { /* */ }
}

function filterTree(value: string, data: TreeNode): boolean {
    if (!value) return true
    const kw = value.toLowerCase()
    return data.label.toLowerCase().includes(kw)
}

async function onTreeClick(node: TreeNode) {
    selectedTyp.value = node.code_cd
    selectedLabel.value = node.label
    loading.value = true
    try {
        const res = await fetchSyscodes(node.code_cd)
        codes.value = (res.data || []) as Record<string,unknown>[]
    } finally { loading.value = false }
}

// ---- 类型管理 ----

const typeEditingId = ref<number | null>(null)

function openTypeDialog(data?: TreeNode) {
    if (data) {
        // 从 allData 中找到对应的 SY 记录以获取 id
        typeEditingId.value = data._id || null
        typeForm.code_cd = data.code_cd
        typeForm.code_nm = data.label.replace(/（.*/, '')
        typeForm.sort_no = data.sort_no
    } else {
        typeEditingId.value = null
        Object.assign(typeForm, { code_cd: '', code_nm: '', sort_no: 0 })
    }
    typeDialogVisible.value = true
}

async function handleSaveType() {
    if (!typeForm.code_cd || !typeForm.code_nm) { ElMessage.warning('编码和名称为必填'); return }
    typeSaving.value = true
    try {
        if (typeEditingId.value) {
            await updateSyscode(typeEditingId.value, { code_nm: typeForm.code_nm, sort_no: typeForm.sort_no, useflg: '1' })
            ElMessage.success('类型更新成功')
        } else {
            await createSyscode({ code_typ: 'SY', code_cd: typeForm.code_cd, code_nm: typeForm.code_nm, sort_no: typeForm.sort_no || 0, useflg: '1' })
            ElMessage.success('类型创建成功')
        }
        typeDialogVisible.value = false
        loadTree()
    } finally { typeSaving.value = false }
}

async function handleDeleteType(data: TreeNode) {
    try {
        // 先查该类型下有多少编码
        const res = await fetchSyscodes(data.code_cd)
        const childCount = (res.data || []).length
        const msg = childCount > 0
            ? `该类型下有 ${childCount} 条编码记录，删除类型时会一并删除这些编码。确定删除？`
            : `确定删除字典类型 ${data.label}？`
        await ElMessageBox.confirm(msg, '确认删除', { type: 'warning' })
        if (data._id) {
            // 删除 SY 注册
            await deleteSyscode(data._id)
            // 删除该类型下所有编码
            const children = (res.data || []) as Record<string,unknown>[]
            for (const c of children) {
                await deleteSyscode(c.id as number).catch(() => {})
            }
            ElMessage.success(`已删除类型及 ${childCount} 条编码`)
            if (selectedTyp.value === data.code_cd) { selectedTyp.value = ''; codes.value = [] }
            loadTree()
        }
    } catch (e: unknown) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// ---- 编码 CRUD ----

function openDialog(row?: Record<string,unknown>) {
    if (row) {
        editing.value = row
        form.code_typ = row.code_typ as string || ''
        form.code_cd = row.code_cd as string || ''
        form.code_nm = row.code_nm as string || ''
        form.memo = row.memo as string || ''
        form.sort_no = Number(row.sort_no) || 0
    } else {
        editing.value = null
        Object.assign(form, { code_typ: selectedTyp.value, code_cd: '', code_nm: '', memo: '', sort_no: 0 })
    }
    dialogVisible.value = true
}

async function handleSave() {
    if (!form.code_cd || !form.code_nm) { ElMessage.warning('编码和名称为必填'); return }
    saving.value = true
    try {
        if (editing.value) {
            await updateSyscode(editing.value.id as number, { code_cd: form.code_cd, code_nm: form.code_nm, memo: form.memo, sort_no: form.sort_no, useflg: '1' })
            ElMessage.success('更新成功')
        } else {
            await createSyscode({ ...form, useflg: '1', sort_no: form.sort_no || 0 })
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        if (selectedTyp.value) onTreeClick(treeData.value.find(n => n.code_cd === selectedTyp.value) || { code_cd: selectedTyp.value, label: selectedLabel.value, sort_no: 0 })
    } finally { saving.value = false }
}

async function handleDelete(row: Record<string,unknown>) {
    try {
        await ElMessageBox.confirm(`确定删除 ${row.code_cd}（${row.code_nm}）？`, '确认删除')
        await deleteSyscode(row.id as number)
        ElMessage.success('已删除')
        if (selectedTyp.value) onTreeClick(treeData.value.find(n => n.code_cd === selectedTyp.value) || { code_cd: selectedTyp.value, label: selectedLabel.value, sort_no: 0 })
    } catch (e: unknown) { if (e !== 'cancel') ElMessage.error('删除失败') }
}
</script>

<style lang="scss" scoped>
.codes-page { display: flex; gap: 12px; padding: 16px; height: calc(100vh - 80px); }
.tree-panel {
    width: 260px; flex-shrink: 0; overflow-y: auto;
    :deep(.el-card__body) { padding: 8px; }
}
.tree-header { display: flex; justify-content: space-between; align-items: center; }
.tree-node {
    display: flex; align-items: center; flex: 1; min-width: 0; font-size: 13px;
    .tree-node-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 1; }
    .tree-node-actions { display: none; flex-shrink: 0; margin-left: 4px; }
    .tree-node-actions .el-button { padding: 0 2px; font-size: 12px; height: auto; min-height: auto; }
    &:hover .tree-node-actions { display: flex; }
}
.table-panel { flex: 1; overflow-y: auto; min-width: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
