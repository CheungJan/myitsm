procedure usp_trans_unit_confrim( as_type   char,
                                                    as_id    number,
                                                   --as_mid    char,
                                                   as_userid char,
                                                   as_return out varchar2)

 as
  v_id          number(20);
  v_tftype      char(2);
  v_tfid        char(8);
  v_eid         varchar2(128);
  v_itemcd      varchar2(128);
  v_custcd      char(8);
  V_oldCUSTCD   char(8);
  v_posnumber   number;
  v_custcard    varchar2(20);
  v_oldcustcard varchar2(20);
  v_address     varchar2(80);
  v_newcustcard varchar2(20);
  v_str1        varchar2(200);
  v_pos         number(5);
  v_startdate   date;
  v_NAME        varchar2(100);
  v_PHONENO     varchar2(100);
  v_CONTACTOR   varchar2(100);
  v_mid         varchar2(8);
  v_oldposid    varchar2(13);
  v_ischange    char(1);
  v_changeeid   varchar2(50);
  v_itemeid     varchar2(128);
  v_itemeidcd    varchar2(128);
  v_item         number(5);
  V_ENGINEER     CHAR (6); --上门工程师
  v_mr           CHAR (1);--是否翻新机
  v_row          number;
  ----
begin

  v_id     := as_id;
  If as_type = 'XZ' Then
    select count(1) into v_row from sm_in_open_result where id = v_id and sys_status = '1';
  End If;
  /***********---整机---v_type='1'**********************
  一、门店开通（XZ）
  二、旧机翻新（GX）
  三、免费更换（GH）
  四、门店关闭（GB）
  五、门店搬迁（BQ）
  六、磁卡号变更（CK）
  七、设备变更（BG）
  -------------------------------------------------------------------
  uf_add_item --新增配件
  uf_add_posunit  --新增pos
  uf_23update_cust  --同步客户
  usp_insert_biz  --记录中间表 （想做流水表，目前只有翻新使用）
  ******************************************************/


    select plan_no, case_no, cardcode, serialno, COMPLETEDDATE
      into v_tfid, v_mid, v_custcard, v_str1, v_startdate
      from sm_in_open_result
     where id = v_id and sys_status = '1';

    select sltyp, itemcd
      into v_tftype, v_itemcd
      from tsl01_extend b
     where opbillid = v_tfid;

    if v_startdate is not null then
      --门店开通
      IF v_tftype = 'XZ' THEN  ----开通单状态
        update tsl02_extenddt
           set opqty = opqty + 1
         where custcard = v_custcard  and opbillid = v_tfid;

        update tsl01_extend
           set useflg = decode((select sum(planqty - opqty)  from tsl02_extenddt  where opbillid = v_tfid),
                               0,
                               '2',
                               useflg)
         where opbillid = v_tfid;

        --销售单
        update tsl10_slbill
           set openqty = openqty + 1
         where slbillid in
               (select slbillid from tsl01_extend where opbillid = v_tfid);
        ---------------------
        update sm_in_open_result set sys_status = '0' where id = v_id;
        ------------------
        update tmm22_customers
           set s_status = '1', opendate = v_startdate
         where custcard = v_custcard;

        ---------
        v_pos := instr(v_str1, ',');
        If v_pos > 0 then
           as_return := '数据异常,不允许多台!';
           return;
        end if;

        ----tmm35
        insert into tmm35_cust_pos_rl
                    (custcd,         eid,          itemcd,       startdate,        sysinfo,
                     softinfo,       posupddate,   posinfo,      area,             status,
                     typflg,         maintenancedate,  maintenancetyp, opercd,     gendate,
                     upddate,        useflg)
              select custcd,         v_str1,       v_itemcd,     v_startdate,       '',
                       '',           v_startdate,  '',           '',                '',
                       '',           '',           '',           as_userid,        sysdate,
                     sysdate,        '1'
                from tmm22_customers
               where custcard = v_custcard;

        ---tmm44
        update tmm44_pos_r_eid
           set tmm44_pos_r_eid.gendate = v_startdate,
               tmm44_pos_r_eid.upddate = v_startdate
         where tmm44_pos_r_eid.posid = v_str1;

        ----tmm43
        update tmm43_eid set sflg = '1' where eid = v_str1;
        ----twh
        update twh16_outdteid
           set qcqty = 1
         where outbillid in
               (select outbillid from twh15_out where invtyp = '8')
           and qcqty = 0 and eid = v_str1;

        --附属配件 add by cbh 20171113 新增附属配件变更
        --SELECT IS_CHANGE,''''||regexp_replace(CHANGE_EID,',',''',''')||'''' INTO v_ischange,v_changeeid  FROM TIT14_EQUIPMENT_OPEN WHERE NEW_OPENING_ID = v_mid;
        SELECT IS_CHANGE,CHANGE_EID INTO v_ischange,v_changeeid  FROM TIT14_EQUIPMENT_OPEN WHERE NEW_OPENING_ID = v_mid;

        If v_ischange = '1' Then
           --tmm43  流水所属
           --sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中  8 在库 9 出库
           UPDATE TMM43_EID SET SFLG = '1' , refid = v_mid, whcd = '', gendate = sysdate
           WHERE instr(v_changeeid,eid) > 0;
           IF sql%rowcount<1 THEN
              as_return := '数据异常,更新流水所属失败!';
              --return;
           End if;
           --tmm44  POS所属
           UPDATE tmm44_pos_r_eid SET POSID = v_str1, USEFLG = '1' WHERE instr(v_changeeid,eid) > 0;

           IF sql%rowcount<1 THEN
              --配置表中没有item
              v_item := instr(v_changeeid, ',');

              WHILE v_item <> 0 LOOP
                v_itemeid := substr(v_changeeid, 1, v_item - 1);
	
                SELECT ITEMCD into v_itemeidcd FROM TMM43_EID WHERE EID = v_itemeid;
                insert into tmm44_pos_r_eid
                            (posid, itemcd, eid, opercd, gendate, upddate, useflg)
                            values
                            (v_str1, v_itemeidcd, v_itemeid, as_userid, sysdate, sysdate, '1');
                IF sql%rowcount<1 THEN
                   as_return := '数据异常,更新44POS所属失败!';
                   return;
                End if;
                v_changeeid := substr(v_changeeid, v_item + 1);

                v_item := instr(v_changeeid, ',');
                IF v_item = 0 THEN
                   SELECT ITEMCD into v_itemeidcd FROM TMM43_EID WHERE EID = v_changeeid;
                   INSERT INTO tmm44_pos_r_eid
                               (posid, itemcd, eid, opercd, gendate, upddate, useflg)
                               VALUES
                               (v_str1, v_itemeidcd, v_changeeid, as_userid, sysdate, sysdate, '1');
                   IF sql%rowcount<1 THEN
                      as_return := '数据异常,更新44POS所属失败!';
                      return;
                   End if;
                END IF ;
              END LOOP ;
           End if;
	
        End If;
        ------------------------
        --add by libin,at20161223,同步实施部门店信息（已开通 非视频 且有有效pos机 有效的门店）
        delete from tmm22_customers@ccgl_24 where trim(custcard) = v_custcard;
        insert into tmm22_customers@ccgl_24
        select * from tmm22_customers b
        where b.busityp <> 'YX' and b.s_status='1' and b.useflg = '1'
          and b.custnm not like '%视频%' and trim(b.custcard) = v_custcard
          and b.custcd in(select distinct r.custcd from TMM35_cust_pos_rl r where r.useflg='1');
        ------------------------
      END IF;

      --回写开通单状态
      --回写pos门店关系表
      --------------------------------------------------
      --旧机翻新
      IF v_tftype = 'GX' THEN
        ----开通单状态
        update tsl02_extenddt
           set opqty = opqty + 1
         where custcard = v_custcard  and opbillid = v_tfid;

        update tsl01_extend
           set useflg = decode((select sum(planqty - opqty)  from tsl02_extenddt where opbillid = v_tfid),
                               0,
                               '2',
                               useflg)
         where opbillid = v_tfid;
        --销售单状态
        update tsl10_slbill
           set openqty = openqty + 1
         where slbillid in
               (select slbillid from tsl01_extend where opbillid = v_tfid);

        ---------------------
        update sm_in_open_result set sys_status = '0' where id = v_id;
        ------------------
        update tmm22_customers
           set replacedate = v_startdate,
               S_STATUS    = '1'
         where custcard = v_custcard;
        ------------------
        v_pos := instr(v_str1, ',');
        If v_pos > 0 then
           as_return := '数据异常,不允许多台!';
           return;
        end if;

        if v_pos = 0 then
          ----tmm35
          insert into tmm35_cust_pos_rl
                      (custcd,      eid,         itemcd,    startdate,           sysinfo,
                       softinfo,    posupddate,  posinfo,   area,                status,
                       typflg,      maintenancedate, maintenancetyp,    opercd,  gendate,
                       upddate,  useflg)
                select custcd,   v_str1,   v_itemcd,    v_startdate,    '',
                       '',   v_startdate,    '',    '',   '',
                       '',  '',    '',   as_userid,  sysdate,
                       sysdate,     '1'
                  from tmm22_customers
                 where custcard = v_custcard;
          ---tmm44
          update tmm44_pos_r_eid
             set tmm44_pos_r_eid.gendate = v_startdate,
                 tmm44_pos_r_eid.upddate = v_startdate
           where tmm44_pos_r_eid.posid = v_str1;

          ----tmm43
          update tmm43_eid set sflg = '1' where eid = v_str1;

          -----twh
          update twh16_outdteid
             set qcqty = 1
           where eid = v_str1
             and qcqty = 0
             and outbillid in
                 (select outbillid from twh15_out where invtyp = '8');

           --附属配件 add by cbh 20171113 新增附属配件变更
          SELECT IS_CHANGE,CHANGE_EID INTO v_ischange,v_changeeid  FROM TIT15_EQUIPMENT_RENOVATE WHERE RENOVATE_ID = v_mid;

          IF v_ischange = '1' THEN
             --tmm43  流水所属
             --sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中  8 在库 9 出库
             UPDATE TMM43_EID SET SFLG = '1' , refid = v_mid, whcd = '', gendate = sysdate
             WHERE instr(v_changeeid,eid) > 0;
             IF sql%rowcount<1 THEN
	            as_return := '数据异常,更新流水所属失败!';
	            --return;
	           End if;
	           --tmm44  POS所属
             UPDATE tmm44_pos_r_eid SET POSID = v_str1, USEFLG = '1' WHERE instr(v_changeeid,eid) > 0;
             IF sql%rowcount<1 THEN
                --配置表中没有item
                v_item := instr(v_changeeid, ',');

                WHILE v_item <> 0 LOOP
	                v_itemeid := substr(v_changeeid, 1, v_item - 1);
	
	                SELECT ITEMCD into v_itemeidcd FROM TMM43_EID WHERE EID = v_itemeid;
	                insert into tmm44_pos_r_eid
                              (posid, itemcd, eid, opercd, gendate, upddate, useflg)
                              values
                              (v_str1, v_itemeidcd, v_itemeid, as_userid, sysdate, sysdate, '1');
                  IF sql%rowcount<1 THEN
                     as_return := '数据异常,更新44POS所属失败!';
                     return;
                  End if;
			
			            v_changeeid := substr(v_changeeid, v_item + 1);

                  v_item := instr(v_changeeid, ',');
                  IF v_item = 0 THEN
                     SELECT ITEMCD into v_itemeidcd FROM TMM43_EID WHERE EID = v_changeeid;
                     INSERT INTO tmm44_pos_r_eid
                                 (posid, itemcd, eid, opercd, gendate, upddate, useflg)
                                 VALUES
                                 (v_str1, v_itemeidcd, v_changeeid, as_userid, sysdate, sysdate, '1');
                     IF sql%rowcount<1 THEN
                        as_return := '数据异常,更新44POS所属失败!';
                        return;
                     End if;
				          END IF ;
		            END LOOP ;
	           End if;
          End If;

        END IF;

      ---翻新机回收   到虚拟库挂虚拟客户
        select store_id, old_device_id
          into v_custcd, v_oldposid
          from tit15_maintenance_renovate
         where renew_id = v_mid;

         SELECT MAX(D2D_ENGINEER) INTO V_ENGINEER FROM TIT23_MAINTENANCE_D2D
         WHERE MAINTENANCE_ID = v_mid AND USEFLG = '1' AND d2d_type = '2'  ;
         --新增中间处理表INPT_TPPOS_BIZ
          INSERT INTO INPT_TPPOS_BIZ
           (BIZNO, CUSTCD, CUSTCARD,MRPOSID, OPERCD, STATUS, CREATOR, CREATDATE)
           VALUES
           (v_mid,v_custcd,v_custcard,v_oldposid ,V_ENGINEER, '0',as_userid, sysdate);

          -----修改TMM43
          UPDATE TMM43_EID
             SET --WHCD    = 'MH',  --直调虚拟库
                 --SFLG    = '8',
                 REFID   = v_mid,
                -- ITEMTYP = 'DJ',
                 GENDATE = SYSDATE
           WHERE EID = v_oldposid;
          -----作废TMM35_CUST_POS_RL信息
          -----调回通方客户
          UPDATE TMM35_CUST_POS_RL
             SET CUSTCD = '00000389'
           WHERE EID = v_oldposid
             AND CUSTCD = V_CUSTCD;
          --END IF;
      END IF;

      --免费更换
      IF v_tftype = 'GH' THEN

        ----开通单状态

        update tsl02_extenddt
           set opqty = opqty + 1
         where custcard = v_custcard
           and opbillid = v_tfid;

        update tsl01_extend
           set useflg = decode((select sum(planqty - opqty)
                                 from tsl02_extenddt
                                where opbillid = v_tfid),
                               0,
                               '2',
                               useflg)
         where opbillid = v_tfid;
        --销售单状态
        update tsl10_slbill
           set openqty = openqty + 1
         where slbillid in
               (select slbillid from tsl01_extend where opbillid = v_tfid);

        ---------------------
        update sm_in_open_result set sys_status = '0' where id = v_id;
        ------------------
        update tmm22_customers
           set replacedate = v_startdate,
               S_STATUS    = '1'
         where custcard = v_custcard;
        --------------------
        v_pos := instr(v_str1, ',');
        If v_pos > 0 then
           as_return := '数据异常,不允许多台!';
           return;
        end if;

        if v_pos = 0 then
          ----tmm35
          insert into tmm35_cust_pos_rl
            (custcd, eid, itemcd, startdate, sysinfo, softinfo,
             posupddate, posinfo, area, status, typflg,
             maintenancedate, maintenancetyp, opercd,  gendate,  upddate, useflg)
            select custcd,  v_str1,  v_itemcd, v_startdate,  '',  '',
                   v_startdate,  '',   '',  '',  '',
                   '',   '',  as_userid,  sysdate,  sysdate,   '1'
              from tmm22_customers
             where custcard = v_custcard;
          ---tmm44
          update tmm44_pos_r_eid
             set tmm44_pos_r_eid.gendate = v_startdate,
                 tmm44_pos_r_eid.upddate = v_startdate
           where tmm44_pos_r_eid.posid = v_str1;

          ----tmm43
          update tmm43_eid set sflg = '1' where eid = v_str1;

          -----twh

          update twh16_outdteid
             set qcqty = 1

           where eid = v_str1
             and qcqty = 0
             and outbillid in
                 (select outbillid from twh15_out where invtyp = '8');

        end if;
      end if;
      -----------------------------------------------------
      --门店关闭
      IF v_tftype = 'GB' THEN
        ----开通单状态
        update tsl01_extend set useflg = '2' where opbillid = v_tfid;

        ---------------------
        update sm_in_open_result set sys_status = '0' where id = v_id;
        ------------------
        update tmm22_customers T
           set T.s_status = '3', T.custnm = '(永久关闭)' || T.custnm
         where T.custcard = v_custcard
           AND T.CUSTCD = (SELECT S.STORE_ID
                             FROM TIT18_STORE_CLOSE S
                            WHERE S.REQUSET_PAPER_ID = v_tfid
                              AND S.CLOSE_TYPE = 'YJ');

        update tmm22_customers T
           set T.s_status = '2', T.custnm = '(临时关闭)' || T.custnm
         where T.custcard = v_custcard
           AND T.CUSTCD = (SELECT S.STORE_ID
                             FROM TIT18_STORE_CLOSE S
                            WHERE S.REQUSET_PAPER_ID = v_tfid
                              AND S.CLOSE_TYPE = 'LS');



        ------------------------
        --add by libin,at20170323,同步实施部门店信息（已开通 非视频 且有有效pos机 有效的门店）
        delete from tmm22_customers@ccgl_24 where trim(custcard) = v_custcard;
        insert into tmm22_customers@ccgl_24
        select * from tmm22_customers b
        where b.busityp <> 'YX' and b.s_status='1' and b.useflg = '1'
          and b.custnm not like '%视频%' and trim(b.custcard) = v_custcard
          and b.custcd in(select distinct r.custcd from TMM35_cust_pos_rl r where r.useflg='1');
        ------------------------
      end if;
      --门店搬迁
      IF v_tftype = 'BQ' THEN
        ----开通单状态
        update tsl01_extend set useflg = '2' where opbillid = v_tfid;

        ---------------------
        update sm_in_open_result set sys_status = '0' where id = v_id;
        ------------------

        select rtrim(newcustcard), newaddress, N_NAME, N_PHONENO, N_CONTACTOR
          into v_newcustcard, v_address, v_NAME, v_PHONENO, v_CONTACTOR
          from tsl02_extenddt
         where opbillid = v_tfid;

        update tmm22_customers
           set custcard                   = v_newcustcard,
               address                    = v_address,
               custnm                     = v_NAME,
               PHONENO                    = v_PHONENO,
               CONTACTOR                  = v_CONTACTOR,
               S_STATUS                   = '1',
               tmm22_customers.sttransflg = '0'
         where custcard = v_custcard;

        ------------------------
        --add by libin,at20170323,同步实施部门店信息（已开通 非视频 且有有效pos机 有效的门店）
        delete from tmm22_customers@ccgl_24 where trim(custcard) = v_custcard;
        insert into tmm22_customers@ccgl_24
        select * from tmm22_customers b
        where b.busityp <> 'YX' and b.s_status='1' and b.useflg = '1'
          and b.custnm not like '%视频%' and trim(b.custcard) = v_newcustcard
          and b.custcd in(select distinct r.custcd from TMM35_cust_pos_rl r where r.useflg='1');
        ------------------------
      end if;
      --磁卡号变更
      IF v_tftype = 'CK' THEN
        ----开通单状态
        update tsl01_extend set useflg = '2' where opbillid = v_tfid;

        ---------------------
        update sm_in_open_result set sys_status = '0' where id = v_id;
        ------------------

        select rtrim(tsl02_extenddt.newcustcard), tsl02_extenddt.custcard
          into v_newcustcard, v_oldcustcard
          from tsl02_extenddt
         where opbillid = v_tfid;

        update tmm22_customers
           set custcard = v_newcustcard
         where custcard = v_oldcustcard;

        ------------------------
        --add by libin,at20170323,同步实施部门店信息（已开通 非视频 且有有效pos机 有效的门店）
        delete from tmm22_customers@ccgl_24 where trim(custcard) = v_oldcustcard;
        insert into tmm22_customers@ccgl_24
        select * from tmm22_customers b
        where b.busityp <> 'YX' and b.s_status='1' and b.useflg = '1'
          and b.custnm not like '%视频%' and trim(b.custcard) = v_newcustcard
          and b.custcd in(select distinct r.custcd from TMM35_cust_pos_rl r where r.useflg='1');
        ------------------------
      END IF;
      --设备变更
      IF v_tftype = 'BG' THEN
        ----开通单状态
        update tsl01_extend set useflg = '2' where opbillid = v_tfid;

        ---------------------
        update sm_in_open_result set sys_status = '0' where id = v_id;
        ------------------

        -- 变更 tmm35_cust_pos_rl

        select newcustcard,    newcustcd, custcd,      eid,   mr
          into v_newcustcard,  v_custcd,  V_oldCUSTCD, v_eid, v_mr
          from tsl02_extenddt
         where opbillid = v_tfid;

        --delete by libin，at 20170323，reason：确保只修改一条数据
        --update tmm35_cust_pos_rl set useflg = '9' where eid = v_eid;
        --设备变更7000  需要搬迁失效POS(原翻新后的机器) 屏蔽 useflg ='1' and
        IF nvl(v_mr,'0') = '0' THEN
	        update tmm35_cust_pos_rl set useflg = 'A' WHERE eid = v_eid;
	        IF sql%rowcount<1 THEN
	           as_return := '数据异常,仓储系统无此设备!';
	           --return;
	        End if;

        BEGIN
	        insert into tmm35_cust_pos_rl
	          (custcd,  eid,  itemcd,  startdate,  sysinfo, softinfo,
	           posupddate,  posinfo, area,  status,  typflg,
	           maintenancedate,  maintenancetyp, opercd,  gendate,   upddate,  useflg)
	          select v_custcd,  eid,  itemcd,   startdate,  sysinfo,   softinfo,
	                 posupddate,   posinfo,  area,   status,  typflg,
	                 maintenancedate,  maintenancetyp,   opercd,  gendate,  sysdate,  '1'
	            from tmm35_cust_pos_rl
	           --delete by libin，at 20170323，reason：确保只修改一条数据
	           --where useflg ='A' and eid = v_eid;
	           where useflg ='A' and eid = v_eid;
           EXCEPTION
              WHEN OTHERS THEN
              v_posnumber := -1;
           END  ;

	         SELECT count(1) INTO v_posnumber  FROM TMM35_CUST_POS_RL WHERE eid = v_eid;
	
	        --add by libin，at 20170323，reason：回复原有的操作，把useflg置为9，但不知道为什么置为9
	        update tmm35_cust_pos_rl set useflg = '9' where useflg ='A' and eid = v_eid;
	        IF sql%rowcount<1 THEN
	          v_posnumber := 0;
	        END IF;
	
         SELECT count(1) INTO v_posnumber  FROM TMM35_CUST_POS_RL WHERE useflg ='1' AND eid = v_eid AND CUSTCD = V_CUSTCD;

        --ADD BY CBH  AT 20170823 1.更新客户信息；2.新客户的资产无效(此条待议)
        --1.原设备客户：设备数量、开通状态、有效状态、设备状态、设备详细状态
        SELECT count(1) INTO v_posnumber  FROM TMM35_CUST_POS_RL WHERE CUSTCD = V_oldCUSTCD AND USEFLG = '1';
        --SELECT pos_n INTO v_posnumber FROM TMM22_CUSTOMERS WHERE CUSTCD = V_oldCUSTCD;
        IF v_posnumber > 1 THEN
           UPDATE TMM22_CUSTOMERS SET POS_N = v_posnumber  - 1 WHERE  CUSTCD = V_oldCUSTCD;
        END IF;

        IF v_posnumber = 0 THEN
           UPDATE TMM22_CUSTOMERS
              SET POS_N = 0,     S_STATUS = '4',
                  USEFLG = '0' , POSSTATUS = NULL ,POSSTATUS1 = NULL
            WHERE CUSTCD = V_oldCUSTCD;
        END IF ;
        --2.现设备客户：(目前先判断客户设备信息是否为空，为空则取原客户设备信息替换)
        UPDATE TMM22_CUSTOMERS
           SET S_STATUS = '1',     USEFLG = '1',
               replacedate = v_startdate
         WHERE CUSTCD = v_custcd;

         --同步实施部客户
        delete from tmm22_customers@ccgl_24 where trim(CUSTCD) = v_custcd;
        insert into tmm22_customers@ccgl_24
        select * from tmm22_customers b
        where b.busityp <> 'YX' and b.s_status='1' and b.useflg = '1'
          and b.custnm not like '%视频%' and trim(b.CUSTCD) = v_custcd
          and b.custcd in(select distinct r.custcd from TMM35_cust_pos_rl r where r.useflg='1');



        ELSE  --翻新机变更处理
	       insert into tmm35_cust_pos_rl
	          (custcd,  eid,  itemcd, startdate,  sysinfo,   softinfo,
	           posupddate,  posinfo,  area,  status,  typflg,
	           maintenancedate, maintenancetyp,  opercd,  gendate,  upddate,  useflg)
	          select v_custcd,   eid,  itemcd,   startdate,  sysinfo, softinfo,
	                 posupddate,   posinfo,   area, status,  typflg,
	                 maintenancedate,  maintenancetyp, opercd,  gendate,  sysdate,  '1'
	            from tmm35_cust_pos_rl
	           where custcd ='00000389' and eid = v_eid;

	          IF sql%rowcount<1 THEN
	             as_return := '数据异常,35POS更新00000389所属失败!';
	             return;
	          End if;

	         UPDATE TMM43_EID
             SET WHCD    = '',
                 SFLG    = '1',
                 REFID   = v_mid,
                 GENDATE = SYSDATE
           WHERE EID = v_eid;

           IF sql%rowcount<1 THEN
	             as_return := '数据异常,43POS更新EID所属失败!';
	             return;
	          End if;

           UPDATE INPT_TPPOS_BIZ
           SET STATUS = '1',  --0未处理 --1已变更 --2已回收  9--报废
               UPDATOR = as_userid,
               --REFNO处理单据号
               UPDDATE = SYSDATE
               WHERE MRPOSID = v_eid;

            IF sql%rowcount<1 THEN
	             as_return := '数据异常,处理中间表失败!';
	             return;
	          End if;
	
	     END IF ;
      end if;
    END IF;  --整机顺流完成
    --整机逆流--作废
    if v_startdate is null then
      ----开通单状态
      update tsl01_extend set useflg = '9' where opbillid = v_tfid;

      ---------------------
      update sm_in_open_result set sys_status = '9' where id = v_id;
      ------------------
    end if;


  -------------------------
  as_return := 'OK';
  -------------------

EXCEPTION
  when others then
    as_return := sqlcode || sqlerrm;
END;
