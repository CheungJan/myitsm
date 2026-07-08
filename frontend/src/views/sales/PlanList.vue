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
        <el-table-column label="日期" width="110"><template #default="{row}">{{ fmtDateTime(row.gendate as string) }}</template></el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{row}">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="row.plan_status==='00'" link type="warning" size="small" @click="openEdit(row)">修改</el-button>
            <el-button v-if="row.plan_status==='00' && row.serve_status!=='01'" link type="info" size="small" @click="doRequestServe(row)">请求呼出</el-button>
            <el-tag v-else-if="row.plan_status==='00' && row.serve_status==='01'" type="warning" size="small">已要求呼出</el-tag>
            <el-button v-if="row.plan_status==='00'" link type="success" size="small" @click="doTransition(row,'02')">确认</el-button>
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
              <el-descriptions-item label="理论订货日">{{ weekdayLabel((detail as any).custrnm) }}</el-descriptions-item>
              <el-descriptions-item label="客户编码">{{ detail.custcd || '-' }}</el-descriptions-item>
              <el-descriptions-item label="磁卡号">{{ detail.custcard || '-' }}</el-descriptions-item>
              <el-descriptions-item label="新磁卡号" v-if="detail.new_custcard">{{ detail.new_custcard }}</el-descriptions-item>
              <el-descriptions-item label="新客户" v-if="detail.new_custcd">{{ detail.new_custcd }} {{ detail.new_custnm || '' }}</el-descriptions-item>
              <el-descriptions-item label="地址">{{ detail.address || '-' }}</el-descriptions-item>
              <el-descriptions-item label="新地址" v-if="detail.new_address">{{ detail.new_address }}</el-descriptions-item>
              <el-descriptions-item label="省/直辖市">{{ (detail as any).geo_prvn_cd ? geoPrvnLabel((detail as any).geo_prvn_cd) : '-' }}</el-descriptions-item>
              <el-descriptions-item label="地级市">{{ (detail as any).geo_city_cd ? geoCityLabel((detail as any).geo_city_cd) : '-' }}</el-descriptions-item>
              <el-descriptions-item label="区县">{{ (detail as any).geo_area_cd ? geoAreaLabel((detail as any).geo_area_cd) : '-' }}</el-descriptions-item>
              <el-descriptions-item label="街道乡镇">{{ (detail as any).geo_street_cd ? geoStreetLabel((detail as any).geo_street_cd) : '-' }}</el-descriptions-item>
              <el-descriptions-item label="负责区域">{{ (detail as any).area_cd ? areaCdLabel((detail as any).area_cd) : '-' }}</el-descriptions-item>
              <el-descriptions-item label="环线位置">{{ (detail as any).location ? (wzLabel((detail as any).location) || (detail as any).location) : '-' }}</el-descriptions-item>
              <el-descriptions-item label="联系人">{{ detail.contactor || '-' }}</el-descriptions-item>
              <el-descriptions-item label="电话">{{ detail.phoneno || '-' }}</el-descriptions-item>
              <el-descriptions-item label="经理">{{ detail.jl_contactor || '-' }}</el-descriptions-item>
              <el-descriptions-item label="经理电话">{{ detail.jl_phoneno || '-' }}</el-descriptions-item>
              <el-descriptions-item label="计划类型">{{ plLabel(detail.plantyp) }}</el-descriptions-item>
              <el-descriptions-item label="业务类型">{{ bsLabel(detail.busityp || '') || detail.busityp || '-' }}</el-descriptions-item>
              <el-descriptions-item label="设备来源">{{ detail.pos_from ? (pfLabel(detail.pos_from as string) || detail.pos_from) : '-' }}</el-descriptions-item>
              <el-descriptions-item label="机型">{{ detail.pos_item || '-' }}</el-descriptions-item>
              <el-descriptions-item label="押金">{{ detail.deposit ? '¥'+Number(detail.deposit).toLocaleString() : '-' }}</el-descriptions-item>
              <el-descriptions-item label="租赁">{{ detail.is_rent==='Y'?'租赁':'购买' }}</el-descriptions-item>
              <el-descriptions-item label="合同">{{ detail.is_contract==='1'?'是':'否' }}</el-descriptions-item>
              <el-descriptions-item label="有限公司">{{ classLabel(detail.classcd as string) || detail.classcd || '-' }}</el-descriptions-item>
              <el-descriptions-item label="客户属性">{{ pptLabel(detail.pptcode as string) || detail.pptcode || '-' }}</el-descriptions-item>
              <el-descriptions-item label="通讯方式">{{ commmodeLabel(detail.commmode as string) || detail.commmode || '-' }}</el-descriptions-item>
              <el-descriptions-item label="所属云类别">{{ yunTypeLabel(detail.yun_type as string) || detail.yun_type || '-' }}</el-descriptions-item>
              <el-descriptions-item label="下游单据">{{ detail.imple_billid || '未生成' }}</el-descriptions-item>
              <el-descriptions-item label="出库标志">{{ outflagLabel(detail.is_outflag as string) }}</el-descriptions-item>
              <el-descriptions-item label="分配呼出人">{{ serveErcdLabel(detail.serve_ercd as string) }}</el-descriptions-item>
              <el-descriptions-item label="创建日期">{{ fmtDateTime(detail.gendate as string) }}</el-descriptions-item>
              <el-descriptions-item label="操作员">{{ detail.opercd || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <el-tab-pane label="呼出记录" name="serve">
            <el-table :data="serveRecords" size="small" v-loading="serveLoading" empty-text="暂无呼出记录">
              <el-table-column prop="servetyp" label="类型" width="80"><template #default="{row}">{{ ['客户确认','预计划呼出','实施任务'][Number(row.servetyp)]||row.servetyp }}</template></el-table-column>
              <el-table-column prop="serve_task" label="任务" min-width="100" show-overflow-tooltip />
              <el-table-column prop="serve_back" label="呼出结果" width="80"><template #default="{row}"><el-tag :type="({Y:'success',N:'danger',O:'warning'} as Record<string, string>)[row.serve_back as string]||'info'" size="small">{{ ({Y:'同意',N:'不同意',O:'未接通'} as Record<string, string>)[row.serve_back as string]||row.serve_back||'-' }}</el-tag></template></el-table-column>
              <el-table-column prop="serve_mark" label="客户反馈" min-width="120" show-overflow-tooltip />
              <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='01'?'success':row.status==='09'?'danger':'info'" size="small">{{ ({'00':'待呼出','01':'已呼出','09':'已作废'} as Record<string, string>)[row.status as string]||row.status }}</el-tag></template></el-table-column>
              <el-table-column label="日期" width="110"><template #default="{row}">{{ fmtDateTime(row.gendate as string) }}</template></el-table-column>
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
              <el-table-column label="更新日期" width="120"><template #default="{row}">{{ fmtDateTime(row.upddate as string) }}</template></el-table-column>
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
              <el-table-column label="更新日期" width="120"><template #default="{row}">{{ fmtDateTime(row.upddate as string) }}</template></el-table-column>
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
          <el-col :span="8"><el-form-item label="磁卡号"><el-input v-model="form.custcard" :placeholder="custcardPlaceholder" :readonly="custcardReadonly" :disabled="custcardDisabled" @click="onCustcardClick"><template v-if="showCustcardPickerBtn" #append><el-button @click="openCustPicker">选择</el-button></template></el-input></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="客户编码"><el-input v-model="form.custcd" :placeholder="custcdPlaceholder" :readonly="custcdReadonly" :disabled="custcdDisabled"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="客户名称"><el-input v-model="form.custnm" placeholder="名称"/></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="6"><el-form-item label="联系人"><el-input v-model="form.contactor"/></el-form-item></el-col>
          <el-col :span="10"><el-form-item label="电话"><el-input v-model="form.phoneno"/></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="6"><el-form-item label="省/直辖市" label-width="80px"><el-select v-model="form.geo_prvn_cd" clearable filterable style="width:100%" @change="onPlanGeoPrvnChange"><el-option v-for="p in geoProvinces" :key="p.code" :label="p.name" :value="p.code" /></el-select></el-form-item></el-col>
          <el-col :span="5"><el-form-item label="地级市" label-width="60px"><el-select v-model="form.geo_city_cd" clearable filterable style="width:100%" @change="onPlanGeoCityChange" :loading="geoCitiesLoading"><el-option v-for="c in geoCities" :key="c.code" :label="c.name" :value="c.code" /></el-select></el-form-item></el-col>
          <el-col :span="5"><el-form-item label="区县" label-width="44px"><el-select v-model="form.geo_area_cd" clearable filterable style="width:100%" @change="onPlanGeoAreaChange" :loading="geoAreasLoading"><el-option v-for="a in geoAreas" :key="a.code" :label="a.name" :value="a.code" /></el-select></el-form-item></el-col>
          <el-col :span="7"><el-form-item label="街道乡镇" label-width="68px"><el-select v-model="form.geo_street_cd" clearable filterable style="width:100%" :loading="geoStreetsLoading"><el-option v-for="s in geoStreets" :key="s.code" :label="s.name" :value="s.code" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="地址"><el-input v-model="form.address" placeholder="地址"/></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="负责区域"><el-select v-model="form.area_cd" clearable filterable style="width:100%"><el-option v-for="a in planAreas" :key="(a.area_cd||'').trim()" :label="a.name||a.area_nm" :value="(a.area_cd||'').trim()" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="环线位置"><el-select v-model="form.location" clearable style="width:100%"><el-option v-for="o in wzOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="理论订货日"><el-select v-model="form.custrnm" clearable style="width:100%"><el-option v-for="o in weekdayOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item></el-col>
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
          <el-col :span="8"><el-form-item label="通讯方式"><el-select v-model="form.commmode" filterable clearable style="width:100%"><el-option v-for="c in commodeOptions" :key="c.value" :label="c.label" :value="c.value"/></el-select></el-form-item></el-col>
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
        <!-- 方案 A：商用仓库对应设备可选下拉（预绑定 EID） -->
        <el-row v-if="showModelPicker && showEidPicker" :gutter="20">
          <el-col :span="18"><el-form-item label="对应设备">
            <el-select v-model="form.posid" filterable clearable placeholder="可选，指定具体 EID（方案 A 预绑定）" style="width:100%">
              <el-option v-for="e in availableEids" :key="e.eid" :value="e.eid" :label="e.eid">
                <div class="eid-option">
                  <span class="eid-code"><b>{{ e.eid }}</b></span>
                  <span class="eid-wh">{{ e.whnm || e.whcd }}</span>
                  <span class="eid-asset">{{ e.asset_type_nm || atLabel(e.asset_type) }}</span>
                  <span class="eid-qc">{{ e.itemtyp_nm || e.itemtyp }}</span>
                </div>
              </el-option>
            </el-select>
            <span class="eid-hint" style="margin-left:8px;color:#909399;font-size:12px">不选则发货时由仓库绑定（方案 B）</span>
          </el-form-item></el-col>
        </el-row>
        <!-- 旧设备块(20/30/40): 旧设备ID+旧机型+旧机处理 -->
        <template v-if="showOldPos">
          <el-row :gutter="20">
            <el-col :span="8"><el-form-item label="旧设备ID"><el-select v-model="form.posid" filterable clearable placeholder="选择客户后联动" style="width:100%" @change="onMainAssetSelect"><el-option v-for="a in mainAssets" :key="a.eid" :label="mainAssetLabel(a.eid)" :value="a.eid"/></el-select></el-form-item></el-col>
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
    <el-dialog :title="custPickerTitle" v-model="custPickerVisible" width="900px" top="5vh">
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
  fetchPlans, fetchPlan, createPlan, updatePlan,
  transitionPlan, completePlan, voidPlan,
  fetchPlanServes, createPlanServe, fetchAvailableEids,
} from '@/api/sales'
import type { PlanRecord, ServeRecord, AvailableEid } from '@/api/sales'
import request from '@/api/request'
import { fetchGroupMembers } from '@/api/system'
import { fetchCustomers, fetchGeoProvinces, fetchGeoCities, fetchGeoAreas, fetchGeoStreets, fetchAreas } from '@/api/master'
import type { CustRecord } from '@/api/master'

const { dictLabel: plLabel, dictOptions: plOptions } = useDict('PL')
const { dictLabel: bsLabel } = useDict('BT')
const { dictLabel: pfLabel, dictOptions: pfOptions } = useDict('PF')  // 设备来源: 00商用仓库/01门店移机/02烟草直调/03IT公司/04海晟公司
// 旧机处理方式字典(PB 源码 dd_mm_solve, codetyp='PB')
const { dictOptions: solveOptions } = useDict('PB')
// 客户类型字典(PB dd_mm_busityp, codetyp='BT')
const { dictOptions: busitypOptions } = useDict('BT')
// 客户属性字典(PB dd_mm_pptyp, codetyp='YB')
const { dictOptions: pptcodeOptions } = useDict('YB')
// 所属云类别字典(PB dddw_pos_yuntype, codetyp='PY')
const { dictOptions: yunTypeOptions } = useDict('PY')
// 环线位置字典(codetyp='WZ')
const { dictLabel: wzLabel, dictOptions: wzOptions } = useDict('WZ')
// 单据状态字典(PB dd_mm_status, codetyp='TS')
const { dictOptions: statusOptions } = useDict('TS')
// 客户分类(tmm21_custclass) + 通讯方式(tmm31_syscodes code_typ='CM')
const classOptions = ref<{ class_cd: string; class_nm: string }[]>([])
const { dictOptions: commodeOptions, dictLabel: commmodeLabel } = useDict('CM')
async function loadClassOptions() {
  try {
    const r1 = await request.get<never, { data: any[] }>('/custclasses'); classOptions.value = (r1?.data || []).map((c: any) => ({ class_cd: c.class_cd, class_nm: c.class_nm }))
  } catch { classOptions.value = [] }
}

// 服务台用户组编码（18）：分配呼出人下拉只显示该组有效成员
const SERVE_GROUP_CD = '18'
const userOptions = ref<{ user_cd: string; user_nm: string }[]>([])
async function loadUserOptions() {
  try {
    const r = await fetchGroupMembers(SERVE_GROUP_CD, { active_only: '1' })
    userOptions.value = ((r?.data as any[]) || [])
      .map((u: any) => ({ user_cd: u.user_cd, user_nm: u.user_nm || '' }))
  } catch { userOptions.value = [] }
}
// 分配呼出人编码→姓名标签
function serveErcdLabel(code: string) {
  if (!code) return '-'
  const u = userOptions.value.find(x => x.user_cd === code)
  return u ? `${u.user_nm || u.user_cd}` : code
}

// 客户选择对话框(对齐 PB: 点击磁卡号弹出选择有效客户)
const custPickerVisible = ref(false)
const custPickerRows = ref<CustRecord[]>([])
const custPickerLoading = ref(false)
const custSearchKey = ref('')
const custPickerPage = ref(1); const custPickerPerPage = ref(20); const custPickerTotal = ref(0)
// pickerMode: 'target'=目标客户(主客户信息), 'source'=源客户(new_* 字段)
const pickerMode = ref<'target' | 'source'>('target')
// 客户选择对话框标题：
// - plantyp=00 全新开通：复制已有客户信息（新建），对齐 SAP XD01 "Refer to"
// - 其他 plantyp：选择目标客户（老客户业务，回写 custcd 联动）
const custPickerTitle = computed(() => {
  if (pickerMode.value === 'source') return '选择源客户'
  return form.plantyp === '00' ? '复制已有客户信息（新建）' : '选择目标客户'
})
function openCustPicker() {
  if (isEdit.value) return  // 编辑模式不允许选择客户
  pickerMode.value = 'target'
  custPickerVisible.value = true
  custPickerPage.value = 1
  loadCustPicker()
}
// 磁卡号字段点击行为分流：
// - plantyp=10 磁卡号变更：未选源门店时提示并引导先选源门店，选源后不打开选择（直接输入新磁卡号）
// - 其他 plantyp readonly 时：点击打开客户选择对话框
function onCustcardClick() {
  if (form.plantyp === '10') {
    if (!form.new_custcd) {
      ElMessage.warning('请先选择源门店')
      openSrcCustPicker()
    }
    return
  }
  if (custcardReadonly.value) openCustPicker()
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
    // 客户/磁卡号选择仅列出正式用户(ACTIVE)，排除预计划未完成的临时(TEMP)/待确认(PENDING)客户
    const r = await fetchCustomers({
      page: custPickerPage.value, per_page: custPickerPerPage.value,
      search: custSearchKey.value, customer_status: 'ACTIVE',
    })
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
    // plantyp=10 磁卡号变更：同步源门店基础信息到当前客户字段
    // 对齐行业换卡业务标准：主键不变 + 唯一标识变 + 业务信息从源复制
    // - custcd = 源门店 custcd（不变）
    // - 同步非地址/店名/磁卡号信息：联系人/电话/客户经理/类别/业务类型等
    // - 不同步：custnm（店名可改）/address（地址可改）/custcard（新磁卡号用户输入）
    if (form.plantyp === '10') {
      form.custcd = row.cust_cd || ''  // custcd 不变，等于源门店 custcd
      form.custrnm = row.custrnm || ''
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
      form.geo_prvn_cd = (row as any).geo_prvn_cd || ''
      form.geo_city_cd = (row as any).geo_city_cd || ''
      form.geo_area_cd = (row as any).geo_area_cd || ''
      form.geo_street_cd = (row as any).geo_street_cd || ''
      form.area_cd = (row as any).area_cd || ''
      form.location = (row as any).location || ''
      if (form.geo_prvn_cd || form.geo_city_cd || form.geo_area_cd)
        loadPlanGeoForEdit(form.geo_prvn_cd || '', form.geo_city_cd || '', form.geo_area_cd || '')
      // 清空磁卡号字段，提示用户输入新磁卡号
      form.custcard = ''
      // 清空店名/地址，用户可修改（从源复制但允许改）
      form.custnm = row.cust_nm || ''
      form.address = row.address || ''
      ElMessage.info('已关联源门店基础信息，请输入新磁卡号（客户编码保持不变）')
    }
  } else if (form.plantyp === '00') {
    // 全新开通 - 复制新建模式（对齐 SAP XD01 "Refer to" / 用友客户档案复制）：
    // 连锁客户场景：选 A 门店 → 复制基础信息 → 改店名/地址 → 输入新磁卡号 → 保存自动生成新 custcd
    // 主键和唯一标识强制清空，要求用户输入新的，避免回写已有客户造成冲突
    form.custcard = ''  // 强制清空，要求输入新磁卡号
    form.custcd = ''    // 保持空，保存时由后端按 MAX(cust_cd)+1 自动生成
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
    form.geo_prvn_cd = (row as any).geo_prvn_cd || ''
    form.geo_city_cd = (row as any).geo_city_cd || ''
    form.geo_area_cd = (row as any).geo_area_cd || ''
    form.geo_street_cd = (row as any).geo_street_cd || ''
    form.area_cd = (row as any).area_cd || ''
    form.location = (row as any).location || ''
    if (form.geo_prvn_cd || form.geo_city_cd || form.geo_area_cd)
      loadPlanGeoForEdit(form.geo_prvn_cd || '', form.geo_city_cd || '', form.geo_area_cd || '')
    // 全新开通不加载已有资产（新客户无历史设备）
    mainAssets.value = []; form.posid = ''; form.pos_item = ''
  } else {
    // 其他 plantyp（10/20/30/40）- 老客户业务：回写 custcd 联动
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
    form.geo_prvn_cd = (row as any).geo_prvn_cd || ''
    form.geo_city_cd = (row as any).geo_city_cd || ''
    form.geo_area_cd = (row as any).geo_area_cd || ''
    form.geo_street_cd = (row as any).geo_street_cd || ''
    form.area_cd = (row as any).area_cd || ''
    form.location = (row as any).location || ''
    if (form.geo_prvn_cd || form.geo_city_cd || form.geo_area_cd)
      loadPlanGeoForEdit(form.geo_prvn_cd || '', form.geo_city_cd || '', form.geo_area_cd || '')
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
    // plantyp=10 清空源门店时同时清理同步到当前客户的字段
    if (form.plantyp === '10') {
      form.custcd = ''; form.custcard = ''
      form.custnm = ''; form.custrnm = ''; form.address = ''
      form.contactor = ''; form.phoneno = ''
      form.classcd = ''; form.busityp = ''; form.pptcode = ''
      form.yun_type = ''; form.commmode = ''; form.is_contract = '0'
      form.jl_contactor = ''; form.jl_phoneno = ''
    }
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

// 资产类型字典(AT: 01新机/02旧机/03翻新机/04报废) —— 用于旧设备下拉显示
const { dictLabel: atLabel } = useDict('AT')

// 方案 A：商用仓库对应设备可选下拉（预绑定 EID）
// 当 pos_from='00' 且 plantyp in ('00','20') 时，选机型后可可选指定具体 EID
const availableEids = ref<AvailableEid[]>([])
const showEidPicker = computed(() => {
  // 商用仓库 + 开通/翻新 才显示对应设备下拉
  return isPosFrom('00') && ['00', '20'].includes(form.plantyp)
})
async function loadAvailableEids(modelCd: string) {
  availableEids.value = []
  if (!modelCd) return
  try {
    const r = await fetchAvailableEids({ model_cd: modelCd, per_page: 100 })
    availableEids.value = (r?.data?.items || []) as any
  } catch { availableEids.value = [] }
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

// 磁卡号字段：plantyp=00(全新开通)和plantyp=10(磁卡号变更)时支持手动输入
// 因为全新开通针对新用户、磁卡号变更是老用户新磁卡号，系统客户表不存在这些记录
// 其他plantyp(20/30/40)为老客户业务，磁卡号从已有客户选择
// plantyp=10 特殊：必须先选源门店（老客户），选后才能输入新磁卡号，对齐行业换卡业务标准
// - disabled：完全禁用交互（不可点击、不可选中、不可触发事件），用于 plantyp=10 未选源门店时强制引导先选源
// - readonly：只读但仍可点击触发 click 事件，用于其他 plantyp 老客户业务点击打开选择对话框
const custcardDisabled = computed(() => {
  // plantyp=10 未选源门店时完全禁用，强制先选源门店
  return form.plantyp === '10' && !form.new_custcd
})
const custcardReadonly = computed(() => {
  // 其他 plantyp（20/30/40）老客户业务：readonly 点击打开选择
  if (['00', '10'].includes(form.plantyp)) return false
  return true
})
const custcardPlaceholder = computed(() => {
  if (form.plantyp === '10' && !form.new_custcd) return '请先选择源门店'
  if (custcardReadonly.value) return '点击选择已有客户'
  return '输入磁卡号或点击选择'
})
// 磁卡号字段"选择"按钮显隐：
// - plantyp=00 全新开通：显示（复制新建模式）
// - plantyp=10 磁卡号变更：隐藏（新磁卡号手动输入，通过选择源门店关联基础信息）
// - 其他 plantyp（20/30/40）：显示（老客户业务，选择已有客户联动）
const showCustcardPickerBtn = computed(() => form.plantyp !== '10')

// 客户编码字段（对齐 PB w_plan_cust_befor_new.srw of_insert_cust）：
// - plantyp=00 全新开通：用户输入磁卡号，custcd 保存时由后端按 MAX(custcd)+1 左补零 8 位自动生成，
//   字段只读，placeholder 提示"保存后自动生成"
// - plantyp=10 磁卡号变更：custcd = 源门店 custcd（不变），选源门店后自动带出，字段只读
//   对齐行业换卡业务标准：主键不变 + 唯一标识变 + 业务信息从源复制
// - 其他 plantyp（20/30/40）：老客户业务，custcd 从磁卡号选择联动带出，
//   未选磁卡号时禁用空白不允许填写，选磁卡号后只读显示
const custcdReadonly = computed(() => true)
const custcdDisabled = computed(() => {
  if (form.plantyp === '00') return false
  if (form.plantyp === '10') return !form.new_custcd  // 未选源门店时禁用
  return !form.custcard
})
const custcdPlaceholder = computed(() => {
  if (form.plantyp === '00') return '保存后自动生成'
  if (form.plantyp === '10') return form.new_custcd ? '' : '选择源门店后自动带出'
  return form.custcard ? '' : '选择磁卡号后自动带出'
})

// 磁卡号变更子类型(plantyp=10): 重构版本始终 CK，按数据条件隐式区分两条路径
// 对齐后端 sales_service.py _build_downstream_payload（change_type 始终 'CK'）
// 对齐 PB USP_PLAN_IMPLE 硬编码 CK + USP_PLAN_CONFRIM V_NEW_POSID 隐式判断
// CK(含设备转移): new_posid 或 posid 非空 + new_custcd 非空 → rl 转移 + 目标客户合并
// CK(纯磁卡号变更): 无设备或无新客户 → 仅同步客户主表
const changeSubType = computed(() => {
  if (form.plantyp !== '10') return { code: '', label: '', hint: '', tagType: 'info' as const }
  const hasDevice = !!(form.new_posid || form.posid || '').trim()
  const hasNewCust = !!(form.new_custcd || '').trim()
  if (hasDevice && hasNewCust) {
    return { code: 'CK', label: '磁卡号变更（含设备转移）', hint: '源磁卡号设备转移到新磁卡号下，旧客户 rl 失效 + 新客户 rl 新建', tagType: 'warning' as const }
  }
  return { code: 'CK', label: '磁卡号变更（纯信息变更）', hint: '仅同步客户主表（磁卡号/姓名/地址/电话）+ 写历史 + 回写计划', tagType: 'success' as const }
})

// 主客户(目标客户)名下有效资产列表,用于旧设备ID下拉(20/30/40)
const mainAssets = ref<{ eid: string; itemcd: string; item_nm: string; asset_type?: string }[]>([])
async function loadMainAssets(custCd: string) {
  mainAssets.value = []; form.posid = ''; form.pos_item = ''
  if (!custCd) return
  try {
    const r = await request.get<never, { data: { items: any[]; total: number } }>('/assets', {
      params: { cust_cd: custCd, useflg: '1', location: 'customer', per_page: 200 }
    })
    mainAssets.value = (r?.data?.items || []).map((a: any) => ({
      eid: a.eid || '', itemcd: a.itemcd || '', item_nm: a.item_nm || '',
      asset_type: a.asset_type || ''
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
// 旧设备下拉显示标签：eid + 资产类型名称
function mainAssetLabel(eid: string) {
  const a = mainAssets.value.find(x => x.eid === eid)
  if (!a) return eid
  const at = a.asset_type ? atLabel(a.asset_type) : ''
  return at ? `${eid}（${at}）` : eid
}

function onPlantypChange() {
  form.pos_from = ''; form.cust_useflg = '0'; form.pos_item = ''; form.posid = ''
  // 切换计划类型时清理客户编码：
  // - 切换到 plantyp=00：保存时由后端自动生成，清空当前值
  // - 切换到其他 plantyp：需重新选择磁卡号联动带出，清空当前值
  form.custcd = ''
}
function onPosFromChange() { if (form.pos_from === '00') { form.cust_useflg = '0'; form.new_custcard = ''; form.new_custcd = ''; form.new_phoneno = ''; form.new_address = '' } }
function onModelSelect(val: string) {
  const m = modelOptions.value.find(x => x.item_cd === val)
  if (m) { form.deposit = m.rent_money || 0
    if (m.stock_qty <= 0) ElMessage.warning('该机型库存不足,保存后将自动触发采购需求')
  }
  // 方案 A：选机型后加载可用 EID 列表，清空已选 posid
  form.posid = ''
  if (showEidPicker.value && val) loadAvailableEids(val)
}

// 状态标签映射 (对齐 PB plan_cust.status: 00/01/02/04/09)
function statusLabel(s: string) {
  const m: Record<string, string> = { '00': '计划中', '01': '计划完成', '02': '分派中', '03': '实施完成', '04': '实施中', '08': '计划退回', '09': '计划作废' }
  return m[s] || s
}
// 出库标志三态显示（N/A=非商用仓库不适用 / 0=待出库 / 1=已出库）
function outflagLabel(v: unknown) {
  const s = String(v ?? '')
  const m: Record<string, string> = { 'N/A': '不适用', '0': '待出库', '1': '已出库' }
  return m[s] ?? (s || '-')
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
// 日期时间格式化：将 ISO 格式 (2026-07-04T10:26:08.629613) 转为 yyyy-mm-dd hh:mm:ss
function fmtDateTime(v: string | undefined | null): string {
  if (!v) return '-'
  const s = String(v)
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(s)) return s.slice(0, 19)
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(s)) return s.replace('T', ' ').slice(0, 19)
  return s
}
// 客户分类标签
function classLabel(classcd: string) {
  const c = classOptions.value.find(x => x.class_cd === classcd)
  return c ? `${classcd} - ${c.class_nm}` : classcd
}
// 客户属性标签
function pptLabel(pptcode: string) {
  const o = pptcodeOptions.value.find(x => x.value === pptcode)
  return o ? o.label : pptcode
}
// 通讯方式标签（已改用 useDict('CM') 的 commmodeLabel）
// 所属云类别标签
function yunTypeLabel(yun_type: string) {
  const y = yunTypeOptions.value.find(x => x.value === yun_type)
  return y ? y.label : yun_type
}
// 理论订货日（门店订货日）选项：周一到周日，存储为 1-7
const weekdayOptions = [
  { label: '周一', value: '1' },
  { label: '周二', value: '2' },
  { label: '周三', value: '3' },
  { label: '周四', value: '4' },
  { label: '周五', value: '5' },
  { label: '周六', value: '6' },
  { label: '周日', value: '7' },
]
function weekdayLabel(value: string | null | undefined) {
  if (!value) return '-'
  const o = weekdayOptions.find(x => x.value === String(value))
  return o ? o.label : String(value)
}
// 负责区域标签
function areaCdLabel(areaCd: string) {
  const a = planAreas.value.find(x => (x.area_cd || '').trim() === areaCd)
  return a ? (a.name || a.area_nm) : areaCd
}
// 省/市/区/街道标签：详情页只读展示，按需懒加载对应级联下拉数据后再匹配名称
function geoPrvnLabel(code: string) {
  const p = geoProvinces.value.find(x => x.code === code)
  return p ? p.name : code
}
function geoCityLabel(code: string) {
  const c = geoCities.value.find(x => x.code === code)
  return c ? c.name : code
}
function geoAreaLabel(code: string) {
  const a = geoAreas.value.find(x => x.code === code)
  return a ? a.name : code
}
function geoStreetLabel(code: string) {
  const s = geoStreets.value.find(x => x.code === code)
  return s ? s.name : code
}

// 列表
const plans = ref<PlanRecord[]>([]); const loading = ref(false)
const page = ref(1); const perPage = ref(20); const total = ref(0)
const searchPlanno = ref(''); const searchCustNm = ref(''); const searchStatus = ref('')
const searchCustcard = ref(''); const searchPlantyp = ref('')
const searchDateFrom = ref(''); const searchDateTo = ref('')
const searchServeStatus = ref('')

watch(page, () => loadData()); watch(perPage, () => { page.value = 1; loadData() })
onMounted(() => { loadData(); loadModels(); loadClassOptions(); loadUserOptions(); initPlanGeo() })

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
// ---- geo 地理四级联动 ----
const geoProvinces = ref<{ code: string; name: string }[]>([])
const geoCities = ref<{ code: string; name: string }[]>([])
const geoAreas = ref<{ code: string; name: string }[]>([])
const geoStreets = ref<{ code: string; name: string }[]>([])
const geoCitiesLoading = ref(false)
const geoAreasLoading = ref(false)
const geoStreetsLoading = ref(false)
const planAreas = ref<{ area_cd: string; area_nm: string; name: string }[]>([])

async function initPlanGeo() {
  const [pvRes, ctRes, arRes] = await Promise.all([fetchGeoProvinces(), fetchGeoCities('31'), fetchAreas()])
  geoProvinces.value = pvRes.data || []
  geoCities.value = ctRes.data || []
  planAreas.value = arRes.data || []
}

async function onPlanGeoPrvnChange() {
  form.geo_city_cd = ''; form.geo_area_cd = ''; form.geo_street_cd = ''
  geoCities.value = []; geoAreas.value = []; geoStreets.value = []
  if (form.geo_prvn_cd) {
    geoCitiesLoading.value = true
    const res = await fetchGeoCities(form.geo_prvn_cd)
    geoCities.value = res.data || []
    geoCitiesLoading.value = false
  }
}

async function onPlanGeoCityChange() {
  form.geo_area_cd = ''; form.geo_street_cd = ''
  geoAreas.value = []; geoStreets.value = []
  if (form.geo_city_cd) {
    geoAreasLoading.value = true
    const res = await fetchGeoAreas(form.geo_city_cd)
    geoAreas.value = res.data || []
    geoAreasLoading.value = false
  }
}

async function onPlanGeoAreaChange() {
  form.geo_street_cd = ''
  geoStreets.value = []
  if (form.geo_area_cd) {
    geoStreetsLoading.value = true
    const res = await fetchGeoStreets(form.geo_area_cd)
    geoStreets.value = res.data || []
    geoStreetsLoading.value = false
  }
}

async function loadPlanGeoForEdit(prvnCd: string, cityCd: string, areaCd: string) {
  const tasks: Promise<void>[] = []
  if (prvnCd) tasks.push(fetchGeoCities(prvnCd).then(r => { geoCities.value = r.data || [] }))
  if (cityCd) tasks.push(fetchGeoAreas(cityCd).then(r => { geoAreas.value = r.data || [] }))
  if (areaCd) tasks.push(fetchGeoStreets(areaCd).then(r => { geoStreets.value = r.data || [] }))
  await Promise.all(tasks)
}

const form = reactive<PlanRecord & {
  deposit?: number; is_rent?: string; yun_type?: string; pos_item?: string;
  pos_from?: string; cust_useflg?: string; posid?: string;
  new_custcard?: string; new_custcd?: string; new_custnm?: string;
  new_address?: string; new_phoneno?: string; new_positem?: string; new_posid?: string;
  solve_type?: string; jl_contactor?: string; jl_phoneno?: string;
  classcd?: string; busityp?: string; is_contract?: string; pptcode?: string; commmode?: string;
  status?: string;
  call_serve?: boolean; serve_task?: string;
  geo_prvn_cd?: string; geo_city_cd?: string; geo_area_cd?: string; geo_street_cd?: string;
  area_cd?: string; location?: string;
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
  geo_prvn_cd: '', geo_city_cd: '', geo_area_cd: '', geo_street_cd: '', area_cd: '', location: '',
})
const saving = ref(false)

// openEdit 已合并到 openDialog(row?) 统一入口
function openCreate() {
  isEdit.value = false
  Object.assign(form, {
    planno: '', custnm: '', custcard: '', custcd: '', plantyp: '00', plan_status: '00',
    plandate: '', opercd: '', gendate: '',
    custrnm: '', address: '', contactor: '', phoneno: '', // custrnm 存储理论订货日（1-7）
    is_rent: 'N', deposit: 0, yun_type: '', pos_item: '',
    pos_from: '', cust_useflg: '0', posid: '',
    new_custcard: '', new_custcd: '', new_custnm: '', new_address: '', new_phoneno: '',
    new_positem: '', new_posid: '', solve_type: '',
    jl_contactor: '', jl_phoneno: '', classcd: '', busityp: '', is_contract: '0', pptcode: '', commmode: '',
    status: '00',
    call_serve: false, serve_task: '',
    geo_prvn_cd: '31', geo_city_cd: '3101', geo_area_cd: '', geo_street_cd: '', area_cd: '', location: '',
  })
  // 默认加载上海区县列表
  fetchGeoAreas('3101').then(r => { geoAreas.value = r.data || [] })
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      custnm: form.custnm, custcard: form.custcard, custrnm: form.custrnm, // custrnm=理论订货日（1-7）
      address: form.address, contactor: form.contactor, phoneno: form.phoneno,
      plantyp: form.plantyp, busityp: form.busityp, is_rent: form.is_rent,
      deposit: form.deposit, yun_type: form.yun_type, pos_item: form.pos_item,
      pos_from: form.pos_from, cust_useflg: form.cust_useflg, posid: form.posid,
      new_custcard: form.new_custcard, new_custcd: form.new_custcd,
      new_custnm: form.new_custnm, new_address: form.new_address, new_phoneno: form.new_phoneno,
      new_positem: form.new_positem, new_posid: form.new_posid, solve_type: form.solve_type,
      plandate: form.plandate, opercd: form.opercd, gendate: form.gendate,
      jl_contactor: form.jl_contactor, jl_phoneno: form.jl_phoneno,
      classcd: form.classcd, pptcode: form.pptcode, is_contract: form.is_contract, commmode: form.commmode,
      geo_prvn_cd: form.geo_prvn_cd, geo_city_cd: form.geo_city_cd,
      geo_area_cd: form.geo_area_cd, geo_street_cd: form.geo_street_cd,
      area_cd: form.area_cd, location: form.location,
    }
    // 新增/编辑时均传递呼出勾选与任务（编辑时支持更新呼出单）
    payload.call_serve = form.call_serve
    payload.serve_task = form.serve_task
    if (isEdit.value) {
      await updatePlan(form.planno, payload)
    } else {
      const r = await createPlan({ custcd: form.custcd, ...payload })
      const data = (r?.data as any) || {}
      // 回填后端自动生成的 planno 和 custcd（plantyp=00 全新开通场景，
      // 对齐 PB w_plan_cust_befor_new.srw of_insert_cust: SetItem(ll_row, 'CustCd', ls_Custcd)）
      if (data.planno) form.planno = data.planno
      if (data.custcd) form.custcd = data.custcd
    }
    dialogVisible.value = false; loadData(); ElMessage.success('保存成功')
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

// 详情抽屉
const drawerVisible = ref(false); const detail = ref<PlanRecord | null>(null); const detailTab = ref('info')
const serveRecords = ref<ServeRecord[]>([]); const serveLoading = ref(false)
const custDevices = ref<any[]>([]); const deviceLoading = ref(false)
const deviceHistory = ref<any[]>([]); const historyLoading = ref(false)

// 打开编辑对话框：先获取详情再回填，避免依赖列表页字段
async function openEdit(row: PlanRecord) {
  isEdit.value = true
  let detail = row as any
  try {
    const res = await fetchPlan(row.planno)
    if (res?.data) detail = res.data
  } catch { /* 降级使用列表行数据 */ }

  Object.assign(form, {
    planno: detail.planno,
    plantyp: detail.plantyp || '',
    plan_status: detail.plan_status || '',
    custcd: detail.custcd || '',
    custnm: detail.custnm || '',
    custcard: detail.custcard || '',
    custrnm: detail.custrnm || '', // custrnm 存储理论订货日（1-7）
    address: detail.address || '',
    contactor: detail.contactor || '',
    phoneno: detail.phoneno || '',
    new_custcard: detail.new_custcard || '',
    new_custcd: detail.new_custcd || '',
    new_custnm: detail.new_custnm || '',
    new_address: detail.new_address || '',
    new_phoneno: detail.new_phoneno || '',
    jl_contactor: detail.jl_contactor || '',
    jl_phoneno: detail.jl_phoneno || '',
    busityp: detail.busityp || '',
    classcd: detail.classcd || '',
    pptcode: detail.pptcode || '',
    commmode: detail.commmode || '',
    is_contract: detail.is_contract || '0',
    yun_type: detail.yun_type || '',
    pos_from: detail.pos_from || '',
    pos_item: detail.pos_item || '',
    posid: detail.posid || '',
    cust_useflg: detail.cust_useflg || '0',
    new_positem: detail.new_positem || '',
    new_posid: detail.new_posid || '',
    solve_type: detail.solve_type || '',
    deposit: detail.deposit || 0,
    is_rent: detail.is_rent || 'N',
    status: detail.status || '00',
    geo_prvn_cd: detail.geo_prvn_cd || '',
    geo_city_cd: detail.geo_city_cd || '',
    geo_area_cd: detail.geo_area_cd || '',
    geo_street_cd: detail.geo_street_cd || '',
    area_cd: detail.area_cd || '',
    location: detail.location || '',
    // 根据 serve_status 回填呼出勾选，任务描述异步加载
    call_serve: detail.serve_status === '01',
    serve_task: '',
  })
  // 反向加载地理级联下拉
  const p = detail.geo_prvn_cd || ''
  const c = detail.geo_city_cd || ''
  const a = detail.geo_area_cd || ''
  if (p || c || a) await loadPlanGeoForEdit(p, c, a)
  // 加载当前机型对应的可用 EID 列表（方案 A 预绑定设备）
  if (showEidPicker.value && detail.pos_item) {
    loadAvailableEids(detail.pos_item)
  }
  // 如果已有待呼出单，加载其任务描述
  if (detail.serve_status === '01') {
    try {
      const res = await fetchPlanServes(detail.planno)
      const serves = (res?.data || []) as ServeRecord[]
      const pending = serves.find(s => s.status === '00')
      if (pending) form.serve_task = pending.serve_task || ''
    } catch { /* ignore */ }
  }
  dialogVisible.value = true
}

async function openDetail(row: PlanRecord) {
  detail.value = row; drawerVisible.value = true; detailTab.value = 'info'
  // 获取完整详情（补充 tmm22_customers 才有的地理/负责区域字段），并加载对应级联下拉数据以便解析名称
  try {
    const res = await fetchPlan(row.planno)
    if (res?.data) {
      detail.value = res.data
      const d = res.data as any
      const p = d.geo_prvn_cd || ''
      const c = d.geo_city_cd || ''
      const a = d.geo_area_cd || ''
      if (p || c || a) await loadPlanGeoForEdit(p, c, a)
    }
  } catch { /* 降级使用列表行数据 */ }
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
/* EID 下拉选项 */
.eid-option { display:flex; align-items:center; width:100%; gap:10px }
.eid-option .eid-code { min-width:120px; font-weight:600 }
.eid-option .eid-wh { color:#67c23a; font-size:12px; min-width:80px }
.eid-option .eid-asset { color:#e6a23c; font-size:12px; min-width:60px }
.eid-option .eid-qc { color:#909399; font-size:12px; min-width:50px }
</style>
