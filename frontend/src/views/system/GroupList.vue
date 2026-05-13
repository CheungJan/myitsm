<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>用户组管理（共 {{ total }} 条）</span>
                    <div>
                        <el-button v-if="authStore.hasPerm('groups','create')" type="success" size="small" @click="openDialog()">新增用户组</el-button>
                    </div>
                </div>
            </template>
            <el-table :data="groups" v-loading="loading" stripe>
                <el-table-column prop="group_cd" label="组编码" width="120" />
                <el-table-column prop="group_nm" label="组名称" width="200" />
                <el-table-column label="状态" width="80">
                    <template #default="{ row }">
                        <el-tag :type="row.status === '1' ? 'success' : 'danger'" size="small">
                            {{ row.status === '1' ? '有效' : '无效' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="360" fixed="right">
                    <template #default="{ row }">
                        <el-button v-if="authStore.hasPerm('groups','edit')" type="primary" link size="small" @click="openMembers(row)">成员管理</el-button>
                        <el-button v-if="authStore.hasPerm('groups','edit')" type="warning" link size="small" @click="openPerms(row)">权限设置</el-button>
                        <el-button v-if="authStore.hasPerm('groups','edit')" type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button v-if="authStore.hasPerm('groups','delete')" type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
        </el-card>

        <!-- 新增/编辑用户组 -->
        <el-dialog :title="editing ? '编辑用户组' : '新增用户组'" v-model="dialogVisible" width="500px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="编码" required>
                    <el-input v-model="form.group_cd" :disabled="!!editing" />
                </el-form-item>
                <el-form-item label="名称" required>
                    <el-input v-model="form.group_nm" />
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

        <!-- 权限设置 -->
        <el-dialog title="权限设置" v-model="permVisible" width="600px">
            <div v-if="permLoading" v-loading="permLoading" style="height:200px" />
            <div v-else>
                <div v-for="mod in permTree" :key="mod.menu_cd" style="margin-bottom:16px">
                    <div style="font-weight:bold;margin-bottom:8px;color:#409eff">{{ mod.menu_nm }}</div>
                    <div v-for="page in mod.children || []" :key="page.menu_cd" style="display:flex;align-items:center;gap:12px;margin-bottom:6px;padding-left:16px">
                        <span style="width:100px;font-size:13px">{{ page.menu_nm }}</span>
                        <el-checkbox
                            v-for="fn in page.funcs || []"
                            :key="fn.func_cd"
                            v-model="permState[page.menu_cd + ':' + fn.func_cd]"
                            :label="fn.func_nm"
                            size="small"
                            border
                        />
                    </div>
                </div>
            </div>
            <template #footer>
                <el-button @click="permVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSavePerms" :loading="permSaving">保存权限</el-button>
            </template>
        </el-dialog>

        <!-- 成员管理 -->
        <el-dialog title="成员管理" v-model="memberVisible" width="500px">
            <div style="display:flex;gap:8px;margin-bottom:12px">
                <el-select v-model="newMember" placeholder="选择用户" filterable style="flex:1">
                    <el-option v-for="u in allUsers" :key="u.user_cd" :label="`${u.user_cd} - ${u.user_nm}`" :value="u.user_cd" />
                </el-select>
                <el-button type="primary" @click="handleAddMember" :disabled="!newMember">添加</el-button>
            </div>
            <el-table :data="members" v-loading="memberLoading" stripe>
                <el-table-column prop="user_cd" label="用户编码" width="120" />
                <el-table-column prop="user_nm" label="用户名称" width="160" />
                <el-table-column label="操作" width="100">
                    <template #default="{ row }">
                        <el-button type="danger" link size="small" @click="handleRemoveMember(row)">移除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { watch } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
    fetchGroups, createGroup, updateGroup, deleteGroup,
    fetchGroupMembers, addGroupMember, removeGroupMember,
    fetchGroupRights, setGroupRights,
    fetchUsers, fetchPermTree
} from '@/api/system'

const authStore = useAuthStore()

const groups = ref<Record<string,unknown>[]>([])
const loading = ref(false); const page = ref(1); const perPage = ref(20); const total = ref(0)

const dialogVisible = ref(false); const editing = ref<Record<string,string>|null>(null); const saving = ref(false)
const form = reactive({ group_cd: '', group_nm: '', status: '1' })

const memberVisible = ref(false); const memberLoading = ref(false)
const currentGroupCd = ref('')
const members = ref<{ user_cd: string; user_nm: string }[]>([])
const newMember = ref('')
const allUsers = ref<{ user_cd: string; user_nm: string }[]>([])

// 权限设置
const permVisible = ref(false); const permLoading = ref(false); const permSaving = ref(false)
const permState = reactive<Record<string, boolean>>({})
const permTree = ref<{ menu_cd: string; menu_nm: string; children: { menu_cd: string; menu_nm: string; funcs: { func_cd: string; func_nm: string }[] }[] }[]>([])

watch(page, () => loadData())
watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchGroups()
        const list = (res.data || []) as never[]
        total.value = list.length
        groups.value = list.slice((page.value - 1) * perPage.value, page.value * perPage.value)
    } catch {
        ElMessage.error('加载用户组列表失败')
    } finally { loading.value = false }
}

