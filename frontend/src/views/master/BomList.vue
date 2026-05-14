<template>
    <div class="bom-page">
        <!-- 左侧：BOM 列表 -->
        <div class="list-panel">
            <el-card shadow="never">
                <template #header>
                    <div class="panel-header">
                        <span>BOM 列表（共 {{ total }} 条）</span>
                        <el-button type="primary" size="small" @click="openCreateBom">新增 BOM</el-button>
                    </div>
                </template>
                <el-input v-model="searchText" placeholder="搜索 BOM 代码或名称" clearable size="small" style="margin-bottom: 12px" @keyup.enter="onSearch" @clear="onSearch" />
                <el-table :data="boms" v-loading="loading" stripe highlight-current-row @row-click="onSelectBom">
                    <el-table-column prop="bomcd" label="BOM 代码" width="110" />
                    <el-table-column prop="bomnm" label="BOM 名称" min-width="140" show-overflow-tooltip />
                    <el-table-column label="BOM 类型" width="100" align="center">
                        <template #default="{ row }">
                            <el-tag :type="bomType(row).type" size="small">{{ bomType(row).label }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="状态" width="70" align="center">
                        <template #default="{ row }">
                            <el-tag :type="row.useflg === '0' ? 'danger' : 'success'" size="small">{{ row.useflg === '0' ? '无效' : '有效' }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="gendate" label="生成日期" width="100" />
                    <el-table-column label="操作" width="110" fixed="right">
                        <template #default="{ row }">
                            <el-button type="primary" link size="small" @click.stop="openEditBom(row)">编辑</el-button>
                            <el-button type="danger" link size="small" @click.stop="handleDeleteBom(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top: 16px; justify-content: flex-end" />
            </el-card>
        </div>

        <!-- 右侧：BOM 详情 -->
        <div class="detail-panel" v-if="selectedBom">
            <el-card shadow="never">
                <template #header>
                    <div class="panel-header">
                        <span>{{ selectedBom.bomcd }} - {{ selectedBom.bomnm }} 明细</span>
                        <el-button type="primary" size="small" @click="openAddDetail">添加物料</el-button>
                    </div>
                </template>
                <el-table :data="details" v-loading="detailLoading" stripe size="small">
                    <el-table-column prop="itemcd" label="物料代码" width="110" />
                    <el-table-column prop="item_nm" label="物料名称" min-width="150" show-overflow-tooltip />
                    <el-table-column prop="bomqty" label="数量" width="70" align="center" />
                    <el-table-column label="物料类型" width="90" align="center">
                        <template #default="{ row }">
                            <el-tag :type="row.itemtyp === '1' ? 'warning' : 'info'" size="small">{{ row.itemtyp === '1' ? '核心配件' : '外设配件' }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="70" align="center">
                        <template #default="{ row }">
                            <el-button type="danger" link size="small" @click="handleDeleteDetail(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-card>
        </div>
        <div class="detail-panel" v-else>
            <el-card shadow="never">
                <template #header><span>BOM 明细</span></template>
                <div class="empty-hint">请从左侧列表选择一个 BOM 查看明细</div>
            </el-card>
        </div>

        <!-- 新增/编辑 BOM 对话框 -->
        <el-dialog :title="bomDialogTitle" v-model="bomDialogVisible" width="420px">
            <el-form :model="bomForm" label-width="80px">
                <el-form-item label="BOM 代码">
                    <el-input v-model="bomForm.bomcd" maxlength="6" placeholder="6位大写字母/数字" :disabled="isEditingBom" style="text-transform: uppercase" />
                </el-form-item>
                <el-form-item label="BOM 名称">
                    <el-input v-model="bomForm.bomnm" placeholder="请输入 BOM 名称" />
                </el-form-item>
                <el-form-item label="状态" v-if="isEditingBom">
                    <el-select v-model="bomForm.useflg" style="width: 100%">
                        <el-option label="有效" value="1" />
                        <el-option label="无效" value="0" />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="bomDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSaveBom" :loading="saving">确定</el-button>
            </template>
        </el-dialog>

        <!-- 添加物料对话框 -->
        <el-dialog title="添加物料" v-model="addDetailVisible" width="420px">
            <el-form :model="detailForm" label-width="80px">
                <el-form-item label="选择物料">
                    <el-select v-model="detailForm.itemcd" filterable placeholder="搜索物料代码或名称" style="width: 100%" :filter-method="filterItems" @visible-change="onItemSelectOpen">
                        <el-option v-for="it in filteredItems" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="数量">
                    <el-input-number v-model="detailForm.bomqty" :min="1" :max="9999" style="width: 100%" />
                </el-form-item>
                <el-form-item label="物料类型">
                    <el-select v-model="detailForm.itemtyp" style="width: 100%">
                        <el-option label="外设配件" value="0" />
                        <el-option label="核心配件" value="1" />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="addDetailVisible = false">取消</el-button>
                <el-button type="primary" @click="handleAddDetail" :loading="addingDetail">确定</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, computed } from 'vue'
import AppPagination from '@/components/common/AppPagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
    fetchBoms, fetchBom, createBom, updateBom, deleteBom,
    addBomDetail, deleteBomDetail,
    fetchItems,
} from '@/api/master'
import type { BomRecord, BomDetailRecord, ItemRecord } from '@/api/master'

// 列表数据
const boms = ref<BomRecord[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const perPage = ref(20)
const searchText = ref('')

// 当前选中的 BOM
const selectedBom = ref<BomRecord | null>(null)
const details = ref<BomDetailRecord[]>([])
const detailLoading = ref(false)

// BOM 对话框
const bomDialogVisible = ref(false)
const isEditingBom = ref(false)
const saving = ref(false)
const bomForm = reactive({ bomcd: '', bomnm: '', useflg: '1' })

// 添加物料对话框
const addDetailVisible = ref(false)
const addingDetail = ref(false)
const detailForm = reactive({ itemcd: '', bomqty: 1, itemtyp: '0' })
const allItems = ref<ItemRecord[]>([])
const filteredItems = ref<ItemRecord[]>([])

// 计算属性：BOM 类型
function bomType(row: BomRecord): { type: string; label: string } {
    if (!row.details || row.details.length === 0) {
        return { type: 'info', label: '主机+配件' }
    }
    const hasCore = row.details.some((d) => d.itemtyp === '1')
    return hasCore
        ? { type: 'warning', label: '全配件' }
        : { type: 'info', label: '主机+配件' }
}

const bomDialogTitle = computed(() => isEditingBom.value ? '编辑 BOM' : '新增 BOM')

// Watch 分页变化
watch(page, () => loadBoms())
watch(perPage, () => { page.value = 1; loadBoms() })

onMounted(() => { loadBoms() })

// 加载 BOM 列表
async function loadBoms() {
    loading.value = true
    try {
        const res = await fetchBoms({
            page: page.value,
            per_page: perPage.value,
            search: searchText.value || undefined,
        })
        boms.value = res.data.items || []
        total.value = res.data.total || 0
    } catch {
        ElMessage.error('加载 BOM 列表失败')
    } finally {
        loading.value = false
    }
}

function onSearch() {
    page.value = 1
    loadBoms()
}

// 选中 BOM，加载明细
async function onSelectBom(row: BomRecord) {
    selectedBom.value = row
    detailLoading.value = true
    try {
        const res = await fetchBom(row.bomcd)
        details.value = res.data.details || []
    } catch {
        ElMessage.error('加载 BOM 明细失败')
    } finally {
        detailLoading.value = false
    }
}

// 新增 BOM
function openCreateBom() {
    bomForm.bomcd = ''
    bomForm.bomnm = ''
    bomForm.useflg = '1'
    isEditingBom.value = false
    bomDialogVisible.value = true
}

// 编辑 BOM
function openEditBom(row: BomRecord) {
    bomForm.bomcd = row.bomcd
    bomForm.bomnm = row.bomnm
    bomForm.useflg = row.useflg
    isEditingBom.value = true
    bomDialogVisible.value = true
}

// 保存 BOM
async function handleSaveBom() {
    if (!bomForm.bomcd.trim() || !bomForm.bomnm.trim()) {
        ElMessage.warning('请填写 BOM 代码和名称')
        return
    }
    saving.value = true
    try {
        if (isEditingBom.value) {
            await updateBom(bomForm.bomcd, { bomnm: bomForm.bomnm, useflg: bomForm.useflg })
            ElMessage.success('更新成功')
        } else {
            await createBom({ bomcd: bomForm.bomcd.toUpperCase(), bomnm: bomForm.bomnm })
            ElMessage.success('创建成功')
        }
        bomDialogVisible.value = false
        loadBoms()
        // 如果当前选中的 BOM 被编辑，刷新明细
        if (selectedBom.value?.bomcd === bomForm.bomcd) {
            await onSelectBom(selectedBom.value)
        }
    } catch {
        ElMessage.error('保存失败')
    } finally {
        saving.value = false
    }
}

// 删除 BOM
async function handleDeleteBom(row: BomRecord) {
    try {
        await ElMessageBox.confirm(`确认删除 BOM "${row.bomcd} - ${row.bomnm}" 吗？`, '删除确认', {
            type: 'warning',
            confirmButtonText: '删除',
            cancelButtonText: '取消',
        })
    } catch {
        return
    }
    try {
        await deleteBom(row.bomcd)
        ElMessage.success('删除成功')
        if (selectedBom.value?.bomcd === row.bomcd) {
            selectedBom.value = null
            details.value = []
        }
        loadBoms()
    } catch {
        ElMessage.error('删除失败')
    }
}

// 打开添加物料对话框
async function openAddDetail() {
    if (!selectedBom.value) return
    detailForm.itemcd = ''
    detailForm.bomqty = 1
    detailForm.itemtyp = '0'
    // 加载所有物料用于搜索
    if (allItems.value.length === 0) {
        try {
            const res = await fetchItems({ per_page: 9999 })
            allItems.value = res.data.items || []
            filteredItems.value = [...allItems.value]
        } catch {
            ElMessage.error('加载物料列表失败')
            return
        }
    } else {
        filteredItems.value = [...allItems.value]
    }
    addDetailVisible.value = true
}

// 物料远程搜索过滤
function filterItems(query: string) {
    if (!query) {
        filteredItems.value = [...allItems.value]
    } else {
        const lower = query.toLowerCase()
        filteredItems.value = allItems.value.filter(
            (it) => it.item_cd.toLowerCase().includes(lower) || it.item_nm.toLowerCase().includes(lower)
        )
    }
}

function onItemSelectOpen(visible: boolean) {
    if (visible) {
        filteredItems.value = [...allItems.value]
    }
}

// 添加物料明细
async function handleAddDetail() {
    if (!selectedBom.value) return
    if (!detailForm.itemcd) {
        ElMessage.warning('请选择物料')
        return
    }
    addingDetail.value = true
    try {
        await addBomDetail(selectedBom.value.bomcd, {
            itemcd: detailForm.itemcd,
            bomqty: detailForm.bomqty,
            itemtyp: detailForm.itemtyp,
        })
        ElMessage.success('添加成功')
        addDetailVisible.value = false
        // 刷新明细
        await onSelectBom(selectedBom.value)
    } catch {
        ElMessage.error('添加失败')
    } finally {
        addingDetail.value = false
    }
}

// 删除物料明细
async function handleDeleteDetail(row: BomDetailRecord) {
    if (!selectedBom.value) return
    try {
        await ElMessageBox.confirm(`确认从 BOM 中移除物料 "${row.itemcd}" 吗？`, '删除确认', {
            type: 'warning',
            confirmButtonText: '删除',
            cancelButtonText: '取消',
        })
    } catch {
        return
    }
    try {
        await deleteBomDetail(selectedBom.value.bomcd, row.itemcd)
        ElMessage.success('删除成功')
        await onSelectBom(selectedBom.value)
    } catch {
        ElMessage.error('删除失败')
    }
}
</script>

<style lang="scss" scoped>
.bom-page {
    display: flex;
    gap: 12px;
    padding: 16px;
    height: calc(100vh - 80px);
}

.list-panel {
    width: 520px;
    flex-shrink: 0;
    overflow-y: auto;
}

.detail-panel {
    flex: 1;
    overflow-y: auto;
    min-width: 0;
}

.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
    font-weight: 500;
}

.empty-hint {
    color: #909399;
    text-align: center;
    padding: 48px 0;
    font-size: 14px;
}
</style>
