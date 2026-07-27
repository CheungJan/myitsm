<template>
  <div class="page">
    <div class="page-header"><h2>出库单管理</h2><el-button type="primary" size="small" @click="openCreate">新建</el-button></div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field">
          <label>单号</label>
          <el-input v-model="s.bill" placeholder="单号" size="small" style="width:140px" clearable @keyup.enter="doSearch" />
        </div>
        <div class="field">
          <label>仓库</label>
          <el-select v-model="s.whcd" size="small" style="width:130px" clearable>
            <el-option v-for="w in whOptions" :key="w.whcd" :label="w.whnm" :value="w.whcd" />
          </el-select>
        </div>
        <div class="field">
          <label>类型</label>
          <el-select v-model="s.invtyp" size="small" style="width:130px" clearable>
            <el-option v-for="o in invtypOptions" :key="o.value" :label="o.label" :value="o.value"/>
          </el-select>
        </div>
        <div class="field">
          <label>状态</label>
          <el-select v-model="s.auditflg" size="small" style="width:100px" clearable>
            <el-option v-for="(label, code) in auditMap" :key="code" :label="label" :value="code"/>
          </el-select>
        </div>
        <el-button type="primary" size="small" @click="doSearch" style="margin-left:auto">查询</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDrawer">
        <el-table-column prop="outbillid" label="出库单号" width="120" />
        <el-table-column prop="refbillid" label="关联单据" width="120" />
        <el-table-column label="仓库" width="120">
          <template #default="{ row }">{{ row.whnm || row.whcd }}</template>
        </el-table-column>
        <el-table-column label="出库类型" width="100">
          <template #default="{ row }">{{ ovLabel(row.invtyp) }}</template>
        </el-table-column>
        <el-table-column label="出库日期" width="140">
          <template #default="{ row }">{{ formatDate(row.outdate || row.gendate) }}</template>
        </el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作员" width="80">
          <template #default="{ row }">{{ userName(row.opercd) }}</template>
        </el-table-column>
        <el-table-column label="审批" width="70">
          <template #default="{ row }">
            <el-tag :type="auditTag(row.auditflg)" size="small">{{ auditLabel(row.auditflg) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.auditflg === '0' || row.auditflg === '8'" link type="primary" size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button v-if="row.auditflg === '0'" link type="warning" size="small" @click.stop="openAudit(row)">审核</el-button>
            <el-button v-if="row.auditflg === '2'" link type="warning" size="small" @click.stop="handleUnaudit(row)">反审核</el-button>
            <el-button v-if="row.auditflg === '0' || row.auditflg === '8'" link type="danger" size="small" @click.stop="handleVoid(row)">作废</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <!-- 审核弹窗 -->
    <el-dialog title="审核出库单" v-model="auditing" width="620px" @closed="auditTarget = null; auditMemo = ''">
      <template v-if="auditTarget">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单号">{{ auditTarget.outbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ auditTarget.refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ auditTarget.whnm || auditTarget.whcd }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ ovLabel(auditTarget.invtyp as string) }}</el-descriptions-item>
        </el-descriptions>
        <template v-if="((auditTarget.details_prd as any[])||[]).length > 0">
          <h4 style="margin:12px 0 8px">出库明细</h4>
          <el-table :data="(auditTarget.details_prd as any[]) || []" size="small" stripe>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column label="批次时间" width="100">
              <template #default="{row}">{{ row.prddate ? formatDate(row.prddate).substring(0,10) : '-' }}</template>
            </el-table-column>
            <el-table-column prop="outqty" label="数量" width="70"/>
          </el-table>
        </template>
        <template v-if="((auditTarget.details_eid as any[])||[]).length > 0">
          <h4 style="margin:12px 0 8px">出库明细(EID)</h4>
          <el-table :data="(auditTarget.details_eid as any[]) || []" size="small" stripe>
            <el-table-column prop="eid" label="EID" min-width="140"/>
            <el-table-column prop="itemcd" label="物料" width="100"/>
            <el-table-column prop="item_nm" label="物料名称" min-width="140"/>
            <el-table-column prop="outqty" label="数量" width="70"/>
          </el-table>
        </template>
        <el-input
          v-model="auditMemo"
          type="textarea"
          :rows="2"
          placeholder="审核备注"
          style="margin-top:12px"
        />
      </template>
      <template #footer>
        <el-button @click="auditing = false">取消</el-button>
        <el-button type="warning" @click="handleAudit('8')" :loading="auditLoading">审核退回</el-button>
        <el-button type="success" @click="handleAudit('2')" :loading="auditLoading">审核通过</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawer" title="出库单详情" size="600px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small" :label-style="{width:'100px'}">
          <el-descriptions-item label="单号">{{ detail.outbillid }}</el-descriptions-item>
          <el-descriptions-item label="关联单据">{{ detail.refbillid || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ detail.whnm || detail.whcd }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ ovLabel(detail.invtyp as string) }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ formatDate((detail.outdate || detail.gendate) as string) }}</el-descriptions-item>
          <el-descriptions-item label="操作员">{{ userName(detail.opercd as string) }}</el-descriptions-item>
          <el-descriptions-item label="审批">
            <el-tag :type="auditTag(detail.auditflg as string)" size="small">{{ auditLabel(detail.auditflg as string) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">
            <div style="word-break: break-all; white-space: pre-wrap;">{{ detail.memo || '-' }}</div>
          </el-descriptions-item>
        </el-descriptions>
        <template v-if="((detail.details_prd as any[])||[]).length > 0">
          <h4 style="margin:16px 0 8px">出库明细</h4>
          <el-table :data="(detail.details_prd as any[]) || []" size="small" stripe>
            <el-table-column prop="itemcd" label="物料" width="100" />
            <el-table-column prop="item_nm" label="物料名称" min-width="140" />
            <el-table-column label="批次时间" width="100">
              <template #default="{row}">{{ row.prddate ? formatDate(row.prddate).substring(0,10) : '-' }}</template>
            </el-table-column>
            <el-table-column prop="outqty" label="数量" width="70" />
            <el-table-column v-if="detail.invtyp === '9' && detail.auditflg === '2'" label="状态" width="80">
              <template #default="{row}">
                <el-tag v-if="row.closed_flg === '1'" type="info" size="small">已结案</el-tag>
                <el-tag v-else-if="row.pending_qty === 0" type="success" size="small">已入库</el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="detail.invtyp === '9' && detail.auditflg === '2'" label="操作" width="70">
              <template #default="{row}">
                <el-button v-if="row.closed_flg !== '1' && row.pending_qty > 0 && (detail as any).has_returned" link type="warning" size="small" @click="openCloseLine(row, 'prd')">结案</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
        <template v-if="((detail.details_eid as any[])||[]).length > 0">
          <h4 style="margin:16px 0 8px">出库明细(EID)</h4>
          <el-table :data="(detail.details_eid as any[]) || []" size="small" stripe>
            <el-table-column prop="eid" label="EID" min-width="140" />
            <el-table-column prop="itemcd" label="物料" width="100" />
            <el-table-column prop="item_nm" label="物料名称" min-width="140" />
            <el-table-column prop="outqty" label="数量" width="70" />
            <el-table-column v-if="detail.invtyp === '9' && detail.auditflg === '2'" label="状态" width="80">
              <template #default="{row}">
                <el-tag v-if="row.closed_flg === '1'" type="info" size="small">已结案</el-tag>
                <el-tag v-else-if="row.pending_qty === 0" type="success" size="small">已入库</el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="detail.invtyp === '9' && detail.auditflg === '2'" label="操作" width="70">
              <template #default="{row}">
                <el-button v-if="row.closed_flg !== '1' && row.pending_qty > 0 && (detail as any).has_returned" link type="warning" size="small" @click="openCloseLine(row, 'eid')">结案</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </template>
    </el-drawer>

    <!-- 新建出库单 -->
    <el-dialog :title="editing ? '编辑出库单' : '新建出库单'" v-model="creating" width="750px" @closed="resetCreateForm">
      <el-form :model="createForm" label-width="100px" size="small">
        <el-form-item label="出库类型" required>
          <el-select v-model="createForm.invtyp" style="width:100%" @change="onInvtypChange" :disabled="editing">
            <el-option v-for="o in invtypOptions" :key="o.value" :label="o.label" :value="o.value"/>
          </el-select>
        </el-form-item>
        <el-form-item label="出库仓库" required>
          <el-select v-model="createForm.whcd" style="width:100%" filterable placeholder="选择仓库">
            <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='8' || createForm.invtyp==='10'" label="关联工单">
          <el-select v-model="selectedWorkOrderId" style="width:100%" filterable placeholder="选择已下达/生产中的工单" @change="onWorkOrderSelect" :loading="woLoading" clearable>
            <el-option v-for="w in workOrderOptions" :key="w.wo_id" :label="`${w.wo_id} ${w.item_cd||''} (${woStatusMap[w.status||'']||w.status||'?'} | ${w.plan_qty||0}件)`" :value="w.wo_id"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='5'" label="采购入库单" required>
          <el-select v-model="selectedQcPendingId" style="width:100%" filterable placeholder="选择已审核的采购入库单（待质检）" @change="onQcPendingSelect" :loading="qcPendingLoading" :disabled="editing">
            <el-option v-for="o in qcPendingOrders" :key="o.inbillid" :label="`${o.inbillid}${o.refbillid ? ' ← '+o.refbillid : ''} (${o.whcd||''}仓 待检)`" :value="o.inbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='6'" label="退货单" required>
          <el-select v-model="selectedReturnId" style="width:100%" filterable placeholder="选择已审核的采购退货单" @change="onReturnSelect" :loading="returnOrderLoading" :disabled="editing">
<el-option v-for="o in returnableOrders" :key="o.pcbillid" :label="`${o.pcbillid} (待退${o.total_returnable}件)`" :value="o.pcbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp==='6' && selectedReturnId" label="供应商">
          <span style="color:#303133">{{ selectedReturnSuppNm }}</span>
        </el-form-item>
        <el-form-item v-else-if="showRefBillid" label="关联单据号">
          <el-input v-model="createForm.refbillid" :placeholder="refBillidPlaceholder"/>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp === '2' || createForm.invtyp === '3'" label="目标仓库" required>
          <el-select v-model="createForm.targetwhcd" style="width:100%" filterable :placeholder="createForm.invtyp === '2' ? '选择工程师仓' : '选择目标仓库'">
            <el-option v-for="w in whOptions" :key="w.whcd" :label="`${w.whcd} ${w.whnm}`" :value="w.whcd"/>
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.invtyp === '6' && !selectedReturnId" label="供应商">
          <el-select v-model="createForm.suppcd" style="width:100%" filterable placeholder="选择供应商">
            <el-option v-for="s in suppOptions" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="出库日期">
          <el-date-picker v-model="createForm.outdate" type="date" style="width:100%" value-format="YYYY-MM-DD"/>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.memo" type="textarea" :rows="2"/>
        </el-form-item>
        <el-form-item v-if="createForm.whcd && createForm.invtyp !== '6'" label="仓库存量">
          <div style="width:100%;max-height:240px;overflow-y:auto;border:1px solid #e0e0e0;border-radius:4px;padding:8px">
            <div style="display:flex;gap:8px;margin-bottom:8px">
              <el-radio-group v-model="stockViewMode" size="small" @change="onStockViewModeChange">
                <el-radio-button value="batch">批次</el-radio-button>
                <el-radio-button value="eid">EID</el-radio-button>
              </el-radio-group>
              <el-input v-model="stockSearch" size="small" placeholder="搜索" clearable style="flex:1"/>
            </div>
            <div v-if="stockLoading" style="text-align:center;color:#909399;padding:16px">加载中...</div>
            <div v-else-if="filteredStock.length === 0" style="text-align:center;color:#909399;padding:16px">暂无数据</div>
            <!-- 批次模式 -->
            <template v-if="stockViewMode === 'batch'">
              <div v-for="s in filteredStock" :key="s.itemcd + '|' + (s.itemtyp||'') + '|' + (s.prddate||'')" style="display:flex;align-items:center;justify-content:space-between;padding:4px 8px;cursor:pointer;border-radius:4px"
                   :style="{background: isStockSelected(s.itemcd, s.itemtyp, s.prddate, s.ref_inbillid, s.reflineno) ? '#ecf5ff' : ''}"
                   @click="toggleStockItem(s)">
                <span style="font-size:13px">
                  <el-tag size="small" type="info" v-if="s.whcd" style="margin-right:4px">{{ s.whcd }}</el-tag>
                  {{ s.itemcd }} {{ s.item_nm || '' }}
                  <span v-if="s.prddate" style="color:#909399;font-size:11px">{{ formatDate(s.prddate)?.substring(0,10) }}</span>
                </span>
                <span style="display:flex;gap:4px">
                  <el-tag size="small" type="info" v-if="s.itemtyp">{{ qcLabel(s.itemtyp || '') || s.itemtyp }}</el-tag>
                  <el-tag size="small" type="warning">{{ s.itemqty || 0 }}</el-tag>
                </span>
              </div>
            </template>
            <!-- EID模式 -->
            <template v-else>
              <div v-for="s in filteredStock" :key="s.eid||s.itemcd" style="display:flex;align-items:center;justify-content:space-between;padding:4px 8px;cursor:pointer;border-radius:4px"
                   :style="{background: isStockSelected(s.eid||s.itemcd) ? '#ecf5ff' : ''}"
                   @click="toggleEidItem(s)">
                <span style="font-size:13px">
                  <el-tag size="small" type="info" v-if="s.whcd" style="margin-right:4px">{{ s.whcd }}</el-tag>
                  {{ s.eid }} {{ s.item_nm||s.itemcd }}
                </span>
                <el-tag size="small" :type="s.qcflg==='GA'||s.qcflg==='GB'||s.qcflg==='GC'?'success':'warning'">{{ qcLabel(s.qcflg || '') || s.qcflg || '?' }}</el-tag>
              </div>
            </template>
          </div>
        </el-form-item>

        <el-form-item v-if="createForm.invtyp === '8'" label="BOM 导入">
          <div style="display:flex;gap:8px;align-items:center;width:100%">
            <el-tree-select v-model="bomImportCd" :data="bomTreeData" :props="{label:'class_nm',value:'class_cd',children:'children',disabled: isBomNodeDisabled}" node-key="class_cd" filterable clearable check-strictly size="small" style="flex:1" placeholder="选择 BOM（按分类浏览或搜索）" :filter-node-method="filterBomTreeNode" :render-after-expand="false" @change="onBomTreeSelect"/>
            <el-input-number v-model="bomImportQty" :min="1" :max="9999" size="small" style="width:100px" placeholder="数量"/>
            <el-button size="small" type="primary" @click="openBomDialog" :disabled="!bomImportCd">展开预览</el-button>
          </div>
        </el-form-item>
        <el-form-item label="出库明细">
          <div style="width:100%">
            <el-table :data="createDetails" size="small" stripe>
              <el-table-column label="物料" min-width="180">
                <template #default="{$index}">
                  <el-select v-model="createDetails[$index].itemcd" filterable remote reserve-keyword :remote-method="(q:string)=>searchItems(q)" :loading="itemSearching" style="width:100%" size="small" placeholder="搜索物料" clearable>
                    <el-option v-for="it in itemOptions" :key="it.item_cd" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd"/>
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="数量" width="100">
                <template #default="{$index}">
                  <el-input-number v-model="createDetails[$index].outqty" :min="1" :max="createDetails[$index].eid ? 1 : 99999" :disabled="!!createDetails[$index].eid" size="small" style="width:90px"/>
                </template>
              </el-table-column>
              <el-table-column label="EID" width="130">
                <template #default="{$index}">
                  <el-input v-model="createDetails[$index].eid" size="small" placeholder="可选填EID" @change="onEidInput($index)"/>
                </template>
              </el-table-column>
              <el-table-column label="批次时间" width="120">
                <template #default="{$index}">
                  <el-input v-model="createDetails[$index].prddate" size="small" placeholder="批次日期" :disabled="!!createDetails[$index].eid"/>
                </template>
              </el-table-column>
              <el-table-column label="关联行号" width="100">
                <template #default="{$index}">
                  <el-input-number v-model="createDetails[$index].reflineno" :min="0" size="small" style="width:90px"/>
                </template>
              </el-table-column>
              <el-table-column v-if="createForm.invtyp==='5'" label="来源入库单" width="110">
                <template #default="{$index}">
                  <el-input v-model="createDetails[$index].ref_inbillid" size="small" readonly />
                </template>
              </el-table-column>
              <el-table-column v-if="createForm.invtyp == '5'" label="来源入库单" width="110">
                <template #default="{$index}">
                  <el-tag size="small" type="info">{{ createDetails[$index].ref_inbillid || '-' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60">
                <template #default="{$index}">
                  <el-button link type="danger" size="small" @click="removeDetail($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button type="primary" link size="small" @click="addDetail" style="margin-top:8px">+ 添加明细</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="creating = false">取消</el-button>
        <el-button v-if="editing" type="primary" @click="handleUpdate" :loading="createSaving">保存修改</el-button>
        <el-button v-else type="primary" @click="handleCreate" :loading="createSaving">创建</el-button>
      </template>
    </el-dialog>

    <!-- BOM 展开预览弹窗 -->
    <el-dialog v-model="bomDialogVisible" title="BOM 展开预览" width="600px">
      <div v-if="bomLoading" style="text-align:center;padding:24px;color:#909399">加载中...</div>
      <template v-else-if="bomExpandResult">
        <div style="margin-bottom:12px;color:#606266;font-size:13px">
          {{ bomExpandResult.bomcd }} {{ bomExpandResult.bomnm }} × <strong>{{ bomExpandResult.qty }}</strong> 套
          <span v-if="bomExpandResult.whcd" style="margin-left:8px">仓库：{{ bomExpandResult.whcd }}</span>
        </div>
        <el-table :data="bomExpandResult.lines" size="small" stripe>
          <el-table-column prop="itemcd" label="物料" width="90"/>
          <el-table-column prop="item_nm" label="名称" min-width="120" show-overflow-tooltip/>
          <el-table-column label="批次时间" width="100">
            <template #default="{row}">{{ row.prddate ? row.prddate.substring(0,10) : '-' }}</template>
          </el-table-column>
          <el-table-column prop="need_qty" label="需求量" width="80" align="right"/>
          <el-table-column v-if="bomExpandResult.whcd" prop="stock_qty" label="库存" width="70" align="right"/>
          <el-table-column v-if="bomExpandResult.whcd" label="领用数量" width="100" align="center">
            <template #default="{row}">
              <el-input-number v-model="row.pick_qty" :min="0" :max="row.stock_qty" size="small" style="width:90px"/>
            </template>
          </el-table-column>
          <el-table-column v-if="bomExpandResult.whcd" label="是否足量" width="80" align="center">
            <template #default="{row}">
              <el-tag :type="row.enough ? 'success' : 'danger'" size="small">{{ row.enough ? '足' : '不足' }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template #footer>
        <el-button @click="bomDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="applyBomToDetails" :disabled="!bomAllEnough">导入到出库明细</el-button>
        <span v-if="!bomAllEnough" style="color:#f56c6c;font-size:12px;margin-left:8px">⚠ 库存不足，请调整数量或补充库存</span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { useUserNames } from '@/composables/useUserNames'
import { useDict } from '@/composables/useDict'
import request from '@/api/request'
import { fetchSyscodes, fetchItems, fetchBomClassTree, type ItemRecord, type ItemClassNode } from '@/api/master'  // fetchSuppliersSimple 保留备用
const { userName } = useUserNames()
const { dictMap: ovMap, dictLabel: ovLabel } = useDict('OV')
const { dictLabel: qcLabel } = useDict('QC')

import {
    fetchStockOut,
    fetchStockOutDetail,
    fetchWarehouses,
    createStockOut,
    updateStockOut,
    auditStockOut,
    voidStockOut,
    unauditStockOut,
    closeStockOutLines,
    fetchReturnableOrders,
    fetchReturnableOrderLines,
    fetchStock,
    fetchQcPending,
    fetchQcPendingLines,
    type StockOutRecord,
    type ReturnableOrder,
    type ReturnableOrderLine,
    type QcPendingOrder,
    type QcPendingLine,
} from '@/api/warehouse'

const { items, loading, page, perPage, total, onSearch, load } = useListPage<StockOutRecord>(fetchStockOut)
const s = reactive({ bill: '', whcd: '', auditflg: '', invtyp: '' })
const whOptions = ref<{ whcd: string; whnm: string }[]>([])
const drawer = ref(false)
const detail = ref<StockOutRecord | null>(null)
const auditMap = ref<Record<string, string>>({})

// ---- 新建出库单 ----
const invtypOptions = computed(() =>
    Object.entries(ovMap.value)
        .map(([value, label]) => ({ value, label }))
        .sort((a, b) => a.value.localeCompare(b.value))
)
const creating = ref(false)
const createSaving = ref(false)
const createForm = reactive({ invtyp: '', whcd: '', refbillid: '', targetwhcd: '', suppcd: '', outdate: '', memo: '' })
interface DetailRow { itemcd: string; outqty: number; eid: string; reflineno: number | undefined; itemtyp: string; prddate: string; ref_inbillid: string }
const createDetails = reactive<DetailRow[]>([])
const suppOptions = ref<{ supp_cd: string; supp_nm: string }[]>([])
const itemOptions = ref<ItemRecord[]>([])
const itemSearching = ref(false)
const editing = ref(false)
const editingId = ref('')

async function onEidInput(idx: number) {
    const eid = createDetails[idx]?.eid
    if (!eid || eid.length < 3) return
    // EID模式：数量强制为1
    createDetails[idx].outqty = 1
    try {
        const r = await request.get(`/master/eid/${eid}`)
        const data = (r as any).data
        if (data?.whcd) {
            createForm.whcd = data.whcd
            ElMessage.success(`EID ${eid} 在 ${data.whcd} 仓，已自动填入`)
        }
    } catch { /* ignore */ }
}

async function openEdit(row: StockOutRecord) {
    editingId.value = row.outbillid
    editing.value = true
    creating.value = true
    try {
        const r = await fetchStockOutDetail(row.outbillid)
        const detail = r.data as any
        createForm.invtyp = detail.invtyp || ''
        createForm.whcd = detail.whcd || ''
        createForm.targetwhcd = detail.targetwhcd || ''
        createForm.refbillid = detail.refbillid || ''
        createForm.suppcd = detail.suppcd || ''
        createForm.outdate = detail.outdate || ''
        createForm.memo = (detail.memo || '').replace(' [手动更新]', '')
        createDetails.length = 0
        ;(detail.details_prd || []).forEach((d: any) => {
            createDetails.push({ itemcd: d.itemcd, outqty: d.outqty || 1, eid: d.eid || '', reflineno: d.reflineno, itemtyp: d.itemtyp || '', prddate: (d.prddate || '').substring(0, 10), ref_inbillid: d.ref_inbillid || '' })
        })
        ;(detail.details_eid || []).forEach((d: any) => {
            createDetails.push({ itemcd: d.itemcd, outqty: d.outqty || 1, eid: d.eid || '', reflineno: undefined, itemtyp: d.itemtyp || '', prddate: '', ref_inbillid: d.ref_inbillid || '' })
        })
        // 编辑时重新加载仓库库存（watch 中已跳过 editing 场景）
        setTimeout(() => loadWarehouseStock(), 50)
    } catch { /* use row data */ }
}

async function handleUpdate() {
    if (!createForm.whcd) { ElMessage.warning('请选择仓库'); return }
    if ((createForm.invtyp === '2' || createForm.invtyp === '3') && !createForm.targetwhcd) { ElMessage.warning('请选择目标仓库'); return }
    if (createDetails.length === 0 || createDetails.some(d => !d.itemcd || !d.outqty)) { ElMessage.warning('请完善明细'); return }
    // 无批次日期时自动 FIFO 分配
    createDetails.forEach(d => {
        if (!d.prddate && !d.eid && d.itemcd && d.outqty) {
            const batches = stockItems.value
                .filter(s => s.itemcd === d.itemcd && s.itemqty >= d.outqty)
                .sort((a, b) => (a.prddate || '').localeCompare(b.prddate || ''))
            if (batches.length > 0) {
                d.prddate = batches[0].prddate || ''
                d.ref_inbillid = batches[0].ref_inbillid || ''
                d.reflineno = batches[0].reflineno
                d.itemtyp = batches[0].itemtyp || ''
            }
        }
    })
    // 补料 OV=8 编辑：校验物料和数量不超出补料申请范围
    if (editingId.value && (createForm.invtyp === '8') && (createForm.memo||'').includes('补料')) {
        try {
            const origRes = await fetchStockOutDetail(editingId.value) as any
            const origPrds = [...(origRes?.data?.details_prd || []), ...(origRes?.data?.details_eid || [])]
            const origQty: Record<string, number> = {}
            origPrds.forEach((d: any) => { origQty[d.itemcd] = (origQty[d.itemcd]||0) + (Number(d.outqty)||1) })
            const curQty: Record<string, number> = {}
            createDetails.forEach(d => { curQty[d.itemcd] = (curQty[d.itemcd]||0) + (Number(d.outqty)||1) })
            for (const cd of Object.keys(origQty)) {
                if (!curQty[cd]) { ElMessage.warning(`物料 ${cd} 缺领（申请${origQty[cd]}，当前0），请补充`); return }
                if (curQty[cd] > origQty[cd]) { ElMessage.warning(`物料 ${cd} 超出补料申请数量（申请${origQty[cd]}，当前${curQty[cd]}），请调整`); return }
                if (curQty[cd] < origQty[cd]) { ElMessage.warning(`物料 ${cd} 缺领（申请${origQty[cd]}，当前${curQty[cd]}），请补充`); return }
            }
            for (const cd of Object.keys(curQty)) {
                if (!origQty[cd]) { ElMessage.warning(`物料 ${cd} 不在补料申请范围内，请移除`); return }
            }
        } catch { /* 查询失败不阻塞 */ }
    }
    // OV=8/10 生产出库：校验实际领料与 BOM 需求一致（补料豁免：按实际不良数领用）
    if ((createForm.invtyp === '8' || createForm.invtyp === '10') && createForm.refbillid && !(createForm.memo||'').includes('补料')) {
        try {
            const woRes = await request.get(`/mes/work-orders/${createForm.refbillid}`)
            const wo = (woRes as any)?.data
            if (wo?.item_cd) {
                const bomRes = await request.get(`/bom/${wo.item_cd}`)
                const bomRows = (bomRes as any)?.data?.details || []
                if (bomRows.length > 0) {
                    const bomMap = new Map<string, number>()
                    bomRows.forEach((r: any) => { bomMap.set(r.itemcd, (bomMap.get(r.itemcd)||0) + (parseInt(String(r.bomqty))||1)) })
                    const actualMap = new Map<string, number>()
                    createDetails.forEach(d => { actualMap.set(d.itemcd, (actualMap.get(d.itemcd)||0) + (parseInt(String(d.outqty))||0)) })
                    // 检查 BOM 要求物料
                    for (const [itemcd, need] of bomMap) {
                        const actual = actualMap.get(itemcd) || 0
                        const totalNeed = need * (wo.plan_qty || 1)
                        if (actual !== totalNeed) {
                            ElMessage.warning(`物料 ${itemcd} 需求 ${totalNeed}，实际 ${actual}，请调整`); return
                        }
                    }
                    // 检查多余物料
                    for (const [itemcd] of actualMap) {
                        if (!bomMap.has(itemcd)) {
                            ElMessage.warning(`物料 ${itemcd} 不在 BOM 中，不能领用`); return
                        }
                    }
                }
            }
        } catch (e: any) { ElMessage.error('工单或BOM查询失败，无法校验'); return }
    }
    createSaving.value = true
    try {
        const body: Record<string, unknown> = { whcd: createForm.whcd, memo: createForm.memo }
        if (createForm.outdate) body.outdate = createForm.outdate
        if (createForm.targetwhcd) body.targetwhcd = createForm.targetwhcd
        body.details_prd = createDetails.filter(d => !d.eid).map(d => ({ itemcd: d.itemcd, outqty: d.outqty, ...(d.itemtyp ? { itemtyp: d.itemtyp } : {}), ...(d.prddate ? { prddate: d.prddate } : {}), ...(d.reflineno ? { reflineno: d.reflineno } : {}), ...(d.ref_inbillid ? { ref_inbillid: d.ref_inbillid } : {}) }))
        body.details_eid = createDetails.filter(d => d.eid).map(d => ({ itemcd: d.itemcd, outqty: d.outqty, eid: d.eid, ...(d.itemtyp ? { itemtyp: d.itemtyp } : {}), ...(d.ref_inbillid ? { ref_inbillid: d.ref_inbillid } : {}) }))
        await updateStockOut(editingId.value, body)
        ElMessage.success('更新成功')
        creating.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '更新失败')
    } finally { createSaving.value = false }
}

const showRefBillid = computed(() => {
    if (createForm.invtyp === '6') return false
    if (createForm.invtyp === '5') return false
    if (createForm.invtyp === '8') return false
    return ['2'].includes(createForm.invtyp)
})

// 仓库库存浏览
const hasDocSelector = computed(() => createForm.invtyp === '6' || (createForm.invtyp === '5' && !!selectedQcPendingId.value))
const stockItems = ref<{itemcd:string; item_nm:string; itemqty:number; eid?:string; qcflg?:string; itemtyp?:string; prddate?:string; whcd?:string; ref_inbillid?:string; reflineno?:number}[]>([])
const stockLoading = ref(false)
const stockSearch = ref('')
const stockViewMode = ref('batch')
const filteredStock = computed(() => {
    let list = stockItems.value
    // 文档模式（OV=5选单）：EID模式只显示有EID的行，批次模式全部显示
    if (hasDocSelector.value) {
        list = stockViewMode.value === 'eid'
            ? list.filter(s => s.eid)
            : list
    }
    if (!stockSearch.value) return list
    const q = stockSearch.value.toLowerCase()
    return list.filter(s => {
        const key = stockViewMode.value === 'eid' ? (s.eid||'') : s.itemcd
        return key.toLowerCase().includes(q) || (s.item_nm||'').toLowerCase().includes(q)
    })
})

async function loadWarehouseStock() {
    const whcd = createForm.whcd
    if (!whcd || hasDocSelector.value) { stockItems.value = []; return }
    stockLoading.value = true
    try {
        if (stockViewMode.value === 'eid') {
            // EID模式：查该仓库有EID的设备
            const r = await request.get('/eid', { params: { whcd, per_page: 200 } as any, silent: true } as any)
            stockItems.value = ((r as any)?.data?.items || [])
                .filter((e: any) => {
                    if (createForm.invtyp === '9') return (e.qcflg || '') === 'BH'      // 返修：坏品
                    if (createForm.invtyp === '7') return (e.qcflg || '') === 'BF'      // 报废：报废品
                    if (createForm.invtyp === '5') return (e.qcflg || '') === 'DJ'      // 质检：待检品
                    return true                                                          // 其他：全部
                })
                .map((e: any) => ({
                    itemcd: e.itemcd, item_nm: e.item_nm || '', itemqty: 1,
                    eid: e.eid, qcflg: e.qcflg || '', whcd: e.whcd || whcd,
                }))
        } else {
            // 批次模式：展示库存明细（按 prddate 区分批次，不聚合）
            const r = await fetchStock({ whcd, per_page: '100' })
            stockItems.value = ((r.data as any)?.items || [])
                .filter((s: any) => {
                    if (createForm.invtyp === '9') return (s.itemtyp || '') === 'BH' && (s.consume || '') !== '1'  // 返修：坏品+非易耗
                    if (createForm.invtyp === '7') return (s.itemtyp || '') === 'BF'                                // 报废：报废品
                    if (createForm.invtyp === '5') return (s.itemtyp || '') === 'DJ'                                // 质检：待检品
                    return (s.itemqty || 0) > 0                                                                     // 其他：全部
                })
                .map((s: any) => ({
                    itemcd: s.itemcd, item_nm: s.item_nm || '', itemqty: s.itemqty || 0,
                    itemtyp: s.itemtyp || '', prddate: (s.prddate || '').substring(0, 10),
                    whcd: s.whcd || whcd,
                    ref_inbillid: s.ref_inbillid || '',
                }))
        }
    } catch { stockItems.value = [] }
    finally { stockLoading.value = false }
}

function onStockViewModeChange() {
    if (!hasDocSelector.value) loadWarehouseStock()
}

watch(() => createForm.whcd, (_, oldWhcd) => {
    if (editing.value) return
    // 质检出库模式(OV=5)：不清空明细，支持多入库单累积
    // 其他模式或用户手动切换仓库时：清空明细
    if (createForm.invtyp !== '5' && oldWhcd !== undefined) {
        createDetails.length = 0
    }
    if (!hasDocSelector.value) loadWarehouseStock()
})

function isStockSelected(key: string, itemtyp?: string, prddate?: string, ref_inbillid?: string, reflineno?: number) {
    if (stockViewMode.value === 'eid') return createDetails.some(d => d.eid === key)
    // 质检出库模式：物料+批次+入库单+行号 四维匹配
    if (createForm.invtyp === '5') {
        return createDetails.some(d =>
            d.itemcd === key &&
            d.itemtyp === (itemtyp || '') &&
            d.prddate === (prddate || '') &&
            d.ref_inbillid === (ref_inbillid || '') &&
            d.reflineno === reflineno
        )
    }
    return createDetails.some(d => d.itemcd === key && d.itemtyp === (itemtyp || ''))
}
function toggleStockItem(item: {itemcd:string; item_nm:string; itemqty:number; itemtyp?:string; prddate?:string; whcd?:string; ref_inbillid?:string; reflineno?:number}) {
    const ityp = item.itemtyp || ''
    const pdate = item.prddate || ''
    const inbillid = item.ref_inbillid || ''  // 仅从库存取来源入库单号，OV=8不适用工单号
    const lineno = item.reflineno
    let idx: number
    if (createForm.invtyp === '5') {
        // 质检出库模式：物料+批次+入库单+行号，四维区分同物料不同行
        idx = createDetails.findIndex(d =>
            d.itemcd === item.itemcd &&
            d.itemtyp === ityp &&
            d.prddate === pdate &&
            !d.eid &&
            d.ref_inbillid === inbillid &&
            d.reflineno === lineno
        )
    } else {
        // 其他模式：原逻辑，只比较物料和类型
        idx = createDetails.findIndex(d => d.itemcd === item.itemcd && d.itemtyp === ityp && !d.eid)
    }
    if (idx >= 0) { createDetails.splice(idx, 1); return }
    createDetails.push({ itemcd: item.itemcd, outqty: item.itemqty || 1, eid: '', reflineno: lineno, itemtyp: ityp, prddate: pdate, ref_inbillid: inbillid })
}
function toggleEidItem(item: {itemcd:string; item_nm:string; eid?:string}) {
    const key = item.eid || item.itemcd
    const idx = createDetails.findIndex(d => d.eid === key)
    if (idx >= 0) {
        // 移除 EID 行：恢复同物料批次行数量
        const bIdx = createDetails.findIndex(d => !d.eid && d.itemcd === item.itemcd)
        if (bIdx >= 0) { createDetails[bIdx].outqty++ }
        else { createDetails.push({ itemcd: item.itemcd, outqty: 1, eid: '', reflineno: undefined, itemtyp: '', prddate: '', ref_inbillid: '' }) }
        createDetails.splice(idx, 1); return
    }
    // 添加 EID 行时，自动减少同物料批次行的数量
    const batchIdx = createDetails.findIndex(d => !d.eid && d.itemcd === item.itemcd && (d.outqty||0) > 0)
    if (batchIdx >= 0 && createDetails[batchIdx].outqty > 1) {
        createDetails[batchIdx].outqty--
    } else if (batchIdx >= 0) {
        createDetails.splice(batchIdx, 1)
    }
    createDetails.push({ itemcd: item.itemcd, outqty: 1, eid: item.eid || '', reflineno: undefined, itemtyp: '', prddate: '', ref_inbillid: '' })
}
const refBillidPlaceholder = computed(() => {
    if (createForm.invtyp === '2') return '服务领用单号'
    if (createForm.invtyp === '5') return '质检单号'
    if (createForm.invtyp === '6') return '采购退货单号'
    return '关联单据号'
})

// ---- OV=8 生产出库：BOM 导入弹窗 ----
const bomImportCd = ref('')
const bomImportQty = ref(1)
const bomTreeData = ref<ItemClassNode[]>([])
const bomDialogVisible = ref(false)
const bomLoading = ref(false)
const bomExpandResult = ref<{
    bomcd: string; bomnm: string; qty: number; whcd: string | null;
    lines: { itemcd: string; item_nm: string; itemtyp: string; prddate: string; bomqty: number; need_qty: number; stock_qty: number | null; pick_qty: number; enough: boolean | null }[]
} | null>(null)

function isBomNodeDisabled(data: ItemClassNode) {
    // 只有叶子节点(type='item')可选，分类层级不可选
    return (data as any).type !== 'item'
}

function filterBomTreeNode(value: string, data: ItemClassNode) {
    if (!value) return true
    return (data.class_nm || data.class_cd).toLowerCase().includes(value.toLowerCase())
}

function onBomTreeSelect(val: string) {
    bomImportCd.value = val
}

async function openBomDialog() {
    if (!bomImportCd.value) return
    bomDialogVisible.value = true
    bomLoading.value = true
    try {
        const params: Record<string, any> = { qty: bomImportQty.value }
        if (createForm.whcd) params.whcd = createForm.whcd
        const r = await request.get(`/bom/${bomImportCd.value}/expand`, { params } as any)
        bomExpandResult.value = (r as any).data || null
    } catch { bomExpandResult.value = null }
    finally { bomLoading.value = false }
}

const bomAllEnough = computed(() => {
    if (!bomExpandResult.value) return false
    if (!bomExpandResult.value.whcd) return false
    // 按物料汇总 pick_qty >= need_qty 才允许导入
    const totals = new Map<string, number>()
    const needs = new Map<string, number>()
    for (const l of bomExpandResult.value.lines) {
        totals.set(l.itemcd, (totals.get(l.itemcd) || 0) + (l.pick_qty || 0))
        needs.set(l.itemcd, l.need_qty)
    }
    for (const [itemcd, total] of totals) {
        if (total < (needs.get(itemcd) || 0)) return false
    }
    return true
})

function applyBomToDetails() {
    if (!bomExpandResult.value) return
    const imported: string[] = []
    bomExpandResult.value.lines
        .filter(l => (l.pick_qty || 0) > 0)
        .forEach(l => {
            const existing = createDetails.find(d => d.itemcd === l.itemcd && d.prddate === (l.prddate || '') && !d.eid)
            if (existing) {
                existing.outqty += l.pick_qty
            } else {
                createDetails.push({ itemcd: l.itemcd, outqty: l.pick_qty, eid: '', reflineno: undefined, itemtyp: l.itemtyp || '', prddate: l.prddate || '', ref_inbillid: '' })
            }
            imported.push(l.itemcd)
        })
    bomDialogVisible.value = false
    ElMessage.success(`已导入 ${bomExpandResult.value.lines.length} 条 BOM 明细`)
}

// ---- 生产出库：关联工单选择器 ----
const woStatusMap: Record<string, string> = { DRAFT: '草稿', RELEASED: '已下达', PICKING: '领料中', IN_PROGRESS: '生产中', QC_PENDING: '待最终检', COMPLETED: '已完工', CANCELLED: '已取消' }
const workOrderOptions = ref<{ wo_id: string; item_cd?: string; plan_qty?: number; status?: string }[]>([])
const woLoading = ref(false)
const selectedWorkOrderId = ref('')

async function loadWorkOrderOptions() {
    woLoading.value = true
    try {
        const r = await request.get('/mes/work-orders', { params: { per_page: '100' } } as any)
        workOrderOptions.value = ((r as any)?.data?.items || []).filter(
            (w: any) => w.status === 'PICKING' || w.status === 'IN_PROGRESS'
        )
    } catch { workOrderOptions.value = [] }
    finally { woLoading.value = false }
}

function onWorkOrderSelect(woId: string) {
    createForm.refbillid = woId || ''
    if (woId) {
        const wo = workOrderOptions.value.find(w => w.wo_id === woId)
        if (wo?.plan_qty) bomImportQty.value = wo.plan_qty
    }
}

// ---- 质检出库：选择采购入库单 ----
const qcPendingOrders = ref<QcPendingOrder[]>([])
const qcPendingLoading = ref(false)
const selectedQcPendingId = ref('')

async function loadQcPendingOrders() {
    qcPendingLoading.value = true
    try { const r = await fetchQcPending(); qcPendingOrders.value = r.data || [] }
    catch { qcPendingOrders.value = [] }
    finally { qcPendingLoading.value = false }
}

async function onQcPendingSelect(inbillid: string) {
    if (!inbillid) { selectedQcPendingId.value = ''; qcPendingLines.value = []; loadWarehouseStock(); return }
    selectedQcPendingId.value = inbillid
    createForm.refbillid = inbillid
    // 切换入库单时清空旧的物料列表
    stockItems.value = []
    // 查找选中的入库单信息
    const selectedOrder = qcPendingOrders.value.find(o => o.inbillid === inbillid)
    if (selectedOrder) {
        // 自动带出仓库（与入库单一致）
        createForm.whcd = selectedOrder.whcd || ''
    }
    // 加载该入库单的物料明细（替代整个仓库库存）
    await loadQcPendingLines(inbillid)
}

// ---- 质检出库：加载采购入库单物料明细 ----
const qcPendingLines = ref<QcPendingLine[]>([])
async function loadQcPendingLines(inbillid: string) {
    stockLoading.value = true
    try {
        const r = await fetchQcPendingLines(inbillid)
        const newLines = r.data || []
        // 累积到现有列表（支持多入库单）
        qcPendingLines.value = [...qcPendingLines.value, ...newLines]
        // 转换为stockItems格式并追加（不替换已有数据）
        const newItems = newLines.map(line => ({
            itemcd: line.itemcd,
            item_nm: line.item_nm,
            itemqty: line.qty,
            itemtyp: line.itemtyp || 'DJ',
            prddate: line.prddate || '',
            eid: line.eid,
            whcd: line.whcd,
            opt: line.opt,
            reflineno: line.lineno,     // 来源入库单行号（区分同物料不同行）
            ref_inbillid: inbillid,     // 来源入库单号
        }))
        stockItems.value = [...stockItems.value, ...newItems]
    } catch {
        // 失败时不影响已有数据
    } finally {
        stockLoading.value = false
    }
}

// ---- 退货出库：选择退货单 ----
const returnableOrders = ref<ReturnableOrder[]>([])
const returnOrderLoading = ref(false)
const selectedReturnId = ref('')
const selectedReturnSuppNm = ref('')

async function loadReturnableOrders() {
    returnOrderLoading.value = true
    try { const r = await fetchReturnableOrders(); returnableOrders.value = r.data || [] }
    catch { /* ignore */ }
    finally { returnOrderLoading.value = false }
}

async function onReturnSelect(pcbillid: string) {
    if (!pcbillid) { selectedReturnSuppNm.value = ''; return }
    const order = returnableOrders.value.find(o => o.pcbillid === pcbillid)
    if (order) {
        createForm.refbillid = order.pcbillid
        createForm.suppcd = order.suppliercd
        selectedReturnSuppNm.value = order.supp_nm
    }
    const r = await fetchReturnableOrderLines(pcbillid)
    const lines = (r.data || []) as ReturnableOrderLine[]
    createDetails.length = 0
    lines.forEach(l => {
        createDetails.push({
            itemcd: l.itemcd,
            outqty: l.returnable_qty,
            eid: l.eid || '',
            reflineno: l.lineno,
            itemtyp: '',
            prddate: '',
            ref_inbillid: '',
        })
    })
}

function openCreate() {
    editing.value = false
    editingId.value = ''
    creating.value = true
    createForm.whcd = ''
    loadReturnableOrders()
}

function onInvtypChange() {
    createForm.refbillid = ''
    createForm.targetwhcd = ''
    createForm.suppcd = ''
    selectedReturnId.value = ''
    selectedReturnSuppNm.value = ''
    selectedQcPendingId.value = ''
    qcPendingLines.value = []  // 清空累积的入库单明细
    bomImportCd.value = ''
    bomImportQty.value = 1
    createDetails.length = 0
    stockItems.value = []
    if (createForm.invtyp === '5') loadQcPendingOrders()
    if (createForm.invtyp === '8' || createForm.invtyp === '10') loadWorkOrderOptions()
    // 退货出库默认仓库：返厂退机区(L1)
    if (createForm.invtyp === '6') createForm.whcd = 'L1'
}

async function searchItems(query: string) {
    if (!query || query.length < 1) { itemOptions.value = []; return }
    itemSearching.value = true
    try {
        const r = await fetchItems({ search: query, per_page: 20 })
        itemOptions.value = r.data?.items || []
    } catch { /* 忽略 */ }
    finally { itemSearching.value = false }
}

function addDetail() {
    createDetails.push({ itemcd: '', outqty: 1, eid: '', reflineno: undefined, itemtyp: '', prddate: '', ref_inbillid: '' })
}

function removeDetail(index: number) {
    createDetails.splice(index, 1)
}

function resetCreateForm() {
    editing.value = false
    editingId.value = ''
    createForm.invtyp = ''
    createForm.whcd = ''
    createForm.refbillid = ''
    createForm.targetwhcd = ''
    createForm.suppcd = ''
    createForm.outdate = ''
    createForm.memo = ''
    selectedQcPendingId.value = ''
    selectedWorkOrderId.value = ''
    bomImportCd.value = ''
    bomImportQty.value = 1
    createDetails.length = 0
}

async function handleCreate() {
    if (!createForm.whcd || !createForm.invtyp) { ElMessage.warning('请填写出库类型和出库仓库'); return }
    if ((createForm.invtyp === '2' || createForm.invtyp === '3') && !createForm.targetwhcd) { ElMessage.warning('请选择目标仓库'); return }
    if (createDetails.length === 0 || createDetails.some(d => !d.itemcd || !d.outqty)) { ElMessage.warning('请完善出库明细'); return }
    createSaving.value = true
    try {
        const body: Record<string, unknown> = {
            whcd: createForm.whcd,
            invtyp: createForm.invtyp,
            details_prd: createDetails
                .filter(d => !d.eid)
                .map(d => ({
                    itemcd: d.itemcd,
                    outqty: d.outqty,
                    ...(d.itemtyp ? { itemtyp: d.itemtyp } : {}),
                    ...(d.prddate ? { prddate: d.prddate } : {}),
                    ...(d.reflineno != null ? { reflineno: d.reflineno } : {}),
                    ...(d.ref_inbillid ? { ref_inbillid: d.ref_inbillid } : {}),
                })),
            details_eid: createDetails
                .filter(d => d.eid)
                .map(d => ({
                    itemcd: d.itemcd,
                    outqty: d.outqty,
                    eid: d.eid,
                    ...(d.itemtyp ? { itemtyp: d.itemtyp } : {}),
                    ...(d.reflineno != null ? { reflineno: d.reflineno } : {}),
                    ...(d.ref_inbillid ? { ref_inbillid: d.ref_inbillid } : {}),
                })),
        }
        if (createForm.outdate) body.outdate = createForm.outdate
        if (createForm.refbillid) body.refbillid = createForm.refbillid
        if (createForm.targetwhcd) body.targetwhcd = createForm.targetwhcd
        if (createForm.suppcd) body.suppcd = createForm.suppcd
        if (createForm.memo) body.memo = createForm.memo
        // 退货出库：检查是否已有草稿
        if (createForm.invtyp === '6' && createForm.refbillid) {
            const existing = (items.value as any[]).find(
                (r: any) => r.refbillid === createForm.refbillid && r.invtyp === '6' && r.auditflg === '0'
            )
            if (existing) {
                try {
                    await ElMessageBox.confirm(
                        `该退货单已有草稿出库单 ${existing.outbillid}，将更新此草稿而非新建。`,
                        '确认更新草稿',
                        { confirmButtonText: '更新草稿', cancelButtonText: '取消', type: 'warning' }
                    )
                } catch { createSaving.value = false; return }
            }
        }
        await createStockOut(body)
        ElMessage.success('出库单创建成功')
        creating.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '创建失败')
    } finally { createSaving.value = false }
}

onMounted(async () => {
    try {
        const r = await fetchWarehouses()
        whOptions.value = r.data || []
    } catch { /* 忽略 */ }
    try {
        const r = await fetchSyscodes('AF')
        ;(r.data || []).forEach((c: { code_cd: string; code_nm: string }) => {
            auditMap.value[c.code_cd] = c.code_nm
        })
    } catch { /* 忽略 */ }
    try { bomTreeData.value = (await fetchBomClassTree('1')).data || [] } catch { /* 忽略 */ }
})

function auditTag(cd: string) {
    const m: Record<string, string> = { '0': 'info', '1': 'warning', '2': 'success' }
    return m[cd] || 'info'
}

function formatDate(val: string | undefined): string {
    if (!val) return '-'
    return val.replace('T', ' ').substring(0, 19)
}

function auditLabel(cd: string) {
    return auditMap.value[cd] || cd
}

function doSearch() {
    const p: Record<string, string> = {}
    if (s.bill) p.outbillid = s.bill
    if (s.whcd) p.whcd = s.whcd
    if (s.auditflg) p.auditflg = s.auditflg
    if (s.invtyp) p.invtyp = s.invtyp
    onSearch(p)
}

async function openDrawer(row: StockOutRecord) {
    drawer.value = true
    try {
        const r = await fetchStockOutDetail(row.outbillid)
        detail.value = r.data as any
    } catch {
        detail.value = row
    }
}

const auditing = ref(false)
const auditTarget = ref<StockOutRecord | null>(null)
const auditLoading = ref(false)
const auditMemo = ref('')

async function openAudit(row: StockOutRecord) {
    auditTarget.value = row
    auditing.value = true
    try {
        const r = await fetchStockOutDetail(row.outbillid)
        auditTarget.value = r.data as any
    } catch { /* use row data */ }
}

// ---- 行级结案 ----
async function openCloseLine(row: any, type: string) {
    if (!detail.value) return
    try {
        const { value: reason } = await ElMessageBox.prompt(
            `确定结案该明细行（${row.itemcd}${row.eid ? ' EID:' + row.eid : ''}）？结案后不再等待入库。`,
            '行级结案',
            { inputPlaceholder: '请填写结案原因（如：停产/报废/替代等）', confirmButtonText: '确认结案', cancelButtonText: '取消', type: 'warning', inputValidator: (v: string) => !!v?.trim() || '请填写结案原因' },
        )
        const res = await closeStockOutLines(detail.value.outbillid, [{ lineno: row.lineno, type }], reason) as any
        const data = res?.data || res
        let msg = '结案成功'
        if (data?.cleaned_lines) msg += `，已清理关联入库草稿中 ${data.cleaned_lines} 条明细`
        if (data?.voided_drafts?.length) msg += `，草稿 ${data.voided_drafts.join(',')} 已自动作废`
        ElMessage.success(msg)
        // 刷新详情
        const r = await fetchStockOutDetail(detail.value.outbillid)
        detail.value = r.data
    } catch { /* 取消 */ }
}

async function handleUnaudit(row: StockOutRecord) {
    try {
        await ElMessageBox.confirm(
            `反审核将回退库存并清除物料消耗记录，确定反审核 ${row.outbillid} 吗？`,
            '确认反审核', { type: 'warning' }
        )
        await unauditStockOut(row.outbillid)
        ElMessage.success('已反审核，可重新审核')
        load()
    } catch { /* 取消 */ }
}

async function handleVoid(row: StockOutRecord) {
    try {
        await ElMessageBox.confirm(`确定作废出库单 ${row.outbillid} 吗？`, '确认作废', { type: 'warning' })
        await voidStockOut(row.outbillid)
        ElMessage.success('已作废')
        load()
    } catch { /* 取消 */ }
}

async function handleAudit(flg: string) {
    if (!auditTarget.value) return
    auditLoading.value = true
    try {
        await auditStockOut(auditTarget.value.outbillid, flg, auditMemo.value || undefined)
        ElMessage.success(flg === '2' ? '审核通过' : '已退回')
        auditing.value = false
        load()
    } catch (e: any) {
        ElMessage.error(e?.response?.data?.message || '审核失败')
    } finally { auditLoading.value = false }
}
</script>

<style scoped>
.page { padding: 0 }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0 }
.search-bar { display: flex; gap: 12px; align-items: center }
.field { display: flex; align-items: center; gap: 6px }
.field label { font-size: 13px; color: #606266 }
</style>
