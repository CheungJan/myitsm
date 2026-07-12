<template>
  <div v-loading="loading">
    <el-descriptions :column="2" border size="small" class="customer-info">
      <el-descriptions-item label="门店名称" :span="2">{{ customer?.cust_nm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="客户编码">{{ customer?.cust_cd || '-' }}</el-descriptions-item>
      <el-descriptions-item label="磁卡号">{{ customer?.cust_card || '-' }}</el-descriptions-item>
      <el-descriptions-item label="联系人">{{ customer?.contactor || '-' }}</el-descriptions-item>
      <el-descriptions-item label="电话">{{ customer?.phone_no || '-' }}</el-descriptions-item>
      <el-descriptions-item label="地址" :span="2">{{ customer?.address || '-' }}</el-descriptions-item>
      <el-descriptions-item label="通讯方式">{{ customer?.comm_mode_nm || customer?.comm_mode || '-' }}</el-descriptions-item>
      <el-descriptions-item label="支付方式">{{ customer?.zf_type_nm || customer?.zf_type || '-' }}</el-descriptions-item>
      <el-descriptions-item label="合同标志">{{ customer?.is_contract === 'Y' ? '是' : (customer?.is_contract === '1' ? '是' : '否') }}</el-descriptions-item>
      <el-descriptions-item label="软件版本">{{ customer?.soft_edition || '-' }}</el-descriptions-item>
      <el-descriptions-item label="操作系统">{{ customer?.opersystem || '-' }}</el-descriptions-item>
      <el-descriptions-item label="数据库版本">{{ customer?.data_base || '-' }}</el-descriptions-item>
      <el-descriptions-item label="门店状态">{{ customer?.s_status_nm || customer?.s_status || '-' }}</el-descriptions-item>
      <el-descriptions-item label="客户等级">{{ customer?.levels || '-' }}</el-descriptions-item>
      <el-descriptions-item label="POS 数量">{{ customer?.pos_n || '0' }}</el-descriptions-item>
      <el-descriptions-item label="首次开通" :span="2">{{ customer?.opendate || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left">历史同业务单据</el-divider>
    <el-table :data="historyList" size="small" empty-text="暂无" highlight-current-row @row-click="onRowClick">
      <el-table-column prop="new_opening_id" label="单号" width="120" />
      <el-table-column prop="renew_id" label="单号" width="120" />
      <el-table-column prop="device_change_id" label="单号" width="120" />
      <el-table-column prop="store_close_id" label="单号" width="120" />
      <el-table-column prop="recycle_id" label="单号" width="120" />
      <el-table-column prop="maintenance_id" label="单号" width="120" />
      <el-table-column prop="daily_maintenance_id" label="单号" width="120" />
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-tag size="small" :type="statusTag(row.current_status as string)">{{ statusLabel(row.current_status as string) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="140" />
      <el-table-column prop="close_time" label="关单时间" width="140" />
      <el-table-column prop="short_description" label="简述" min-width="120" show-overflow-tooltip />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchCustomerDetail } from '@/api/master'
import { fetchHistoryByStore } from '@/api/itsm'

interface Props {
  storeId: string
  businessType: string
  currentRecordId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'select', record: Record<string, unknown>): void }>()

const loading = ref(false)
const customer = ref<Record<string, unknown> | null>(null)
const historyList = ref<Record<string, unknown>[]>([])

function statusTag(s: string) {
  const m: Record<string, string> = { '1': 'info', '2': 'primary', '3': 'success', '4': 'warning', '5': 'primary', '9': 'danger' }
  return m[s] || 'info'
}
function statusLabel(s: string) {
  const m: Record<string, string> = { '1': '新建', '2': '分配', '3': '关闭', '4': '未解决', '5': '已解决', '9': '作废' }
  return m[s] || s
}

async function load() {
  if (!props.storeId) return
  loading.value = true
  try {
    const [custRes, histRes] = await Promise.all([
      fetchCustomerDetail(props.storeId),
      fetchHistoryByStore(props.businessType, props.storeId),
    ])
    customer.value = (custRes as any).data || null
    historyList.value = ((histRes as any).data?.items || []) as Record<string, unknown>[]
  } catch (err) {
    ElMessage.error('加载客户信息失败')
  } finally {
    loading.value = false
  }
}

function onRowClick(row: Record<string, unknown>) {
  emit('select', row)
}

watch(() => [props.storeId, props.businessType], load, { immediate: true })
</script>

<style scoped>
.customer-info :deep(.el-descriptions__label) { width: 100px; }
</style>
