function UF_GET_BUSINESSID(IN_BILLNO IN VARCHAR2)

 return NUMBER as

  Result NUMBER;

  v_CurBillNo NUMBER;

  v_MaxBillNo NUMBER;

begin

  select COUNT(business_operation_id),nvl(MAX(BUSINESS_OPERATION_ID),0)

    into v_CurBillNo, v_MaxBillNo

    from TIT20_BUSINESS_OPERATION

   where maintenance_id = IN_BILLNO;

  if v_CurBillNo > v_MaxBillNo then

    Result := -1;

    GOTO ENDOFFUN;

  end if;

  Result := v_MaxBillNo + 1;

  <<ENDOFFUN>>

  return Result;

end UF_GET_BUSINESSID;
