FUNCTION UF_INSERT_POSITEM(IN_POSID     IN VARCHAR2,
                                             IN_ITEMID    IN VARCHAR2,
                                             IN_OPERCD    IN VARCHAR2,
                                             IN_REFID     IN VARCHAR2
                                          )

 RETURN VARCHAR2
 AS
  V_RET     VARCHAR2(100);
  V_ITEM    NUMBER;
  --V_OPERCD  CHAR(6);
  V_STR     VARCHAR2(128);
  v_itemeid VARCHAR2(13);
  v_itemeidcd VARCHAR2(128);
  V_FNRET    VARCHAR2(128);

  --
    --POS新增配件
    --IN_ITEMID = '000KB08030969,000MB08030718'
  --
BEGIN
     V_STR := IN_ITEMID;

	 -------------------------------tmm43  流水所属-----------------------------
	 --sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中  8 在库 9 出库
	 UPDATE TMM43_EID SET SFLG = '1' , refid = IN_REFID, whcd = '', gendate = sysdate
	 WHERE instr(IN_ITEMID,eid) > 0;
	 IF sql%rowcount<1 THEN
	    V_RET := '数据异常,更新流水所属失败!';
	    RETURN V_RET;
	 End if;
	
	
	 -------------------------------tmm44  POS所属-------------------------------
	 --UPDATE tmm44_pos_r_eid SET POSID = IN_POSID, USEFLG = '1' WHERE instr(IN_ITEMID,eid) > 0;
	
	 UPDATE tmm44_pos_r_eid SET USEFLG = '0' WHERE instr(IN_ITEMID,eid) > 0; --旧配件无效化
	
	 v_item := instr(V_STR, ',');

      --1.3基本为附属配件（路由器）如：'MD4GP11756018,MD4G011755618'，以下防止单一添加配件
      IF v_item = 0 THEN
         SELECT ITEMCD into v_itemeidcd FROM TMM43_EID WHERE EID = V_STR;
         INSERT INTO tmm44_pos_r_eid
                     (posid, itemcd, eid, opercd, gendate, upddate, useflg)
                     VALUES
                     (IN_POSID, v_itemeidcd, V_STR, IN_OPERCD, sysdate, sysdate, '1');
         IF sql%rowcount<1 THEN
            V_RET := '数据异常0,更新44POS所属失败!';
            RETURN V_RET;
         End if;
      END IF ;
      --1.3结束

	
	    WHILE v_item <> 0 LOOP
	      v_itemeid := substr(V_STR, 1, v_item - 1);
	
	      SELECT ITEMCD into v_itemeidcd FROM TMM43_EID WHERE EID = v_itemeid;
	      insert into tmm44_pos_r_eid
	                  (posid, itemcd, eid, opercd, gendate, upddate, useflg)
	                  values
	                  (IN_POSID, v_itemeidcd, v_itemeid, IN_OPERCD, sysdate, sysdate, '1');
	      IF sql%rowcount<1 THEN
	         V_RET := '数据异常1,更新44POS所属失败!';
	         RETURN V_RET;
	      End if;
	      V_STR := substr(V_STR, v_item + 1);
	
	      v_item := instr(V_STR, ',');
	      IF v_item = 0 THEN
	
	         SELECT ITEMCD into v_itemeidcd FROM TMM43_EID WHERE EID = V_STR;
	         INSERT INTO tmm44_pos_r_eid
	                     (posid, itemcd, eid, opercd, gendate, upddate, useflg)
	                     VALUES
	                     (IN_POSID, v_itemeidcd, V_STR, IN_OPERCD, sysdate, sysdate, '1');
	         IF sql%rowcount<1 THEN
	            V_RET := '数据异常2,更新44POS所属失败!';
	            RETURN V_RET;
	         End if;
	      END IF ;
	    END LOOP ;

  /*
   -------------------------------SM_PART  数据确认-------------------------------
   V_FNRET := uf_insert_tranitem(IN_POSID,IN_ITEMID,IN_OPERCD,IN_REFID);
   IF V_FNRET <> 'OK' THEN
      RETURN '附属配件数据确认'||V_FNRET;
   END IF;

  */
  V_RET := 'OK';

  RETURN V_RET;

END UF_INSERT_POSITEM;
