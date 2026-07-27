<template>
  <div class="itsm-detail-layout">
    <div class="itsm-search">
      <slot name="search" />
    </div>
    <div class="itsm-body">
      <div class="itsm-list" :class="{ collapsed: listCollapsed }">
        <div class="list-toggle" @click="listCollapsed=!listCollapsed">
          <el-icon><component :is="listCollapsed ? 'Expand' : 'Fold'" /></el-icon>
        </div>
        <div class="list-content" v-show="!listCollapsed">
          <slot name="list" />
        </div>
      </div>
      <div class="itsm-detail" :class="{ 'no-detail': !hasSelection }">
        <div v-if="hasSelection" class="fade-in">
          <div class="itsm-summary">
            <slot name="summary" />
          </div>
          <div class="itsm-actions">
            <slot name="actions" />
          </div>
          <div class="itsm-tabs">
            <slot name="tabs" />
          </div>
        </div>
        <div v-else class="empty-state">
          <el-icon :size="48" color="#c0c4cc"><component is="Document" /></el-icon>
          <p>请从左侧列表选择一条单据查看详情</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, useSlots } from 'vue'
const slots = useSlots()
const listCollapsed = ref(false)
const hasSelection = computed(() => !!slots.summary)
</script>

<style scoped>
.itsm-detail-layout { display:flex;flex-direction:column;height:100%;background:#fff; }
.itsm-search { padding:8px 12px;border-bottom:1px solid #e4e7ed;background:#f5f7fa; }
.itsm-body { display:flex;flex:1;overflow:hidden; }
.itsm-list { position:relative;width:30%;min-width:36px;max-width:420px;overflow:auto;border-right:1px solid #e4e7ed;transition:width .25s ease; }
.itsm-list.collapsed { width:36px;min-width:36px; }
.list-toggle { position:sticky;top:0;z-index:1;padding:6px;text-align:center;cursor:pointer;background:#f5f7fa;border-bottom:1px solid #e4e7ed;font-size:14px; }
.list-toggle:hover { background:#e8eaed; }
.list-content { padding:4px; }
.itsm-detail { flex:1;display:flex;flex-direction:column;overflow:auto;padding:12px;min-width:0; }
.itsm-detail.no-detail { align-items:center;justify-content:center; }
.empty-state { text-align:center;color:#909399; }
.empty-state p { margin-top:12px;font-size:14px; }
.fade-in { animation:fadeIn .2s ease; }
@keyframes fadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
.itsm-summary { margin-bottom:12px; }
.itsm-actions { margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap; }
.itsm-tabs { flex:1;min-height:0; }

@media (max-width: 768px) {
  .itsm-list { width:40%;min-width:36px;max-width:none; }
  .itsm-list.collapsed { width:36px; }
  .itsm-detail { padding:8px; }
}
</style>
