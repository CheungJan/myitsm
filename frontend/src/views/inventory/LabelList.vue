<template>
  <div class="page">
    <div class="page-header">
      <h2>标签管理</h2>
      <div style="display:flex;gap:8px">
        <el-button size="small" @click="openBulk">批量录入</el-button>
        <el-button type="primary" size="small" @click="openActivateBatch">批量激活</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>标签号</label>
          <el-input v-model="s.labelid" placeholder="标签号" size="small" style="width:160px" clearable @keyup.enter="doSearch"/>
        </div>
        <div class="field"><label>中类编码</label>
          <el-input v-model="s.classcd" placeholder="中类编码" size="small" style="width:120px" clearable @keyup.enter="doSearch"/>
        </div>
        <div class="field"><label>状态</label>
          <el-select v-model="s.useflg" size="small" style="width:110px" clearable>
            <el-option label="未激活" value="1"/>
            <el-option label="已激活" value="0"/>
          </el-select>
        </div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small">
        <el-table-column prop="labelid" label="标签号" width="160"/>
        <el-table-column prop="classcd" label="中类编码" width="100"/>
        <el-table-column label="操作员" width="80">
          <template #default="{row}">{{ userName(row.opercd) }}</template>
        </el-table-column>
        <el-table-column label="录入日期" width="120">
          <template #default="{row}">{{ (row.gendate||'').substring(0,10) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{row}">
            <el-tag :type="row.useflg==='1'?'success':'info'" size="small">{{ row.useflg==='1'?'未激活':'已激活' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{row}">
            <el-button v-if="row.useflg==='1'" link type="primary" size="small" @click="openActivateSingle(row)">激活</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <!-- 批量录入弹窗 -->
    <el-dialog v-model="bulkVisible" title="批量录入 / 生成标签" width="520px" @closed="bulkText='';genForm.classcd=''">
      <el-tabs v-model="bulkTab">
        <el-tab-pane label="手动录入" name="manual">
          <div style="margin-bottom:8px;color:#606266;font-size:13px">
            每行一条，格式：<code>标签号,中类编码</code>（例：<code>0000000000001,MM0001</code>）
          </div>
          <el-input v-model="bulkText" type="textarea" :rows="10" placeholder="0000000000001,MM0001"/>
        </el-tab-pane>
        <el-tab-pane label="自动生成（PB规则）" name="generate">
          <el-form :model="genForm" label-width="80px" size="small">
            <el-form-item label="中类编码" required>
              <el-input v-model="genForm.classcd" placeholder="6位中类编码，如 MM0001" maxlength="6"/>
            </el-form-item>
            <el-form-item label="类型">
              <el-radio-group v-model="genForm.typflg">
                <el-radio value="0">配件（classcd+YY+月+序号）</el-radio>
                <el-radio value="1">成品（日期+标识+序号）</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="genForm.typflg==='1'" label="标识">
              <el-input v-model="genForm.sign" placeholder="1位标识字符" maxlength="1" style="width:80px"/>
            </el-form-item>
            <el-form-item label="日期">
              <el-date-picker v-model="genForm.date" type="date" value-format="YYYY-MM-DD" style="width:200px" placeholder="默认今天"/>
            </el-form-item>
            <el-form-item label="生成数量">
              <el-input-number v-model="genForm.count" :min="1" :max="10000" style="width:120px"/>
            </el-form-item>
            <el-form-item>
              <span v-if="genResult" style="color:#67c23a;font-size:13px">
                前缀：<code>{{ genResult.prefix }}</code>，序号 {{ genResult.start_seq }}-{{ genResult.start_seq + (genResult.inserted||0) - 1 }}，已写入 {{ genResult.inserted }} 条
              </span>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="bulkVisible=false">取消</el-button>
        <el-button v-if="bulkTab==='manual'" type="primary" @click="doBulk" :loading="bulkSaving">录入</el-button>
        <el-button v-else type="primary" @click="doGenerate" :loading="genSaving">生成</el-button>
      </template>
    </el-dialog>

    <!-- 激活弹窗（单条 / 批量） -->
    <el-dialog v-model="activateVisible" :title="activateSingle?'激活标签':'批量激活标签'" width="560px" @closed="resetActivate">
      <el-form :model="activateForm" label-width="90px" size="small">
        <template v-if="activateSingle">
          <el-form-item label="标签号"><el-input :value="activateForm.labelid" disabled/></el-form-item>
          <el-form-item label="中类编码"><el-input :value="activateForm.classcd" disabled/></el-form-item>
          <el-form-item label="物料编码" required>
            <el-select v-model="activateForm.itemcd" filterable remote reserve-keyword :remote-method="searchItems" :loading="itemSearching" style="width:100%" placeholder="搜索物料编码">
              <el-option v-for="it in itemOptions" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd"/>
            </el-select>
          </el-form-item>
          <el-form-item label="仓库">
            <el-select v-model="activateForm.whcd" filterable clearable style="width:100%" placeholder="可选，激活后入驻仓库">
              <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
            </el-select>
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="标签列表">
            <el-input v-model="activateBatchText" type="textarea" :rows="6" placeholder="标签号,中类编码,物料编码（每行一条）"/>
            <div style="color:#909399;font-size:12px;margin-top:4px">格式：标签号,中类编码,物料编码</div>
          </el-form-item>
        </template>
        <el-form-item label="质检标志" required>
          <el-radio-group v-model="activateForm.qcflg">
            <el-radio value="GA">GA 合格（成品直接入库）</el-radio>
            <el-radio value="DJ">DJ 待检（配件，需质检）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="生产日期">
          <el-date-picker v-model="activateForm.prddate" type="date" style="width:100%" value-format="YYYY-MM-DD" placeholder="可选"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="activateVisible=false">取消</el-button>
        <el-button type="primary" @click="doActivate" :loading="activateSaving">激活</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useUserNames } from '@/composables/useUserNames'
import { fetchItems, type ItemRecord } from '@/api/master'
import request from '@/api/request'

const { userName } = useUserNames()

interface LabelRecord { labelid: string; classcd: string; opercd: string; gendate: string; useflg: string }

const s = reactive({ labelid: '', classcd: '', useflg: '' })

function buildParams(p?: Record<string, string>) {
    const base: Record<string, string> = { ...(p || {}) }
    if (s.labelid) base.labelid = s.labelid
    if (s.classcd) base.classcd = s.classcd
    if (s.useflg !== '') base.useflg = s.useflg
    return base
}

const { items, loading, page, perPage, total, load } = useListPage<LabelRecord>(
    (p?: Record<string, string>) => request.get('/inventory/labels', { params: buildParams(p) })
)

function doSearch() { page.value = 1; load() }

// ---- 仓库选项 ----
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
async function loadWh() {
    if (whOptions.value.length) return
    try { const r = await request.get('/warehouses'); whOptions.value = (r as any).data || [] } catch { /* ignore */ }
}

// ---- 批量录入 ----
const bulkVisible = ref(false)
const bulkText = ref('')
const bulkSaving = ref(false)

function openBulk() { bulkVisible.value = true }

async function doBulk() {
    const rows = bulkText.value.trim().split('\n').filter(l => l.trim()).map(l => {
        const parts = l.split(',').map(p => p.trim())
        return { labelid: parts[0] || '', classcd: parts[1] || '' }
    }).filter(r => r.labelid && r.classcd)
    if (!rows.length) { ElMessage.warning('无有效行（格式：标签号,中类编码）'); return }
    bulkSaving.value = true
    try {
        const r = await request.post('/inventory/labels/bulk', { rows })
        ElMessage.success(`录入 ${(r as any).data?.inserted ?? 0}/${rows.length} 条`)
        bulkVisible.value = false; load()
    } catch (e: any) { ElMessage.error(e?.response?.data?.message || '录入失败') }
    finally { bulkSaving.value = false }
}

// ---- 批量生成 ----
const bulkTab = ref('manual')
const genForm = reactive({ classcd: '', typflg: '1', sign: 'L', date: '', count: 10 })
const genSaving = ref(false)
const genResult = ref<{ prefix: string; start_seq: number; inserted: number } | null>(null)

async function doGenerate() {
    if (!genForm.classcd || genForm.classcd.length !== 6) { ElMessage.warning('请输入6位中类编码'); return }
    if (genForm.typflg === '1' && !genForm.sign) { ElMessage.warning('成品类型需填写标识'); return }
    genSaving.value = true
    try {
        const r = await request.post('/inventory/labels/generate', { ...genForm })
        genResult.value = (r as any).data || null
        ElMessage.success(`生成 ${genResult.value?.inserted ?? 0}/${genForm.count} 条标签`)
        load()
    } catch (e: any) { ElMessage.error(e?.response?.data?.message || '生成失败') }
    finally { genSaving.value = false }
}

// ---- 激活 ----
const activateVisible = ref(false)
const activateSingle = ref(true)
const activateSaving = ref(false)
const activateBatchText = ref('')
const activateForm = reactive({ labelid: '', classcd: '', itemcd: '', whcd: '', qcflg: 'GA', prddate: '' })
const itemOptions = ref<ItemRecord[]>([])
const itemSearching = ref(false)

function openActivateSingle(row: LabelRecord) {
    activateSingle.value = true
    Object.assign(activateForm, { labelid: row.labelid, classcd: row.classcd, itemcd: '', whcd: '', qcflg: 'GA', prddate: '' })
    activateVisible.value = true; loadWh()
}

function openActivateBatch() {
    activateSingle.value = false
    activateBatchText.value = ''
    Object.assign(activateForm, { labelid: '', classcd: '', itemcd: '', whcd: '', qcflg: 'GA', prddate: '' })
    activateVisible.value = true
}

function resetActivate() { activateBatchText.value = ''; Object.assign(activateForm, { labelid: '', classcd: '', itemcd: '', whcd: '', qcflg: 'GA', prddate: '' }) }

async function searchItems(query: string) {
    if (!query) { itemOptions.value = []; return }
    itemSearching.value = true
    try { const r = await fetchItems({ search: query, per_page: 20 }); itemOptions.value = r.data?.items || [] }
    catch { /* ignore */ } finally { itemSearching.value = false }
}

async function doActivate() {
    activateSaving.value = true
    try {
        if (activateSingle.value) {
            if (!activateForm.itemcd) { ElMessage.warning('请选择物料编码'); return }
            await request.post('/inventory/labels/activate', {
                labelid: activateForm.labelid, classcd: activateForm.classcd,
                itemcd: activateForm.itemcd, whcd: activateForm.whcd || undefined,
                qcflg: activateForm.qcflg, prddate: activateForm.prddate || undefined,
            })
            ElMessage.success('激活成功')
        } else {
            const labels = activateBatchText.value.trim().split('\n').filter(l => l.trim()).map(l => {
                const p = l.split(',').map(x => x.trim())
                return { labelid: p[0] || '', classcd: p[1] || '', itemcd: p[2] || '', qcflg: activateForm.qcflg, prddate: activateForm.prddate || undefined }
            }).filter(r => r.labelid && r.classcd && r.itemcd)
            if (!labels.length) { ElMessage.warning('无有效行'); return }
            const r = await request.post('/inventory/labels/batch-activate', { labels, qcflg: activateForm.qcflg })
            const d = (r as any).data
            const msg = `激活成功 ${d.success} 条` + (d.failed ? `，失败 ${d.failed} 条` : '')
            d.failed ? ElMessage.warning(msg) : ElMessage.success(msg)
        }
        activateVisible.value = false; load()
    } catch (e: any) { ElMessage.error(e?.response?.data?.message || '激活失败') }
    finally { activateSaving.value = false }
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0 }
.search-bar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap }
.field { display: flex; align-items: center; gap: 4px }
.field label { font-size: 13px; color: #606266; white-space: nowrap }
</style>
