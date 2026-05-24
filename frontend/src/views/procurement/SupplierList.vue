<template>
  <div class="page">
    <div class="page-header">
      <h2>供应商管理</h2>
      <div style="display:flex;gap:8px;">
        <el-input v-model="searchKeyword" placeholder="搜索编码/名称" clearable style="width:200px" size="small" @keyup.enter="handleSearch" @clear="handleSearch" />
        <el-button type="primary" size="small" @click="openCreate">新增供应商</el-button>
      </div>
    </div>
    <div style="display:flex;gap:12px;">
      <div style="width:180px;flex-shrink:0;">
        <el-card shadow="never">
          <template #header><span style="font-size:14px;font-weight:600;">供应商分类</span></template>
          <el-menu :default-active="activeClass" @select="handleClassSelect" style="border-right:none;">
            <el-menu-item index=""><span style="color:#909399;">全部</span></el-menu-item>
            <el-menu-item v-for="c in classList" :key="c.class_cd" :index="c.class_cd" style="display:flex;justify-content:space-between;align-items:center;">
              <span>{{ c.class_nm }}</span>
              <span style="display:flex;gap:2px;margin-left:4px;" @click.stop>
                <el-button link size="small" @click="openClassDialog(c)"><el-icon><EditPen /></el-icon></el-button>
                <el-button link size="small" @click="handleDeleteClass(c)"><el-icon><Delete /></el-icon></el-button>
              </span>
            </el-menu-item>
          </el-menu>
          <div style="padding:8px;border-top:1px solid #ebeef5;margin-top:8px;">
            <el-button link size="small" @click="openClassDialog(null)">+ 新增分类</el-button>
          </div>
        </el-card>
      </div>
      <div style="flex:1;">
        <el-card shadow="never">
          <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row>
            <el-table-column prop="supp_cd" label="编码" width="90" />
            <el-table-column prop="supp_nm" label="名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="custanm" label="简称" width="100" />
            <el-table-column label="分类" width="100">
              <template #default="{row}">{{ classMap[row.class_cd as string] || row.class_cd }}</template>
            </el-table-column>
            <el-table-column prop="contactor" label="联系人" width="80" />
            <el-table-column prop="phoneno" label="电话" width="110" />
            <el-table-column label="状态" width="70">
              <template #default="{row}">
                <el-tag :type="row.useflg==='0'?'info':'success'" size="small">{{ row.useflg==='0'?'停用':'启用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{row}">
                <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:12px;display:flex;justify-content:space-between;align-items:center;">
            <span style="color:#909399;font-size:13px;">共 {{ total }} 条</span>
            <el-pagination v-model:current-page="page" :page-size="perPage" :total="total" layout="prev,pager,next" small @current-change="load" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="formTitle" v-model="formVisible" width="650px" @close="resetForm">
      <el-form ref="formRef" :model="form" label-width="100px" size="small">
        <el-divider content-position="left">基本信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="编码">
              <el-input v-model="form.supp_cd" :disabled="isEdit" :placeholder="isEdit?'':'留空自动生成'" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="名称" required>
              <el-input v-model="form.supp_nm" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="简称"><el-input v-model="form.custanm" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="简码"><el-input v-model="form.custbrcd" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="分类">
              <el-select v-model="form.class_cd" style="width:100%">
                <el-option v-for="c in classList" :key="c.class_cd" :label="c.class_nm" :value="c.class_cd" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="form.useflg" active-value="1" inactive-value="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系人"><el-input v-model="form.contactor" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话"><el-input v-model="form.phoneno" /></el-form-item>
          </el-col>
        </el-row>
        <el-collapse>
          <el-collapse-item title="扩展信息">
            <el-row :gutter="16">
              <el-col :span="24"><el-form-item label="地址"><el-input v-model="form.address" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="8"><el-form-item label="邮编"><el-input v-model="form.zipcd" /></el-form-item></el-col>
              <el-col :span="8"><el-form-item label="传真"><el-input v-model="form.faxno" /></el-form-item></el-col>
              <el-col :span="8"><el-form-item label="等级"><el-input v-model="form.scale" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="24"><el-form-item label="税号"><el-input v-model="form.taxno" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="开户银行"><el-input v-model="form.banknm" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="银行账号"><el-input v-model="form.bankaccno" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="采购代表"><el-input v-model="form.pcrep" /></el-form-item></el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>
      </el-form>
      <template #footer>
        <el-button size="small" @click="formVisible=false">取消</el-button>
        <el-button type="primary" size="small" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情 Tab 弹窗 -->
    <el-dialog :title="'供应商 — ' + (detailData?.supp_nm || '')" v-model="detailVisible" width="750px">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="基本信息" name="info">
          <el-descriptions v-if="detailData" :column="2" border size="small">
            <el-descriptions-item label="编码">{{ detailData.supp_cd }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ detailData.supp_nm }}</el-descriptions-item>
            <el-descriptions-item label="简称">{{ detailData.custanm || '-' }}</el-descriptions-item>
            <el-descriptions-item label="简码">{{ detailData.custbrcd || '-' }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ classMap[detailData.class_cd as string] || detailData.class_cd }}</el-descriptions-item>
            <el-descriptions-item label="联系人">{{ detailData.contactor || '-' }}</el-descriptions-item>
            <el-descriptions-item label="电话">{{ detailData.phoneno || '-' }}</el-descriptions-item>
            <el-descriptions-item label="传真">{{ detailData.faxno || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="detailData.useflg==='0'?'info':'success'" size="small">{{ detailData.useflg==='0'?'停用':'启用' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="地址" :span="2">{{ detailData.address || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="供应商品" name="items">
          <div style="margin-bottom:8px;"><el-button type="primary" size="small" @click="openAddItem">+ 新增供应商品</el-button></div>
          <el-table :data="suppItems" v-loading="suppItemsLoading" size="small" stripe>
            <el-table-column prop="itemcd" label="物料编码" width="90" />
            <el-table-column prop="item_nm" label="名称" min-width="140" show-overflow-tooltip />
            <el-table-column label="默认" width="60"><template #default="{row}">
              <el-tag :type="row.dfltflg==='Y'?'success':'info'" size="small">{{ row.dfltflg==='Y'?'是':'否' }}</el-tag>
            </template></el-table-column>
            <el-table-column prop="delivercycle" label="配送周期(天)" width="100" />
            <el-table-column prop="servicecycle" label="服务周期(天)" width="100" />
            <el-table-column prop="guaranteeperiod" label="保修期(天)" width="100" />
            <el-table-column label="操作" width="120"><template #default="{row}">
              <el-button link type="primary" size="small" @click="openEditItem(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDeleteItem(row)">删除</el-button>
            </template></el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="价格报价" name="prices">
          <div style="margin-bottom:8px;"><el-button type="primary" size="small" @click="openAddPrice">+ 新增报价</el-button></div>
          <el-table :data="suppPrices" v-loading="suppPricesLoading" size="small" stripe>
            <el-table-column prop="itemcd" label="物料编码" width="90" />
            <el-table-column prop="item_nm" label="名称" min-width="120" show-overflow-tooltip />
            <el-table-column prop="min_qty" label="最小起订" width="80" />
            <el-table-column prop="itemprice" label="单价" width="100" />
            <el-table-column prop="effective_date" label="生效" width="100" />
            <el-table-column prop="expire_date" label="失效" width="100" />
            <el-table-column label="操作" width="120"><template #default="{row}">
              <el-button link type="primary" size="small" @click="openEditPrice(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDeletePrice(row)">删除</el-button>
            </template></el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 供应商品新增/编辑弹窗 -->
    <el-dialog :title="itemIsEdit?'编辑供应商品':'新增供应商品'" v-model="itemDialogVisible" width="400px">
      <el-form :model="itemForm" label-width="80px" size="small">
        <el-form-item label="物料" required>
          <el-select v-model="itemForm.itemcd" :disabled="itemIsEdit" style="width:100%" filterable placeholder="搜索物料编码/名称">
            <el-option v-for="it in allItems" :key="it.item_cd as string" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认"><el-switch v-model="itemForm.dfltflg" active-value="Y" inactive-value="N" /></el-form-item>
        <el-form-item label="配送周期(天)"><el-input-number v-model="itemForm.delivercycle" :min="0" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="服务周期(天)"><el-input-number v-model="itemForm.servicecycle" :min="0" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="保修期(天)"><el-input-number v-model="itemForm.guaranteeperiod" :min="0" controls-position="right" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button size="small" @click="itemDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="handleSaveItem">保存</el-button></template>
    </el-dialog>

    <!-- 价格新增/编辑弹窗 -->
    <el-dialog :title="priceIsEdit?'编辑报价':'新增报价'" v-model="priceDialogVisible" width="400px">
      <el-form :model="priceForm" label-width="80px" size="small">
        <el-form-item label="物料" required>
          <el-select v-model="priceForm.itemcd" :disabled="priceIsEdit" style="width:100%">
            <el-option v-for="it in suppItems" :key="it.itemcd as string" :label="`${it.itemcd} ${it.item_nm}`" :value="it.itemcd" />
          </el-select>
        </el-form-item>
        <el-form-item label="最小起订"><el-input-number v-model="priceForm.min_qty" :min="0" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="单价" required><el-input-number v-model="priceForm.itemprice" :min="0" :precision="2" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="生效日期"><el-date-picker v-model="priceForm.effective_date" type="date" style="width:100%" /></el-form-item>
        <el-form-item label="失效日期"><el-date-picker v-model="priceForm.expire_date" type="date" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button size="small" @click="priceDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="handleSavePrice">保存</el-button></template>
    </el-dialog>

    <!-- 分类管理弹窗 -->
    <el-dialog :title="classDialogTitle" v-model="classDialogVisible" width="400px">
      <el-form :model="classForm" label-width="80px" size="small">
        <el-form-item label="编码" required><el-input v-model="classForm.class_cd" :disabled="classIsEdit" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="classForm.class_nm" /></el-form-item>
        <el-form-item label="上级">
          <el-select v-model="classForm.parent" style="width:100%" clearable>
            <el-option v-for="c in classList" :key="c.class_cd" :label="c.class_nm" :value="c.class_cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型"><el-input v-model="classForm.classtyp" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="classDialogVisible=false">取消</el-button>
        <el-button v-if="classIsEdit" link type="danger" size="small" @click="handleDeleteClass">删除</el-button>
        <el-button type="primary" size="small" @click="handleSaveClass">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { EditPen, Delete } from '@element-plus/icons-vue'
import {
  fetchSuppliersPaginated, createSupplier, updateSupplier, deleteSupplier,
  fetchSupplierClasses, createSupplierClass, updateSupplierClass, deleteSupplierClass,
  fetchSupplierItems, addSupplierItem, updateSupplierItem, deleteSupplierItem,
  fetchSupplierPrices, createSupplierPrice, updateSupplierPrice, deleteSupplierPrice,
  fetchItems,
} from '@/api/master'

const searchKeyword = ref('')
const activeClass = ref('')
const page = ref(1)
const perPage = 20
const total = ref(0)
const items = ref<Record<string,unknown>[]>([])
const loading = ref(false)
const saving = ref(false)
const classList = ref<Record<string,unknown>[]>([])
const classMap = computed(() => {
  const m: Record<string,string> = {}
  classList.value.forEach((c: any) => { m[c.class_cd] = c.class_nm })
  return m
})

// 新增/编辑表单
const formVisible = ref(false)
const isEdit = ref(false)
const form = reactive<Record<string,any>>({
  supp_cd: '', supp_nm: '', custanm: '', custbrcd: '', class_cd: '',
  contactor: '', phoneno: '', useflg: '1',
  address: '', zipcd: '', faxno: '', taxno: '', banknm: '', bankaccno: '', pcrep: '', scale: ''
})
const formTitle = computed(() => isEdit.value ? '编辑供应商' : '新增供应商')

// 详情弹窗
const detailVisible = ref(false)
const detailData = ref<Record<string,unknown>|null>(null)

// 分类表单
const classDialogVisible = ref(false)
const classIsEdit = ref(false)
const classForm = reactive({ class_cd: '', class_nm: '', parent: '', classtyp: '' })
const classDialogTitle = computed(() => classIsEdit.value ? '编辑分类' : '新增分类')

// Tab state
const activeTab = ref('info')

// Supply items
const suppItems = ref<Record<string,unknown>[]>([])
const suppItemsLoading = ref(false)
const itemDialogVisible = ref(false)
const itemIsEdit = ref(false)
const currentItemCd = ref('')
const itemForm = reactive({ itemcd: '', dfltflg: 'N', delivercycle: 0, servicecycle: 0, guaranteeperiod: 0 })
const allItems = ref<Record<string,unknown>[]>([])

// Prices
const suppPrices = ref<Record<string,unknown>[]>([])
const suppPricesLoading = ref(false)
const priceDialogVisible = ref(false)
const priceIsEdit = ref(false)
const currentPriceId = ref(0)
const priceForm = reactive({ itemcd: '', min_qty: 0, itemprice: 0, effective_date: '', expire_date: '' })

async function handleTabChange(tab: string) {
  if (tab === 'items' && suppItems.value.length === 0) {
    suppItemsLoading.value = true
    try {
      const r = await fetchSupplierItems(detailData.value?.supp_cd as string)
      suppItems.value = (r.data as any[]) || []
    } catch { ElMessage.error('加载失败') }
    finally { suppItemsLoading.value = false }
  }
  if (tab === 'prices' && suppPrices.value.length === 0) {
    suppPricesLoading.value = true
    try {
      const r = await fetchSupplierPrices(detailData.value?.supp_cd as string)
      suppPrices.value = (r.data as any[]) || []
    } catch { ElMessage.error('加载失败') }
    finally { suppPricesLoading.value = false }
  }
}

// Item CRUD
function openAddItem() {
  itemIsEdit.value = false; currentItemCd.value = ''
  itemForm.itemcd = ''; itemForm.dfltflg = 'N'; itemForm.delivercycle = 0; itemForm.servicecycle = 0; itemForm.guaranteeperiod = 0
  itemDialogVisible.value = true
}
function openEditItem(row: any) {
  itemIsEdit.value = true; currentItemCd.value = row.itemcd as string
  itemForm.itemcd = row.itemcd; itemForm.dfltflg = row.dfltflg || 'N'
  itemForm.delivercycle = Number(row.delivercycle) || 0; itemForm.servicecycle = Number(row.servicecycle) || 0
  itemForm.guaranteeperiod = Number(row.guaranteeperiod) || 0
  itemDialogVisible.value = true
}
async function handleSaveItem() {
  if (!itemForm.itemcd) { ElMessage.warning('请选择物料'); return }
  try {
    if (itemIsEdit.value) {
      await updateSupplierItem(detailData.value?.supp_cd as string, currentItemCd.value, { ...itemForm, itemcd: undefined })
    } else {
      await addSupplierItem(detailData.value?.supp_cd as string, { ...itemForm })
    }
    itemDialogVisible.value = false
    suppItems.value = []; await handleTabChange('items')
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
}
async function handleDeleteItem(row: any) {
  try { await ElMessageBox.confirm(`确定移除商品 ${row.item_nm}？`, '确认', { type: 'warning' }) } catch { return }
  try {
    await deleteSupplierItem(detailData.value?.supp_cd as string, row.itemcd as string)
    suppItems.value = suppItems.value.filter(i => i.itemcd !== row.itemcd)
    ElMessage.success('删除成功')
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

// Price CRUD
function openAddPrice() {
  priceIsEdit.value = false; currentPriceId.value = 0
  priceForm.itemcd = ''; priceForm.min_qty = 0; priceForm.itemprice = 0; priceForm.effective_date = ''; priceForm.expire_date = ''
  priceDialogVisible.value = true
}
function openEditPrice(row: any) {
  priceIsEdit.value = true; currentPriceId.value = row.id as number
  priceForm.itemcd = row.itemcd; priceForm.min_qty = Number(row.min_qty) || 0; priceForm.itemprice = Number(row.itemprice) || 0
  priceForm.effective_date = row.effective_date || ''; priceForm.expire_date = row.expire_date || ''
  priceDialogVisible.value = true
}
async function handleSavePrice() {
  if (!priceForm.itemcd) { ElMessage.warning('请选择物料'); return }
  try {
    const data = { ...priceForm, itemcd: priceForm.itemcd }
    if (priceIsEdit.value) {
      await updateSupplierPrice(detailData.value?.supp_cd as string, currentPriceId.value, data)
    } else {
      await createSupplierPrice(detailData.value?.supp_cd as string, data)
    }
    priceDialogVisible.value = false
    suppPrices.value = []; await handleTabChange('prices')
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
}
async function handleDeletePrice(row: any) {
  try { await ElMessageBox.confirm('确定删除此报价？', '确认', { type: 'warning' }) } catch { return }
  try {
    await deleteSupplierPrice(detailData.value?.supp_cd as string, row.id as number)
    suppPrices.value = suppPrices.value.filter(p => p.id !== row.id)
    ElMessage.success('删除成功')
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

async function loadAllItems() {
  try { const r = await fetchItems({ per_page: 9999 } as any); allItems.value = (r.data as any)?.items || [] } catch { /* */ }
}

async function load() {
  loading.value = true
  try {
    const res = await fetchSuppliersPaginated({ keyword: searchKeyword.value, class_cd: activeClass.value, page: page.value, per_page: perPage })
    const d = res.data as any
    items.value = d.items || []
    total.value = d.total || 0
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

async function loadClasses() {
  try { const r = await fetchSupplierClasses(); classList.value = (r.data as any[]) || [] } catch { /* empty */ }
}

function handleSearch() { page.value = 1; load() }
function handleClassSelect(index: string) { activeClass.value = index; page.value = 1; load() }

function resetForm() {
  Object.keys(form).forEach(k => { form[k] = k === 'useflg' ? '1' : '' })
  isEdit.value = false
}

function openCreate() { resetForm(); formVisible.value = true }

function openEdit(row: any) {
  isEdit.value = true
  Object.keys(form).forEach(k => { if (row[k] !== undefined) form[k] = row[k] })
  formVisible.value = true
}

function openDetail(row: any) {
  detailData.value = row
  activeTab.value = 'info'
  suppItems.value = []
  suppPrices.value = []
  detailVisible.value = true
}

async function handleSave() {
  if (!form.supp_nm) { ElMessage.warning('请输入供应商名称'); return }
  saving.value = true
  try {
    const data = { ...form }
    if (isEdit.value) {
      await updateSupplier(form.supp_cd as string, data)
      ElMessage.success('修改成功')
    } else {
      await createSupplier(data)
      ElMessage.success('新增成功')
    }
    formVisible.value = false
    await load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
  finally { saving.value = false }
}

async function handleDelete(row: any) {
  try { await ElMessageBox.confirm(`确定删除供应商 ${row.supp_nm}？`, '确认删除', { type: 'warning' }) } catch { return }
  try {
    await deleteSupplier(row.supp_cd as string)
    ElMessage.success('删除成功')
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '删除失败')
  }
}

function openClassDialog(row?: any) {
  if (row) {
    classIsEdit.value = true
    classForm.class_cd = row.class_cd
    classForm.class_nm = row.class_nm
    classForm.parent = row.parent || ''
    classForm.classtyp = row.classtyp || ''
  } else {
    classIsEdit.value = false
    classForm.class_cd = ''; classForm.class_nm = ''; classForm.parent = ''; classForm.classtyp = ''
  }
  classDialogVisible.value = true
}

async function handleSaveClass() {
  if (!classForm.class_cd || !classForm.class_nm) { ElMessage.warning('编码和名称不能为空'); return }
  try {
    if (classIsEdit.value) {
      await updateSupplierClass(classForm.class_cd, classForm)
      ElMessage.success('修改成功')
    } else {
      await createSupplierClass(classForm)
      ElMessage.success('新增成功')
    }
    classDialogVisible.value = false
    await loadClasses()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
}

async function handleDeleteClass(row?: any) {
  const target = row || classForm
  try { await ElMessageBox.confirm(`确定删除分类 ${target.class_nm}？`, '确认', { type: 'warning' }) } catch { return }
  try {
    await deleteSupplierClass(target.class_cd)
    ElMessage.success('删除成功')
    if (row) { await loadClasses() } else { classDialogVisible.value = false; await loadClasses() }
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

onMounted(() => { loadClasses(); load(); loadAllItems() })
</script>

<style scoped>
.page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0; }
</style>
