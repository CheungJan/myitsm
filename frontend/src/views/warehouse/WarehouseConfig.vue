<template>
    <div class="page">
        <el-card header="仓库配置">
            <el-form label-width="180px" style="max-width:600px" v-loading="loading">
                <el-divider content-position="left">不良品入库仓库</el-divider>
                <el-form-item label="报废仓 (BF)">
                    <el-select v-model="form.qc_scrap_warehouse" placeholder="请选择仓库" style="width:220px" filterable>
                        <el-option v-for="wh in warehouses" :key="wh.whcd" :label="`${wh.whnm} (${wh.whcd})`" :value="wh.whcd" />
                    </el-select>
                    <span class="tip">QC 判定为报废的不良品入库仓库</span>
                </el-form-item>
                <el-form-item label="返修仓 (BH)">
                    <el-select v-model="form.qc_repair_warehouse" placeholder="请选择仓库" style="width:220px" filterable>
                        <el-option v-for="wh in warehouses" :key="wh.whcd" :label="`${wh.whnm} (${wh.whcd})`" :value="wh.whcd" />
                    </el-select>
                    <span class="tip">QC 判定为返修的不良品入库仓库</span>
                </el-form-item>
                <el-form-item label="退换仓 (TH)">
                    <el-select v-model="form.qc_return_warehouse" placeholder="请选择仓库" style="width:220px" filterable>
                        <el-option v-for="wh in warehouses" :key="wh.whcd" :label="`${wh.whnm} (${wh.whcd})`" :value="wh.whcd" />
                    </el-select>
                    <span class="tip">QC 判定为退换的不良品入库仓库</span>
                </el-form-item>

                <el-divider content-position="left">入库类型默认仓库</el-divider>
                <el-form-item v-for="item in inTypes" :key="item.key" :label="`${item.label} (IV=${item.invtyp})`">
                    <el-select v-model="form[item.key]" placeholder="请选择仓库" style="width:220px" filterable clearable>
                        <el-option v-for="wh in warehouses" :key="wh.whcd" :label="`${wh.whnm} (${wh.whcd})`" :value="wh.whcd" />
                    </el-select>
                    <span class="tip">{{ item.tip }}</span>
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
                    <el-button @click="handleReset" :disabled="saving">重置</el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchSysparmByCd, updateSysparm } from '@/api/system'
import { fetchWarehouses, type WarehouseRecord } from '@/api/warehouse'

// 入库类型默认仓库配置项（IV=1~8）
const inTypes = [
    { invtyp: '1', key: 'stock_in_whcd_1', label: '采购入库', tip: '采购入库单默认仓库' },
    { invtyp: '2', key: 'stock_in_whcd_2', label: '销售退货', tip: '销售退货入库默认仓库' },
    { invtyp: '3', key: 'stock_in_whcd_3', label: '服务返还', tip: '日常维护单关单自动创建服务返还入库草稿的目标仓库' },
    { invtyp: '4', key: 'stock_in_whcd_4', label: '调拨入库', tip: '调拨入库默认仓库' },
    { invtyp: '5', key: 'stock_in_whcd_5', label: '借出归还', tip: '借出归还入库默认仓库' },
    { invtyp: '6', key: 'stock_in_whcd_6', label: '翻新入库', tip: '翻新入库默认仓库' },
    { invtyp: '7', key: 'stock_in_whcd_7', label: '回收入库', tip: '取机回收/门店关闭/翻新关单自动创建回收入库草稿的目标仓库' },
    { invtyp: '8', key: 'stock_in_whcd_8', label: '成品入库', tip: '成品入库默认仓库' },
]

const KEYS = [
    'qc_scrap_warehouse',
    'qc_repair_warehouse',
    'qc_return_warehouse',
    ...inTypes.map((i) => i.key),
] as const
const DEFAULTS: Record<string, string> = {
    qc_scrap_warehouse: 'L1',
    qc_repair_warehouse: 'LS',
    qc_return_warehouse: 'LS',
    stock_in_whcd_1: '',
    stock_in_whcd_2: '',
    stock_in_whcd_3: '',
    stock_in_whcd_4: '',
    stock_in_whcd_5: '',
    stock_in_whcd_6: '',
    stock_in_whcd_7: '',
    stock_in_whcd_8: '',
}

const form = reactive<Record<string, string>>({ ...DEFAULTS })
const saving = ref(false)
const loading = ref(true)
const warehouses = ref<WarehouseRecord[]>([])

onMounted(async () => {
    // 加载仓库列表
    try {
        const whRes = await fetchWarehouses()
        warehouses.value = (whRes.data || []) as WarehouseRecord[]
    } catch { /* ignore */ }

    // 加载已保存的配置
    for (const key of KEYS) {
        try {
            const res = await fetchSysparmByCd(key)
            const data = res.data as Record<string, unknown> | null
            form[key] = (data?.parm_val as string) || DEFAULTS[key]
        } catch { /* 未配置时后端返回 null，使用默认值 */ }
    }
    loading.value = false
})

async function handleSave() {
    saving.value = true
    try {
        for (const key of KEYS) {
            await updateSysparm(key, { parm_nm: key, parm_val: form[key] })
        }
        ElMessage.success('保存成功')
    } catch {
        ElMessage.error('保存失败')
    }
    finally { saving.value = false }
}

function handleReset() {
    for (const key of KEYS) {
        form[key] = DEFAULTS[key]
    }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
.tip { margin-left: 8px; color: #909399; font-size: 12px; }
</style>