function openDialog(row?: Record<string,string>) {
    editing.value = row || null
    if (row) {
        form.group_cd = row.group_cd || ''
        form.group_nm = row.group_nm || ''
        form.status = row.status || '1'
    } else {
        form.group_cd = ''; form.group_nm = ''; form.status = '1'
    }
    dialogVisible.value = true
}

async function handleSave() {
    if (!form.group_cd || !form.group_nm) {
        ElMessage.warning('编码和名称为必填项')
        return
    }
    saving.value = true
    try {
        const payload: Record<string, string> = { group_nm: form.group_nm, status: form.status, useflg: '1' }
        if (editing.value) {
            await updateGroup(editing.value.group_cd, payload)
            ElMessage.success('更新成功')
        } else {
            payload.group_cd = form.group_cd
            await createGroup(payload)
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } finally { saving.value = false }
}

async function handleDelete(row: Record<string,string>) {
    try {
        await ElMessageBox.confirm(`确定删除用户组 ${row.group_cd}（${row.group_nm}）？`, '确认删除')
        await deleteGroup(row.group_cd)
        ElMessage.success('已删除')
        loadData()
    } catch (e: unknown) {
        if (e !== 'cancel') {
            const err = e as { response?: { data?: { message?: string } } }
            ElMessage.error(err?.response?.data?.message || '删除失败')
        }
    }
}

async function openMembers(row: Record<string,string>) {
    currentGroupCd.value = row.group_cd || ''
    newMember.value = ''
    memberVisible.value = true
    await Promise.all([loadMembers(), loadAllUsers()])
}

async function loadMembers() {
    memberLoading.value = true
    try {
        const res = await fetchGroupMembers(currentGroupCd.value)
        members.value = (res.data || []) as { user_cd: string; user_nm: string }[]
    } finally { memberLoading.value = false }
}

async function loadAllUsers() {
    try {
        const res = await fetchUsers()
        allUsers.value = ((res.data || []) as { user_cd: string; user_nm: string }[])
            .filter(u => u.user_cd)
    } catch {
        ElMessage.error('加载用户列表失败')
    }
}

async function handleAddMember() {
    if (!newMember.value) return
    try {
        await addGroupMember(currentGroupCd.value, newMember.value)
        ElMessage.success('添加成功')
        newMember.value = ''
        await loadMembers()
    } finally { /* 错误由 Axios 拦截器提示 */ }
}

async function handleRemoveMember(row: { user_cd: string }) {
    try {
        await removeGroupMember(currentGroupCd.value, row.user_cd)
        ElMessage.success('已移除')
        await loadMembers()
    } finally { /* 错误由 Axios 拦截器提示 */ }
}

// ——— 权限设置 ———

async function openPerms(row: Record<string,string>) {
    currentGroupCd.value = row.group_cd || ''
    permVisible.value = true
    permLoading.value = true
    // 重置所有权限状态为 false
    for (const key of Object.keys(permState)) delete permState[key]
    try {
        const [rightsRes, treeRes] = await Promise.all([
            fetchGroupRights(currentGroupCd.value),
            fetchPermTree(),
        ])
        permTree.value = treeRes.data || []
        const rights = (rightsRes.data || []) as { menu_cd: string; func_cd: string }[]
        for (const r of rights) {
            permState[r.menu_cd + ':' + r.func_cd] = true
        }
    } catch {
        ElMessage.error('加载权限失败')
    }
    finally { permLoading.value = false }
}

async function handleSavePerms() {
    permSaving.value = true
    try {
        const rights: { menu_cd: string; func_cd: string }[] = []
        for (const [key, checked] of Object.entries(permState)) {
            if (checked) {
                const [menu_cd, func_cd] = key.split(':')
                rights.push({ menu_cd, func_cd })
            }
        }
        await setGroupRights(currentGroupCd.value, rights)
        ElMessage.success('权限设置成功')
        permVisible.value = false
    } finally { permSaving.value = false }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
