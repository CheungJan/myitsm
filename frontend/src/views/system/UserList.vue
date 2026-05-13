<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>用户管理（共 {{ total }} 条）</span>
                    <div class="filter-bar">
                        <el-input v-model="filters.user_cd" placeholder="编码" clearable style="width:140px" @keyup.enter="onSearch" />
                        <el-input v-model="filters.user_nm" placeholder="姓名" clearable style="width:140px" @keyup.enter="onSearch" />
                        <el-select v-model="filters.dept_cd" placeholder="部门" clearable style="width:140px" @change="onSearch">
                            <el-option v-for="d in deptOptions" :key="d.dept_cd" :label="d.dept_nm" :value="d.dept_cd" />
                        </el-select>
                        <el-button type="primary" size="small" @click="onSearch">查询</el-button>
                        <el-button v-if="authStore.hasPerm('users','create')" type="success" size="small" @click="openDialog()">新增用户</el-button>
                    </div>
                </div>
            </template>
            <el-table :data="users" v-loading="loading" stripe>
                <el-table-column prop="user_cd" label="编码" width="100" />
                <el-table-column prop="user_nm" label="姓名" width="120" />
                <el-table-column prop="dept_nm" label="部门" width="120" />
                <el-table-column prop="phone" label="电话" width="130" />
                <el-table-column prop="email" label="邮箱" min-width="160" />
                <el-table-column label="状态" width="80">
                    <template #default="{ row }">
                        <el-tag :type="row.status === '1' ? 'success' : 'danger'" size="small">
                            {{ row.status === '1' ? '有效' : row.status === '0' ? '无效' : row.status }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="所属组" width="180">
                    <template #default="{ row }">
                        <span v-if="row.groups?.length">{{ row.groups.map((g: Record<string,string>) => g.group_nm).join(', ') }}</span>
                    </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="160" />
                <el-table-column label="操作" width="160" fixed="right">
                    <template #default="{ row }">
                        <el-button v-if="authStore.hasPerm('users','edit')" type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button v-if="authStore.hasPerm('users','delete')" type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
        </el-card>

        <el-dialog :title="editing ? '编辑用户' : '新增用户'" v-model="dialogVisible" width="500px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="编码" required>
                    <el-input v-model="form.user_cd" :disabled="!!editing" />
                </el-form-item>
                <el-form-item label="姓名" required>
                    <el-input v-model="form.user_nm" />
                </el-form-item>
                <el-form-item label="密码" :required="!editing">
                    <el-input v-model="form.password" type="password" :placeholder="editing ? '留空不修改' : '必填'" show-password />
                </el-form-item>
                <el-form-item label="部门">
                    <el-select v-model="form.dept_cd" clearable style="width:100%">
                        <el-option v-for="d in deptOptions" :key="d.dept_cd" :label="d.dept_nm" :value="d.dept_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="电话">
                    <el-input v-model="form.phone" />
                </el-form-item>
                <el-form-item label="邮箱">
                    <el-input v-model="form.email" />
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
import { fetchUsers, createUser, updateUser, deleteUser, fetchDepartments } from '@/api/system'

const authStore = useAuthStore()

const users = ref<Record<string,unknown>[]>([])
const loading = ref(false); const page = ref(1); const perPage = ref(20); const total = ref(0)
const filters = reactive({ user_cd: '', user_nm: '', dept_cd: '' })
const deptOptions = ref<{ dept_cd: string; dept_nm: string }[]>([])

const dialogVisible = ref(false)
const editing = ref<Record<string,string>|null>(null)
const saving = ref(false)
const form = reactive({ user_cd: '', user_nm: '', password: '', dept_cd: '', phone: '', email: '', status: '1' })

watch(page, () => loadData())
watch(perPage, () => { page.value = 1; loadData() })
onMounted(async () => {
    const res = await fetchDepartments()
    deptOptions.value = ((res.data || []) as { dept_cd: string; dept_nm: string }[])
        .filter(d => d.dept_cd)
    await loadData()
})

async function loadData() {
    loading.value = true
    try {
        const params: Record<string, string> = {}
        if (filters.user_cd) params.user_cd = filters.user_cd
        if (filters.user_nm) params.user_nm = filters.user_nm
        if (filters.dept_cd) params.dept_cd = filters.dept_cd
        const res = await fetchUsers(params)
        const list = (res.data || []) as never[]
        total.value = list.length
        const start = (page.value - 1) * perPage.value
        users.value = list.slice(start, start + perPage.value)
    } catch (e) {
        ElMessage.error('加载用户列表失败')
    } finally { loading.value = false }
}

function onSearch() {
    page.value = 1
    loadData()
}

function openDialog(row?: Record<string,string>) {
    if (row) {
        editing.value = row
        form.user_cd = row.user_cd || ''
        form.user_nm = row.user_nm || ''
        form.password = ''
        form.dept_cd = row.dept_cd || ''
        form.phone = row.phone || ''
        form.email = row.email || ''
        form.status = row.status || '1'
    } else {
        editing.value = null
        form.user_cd = ''
        form.user_nm = ''
        form.password = ''
        form.dept_cd = ''
        form.phone = ''
        form.email = ''
        form.status = '1'
    }
    dialogVisible.value = true
}

async function handleSave() {
    if (!form.user_cd || !form.user_nm) {
        ElMessage.warning('编码和姓名为必填项')
        return
    }
    if (!editing.value && !form.password) {
        ElMessage.warning('新增用户必须填写密码')
        return
    }
    saving.value = true
    try {
        // 去掉空字符串的外键字段，避免 PostgreSQL FK 约束错误
        const payload: Record<string, string> = { user_nm: form.user_nm }
        if (form.dept_cd) payload.dept_cd = form.dept_cd
        if (form.phone) payload.phone = form.phone
        if (form.email) payload.email = form.email
        payload.status = form.status || '1'
        payload.useflg = '1'
        if (form.password) payload.password = form.password
        if (editing.value) {
            await updateUser(editing.value.user_cd, payload)
            ElMessage.success('更新成功')
        } else {
            payload.user_cd = form.user_cd
            await createUser(payload)
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } catch (e: unknown) {
        const err = e as { response?: { data?: { message?: string } } }
        ElMessage.error(err?.response?.data?.message || '保存失败，请检查输入')
    }
    finally { saving.value = false }
}

async function handleDelete(row: Record<string,string>) {
    try {
        await ElMessageBox.confirm(`确定删除用户 ${row.user_cd}（${row.user_nm}）？`, '确认删除')
        await deleteUser(row.user_cd)
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
.filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
</style>
