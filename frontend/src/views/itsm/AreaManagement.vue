<template>
  <div class="area-management">
    <div class="page-header">
      <h2>区域人员管理</h2>
      <el-button type="primary" size="small" @click="openCreate">新增区域</el-button>
    </div>

    <div class="filter-bar">
      <el-select v-model="filterUseflg" size="small" style="width:140px" clearable placeholder="全部状态" @change="load">
        <el-option label="有效" value="1"/>
        <el-option label="停用" value="0"/>
      </el-select>
    </div>

    <el-table :data="areas" v-loading="loading" size="small" border>
      <el-table-column prop="area_cd" label="区域编码" width="120"/>
      <el-table-column prop="area_nm" label="划区名称" width="160"/>
      <el-table-column label="区域负责人" width="140">
        <template #default="{ row }">{{ row.usercd_nm || row.usercd || '-' }}</template>
      </el-table-column>
      <el-table-column prop="parent_cd" label="上级区域" width="120">
        <template #default="{ row }">{{ row.parent_cd || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.useflg === '1' ? 'success' : 'info'" size="small">{{ row.useflg === '1' ? '有效' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" link type="primary" @click="openUserAssign(row)">分配用户</el-button>
          <el-button size="small" link type="danger" @click="doDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 区域表单弹窗 -->
    <el-dialog v-model="formVisible" :title="editCd ? '编辑区域' : '新增区域'" width="480px">
      <el-form :model="form" label-width="90px" size="small" :rules="rules" ref="formRef">
        <el-form-item label="区域编码" prop="area_cd">
          <el-input v-model="form.area_cd" :disabled="!!editCd" placeholder="如 A1"/>
        </el-form-item>
        <el-form-item label="划区名称" prop="area_nm">
          <el-input v-model="form.area_nm" placeholder="如 华东"/>
        </el-form-item>
        <el-form-item label="上级区域">
          <el-input v-model="form.parent_cd" placeholder="可选"/>
        </el-form-item>
        <el-form-item label="区域负责人">
          <el-select v-model="form.usercd" filterable clearable style="width:100%" placeholder="选择负责人">
            <el-option v-for="u in userOptions" :key="u.user_cd" :label="`${u.user_nm} (${u.user_cd})`" :value="u.user_cd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="有效">
          <el-switch v-model="form.useflg" active-value="1" inactive-value="0"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="formVisible=false">取消</el-button>
        <el-button size="small" type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 用户分配弹窗 -->
    <el-dialog v-model="userVisible" :title="`分配用户 - ${currentArea?.area_nm || ''}`" width="600px">
      <el-table :data="userList" size="small" border max-height="400" @selection-change="onSelectionChange" ref="userTableRef">
        <el-table-column type="selection" width="50"/>
        <el-table-column prop="user_cd" label="用户编码" width="120"/>
        <el-table-column prop="user_nm" label="姓名" width="120"/>
        <el-table-column prop="dept_cd" label="部门" width="120"/>
      </el-table>
      <template #footer>
        <el-button size="small" @click="userVisible=false">取消</el-button>
        <el-button size="small" type="primary" @click="submitUserAssign">保存分配</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchAreas, createArea, updateArea, deleteArea, fetchAreaUsers, setAreaUsers } from '@/api/master'
import { fetchUsers } from '@/api/system'
import type { AreaRecord, AreaUserRecord } from '@/api/master'
import type { UserItem } from '@/api/system'

const areas = ref<AreaRecord[]>([])
const loading = ref(false)
const formVisible = ref(false)
const editCd = ref('')
const form = ref<Record<string, unknown>>({})
const formRef = ref()
const filterUseflg = ref('')
const userOptions = ref<UserItem[]>([])

const userVisible = ref(false)
const currentArea = ref<AreaRecord | null>(null)
const userList = ref<AreaUserRecord[]>([])
const selectedUsers = ref<AreaUserRecord[]>([])
const userTableRef = ref()

const rules = {
  area_cd: [{ required: true, message: '请输入区域编码', trigger: 'blur' }],
  area_nm: [{ required: true, message: '请输入划区名称', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const r = await fetchAreas()
    let list = r?.data || []
    if (filterUseflg.value) {
      list = list.filter((a: AreaRecord) => (a.useflg || '') === filterUseflg.value)
    }
    areas.value = list
  } catch {
    areas.value = []
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  try {
    const r = await fetchUsers({ useflg: '1' })
    userOptions.value = r?.data || []
  } catch {
    userOptions.value = []
  }
}

function openCreate() {
  editCd.value = ''
  form.value = { area_cd: '', area_nm: '', parent_cd: '', usercd: '', useflg: '1' }
  formVisible.value = true
}

function openEdit(row: AreaRecord) {
  editCd.value = row.area_cd
  form.value = { area_cd: row.area_cd, area_nm: row.area_nm, parent_cd: row.parent_cd || '', usercd: row.usercd || '', useflg: row.useflg || '1' }
  formVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  try { await formRef.value.validate() } catch { return }
  const data = { ...form.value }
  try {
    if (editCd.value) {
      await updateArea(editCd.value, data)
      ElMessage.success('编辑成功')
    } else {
      await createArea(data)
      ElMessage.success('新增成功')
    }
    formVisible.value = false
    await load()
  } catch {
    ElMessage.error(editCd.value ? '编辑失败' : '新增失败')
  }
}

async function doDelete(row: AreaRecord) {
  try {
    await ElMessageBox.confirm(`确认删除区域 ${row.area_nm}？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await deleteArea(row.area_cd)
    ElMessage.success('删除成功')
    await load()
  } catch {
    ElMessage.error('删除失败（可能有关联用户）')
  }
}

async function openUserAssign(row: AreaRecord) {
  currentArea.value = row
  userVisible.value = true
  try {
    const r = await fetchAreaUsers(row.area_cd)
    userList.value = r?.data || []
    // 默认勾选 choose=1 的用户
    const chosen = userList.value.filter(u => u.choose === 1)
    selectedUsers.value = chosen
    // 等 DOM 渲染后设置勾选
    setTimeout(() => {
      chosen.forEach(u => {
        userTableRef.value?.toggleRowSelection(u, true)
      })
    }, 50)
  } catch {
    userList.value = []
  }
}

function onSelectionChange(rows: AreaUserRecord[]) {
  selectedUsers.value = rows
}

async function submitUserAssign() {
  if (!currentArea.value) return
  const userCds = selectedUsers.value.map(u => u.user_cd)
  try {
    await setAreaUsers(currentArea.value.area_cd, userCds)
    ElMessage.success('分配成功')
    userVisible.value = false
    await load()
  } catch {
    ElMessage.error('分配失败')
  }
}

onMounted(() => {
  load()
  loadUsers()
})
</script>

<style scoped>
.area-management { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.page-header h2 { margin: 0; font-size: 18px; }
.filter-bar { margin-bottom: 12px; }
</style>
