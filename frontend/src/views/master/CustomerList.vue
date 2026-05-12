<template>
    <div class="cust-page">
        <!-- 左侧客户分类 -->
        <div class="tree-panel">
            <el-card shadow="never">
                <template #header>
                    <div class="tree-header">
                        <span>客户分类</span>
                        <el-button type="primary" size="small" @click="openClassDialog()">新增</el-button>
                    </div>
                </template>
                <el-input v-model="treeFilterText" placeholder="输入关键字过滤" clearable size="small" style="margin-bottom:4px" />
                <div class="tree-actions">
                    <el-button link size="small" @click="expandAll">全部展开</el-button>
                    <el-button link size="small" @click="collapseAll">全部收缩</el-button>
                </div>
                <el-tree
                    ref="treeRef"
                    :data="treeData"
                    :props="{ label: 'class_nm', children: 'children' }"
                    node-key="class_cd"
                    highlight-current
                    :filter-node-method="filterTreeNode"
                    @node-click="onTreeClick"
                >
                    <template #default="{ data }">
                        <span class="tree-node" :class="{ 'is-invalid': data.useflg === '0' }">
                            <span class="tree-node-label">{{ data.class_nm }}</span>
                            <span class="tree-node-code">({{ data.class_cd }})</span>
                            <span v-if="data.useflg === '0'" class="tree-node-badge">无效</span>
                            <span class="tree-node-actions">
                                <el-button link size="small" @click.stop="openClassDialog(data)">编辑</el-button>
                                <el-button link size="small" type="danger" @click.stop="handleDeleteClass(data)">删除</el-button>
                            </span>
                        </span>
                    </template>
                </el-tree>
            </el-card>
        </div>

        <!-- 右侧客户表格 -->
        <div class="table-panel">
            <el-card>
                <template #header>
                    <div class="page-header">
                        <span>客户管理（共 {{ total }} 条）<template v-if="selectedClassCd"> — 分类: {{ selectedClassCd }}</template></span>
                        <div class="header-actions">
                            <el-input v-model="searchText" placeholder="搜索磁卡号或名称" clearable size="small" style="width:200px" @keyup.enter="onSearch" @clear="onSearch" />
                            <el-button type="primary" size="small" style="margin-left:8px" @click="openCustDialog()">新增客户</el-button>
                        </div>
                    </div>
                </template>
                <el-table :data="customers" v-loading="loading" stripe>
                    <el-table-column prop="cust_card" label="磁卡号" width="120" />
                    <el-table-column prop="cust_nm" label="名称" min-width="180" />
                    <el-table-column prop="class_cd" label="分类" width="80" />
                    <el-table-column prop="phone_no" label="电话" width="130" />
                    <el-table-column prop="contactor" label="联系人" width="100" />
                    <el-table-column label="操作" width="180" fixed="right">
                        <template #default="{ row }">
                            <el-button type="info" link size="small" @click="openDetail(row)">详情</el-button>
                            <el-button type="primary" link size="small" @click="openCustDialog(row)">编辑</el-button>
                            <el-button type="danger" link size="small" @click="handleDeleteCust(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:16px;justify-content:flex-end" />
            </el-card>
        </div>

        <!-- 客户新增/编辑弹窗 -->
        <el-dialog :title="custEditing ? '编辑客户' : '新增客户'" v-model="custDialogVisible" width="800px">
            <el-form :model="custForm" label-width="100px">
                <el-collapse v-model="editActiveGroups">
                    <el-collapse-item title="核心信息" name="core">
                        <el-row :gutter="12">
                            <el-col :span="12"><el-form-item label="名称" required><el-input v-model="custForm.cust_nm" /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="磁卡号" required><el-input v-model="custForm.cust_card" /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="简称"><el-input v-model="custForm.cust_anm" /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="全称"><el-input v-model="custForm.custrnm" /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="品牌代码"><el-input v-model="custForm.cust_brcd" /></el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                    <el-collapse-item title="分类与层级" name="classify">
                        <el-row :gutter="12">
                            <el-col :span="8"><el-form-item label="客户分类"><el-select v-model="custForm.class_cd" clearable filterable style="width:100%"><el-option v-for="c in classOptions" :key="c.class_cd" :label="`${c.class_cd} - ${c.class_nm}`" :value="c.class_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="区域编码"><el-input v-model="custForm.area_cd" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="管理单位"><el-input v-model="custForm.parentcd" /></el-form-item></el-col>
                            <el-col :span="6"><el-form-item label="负责区域"><el-select v-model="custForm.area" clearable style="width:100%"><el-option v-for="a in areas" :key="a.area_cd" :label="a.name || a.area_nm" :value="String(a.area_id)" /></el-select></el-form-item></el-col>
                            <el-col :span="6"><el-form-item label="环线位置"><el-select v-model="custForm.location" clearable style="width:100%"><el-option label="内环" value="1" /><el-option label="中环" value="2" /><el-option label="外环" value="3" /></el-select></el-form-item></el-col>
                        </el-row>
                        <el-row :gutter="12">
                            <el-col :span="8"><el-form-item label="国家"><el-select v-model="custForm.country_cd" clearable style="width:100%" @change="onCountryChange"><el-option v-for="c in countries" :key="c.country_cd" :label="c.country_nm" :value="c.country_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="省/直辖市"><el-select v-model="custForm.prvn_cd" clearable style="width:100%" @change="onProvinceChange"><el-option v-for="p in provinces" :key="p.prvn_cd" :label="p.prvn_nm" :value="p.prvn_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="城市/区"><el-select v-model="custForm.city_cd" clearable style="width:100%" @change="onCityChange"><el-option v-for="c in cities" :key="c.city_cd" :label="c.city_nm" :value="c.city_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="区县/街道"><el-select v-model="custForm.town_cd" clearable style="width:100%"><el-option v-for="t in towns" :key="t.town_cd" :label="t.town_nm" :value="t.town_cd" /></el-select></el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                    <el-collapse-item title="联系信息" name="contact">
                        <el-row :gutter="12">
                            <el-col :span="24"><el-form-item label="地址"><el-input v-model="custForm.address" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="电话"><el-input v-model="custForm.phone_no" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="联系人"><el-input v-model="custForm.contactor" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="邮编"><el-input v-model="custForm.zipcd" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="传真"><el-input v-model="custForm.faxno" /></el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                    <el-collapse-item title="财务信息" name="finance">
                        <el-row :gutter="12">
                            <el-col :span="12"><el-form-item label="税号"><el-input v-model="custForm.taxno" /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="银行名称"><el-input v-model="custForm.banknm" /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="银行账号"><el-input v-model="custForm.bankaccno" /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="预缴金额"><el-input v-model="custForm.yj_money" /></el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                    <el-collapse-item title="POS 配置" name="pos">
                        <el-row :gutter="12">
                            <el-col :span="6"><el-form-item label="设备数量"><el-input :model-value="custEditing ? String((custEditing as Record<string,unknown>).pos_count || custEditing.pos_n || '0') : '0'" disabled /></el-form-item></el-col>
                            <el-col :span="6"><el-form-item label="POS状态"><el-select v-model="custForm.posstatus" clearable style="width:100%"><el-option v-for="t in posStatuses" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="6"><el-form-item label="POS子状态"><el-input v-model="custForm.posstatus1" /></el-form-item></el-col>
                            <el-col :span="6"><el-form-item label="广告机"><el-input v-model="custForm.ad_video" /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="操作系统"><el-input v-model="custForm.opersystem" disabled /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="数据库"><el-input v-model="custForm.data_base" disabled /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="软件版本"><el-input v-model="custForm.soft_edition" disabled /></el-form-item></el-col>
                            <el-col :span="12"><el-form-item label="内核版本"><el-input v-model="custForm.systemcode" disabled /></el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                    <el-collapse-item title="通信" name="comm">
                        <el-row :gutter="12">
                            <el-col :span="8"><el-form-item label="通讯方式"><el-select v-model="custForm.comm_mode" clearable style="width:100%"><el-option v-for="t in commodes" :key="t.cmm_cd" :label="t.cmm_nm" :value="t.cmm_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="3G卡号"><el-input v-model="custForm.card3g" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="3G地址"><el-input v-model="custForm.adr3g" /></el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                    <el-collapse-item title="业务属性" name="biz">
                        <el-row :gutter="12">
                            <el-col :span="8"><el-form-item label="业务类型"><el-select v-model="custForm.busi_typ" clearable style="width:100%"><el-option v-for="t in businessTypes" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="门店属性"><el-select v-model="custForm.ppt_code" clearable style="width:100%"><el-option v-for="t in storeAttrs" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="客户等级"><el-input v-model="custForm.levels" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="要货方式"><el-input v-model="custForm.ordertype" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="合同标志"><el-input v-model="custForm.is_contract" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="支付方式"><el-select v-model="custForm.zf_type" clearable style="width:100%"><el-option v-for="t in payTypes" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                        </el-row>
                        <el-row :gutter="12">
                            <el-col :span="8"><el-form-item label="经理联系人"><el-input v-model="custForm.jl_contactor" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="经理电话"><el-input v-model="custForm.jl_phoneno" /></el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                    <el-collapse-item title="生命周期" name="life">
                        <el-row :gutter="12">
                            <el-col :span="8"><el-form-item label="客户状态"><el-select v-model="custForm.customer_status" clearable style="width:100%"><el-option v-for="t in csOptions" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="设备状态"><el-select v-model="custForm.s_status" clearable style="width:100%"><el-option v-for="t in deviceStatuses" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="首次开通"><el-input v-model="custForm.opendate" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="最近更换"><el-input v-model="custForm.replacedate" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="来源类型"><el-select v-model="custForm.source_type" clearable style="width:100%"><el-option v-for="t in srcOptions" :key="t.code_cd" :label="t.code_nm" :value="t.code_cd" /></el-select></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="预计划ID"><el-input v-model="custForm.preplan_id" /></el-form-item></el-col>
                            <el-col :span="8"><el-form-item label="有效标志">
                                <el-select v-model="custForm.useflg" style="width:100%"><el-option label="有效" value="1" /><el-option label="无效" value="0" /></el-select>
                            </el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                    <el-collapse-item title="其他" name="other">
                        <el-row :gutter="12">
                            <el-col :span="24"><el-form-item label="备注"><el-input v-model="custForm.backup" type="textarea" /></el-form-item></el-col>
                        </el-row>
                    </el-collapse-item>
                </el-collapse>
            </el-form>
            <template #footer>
                <el-button @click="custDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSaveCust" :loading="custSaving">保存</el-button>
            </template>
        </el-dialog>

        <!-- 客户详情弹窗 -->
        <el-dialog title="客户详情" v-model="detailVisible" width="750px">
            <template v-if="detailRow">
                <el-divider content-position="left">核心信息</el-divider>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="编码">{{ detailRow.cust_cd }}</el-descriptions-item>
                    <el-descriptions-item label="名称" :span="2">{{ detailRow.cust_nm }}</el-descriptions-item>
                    <el-descriptions-item label="磁卡号">{{ detailRow.cust_card || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="简称">{{ detailRow.cust_anm || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="全称">{{ detailRow.custrnm || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="品牌代码">{{ detailRow.cust_brcd || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="状态">
                        <el-tag :type="detailRow.useflg === '0' ? 'danger' : 'success'" size="small">{{ detailRow.useflg === '0' ? '无效' : '有效' }}</el-tag>
                    </el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">分类与层级</el-divider>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="客户分类">{{ (detailRow as Record<string,unknown>).class_cd_nm || detailRow.class_cd || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="区域编码">{{ detailRow.area_cd || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="管理单位">{{ (detailRow as Record<string,unknown>).parentcd_nm || detailRow.parentcd || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="负责区域">{{ (detailRow as Record<string,unknown>).area_nm || detailRow.area || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="环线位置">{{ (detailRow as Record<string,unknown>).location_nm || detailRow.location || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="国家">{{ (detailRow as Record<string,unknown>).country_nm || detailRow.country_cd || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="省/直辖市">{{ (detailRow as Record<string,unknown>).prvn_nm || detailRow.prvn_cd || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="城市/区">{{ (detailRow as Record<string,unknown>).city_nm || detailRow.city_cd || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="区县/街道">{{ (detailRow as Record<string,unknown>).town_nm || detailRow.town_cd || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">联系信息</el-divider>
                <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="地址" :span="2">{{ detailRow.address || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="电话">{{ detailRow.phone_no || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="联系人">{{ detailRow.contactor || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="邮编">{{ detailRow.zipcd || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="传真">{{ detailRow.faxno || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">财务信息</el-divider>
                <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="税号">{{ detailRow.taxno || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="开户银行">{{ detailRow.banknm || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="银行账号">{{ detailRow.bankaccno || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="预缴金额">{{ detailRow.yj_money || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">POS 配置</el-divider>
                <el-table :data="custDevices" size="small" max-height="250" stripe v-if="custDevices.length" style="margin-bottom:8px">
                    <el-table-column prop="eid" label="设备 SN" width="150" />
                    <el-table-column prop="item_nm" label="商品名" min-width="140" />
                    <el-table-column prop="item_cd" label="物料编码" width="100" />
                    <el-table-column label="状态" width="60">
                        <template #default="{ row }">
                            <el-tag :type="row.useflg === '0' ? 'danger' : 'success'" size="small">{{ row.useflg === '0' ? '无效' : '有效' }}</el-tag>
                        </template>
                    </el-table-column>
                </el-table>
                <div v-else style="color:#909399;padding:4px 0">该客户暂无设备关联</div>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="设备数量">{{ (detailRow as Record<string,unknown>).pos_count || detailRow.pos_n || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="POS状态">{{ (detailRow as Record<string,unknown>).posstatus_nm || detailRow.posstatus || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="POS子状态">{{ detailRow.posstatus1 || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="广告机">{{ detailRow.ad_video === '1' ? '是' : '否' }}</el-descriptions-item>
                    <el-descriptions-item label="操作系统" :span="2">{{ detailRow.opersystem || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="数据库">{{ detailRow.data_base || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="软件版本">{{ detailRow.soft_edition || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="内核版本">{{ detailRow.systemcode || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">通信</el-divider>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="通讯方式">{{ (detailRow as Record<string,unknown>).comm_mode_nm || detailRow.comm_mode || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="3G卡号">{{ detailRow.card3g || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="3G地址">{{ detailRow.adr3g || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">业务属性</el-divider>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="业务类型">{{ (detailRow as Record<string,unknown>).busi_typ_nm || detailRow.busi_typ || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="门店属性">{{ (detailRow as Record<string,unknown>).ppt_code_nm || detailRow.ppt_code || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="客户等级">{{ detailRow.levels || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="要货方式">{{ detailRow.ordertype || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="合同标志">{{ detailRow.is_contract || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="支付方式">{{ (detailRow as Record<string,unknown>).zf_type_nm || detailRow.zf_type || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="经理联系人">{{ detailRow.jl_contactor || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="经理电话">{{ detailRow.jl_phoneno || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">生命周期 & 其他</el-divider>
                <el-descriptions :column="3" border size="small">
                    <el-descriptions-item label="客户状态">{{ (detailRow as Record<string,unknown>).customer_status_nm || detailRow.customer_status || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="首次开通">{{ detailRow.opendate || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="最近更换">{{ detailRow.replacedate || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="来源类型">{{ (detailRow as Record<string,unknown>).source_type_nm || detailRow.source_type || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="预计划单号">{{ detailRow.preplan_id || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="设备状态">{{ (detailRow as Record<string,unknown>).s_status_nm || detailRow.s_status || '-' }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="left">备注</el-divider>
                <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="备注">{{ detailRow.backup || '-' }}</el-descriptions-item>
                </el-descriptions>
            </template>
            <template #footer>
                <el-button @click="detailVisible = false">关闭</el-button>
            </template>
        </el-dialog>

        <!-- 分类新增/编辑弹窗 -->
        <el-dialog :title="classEditing ? '编辑分类' : '新增分类'" v-model="classDialogVisible" width="500px">
            <el-form :model="classForm" label-width="80px">
                <el-form-item label="编码" required>
                    <el-input v-model="classForm.class_cd" :disabled="!!classEditing" />
                </el-form-item>
                <el-form-item label="名称" required>
                    <el-input v-model="classForm.class_nm" />
                </el-form-item>
                <el-form-item label="上级分类">
                    <el-select v-model="classForm.parent_cd" clearable filterable style="width:100%" placeholder="空 = 根分类">
                        <el-option v-for="c in classOptions" :key="c.class_cd" :label="`${c.class_cd} - ${c.class_nm}`" :value="c.class_cd" />
                    </el-select>
                </el-form-item>
                <el-form-item label="状态">
                    <el-select v-model="classForm.useflg" style="width:100%">
                        <el-option label="有效" value="1" />
                        <el-option label="无效" value="0" />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="classDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSaveClass" :loading="classSaving">保存</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { watch } from 'vue'
import type { ElTree } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
    fetchCustomers, createCustomer, updateCustomer, deleteCustomer,
    fetchCustClassTree, fetchCustClasses,
    createCustClass, updateCustClass, deleteCustClass,
    fetchSyscodes, fetchAreas, fetchCommodes,
    fetchCountries, fetchProvinces, fetchCities, fetchTowns,
} from '@/api/master'
import type { CustClassNode, CustRecord, CustPage } from '@/api/master'

// ---- 分类树 ----
const treeData = ref<CustClassNode[]>([])
const treeFilterText = ref('')
const treeRef = ref<InstanceType<typeof ElTree>>()
const selectedClassCd = ref('')
const classOptions = ref<{ class_cd: string; class_nm: string; parent_cd: string }[]>([])

// ---- 客户列表 ----
const customers = ref<CustRecord[]>([])
const loading = ref(false)
const searchText = ref('')
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

// ---- 客户详情 ----
const detailVisible = ref(false)
const detailRow = ref<CustRecord | null>(null)
const custDevices = ref<Record<string,unknown>[]>([])

// ---- 客户弹窗 ----
const custDialogVisible = ref(false)
const custEditing = ref<CustRecord | null>(null)
const custSaving = ref(false)
const editActiveGroups = ref<string[]>(['core'])
const custForm = reactive<Record<string, string>>({
    cust_card: '', cust_nm: '', cust_anm: '', custrnm: '', store_cd: '', cust_brcd: '',
    class_cd: '', area_cd: '', parentcd: '',
    address: '', phone_no: '', contactor: '', zipcd: '', faxno: '',
    country_cd: '', prvn_cd: '', city_cd: '', town_cd: '',
    taxno: '', banknm: '', bankaccno: '', yj_money: '',
    pos_n: '', posstatus: '', posstatus1: '', ad_video: '', opersystem: '', data_base: '', soft_edition: '', systemcode: '',
    card3g: '', adr3g: '',
    busi_typ: '', ppt_code: '', levels: '', ordertype: '', is_contract: '', zf_type: '', comm_mode: '',
    customer_status: '', opendate: '', replacedate: '', source_type: '', preplan_id: '', useflg: '1',
    jl_contactor: '', jl_phoneno: '', area: '', location: '', s_status: '', backup: '',
})

// ---- 码表数据 ----
const businessTypes = ref<{ code_cd: string; code_nm: string }[]>([])
const storeAttrs = ref<{ code_cd: string; code_nm: string }[]>([])
const payTypes = ref<{ code_cd: string; code_nm: string }[]>([])
const areas = ref<{ area_cd: string; area_nm: string; area_id: number; name: string }[]>([])
const commodes = ref<{ cmm_cd: string; cmm_nm: string }[]>([])
const posStatuses = ref<{ code_cd: string; code_nm: string }[]>([])
const deviceStatuses = ref<{ code_cd: string; code_nm: string }[]>([])
const csOptions = ref<{ code_cd: string; code_nm: string }[]>([])
const srcOptions = ref<{ code_cd: string; code_nm: string }[]>([])
const countries = ref<{ country_cd: string; country_nm: string }[]>([])
const provinces = ref<{ prvn_cd: string; prvn_nm: string }[]>([])
const cities = ref<{ city_cd: string; city_nm: string }[]>([])
const towns = ref<{ town_cd: string; town_nm: string }[]>([])

// ---- 分类弹窗 ----
const classDialogVisible = ref(false)
const classEditing = ref<CustClassNode | null>(null)
const classSaving = ref(false)
const classForm = reactive({ class_cd: '', class_nm: '', parent_cd: '', useflg: '1' })

watch(page, () => loadCustomers())
watch(perPage, () => { page.value = 1; loadCustomers() })
watch(treeFilterText, (v) => treeRef.value?.filter(v))

onMounted(async () => {
    await Promise.all([loadTree(), loadClassOptions(), loadLookups(), initCities()])
    loadCustomers()
})

async function onCountryChange() {
    custForm.prvn_cd = ''; custForm.city_cd = ''; custForm.town_cd = ''
    cities.value = []; towns.value = []
}

async function onProvinceChange() {
    custForm.city_cd = ''; custForm.town_cd = ''
    towns.value = []
    if (custForm.prvn_cd) {
        const res = await fetchCities(custForm.prvn_cd)
        cities.value = res.data || []
    } else { cities.value = [] }
}

// 初始化加载上海区县（默认省份09=上海）
async function initCities() {
    const res = await fetchCities('09')
    cities.value = res.data || []
}

async function autoMatchCity() {
    // 根据客户分类名称匹配上海区县
    const className = classOptions.value.find(c => c.class_cd === custForm.class_cd)?.class_nm || ''
    const mappings: Record<string, string> = {
        '长宁': '0110', '徐汇': '0125', '浦东': '0121', '沪东': '0121',
        '黄浦': '0114', '静安': '0117', '普陀': '0120', '虹口': '0113',
        '杨浦': '0126', '宝山': '0109', '闵行': '0128', '嘉定': '0115',
        '金山': '0116', '松江': '0124', '青浦': '0122', '奉贤': '0112',
        '崇明': '0111', '闸北': '0127', '卢湾': '0118', '南汇': '0119',
    }
    for (const [key, cityCd] of Object.entries(mappings)) {
        if (className.includes(key)) {
            custForm.city_cd = cityCd
            // 加载该城市下的区县
            const res = await fetchCities('09')
            cities.value = res.data || []
            const tres = await fetchTowns(cityCd)
            towns.value = tres.data || []
            return
        }
    }
    // 未匹配则加载上海全部区
    const res = await fetchCities('09')
    cities.value = res.data || []
    towns.value = []
}

async function onCityChange() {
    custForm.town_cd = ''
    if (custForm.city_cd) {
        const res = await fetchTowns(custForm.city_cd)
        towns.value = res.data || []
    } else { towns.value = [] }
}

async function loadLookups() {
    try {
        const [bt, yb, zf, ps, ar, cm, ct, pv] = await Promise.all([
            fetchSyscodes('BT'), fetchSyscodes('YB'), fetchSyscodes('ZF'),
            fetchSyscodes('PS'),
            fetchAreas(), fetchCommodes(),
            fetchCountries(), fetchProvinces(),
        ])
        businessTypes.value = bt.data || []
        storeAttrs.value = yb.data || []
        payTypes.value = zf.data || []
        posStatuses.value = ps.data || []
        const ss = await fetchSyscodes('SS')
        deviceStatuses.value = ss.data || []
        const cs = await fetchSyscodes('CS')
        csOptions.value = cs.data || []
        const src = await fetchSyscodes('SRC')
        srcOptions.value = src.data || []
        areas.value = ar.data || []
        commodes.value = cm.data || []
        countries.value = ct.data || []
        provinces.value = pv.data || []
    } catch { /* 编辑下拉用，非关键 */ }
}

// ---- 分类树 ----

async function loadTree() {
    try {
        const res = await fetchCustClassTree()
        treeData.value = res.data || []
    } catch {
        ElMessage.error('加载分类树失败')
    }
}

async function loadClassOptions() {
    try {
        const res = await fetchCustClasses()
        classOptions.value = (res.data || []) as { class_cd: string; class_nm: string; parent_cd: string }[]
    } catch { /* */ }
}

function filterTreeNode(value: string, data: CustClassNode): boolean {
    if (!value) return true
    const kw = value.toLowerCase()
    return data.class_nm.toLowerCase().includes(kw) || data.class_cd.toLowerCase().includes(kw)
}

function expandAll() {
    const nodes = (treeRef.value as unknown as { store: { nodesMap: Record<string, { expand: () => void }> } })?.store?.nodesMap
    if (nodes) Object.values(nodes).forEach((n) => n.expand?.())
}

function collapseAll() {
    const nodes = (treeRef.value as unknown as { store: { nodesMap: Record<string, { collapse: () => void }> } })?.store?.nodesMap
    if (nodes) Object.values(nodes).forEach((n) => n.collapse?.())
}

function onTreeClick(node: CustClassNode) {
    selectedClassCd.value = node.class_cd
    searchText.value = ''
    page.value = 1
    loadCustomers()
}

// ---- 分类 CRUD ----

function openClassDialog(data?: CustClassNode) {
    if (data) {
        classEditing.value = data
        classForm.class_cd = data.class_cd || ''
        classForm.class_nm = data.class_nm || ''
        classForm.parent_cd = (data as unknown as Record<string,string>).parent_cd || ''
        classForm.useflg = data.useflg !== undefined ? data.useflg : '1'
    } else {
        classEditing.value = null
        classForm.class_cd = selectedClassCd.value || ''
        classForm.class_nm = ''
        classForm.parent_cd = selectedClassCd.value || ''
        classForm.useflg = '1'
    }
    classDialogVisible.value = true
}

async function handleSaveClass() {
    if (!classForm.class_cd || !classForm.class_nm) {
        ElMessage.warning('编码和名称为必填项')
        return
    }
    classSaving.value = true
    try {
        const payload: Record<string, string> = { class_nm: classForm.class_nm, useflg: classForm.useflg }
        if (classForm.parent_cd) payload.parent_cd = classForm.parent_cd
        if (classEditing.value) {
            await updateCustClass(classEditing.value.class_cd, payload)
            ElMessage.success('更新成功')
        } else {
            payload.class_cd = classForm.class_cd
            await createCustClass(payload)
            ElMessage.success('创建成功')
        }
        classDialogVisible.value = false
        await Promise.all([loadTree(), loadClassOptions()])
    } finally { classSaving.value = false }
}

async function handleDeleteClass(data: CustClassNode) {
    try {
        await ElMessageBox.confirm(`确定删除分类 ${data.class_cd}（${data.class_nm}）？`, '确认删除')
        await deleteCustClass(data.class_cd)
        ElMessage.success('已删除')
        if (selectedClassCd.value === data.class_cd) selectedClassCd.value = ''
        await Promise.all([loadTree(), loadClassOptions()])
        loadCustomers()
    } catch (e: unknown) {
        if (e !== 'cancel') ElMessage.error('删除失败')
    }
}

// ---- 客户列表 ----

async function loadCustomers() {
    loading.value = true
    try {
        const params: { page: string; per_page: string; class_cd?: string; search?: string } = {
            page: String(page.value),
            per_page: String(perPage.value),
        }
        if (searchText.value) {
            params.search = searchText.value
        } else if (selectedClassCd.value) {
            params.class_cd = selectedClassCd.value
        }
        const res = await fetchCustomers(params)
        const data = res.data as CustPage
        customers.value = data.items || []
        total.value = data.total || 0
    } catch {
        ElMessage.error('加载客户列表失败')
    } finally { loading.value = false }
}

function onSearch() {
    page.value = 1
    loadCustomers()
}

// ---- 客户详情 ----

async function openDetail(row: CustRecord) {
    detailRow.value = row; detailVisible.value = true; custDevices.value = []
    try {
        const token = localStorage.getItem('token')
        const resp = await fetch(`/api/v1/assets?cust_cd=${row.cust_cd}&per_page=100`, { headers: { Authorization: `Bearer ${token}` } })
        if (resp.ok) { const d = await resp.json(); custDevices.value = d.data?.items || [] }
    } catch { /* */ }
}

// ---- 客户 CRUD ----

function openCustDialog(row?: CustRecord) {
    if (row) {
        custEditing.value = row
        for (const key of Object.keys(custForm)) {
            (custForm as Record<string,string>)[key] = (row as Record<string,unknown>)[key] as string || ''
        }
    } else {
        custEditing.value = null
        for (const key of Object.keys(custForm)) {
            (custForm as Record<string,string>)[key] = ''
        }
        custForm.class_cd = selectedClassCd.value || ''
        custForm.parentcd = selectedClassCd.value || ''
        custForm.useflg = '1'
        custForm.customer_status = 'ACTIVE'
        custForm.source_type = 'MANUAL'
        custForm.country_cd = '191'   // 默认中国
        custForm.prvn_cd = '09'       // 默认上海
        autoMatchCity()
    }
    editActiveGroups.value = ['core']
    custDialogVisible.value = true
}

async function handleSaveCust() {
    if (!custForm.cust_nm || !custForm.cust_card) {
        ElMessage.warning('名称和磁卡号为必填项')
        return
    }
    custSaving.value = true
    try {
        const payload: Record<string, string> = {}
        const skipKeys = ['opersystem', 'data_base', 'soft_edition', 'systemcode']  // 软件配置由设备监控更新
        for (const key of Object.keys(custForm)) {
            if (skipKeys.includes(key)) continue
            const v = (custForm as Record<string,string>)[key]
            if (v !== '' && v !== undefined && v !== null) payload[key] = v
        }
        // 确保 useflg 有默认值
        if (!payload.useflg) payload.useflg = '1'
        if (custEditing.value) {
            await updateCustomer(custEditing.value.cust_cd, payload)
            ElMessage.success('更新成功')
        } else {
            await createCustomer(payload)
            ElMessage.success('创建成功')
        }
        custDialogVisible.value = false
        loadCustomers()
    } finally { custSaving.value = false }
}

async function handleDeleteCust(row: CustRecord) {
    try {
        await ElMessageBox.confirm(`确定删除客户 ${row.cust_card || row.cust_cd}（${row.cust_nm}）？`, '确认删除')
        await deleteCustomer(row.cust_cd)
        ElMessage.success('已删除')
        loadCustomers()
    } catch (e: unknown) {
        if (e !== 'cancel') ElMessage.error('删除失败')
    }
}
</script>

<style lang="scss" scoped>
.cust-page {
    display: flex; gap: 12px; padding: 16px; height: calc(100vh - 80px);
}
.tree-panel {
    width: 280px; flex-shrink: 0; overflow-y: auto;
    :deep(.el-card__body) { padding: 8px; }
    :deep(.el-tree-node__content) { height: auto; min-height: 28px; padding-right: 4px; }
}
.tree-header { display: flex; justify-content: space-between; align-items: center; }
.tree-actions { display: flex; gap: 4px; margin-bottom: 4px; }
.tree-node {
    display: flex; align-items: center; flex: 1; min-width: 0; font-size: 13px; overflow: hidden;
    .tree-node-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 1; }
    .tree-node-code { color: #909399; font-size: 11px; flex-shrink: 0; margin-left: 2px; }
    .tree-node-badge { color: #f56c6c; font-size: 10px; margin-left: 4px; flex-shrink: 0; }
    .tree-node-actions { display: none; flex-shrink: 0; margin-left: 2px; }
    .tree-node-actions .el-button { padding: 0 2px; font-size: 12px; height: auto; min-height: auto; }
    &:hover .tree-node-actions { display: flex; }
    &.is-invalid {
        .tree-node-label { color: #c0c4cc; text-decoration: line-through; }
        .tree-node-code { color: #c0c4cc; }
    }
}
.table-panel { flex: 1; overflow-y: auto; min-width: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.header-actions { display: flex; align-items: center; }
</style>
