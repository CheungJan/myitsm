<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>仓库管理（共 {{ total }} 条）</span>
                    <div>
                        <el-select v-model="filterUseflg" placeholder="有效性" size="small" style="width:100px;margin-right:8px" @change="filterData">
                            <el-option label="全部" value="" />
                            <el-option label="有效" value="1" />
                            <el-option label="无效" value="0" />
                        </el-select>
                        <el-button type="primary" size="small" @click="openDialog()">新增仓库</el-button>
                    </div>
                </div>
            </template>
            <el-table :data="warehouses" v-loading="loading" stripe>
                <el-table-column prop="whcd" label="编码" width="80" />
                <el-table-column prop="whnm" label="名称" width="160" />
                <el-table-column prop="address" label="地址" min-width="160" />
                <el-table-column prop="phoneno" label="电话" width="120" />
                <el-table-column prop="leader" label="负责人" width="90" />
                <el-table-column label="状态" width="70">
                    <template #default="{ row }">
                        <el-tag :type="row.useflg === '0' ? 'danger' : 'success'" size="small">{{ row.useflg === '0' ? '无效' : '有效' }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="140" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog :title="editing ? '编辑仓库' : '新增仓库'" v-model="dialogVisible" width="500px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="编码" required>
                    <el-input v-model="form.whcd" :disabled="!!editing" />
                </el-form-item>
                <el-form-item label="名称" required>
                    <el-input v-model="form.whnm" />
                </el-form-item>
                <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
                <el-form-item label="电话"><el-input v-model="form.phoneno" /></el-form-item>
                <el-form-item label="负责人"><el-input v-model="form.leader" /></el-form-item>
                <el-form-item label="状态">
                    <el-select v-model="form.useflg" style="width:100%">
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchWarehouses } from '@/api/warehouse'

const warehouses = ref<Record<string,unknown>[]>([])
const allData = ref<Record<string,unknown>[]>([])
const loading = ref(false); const total = ref(0); const filterUseflg = ref('')
const dialogVisible = ref(false); const editing = ref<Record<string,unknown>|null>(null); const saving = ref(false)
const form = reactive({ whcd: '', whnm: '', address: '', phoneno: '', leader: '', useflg: '1' })

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchWarehouses()
        allData.value = (res.data || []) as Record<string,unknown>[]
        filterData()
    } finally { loading.value = false }
}

function filterData() {
    let list = allData.value
    if (filterUseflg.value) list = list.filter(r => r.useflg === filterUseflg.value)
    total.value = list.length
    warehouses.value = list
}

function openDialog(row?: Record<string,unknown>) {
    if (row) { editing.value = row; form.whcd = row.whcd as string; form.whnm = row.whnm as string; form.address = (row.address as string)||''; form.phoneno = (row.phoneno as string)||''; form.leader = (row.leader as string)||''; form.useflg = (row.useflg as string)||'1' }
    else { editing.value = null; Object.assign(form, { whcd:'',whnm:'',address:'',phoneno:'',leader:'',useflg:'1' }) }
    dialogVisible.value = true
}

async function handleSave() {
    if (!form.whcd || !form.whnm) { ElMessage.warning('编码和名称为必填项'); return }
    saving.value = true
    try {
        const token = localStorage.getItem('token')
        const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
        if (editing.value) {
            await fetch(`/api/v1/warehouses/${editing.value.whcd}`, { method: 'PUT', headers, body: JSON.stringify(form) })
            ElMessage.success('更新成功')
        } else {
            await fetch('/api/v1/warehouses', { method: 'POST', headers, body: JSON.stringify(form) })
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } catch { ElMessage.error('保存失败') }
    finally { saving.value = false }
}

async function handleDelete(row: Record<string,unknown>) {
    try {
        await ElMessageBox.confirm(`确定删除仓库 ${row.whcd}(${row.whnm})？`, '确认删除')
        const token = localStorage.getItem('token')
        await fetch(`/api/v1/warehouses/${row.whcd}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } })
        ElMessage.success('已删除')
        loadData()
    } catch (e: unknown) { if (e !== 'cancel') ElMessage.error('删除失败') }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
