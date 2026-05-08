<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>客户管理（共 {{ total }} 条）</span>
                    <el-button type="primary" size="small" @click="openDialog()">新增客户</el-button>
                </div>
            </template>
            <el-table :data="customers" v-loading="loading" stripe>
                <el-table-column prop="cust_cd" label="客户编码" width="120" />
                <el-table-column prop="cust_nm" label="客户名称" min-width="180" />
                <el-table-column prop="class_cd" label="分类" width="100" />
                <el-table-column prop="busi_typ" label="业务类型" width="100" />
                <el-table-column prop="phone_no" label="电话" width="140" />
                <el-table-column prop="contactor" label="联系人" width="100" />
                <el-table-column label="操作" width="180" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination v-model:current-page="page" :total="total" :page-size="20"
                layout="total, prev, pager, next" @current-change="loadData"
                style="margin-top:16px;justify-content:flex-end" />
        </el-card>

        <el-dialog :title="editing ? '编辑客户' : '新增客户'" v-model="dialogVisible" width="500px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="编码" required><el-input v-model="form.cust_cd" :disabled="!!editing" /></el-form-item>
                <el-form-item label="名称" required><el-input v-model="form.cust_nm" /></el-form-item>
                <el-form-item label="分类"><el-input v-model="form.class_cd" /></el-form-item>
                <el-form-item label="业务类型"><el-input v-model="form.busi_typ" /></el-form-item>
                <el-form-item label="电话"><el-input v-model="form.phone_no" /></el-form-item>
                <el-form-item label="联系人"><el-input v-model="form.contactor" /></el-form-item>
                <el-form-item label="地址"><el-input v-model="form.address" type="textarea" /></el-form-item>
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
import { fetchCustomers, createCustomer, updateCustomer, deleteCustomer } from '@/api/master'

const customers = ref<Record<string,unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

const dialogVisible = ref(false)
const editing = ref<Record<string,string>|null>(null)
const saving = ref(false)
const form = reactive({ cust_cd: '', cust_nm: '', class_cd: '', busi_typ: '', phone_no: '', contactor: '', address: '' })

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchCustomers({ page: String(page.value), per_page: '20' })
        const data = res.data as { items: Record<string,unknown>[], total: number }
        customers.value = data.items || []
        total.value = data.total || 0
    } finally { loading.value = false }
}

function openDialog(row?: Record<string,string>) {
    if (row) {
        editing.value = row
        form.cust_cd = row.cust_cd; form.cust_nm = row.cust_nm || ''
        form.class_cd = row.class_cd || ''; form.busi_typ = row.busi_typ || ''
        form.phone_no = row.phone_no || ''; form.contactor = row.contactor || ''
        form.address = row.address || ''
    } else {
        editing.value = null
        form.cust_cd = ''; form.cust_nm = ''; form.class_cd = ''
        form.busi_typ = ''; form.phone_no = ''; form.contactor = ''; form.address = ''
    }
    dialogVisible.value = true
}

async function handleSave() {
    saving.value = true
    try {
        if (editing.value) {
            await updateCustomer(editing.value.cust_cd, { ...form })
            ElMessage.success('更新成功')
        } else {
            await createCustomer({ ...form, useflg: '1' })
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } catch { /* */ }
    finally { saving.value = false }
}

async function handleDelete(row: Record<string,string>) {
    await ElMessageBox.confirm(`确定删除客户 ${row.cust_cd}？`, '确认')
    try {
        await deleteCustomer(row.cust_cd)
        ElMessage.success('已删除')
        loadData()
    } catch { /* */ }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
