<template>
  <div class="plan-page">
    <div class="page-header">
      <h2>预计划管理</h2>
      <el-button type="primary" @click="openCreate">＋ 新建预计划</el-button>
    </div>
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="search-bar">
        <div class="field"><label>计划单号</label><el-input v-model="searchPlanno" placeholder="输入单号" size="small" style="width:130px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>磁卡号</label><el-input v-model="searchCustcard" placeholder="磁卡号模糊" size="small" style="width:130px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>客户名称</label><el-input v-model="searchCustNm" placeholder="输入客户" size="small" style="width:130px" clearable @keyup.enter="onSearch" /></div>
        <div class="field"><label>计划类型</label><el-select v-model="searchPlantyp" size="small" style="width:110px" clearable>
          <el-option label="新机开通" value="00" /><el-option label="设备变更" value="10" />
          <el-option label="旧机翻新" value="20" /><el-option label="设备取回" value="30" />
          <el-option label="门店关闭" value="40" /></el-select></div>
        <div class="field"><label>状态</label><el-select v-model="searchStatus" size="small" style="width:110px" clearable>
          <el-option label="计划中" value="00" /><el-option label="计划完成" value="01" />
          <el-option label="分派中" value="02" /><el-option label="实施完成" value="03" />
          <el-option label="实施中" value="04" /><el-option label="计划退回" value="08" />
          <el-option label="计划作废" value="09" /></el-select></div>
        <div class="field"><label>计划日期</label>
          <el-date-picker v-model="searchDateFrom" type="date" placeholder="开始" size="small" style="width:120px" value-format="YYYY-MM-DD" clearable />
          <span style="margin:0 4px">至</span>
          <el-date-picker v-model="searchDateTo" type="date" placeholder="结束" size="small" style="width:120px" value-format="YYYY-MM-DD" clearable />
        </div>
        <div class="field"><el-checkbox v-model="searchServeStatus" true-value="01" false-value="">仅呼出中</el-checkbox></div>
        <el-button type="primary" size="small" @click="onSearch">查询</el-button>
        <el-button size="small" @click="onReset">重置</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="plans" v-loading="loading" stripe size="small" highlight-current-row>
        <el-table-column prop="planno" label="计划单号" width="110" />
        <el-table-column prop="custnm" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="custcard" label="磁卡号" width="100" />
        <el-table-column prop="contactor" label="联系人" width="80" />
        <el-table-column prop="phoneno" label="电话" width="120" />
        <el-table-column label="计划类型" width="80"><template #default="{row}">{{ plLabel(row.plantyp) }}</template></el-table-column>
        <el-table-column label="业务类型" width="80"><template #default="{row}">{{ bsLabel(row.busityp) }}</template></el-table-column>
        <el-table-column label="租赁/购买" width="70"><template #default="{row}"><el-tag :type="row.is_rent==='Y'?'success':'info'" size="small">{{ row.is_rent==='Y'?'租赁':'购买' }}</el-tag></template></el-table-column>
        <el-table-column label="机型" width="80"><template #default="{row}">{{ row.pos_item || '-' }}</template></el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{row}"><el-tag :type="statusTag(row.plan_status)" size="small">{{ statusLabel(row.plan_status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="客户" width="70" align="center">
          <template #default="{row}"><el-tag :type="custTag(row)" size="small">{{ custLabel(row) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="deposit" label="押金" width="100" align="right"><template #default="{row}">{{ row.deposit ? '¥'+Number(row.deposit).toLocaleString() : '-' }}</template></el-table-column>
        <el-table-column prop="gendate" label="日期" width="90" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{row}">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="row.plan_status==='00'" link type="info" size="small" @click="doRequestServe(row)">请求呼出</el-button>
            <el-button v-if="row.plan_status==='00'" link type="success" size="small" @click="doTransition(row,'02')">确认</el-button>
            <el-button v-if="row.plan_status==='02'" link type="warning" size="small" @click="doImplement(row)">实施</el-button>
            <el-button v-if="row.plan_status==='04'" link type="primary" size="small" @click="doOutbound(row)">出库</el-button>
            <el-button v-if="row.plan_status==='04'" link type="success" size="small" @click="doComplete(row)">完成</el-button>
            <el-button v-if="vCan(row)" link type="danger" size="small" @click="doVoid(row)">作废</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end" />
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="预计划详情" size="780px">
      <template v-if="detail">
        <el-tabs v-model="detailTab">
          <el-tab-pane label="预计划单" name="info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="计划单号">{{ detail.planno }}</el-descriptions-item>
              <el-descriptions-item label="状态"><el-tag :type="statusTag(detail.plan_status)" size="small">{{ statusLabel(detail.plan_status) }}</el-tag></el-descriptions-item>
              <el-descriptions-item label="客户名称">{{ detail.custnm }}</el-descriptions-item>
              <el-descriptions-item label="客户实名">{{ detail.custrnm || '-' }}</el-descriptions-item>
              <el-descriptions-item label="客户编码">{{ detail.custcd || '-' }}</el-descriptions-item>
              <el-descriptions-item label="磁卡号">{{ detail.custcard || '-' }}</el-descriptions-item>
              <el-descriptions-item label="新磁卡号" v-if="detail.new_custcard">{{ detail.new_custcard }}</el-descriptions-item>
              <el-descriptions-item label="新客户" v-if="detail.new_custcd">{{ detail.new_custcd }} {{ detail.new_custnm || '' }}</el-descriptions-item>
              <el-descriptions-item label="地址">{{ detail.address || '-' }}</el-descriptions-item>
              <el-descriptions-item label="新地址" v-if="detail.new_address">{{ detail.new_address }}</el-descriptions-item>
              <el-descriptions-item label="联系人">{{ detail.contactor || '-' }}</el-descriptions-item>
              <el-descriptions-item label="电话">{{ detail.phoneno || '-' }}</el-descriptions-item>
              <el-descriptions-item label="经理">{{ detail.jl_contactor || '-' }}</el-descriptions-item>
              <el-descriptions-item label="经理电话">{{ detail.jl_phoneno || '-' }}</el-descriptions-item>
              <el-descriptions-item label="计划类型">{{ plLabel(detail.plantyp) }}</el-descriptions-item>
              <el-descriptions-item label="业务类型">{{ bsLabel(detail.busityp || '') || detail.busityp || '-' }}</el-descriptions-item>
              <el-descriptions-item label="设备来源">{{ detail.pos_from || '-' }}</el-descriptions-item>
              <el-descriptions-item label="机型">{{ detail.pos_item || '-' }}</el-descriptions-item>
              <el-descriptions-item label="押金">{{ detail.deposit ? '¥'+Number(detail.deposit).toLocaleString() : '-' }}</el-descriptions-item>
              <el-descriptions-item label="租赁">{{ detail.is_rent==='Y'?'租赁':'购买' }}</el-descriptions-item>
              <el-descriptions-item label="合同">{{ detail.is_contract==='1'?'是':'否' }}</el-descriptions-item>
              <el-descriptions-item label="运营类型">{{ detail.yun_type || '-' }}</el-descriptions-item>
              <el-descriptions-item label="下游单据">{{ detail.imple_billid || '未生成' }}</el-descriptions-item>
              <el-descriptions-item label="出库标志">{{ detail.is_outflag==='1'?'已出库':'未出库' }}</el-descriptions-item>
              <el-descriptions-item label="服务工程师">{{ detail.serve_ercd || '-' }}</el-descriptions-item>
              <el-descriptions-item label="创建日期">{{ detail.gendate || '-' }}</el-descriptions-item>
              <el-descriptions-item label="操作员">{{ detail.opercd || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <el-tab-pane label="呼出记录" name="serve">
            <el-table :data="serveRecords" size="small" v-loading="serveLoading" empty-text="暂无呼出记录">
              <el-table-column prop="servetyp" label="类型" width="80"><template #default="{row}">{{ ['客户确认','预计划呼出','实施任务'][Number(row.servetyp)]||row.servetyp }}</template></el-table-column>
              <el-table-column prop="serve_task" label="任务" min-width="100" show-overflow-tooltip />
              <el-table-column prop="serve_back" label="呼出结果" width="80"><template #default="{row}"><el-tag :type="({Y:'success',N:'danger',O:'warning'} as Record<string, string>)[row.serve_back as string]||'info'" size="small">{{ ({Y:'同意',N:'不同意',O:'未接通'} as Record<string, string>)[row.serve_back as string]||row.serve_back||'-' }}</el-tag></template></el-table-column>
              <el-table-column prop="serve_mark" label="客户反馈" min-width="120" show-overflow-tooltip />
              <el-table-column prop="commmode" label="通讯方式" width="80" />
              <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='01'?'success':row.status==='09'?'danger':'info'" size="small">{{ ({'00':'待呼出','01':'已呼出','09':'已作废'} as Record<string, string>)[row.status as string]||row.status }}</el-tag></template></el-table-column>
              <el-table-column prop="gendate" label="日期" width="90" />
              <el-table-column prop="genercd" label="操作员" width="70" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="当前设备" name="device">
            <el-table :data="custDevices" size="small" v-loading="deviceLoading" empty-text="暂无设备信息"
              row-key="_id" :tree-props="{ children: 'children', hasChildren: 'hasChildren' }" :indent="24" default-expand-all>
              <el-table-column prop="eid" label="EID" width="130" />
              <el-table-column label="物料编码/名称" min-width="220">
                <template #default="{row}">
                  <span>{{ row.itemcd }}</span>
                  <span style="color:#909399;margin-left:8px">{{ row.itemnm || '' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="80">
                <template #default="{row}">
                  <el-tag v-if="row.isPos" size="small" :type="row.useflg==='1'?'success':'danger'">{{ row.useflg==='1'?'在用':'已失效' }}</el-tag>
                  <el-tag v-else size="small" :type="row.useflg==='1'?'success':'danger'">{{ row.useflg==='1'?'有效':'失效' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="upddate" label="更新日期" width="100" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="历史设备" name="history">
            <el-table :data="deviceHistory" size="small" v-loading="historyLoading" empty-text="暂无历史记录">
              <el-table-column prop="eid" label="设备EID" width="130" />
              <el-table-column prop="itemcd" label="物料编码" width="80" />
              <el-table-column prop="itemnm" label="物料名称" min-width="120" show-overflow-tooltip />
              <el-table-column prop="sysinfo" label="系统信息" width="100" show-overflow-tooltip />
              <el-table-column prop="softinfo" label="软件版本" width="100" show-overflow-tooltip />
              <el-table-column prop="posinfo" label="POS信息" width="100" show-overflow-tooltip />
              <el-table-column label="状态" width="70"><template #default="{row}"><el-tag size="small" :type="row.useflg==='1'?'success':'danger'">{{ row.useflg==='1'?'有效':'失效' }}</el-tag></template></el-table-column>
              <el-table-column prop="upddate" label="更新日期" width="90" />
            </el-table>
          </el-tab-pane>
        </el-tabs>

      </template>
    </el-drawer>

    <!-- 新建/编辑对话框 -->
    <el-dialog :title="isEdit?'编辑预计划':'新建预计划'" v-model="dialogVisible" width="860px" top="2vh">
      <el-form :model="form" label-width="90px" size="default">
        <!-- 一、简要信息 -->
        <el-divider content-position="left">简要信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="计划类型"><el-select v-model="form.plantyp" style="width:100%" @change="onPlantypChange"><el-option v-for="o in plOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="预计划单号"><el-input :model-value="form.planno" disabled placeholder="保存后自动生成"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="单据状态"><el-select v-model="form.status" disabled style="width:100%"><el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item></el-col>
        </el-row>
        <!-- 磁卡号变更子类型提示(plantyp=10 时根据填写的源字段实时判定 CK/BG/BQ) -->
        <el-row v-if="form.plantyp==='10'" :gutter="20">
          <el-col :span="24">
            <el-form-item label="变更子类型">
              <el-tag :type="changeSubType.tagType" size="default">
                {{ changeSubType.code }} - {{ changeSubType.label }}
              </el-tag>
              <span class="change-subtype-hint" style="margin-left:12px;color:#909399;font-size:12px">
                {{ changeSubType.hint }}
              </span>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 二、客户信息 -->
        <el-divider content-position="left">客户信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="磁卡号"><el-input v-model="form.custcard" placeholder="点击选择已有客户" readonly @click="openCustPicker"><template #append><el-button @click="openCustPicker">选择</el-button></template></el-input></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="客户编码"><el-input v-model="form.custcd" placeholder="编码"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="客户名称"><el-input v-model="form.custnm" placeholder="名称"/></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="地址"><el-input v-model="form.address" placeholder="地址"/></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="联系人"><el-input v-model="form.contactor"/></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="电话"><el-input v-model="form.phoneno"/></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="客户经理"><el-input v-model="form.jl_contactor"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="经理电话"><el-input v-model="form.jl_phoneno"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="客户类型"><el-select v-model="form.busityp" filterable clearable style="width:100%"><el-option v-for="o in busitypOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="有限公司"><el-select v-model="form.classcd" filterable clearable style="width:100%"><el-option v-for="c in classOptions" :key="c.class_cd" :label="c.class_nm" :value="c.class_cd"/></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="客户属性"><el-select v-model="form.pptcode" filterable clearable style="width:100%"><el-option v-for="o in pptcodeOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="所属云类别"><el-select v-model="form.yun_type" filterable clearable style="width:100%"><el-option v-for="o in yunTypeOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="合同"><el-select v-model="form.is_contract" style="width:100%"><el-option label="否" value="0"/><el-option label="是" value="1"/></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="通讯方式"><el-select v-model="form.commmode" filterable clearable style="width:100%"><el-option v-for="c in commodeOptions" :key="c.cmm_cd" :label="c.cmm_nm" :value="c.cmm_cd"/></el-select></el-form-item></el-col>
        </el-row>

        <!-- 三、设备信息(对齐 PB w_plan_cust_befor.of_design_pos 可见性矩阵) -->
        <el-divider content-position="left">设备信息</el-divider>
        <!-- 设备来源: 00(00/01/02)、10、20 显示; 30/40 隐藏 -->
        <el-row v-if="showPosFrom" :gutter="20">
          <el-col :span="8"><el-form-item label="设备来源"><el-select v-model="form.pos_from" style="width:100%" @change="onPosFromChange"><el-option v-for="o in filteredPfOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item></el-col>
        </el-row>
        <!-- 计划机型: 选机型+库存+品级(绿A/B/C) -->
        <el-row v-if="showModelPicker" :gutter="20">
          <el-col :span="18"><el-form-item label="计划机型">
            <el-select v-model="form.pos_item" filterable clearable placeholder="选择机型" style="width:100%" @change="onModelSelect" popper-class="pos-model-select">
              <el-option v-for="m in modelOptions" :key="m.item_cd" :value="m.item_cd">
                <div class="model-option">
                  <span class="model-code"><b>{{ m.item_cd }}</b></span>
                  <span class="model-name">{{ m.item_nm }}</span>
                  <span class="model-price">¥{{ m.rent_money || '-' }}</span>
                  <span class="model-stock" :class="m.stock_qty>0?'in':'out'">{{ m.stock_qty>0?'库存:'+m.stock_qty:'缺货' }}</span>
                  <span class="model-grade">{{ m.grade_label }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <!-- 旧设备块(20/30/40): 旧设备ID+旧机型+旧机处理 -->
        <template v-if="showOldPos">
          <el-row :gutter="20">
            <el-col :span="8"><el-form-item label="旧设备ID"><el-select v-model="form.posid" filterable clearable placeholder="选择客户后联动" style="width:100%" @change="onMainAssetSelect"><el-option v-for="a in mainAssets" :key="a.eid" :label="a.eid" :value="a.eid"/></el-select></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="旧机型"><el-input :model-value="mainAssets.find(a=>a.eid===form.posid)?.item_nm || form.pos_item || ''" disabled placeholder="选择旧设备后自动带出"/></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="旧机处理"><el-select v-model="form.solve_type" filterable clearable placeholder="处理方式" style="width:100%"><el-option v-for="o in solveOptions" :key="o.value" :label="o.label" :value="o.value"/></el-select></el-form-item></el-col>
          </el-row>
        </template>
        <!-- 源设备块(00(01/02)/10/20(01/02/03/04)): 源磁卡号+源设备ID+源机型 -->
        <template v-if="showSrcCust">
          <el-row :gutter="20">
            <el-col :span="8"><el-form-item label="源磁卡号"><el-input v-model="form.new_custcard" placeholder="点击选择源客户" readonly @click="openSrcCustPicker"><template #append><el-button @click="openSrcCustPicker">选择</el-button></template></el-input></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="源设备ID"><el-select v-model="form.new_posid" filterable clearable placeholder="选择源客户后联动" style="width:100%" @change="onSrcAssetSelect"><el-option v-for="a in srcAssets" :key="a.eid" :label="a.eid" :value="a.eid"/></el-select></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="源机型"><el-input :model-value="srcAssets.find(a=>a.eid===form.new_posid)?.item_nm || form.new_positem || ''" disabled placeholder="选择源设备后自动带出"/></el-form-item></el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8"><el-form-item label="源名称"><el-input v-model="form.new_custnm"/></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="源地址"><el-input v-model="form.new_address"/></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="源电话"><el-input v-model="form.new_phoneno"/></el-form-item></el-col>
          </el-row>
        </template>
        <!-- 客户无效化(00(01/02)/20(01/02/03/04)/30/40) -->
        <el-row v-if="showCustUseflg" :gutter="20">
          <el-col :span="8"><el-form-item label="客户无效化"><el-switch v-model="form.cust_useflg" active-value="1" inactive-value="0"/></el-form-item></el-col>
        </el-row>

        <!-- 四、租售金额 -->
        <el-divider content-position="left">金额</el-divider>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="租赁/购买"><el-radio-group v-model="form.is_rent"><el-radio value="Y">租赁</el-radio><el-radio value="N">购买</el-radio></el-radio-group></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="押金金额"><el-input-number v-model="form.deposit" :min="0" :precision="2" style="width:100%" controls-position="right"/></el-form-item></el-col>
        </el-row>
        <!-- 五、呼出勾选(对齐 PB w_plan_cust_befor_new.cbx_serve) -->
        <el-divider content-position="left">呼出安排</el-divider>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="请求呼出"><el-switch v-model="form.call_serve" active-text="保存后触发呼出" inactive-text="不触发"/></el-form-item></el-col>
          <el-col v-if="form.call_serve" :span="12"><el-form-item label="呼出任务"><el-input v-model="form.serve_task" placeholder="如:确认门店情况"/></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="handleSave" :loading="saving">保存</el-button></template>
    </el-dialog>

    <!-- 客户选择对话框 -->
    <el-dialog :title="pickerMode==='source' ? '选择源客户' : '选择目标客户'" v-model="custPickerVisible" width="900px" top="5vh">
      <div style="margin-bottom:10px">
        <el-input v-model="custSearchKey" placeholder="输入磁卡号/客户编码/名称搜索" style="width:300px" clearable @keyup.enter="loadCustPicker" @clear="loadCustPicker"/>
        <el-button type="primary" @click="loadCustPicker" style="margin-left:8px">查询</el-button>
        <el-button @click="clearCustPicker">新客户(手动输入)</el-button>
      </div>
      <el-table :data="custPickerRows" v-loading="custPickerLoading" stripe height="400" @row-dblclick="onCustSelect">
        <el-table-column prop="cust_card" label="磁卡号" width="120"/>
        <el-table-column prop="cust_cd" label="编码" width="100"/>
        <el-table-column prop="cust_nm" label="名称" min-width="180" show-overflow-tooltip/>
        <el-table-column prop="class_cd" label="分类" width="80"/>
        <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip/>
        <el-table-column prop="phone_no" label="电话" width="120"/>
        <el-table-column label="操作" width="80" fixed="right"><template #default="{row}"><el-button link type="primary" size="small" @click="onCustSelect(row)">选择</el-button></template></el-table-column>
      </el-table>
      <AppPagination :page="custPickerPage" :per-page="custPickerPerPage" :total="custPickerTotal" @update:page="custPickerPage=$event;loadCustPicker()" @update:per-page="custPickerPerPage=$event;custPickerPage=1;loadCustPicker()"/>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { useDict } from '@/composables/useDict'
import {
  fetchPlans, createPlan, updatePlan,
  transitionPlan, implementPlan, completePlan, voidPlan, createOutbound,
  fetchPlanServes, createPlanServe,
} from '@/api/sales'
import type { PlanRecord, ServeRecord } from '@/api/sales'
import request from '@/api/request'
import { fetchCustomers } from '@/api/master'
import type { CustRecord } from '@/api/master'

const { dictLabel: plLabel, dictOptions: plOptions } = useDict('PL')
const { dictLabel: bsLabel } = useDict('BT')
const { dictOptions: pfOptions } = useDict('PF')  // 设备来源: 00商用仓库/01门店移机/02烟草直调/03IT公司/04海晟公司
// 旧机处理方式字典(PB 源码 dd_mm_solve, codetyp='PB')
const { dictOptions: solveOptions } = useDict('PB')
// 客户类型字典(PB dd_mm_busityp, codetyp='BT')
const { dictOptions: busitypOptions } = useDict('BT')
// 客户属性字典(PB dd_mm_pptyp, codetyp='YB')
const { dictOptions: pptcodeOptions } = useDict('YB')
// 所属云类别字典(PB dddw_pos_yuntype, codetyp='PY')
const { dictOptions: yunTypeOptions } = useDict('PY')
// 单据状态字典(PB dd_mm_status, codetyp='TS')
const { dictOptions: statusOptions } = useDict('TS')
// 客户分类(tmm21_custclass) + 通讯方式(tmm47_commode)
const classOptions = ref<{ class_cd: string; class_nm: string }[]>([])
const commodeOptions = ref<{ cmm_cd: string; cmm_nm: string }[]>([])
async function loadClassAndCommode() {
  try {
    const r1 = await request.get<never, { data: any[] }>('/custclasses'); classOptions.value = (r1?.data || []).map((c: any) => ({ class_cd: c.class_cd, class_nm: c.class_nm }))
  } catch { classOptions.value = [] }
  try {
    const r2 = await request.get<never, { data: any[] }>('/commodes'); commodeOptions.value = (r2?.data || []).map((c: any) => ({ cmm_cd: c.cmm_cd, cmm_nm: c.cmm_nm }))
  } catch { commodeOptions.value = [] }
}

// 客户选择对话框(对齐 PB: 点击磁卡号弹出选择有效客户)
const custPickerVisible = ref(false)
const custPickerRows = ref<CustRecord[]>([])
const custPickerLoading = ref(false)
const custSearchKey = ref('')
const custPickerPage = ref(1); const custPickerPerPage = ref(20); const custPickerTotal = ref(0)
// pickerMode: 'target'=目标客户(主客户信息), 'source'=源客户(new_* 字段)
const pickerMode = ref<'target' | 'source'>('target')
function openCustPicker() {
  if (isEdit.value) return  // 编辑模式不允许选择客户
  pickerMode.value = 'target'
  custPickerVisible.value = true
  custPickerPage.value = 1
  loadCustPicker()
}
function openSrcCustPicker() {
  pickerMode.value = 'source'
  custPickerVisible.value = true
  custPickerPage.value = 1
  loadCustPicker()
}
async function loadCustPicker() {
  custPickerLoading.value = true
  try {
    const r = await fetchCustomers({ page: custPickerPage.value, per_page: custPickerPerPage.value, search: custSearchKey.value })
    custPickerRows.value = (r?.data?.items || []).filter((c: CustRecord) => c.useflg === '1')
    custPickerTotal.value = r?.data?.total || 0
  } catch { custPickerRows.value = []; custPickerTotal.value = 0 }
  finally { custPickerLoading.value = false }
}
function onCustSelect(row: CustRecord) {
  if (pickerMode.value === 'source') {
    // 源客户: 赋值到 new_* 字段(源设备所属客户)
    form.new_custcard = row.cust_card || ''
    form.new_custcd = row.cust_cd || ''
    form.new_custnm = row.cust_nm || ''
    form.new_address = row.address || ''
    form.new_phoneno = row.phone_no || ''
    // 联动加载该客户名下有效成品资产
    loadSrcAssets(row.cust_cd || '')
  } else {
    // 目标客户: 赋值到主客户信息字段
    form.custcard = row.cust_card || ''
    form.custcd = row.cust_cd || ''
    form.custnm = row.cust_nm || ''
    form.custrnm = row.custrnm || ''
    form.address = row.address || ''
    form.contactor = row.contactor || ''
    form.phoneno = row.phone_no || ''
    form.classcd = row.class_cd || ''
    form.busityp = row.busi_typ || ''
    form.pptcode = row.ppt_code || ''
    form.yun_type = (row as any).yun_type || ''
    form.commmode = row.comm_mode || ''
    form.is_contract = row.is_contract || '0'
    form.jl_contactor = row.jl_contactor || ''
    form.jl_phoneno = row.jl_phoneno || ''
    // 联动加载主客户名下有效资产(供旧设备ID下拉)
    loadMainAssets(row.cust_cd || '')
  }
  custPickerVisible.value = false
}
function clearCustPicker() {
  if (pickerMode.value === 'source') {
    form.new_custcard = ''; form.new_custcd = ''; form.new_custnm = ''
    form.new_address = ''; form.new_phoneno = ''
    srcAssets.value = []; form.new_posid = ''; form.new_positem = ''
  } else {
    form.custcard = ''; form.custcd = ''; form.custnm = ''; form.custrnm = ''
    form.address = ''; form.contactor = ''; form.phoneno = ''
    mainAssets.value = []; form.posid = ''; form.pos_item = ''
  }
  custPickerVisible.value = false
}

// 源客户名下有效成品资产列表(选择源客户后联动)
const srcAssets = ref<{ eid: string; itemcd: string; item_nm: string }[]>([])
async function loadSrcAssets(custCd: string) {
  srcAssets.value = []; form.new_posid = ''; form.new_positem = ''
  if (!custCd) return
  try {
    const r = await request.get<never, { data: { items: any[]; total: number } }>('/assets', {
      params: { cust_cd: custCd, useflg: '1', location: 'customer', per_page: 200 }
    })
    srcAssets.value = (r?.data?.items || []).map((a: any) => ({
      eid: a.eid || '', itemcd: a.itemcd || '', item_nm: a.item_nm || ''
    }))
  } catch { srcAssets.value = [] }
}
function onSrcAssetSelect(eid: string) {
  const a = srcAssets.value.find(x => x.eid === eid)
  if (a) { form.new_positem = a.itemcd }
}

// PL 计划类型字典(对齐 PB dd_mm_plantyp: 00全新开通/10磁卡号变更/20旧机翻新/30设备取回/40门店关门)
// plOptions 已由 useDict('PL') 提供有序数组,保留后端 sort_no 顺序

// 机型下拉选项(在产机型: Item JOIN Bom useflg=1,押金/售价从 tip01_price 读取)
const modelOptions = ref<{ item_cd: string; item_nm: string; rent_money: number; sale_money: number; stock_qty: number; grade_label: string }[]>([])
async function loadModels() {
  try { const r = await request.get<never,{data:any[]}>('/items/pos-models'); modelOptions.value = (r?.data||[]) as any } catch { modelOptions.value = [] }
}

// pos_from 下拉选项（PB 按 plantyp 过滤可用来源）
const plantypPfFilter: Record<string, string[]> = { '00': ['00','01','02'], '10': ['01'], '20': ['00','01','02','03','04'], '30': [], '40': [] }
const filteredPfOptions = computed(() => pfOptions.value.filter(o => (plantypPfFilter[form.plantyp]||[]).includes(o.value)))
const showPosFrom = computed(() => (plantypPfFilter[form.plantyp]||[]).length > 0)
// 判断当前 pos_from
function isPosFrom(v: string) { return form.pos_from === v }
// 字段可见性矩阵(对齐 PB w_plan_cust_befor.of_design_pos)
// plantyp: 00开通/10磁卡号变更/20翻新/30取回/40关门; pos_from: 00仓库/01门店移机/02烟草直调/03IT公司/04海晟
const showModelPicker = computed(() => {
  // 计划机型行(选机型+查库存):
  //   00(00仓库) 全新开通选机型
  //   20(00仓库) 旧机翻新选目标机型
  //   30/40 取回/关门选机型(无 pos_from,直接显示)
  if (form.plantyp === '00' && isPosFrom('00')) return true
  if (form.plantyp === '20' && isPosFrom('00')) return true
  if (['30', '40'].includes(form.plantyp)) return true
  return false
})
const showOldPos = computed(() => ['20', '30', '40'].includes(form.plantyp))
// 旧设备块(旧设备ID+旧机型+旧机处理): 20/30/40 显示
const showSrcCust = computed(() => {
  // 源设备块(源磁卡号+源设备ID+源机型): 00(01/02)、10、20(01/02/03/04) 显示
  if (form.plantyp === '00') return isPosFrom('01') || isPosFrom('02')
  if (form.plantyp === '10') return true
  if (form.plantyp === '20') return ['01', '02', '03', '04'].includes(form.pos_from || '')
  return false
})
const showCustUseflg = computed(() => {
  // 客户无效化: 00(01/02)、20(01/02/03/04)、30、40 显示
  if (form.plantyp === '00') return isPosFrom('01') || isPosFrom('02')
  if (form.plantyp === '10') return false
  if (form.plantyp === '20') return ['01', '02', '03', '04'].includes(form.pos_from || '')
  return ['30', '40'].includes(form.plantyp)
})

// 磁卡号变更子类型(plantyp=10): 根据源磁卡号/源设备ID填写情况实时判定 CK/BG/BQ
// 对齐后端 sales_service.py:232-250 的 _build_downstream_payload 映射逻辑
const changeSubType = computed(() => {
  if (form.plantyp !== '10') return { code: '', label: '', hint: '', tagType: 'info' as const }
  const hasCard = !!(form.new_custcard || '').trim()
  const hasDevice = !!(form.new_posid || '').trim()
  if (hasDevice && hasCard) return { code: 'BG', label: '磁卡号+设备变更', hint: '源磁卡号和源设备ID均已选择,将生成设备变更单(BG)', tagType: 'warning' as const }
  if (hasCard) return { code: 'CK', label: '仅磁卡号变更', hint: '只选了源磁卡号,将生成设备变更单(CK)', tagType: 'success' as const }
  return { code: 'BQ', label: '信息变更', hint: '源磁卡号和源设备ID均未选,修改客户信息后将生成设备变更单(BQ)', tagType: 'info' as const }
})

// 主客户(目标客户)名下有效资产列表,用于旧设备ID下拉(20/30/40)
const mainAssets = ref<{ eid: string; itemcd: string; item_nm: string }[]>([])
async function loadMainAssets(custCd: string) {
  mainAssets.value = []; form.posid = ''; form.pos_item = ''
  if (!custCd) return
  try {
    const r = await request.get<never, { data: { items: any[]; total: number } }>('/assets', {
      params: { cust_cd: custCd, useflg: '1', location: 'customer', per_page: 200 }
    })
    mainAssets.value = (r?.data?.items || []).map((a: any) => ({
      eid: a.eid || '', itemcd: a.itemcd || '', item_nm: a.item_nm || ''
    }))
  } catch { mainAssets.value = [] }
}
function onMainAssetSelect(eid: string) {
  const a = mainAssets.value.find(x => x.eid === eid)
  if (a) {
    form.pos_item = a.itemcd
    // 按旧机型编码查在产机型带押金(非商用仓库场景)
    const m = modelOptions.value.find(x => x.item_cd === a.itemcd)
    form.deposit = m?.rent_money || 0
  }
}

function onPlantypChange() { form.pos_from = ''; form.cust_useflg = '0'; form.pos_item = ''; form.posid = '' }
function onPosFromChange() { if (form.pos_from === '00') { form.cust_useflg = '0'; form.new_custcard = ''; form.new_custcd = ''; form.new_phoneno = ''; form.new_address = '' } }
function onModelSelect(val: string) {
  const m = modelOptions.value.find(x => x.item_cd === val)
  if (m) { form.deposit = m.rent_money || 0
    if (m.stock_qty <= 0) ElMessage.warning('该机型库存不足,保存后将自动触发采购需求')
  }
}

// 状态标签映射 (对齐 PB plan_cust.status: 00/01/02/04/09)
function statusLabel(s: string) {
  const m: Record<string, string> = { '00': '计划中', '01': '计划完成', '02': '分派中', '03': '实施完成', '04': '实施中', '08': '计划退回', '09': '计划作废' }
  return m[s] || s
}
function statusTag(s: string) {
  const m: Record<string, string> = { '00': 'info', '01': 'success', '02': 'warning', '03': 'primary', '04': '', '08': 'danger', '09': 'danger' }
  return m[s] || 'info'
}
// 客户生命周期标签 — 优先读 customer_status(后端API新增字段)
function custLabel(row: PlanRecord) {
  const cs = row.customer_status as string
  if (cs === 'TEMP') return '临时'
  if (cs === 'PENDING') return '待确认'
  if (cs === 'ACTIVE') return '正式'
  if (cs === 'INVALID') return '已失效'
  // fallback: 从 plan_status 推断
  const s = row.plan_status
  if (s === '09') return '已失效'
  if (s === '01') return '正式'
  if (s === '00') return '待确认'
  return '正式'
}
function custTag(row: PlanRecord) {
  const cs = row.customer_status as string
  if (cs === 'TEMP') return 'info'
  if (cs === 'PENDING') return 'warning'
  if (cs === 'ACTIVE') return 'success'
  if (cs === 'INVALID') return 'danger'
  const s = row.plan_status
  if (s === '09') return 'danger'
  if (s === '01') return 'success'
  return 'info'
}
// 可作废的状态
function vCan(row: PlanRecord) { return ['00', '02', '03', '04', '08'].includes(row.plan_status || '') }

// 列表
const plans = ref<PlanRecord[]>([]); const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const searchPlanno = ref(''); const searchCustNm = ref(''); const searchStatus = ref('')
const searchCustcard = ref(''); const searchPlantyp = ref('')
const searchDateFrom = ref(''); const searchDateTo = ref('')
const searchServeStatus = ref('')

watch(page, () => loadData()); watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => { loadData(); loadModels(); loadClassAndCommode() })

function onReset() {
  searchPlanno.value = ''; searchCustNm.value = ''; searchStatus.value = ''
  searchCustcard.value = ''; searchPlantyp.value = ''
  searchDateFrom.value = ''; searchDateTo.value = ''; searchServeStatus.value = ''
  page.value = 1; loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, string> = { page: String(page.value), per_page: String(perPage.value) }
    if (searchPlanno.value) params.planno = searchPlanno.value
    if (searchCustNm.value) params.custnm = searchCustNm.value
    if (searchStatus.value) params.plan_status = searchStatus.value
    if (searchCustcard.value) params.custcard = searchCustcard.value
    if (searchPlantyp.value) params.plantyp = searchPlantyp.value
    if (searchDateFrom.value) params.date_from = searchDateFrom.value
    if (searchDateTo.value) params.date_to = searchDateTo.value
    if (searchServeStatus.value) params.serve_status = searchServeStatus.value
    const res = await fetchPlans(params)
    plans.value = res.data.items || []; total.value = res.data.total || 0
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function onSearch() { page.value = 1; loadData() }

// 对话框
const dialogVisible = ref(false); const isEdit = ref(false)
const form = reactive<PlanRecord & {
  deposit?: number; is_rent?: string; yun_type?: string; pos_item?: string;
  pos_from?: string; cust_useflg?: string; posid?: string;
  new_custcard?: string; new_custcd?: string; new_custnm?: string;
  new_address?: string; new_phoneno?: string; new_positem?: string; new_posid?: string;
  solve_type?: string; jl_contactor?: string; jl_phoneno?: string;
  classcd?: string; busityp?: string; is_contract?: string; pptcode?: string; commmode?: string;
  status?: string;
  call_serve?: boolean; serve_task?: string;
}>({
  planno: '', custnm: '', custcard: '', custcd: '', plantyp: '00', plan_status: '00',
  plandate: '', opercd: '', gendate: '',
  is_rent: 'N', deposit: 0, yun_type: '', pos_item: '',
  pos_from: '', cust_useflg: '0', posid: '',
  new_custcard: '', new_custcd: '', new_custnm: '', new_address: '', new_phoneno: '',
  new_positem: '', new_posid: '', solve_type: '',
  jl_contactor: '', jl_phoneno: '', classcd: '', busityp: '', is_contract: '0', pptcode: '', commmode: '',
  status: '00',
  call_serve: false, serve_task: '',
})
const saving = ref(false)

// openEdit 已合并到 openDialog(row?) 统一入口
function openCreate() {
  isEdit.value = false
  Object.assign(form, {
    planno: '', custnm: '', custcard: '', custcd: '', plantyp: '00', plan_status: '00',
    is_rent: 'N', deposit: 0, yun_type: '', pos_item: '',
    pos_from: '', cust_useflg: '0', posid: '',
    new_custcard: '', new_custcd: '', new_custnm: '', new_address: '', new_phoneno: '',
    new_positem: '', new_posid: '', solve_type: '',
    jl_contactor: '', jl_phoneno: '', classcd: '', busityp: '', is_contract: '0', pptcode: '', commmode: '',
    status: '00',
    call_serve: false, serve_task: '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      custnm: form.custnm, custcard: form.custcard, custrnm: form.custrnm,
      address: form.address, contactor: form.contactor, phoneno: form.phoneno,
      plantyp: form.plantyp, busityp: form.busityp, is_rent: form.is_rent,
      deposit: form.deposit, yun_type: form.yun_type, pos_item: form.pos_item,
      pos_from: form.pos_from, cust_useflg: form.cust_useflg, posid: form.posid,
      new_custcard: form.new_custcard, new_custcd: form.new_custcd,
      new_custnm: form.new_custnm, new_address: form.new_address, new_phoneno: form.new_phoneno,
      new_positem: form.new_positem, new_posid: form.new_posid, solve_type: form.solve_type,
      jl_contactor: form.jl_contactor, jl_phoneno: form.jl_phoneno,
      classcd: form.classcd, pptcode: form.pptcode, is_contract: form.is_contract, commmode: form.commmode,
    }
    // 新增时传递呼出勾选(对齐 PB cbx_serve)
    if (!isEdit.value) {
      payload.call_serve = form.call_serve
      payload.serve_task = form.serve_task
    }
    if (isEdit.value) { await updatePlan(form.planno, payload) } else { const r = await createPlan({ custcd: form.custcd, ...payload }); const newPlanno = (r?.data as any)?.planno || ''; if (newPlanno) form.planno = newPlanno }
    dialogVisible.value = false; loadData(); ElMessage.success('保存成功')
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

// 详情抽屉
const drawerVisible = ref(false); const detail = ref<PlanRecord | null>(null); const detailTab = ref('info')
const serveRecords = ref<ServeRecord[]>([]); const serveLoading = ref(false)
const custDevices = ref<any[]>([]); const deviceLoading = ref(false)
const deviceHistory = ref<any[]>([]); const historyLoading = ref(false)

async function openDetail(row: PlanRecord) {
  detail.value = row; drawerVisible.value = true; detailTab.value = 'info'
  serveLoading.value = true
  try {
    const res = await fetchPlanServes(row.planno)
    serveRecords.value = (res.data as ServeRecord[]) || []
  } catch { serveRecords.value = [] }
  finally { serveLoading.value = false }

  // 当前设备：对齐 PB d_plan_bom_dtl，按 pos_eid 分组成树形
  deviceLoading.value = true
  try {
    const r = await request.get(`/sales/plans/${row.planno}/devices/current`) as any
    const rows = (r?.data || []) as any[]
    // 按 pos_eid 分组，POS 为父行，配件为子行
    const posMap = new Map<string, { pos: any; accessories: any[] }>()
    for (const d of rows) {
      const key = d.pos_eid || '__nopos__'
      if (!posMap.has(key)) {
        posMap.set(key, {
          pos: { eid: d.pos_eid, itemcd: d.pos_itemcd, itemnm: d.pos_itemnm, useflg: d.pos_useflg, upddate: d.upddate },
          accessories: [],
        })
      }
      if (d.acc_eid && d.acc_useflg === '1') {
        posMap.get(key)!.accessories.push({ eid: d.acc_eid, itemcd: d.acc_itemcd, itemnm: d.acc_itemnm || '', useflg: d.acc_useflg, upddate: d.upddate })
      }
    }
    // 构建树形数据
    const tree: any[] = []
    let id = 0
    for (const [, v] of posMap) {
      const parent = { _id: ++id, eid: v.pos.eid, itemcd: v.pos.itemcd, itemnm: v.pos.itemnm, isPos: true, useflg: v.pos.useflg, upddate: v.pos.upddate, children: [] as any[], hasChildren: v.accessories.length > 0 }
      for (const acc of v.accessories) {
        parent.children.push({ _id: ++id, eid: acc.eid, itemcd: acc.itemcd, itemnm: acc.itemnm, isPos: false, useflg: acc.useflg, upddate: acc.upddate })
      }
      tree.push(parent)
    }
    custDevices.value = tree
  } catch { custDevices.value = [] }
  finally { deviceLoading.value = false }

  // 历史设备：对齐 PB d_plan_bom_lst（tmm35_cust_pos_rl 所有记录含失效）
  historyLoading.value = true
  try {
    const r = await request.get(`/sales/plans/${row.planno}/devices/history`) as any
    deviceHistory.value = (r?.data || []).map((d: any) => ({
      itemcd: d.itemcd, itemnm: d.itemnm, eid: d.eid,
      sysinfo: d.sysinfo, softinfo: d.softinfo, posinfo: d.posinfo,
      upddate: d.upddate, useflg: d.useflg,
    }))
  } catch { deviceHistory.value = [] }
  finally { historyLoading.value = false }
}

// 状态操作
async function doRequestServe(row: PlanRecord) {
  try {
    await createPlanServe(row.planno, { servetyp: '1', serve_task: `预计划呼出-${row.planno}` })
    ElMessage.success(`呼出单已创建`)
    loadData()
  } catch { ElMessage.error('请求呼出失败') }
}
async function doTransition(row: PlanRecord, to: string) {
  try {
    await transitionPlan(row.planno, to)
    ElMessage.success(`已流转到 ${statusLabel(to)}`)
    loadData()
  } catch { ElMessage.error('操作失败') }
}
async function doImplement(row: PlanRecord) {
  try {
    await ElMessageBox.confirm(`确认实施？将为预计划 ${row.planno} 生成下游单据。`, '实施确认', { type: 'warning' })
    const res = await implementPlan(row.planno)
    const dsid = (res.data as any)?.downstream_id || ''
    ElMessage.success(`实施确认成功，下游单据: ${dsid}`)
    loadData()
  } catch { /* 取消 */ }
}
async function doOutbound(row: PlanRecord) {
  try {
    await ElMessageBox.confirm(`为预计划 ${row.planno} 生成 OV=1 销售出库草稿？`, '生成出库单', { type: 'info' })
    const res = await createOutbound(row.planno, '04')
    const obid = (res.data as any)?.outbillid || ''
    ElMessage.success(`出库单已创建: ${obid}`)
    loadData()
  } catch { /* 取消 */ }
}
async function doComplete(row: PlanRecord) {
  try {
    await ElMessageBox.confirm(`确认完成？客户将从待确认转为正式客户。`, '完成确认', { type: 'warning' })
    await completePlan(row.planno)
    ElMessage.success('已完成，客户已转正')
    loadData()
  } catch { /* 取消 */ }
}
async function doVoid(row: PlanRecord) {
  try {
    const { value: remark } = await ElMessageBox.prompt('作废原因（可选）', '作废预计划', { inputType: 'text' })
    await voidPlan(row.planno, remark || undefined)
    ElMessage.success('已作废')
    loadData()
  } catch { /* 取消 */ }
}
</script>

<style scoped>
.plan-page { padding: 0 }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px }
.page-header h2 { font-size:18px; font-weight:600; margin:0 }
.search-bar { display:flex; gap:12px; flex-wrap:wrap; align-items:center }
.field { display:flex; align-items:center; gap:6px }
.field label { font-size:13px; color:#606266; white-space:nowrap }
/* 机型下拉选项 */
.model-option { display:flex; align-items:center; width:100%; gap:8px }
.model-option .model-code { min-width:70px; font-weight:600 }
.model-option .model-name { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
.model-option .model-price { color:#e6a23c; font-size:12px; min-width:65px }
.model-option .model-stock.in { color:#67c23a; font-size:12px; min-width:60px }
.model-option .model-stock.out { color:#f56c6c; font-size:12px; min-width:60px }
.model-option .model-grade { color:#909399; font-size:11px; min-width:130px; white-space:nowrap }
</style>
