function UF_INSERT_BUSINESS(IN_BILLNO     IN VARCHAR2,
                                              IN_OPERATION  IN VARCHAR2,
                                              IN_OPERATOR   IN CHAR,
                                              IN_DECRIPTION IN VARCHAR2,
                                              in_flag       in char)

 return number as

  Result     number;
  V_BUSINESS TIT20_BUSINESS_OPERATION%ROWTYPE;

begin
  --取流水表当前单据流水
  Result := UF_GET_BUSINESSID(IN_BILLNO);
  IF Result = -1 THEN
    GOTO ENDOFFUN;
  END IF;

  V_BUSINESS.business_operation_id := Result; --业务流水操作表ID
  V_BUSINESS.maintenance_id        := IN_BILLNO; --维护单ID
  V_BUSINESS.operation_name        := IN_OPERATION; --操作名称
  V_BUSINESS.status                := '1'; --操作状态
  V_BUSINESS.result                := '1'; --操作结果
  V_BUSINESS.exemption_status      := '1'; --免责状态
  V_BUSINESS.operator              := IN_OPERATOR; --操作人
  V_BUSINESS.operate_time          := sysdate; --操作时间
  V_BUSINESS.operate_time_length   := null; --操作时长
  V_BUSINESS.operate_decription    := IN_DECRIPTION; --操作过程描述
  V_BUSINESS.create_time           := sysdate; --创建时间
  V_BUSINESS.creator               := IN_OPERATOR; --创建人
  V_BUSINESS.update_time           := null; --更新时间
  V_BUSINESS.updator               := null; --更新人
  begin
    insert into TIT20_BUSINESS_OPERATION values V_BUSINESS;
  exception
    when others then
      raise_application_error(-20010, '新增单据流水记录错误！');
      rollback;
      return - 2;
  end;
  if in_flag = 'Y' then
    COMMIT;
  end if;
  <<ENDOFFUN>>

  return Result;

end UF_INSERT_BUSINESS;
