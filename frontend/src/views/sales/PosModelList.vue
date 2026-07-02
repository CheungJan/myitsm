<template>
  <div class="page">
    <div class="page-header">
      <h2>机型押金标准</h2>
      <el-button type="primary" @click="openCreate">＋ 新增机型</el-button>
    </div>
    <el-alert type="warning" :closable="false" show-icon style="margin-bottom:12px">
      本页已弃用。押金/售价请到 <b>物料管理 → 价格管理</b> 维护(busityp=40 押金/10 销售价);在产机型筛选请到 <b>物料管理 → BOM 维护</b> 设置 useflg。此处仅供历史数据查看。
    </el-alert>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small">
        <el-table-column prop="model_cd" label="机型编码" width="110" />
        <el-table-column prop="model_nm" label="机型名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="item_cd" label="成品物料编码" width="130" show-overflow-tooltip />
        <el-table-column prop="rent_money" label="押金" width="100" align="right"><template #default="{row}">¥{{ Number(row.rent_money||0).toLocaleString() }}</template></el-table-column>
        <el-table-column prop="sale_money" label="售价" width="100" align="right"><template #default="{row}">¥{{ Number(row.sale_money||0).toLocaleString() }}</template></el-table-column>
        <el-table-column label="状态" width="70"><template #default="{row}"><el-tag :type="row.useflg==='1'?'success':'info'" size="small">{{ row.useflg==='1'?'在产':'停产' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="120"><template #default="{row}"><el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button></template></el-table-column>
      </el-table>
    </el-card>

    <el-dialog :title="isEdit?'编辑机型':'新增机型'" v-model="dlg" width="420px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="机型编码"><el-input v-model="form.model_cd" :disabled="isEdit"/></el-form-item>
        <el-form-item label="机型名称"><el-input v-model="form.model_nm"/></el-form-item>
        <el-form-item label="成品物料编码"><el-input v-model="form.item_cd" placeholder="关联 tmm12_items.item_cd"/></el-form-item>
        <el-form-item label="押金金额"><el-input-number v-model="form.rent_money" :min="0" :precision="2" style="width:100%" controls-position="right"/></el-form-item>
        <el-form-item label="销售价格"><el-input-number v-model="form.sale_money" :min="0" :precision="2" style="width:100%" controls-position="right"/></el-form-item>
        <el-form-item label="有效标志"><el-switch v-model="form.useflg" active-value="1" inactive-value="0" active-text="在产" inactive-text="停产"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg=false">取消</el-button><el-button type="primary" :loading="saving" @click="doSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

interface PosModel { model_cd: string; model_nm: string; item_cd?: string; rent_money: number; sale_money: number; useflg: string }
const items = ref<PosModel[]>([]); const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const r = await request.get<never, { data: PosModel[] }>('/deposit/deposit-models')
    items.value = r?.data || []
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
onMounted(load)

const dlg = ref(false); const isEdit = ref(false); const saving = ref(false)
const form = ref<PosModel>({ model_cd: '', model_nm: '', item_cd: '', rent_money: 0, sale_money: 0, useflg: '1' })
function openCreate() { isEdit.value = false; form.value = { model_cd: '', model_nm: '', item_cd: '', rent_money: 0, sale_money: 0, useflg: '1' }; dlg.value = true }
function openEdit(row: PosModel) { isEdit.value = true; form.value = { model_cd: row.model_cd, model_nm: row.model_nm, item_cd: row.item_cd || '', rent_money: Number(row.rent_money)||0, sale_money: Number(row.sale_money)||0, useflg: row.useflg }; dlg.value = true }
async function doSave() {
  saving.value = true
  try {
    const payload = { model_nm: form.value.model_nm, item_cd: form.value.item_cd, rent_money: form.value.rent_money, sale_money: form.value.sale_money, useflg: form.value.useflg }
    if (isEdit.value) {
      await request.put(`/deposit/deposit-models/${form.value.model_cd}`, payload)
    } else {
      await request.post('/deposit/deposit-models', { model_cd: form.value.model_cd, ...payload })
    }
    dlg.value = false; load(); ElMessage.success('保存成功')
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px }
.page-header h2 { font-size:18px; font-weight:600; margin:0 }
</style>
