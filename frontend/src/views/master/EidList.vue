<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="page-header">
                    <span>EID 设备管理（共 {{ total }} 条）</span>
                    <el-button type="primary" size="small" @click="openDialog()">新增设备</el-button>
                </div>
            </template>
            <el-table :data="eids" v-loading="loading" stripe>
                <el-table-column prop="eid" label="设备 SN" min-width="150" />
                <el-table-column prop="item_cd" label="物料编码" width="120" />
                <el-table-column prop="etyp" label="类型" width="80" />
                <el-table-column prop="whcd" label="仓库" width="80" />
                <el-table-column prop="sflg" label="状态" width="80" />
                <el-table-column prop="new_old" label="新旧" width="80" />
                <el-table-column prop="prddate" label="生产日期" width="120" />
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

        <el-dialog :title="editing ? '编辑 EID' : '新增 EID'" v-model="dialogVisible" width="500px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="SN" required><el-input v-model="form.eid" :disabled="!!editing" /></el-form-item>
                <el-form-item label="物料编码" required><el-input v-model="form.item_cd" /></el-form-item>
                <el-form-item label="类型"><el-input v-model="form.etyp" /></el-form-item>
                <el-form-item label="仓库"><el-input v-model="form.whcd" /></el-form-item>
                <el-form-item label="状态"><el-input v-model="form.sflg" /></el-form-item>
                <el-form-item label="新旧"><el-input v-model="form.new_old" /></el-form-item>
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
import { fetchEidList, createEid, updateEid, deleteEid } from '@/api/master'

const eids = ref<Record<string,unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

const dialogVisible = ref(false)
const editing = ref<Record<string,string>|null>(null)
const saving = ref(false)
const form = reactive({ eid: '', item_cd: '', etyp: '0', whcd: '', sflg: '8', new_old: '1' })

onMounted(() => loadData())

async function loadData() {
    loading.value = true
    try {
        const res = await fetchEidList({ page: String(page.value), per_page: '20' })
        const data = res.data as { items: Record<string,unknown>[], total: number }
        eids.value = data.items || []
        total.value = data.total || 0
    } finally { loading.value = false }
}

function openDialog(row?: Record<string,string>) {
    if (row) {
        editing.value = row
        form.eid = row.eid; form.item_cd = row.item_cd || ''
        form.etyp = row.etyp || '0'; form.whcd = row.whcd || ''
        form.sflg = row.sflg || '8'; form.new_old = row.new_old || '1'
    } else {
        editing.value = null
        form.eid = ''; form.item_cd = ''; form.etyp = '0'
        form.whcd = ''; form.sflg = '8'; form.new_old = '1'
    }
    dialogVisible.value = true
}

async function handleSave() {
    saving.value = true
    try {
        if (editing.value) {
            await updateEid(editing.value.eid, { ...form })
            ElMessage.success('更新成功')
        } else {
            await createEid({ ...form, useflg: '1' })
            ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
    } catch { /* */ }
    finally { saving.value = false }
}

async function handleDelete(row: Record<string,string>) {
    await ElMessageBox.confirm(`确定删除 EID ${row.eid}？`, '确认')
    try {
        await deleteEid(row.eid)
        ElMessage.success('已删除')
        loadData()
    } catch { /* */ }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
