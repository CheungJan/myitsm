<template>
  <div class="page">
    <div class="page-header"><h2>采购单据</h2></div>
    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open">
        <el-table-column prop="pcbillid" label="单据号" width="110"/>
        <el-table-column label="采购类型" width="80"><template #default="{row}">{{ row.pctyp || '-' }}</template></el-table-column>
        <el-table-column prop="custcd" label="客户" width="90"/>
        <el-table-column label="金额" width="100" align="right"><template #default="{row}">{{ row.pcamt || '-' }}</template></el-table-column>
        <el-table-column label="日期" width="100"><template #default="{row}">{{ row.pcdate || row.gendate || '-' }}</template></el-table-column>
        <el-table-column prop="whcd" label="仓库" width="80"/>
        <el-table-column label="发票" width="60"><template #default="{row}"><el-tag :type="row.invoiceflg==='1'?'success':'info'" size="small">{{ row.invoiceflg==='1'?'已开':'未开' }}</el-tag></template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
        <el-table-column prop="opercd" label="操作员" width="80"/>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>
    <el-dialog :title="'采购单据 — '+(detail?.pcbillid||'')" v-model="drawer" width="500px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="单据号">{{ detail.pcbillid }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ detail.pctyp||'-' }}</el-descriptions-item>
          <el-descriptions-item label="客户">{{ detail.custcd||'-' }}</el-descriptions-item>
          <el-descriptions-item label="金额">{{ detail.pcamt }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ detail.whcd||'-' }}</el-descriptions-item>
          <el-descriptions-item label="发票"><el-tag :type="detail.invoiceflg==='1'?'success':'info'" size="small">{{ detail.invoiceflg==='1'?'已开':'未开' }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="日期">{{ detail.pcdate||detail.gendate }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo||'-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {fetchProcBills} from '@/api/procurement';import type {ProcRecord} from '@/api/procurement'
const{items,loading,page,perPage,total}=useListPage<ProcRecord>(fetchProcBills);const{drawer,detail,open}=useDetailDrawer<ProcRecord>()</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
