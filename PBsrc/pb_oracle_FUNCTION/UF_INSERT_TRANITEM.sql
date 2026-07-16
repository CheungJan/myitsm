FUNCTION UF_INSERT_TRANITEM(IN_POSID     IN VARCHAR2,
                                             IN_ITEMID    IN VARCHAR2,
                                             IN_OPERCD    IN VARCHAR2,
                                             IN_REFID     IN VARCHAR2
                                          )

 RETURN VARCHAR2
 AS
 --PRAGMA AUTONOMOUS_TRANSACTION;
  V_RET     VARCHAR2(100);
  V_ROW     NUMBER;
  V_ITEM    NUMBER;
  V_STR     VARCHAR2(128);
  v_itemeid VARCHAR2(13);

  --
    --附属配件生成确认数据
  --
BEGIN

  SELECT count(1) into V_ROW FROM TMM43_EID a,TMM12_ITEMS b WHERE a.ITEMCD= b.ITEMCD AND instr(IN_ITEMID,eid) > 0;

  V_STR := IN_ITEMID;
  IF V_ROW < 1 THEN
     RETURN '未找到数据';
  END IF;

  v_item := instr(V_STR, ',');
	
  WHILE v_item <> 0 LOOP
	  v_itemeid := substr(V_STR, 1, v_item - 1);

    BEGIN
      INSERT INTO sm_in_part_change
                (id, changetype, name, serialno, model,
                 old_name, old_serialno, old_model,
                 case_no,insert_time,  sys_status,OPERFLG,memo)

            SELECT SM_PART_SEQNO.NEXTVAL id,
                   1 changetype ,b.ITEMNM name ,
                   v_itemeid AS serialno,
                    b.ITEMCD model, '' AS old_name,IN_POSID,'' as old_model,
                    IN_REFID,
                    SYSDATE insert_time, 1,'0' OPERFLG ,
                    IN_REFID||'单附属配件，上门工程师：'||IN_OPERCD
                FROM TMM43_EID a,TMM12_ITEMS b WHERE a.ITEMCD= b.ITEMCD
                 AND EID = v_itemeid; --instr(IN_ITEMID,eid) > 0; --instr('MD4G0116A0450,MD4G0116A0451',eid) > 0;

      IF sql%rowcount<1 THEN
         V_RET := '数据异常1,插入确认数据失败!';
         RETURN V_RET;
      End if;
     exception
        when others then
        return  sqlcode||sqlerrm||'数据异常2,插入确认数据失败!';
     End;

     V_STR := substr(V_STR, v_item + 1);
	
     v_item := instr(V_STR, ',');
     IF v_item = 0 THEN
       BEGIN
        INSERT INTO sm_in_part_change
                  (id, changetype, name, serialno, model,
                   old_name, old_serialno, old_model,
                   case_no,insert_time,  sys_status,OPERFLG,memo)

              SELECT SM_PART_SEQNO.NEXTVAL id,
                     1 changetype ,b.ITEMNM name ,
                     V_STR AS serialno,
                      b.ITEMCD model, '' AS old_name,IN_POSID,'' as old_model,
                      IN_REFID,
                      SYSDATE insert_time, 1,'0' OPERFLG ,
                      IN_REFID||'单附属配件，上门工程师：'||IN_OPERCD
                  FROM TMM43_EID a,TMM12_ITEMS b WHERE a.ITEMCD= b.ITEMCD
                   AND EID = V_STR;

        IF sql%rowcount<1 THEN
           V_RET := '2数据异常1,插入确认数据失败!';
           RETURN V_RET;
        End if;
       exception
          when others then
          return  '2数据异常2,插入确认数据失败!';
       End;
     End If;

  END LOOP ;



  V_RET := 'OK';

 -- COMMIT;

  RETURN V_RET;

END UF_INSERT_TRANITEM;
