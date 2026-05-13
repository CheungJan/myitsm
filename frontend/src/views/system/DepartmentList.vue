<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>部门管理（共 {{ total }} 条）</span>
                    <div>
                        <el-button v-if="authStore.hasPerm('depts','create')" type="success" size="small" @click="openDialog()">新增部门</el-button>
                    </div>
                </div>
            </template>
            <el-table :data="depts" v-loading="loading" stripe>
                <el-table-column prop="dept_cd" label="编码" width="120" />
                <el-table-column prop="dept_nm" label="名称" width="200" />
                <el-table-column prop="parent_cd" label="上级部门" width="120" />
                <el-table-column label="状态" width="80">
                    <template #default="{ row }">
                        <el-tag :type="row.status === '1' ? 'success' : 'danger'" size="small">
                            {{ row.status === '1' ? '有效' : '无效' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="160" fixed="right">
                    <template #default="{ row }">
                        <el-button v-if="authStore.hasPerm('depts','edit')" type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button v-if="authStore.hasPerm('depts','delete')" type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
        </el-card>

        <el-dialog :title="editing ? '编辑部门' : '新增部门'" v-model="dialogVisible" width="500px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="编码" required>
                    <el-input v-model="form.dept_cd" :disabled="!!editing" />
                </el-form-item>
                <el-form-item label="名称" required>
                    <el-input v-model="form.dept_nm" />
                </el-form-item>
                <el-form-item label="上级部门">
                    <el-select v-model="form.parent_cd" clearable style="width:100%">
                        <el-option v-for="d in deptOptions" :key="d.dept_cd" :label="d.dept_nm" :value="d.dept_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="状态">
                    <el-select v-model="form.status" style="width:100%">
                        <el-option label="有效" value="1" />
                        <el-option label="无效" value="0" />
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
import { watch } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { fetchDepartments, createDepartment, updateDepartment, deleteDepartment } from '@/api/system'

const authStore = useAuthStore()

const depts = ref<Record<string,unknown>[]>([])
const loading = ref(false); const page = ref(1); const perPage = ref(20); const total = ref(0)
const deptOptions = ref<{ dept_cd: string; dept_nm: string }[]>([])
const dialogVisible = ref(false); const editing = ref<Record<string,string>|null>(null); const saving = ref(false)
const form = reactive({ dept_cd: '', dept_nm: '', parent_cd: '', status: '1' })

watch(page, () => loadData())
watch(perPage, () => { page.value = 1; loadData() })
onMounted(async () => {
    await loadData()
})

async function loadData() {
    loading.value = true
    try {
        const res = await fetchDepartments()
        const list = (res.data || []) as Record<string,string>[]
        deptOptions.value = list.filter(d => d.dept_cd)
        total.value = list.length
        depts.value = list.slice((page.value - 1) * perPage.value, page.value * perPage.value)
    } finally { loading.value = false }
}

function openDialog(row?: Record<string,string>) {
    editing.value = row || null
    if (row) {
        form.dept_cd = row.dept_cd || ''
        form.dept_nm = row.dept_nm || ''
        form.parent_cd = row.parent_cd || ''
        form.status = row.status || '1'
    } else {
        form.dept_cd = ''; form.dept_nm = ''
        form.parent_cd = ''; form.status = '1'
    }
    dialogVisible.value = true
}

async function handleSave() {
    if (!form.dept_cd || !form.dept_nm) {
        ElMessage.warning('编码和名称为必填项')
        return
    }
    saving.value = true
    try {
        const payload: Record<string, string> = { dept_nm: form.dept_nm, status: form.status, useflg: '1' }
        if (form.parent_cd) payload.parent_cd = form.parent_cd
        if (editing.value) {
            await updateDepartment(editing.value.dept_cd, payload)
            ElMessage.success('更新成功')
        } else {
            payload.dept_cd = form.dept_cd
            await createDepartment(payload)
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } catch {
        ElMessage.error('保存失败')
    }
    finally { saving.value = false }
}

async function handleDelete(row: Record<string,string>) {
    try {
        await ElMessageBox.confirm(`确定删除部门 ${row.dept_cd}（${row.dept_nm}）？`, '确认删除')
        await deleteDepartment(row.dept_cd)
        ElMessage.success('已删除')
        loadData()
    } catch (e: unknown) {
        if (e !== 'cancel') {
            ElMessage.error('删除失败')
        }
    }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
