<template>
  <div class="page">
    <div class="page-header">
      <h2>盘盈盘亏</h2>
      <el-button type="primary" size="small" @click="openCreate">新建</el-button>
    </div>

    <el-card shadow="never">
      <el-table
        :data="items"
        v-loading="loading"
        stripe
        size="small"
        highlight-current-row
        @row-click="open"
      >
        <el-table-column prop="olbillid" label="盘点单号" width="120" />
        <el-table-column label="仓库" width="80">
          <template #default="{ row }">{{ row.whnm || row.whcd }}</template>
        </el-table-column>
        <el-table-column label="盘点类型" width="80">
          <template #default="{ row }">{{ olLabel(row.oltyp) }}</template>
        </el-table-column>
        <el-table-column label="盈/亏" width="60">
          <template #default="{ row }">
            <el-tag
              :type="row.olsign === '+' ? 'success' : 'danger'"
              size="small"
              >{{ row.olsign === '+' ? '盈' : '亏' }}</el-tag
            >
          </template>
        </el-table-column>
        <el-table-column
          prop="olreason"
          label="原因"
          min-width="120"
          show-overflow-tooltip
        />
        <el-table-column label="审核" width="70">
          <template #default="{ row }">
            <el-tag
              :type="row.auditflg === '1' ? 'success' : 'warning'"
              size="small"
              >{{ afLabel(row.auditflg) }}</el-tag
            >
          </template>
        </el-table-column>
        <el-table-column prop="gendate" label="日期" width="100" />
        <el-table-column label="操作员" width="80">
          <template #default="{ row }">{{ userName(row.opercd) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.auditflg === '0'"
              link
              type="primary"
              size="small"
              @click.stop="openAudit(row)"
              >审核</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <AppPagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        style="margin-top: 12px; justify-content: flex-end"
      />
    </el-card>

    <!-- 新建弹窗 -->
    <el-dialog
      title="新建盘盈盘亏单"
      v-model="creating"
      width="700px"
      @closed="resetCreateForm"
    >
      <el-form label-width="80px" size="small">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="仓库" required>
              <el-select
                v-model="form.whcd"
                placeholder="请选择仓库"
                style="width: 100%"
                filterable
              >
                <el-option
                  v-for="w in whOptions"
                  :key="w.whcd"
                  :label="`${w.whcd} ${w.whnm}`"
                  :value="w.whcd"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="盘点类型">
              <el-select v-model="form.oltyp" style="width: 100%" clearable>
                <el-option
                  v-for="o in olOptions"
                  :key="o.code_cd"
                  :label="o.code_nm"
                  :value="o.code_cd"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="盈/亏" required>
          <el-radio-group v-model="form.olsign">
            <el-radio value="+">盘盈</el-radio>
            <el-radio value="-">盘亏</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="form.olreason" placeholder="盘点原因" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="form.memo"
            type="textarea"
            :rows="2"
            placeholder="备注"
          />
        </el-form-item>
      </el-form>

      <h4 style="margin: 8px 0 8px">物料明细</h4>
      <el-table :data="form.details" size="small" stripe>
        <el-table-column label="物料编码" min-width="120">
          <template #default="{ row }">
            <el-input v-model="row.itemcd" placeholder="物料编码" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="差异数量" width="120">
          <template #default="{ row }">
            <el-input
              v-model.number="row.olqty"
              placeholder="数量"
              size="small"
              type="number"
            />
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="120">
          <template #default="{ row }">
            <el-input v-model="row.memo" placeholder="备注" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="60">
          <template #default="{ $index }">
            <el-button
              link
              type="danger"
              size="small"
              @click="form.details.splice($index, 1)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <el-button
        type="primary"
        size="small"
        plain
        style="margin-top: 8px"
        @click="addDetailRow"
        >添加明细行</el-button
      >

      <template #footer>
        <el-button @click="creating = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleCreate"
          :loading="createLoading"
          :disabled="!form.whcd || !form.olsign"
          >提交</el-button
        >
      </template>
    </el-dialog>

    <!-- 审核弹窗 -->
    <el-dialog
      title="审核盘盈盘亏单"
      v-model="auditing"
      width="620px"
      @closed="auditTarget = null"
    >
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{
            auditTarget.olbillid
          }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{
            auditTarget.whnm || auditTarget.whcd
          }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{
            olLabel(auditTarget.oltyp)
          }}</el-descriptions-item>
          <el-descriptions-item label="盈/亏">{{
            auditTarget.olsign === '+' ? '盘盈' : '盘亏'
          }}</el-descriptions-item>
          <el-descriptions-item label="原因" :span="2">{{
            auditTarget.olreason || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{
            auditTarget.memo || '-'
          }}</el-descriptions-item>
        </el-descriptions>

        <template v-if="(auditTarget.details || []).length > 0">
          <h4 style="margin: 12px 0 8px">物料明细</h4>
          <el-table :data="auditTarget.details || []" size="small" stripe>
            <el-table-column prop="itemcd" label="物料" width="100" />
            <el-table-column prop="itemtyp" label="类型" width="60" />
            <el-table-column prop="olqty" label="差异数量" width="100" />
            <el-table-column prop="memo" label="备注" min-width="140" />
          </el-table>
        </template>
        <template v-if="(auditTarget.details_eid || []).length > 0">
          <h4 style="margin: 12px 0 8px">EID明细</h4>
          <el-table :data="auditTarget.details_eid || []" size="small" stripe>
            <el-table-column prop="eid" label="EID" width="140" />
            <el-table-column prop="itemcd" label="物料" width="100" />
            <el-table-column prop="olqty" label="差异数量" width="100" />
          </el-table>
        </template>
      </template>
      <template #footer>
        <el-button @click="auditing = false">取消</el-button>
        <el-button
          type="success"
          @click="handleAudit"
          :loading="auditLoading"
          >审核通过</el-button
        >
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer" title="盘点单详情" size="550px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{
            detail.olbillid
          }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{
            detail.whnm || detail.whcd
          }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{
            olLabel(detail.oltyp)
          }}</el-descriptions-item>
          <el-descriptions-item label="盈/亏">{{
            detail.olsign === '+' ? '盘盈' : '盘亏'
          }}</el-descriptions-item>
          <el-descriptions-item label="原因" :span="2">{{
            detail.olreason || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{
            detail.memo || '-'
          }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin: 16px 0 8px">物料明细</h4>
        <el-table :data="detail.details || []" size="small" stripe>
          <el-table-column prop="itemcd" label="物料" width="100" />
          <el-table-column prop="itemtyp" label="类型" width="60" />
          <el-table-column prop="olqty" label="差异数量" width="100" />
          <el-table-column prop="memo" label="备注" min-width="140" />
        </el-table>
        <h4 style="margin: 16px 0 8px">EID明细</h4>
        <el-table :data="detail.details_eid || []" size="small" stripe>
          <el-table-column prop="eid" label="EID" width="140" />
          <el-table-column prop="itemcd" label="物料" width="100" />
          <el-table-column prop="olqty" label="差异数量" width="100" />
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useDetailDrawer } from '@/composables/useDetailDrawer'
import { useUserNames } from '@/composables/useUserNames'
import { useDict } from '@/composables/useDict'
import { fetchSyscodes } from '@/api/master'
import {
    fetchOverLost,
    fetchOverLostDetail,
    fetchWarehouses,
    createOverLost,
    auditOverLost,
    type OverLostRecord,
} from '@/api/warehouse'

const { items, loading, page, perPage, total, load } =
    useListPage<OverLostRecord>(fetchOverLost)
const { drawer, detail, open } = useDetailDrawer<OverLostRecord>()
const { userName } = useUserNames()
const { dictLabel: afLabel } = useDict('AF')
const { dictLabel: olLabel } = useDict('OL')

// 仓库选项 + 盘点类型字典选项
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
const olOptions = ref<{ code_cd: string; code_nm: string }[]>([])

onMounted(async () => {
    try {
        const r = await fetchWarehouses()
        whOptions.value = r.data || []
    } catch {
        /* 忽略 */
    }
    try {
        const r = await fetchSyscodes('OL')
        olOptions.value = (r.data || []) as { code_cd: string; code_nm: string }[]
    } catch {
        /* 忽略 */
    }
})

// ---- 新建 ----
const creating = ref(false)
const createLoading = ref(false)

interface DetailRow {
    itemcd: string
    olqty: number
    memo: string
}

function emptyDetail(): DetailRow {
    return { itemcd: '', olqty: 0, memo: '' }
}

const form = reactive({
    whcd: '',
    oltyp: '',
    olsign: '' as string,
    olreason: '',
    memo: '',
    details: [emptyDetail()] as DetailRow[],
})

function addDetailRow() {
    form.details.push(emptyDetail())
}

function resetCreateForm() {
    form.whcd = ''
    form.oltyp = ''
    form.olsign = ''
    form.olreason = ''
    form.memo = ''
    form.details = [emptyDetail()]
}

function openCreate() {
    resetCreateForm()
    creating.value = true
}

async function handleCreate() {
    if (!form.whcd || !form.olsign) return
    createLoading.value = true
    try {
        const details = form.details
            .filter((d) => d.itemcd)
            .map((d) => ({
                whcd: form.whcd,
                itemcd: d.itemcd,
                olqty: d.olqty,
                memo: d.memo,
            }))
        await createOverLost({
            whcd: form.whcd,
            oltyp: form.oltyp || undefined,
            olsign: form.olsign,
            olreason: form.olreason || undefined,
            memo: form.memo || undefined,
            details,
        })
        ElMessage.success('创建成功')
        creating.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '创建失败')
    } finally {
        createLoading.value = false
    }
}

// ---- 审核 ----
const auditing = ref(false)
const auditTarget = ref<OverLostRecord | null>(null)
const auditLoading = ref(false)

async function openAudit(row: OverLostRecord) {
    auditTarget.value = row
    auditing.value = true
    try {
        const r = await fetchOverLostDetail(row.olbillid)
        auditTarget.value = r.data as any
    } catch {
        /* use row data */
    }
}

async function handleAudit() {
    if (!auditTarget.value) return
    auditLoading.value = true
    try {
        await auditOverLost(auditTarget.value.olbillid)
        ElMessage.success('审核通过')
        auditing.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '审核失败')
    } finally {
        auditLoading.value = false
    }
}
</script>

<style scoped>
.page {
    padding: 0;
}
.page-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
}
.page-header h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
}
</style>
