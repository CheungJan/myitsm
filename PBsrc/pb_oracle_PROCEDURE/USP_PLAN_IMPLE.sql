procedure usp_plan_imple(i_planno in varchar2,
                                         i_type     in char,
                                         i_oper     in char,
                                         o_return   out varchar2)

 as
  v_id      varchar2(8);
 -- v_num     number;
  v_str     varchar2(200);

  V_PLAN    plan_cust%rowtype;

  v_mopen   tit13_maintenance_open%rowtype;
  v_mren    TIT15_MAINTENANCE_RENOVATE%rowtype;
  v_mchange TIT16_DEVICE_CHANGE%rowtype;
  v_mclose  TIT18_STORE_CLOSE%rowtype;
  --v_replace TIT28_FREE_REPLACE%rowtype;
  v_maint TIT10_MAINTENANCEDAY%rowtype;
begin
  -- 新机开通单
                                      --门店移机这里要加客户代码,避免磁卡号变更
  SELECT CUSTCARD,
         CLASSCD ,      	CUSTCD,       	POS_FROM,       	NEW_CUSTCARD,
         NEW_POSITEM,   	NEW_POSID  , 	SOLVE_TYPE, 		CUST_USEFLG,
         POSID            ,
         NEW_CUSTCD,        NEW_PHONENO,    NEW_ADDRESS,        NEW_CUSTNM
    INTO V_PLAN.CUSTCARD,
         V_PLAN.CLASSCD,	V_PLAN.CUSTCD,	V_PLAN.POS_FROM,	V_PLAN.NEW_CUSTCARD,
         V_PLAN.NEW_POSITEM,V_PLAN.NEW_POSID,V_PLAN.SOLVE_TYPE, V_PLAN.CUST_USEFLG,
         V_PLAN.POSID      ,
         V_PLAN.NEW_CUSTCD ,V_PLAN.NEW_PHONENO  ,V_PLAN.NEW_ADDRESS  ,V_PLAN.NEW_CUSTNM
   FROM PLAN_CUST WHERE PLANNO = i_planno;


  IF i_type = '00' THEN

      v_mopen := null;


      v_id := UF_GET_BILLNOU('MO');
      if length(v_id) <> 8 then
        rollback;
        o_return := '新增itsm设备开通记录错误！';
        return;
      end if;
      v_mopen.NEW_OPENING_ID           := v_id; --新机开通表ID
      v_mopen.COMPANY_ID               := V_PLAN.CLASSCD; --所属区域公司ID（来源仓储）
      v_mopen.STORE_ID                 := V_PLAN.CUSTCD; --门店ID（来源仓储）
      v_mopen.REQUEST_TIME             := sysdate; --请求时间（来源仓储）
      v_mopen.REQUSET_PAPER_ID         := i_planno; --仓储请求单ID（来源仓储）
      v_mopen.DEVICE_ID                := V_PLAN.NEW_POSID; --计划设备（移出设备ID）
      v_mopen.count                    := 1; --开通数量 默认1
      v_mopen.EXPECTED_COMPLETION_TIME := null; --合同要求完成时间（来源仓储）
      v_mopen.DELIVER_NO               := null; --送货单号
      v_mopen.SHORT_DESCRIPTION        := null; --简述
      v_mopen.DETAIL_DESCRIPTION       := null; --详细描述
      v_mopen.CURRENT_STATUS           := 1; --当前状态
      v_mopen.IS_OLD                   := 'N'; --是否补单
      v_mopen.CREATE_TIME              := SYSDATE; --创建时间
      v_mopen.CREATOR                  := i_oper; --创建人
      v_mopen.UPDATE_TIME              := null; --更新时间
      v_mopen.UPDATOR                  := null; --更新人
      v_mopen.FIRSTOR                  := null; --第一次上门工程师ID
      v_mopen.FIRST_TIME               := null; --第一次上门时间
      v_mopen.LEAVE_TIME               := null; --第一次离店时间
      v_mopen.CLOSE_TIME               := null; --关单时间
      v_mopen.REVISIT_TIME             := null; --回访时间

      v_mopen.FROM_CUSTCARD        := V_PLAN.NEW_CUSTCARD; --移出门店磁卡号

      --select custcd into V_PLAN.NEW_CUSTCD from tmm22_cu  where custcard = V_PLAN.NEW_CUSTCARD ;
      --v_mopen.FROM_CUSTCD        := V_PLAN.NEW_CUSTCD; --移出门店代码

      begin
        insert into tit13_maintenance_open values v_mopen;
      exception
        when others then
          raise_application_error(-20010, '新增开通记录错误！');
          rollback;
          o_return := '新增开通记录错误！';
          return;
      end;


  ELSIF i_type = '10' THEN
    --磁卡号变更
    v_mchange := null;

    v_id := UF_GET_BILLNOU('BG');
    if length(v_id) <> 8 then
       rollback;
       o_return := '新增itsm设备变更记录错误！';
       return;
    end if;


	  v_mchange.DEVICE_CHANGE_ID         := v_id; --设备变更ID
	  v_mchange.STORE_ID                 := V_PLAN.CUSTCD; --门店ID
	  v_mchange.REQUSET_PAPER_ID         := i_planno; --变更请求单ID
	  v_mchange.CHANGE_TYPE              := 'CK'; --变更类型
	  v_mchange.DEVICE_ID                := V_PLAN.POSID; --变更POS
	  v_mchange.NEW_ADDRESS              := V_PLAN.NEW_ADDRESS ; --变更地址
	  v_mchange.NEW_STORE_CARD           := V_PLAN.CUSTCARD; --变更磁卡
	  --v_mchange.NEW_STORE_ID             := ext.newcustcd; --变更门店
	  v_mchange.NEW_TEL                  := V_PLAN.NEW_PHONENO ; --变更电话
	  --v_mchange.NEW_CONTACTOR            := ext.n_contactor ; --变更联系人
	  --v_mchange.NEW_NAME               := V_PLAN.NEW_CUSTNM

	  v_mchange.IS_STORE_INSIDE_CHANGE   := 'N'; --是否店内移机
	  v_mchange.REQUEST_TIME             := sysdate; --请求时间
	  v_mchange.EXPECTED_COMPLETION_TIME := null; --合同要求完成时间
	  v_mchange.SHORT_DESCRIPTION        := null; --简述
	
	    v_str := ' 原磁卡号 :'||  V_PLAN.NEW_custcard||' 原店名 :'||  V_PLAN.NEW_CUSTNM||' 原地址 :'||  V_PLAN.NEW_ADDRESS;

	
	  v_mchange.DETAIL_DESCRIPTION       := trim(v_str); --详细描述
	
	  v_mchange.CURRENT_STATUS           := 1; --当前状态
	  v_mchange.IS_OLD                   := 'N'; --是否补单
	  v_mchange.CREATE_TIME              := SYSDATE; --创建时间
	  v_mchange.CREATOR                  := i_oper; --创建人
	  v_mchange.UPDATE_TIME              := null; --更新时间
	  v_mchange.UPDATOR                  := null; --更新人
	  v_mchange.FIRSTOR                  := null; --第一次上门工程师ID
	  v_mchange.FIRST_TIME               := null; --第一次上门时间
	  v_mchange.CLOSE_TIME               := null; --关单时间
	  v_mchange.REVISIT_TIME             := null; --回访时间
	
	  begin
	    insert into TIT16_DEVICE_CHANGE values v_mchange;
	  exception
	    when others then
	      raise_application_error(-20010, '新增itsm设备变更记录错误！');
	      rollback;
	      o_return := '新增itsm设备变更记录错误！';
	      return;
	  end;

  ELSIF i_type = '20' THEN
   --旧机翻新
    v_mren :=null;

    v_id := UF_GET_BILLNOU('MR');
    IF length(v_id) <> 8 THEN
       rollback;
       o_return := '新增itsm旧机翻新记录错误！';
       return;
    END IF;

  	v_mren.RENEW_ID                 := v_id; --旧机翻新表id
  	v_mren.COMPANY_ID               := V_PLAN.CLASSCD;
  	v_mren.STORE_ID                 := V_PLAN.CUSTCD; --门店id
  	v_mren.REQUEST_TIME             := sysdate; --请求时间
  	v_mren.REQUSET_PAPER_ID         := i_planno; --仓储请求单ID（来源仓储）
 	 v_mren.OLD_DEVICE_ID           := V_PLAN.POSID; --旧设备编号
  	v_mren.NEW_DEVICE_ID            := V_PLAN.NEW_POSID; --换新设备编号
  	v_mren.COUNT                    := 1; --翻新更数量
  	v_mren.EXPECTED_COMPLETION_TIME := null; --合同要求完成时间
  	v_mren.SHORT_DESCRIPTION        := null; --简述
  	v_mren.DETAIL_DESCRIPTION       := null; --详细描述
  	v_mren.CURRENT_STATUS           := '1'; --当前状态
  	v_mren.IS_OLD                   := 'N'; --是否补单
  	v_mren.CREATE_TIME              := sysdate; --创建时间
  	v_mren.CREATOR                  := i_oper; --创建人
  	v_mren.UPDATE_TIME              := null; --更新时间
  	v_mren.UPDATOR                  := null; --更新人
  	v_mren.FIRSTOR                  := null; --第一次上门工程师id
  	v_mren.FIRST_TIME               := null; --第一次上门时间
  	v_mren.LEAVE_TIME               := null; --第一次离店时间
  	v_mren.CLOSE_TIME               := null; --关单时间
  	v_mren.REVISIT_TIME             := null; --回访时间
  	v_mren.is_back                  := '0'; --处理方式

  	begin
   	 insert into tit15_maintenance_renovate values v_mren;
     exception
        when others then
         raise_application_error(-20010, '新增itsm旧机翻新记录错误！');
         rollback;
         o_return := '新增itsm旧机翻新记录错误！';
         return;
    end;
 	
 	IF trim(V_PLAN.SOLVE_TYPE)='1' THEN --回收旧机
 	
 	   v_maint := null;
      v_id := UF_GET_BILLNOU('MD');  --这里要另外新加个变量
	    IF length(v_id) <> 8 THEN
	       rollback;
	       o_return := '新增维护取机单号错误！';
	       return;
	    END IF;
 	
 	   v_maint.MAINTENANCE_ID           := v_id; --旧机翻新表id
	   v_maint.COMPANY_ID               := V_PLAN.CLASSCD;
  	   v_maint.STORE_ID                 := V_PLAN.CUSTCD; --门店id
  	   v_maint.TEMP_CONTRACT            := null;
  	   v_maint.FAULT_TYPE               := '3'; --
  	   v_maint.SERVRITY        		    := '1'; --
 	   v_maint.EMERGENCY_LEVEL          := '1'; --
  	   v_maint.PRIORITY           		:= '2'; --
 	   --v_maint.REQUESTER                :=
 	   v_maint.REQUEST_TIME             := sysdate;
 	   v_maint.DELIVER_NO               := null;
 	   v_maint.SHORT_DESCRIPTION        := '业务软件';
 	   v_maint.DETAIL_DESCRIPTION       := '计划取回:'||i_planno;
 	   --v_maint.DEVICE_ID                :=
      v_maint.IS_OLD           := 'N'; --
 	   v_maint.CURRENT_STATUS           := '1'; --当前状态
 	   v_maint.CREATE_TIME              := sysdate; --创建时间
   	   v_maint.CREATOR                  := i_oper; --创建人
  	   v_maint.UPDATE_TIME              := null; --更新时间
  	   v_maint.UPDATOR                  := null; --更新人
  	   v_maint.FIRSTOR                  := null; --第一次上门工程师id
  	   v_maint.FIRST_TIME               := null; --第一次上门时间
  	   v_maint.LEAVE_TIME               := null; --第一次离店时间
  	   v_maint.CLOSE_TIME               := null; --关单时间
  	   v_maint.REVISIT_TIME             := null; --回访时间
  	   v_maint.REQUSET_PAPER_ID                   := i_planno; --计划单号
 	
 	   begin
	   	 insert INTO TIT10_MAINTENANCEDAY values v_maint;
	 	 exception
	    	when others then
	     	 raise_application_error(-20010, '新增设备取回记录错误！');
	     	 rollback;
	     	 o_return := '新增设备取回记录错误！';
	     	 return;
	 	end;
 	END IF ;
 	
  ELSIF i_type = '30' THEN  --
    --设备取回
      v_maint := null;
      v_id := UF_GET_BILLNOU('MD');  --这里要另外新加个变量
	    IF length(v_id) <> 8 THEN
	       rollback;
	       o_return := '新增维护取机单号错误！';
	       return;
	    END IF;
 	
 	   v_maint.MAINTENANCE_ID           := v_id; --旧机翻新表id
	   v_maint.COMPANY_ID               := V_PLAN.CLASSCD;
  	   v_maint.STORE_ID                 := V_PLAN.CUSTCD; --门店id
  	   v_maint.TEMP_CONTRACT            := null;
  	   v_maint.FAULT_TYPE               := '3'; --
  	   v_maint.SERVRITY        		    := '1'; --
 	   v_maint.EMERGENCY_LEVEL          := '1'; --
  	   v_maint.PRIORITY           		:= '2'; --
 	   --v_maint.REQUESTER                :=
 	   v_maint.REQUEST_TIME             := sysdate;
 	   v_maint.DELIVER_NO               := null;
 	   v_maint.SHORT_DESCRIPTION        := '计划取机';
 	   v_maint.DETAIL_DESCRIPTION       := '计划取回:'||i_planno;
 	   --v_maint.DEVICE_ID                :=
      v_maint.IS_OLD           := 'N'; --
 	   v_maint.CURRENT_STATUS           := '1'; --当前状态
 	   v_maint.CREATE_TIME              := sysdate; --创建时间
   	   v_maint.CREATOR                  := i_oper; --创建人
  	   v_maint.UPDATE_TIME              := null; --更新时间
  	   v_maint.UPDATOR                  := null; --更新人
  	   v_maint.FIRSTOR                  := null; --第一次上门工程师id
  	   v_maint.FIRST_TIME               := null; --第一次上门时间
  	   v_maint.LEAVE_TIME               := null; --第一次离店时间
  	   v_maint.CLOSE_TIME               := null; --关单时间
  	   v_maint.REVISIT_TIME             := null; --回访时间
 	   v_maint.REQUSET_PAPER_ID                   := i_planno; --计划单号
 	   begin
	   	 insert INTO TIT10_MAINTENANCEDAY values v_maint;
	 	 exception
	    	when others then
	     	 raise_application_error(-20010, '新增设备取回记录错误！');
	     	 rollback;
	     	 o_return := '新增设备取回记录错误！';
	     	 return;
	 	end;
  ELSIF i_type = '40' THEN
    --门店关闭
      v_mclose := null;

      v_id := UF_GET_BILLNOU('GB');
      if length(v_id) <> 8 then
        rollback;
        o_return := '新增itsm门店关闭记录错误！';
        return;
      end if;
      v_mclose.STORE_CLOSE_ID           := v_id; --门店关闭ID
      v_mclose.STORE_ID                 := V_PLAN.CUSTCD; --门店ID
      v_mclose.REQUEST_TIME             := sysdate; --请求时间
      v_mclose.REQUSET_PAPER_ID         := i_planno; --请求ID
      v_mclose.CLOSE_TYPE               := 'YJ'; --关闭类型
      v_mclose.TEMP_CLOSE_DATE_BEGIN    := null; --临时关闭开始时间
      v_mclose.TEMP_CLOSE_DATE_END      := null; --临时关闭结束时间
      v_mclose.EXPECTED_COMPLETION_TIME := null; --合同要求完成时间
      v_mclose.SHORT_DESCRIPTION        := null; --简述
      v_mclose.DETAIL_DESCRIPTION       := null; --详细描述
      v_mclose.CURRENT_STATUS           := 1; --当前状态
      v_mclose.is_old                   := 'N'; --是否补单
      v_mclose.CREATE_TIME              := SYSDATE; --创建时间
      v_mclose.CREATOR                  := i_oper; --创建人
      v_mclose.UPDATE_TIME              := null; --更新时间
      v_mclose.UPDATOR                  := null; --更新人
      v_mclose.FIRSTOR                  := null; --第一次上门工程师ID
      v_mclose.FIRST_TIME               := null; --第一次上门时间
      v_mclose.CLOSE_TIME               := null; --关单时间
      v_mclose.REVISIT_TIME             := null; --回访时间

      begin
        insert into TIT18_STORE_CLOSE values v_mclose;
      exception
        when others then
          raise_application_error(-20010, '新增itsm门店关闭记录错误！');
          rollback;
          o_return := '新增itsm门店关闭记录错误！';
          return;
      end;

  else
    rollback;
    o_return := '单据类型错误！';
    return;
  end if;

  -------------------------
  o_return := 'OK';
  -------------------

EXCEPTION
  when others then
    o_return := sqlcode || sqlerrm;

end;
