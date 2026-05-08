<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>客户管理（共 {{ total }} 条）</span>
                    <div class="filter-bar">
                        <el-select v-model="classFilter" placeholder="分类筛选" clearable style="width:140px" @change="onFilterChange">
                            <el-option v-for="c in classOptions" :key="c" :label="c" :value="c" />
                        </el-select>
                        <el-input v-model="search" placeholder="搜索编码或名称" clearable style="width:180px" @keyup.enter="onFilterChange" />
                        <el-button type="primary" size="small" @click="onFilterChange">查询</el-button>
                        <el-button type="success" size="small" @click="openDialog()">新增</el-button>
                    </div>
                </div>
            </template>
            <el-table :data="customers" v-loading="loading" stripe>
                <el-table-column prop="cust_cd" label="编码" width="120" />
                <el-table-column prop="cust_nm" label="名称" min-width="160" />
                <el-table-column prop="class_cd" label="分类" width="100" />
                <el-table-column prop="busi_typ" label="业务类型" width="100" />
                <el-table-column prop="phone_no" label="电话" width="140" />
                <el-table-column prop="contactor" label="联系人" width="100" />
                <el-table-column prop="useflg" label="状态" width="80" />
                <el-table-column label="操作" width="160" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
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
import { watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchCustomers, createCustomer, updateCustomer, deleteCustomer } from '@/api/master'
import AppPagination from '@/components/common/AppPagination.vue'

const customers = ref<Record<string,unknown>[]>([])
const loading = ref(false); const search = ref(''); const classFilter = ref('')
const page = ref(1); const perPage = ref(20); const total = ref(0)
const classOptions = ref<string[]>([])
const dialogVisible = ref(false); const editing = ref<Record<string,string>|null>(null); const saving = ref(false)
const form = reactive({ cust_cd: '', cust_nm: '', class_cd: '', busi_typ: '', phone_no: '', contactor: '', address: '' })


watch(page, () => doLoad(classFilter.value || search.value ? true : false))
watch(perPage, () => { page.value = 1; doLoad(classFilter.value || search.value ? true : false) })
onMounted(async () => {
    const res = await fetchCustomers({ page: '1', per_page: '100000' })
    const all = ((res.data as { items: Record<string,unknown>[] }).items || []).map(r => (r as Record<string,string>).class_cd).filter(Boolean)
    classOptions.value = [...new Set(all)].sort()
    await doLoad(false)
})

function onFilterChange() { page.value = 1; doLoad(true) }

async function doLoad(filtered: boolean) {
    loading.value = true
    try {
        const limit = filtered ? 100000 : perPage.value
        const res = await fetchCustomers({ page: '1', per_page: String(limit) })
        let list = ((res.data as { items: Record<string,unknown>[] }).items || []) as never[]
        if (classFilter.value) list = list.filter(r => (r as Record<string,string>).class_cd === classFilter.value)
        if (search.value) {
            const q = search.value.toLowerCase()
            list = list.filter(r => { const d=r as Record<string,string>; return (d.cust_cd||'').includes(q)||(d.cust_nm||'').includes(q) })
        }
        total.value = list.length
        customers.value = filtered ? list.slice((page.value-1)*perPage.value, page.value*perPage.value) : list
    } finally { loading.value = false }
}

function openDialog(row?: Record<string,string>) {
    editing.value = row || null
    if (row) Object.assign(form, { cust_cd: row.cust_cd, cust_nm: row.cust_nm||'', class_cd: row.class_cd||'', busi_typ: row.busi_typ||'', phone_no: row.phone_no||'', contactor: row.contactor||'', address: row.address||'' })
    else Object.assign(form, { cust_cd: '', cust_nm: '', class_cd: '', busi_typ: '', phone_no: '', contactor: '', address: '' })
    dialogVisible.value = true
}

async function refreshClassOptions() {
    const res = await fetchCustomers({ page: '1', per_page: '100000' })
    const all = ((res.data as { items: Record<string,unknown>[] }).items || []).map(r => (r as Record<string,string>).class_cd).filter(Boolean)
    classOptions.value = [...new Set(all)].sort()
}

async function handleSave() {
    saving.value = true
    try {
        const payload = { ...form, useflg: '1' }
        if (editing.value) { await updateCustomer(editing.value.cust_cd, payload); ElMessage.success('更新成功') }
        else { await createCustomer(payload); ElMessage.success('创建成功') }
        dialogVisible.value = false
        await refreshClassOptions()
        onFilterChange()
    } finally { saving.value = false }
}

async function handleDelete(row: Record<string,string>) {
    await ElMessageBox.confirm(`确定删除 ${row.cust_cd}？`, '确认')
    await deleteCustomer(row.cust_cd)
    ElMessage.success('已删除')
    await refreshClassOptions()
    onFilterChange()
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
</style>
