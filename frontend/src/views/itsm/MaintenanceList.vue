<template>
  <div class="page">
    <ItsmDetailLayout>
      <template #search>
        <div class="view-tabs">
          <el-radio-group
            v-model="viewMode"
            size="small"
            @change="onViewModeChange"
          >
            <el-radio-button label="all">
              全部
            </el-radio-button>
            <el-radio-button label="mine">
              派给我
            </el-radio-button>
            <el-radio-button label="area">
              本区域
            </el-radio-button>
          </el-radio-group>
        </div>
        <div class="search-bar">
          <div class="field">
            <label>工单号</label><el-input
              v-model="search.maintenance_id"
              placeholder="维护单ID"
              size="small"
              style="width:130px"
              clearable
              @keyup.enter="doSearch"
            />
          </div>
          <div class="field">
            <label>有限公司</label><el-select
              v-model="search.company_id"
              size="small"
              style="width:150px"
              clearable
              filterable
            >
              <el-option
                v-for="c in yxCompanies"
                :key="c.class_cd"
                :label="c.class_nm"
                :value="c.class_cd"
              />
            </el-select>
          </div>
          <div class="field">
            <label>区域</label><el-select
              v-model="search.area_cd"
              size="small"
              style="width:120px"
              clearable
            >
              <el-option
                v-for="a in areas"
                :key="a.area_cd"
                :label="a.area_nm"
                :value="a.area_cd"
              />
            </el-select>
          </div>
          <div class="field">
            <label>上门工程师</label><el-input
              v-model="search.firstor"
              placeholder="工程师编号"
              size="small"
              style="width:110px"
              clearable
              @keyup.enter="doSearch"
            />
          </div>
          <div class="field">
            <label>磁卡号</label><el-input
              v-model="search.cust_card"
              placeholder="磁卡号"
              size="small"
              style="width:120px"
              clearable
              @keyup.enter="doSearch"
            />
          </div>
          <div class="field">
            <label>店名</label><el-input
              v-model="search.cust_nm"
              placeholder="店名"
              size="small"
              style="width:120px"
              clearable
              @keyup.enter="doSearch"
            />
          </div>
          <div class="field">
            <label>地址</label><el-input
              v-model="search.address"
              placeholder="地址"
              size="small"
              style="width:120px"
              clearable
              @keyup.enter="doSearch"
            />
          </div>
          <div class="field">
            <label>故障类型</label><el-select
              v-model="search.fault_type"
              size="small"
              style="width:120px"
              clearable
            >
              <el-option
                v-for="f in faultTypes"
                :key="f.code_cd"
                :label="f.code_nm"
                :value="f.code_cd"
              />
            </el-select>
          </div>
          <div class="field">
            <label>维护分类</label><el-select
              v-model="search.short_description"
              size="small"
              style="width:130px"
              clearable
              filterable
            >
              <el-option
                v-for="m in mtOptions"
                :key="m.code_cd"
                :label="m.code_nm"
                :value="m.code_nm"
              />
            </el-select>
          </div>
          <div class="field">
            <label>请求日期</label><el-date-picker
              v-model="search.request_begin"
              type="date"
              size="small"
              style="width:140px"
              value-format="YYYY-MM-DD"
              placeholder="起始"
              clearable
            />
          </div>
          <div class="field">
            <label>至</label><el-date-picker
              v-model="search.request_end"
              type="date"
              size="small"
              style="width:140px"
              value-format="YYYY-MM-DD"
              placeholder="结束"
              clearable
            />
          </div>
          <div class="field">
            <label>上门日期</label><el-date-picker
              v-model="search.first_begin"
              type="date"
              size="small"
              style="width:140px"
              value-format="YYYY-MM-DD"
              placeholder="起始"
              clearable
            />
          </div>
          <div class="field">
            <label>至</label><el-date-picker
              v-model="search.first_end"
              type="date"
              size="small"
              style="width:140px"
              value-format="YYYY-MM-DD"
              placeholder="结束"
              clearable
            />
          </div>
          <div class="field">
            <label>状态</label><el-select
              v-model="search.status"
              size="small"
              style="width:110px"
              clearable
            >
              <el-option
                label="新建"
                value="1"
              /><el-option
                label="分配"
                value="2"
              /><el-option
                label="已解决"
                value="5"
              /><el-option
                label="关闭"
                value="3"
              /><el-option
                label="未解决"
                value="4"
              /><el-option
                label="作废"
                value="9"
              />
            </el-select>
          </div>
          <el-button
            type="primary"
            size="small"
            @click="doSearch"
          >
            查询
          </el-button>
          <el-button
            size="small"
            @click="doReset"
          >
            重置
          </el-button>
          <h2 style="margin:0 0 0 auto;font-size:16px;font-weight:600">
            日常维修工单
          </h2>
        </div>
      </template>

      <template #list>
        <el-table
          v-loading="loading"
          :data="items"
          stripe
          size="small"
          highlight-current-row
          row-key="maintenance_id"
          max-height="calc(100vh - 200px)"
          @row-click="open"
        >
          <el-table-column
            prop="maintenance_id"
            label="工单号"
            width="120"
          />
          <el-table-column
            label="门店"
            width="80"
          >
            <template #default="{row}">
              {{ row.store_cust_card || custCard(row.store_id as string) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="short_description"
            label="报修预分类"
            min-width="120"
            show-overflow-tooltip
          />
          <el-table-column
            label="状态"
            width="70"
            align="center"
          >
            <template #default="{row}">
              <el-tag
                :type="statusTag(row.current_status)"
                size="small"
              >
                {{ statusLabel(row.current_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            label="紧急"
            width="55"
          >
            <template #default="{row}">
              {{ jjLabel(row.emergency_level as string) }}
            </template>
          </el-table-column>
          <el-table-column
            label="工程师"
            width="70"
          >
            <template #default="{row}">
              {{ userName(row.firstor) }}
            </template>
          </el-table-column>
          <el-table-column
            label="考核时间"
            width="100"
          >
            <template #default="{row}">
              {{ row.expected_completion_time || '-' }}
            </template>
          </el-table-column>
          <el-table-column
            label="创建"
            width="100"
          >
            <template #default="{row}">
              {{ row.create_time || '-' }}
            </template>
          </el-table-column>
        </el-table>
        <AppPagination
          v-model:current-page="page"
          v-model:page-size="perPage"
          :total="total"
          style="margin-top:8px;justify-content:flex-end"
        />
      </template>

      <template #summary>
        <el-descriptions
          v-if="detail"
          :column="4"
          border
          size="small"
        >
          <el-descriptions-item label="维护单号">
            {{ detail.maintenance_id }}
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag
              :type="statusTag(detail.current_status)"
              size="small"
            >
              {{ statusLabel(detail.current_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="是否补单">
            {{ detail.is_old==='Y'?'是':'否' }}
          </el-descriptions-item>
          <el-descriptions-item label="成功标志">
            {{ detail.is_success==='1'?'成功':(detail.is_success==='0'?'失败':'-') }}
          </el-descriptions-item>
          <el-descriptions-item label="请求人">
            {{ detail.requester || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="请求时间">
            {{ detail.request_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="考核时间">
            {{ detail.expected_completion_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="送货单号">
            {{ detail.deliver_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="故障类型">
            {{ gzLabel(detail.fault_type as string) }}
          </el-descriptions-item>
          <el-descriptions-item label="严重程度">
            {{ yzLabel(detail.servrity as string) }}
          </el-descriptions-item>
          <el-descriptions-item label="紧急程度">
            {{ jjLabel(detail.emergency_level as string) }}
          </el-descriptions-item>
          <el-descriptions-item label="优先级别">
            {{ yxLabel(detail.priority as string) }}
          </el-descriptions-item>
          <el-descriptions-item
            label="报修预分类"
            :span="2"
          >
            {{ mtLabel(detail.short_description as string) }}
          </el-descriptions-item>
          <el-descriptions-item label="请求方式">
            {{ ftLabel(detail.requst_typ as string) }}
          </el-descriptions-item>
          <el-descriptions-item
            label="报修描述"
            :span="2"
          >
            {{ detail.detail_description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="设备_ID">
            {{ detail.device_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="临时联系电话">
            {{ detail.temp_contract || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="首次上门工程师">
            {{ userName(detail.firstor as string) }}
          </el-descriptions-item>
          <el-descriptions-item label="首次上门时间">
            {{ detail.first_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="关单时间">
            {{ detail.close_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="回访时间">
            {{ detail.revisit_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建人">
            {{ userName(detail.creator as string) || detail.creator || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ detail.create_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="更新人">
            {{ userName(detail.updator as string) || detail.updator || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ detail.update_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="关单分类"
            :span="2"
          >
            {{ gdLabel(detail.memo as string) }}
          </el-descriptions-item>
        </el-descriptions>
      </template>

      <template #actions>
        <div
          v-if="detail"
          style="display:flex;gap:8px"
        >
          <el-button
            v-if="detail.current_status==='1'"
            size="small"
            type="primary"
            @click="doTransition(detail,'2')"
          >
            分派
          </el-button>
          <el-button
            v-if="detail.current_status==='2'"
            size="small"
            type="success"
            @click="doTransition(detail,'5')"
          >
            完成维修
          </el-button>
          <el-button
            v-if="detail.current_status==='5'"
            size="small"
            type="warning"
            @click="doTransition(detail,'2')"
          >
            重新打开
          </el-button>
          <el-button
            v-if="['1','2','4','5'].includes(detail.current_status as string)"
            size="small"
            type="danger"
            @click="doTransition(detail,'9')"
          >
            作废
          </el-button>
        </div>
      </template>

      <template #tabs>
        <el-tabs
          v-if="detail"
          v-model="activeTab"
          type="border-card"
          size="small"
        >
          <el-tab-pane
            label="客户信息"
            name="customer"
          >
            <CustomerInfoTab
              :store-id="(detail.store_id as string) || ''"
              business-type="daily"
              :current-record-id="(detail.maintenance_id as string) || ''"
            />
          </el-tab-pane>
          <el-tab-pane
            label="派工"
            name="dispatch"
          >
            <ItsmSubTablePane
              ref="dispatchPaneRef"
              :maintenance-id="(detail.maintenance_id as string) || ''"
              title="派工"
              :fetch-fn="fetchDispatch"
              :create-fn="createDispatch"
              :update-fn="updateDispatch"
              :rules="dispatchRules"
              :row-edit-disabled="isDispatchSent"
              :create-disabled="isClosed"
              :default-form="dispatchDefaultForm"
              :notify-context="dispatchNotifyContext"
              @sent="onDispatchSent"
              @saved="onDispatchSaved"
            >
              <template #columns>
                <el-table-column
                  prop="business_operation_id"
                  label="流水号"
                  width="70"
                />
                <el-table-column
                  label="操作人"
                  width="80"
                >
                  <template #default="{row}">
                    {{ row.operator_nm || row.operator || '-' }}
                  </template>
                </el-table-column>
                <el-table-column
                  label="分派组"
                  width="80"
                >
                  <template #default="{row}">
                    {{ row.accpectd_group_nm || row.accpectd_group || '-' }}
                  </template>
                </el-table-column>
                <el-table-column
                  label="分派人"
                  width="80"
                >
                  <template #default="{row}">
                    {{ row.accpectder_nm || row.accpectder || '-' }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="dispatch_time"
                  label="分派时间"
                  width="120"
                />
                <el-table-column
                  label="创建人"
                  width="80"
                >
                  <template #default="{row}">
                    {{ row.creator_nm || row.creator || '-' }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="create_time"
                  label="创建时间"
                  width="120"
                />
                <el-table-column
                  label="更新人"
                  width="80"
                >
                  <template #default="{row}">
                    {{ row.updator_nm || row.updator || '-' }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="update_time"
                  label="更新时间"
                  width="120"
                />
                <el-table-column
                  label="通知状态"
                  width="140"
                >
                  <template #default="{row}">
                    <el-tag
                      size="small"
                      :type="row.notify_status==='sent'?'success':row.notify_status==='failed'?'danger':'info'"
                    >
                      {{ notifyStatusLabel(row.notify_status as string) }}
                    </el-tag>
                    <el-tag
                      v-if="row.notify_status==='sent' && row.notify_read==='Y'"
                      size="small"
                      type="success"
                      style="margin-left:4px"
                    >
                      已读
                    </el-tag>
                    <el-tag
                      v-else-if="row.notify_status==='sent' && row.notify_read==='N'"
                      size="small"
                      type="warning"
                      style="margin-left:4px"
                    >
                      未读
                    </el-tag>
                    <el-button
                      size="small"
                      link
                      type="primary"
                      style="margin-left:4px"
                      @click="openNotifyEditor(row)"
                    >
                      {{ row.notify_status==='failed'?'重试':(row.notify_status==='sent'?'查看':'发送通知') }}
                    </el-button>
                  </template>
                </el-table-column>
                <el-table-column
                  label="通知数据"
                  width="80"
                >
                  <template #default="{row}">
                    {{ row.notify_data==='Y'?'已产生':'未产生' }}
                  </template>
                </el-table-column>
              </template>
              <template #form="{ form }">
                <el-form-item label="操作人">
                  <el-select
                    v-model="form.operator"
                    filterable
                    style="width:100%"
                    placeholder="选择操作人"
                  >
                    <el-option
                      v-for="u in userOptions"
                      :key="u.user_cd"
                      :label="`${u.user_nm} (${u.user_cd})`"
                      :value="u.user_cd"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="分派组">
                  <el-select
                    v-model="form.accpectd_group"
                    filterable
                    style="width:100%"
                    placeholder="选择分派组"
                    @change="onGroupChange(form)"
                  >
                    <el-option
                      v-for="g in groupOptions"
                      :key="g.group_cd as string"
                      :label="(g.group_nm as string) || (g.group_cd as string)"
                      :value="g.group_cd as string"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="分派人">
                  <el-select
                    v-model="form.accpectder"
                    filterable
                    clearable
                    style="width:100%"
                    placeholder="选择分派人（按组+区域过滤）"
                  >
                    <el-option
                      v-for="u in dispatchCandidates"
                      :key="u.user_cd"
                      :label="`${u.user_nm} (${u.user_cd})`"
                      :value="u.user_cd"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="派工时间">
                  <el-date-picker
                    v-model="form.dispatch_time"
                    type="datetime"
                    value-format="YYYY-MM-DD HH:mm:ss"
                    placeholder="选择派工时间"
                    style="width:100%"
                  />
                </el-form-item>
              </template>
            </ItsmSubTablePane>
          </el-tab-pane>
          <el-tab-pane
            label="通知记录"
            name="notify"
          >
            <el-table
              v-loading="notifyLoading"
              :data="notifyList"
              size="small"
              empty-text="暂无通知记录"
              max-height="500"
            >
              <el-table-column
                prop="dispatch_id"
                width="70"
                label="流水号"
              />
              <el-table-column
                prop="template_id"
                label="模板"
                width="90"
              />
              <el-table-column
                label="业务流水ID"
                width="120"
                show-overflow-tooltip
              >
                <template #default="{row}">
                  {{ row.ref_id || '-' }}
                </template>
              </el-table-column>
              <el-table-column
                label="通知方式"
                width="90"
              >
                <template #default="{row}">
                  <el-tag
                    size="small"
                    :type="channelTagType(row.channel as string)"
                  >
                    {{ channelLabel(row.channel as string) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                label="接收人"
                width="120"
                show-overflow-tooltip
              >
                <template #default="{row}">
                  {{ recipientLabel(row) }}
                </template>
              </el-table-column>
              <el-table-column
                prop="subject"
                label="标题"
                min-width="150"
                show-overflow-tooltip
              />
              <el-table-column
                prop="body"
                label="正文"
                min-width="200"
                show-overflow-tooltip
              />
              <el-table-column
                label="发送状态"
                width="80"
              >
                <template #default="{row}">
                  <el-tag
                    size="small"
                    :type="row.send_status==='sent'?'success':row.send_status==='failed'?'danger':'info'"
                  >
                    {{ sendStatusLabel(row.send_status as string) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                label="已读"
                width="60"
              >
                <template #default="{row}">
                  <el-tag
                    v-if="row.channel==='internal'"
                    size="small"
                    :type="row.read_status==='read'?'success':'info'"
                  >
                    {{ row.read_status==='read'?'已读':'未读' }}
                  </el-tag><span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="read_time"
                label="阅读时间"
                width="135"
              >
                <template #default="{row}">
                  {{ row.read_time || '-' }}
                </template>
              </el-table-column>
              <el-table-column
                prop="retry_count"
                label="重试"
                width="50"
                align="center"
              />
              <el-table-column
                prop="send_time"
                label="发送时间"
                width="135"
              />
              <el-table-column
                prop="error_msg"
                label="错误信息"
                min-width="120"
                show-overflow-tooltip
              />
              <el-table-column
                label="操作员"
                width="90"
              >
                <template #default="{row}">
                  {{ operLabel(row.opercd as string) }}
                </template>
              </el-table-column>
              <el-table-column
                prop="gendate"
                label="创建时间"
                width="135"
              />
            </el-table>
          </el-tab-pane>
          <el-tab-pane
            label="上门服务"
            name="d2d"
          >
            <D2DOperationTab
              :maintenance-id="(detail.maintenance_id as string) || ''"
              :main-record="detail"
            />
          </el-tab-pane>
          <el-tab-pane
            label="回访"
            name="rv"
          >
            <ItsmSubTablePane
              :maintenance-id="(detail.maintenance_id as string) || ''"
              title="回访"
              :fetch-fn="fetchRV"
              :create-fn="createRV"
              :update-fn="updateRV"
              :rules="rvRules"
            >
              <template #columns>
                <el-table-column
                  label="回访人"
                  width="80"
                >
                  <template #default="{row}">
                    {{ row.rv_operator_nm || row.rv_operator || '-' }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="rv_time"
                  label="回访时间"
                  width="120"
                />
                <el-table-column
                  label="满意度"
                  width="70"
                >
                  <template #default="{row}">
                    {{ row.satisfaction_nm || row.satisfaction || '-' }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="feedback"
                  label="反馈"
                  min-width="120"
                  show-overflow-tooltip
                />
              </template>
              <template #form="{ form }">
                <el-form-item label="回访人">
                  <el-input v-model="form.rv_operator" />
                </el-form-item>
                <el-form-item label="回访时间">
                  <el-date-picker
                    v-model="form.rv_time"
                    type="datetime"
                    value-format="YYYY-MM-DD HH:mm:ss"
                    placeholder="选择回访时间"
                    style="width:100%"
                  />
                </el-form-item>
                <el-form-item label="满意度">
                  <el-input v-model="form.satisfaction" />
                </el-form-item>
                <el-form-item label="反馈">
                  <el-input
                    v-model="form.feedback"
                    type="textarea"
                  />
                </el-form-item>
              </template>
            </ItsmSubTablePane>
          </el-tab-pane>
          <el-tab-pane
            label="物料与收费"
            name="mc"
          >
            <MaterialChargePane
              :maintenance-id="(detail.maintenance_id as string) || ''"
              :current-status="(detail.current_status as string) || ''"
              :store-id="(detail.store_id as string) || ''"
              :engineer-id="(detail.engineer_id as string) || ''"
            />
          </el-tab-pane>
          <el-tab-pane
            label="设备资产"
            name="asset"
          >
            <AssetTab :store-id="(detail.store_id as string) || ''" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </ItsmDetailLayout>
    <el-dialog
      v-model="notifyEditorVisible"
      title="派工通知"
      width="640px"
      append-to-body
    >
      <DispatchNotifyEditor
        v-if="notifyEditorVisible"
        :dispatch-id="notifyEditorProps.dispatchId"
        :recipient="notifyEditorProps.recipient"
        :recipient-name="notifyEditorProps.recipientName"
        :maintenance-id="notifyEditorProps.maintenanceId"
        :store-id="notifyEditorProps.storeId"
        :fault-type="notifyEditorProps.faultType"
        @sent="onNotifySent"
      />
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import {reactive,ref,computed,onMounted,watch} from 'vue'
import {useRoute} from 'vue-router'
import {fetchSyscodes, fetchAreas, fetchYXCompanies, fetchAreaUsers} from '@/api/master'
import type {AreaUserRecord} from '@/api/master'
import {fetchGroups, fetchUsers, fetchGroupMembers} from '@/api/system'
import type {UserItem} from '@/api/system'
import {useAuthStore} from '@/stores/auth'
import {ElMessage} from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import {useListPage} from '@/composables/useListPage'
import {useDetailDrawer} from '@/composables/useDetailDrawer'
import {useUserNames} from '@/composables/useUserNames'
import {useCustomerCards} from '@/composables/useCustomerCards'
import {fetchMaintenanceDaily, transitionMaintenanceDaily, fetchRV, createRV, updateRV, fetchDispatch, createDispatch, updateDispatch, fetchDispatchResolve} from '@/api/itsm'
import type {MntRecord} from '@/api/itsm'
import {useDict} from '@/composables/useDict'
import {fetchNotifications} from '@/api/notification'
import ItsmDetailLayout from './ItsmDetailLayout.vue'
import CustomerInfoTab from './CustomerInfoTab.vue'
import AssetTab from './AssetTab.vue'
import ItsmSubTablePane from './ItsmSubTablePane.vue'
import D2DOperationTab from './D2DOperationTab.vue'
import MaterialChargePane from './MaterialChargePane.vue'
import DispatchNotifyEditor from './DispatchNotifyEditor.vue'

const route=useRoute()
const{items,loading,page,perPage,total,onSearch}=useListPage<MntRecord>(fetchMaintenanceDaily)
const{detail,open}=useDetailDrawer<MntRecord>()
const{userName}=useUserNames();const{custCard}=useCustomerCards()
const{dictLabel:yzLabel}=useDict('YZ');const{dictLabel:jjLabel}=useDict('JJ');const{dictLabel:gzLabel}=useDict('GZ');const{dictLabel:mtLabel}=useDict('MT');const{dictLabel:yxLabel}=useDict('YX');const{dictLabel:gdLabel}=useDict('GD');const{dictLabel:ftLabel}=useDict('FT')
const activeTab=ref('customer')
const authStore=useAuthStore()

// 操作员候选：全部有效用户（useflg='1'）
const userOptions=ref<UserItem[]>([])
async function loadUsers(){ try{ const r=await fetchUsers({useflg:'1'}); userOptions.value=r?.data||[] }catch{ userOptions.value=[] } }

// 分派组候选
const groupOptions=ref<Record<string,unknown>[]>([])
async function loadGroups(){ try{ const r=await fetchGroups(); groupOptions.value=(r?.data||[]) as Record<string,unknown>[] }catch{ groupOptions.value=[] } }

onMounted(()=>{ loadUsers(); loadGroups() })

// 派工候选工程师：组成员 ∩ 区域人员，区域长兜底
const dispatchCandidates=ref<AreaUserRecord[]>([])
// 缓存：当前工单的区域人员（choose=1）和区域长
const cachedAreaUsers=ref<AreaUserRecord[]>([])
const areaManagerCd=ref<string>('')
const resolvedTarget=ref<Record<string,unknown>>({})
const notifyList=ref<Record<string,unknown>[]>([])
const notifyLoading=ref(false)

// 按选中的组重载分派人候选：组成员 ∩ 区域人员 + 区域长兜底
async function reloadCandidates(groupCd:string){
  if(!groupCd){
    dispatchCandidates.value=[...cachedAreaUsers.value]
    return
  }
  // 直接加载组成员，不做区域交集（规则引擎已区分 area_manager / group_leader）
  try{
    const r=await fetchGroupMembers(groupCd, {active_only:'1'})
    dispatchCandidates.value=(r?.data||[]).map(m=>({ user_cd:m.user_cd, user_nm:m.user_nm, choose:1 }))
  }catch{ dispatchCandidates.value=[...cachedAreaUsers.value] }
}

// 分派组 change：重载候选、清空分派人
function onGroupChange(form:Record<string,unknown>){
  reloadCandidates(form.accpectd_group as string)
  // 切换组时清空分派人，让用户从筛选后列表重选
  form.accpectder=''
}

watch(()=>detail.value as MntRecord | null, async (d)=>{
  dispatchCandidates.value=[]
  cachedAreaUsers.value=[]
  areaManagerCd.value=''
  if(!d) return
  const areaCd=(d as any).area_cd as string
  if(areaCd){
    try{
      const r=await fetchAreaUsers(areaCd)
      const areaUsers=(r?.data||[]).filter(u=>u.choose===1)
      // 查区域长
      const areaInfo=areas.value.find(a=>a.area_cd===areaCd)
      const mgrCd=areaInfo?.usercd||''
      areaManagerCd.value=mgrCd
      // 区域长不在区域人员列表内时，追加到候选
      if(mgrCd && !areaUsers.some(u=>u.user_cd===mgrCd)){
        const mgr=userOptions.value.find(u=>u.user_cd===mgrCd)
        areaUsers.unshift({ user_cd: mgrCd, user_nm: mgr?.user_nm||mgrCd, choose: 1 })
      }
      cachedAreaUsers.value=areaUsers
      // 解析派单规则目标（先清空候选，等规则解析完再填）
      dispatchCandidates.value=[]
      try{ const rt=await fetchDispatchResolve(d.fault_type as string, d.store_id as string); if(rt?.data) resolvedTarget.value=rt.data as Record<string,unknown> }catch{ resolvedTarget.value={} }
      const tt=resolvedTarget.value.target_type as string
      const tv=resolvedTarget.value.target_value as string
      if((tt==='group_leader'||tt==='load_balance') && tv){
        await reloadCandidates(tv)
      }else{
        dispatchCandidates.value=[...areaUsers]
      }
    }catch{ dispatchCandidates.value=[] }
  }
  // 加载通知记录（本工单所有通知）
  loadNotifyList()
},{immediate:true})

// 加载通知记录（提取为独立函数，供多处复用）
async function loadNotifyList(){
  if(!detail.value?.maintenance_id) return
  notifyLoading.value=true
  try{
    const nr=await fetchNotifications({ref_id:detail.value.maintenance_id as string, per_page:'100', view:'all'})
    notifyList.value=(nr?.data?.items||[]) as Record<string,unknown>[]
  }catch{ notifyList.value=[] }
  finally{ notifyLoading.value=false }
}

// 切换到"通知记录"tab 时自动刷新
watch(activeTab, (tab)=>{
  if(tab==='notify') loadNotifyList()
})

// 派工保存/发送通知后刷新通知记录列表
async function onDispatchSent(){ await loadNotifyList(); dispatchPaneRef.value?.load() }
async function onDispatchSaved(){ dispatchPaneRef.value?.load() }

// 派工新建默认值：操作员=当前登录用户，分派组=A1 兜底，分派人=区域长，派工时间=当前
const dispatchDefaultForm=computed(()=>({ operator: authStore.userCode||'', accpectd_group: (resolvedTarget.value.accpectd_group as string)||'A1', accpectder: (resolvedTarget.value.accpectder as string)||areaManagerCd.value||'', dispatch_time: new Date().toISOString().slice(0,19).replace('T',' ') }))
const dispatchNotifyContext=computed(()=>(detail.value ? {
  maintenance_id: detail.value.maintenance_id,
  store_id: detail.value.store_id,
  cust_card: custCard(detail.value.store_id as string),
  cust_nm: '',
  fault_type: gzLabel(detail.value.fault_type as string),
  short_description: detail.value.short_description||'',
  accpectder: (resolvedTarget.value.accpectder as string)||areaManagerCd.value||'',
  accpectd_group: (resolvedTarget.value.accpectd_group as string)||'A1',
  request_time: detail.value.request_time||'',
  address: '',
  phone_no: '',
} : {}))

// 已发送通知的派工行不可编辑
function isDispatchSent(row:Record<string,unknown>):boolean{ return row.notify_status==='sent' }

// 已关单（状态 3=关单 / 9=作废）不可新增派工
const isClosed=computed(()=>{ const s=((detail.value as any)?.current_status as string)||''; return ['3','9'].includes(s) })

// 子表校验规则（对齐 PB 必填校验）
const rvRules={rv_operator:[{required:true,message:'请输入回访人',trigger:'blur'}],rv_time:[{required:true,message:'请选择回访时间',trigger:'change'}]}
const dispatchRules={accpectd_group:[{required:true,message:'请选择分派组',trigger:'change'}],accpectder:[{required:true,message:'请选择分派人',trigger:'change'}],dispatch_time:[{required:true,message:'请选择派工时间',trigger:'change'}]}
// 通知状态标签（重构 PB fxbz 飞信状态）
const notifyStatusMap:Record<string,string>={sent:'已发',pending:'未发',failed:'失败',N:'未发'}
function notifyStatusLabel(v:string){return notifyStatusMap[v]||'未发'}

// 通知记录 tab 辅助函数
const channelLabelMap:Record<string,string>={internal:'站内',email:'邮件',sms:'短信',dingtalk:'钉钉',ntfy:'推送',feishu:'飞书',wecom:'企微',fetion:'飞信(历史)'}
function channelLabel(v:string){return channelLabelMap[v]||v||'-'}
function channelTagType(v:string){const m:Record<string,string>={internal:'info',email:'primary',sms:'warning',dingtalk:'success',ntfy:'success'};return m[v]||'info'}
function sendStatusLabel(v:string){return v==='sent'?'已发':v==='failed'?'失败':v==='pending'?'待发':'-'}
// 接收人展示：internal 显示用户名，email 显示邮箱，sms 显示手机号
function recipientLabel(row:Record<string,unknown>):string{
  const ch=row.channel as string
  const r=String(row.recipient||'')
  if(!r) return '-'
  if(ch==='internal'){ const nm=userName(r); return nm&&nm!==r?`${nm}(${r})`:r }
  return r
}
// 操作员展示：编码→姓名（姓名(编码)）
function operLabel(code:string):string{
  if(!code) return '-'
  const nm=userName(code)
  return nm&&nm!==code?`${nm}(${code})`:code
}

// 通知编辑器对话框：在派工列表内直接发送/重试通知
const notifyEditorVisible=ref(false)
const dispatchPaneRef=ref<InstanceType<typeof ItsmSubTablePane>|null>(null)
const notifyEditorProps=ref<{dispatchId:number|null;recipient:string;recipientName:string;maintenanceId:string;storeId:string;faultType:string}>({dispatchId:null,recipient:'',recipientName:'',maintenanceId:'',storeId:'',faultType:''})
function openNotifyEditor(row:Record<string,unknown>){
  notifyEditorProps.value={
    dispatchId: (row.id as number|null)??null,
    recipient: (row.accpectder as string)||'',
    recipientName: (row.accpectder_nm as string)||'',
    maintenanceId: (row.maintenance_id as string)||((detail.value as any)?.maintenance_id as string)||'',
    storeId: (detail.value as any)?.store_id as string||'',
    faultType: (detail.value as any)?.fault_type as string||'',
  }
  notifyEditorVisible.value=true
}
async function onNotifySent(){
  notifyEditorVisible.value=false
  await loadNotifyList()
  dispatchPaneRef.value?.load()
}
const search=reactive({
  maintenance_id:'', company_id:'', area_cd:'', firstor:'',
  cust_card:'', cust_nm:'', address:'',
  fault_type:'', short_description:'', status:'',
  request_begin:'', request_end:'', first_begin:'', first_end:''
})
const faultTypes=ref<{code_cd:string;code_nm:string}[]>([])
const mtOptions=ref<{code_cd:string;code_nm:string}[]>([])
const areas=ref<{area_cd:string;area_nm:string;usercd?:string}[]>([])
const yxCompanies=ref<{class_cd:string;class_nm:string}[]>([])

onMounted(async()=>{
  try{const r=await fetchSyscodes('GZ');faultTypes.value=r.data||[]}catch{ /* 忽略字典加载失败 */ }
  try{const r=await fetchSyscodes('MT');mtOptions.value=r.data||[]}catch{ /* 忽略字典加载失败 */ }
  try{const r=await fetchAreas();areas.value=r.data||[]}catch{ /* 忽略区域加载失败 */ }
  try{const r=await fetchYXCompanies();yxCompanies.value=r.data||[]}catch{ /* 忽略公司加载失败 */ }
  // 支持从通知铃铛跳转：携带 maintenance_id + tab=notify
  const q=route.query
  if(q.maintenance_id){
    const mid=String(q.maintenance_id)
    search.maintenance_id=mid
    doSearch()
    // 直接拉取该工单并打开详情
    try{
      const r=await fetchMaintenanceDaily({maintenance_id:mid})
      const found=(r.data?.items||[]).find((it:MntRecord)=>it.maintenance_id===mid)
      if(found){ open(found); if(q.tab) activeTab.value=String(q.tab) }
    }catch{ /* 忽略工单详情加载失败 */ }
  }else if(q.tab){
    activeTab.value=String(q.tab)
  }
})

function statusTag(s:unknown){const m:Record<string,string>={'1':'info','2':'primary','3':'success','4':'warning','5':'primary','9':'danger'};return m[s as string]||'info'}
function statusLabel(s:unknown){const m:Record<string,string>={'1':'新建','2':'分配','3':'关闭','4':'未解决','5':'已解决','9':'作废'};return m[s as string]||s as string}

function doSearch(){
  const p:Record<string,string>={}
  if(search.maintenance_id)p.maintenance_id=search.maintenance_id
  if(search.company_id)p.company_id=search.company_id
  if(search.area_cd)p.area_cd=search.area_cd
  if(search.firstor)p.firstor=search.firstor
  if(search.cust_card)p.cust_card=search.cust_card
  if(search.cust_nm)p.cust_nm=search.cust_nm
  if(search.address)p.address=search.address
  if(search.fault_type)p.fault_type=search.fault_type
  if(search.short_description)p.short_description=search.short_description
  if(search.status)p.status=search.status
  if(search.request_begin)p.request_begin=search.request_begin
  if(search.request_end)p.request_end=search.request_end
  if(search.first_begin)p.first_begin=search.first_begin
  if(search.first_end)p.first_end=search.first_end
  // 视图模式注入：派给我/本区域
  if(viewMode.value==='mine' && authStore.userCode) p.dispatch_to=authStore.userCode
  if(viewMode.value==='area' && authStore.userCode) p.area_user=authStore.userCode
  onSearch(p)
}

function doReset(){
  Object.keys(search).forEach(k=>{(search as any)[k]=''})
  viewMode.value='all'
  onSearch({})
}

// 视图模式切换：派给我/本区域/全部
const viewMode=ref<'all'|'mine'|'area'>('all')
function onViewModeChange(){ doSearch() }

async function doTransition(row:MntRecord,toStatus:string){
  try{
    await transitionMaintenanceDaily(row.maintenance_id as string,{to_status:toStatus})
    ElMessage.success('流转成功')
    onSearch({})
  }catch{ElMessage.error('流转失败')}
}
</script>
<style scoped>
.page{padding:0;display:flex;flex-direction:column;height:calc(100vh - 110px)}
.view-tabs{margin-bottom:8px}
.search-bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.field{display:flex;align-items:center;gap:4px}
.field label{font-size:13px;color:#606266;white-space:nowrap}
</style>
