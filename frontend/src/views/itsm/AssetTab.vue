<template>
  <div v-loading="loading">
    <el-alert
      v-if="chargeInfo && chargeInfo.should_charge"
      :title="`检测到 ${chargeInfo.count} 台客户资产，建议收费`"
      type="warning"
      :closable="false"
      size="small"
      style="margin-bottom:12px"
    />
    <el-alert
      v-else-if="chargeInfo"
      title="无客户资产或均在保修期内，当前不建议收费"
      type="info"
      :closable="false"
      size="small"
      style="margin-bottom:12px"
    />
    <el-table :data="assetList" size="small" empty-text="暂无资产" max-height="300">
      <el-table-column prop="eid" label="EID" width="140" show-overflow-tooltip/>
      <el-table-column prop="itemcd" label="型号" width="100"/>
      <el-table-column prop="item_nm" label="物料名称" min-width="120" show-overflow-tooltip/>
      <el-table-column label="资产归属" width="90"><template #default="{row}">{{ assetOwnerLabel(row.asset_owner as string) }}</template></el-table-column>
      <el-table-column label="设备状态" width="90"><template #default="{row}">{{ sflgLabel(row.sflg as string) }}</template></el-table-column>
      <el-table-column prop="posupddate" label="安装日期" width="120"/>
      <el-table-column prop="maintenanceno" label="来源单据" width="120" show-overflow-tooltip/>
      <el-table-column prop="recycle_status" label="回收状态" width="80"/>
      <el-table-column label="可回收" width="70"><template #default="{row}">{{ row.recyclable === 'Y' ? '是' : '否' }}</template></el-table-column>
    </el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { fetchCustomerAssets } from '@/api/master'
import { shouldCharge } from '@/api/itsm'

const props = defineProps<{ storeId: string }>()
const loading = ref(false)
const assetList = ref<Record<string, unknown>[]>([])
const chargeInfo = ref<{ should_charge: boolean; count: number } | null>(null)

function assetOwnerLabel(v: string) {
  const m: Record<string, string> = { '01': '客户', '02': '公司' }
  return m[v] || v || '-'
}
function sflgLabel(v: string) {
  const m: Record<string, string> = { 'S': '已销售', '1': '在门店', '3': '待检', '0': '在库', '8': '在库', '2': '已报废' }
  return m[v] || v || '-'
}

async function load() {
  if (!props.storeId) {
    assetList.value = []
    chargeInfo.value = null
    return
  }
  loading.value = true
  try {
    const [assetRes, chargeRes] = await Promise.all([
      fetchCustomerAssets(props.storeId, { per_page: '999' }),
      shouldCharge(props.storeId),
    ])
    assetList.value = ((assetRes as any)?.data?.items || []) as Record<string, unknown>[]
    chargeInfo.value = ((chargeRes as any)?.data || {}) as { should_charge: boolean; count: number }
  } catch {
    assetList.value = []
    chargeInfo.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.storeId, load, { immediate: true })
</script>
