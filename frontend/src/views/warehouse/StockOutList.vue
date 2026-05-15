<template>
  <div class="page">
    <h2>出库单管理 — DEBUG</h2>
    <p>组件已加载，共 {{ total }} 条</p>
    <el-table :data="items" v-loading="loading" stripe size="small">
      <el-table-column prop="outbillid" label="出库单号" width="140"/>
      <el-table-column prop="gendate" label="日期" width="120"/>
      <el-table-column prop="opercd" label="操作员" width="100"/>
    </el-table>
    <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
  </div>
</template>
<script setup lang="ts">
import AppPagination from '@/components/common/AppPagination.vue'
import { useListPage } from '@/composables/useListPage'
import { fetchStockOut } from '@/api/warehouse'
import type { StockOutRecord } from '@/api/warehouse'
const { items, loading, page, perPage, total } = useListPage<StockOutRecord>(fetchStockOut)
</script>
<style scoped>.page{padding:0}h2{font-size:18px;font-weight:600;margin-bottom:16px}</style>
