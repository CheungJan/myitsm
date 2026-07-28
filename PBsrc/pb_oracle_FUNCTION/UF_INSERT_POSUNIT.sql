FUNCTION UF_INSERT_POSUNIT(IN_CUSTCD     IN VARCHAR2,
                                             IN_OPERCD     IN VARCHAR2
                                          )

 RETURN VARCHAR2
 AS
  V_RET     VARCHAR2(100);
  V_NUM     NUMBER;
  V_OPERCD  CHAR(6);

  --
    --更新客户信息同步24零管库
  --
BEGIN


  BEGIN
    SELECT COUNT(1) INTO V_NUM FROM TMM35_CUST_POS_RL
     WHERE CUSTCD = IN_CUSTCD AND USEFLG = '1';
  EXCEPTION
    WHEN OTHERS THEN
      V_RET := '客户资产未找到资产信息!';
      RETURN V_RET;
  END;

  IF IN_OPERCD IS NULL THEN
     SELECT OPERCD INTO V_OPERCD FROM TMM22_CUSTOMERS WHERE CUSTCD = IN_CUSTCD;
  END IF;

  --1.更新客户信息(更新时间、更新人、台数、开通状态)

  UPDATE TMM22_CUSTOMERS
     SET UPDDATE = SYSDATE,
         OPERCD = NVL(IN_OPERCD,V_OPERCD),
         POS_N = V_NUM,
         S_STATUS = decode(nvl(V_NUM,0),0,S_STATUS,'1') --大于1为开通状态
   WHERE CUSTCD = IN_CUSTCD;

  IF SQL%ROWCOUNT <> 1 OR SQL%ROWCOUNT IS NULL THEN
      V_RET := '客户信息：更新失败!';
      RETURN V_RET;
  END IF;

  --2.同步实施部门店信息（已开通 非视频 且有有效pos机 有效的门店）
  delete from tmm22_customers@ccgl_24 where trim(CUSTCD) = IN_CUSTCD;
  insert into tmm22_customers@ccgl_24 select * from tmm22_customers b
        where b.custcd = IN_CUSTCD  and b.busityp <> 'YX' and b.s_status='1'
          and b.custnm not like '%视频%' and b.useflg = '1'
          and b.custcd in(select distinct r.custcd from TMM35_cust_pos_rl r where r.useflg='1');
  IF SQL%ROWCOUNT <> 1 OR SQL%ROWCOUNT IS NULL THEN
      V_RET := '24客户信息同步失败!' ;--(-20010,IN_BILLNO || ' 业务流水: ' ||TO_CHAR(IN_BUSINESSID) || ' 更新失败!');
      RETURN V_RET;
  END IF;

  V_RET := 'OK';

  RETURN V_RET;

END UF_INSERT_POSUNIT;
