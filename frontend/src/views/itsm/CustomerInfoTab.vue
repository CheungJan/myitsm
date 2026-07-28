<template>
  <div v-loading="loading">
    <el-descriptions :column="2" border size="small" class="customer-info">
      <el-descriptions-item label="门店名称" :span="2">{{ customer?.cust_nm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="客户编码">{{ customer?.cust_cd || '-' }}</el-descriptions-item>
      <el-descriptions-item label="磁卡号">{{ customer?.cust_card || '-' }}</el-descriptions-item>
      <el-descriptions-item label="管理单位（上级机构）">{{ customer?.parentcd_nm || customer?.parentcd || '-' }}</el-descriptions-item>
      <el-descriptions-item label="客户分类">{{ customer?.class_cd_nm || customer?.class_cd || '-' }}</el-descriptions-item>
      <el-descriptions-item label="业务类型">{{ customer?.busi_typ_nm || customer?.busi_typ || '-' }}</el-descriptions-item>
      <el-descriptions-item label="门店状态">{{ customer?.s_status_nm || customer?.s_status || '-' }}</el-descriptions-item>
      <el-descriptions-item label="联系人">{{ customer?.contactor || '-' }}</el-descriptions-item>
      <el-descriptions-item label="电话">{{ customer?.phone_no || '-' }}</el-descriptions-item>
      <el-descriptions-item label="传真">{{ customer?.faxno || '-' }}</el-descriptions-item>
      <el-descriptions-item label="邮编">{{ customer?.zipcd || '-' }}</el-descriptions-item>
      <el-descriptions-item label="省">{{ customer?.geo_prvn_nm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="市">{{ customer?.geo_city_nm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="区县">{{ customer?.geo_area_nm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="街道">{{ customer?.geo_street_nm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="地址" :span="2">{{ customer?.address || '-' }}</el-descriptions-item>
      <el-descriptions-item label="划区">{{ customer?.area_nm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="环线位置">{{ customer?.location_nm || customer?.location || '-' }}</el-descriptions-item>
      <el-descriptions-item label="最新机型" :span="2">{{ customer?.latest_item_nm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="POS 数量">{{ customer?.pos_n || '0' }}</el-descriptions-item>
      <el-descriptions-item label="品牌">{{ customer?.ppt_code_nm || customer?.ppt_code || '-' }}</el-descriptions-item>
      <el-descriptions-item label="理论定货">{{ customer?.custrnm || '-' }}</el-descriptions-item>
      <el-descriptions-item label="要货方式">{{ customer?.ordertype || '-' }}</el-descriptions-item>
      <el-descriptions-item label="客户等级" :span="2">{{ customer?.levels || '-' }}</el-descriptions-item>
      <el-descriptions-item label="通讯方式">{{ customer?.comm_mode_nm || customer?.comm_mode || '-' }}</el-descriptions-item>
      <el-descriptions-item label="支付方式">{{ customer?.zf_type_nm || customer?.zf_type || '-' }}</el-descriptions-item>
      <el-descriptions-item label="合同标志">{{ customer?.is_contract === 'Y' ? '是' : (customer?.is_contract === '1' ? '是' : '否') }}</el-descriptions-item>
      <el-descriptions-item label="操作系统">{{ customer?.opersystem || '-' }}</el-descriptions-item>
      <el-descriptions-item label="软件版本">{{ customer?.soft_edition || '-' }}</el-descriptions-item>
      <el-descriptions-item label="数据库版本">{{ customer?.data_base || '-' }}</el-descriptions-item>
      <el-descriptions-item label="内核版本">{{ customer?.systemcode || '-' }}</el-descriptions-item>
      <el-descriptions-item label="3G卡号">{{ customer?.card3g || '-' }}</el-descriptions-item>
      <el-descriptions-item label="首次开通">{{ customer?.opendate || '-' }}</el-descriptions-item>
      <el-descriptions-item label="最近更换">{{ customer?.replacedate || '-' }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">{{ customer?.backup || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left">历史同业务单据</el-divider>
    <el-table :data="historyList" size="small" empty-text="暂无" highlight-current-row @row-click="onRowClick">
      <el-table-column label="单号" width="120">
        <template #default="{row}">{{ rowId(row) }}</template>
      </el-table-column>
      <template v-if="props.businessType === 'daily'">
        <el-table-column label="故障类型" width="80">
          <template #default="{row}">{{ row.fault_type_nm || row.fault_type || '-' }}</template>
        </el-table-column>
        <el-table-column prop="request_time" label="请求时间" width="140" />
        <el-table-column prop="expected_completion_time" label="要求完成时间" width="160" />
        <el-table-column prop="short_description" label="故障简述" min-width="120" show-overflow-tooltip />
        <el-table-column prop="detail_description" label="详细描述" min-width="160" show-overflow-tooltip />
        <el-table-column label="当前状态" width="80">
          <template #default="{row}">
            <el-tag size="small" :type="statusTag(row.current_status as string)">{{ row.current_status_nm || statusLabel(row.current_status as string) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="是否补单" width="70">
          <template #default="{row}">{{ row.is_old === 'Y' ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="140" />
        <el-table-column label="创建人" width="80">
          <template #default="{row}">{{ row.creator_nm || row.creator || '-' }}</template>
        </el-table-column>
        <el-table-column prop="update_time" label="更新时间" width="140" />
        <el-table-column label="更新人" width="80">
          <template #default="{row}">{{ row.updator_nm || row.updator || '-' }}</template>
        </el-table-column>
        <el-table-column label="首次上门工程师" width="110">
          <template #default="{row}">{{ row.firstor_nm || row.firstor || '-' }}</template>
        </el-table-column>
        <el-table-column prop="first_time" label="首次上门时间" width="140" />
        <el-table-column prop="close_time" label="关单时间" width="140" />
        <el-table-column prop="revisit_time" label="回访时间" width="140" />
      </template>
      <template v-else>
        <el-table-column label="状态" width="80">
          <template #default="{row}">
            <el-tag size="small" :type="statusTag(row.current_status as string)">{{ statusLabel(row.current_status as string) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="140" />
        <el-table-column prop="close_time" label="关单时间" width="140" />
        <el-table-column prop="short_description" label="简述" min-width="120" show-overflow-tooltip />
      </template>
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

// 根据业务类型提取单号字段
function rowId(row: Record<string, unknown>): string {
  const m: Record<string, string> = {
    open: 'new_opening_id',
    renovate: 'renew_id',
    'device-change': 'device_change_id',
    'store-close': 'store_close_id',
    recycle: 'recycle_id',
    daily: 'maintenance_id',
    maintenance: 'daily_maintenance_id',
  }
  const k = m[props.businessType] || 'maintenance_id'
  return (row[k] as string) || '-'
}

watch(() => [props.storeId, props.businessType], load, { immediate: true })
</script>

<style scoped>
.customer-info :deep(.el-descriptions__label) { width: 100px; }
</style>
