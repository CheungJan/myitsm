TRIGGER "CCGL".T_TMM22_CUSTOMERS
 AFTER INSERT OR UPDATE ON TMM22_CUSTOMERS
 FOR EACH ROW
DECLARE
 AS_CLASSNM		INPT_CUSTOMERS.CLASSNM%TYPE;
 AS_BUSITYP		INPT_CUSTOMERS.BUSITYP%TYPE;
 AS_AREA		  INPT_CUSTOMERS.AREA%TYPE;
 AS_PPTCODE		INPT_CUSTOMERS.PPTCODE%TYPE;
 AS_POSSTATUS	INPT_CUSTOMERS.POSSTATUS%TYPE;
 AS_POSSTATUS1	INPT_CUSTOMERS.POSSTATUS1%TYPE;
 AS_ITSMNM    INPT_CUSTOMERS.ITSMNM%TYPE;
 AS_RTE       VARCHAR(100);

BEGIN

   begin
       SELECT CLASSNM INTO AS_CLASSNM FROM TMM21_CUSTCLASS WHERE CLASSCD = :NEW.CLASSCD AND ROWNUM = 1;
       EXCEPTION
          WHEN no_data_found THEN
          --查询不到数据
          AS_RTE := '查询不到数据';
   END;
   begin
       SELECT CODENM  INTO AS_BUSITYP FROM TMM31_SYSCODES WHERE CODETYP = 'BT' AND CODECD = :NEW.BUSITYP AND ROWNUM = 1;
        EXCEPTION
          WHEN no_data_found THEN
          --查询不到数据
          AS_RTE := '查询不到数据';
   END;
   begin
       SELECT CODENM  INTO AS_PPTCODE FROM TMM31_SYSCODES WHERE CODETYP = 'YB' AND CODECD = :NEW.PPTCODE AND ROWNUM = 1;
        EXCEPTION
          WHEN no_data_found THEN
          --查询不到数据
          AS_RTE := '查询不到数据';
   END;
   begin
       SELECT NAME    INTO AS_AREA    FROM tmm46_area   where id = :NEW.AREA AND ROWNUM = 1;
        EXCEPTION
          WHEN no_data_found THEN
          --查询不到数据
          AS_RTE := '查询不到数据';
   END;
   begin
       SELECT CODENM  INTO AS_POSSTATUS FROM TIT03_SYSCODES WHERE CODETYP = 'ST' AND CODECD = :NEW.POSSTATUS AND ROWNUM = 1;
        EXCEPTION
          WHEN no_data_found THEN
          --查询不到数据
          AS_RTE := '查询不到数据';
   END;
   begin
       SELECT CODENM  INTO AS_POSSTATUS1 FROM TIT03_SYSCODES WHERE CODETYP = 'ZZ' AND CODECD = :NEW.POSSTATUS1 AND ROWNUM = 1;
        EXCEPTION
          WHEN no_data_found THEN
          --查询不到数据
          AS_RTE := '查询不到数据';
   END;
   begin
       SELECT I.ITEMNM INTO AS_ITSMNM FROM TMM35_CUST_POS_RL t , TMM12_ITEMS i	Where t.itemcd = i.itemcd  And t.useflg = '1' AND T.CUSTCD = :OLD.CUSTCD AND ROWNUM = 1;
       EXCEPTION
          WHEN no_data_found THEN
          --查询不到数据
          AS_RTE := '查询不到数据';
   END;

  IF INSERTING THEN

  INSERT INTO INPT_CUSTOMERS (CUSTCD,      CUSTNM,         CUSTCARD,     CLASSNM,          BUSITYP,      ADDRESS,
                              USEFLG,      LOCATION,       AREA,         PPTCODE,          POSSTATUS,    POSSTATUS1,
                              ITSMNM,      DATA_BASE,      CREATEDATE,   SENDFALG
                             )
                      VALUES(:NEW.CUSTCD, :NEW.CUSTNM,    :NEW.CUSTCARD, AS_CLASSNM,       AS_BUSITYP,  :NEW.ADDRESS,
                              DECODE(:NEW.USEFLG,'1','有效','0','无效',''),   DECODE(:NEW.LOCATION,'1','内环','2','中环','3','外环'),    AS_AREA,      AS_PPTCODE,       AS_POSSTATUS, AS_POSSTATUS1,
                              AS_ITSMNM,    :NEW.DATA_BASE,  SYSDATE,      '0'
                             );

  ELSIF UPDATING THEN
  --UPDATE触发
  DELETE INPT_CUSTOMERS WHERE CUSTCD = :OLD.CUSTCD;-- AND CUSTCARD = :OLD.CUSTCARD;

  INSERT INTO INPT_CUSTOMERS (CUSTCD,      CUSTNM,         CUSTCARD,     CLASSNM,          BUSITYP,      ADDRESS,
                              USEFLG,      LOCATION,       AREA,         PPTCODE,          POSSTATUS,    POSSTATUS1,
                              ITSMNM,      DATA_BASE,      CREATEDATE,   SENDFALG
                             )
                      VALUES(:NEW.CUSTCD, :NEW.CUSTNM,    :NEW.CUSTCARD, AS_CLASSNM,       AS_BUSITYP,  :NEW.ADDRESS,
                              DECODE(:NEW.USEFLG,'1','有效','0','无效',''),   DECODE(:NEW.LOCATION,'1','内环','2','中环','3','外环'),    AS_AREA,      AS_PPTCODE,       AS_POSSTATUS, AS_POSSTATUS1,
                              AS_ITSMNM,    :NEW.DATA_BASE,  SYSDATE,      '0'
                             );
  END IF;

END;
