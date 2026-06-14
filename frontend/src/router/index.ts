import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'Login',
            component: () => import('@/views/login/LoginView.vue'),
            meta: { requiresAuth: false }
        },
        {
            path: '/',
            component: () => import('@/layouts/MainLayout.vue'),
            meta: { requiresAuth: true },
            redirect: '/dashboard',
            children: [
                {
                    path: 'dashboard',
                    name: 'Dashboard',
                    component: () => import('@/views/dashboard/DashboardView.vue'),
                    meta: { title: '首页' }
                },
                {
                    path: 'system/users',
                    name: 'Users',
                    component: () => import('@/views/system/UserList.vue'),
                    meta: { title: '用户管理' }
                },
                {
                    path: 'system/departments',
                    name: 'Departments',
                    component: () => import('@/views/system/DepartmentList.vue'),
                    meta: { title: '部门管理' }
                },
                {
                    path: 'system/groups',
                    name: 'Groups',
                    component: () => import('@/views/system/GroupList.vue'),
                    meta: { title: '用户组管理' }
                },
                {
                    path: 'system/params',
                    name: 'SysParams',
                    component: () => import('@/views/system/ParamsList.vue'),
                    meta: { title: '系统参数' }
                },
                {
                    path: 'system/codes',
                    name: 'SysCodes',
                    component: () => import('@/views/system/SystemCodes.vue'),
                    meta: { title: '系统字典' }
                },
                {
                    path: 'master/items',
                    name: 'Items',
                    component: () => import('@/views/master/ItemList.vue'),
                    meta: { title: '物料管理' }
                },
                {
                    path: 'master/customers',
                    name: 'Customers',
                    component: () => import('@/views/master/CustomerList.vue'),
                    meta: { title: '客户管理' }
                },
                {
                    path: 'master/eid',
                    name: 'EidList',
                    component: () => import('@/views/master/EidList.vue'),
                    meta: { title: 'EID 管理' }
                },
                {
                    path: 'master/assets',
                    name: 'Assets',
                    component: () => import('@/views/master/AssetList.vue'),
                    meta: { title: '资产台账' }
                },
                {
                    path: 'master/warehouses',
                    name: 'Warehouses',
                    component: () => import('@/views/master/WarehouseList.vue'),
                    meta: { title: '仓库管理' }
                },
                {
                    path: 'master/bom',
                    name: 'BomList',
                    component: () => import('@/views/master/BomList.vue'),
                    meta: { title: 'BOM管理' }
                },
                {
                    path: 'warehouse/config', name: 'WarehouseConfig', component: () => import('@/views/warehouse/WarehouseConfig.vue'), meta: { title: '仓库配置' }
                },
                {
                    path: 'warehouse/asset-check', name: 'AssetCheckList', component: () => import('@/views/warehouse/AssetCheckList.vue'), meta: { title: '资产盘点' }
                },
                {
                    path: 'warehouse/stock-in',
                    name: 'StockInList',
                    component: () => import('@/views/warehouse/StockInList.vue'),
                    meta: { title: '入库单管理' }
                },
                {
                    path: 'warehouse/stock-balance', name: 'StockBalance', component: () => import('@/views/warehouse/StockBalance.vue'), meta: { title: '库存查询' }
                },
                {
                    path: 'warehouse/stock-movement', name: 'StockMovement', component: () => import('@/views/warehouse/StockMovement.vue'), meta: { title: '库存流水' }
                },
                {
                    path: 'warehouse/stock-out',
                    name: 'StockOutList',
                    component: () => import('@/views/warehouse/StockOutList.vue'),
                    meta: { title: '出库单管理' }
                },
                {
                    path: 'procurement/dashboard', name: 'RequisitionDashboard', component: () => import('@/views/procurement/RequisitionDashboard.vue'), meta: { title: '采购看板' }
                },
                {
                    path: 'procurement/suppliers', name: 'SupplierList', component: () => import('@/views/procurement/SupplierList.vue'), meta: { title: '供应商管理' }
                },
                {
                    path: 'procurement/requisitions',
                    name: 'RequisitionList',
                    component: () => import('@/views/procurement/PurchasePlanList.vue'),
                    meta: { title: '采购需求' }
                },
                {
                    path: 'procurement/orders',
                    name: 'OrderList',
                    component: () => import('@/views/procurement/PurchaseRegisterList.vue'),
                    meta: { title: '采购订单' }
                },
                {
                    path: 'itsm/renovate', name: 'RenovateList', component: () => import('@/views/itsm/RenovateList.vue'), meta: { title: '旧机翻新' }
                },
                {
                    path: 'itsm/device-change', name: 'DeviceChangeList', component: () => import('@/views/itsm/DeviceChangeList.vue'), meta: { title: '设备变更' }
                },
                {
                    path: 'itsm/store-close', name: 'StoreCloseList', component: () => import('@/views/itsm/StoreCloseList.vue'), meta: { title: '门店关闭' }
                },
                {
                    path: 'procurement/settlements', name: 'SettlementList', component: () => import('@/views/procurement/PurchaseBillList.vue'), meta: { title: '采购结算单' }
                },
                {
                    path: 'sales/bills', name: 'SalesBillList', component: () => import('@/views/sales/SalesBillList.vue'), meta: { title: '销售单据' }
                },
                {
                    path: 'itsm/open', name: 'MaintenanceOpenList', component: () => import('@/views/itsm/MaintenanceOpenList.vue'), meta: { title: '新机开通' }
                },
                {
                    path: 'itsm/recycle', name: 'RecycleTaskList', component: () => import('@/views/itsm/RecycleTaskList.vue'), meta: { title: '回收任务' }
                },
                {
                    path: 'qc/results', name: 'QcResultList', component: () => import('@/views/qc/QcResultList.vue'), meta: { title: '质检结果' }
                },
                { path: 'qc/input', name: 'QcInput', component: () => import('@/views/qc/QcInput.vue'), meta: { title: '质检录入' } },
                {
                    path: 'itsm/maintenance',
                    name: 'MaintenanceList',
                    component: () => import('@/views/itsm/MaintenanceList.vue'),
                    meta: { title: '日常维修' }
                },
                {
                    path: 'sales/extends', name: 'SalesExtendList', component: () => import('@/views/sales/SalesExtendList.vue'), meta: { title: '延期管理' }
                },
                {
                    path: 'sales/calls', name: 'CallConsole', component: () => import('@/views/sales/CallConsole.vue'), meta: { title: '话务台' }
                },
                {
                    path: 'warehouse/pos-change', name: 'PosChangeList', component: () => import('@/views/warehouse/PosChangeList.vue'), meta: { title: '设备回收确认' }
                },
                {
                    path: 'procurement/appraisals', name: 'SupplierAppraisalList', component: () => import('@/views/procurement/SupplierAppraisalList.vue'), meta: { title: '供应商评价' }
                },
                {
                    path: 'sales/plans',
                    name: 'PlanList',
                    component: () => import('@/views/sales/PlanList.vue'),
                    meta: { title: '预计划管理' }
                },
                { path: 'portal/users', name: 'PortalUserList', component: () => import('@/views/portal/PortalUserList.vue'), meta: { title: '门户用户' } },
                { path: 'portal/repairs', name: 'RepairRequestList', component: () => import('@/views/portal/RepairRequestList.vue'), meta: { title: '自助报修' } },
                { path: 'portal/ratings', name: 'ServiceRatingList', component: () => import('@/views/portal/ServiceRatingList.vue'), meta: { title: '服务评价' } },
                { path: 'sla/definitions', name: 'SlaDefinitionList', component: () => import('@/views/sla/SlaDefinitionList.vue'), meta: { title: 'SLA定义' } },
                { path: 'sla/tickets', name: 'SlaTicketList', component: () => import('@/views/sla/SlaTicketList.vue'), meta: { title: 'SLA监控' } },
                { path: 'notification/templates', name: 'NotificationTemplateList', component: () => import('@/views/notification/NotificationTemplateList.vue'), meta: { title: '通知模板' } },
                { path: 'notification/notifications', name: 'NotificationList', component: () => import('@/views/notification/NotificationList.vue'), meta: { title: '通知记录' } },
                { path: 'contract/contracts', name: 'ContractList', component: () => import('@/views/contract/ContractList.vue'), meta: { title: '合同管理' } },
                { path: 'contract/invoices', name: 'InvoiceList', component: () => import('@/views/contract/InvoiceList.vue'), meta: { title: '发票管理' } },
                { path: 'billing/rules', name: 'BillingRuleList', component: () => import('@/views/billing/BillingRuleList.vue'), meta: { title: '结算规则' } },
                { path: 'billing/bills', name: 'BillList', component: () => import('@/views/billing/BillList.vue'), meta: { title: '账单管理' } },
                { path: 'finance/accounts', name: 'AccountList', component: () => import('@/views/finance/AccountList.vue'), meta: { title: '会计科目' } },
                { path: 'finance/receivables', name: 'ReceivableList', component: () => import('@/views/finance/ReceivableList.vue'), meta: { title: '应收管理' } },
                { path: 'finance/payables', name: 'PayableList', component: () => import('@/views/finance/PayableList.vue'), meta: { title: '应付管理' } },
                { path: 'finance/payments', name: 'PaymentList', component: () => import('@/views/finance/PaymentList.vue'), meta: { title: '收付款管理' } },
                { path: 'finance/depreciations', name: 'DepreciationList', component: () => import('@/views/finance/DepreciationList.vue'), meta: { title: '设备折旧' } },
                { path: 'itsm/maintenance-plans', name: 'MaintenancePlanList', component: () => import('@/views/itsm/MaintenancePlanList.vue'), meta: { title: '保养计划' } },
                { path: 'itsm/maintenance-t17', name: 'MaintenanceT17List', component: () => import('@/views/itsm/MaintenanceT17List.vue'), meta: { title: '保养工单' } },
                { path: 'itsm/archives', name: 'ArchiveList', component: () => import('@/views/itsm/ArchiveList.vue'), meta: { title: '归档记录' } },
                { path: 'deposit/deposits', name: 'DepositList', component: () => import('@/views/deposit/DepositList.vue'), meta: { title: '押金管理' } },
                { path: 'deposit/details', name: 'DepositDetailList', component: () => import('@/views/deposit/DepositDetailList.vue'), meta: { title: '押金明细' } },
                { path: 'deposit/io', name: 'DepositIOList', component: () => import('@/views/deposit/DepositIOList.vue'), meta: { title: '押金流水' } },
                { path: 'master/asset-attrib', name: 'AssetAttribList', component: () => import('@/views/master/AssetAttribList.vue'), meta: { title: '资产属性' } },
                { path: 'attendance/records', name: 'AttendanceList', component: () => import('@/views/attendance/AttendanceList.vue'), meta: { title: '考勤记录' } },
                { path: 'attendance/summary', name: 'AttendanceCountList', component: () => import('@/views/attendance/AttendanceCountList.vue'), meta: { title: '考勤汇总' } },
                { path: 'inventory/limits', name: 'InventoryLimitList', component: () => import('@/views/inventory/InventoryLimitList.vue'), meta: { title: '库存预警' } },
                { path: 'inventory/prices', name: 'PriceList', component: () => import('@/views/inventory/PriceList.vue'), meta: { title: '价格管理' } },
                { path: 'inventory/adjust-prices', name: 'AdjustPriceList', component: () => import('@/views/inventory/AdjustPriceList.vue'), meta: { title: '调价记录' } },
                { path: 'mes/work-orders', name: 'WorkOrderList', component: () => import('@/views/mes/WorkOrderList.vue'), meta: { title: '生产工单' } },
                { path: 'mes/processes', name: 'ProcessDefList', component: () => import('@/views/mes/ProcessDefList.vue'), meta: { title: '工序定义' } },
                { path: 'mes/work-processes', name: 'WorkProcessList', component: () => import('@/views/mes/WorkProcessList.vue'), meta: { title: '工单工序' } },
                { path: 'mes/materials', name: 'MaterialConsumeList', component: () => import('@/views/mes/MaterialConsumeList.vue'), meta: { title: '物料消耗' } },
                { path: 'iot/connections', name: 'DeviceConnList', component: () => import('@/views/iot/DeviceConnList.vue'), meta: { title: '设备接入' } },
                { path: 'iot/data', name: 'DeviceDataList', component: () => import('@/views/iot/DeviceDataList.vue'), meta: { title: '设备数据' } },
                { path: 'iot/alert-rules', name: 'AlertRuleList', component: () => import('@/views/iot/AlertRuleList.vue'), meta: { title: '报警规则' } },
                { path: 'iot/alerts', name: 'AlertLogList', component: () => import('@/views/iot/AlertLogList.vue'), meta: { title: '报警记录' } },
                { path: 'system/transfers', name: 'TransferAccountList', component: () => import('@/views/system/TransferAccountList.vue'), meta: { title: '调拨科目' } },
                { path: 'reports/center', name: 'ReportCenter', component: () => import('@/views/reports/ReportCenter.vue'), meta: { title: '报表中心' } },
                { path: 'warehouse/overlost', name: 'OverLostList', component: () => import('@/views/warehouse/OverLostList.vue'), meta: { title: '盘盈盘亏' } },
{ path: 'warehouse/reports', name: 'StockReports', component: () => import('@/views/warehouse/StockReports.vue'), meta: { title: '仓库报表' } },
                { path: 'itsm/free-replace', name: 'FreeReplaceList', component: () => import('@/views/itsm/FreeReplaceList.vue'), meta: { title: '免费更换' } },
                { path: 'procurement/returns', name: 'ReturnPurchaseList', component: () => import('@/views/procurement/ReturnPurchaseList.vue'), meta: { title: '采购退货' } },
                { path: 'transactions/bills', name: 'AllTransactionsList', component: () => import('@/views/transactions/AllTransactionsList.vue'), meta: { title: '全模块查询' } },
                { path: 'transactions/transfer', name: 'TransferList', component: () => import('@/views/transactions/TransferList.vue'), meta: { title: '调拨流转' } },
                { path: 'mes/labels', name: 'LabelList', component: () => import('@/views/inventory/LabelList.vue'), meta: { title: '标签管理' } }
            ]
        },
        {
            path: '/:pathMatch(.*)*',
            redirect: '/'
        }
    ]
})

router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem('token')
    if (to.meta.requiresAuth !== false && !token) {
        next('/login')
    } else if (to.path === '/login' && token) {
        next('/')
    } else {
        next()
    }
})

export default router
