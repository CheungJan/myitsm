PROCEDURE USP_ITSM_ARCHIVE(IN_MID   IN VARCHAR2,
                                             IN_OPER  IN CHAR,
                                             O_RETURN OUT VARCHAR2)

 AS
  V_STR   VARCHAR2(20);
  V_NUM   NUMBER;
/*  V_COUNT NUMBER;
  V_GHS   NUMBER;
  V_DYS   NUMBER;
  V_GZLX  VARCHAR2(10);
  V_PJNM  VARCHAR2(40);*/
  V_MD    TIT10_MAINTENANCEDAY%ROWTYPE;
  V_MARCH TIT12_MAINTENANCE_ARCHIVE%ROWTYPE;

BEGIN
  --日常维护单关单归档
  SELECT *
    INTO V_MD
    FROM TIT10_MAINTENANCEDAY T
   WHERE T.MAINTENANCE_ID = IN_MID
     AND T.CURRENT_STATUS <> '9';

  IF V_MD.IS_ARCHIVE = '1' THEN
    ROLLBACK;
    O_RETURN := '维护单已归档,不能再次归档！';
    RETURN;
  END IF;

  IF TRIM(V_MD.FAULTCODE) IS NULL THEN
    ROLLBACK;
    O_RETURN := '故障代码未填写,请先录入故障代码！';
    RETURN;
  END IF;

/*  --判断是否有 免检查的 故障代码
  SELECT COUNT(*) INTO V_COUNT
    FROM TIT04_ARCHIVECODE T
   WHERE UNCHECK = 'Y'
     AND INSTR(TRIM(V_MD.FAULTCODE), ARCHCD) > 0;
  IF V_COUNT = 0 THEN
    --检查故障代码与配件更换的对应关系是否达到要求
    SELECT MAX(CASE WHEN INSTR(TRIM(V_MD.FAULTCODE),','||ACCESSORIES_TYPE) = 0 THEN ACCESSORIES_TYPE ELSE '' END),
    SUM(CASE WHEN INSTR(TRIM(V_MD.FAULTCODE),','||ACCESSORIES_TYPE) > 0 THEN 1 ELSE 0 END) ,
    COUNT(1) INTO V_GZLX,V_DYS,V_GHS
    FROM TIT25_ACCESSORIES_UPDATE T
    WHERE MAINTENANCE_ID = IN_MID
    AND AUDITFLG ='1';
    IF V_GHS <> V_DYS THEN
      SELECT CLASSNM INTO V_PJNM FROM TMM11_ITEMCLASS T WHERE CLASSCD = V_GZLX;
      ROLLBACK;
      O_RETURN := '配件更换中有 '||V_PJNM||'('||V_GZLX||') ,没有对应的故障代码,请添加!' ;
      RETURN;
    END IF;
  END IF;*/
  BEGIN
    --解析故障代码串
    --  RE: 1,CR010007/2,BS10L1B2/2,MB700000/1,SFBG0101/
    FOR I IN 1 .. TOOLS.FMIDN(TRIM(V_MD.FAULTCODE), '/') LOOP
      V_MARCH := null;

      V_STR := TOOLS.FMID(TRIM(V_MD.FAULTCODE), I, 'N', '/');
      IF LENGTH(V_STR) > 0 THEN
        V_MARCH.MAINTENANCE_ID := IN_MID; --维护单ID
        V_MARCH.FAULTCD        := TOOLS.FMID(V_STR, 2, 'N', ','); --故障编码
        IF TOOLS.FMID(V_STR, 1, 'N', ',') = '1' THEN
          V_MARCH.FAULT_TYPE        := V_MARCH.FAULTCD; --故障大类
          V_MARCH.FAULT_DETAIL_TYPE := NULL; --故障小类
        ELSIF TOOLS.FMID(V_STR, 1, 'N', ',') = '2' THEN
          V_MARCH.FAULT_TYPE        := SUBSTR(V_MARCH.FAULTCD, 0, 6); --故障大类
          V_MARCH.FAULT_DETAIL_TYPE := SUBSTR(V_MARCH.FAULTCD, 7); --故障小类
        END IF;
        V_MARCH.FAULTCD_AUDIT := NULL; --故障编码(审核后)
        V_MARCH.DESCRIPTION := NULL; --描述
        V_MARCH.USEFLG      := '1'; --有效标记
        V_MARCH.IS_AUDIT    := '0'; --审核标记
        V_MARCH.CREATE_TIME := SYSDATE; --创建时间
        V_MARCH.CREATOR     := IN_OPER; --创建人
        V_MARCH.UPDATE_TIME := NULL; --更新时间
        V_MARCH.UPDATOR     := NULL; --更新人

        --取操作流水号
        V_NUM := UF_INSERT_BUSINESS(IN_MID,
                                    '维护单归档',
                                    'SYS',
                                    '维护单归档 故障代码:' || V_MARCH.FAULTCD,
                                    'N');
        IF V_NUM < 0 THEN
          RAISE_APPLICATION_ERROR(-20010, '新增维护单归档记录错误！');
          ROLLBACK;
          O_RETURN := '记录归档业务操作流水失败错误！' || V_MARCH.FAULTCD;
          RETURN;
        END IF;

        V_MARCH.BUSINESS_OPERATION_ID := V_NUM; --业务流水操作表ID
        BEGIN
          INSERT INTO TIT12_MAINTENANCE_ARCHIVE VALUES V_MARCH;
        EXCEPTION
          WHEN OTHERS THEN
            RAISE_APPLICATION_ERROR(-20010, '插入维护单归档记录错误！');
            ROLLBACK;
            O_RETURN := '插入维护单归档记录错误！';
            RETURN;
        END;
      END IF;

    END LOOP;
  END;

  UPDATE TIT10_MAINTENANCEDAY T
     SET IS_ARCHIVE = '1'
   WHERE T.MAINTENANCE_ID = IN_MID;

  -------------------------
  O_RETURN := 'OK';
  -------------------

EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK;
    O_RETURN := SQLCODE || SQLERRM;

END;
