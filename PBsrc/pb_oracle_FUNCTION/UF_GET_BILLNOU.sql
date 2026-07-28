function UF_GET_BILLNOU(IN_BILLTYPE IN VARCHAR2)

 return varchar2 as

  Result varchar2(50);

  	v_CurBillNo integer;

    v_MaxBillNo integer;

  begin



  select CurBillId, MaxBillId

  into v_CurBillNo, v_MaxBillNo

  from tmm34_IdMaster

  where IdTyp = IN_BILLTYPE;



   if v_CurBillNo >= v_MaxBillNo then

     Result :=-1;

     ROLLBACK;

      GOTO ENDOFFUN;

   end if;

   v_CurBillNo  := v_CurBillNo +1;



   update tmm34_IdMaster

   set CurBillId = v_CurBillNo

   where IdTyp = IN_BILLTYPE ;

   --  COMMIT;
   if IN_BILLTYPE <> 'RQ' and IN_BILLTYPE <> 'RS' then
      Result := IN_BILLTYPE || lpad(to_char(v_CurBillNo),6,0) ;
   ELSE
       Result := lpad(to_char(v_CurBillNo),8,0) ;
   end if;

  <<ENDOFFUN>>



  return Result;

end UF_GET_BILLNOU;

