procedure usp_itsm_extend_new(i_opbillid in varchar2,
                                                i_type     in char,
                                                i_oper     in char,
                                                o_return   out varchar2)

 as
  v_id      varchar2(8);
  v_num     number;
  v_str     varchar2(200);
  v_mopen   tit13_maintenance_open%rowtype;
  v_mren    tit15_maintenance_renovate%rowtype;
  v_mchange TIT16_DEVICE_CHANGE%rowtype;
  v_mclose  TIT18_STORE_CLOSE%rowtype;
  v_replace TIT28_FREE_REPLACE%rowtype;
begin
  -- 新机开通单
  if i_type = 'XZ' then
    for ext in (select e.*, t.gendate, c.classcd, t.sltyp
                  from tsl01_extend t, tsl02_extenddt e, tmm22_customers c
                 where t.opbillid = e.opbillid
                   and e.custcd = c.custcd
                   and t.opbillid = i_opbillid
                   and c.useflg = '1'
                   and t.auditflg = '1') loop
      if ext.sltyp <> i_type then
        rollback;
        o_return := '单据类型错误！';
        return;
      end if;

      begin
        for i in 1 .. nvl(ext.planqty, 1) loop
          v_mopen := null;

          v_id := UF_GET_BILLNOU('MO');
          if length(v_id) <> 8 then
            rollback;
            o_return := '新增itsm设备开通记录错误！';
            return;
          end if;
          v_mopen.NEW_OPENING_ID           := v_id; --新机开通表ID
          v_mopen.COMPANY_ID               := ext.classcd; --所属区域公司ID（来源仓储）
          v_mopen.STORE_ID                 := ext.CUSTCD; --门店ID（来源仓储）
          v_mopen.REQUEST_TIME             := trunc(nvl(ext.impdate, ext.GENDATE)); --请求时间（来源仓储）
          v_mopen.REQUSET_PAPER_ID         := ext.opbillid; --仓储请求单ID（来源仓储）
          v_mopen.DEVICE_ID                := null; --整机编号
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

          begin
            insert into tit13_maintenance_open values v_mopen;
          exception
            when others then
              raise_application_error(-20010, '新增itsm设备开通记录错误！');
              rollback;
              o_return := '新增itsm设备开通记录错误！';
              return;
          end;

          v_num := UF_INSERT_BUSINESS(v_id,
                                      '新机开通单',
                                      'sys',
                                      '新建新机开通维护单:' || v_id,
                                      'N');
          if v_num < 0 then
            raise_application_error(-20010, '新增itsm设备开通记录错误！');
            rollback;
            o_return := '记录业务操作流水失败错误！';
            return;
          end if;

        end loop;
      end;

    end loop;
  elsif i_type = 'GX' then
    --旧机翻新
    for ext in (select e.*, t.gendate, c.classcd, t.sltyp
                  from tsl01_extend t, tsl02_extenddt e, tmm22_customers c
                 where t.opbillid = e.opbillid
                   and e.custcd = c.custcd
                   and t.opbillid = i_opbillid
                   and c.useflg = '1'
                   and t.auditflg = '1') loop
      if ext.sltyp <> i_type then
        rollback;
        o_return := '单据类型错误！';
        return;
      end if;
      begin
        for i in 1 .. nvl(ext.planqty, 1) loop
          v_mren :=null;

          v_id := UF_GET_BILLNOU('MR');
          if length(v_id) <> 8 then
            rollback;
            o_return := '新增itsm旧机翻新记录错误！';
            return;
          end if;
          v_mren.RENEW_ID                 := v_id; --旧机翻新表id
          v_mren.COMPANY_ID               := ext.classcd; --上级机构
          v_mren.STORE_ID                 := ext.CUSTCD; --门店id
          v_mren.REQUEST_TIME             := trunc(nvl(ext.impdate, ext.GENDATE)); --请求时间
          v_mren.REQUSET_PAPER_ID         := ext.opbillid; --仓储请求单ID（来源仓储）
          v_mren.OLD_DEVICE_ID            := null; --旧设备编号
          v_mren.NEW_DEVICE_ID            := null; --换新设备编号
          v_mren.COUNT                    := 1; --翻新更数量
          v_mren.EXPECTED_COMPLETION_TIME := null; --合同要求完成时间
          v_mren.SHORT_DESCRIPTION        := null; --简述
          v_mren.DETAIL_DESCRIPTION       := null; --详细描述
          v_mren.CURRENT_STATUS           := '1'; --当前状态
          v_mren.IS_OLD                   := 'N'; --是否补单
          v_mren.CREATE_TIME              := sysdate; --创建时间
          v_mren.CREATOR                  := 'sys'; --创建人
          v_mren.UPDATE_TIME              := null; --更新时间
          v_mren.UPDATOR                  := null; --更新人
          v_mren.FIRSTOR                  := null; --第一次上门工程师id
          v_mren.FIRST_TIME               := null; --第一次上门时间
          v_mren.LEAVE_TIME               := null; --第一次离店时间
          v_mren.CLOSE_TIME               := null; --关单时间
          v_mren.REVISIT_TIME             := null; --回访时间
          v_mren.is_back                  := ext.IS_BACK ; --是否返回
          begin
            insert into tit15_maintenance_renovate values v_mren;
          exception
            when others then
              raise_application_error(-20010, '新增itsm旧机翻新记录错误！');
              rollback;
              o_return := '新增itsm旧机翻新记录错误！';
              return;
          end;

          v_num := UF_INSERT_BUSINESS(v_id,
                                      '旧机翻新单',
                                      'sys',
                                      '新建旧机翻新维护单:' || v_id,
                                      'N');
          if v_num < 0 then
            raise_application_error(-20010, '新增itsm旧机翻新记录错误！');
            rollback;
            o_return := '记录业务操作流水失败错误！';
            return;
          end if;

        end loop;
      end;

    end loop;
    --设备变更
  ELSIF i_type = 'BG'or i_type = 'CK'or i_type = 'BQ' THEN
    for ext in (select e.*, t.gendate, c.classcd, t.sltyp
                  from tsl01_extend t, tsl02_extenddt e, tmm22_customers c
                 where t.opbillid = e.opbillid
                   and e.custcd = c.custcd
                   and t.opbillid = i_opbillid
                   and c.useflg = '1'
                   and t.auditflg = '1') loop
      if ext.sltyp <> i_type then
        rollback;
        o_return := '设备变更单据类型错误！';
        return;
      end if;

      begin
        for i in 1 .. nvl(ext.planqty, 1) loop
          v_mchange := null;

          v_id := UF_GET_BILLNOU('BG');
          if length(v_id) <> 8 then
            rollback;
            o_return := '新增itsm设备变更记录错误！';
            return;
          end if;
          v_str := '';

          v_mchange.DEVICE_CHANGE_ID         := v_id; --设备变更ID
          v_mchange.STORE_ID                 := ext.CUSTCD; --门店ID（来源仓储）
          v_mchange.REQUSET_PAPER_ID         := ext.opbillid; --变更请求单ID
          v_mchange.CHANGE_TYPE              := i_type; --变更类型
          v_mchange.NEW_ADDRESS              := ext.NEWADDRESS; --变更地址
          v_mchange.NEW_STORE_CARD           := ext.newcustcard; --变更磁卡
          v_mchange.NEW_STORE_ID             := ext.newcustcd; --变更门店
          v_mchange.NEW_TEL                  := ext.N_PHONENO ; --变更电话
          v_mchange.NEW_CONTACTOR            := ext.n_contactor ; --变更联系人

          v_mchange.IS_STORE_INSIDE_CHANGE   := 'N'; --是否店内移机
          v_mchange.REQUEST_TIME             := trunc(nvl(ext.impdate,ext.GENDATE)); --请求时间（来源仓储）
          v_mchange.EXPECTED_COMPLETION_TIME := null; --合同要求完成时间（来源仓储）
          v_mchange.SHORT_DESCRIPTION        := null; --简述
          if ext.newcustcard <> ext.custcard then
            v_str := ' 原磁卡号 :'||  ext.custcard;
          end if;
          if ext.n_name <> ext.O_NAME then
            v_str := ' 原店名 :'||  ext.O_NAME;
          end if;
          if ext.newaddress  <> ext.address then
            v_str := ' 原地址 :'||  ext.newaddress;
          end if;
          v_mchange.DETAIL_DESCRIPTION       := trim(v_str); --详细描述

          v_mchange.DEVICE_ID             := ext.eid ; --变更POS 20180201

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

          v_num := UF_INSERT_BUSINESS(v_id,
                                      '设备变更单',
                                      'sys',
                                      '新建设备变更维护单:' || v_id,
                                      'N');
          if v_num < 0 then
            raise_application_error(-20010, '新增itsm设备变更记录错误！');
            rollback;
            o_return := '记录业务操作流水失败错误！';
            return;
          end if;
        end loop;
      end;

    end loop;
    --门店关闭
  ELSIF i_type = 'GB' THEN
    for ext in (select e.*, t.gendate, c.classcd, t.sltyp
                  from tsl01_extend t, tsl02_extenddt e, tmm22_customers c
                 where t.opbillid = e.opbillid
                   and e.custcd = c.custcd
                   and t.opbillid = i_opbillid
                   and c.useflg = '1'
                   and t.auditflg = '1') loop

      v_mclose := null;

      if ext.sltyp <> i_type then
        rollback;
        o_return := '门店关闭单据类型错误！';
        return;
      end if;
      v_id := UF_GET_BILLNOU('GB');
      if length(v_id) <> 8 then
        rollback;
        o_return := '新增itsm门店关闭记录错误！';
        return;
      end if;
      v_mclose.STORE_CLOSE_ID           := v_id; --门店关闭ID
      v_mclose.STORE_ID                 := ext.CUSTCD; --门店ID（来源仓储）
      v_mclose.REQUEST_TIME             := trunc(nvl(ext.impdate, ext.GENDATE)); --请求时间（来源仓储）
      v_mclose.REQUSET_PAPER_ID         := ext.opbillid; --请求ID（来源仓储）
      v_mclose.CLOSE_TYPE               := 'YJ'; --关闭类型
      v_mclose.TEMP_CLOSE_DATE_BEGIN    := null; --临时关闭开始时间
      v_mclose.TEMP_CLOSE_DATE_END      := null; --临时关闭结束时间
      v_mclose.EXPECTED_COMPLETION_TIME := null; --合同要求完成时间（来源仓储）
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

      v_num := UF_INSERT_BUSINESS(v_id,
                                  '门店关闭单',
                                  'sys',
                                  '新建门店关闭维护单:' || v_id,
                                  'N');
      if v_num < 0 then
        raise_application_error(-20010, '新增itsm门店关闭记录错误！');
        rollback;
        o_return := '记录业务操作流水失败错误！';
        return;
      end if;
    end loop;
    --免费更换
  ELSIF i_type = 'GH' THEN
    for ext in (select e.*, t.gendate, c.classcd, t.sltyp
                  from tsl01_extend t, tsl02_extenddt e, tmm22_customers c
                 where t.opbillid = e.opbillid
                   and e.custcd = c.custcd
                   and t.opbillid = i_opbillid
                   and c.useflg = '1'
                   and t.auditflg = '1') loop
      if ext.sltyp <> i_type then
        rollback;
        o_return := '免费更换单据类型错误！';
        return;
      end if;

      begin
        for i in 1 .. nvl(ext.planqty, 1) loop
          v_replace := null;
          v_id := UF_GET_BILLNOU('GH');
          if length(v_id) <> 8 then
            rollback;
            o_return := '新增itsm免费更换记录错误！';
            return;
          end if;
          v_replace.RENEW_ID                 := v_id; --门店关闭ID
          v_replace.company_id               := ext.classcd; --所属区域公司ID（来源仓储）
          v_replace.STORE_ID                 := ext.CUSTCD; --门店ID（来源仓储）
          v_replace.REQUEST_TIME             := trunc(nvl(ext.impdate,ext.GENDATE)); --请求时间（来源仓储）
          v_replace.REQUSET_PAPER_ID         := ext.opbillid; --请求ID（来源仓储）
          v_replace.OLD_DEVICE_ID            := null; --旧设备ID
          v_replace.NEW_DEVICE_ID            := null; --新设备ID
          v_replace.COUNT                    := 1; --更换数量
          v_replace.EXPECTED_COMPLETION_TIME := null; --合同要求完成时间（来源仓储）
          v_replace.is_old                   := 'N'; --是否补单
          v_replace.is_back                  := ext.IS_BACK ; --是否返回
          v_replace.SHORT_DESCRIPTION        := null; --简述
          v_replace.DETAIL_DESCRIPTION       := null; --详细描述
          v_replace.CURRENT_STATUS           := 1; --当前状态
          v_replace.CREATE_TIME              := SYSDATE; --创建时间
          v_replace.CREATOR                  := i_oper; --创建人
          v_replace.UPDATE_TIME              := null; --更新时间
          v_replace.UPDATOR                  := null; --更新人
          v_replace.FIRSTOR                  := null; --第一次上门工程师ID
          v_replace.FIRST_TIME               := null; --第一次上门时间
          v_replace.LEAVE_TIME               := null; --第一次离开时间
          v_replace.CLOSE_TIME               := null; --关单时间
          v_replace.REVISIT_TIME             := null; --回访时间

          begin
            insert into TIT28_FREE_REPLACE values v_replace;
          exception
            when others then
              raise_application_error(-20010, '新增itsm免费更换记录错误！');
              rollback;
              o_return := '新增its免费更换记录错误！';
              return;
          end;

          v_num := UF_INSERT_BUSINESS(v_id,
                                      '免费更换单',
                                      'sys',
                                      '新建免费更换维护单:' || v_id,
                                      'N');
          if v_num < 0 then
            raise_application_error(-20010, '新增itsm免费更换记录错误！');
            rollback;
            o_return := '记录业务操作流水失败错误！';
            return;
          end if;
        end loop;
      end;

    end loop;
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
