<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>物料管理（共 {{ total }} 条）</span>
                    <div>
                        <el-input v-model="search" placeholder="搜索编码或名称" clearable style="width:200px" @change="loadData" />
                        <el-button type="primary" size="small" style="margin-left:8px" @click="openDialog()">新增物料</el-button>
                    </div>
                </div>
            </template>
            <el-table :data="items" v-loading="loading" stripe>
                <el-table-column prop="item_cd" label="物料编码" width="120" />
                <el-table-column prop="item_nm" label="物料名称" min-width="150" />
                <el-table-column prop="class_cd" label="分类编码" width="100" />
                <el-table-column prop="itemanm" label="别名" width="120" />
                <el-table-column prop="unit" label="单位" width="80" />
                <el-table-column prop="useflg" label="状态" width="80" />
                <el-table-column label="操作" width="180" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
                        <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
        </el-card>

        <el-dialog :title="editing ? '编辑物料' : '新增物料'" v-model="dialogVisible" width="500px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="编码" required><el-input v-model="form.item_cd" :disabled="!!editing" /></el-form-item>
                <el-form-item label="名称" required><el-input v-model="form.item_nm" /></el-form-item>
                <el-form-item label="分类编码"><el-input v-model="form.class_cd" /></el-form-item>
                <el-form-item label="别名"><el-input v-model="form.itemanm" /></el-form-item>
                <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
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
import { fetchItems, createItem, updateItem, deleteItem } from '@/api/master'

const items = ref<Record<string,unknown>[]>([])
const loading = ref(false); const search = ref(''); const page = ref(1); const perPage = ref(20); const total = ref(0)
const dialogVisible = ref(false); const editing = ref<Record<string,string>|null>(null); const saving = ref(false)
const form = reactive({ item_cd: '', item_nm: '', class_cd: '', itemanm: '', unit: '' })


watch(page, () => loadData())
watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchItems({ page: String(page.value), per_page: String(perPage.value) })
        const data = res.data as { items: Record<string,unknown>[], total: number }
        items.value = data.items || []
        total.value = data.total || 0
    } finally { loading.value = false }
}

function openDialog(row?: Record<string,string>) {
    if (row) {
        editing.value = row
        form.item_cd = row.item_cd || ''; form.item_nm = row.item_nm || ''
        form.class_cd = row.class_cd || ''; form.itemanm = row.itemanm || ''; form.unit = row.unit || ''
    } else {
        editing.value = null
        Object.assign(form, { item_cd: '', item_nm: '', class_cd: '', itemanm: '', unit: '' })
    }
    dialogVisible.value = true
}

async function handleSave() {
    saving.value = true
    try {
        const payload = { ...form, useflg: '1' }
        if (editing.value) {
            await updateItem(editing.value.item_cd, payload)
            ElMessage.success('更新成功')
        } else {
            await createItem(payload)
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } finally { saving.value = false }
}

async function handleDelete(row: Record<string,string>) {
    await ElMessageBox.confirm(`确定删除物料 ${row.item_cd}？`, '确认')
    await deleteItem(row.item_cd)
    ElMessage.success('已删除')
    loadData()
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
