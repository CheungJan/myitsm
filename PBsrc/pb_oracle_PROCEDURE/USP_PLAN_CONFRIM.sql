procedure usp_plan_confrim(as_type   char,
                                             as_id     number,
                                             as_userid char,
                                             as_return out varchar2)

 as
  v_type        char(1);
  v_id          number(20);
  v_tftype      char(2);
  v_plid        char(8);
  v_posid       varchar2(128);

  v_oldeid      varchar2(128);

  v_userid      varchar2(6);
  v_itemcd      varchar2(128);
  v_operflg     char(1);
  v_whcd        char(2);

  v_custcd      char(8);
  v_custcard    varchar2(20);

  v_startdate   date;
  v_outbillid   char(8);
  v_caseno      varchar2(258);

  v_mid         varchar2(8);
  v_back        char(1);
  v_oldposid    varchar2(13);
  v_ischange    char(1);
  v_changeeid   varchar2(50);
  ---------------------
  --V_PLAN         plan_cust%rowtype;
  V_FNRET        varchar2(200);
  V_CLOSETYPE    char(2); --关闭单类型
  V_POS_FROM     varchar2(6); --设备来源
  V_SOLVE_TYPE   varchar2(2); --旧机处理
  V_CUST_USEFLG  varchar2(2); --客户无效化
  V_PLANERCD     CHAR (6);    --计划人员
  V_NEW_CUSTCARD varchar2(20); --移机客户磁卡号
  V_NEW_CUSTCD   varchar2(20);
  V_NEW_POSID    varchar2(13);
  V_NEW_POSITEM  varchar2(6);
  v_custnm       varchar2(80);
  v_address      varchar2(80);
  v_phoneno      varchar2(60);
  v_pos          NUMBER;
  v_a            number(12,2);
  v_tmp_cust     varchar2(80);
  ----
begin

  v_userid := as_userid;
  v_type   := as_type;
  v_id     := as_id;

  /***********---整机---v_type='1'**********************
  A.业务块处理
  B.计划块回写
  C.账目表状态更新 sm_in_open_result
  -------------------------------------------------------------------
  ******************************************************/
  If v_type = '1' Then

    select plan_no, case_no, serialno, COMPLETEDDATE
      into v_plid, v_mid, v_posid, v_startdate
      from sm_in_open_result
     where id = v_id;

     --FOR V_PLAN IN (SELECT * FROM PLAN_CUST WHERE PLANNO = v_plid) LOOP

     SELECT PLANTYP,   POS_FROM,   SOLVE_TYPE , CUST_USEFLG,   NEW_CUSTCARD  ,  NEW_CUSTCD,
            NEW_POSID, NEW_POSITEM,
            CUSTCARD,  CUSTNM,    ADDRESS,    PHONENO,  --磁卡号变更
            OPERCD,Deposit

       into v_tftype,  V_POS_FROM, V_SOLVE_TYPE,V_CUST_USEFLG, V_NEW_CUSTCARD,V_NEW_CUSTCD,
            V_NEW_POSID, V_NEW_POSITEM,
            V_CUSTCARD,  v_custnm,  v_address,  v_phoneno,
            V_PLANERCD ,v_a
     FROM PLAN_CUST WHERE PLANNO = v_plid;

    /*========================整机顺流开始==========================*/
    IF v_startdate is not null then

      /***********************A.业务块处理********************************

      ***********************A.业务块处理********************************/

 -----一、门店开通（00）
      IF v_tftype = '00' THEN

        select store_id into v_custcd
          from TIT13_MAINTENANCE_OPEN WHERE NEW_OPENING_ID = v_mid;
 -----20230629 wangjun插入押金信息

       /*   insert into  tmm61_deposit_dtl
           (custcd, id, c_type, old_a, new_a, change_a, updatetime, r_billid, confirm_a, useflg, remark)
           select v_custcd, seq_tmm61_deposit_dtl.nextval, '新增', nvl(tmm61_deposit.amount_money,0), '', v_a, sysdate, v_plid, '', '0', ''
          from tmm22_customers
           left outer join tmm61_deposit on tmm22_customers.custcd=tmm61_deposit.custcd
                  where tmm22_customers.custcd=v_custcd;
        */

   ----------
        update tmm22_customers
           set s_status = '1', opendate = v_startdate,
               replacedate = null,useflg = '1' --可能存在二次开通
         where custcard = v_custcard;

         SELECT itemcd into v_itemcd FROM TMM43_EID WHERE EID =v_posid;


        IF V_POS_FROM = '00' THEN --仓库出
          ----tmm35
          insert into tmm35_cust_pos_rl
                      (custcd,         eid,          itemcd,       startdate,        sysinfo,
                       softinfo,       posupddate,   posinfo,      area,             status,
                       typflg,         maintenancedate,  maintenancetyp, opercd,     gendate,
                       upddate,        useflg)
                select custcd,         v_posid,       v_itemcd,     v_startdate,       OPERSYSTEM,
                         '',           v_startdate,  '',           '',                '',
                         '',           '',           '',           as_userid,        sysdate,
                       sysdate,        '1'
                  from tmm22_customers
                 where custcard = v_custcard;

          ---tmm44
	        update tmm44_pos_r_eid
	           set tmm44_pos_r_eid.gendate = v_startdate,
	               tmm44_pos_r_eid.upddate = v_startdate
	         where tmm44_pos_r_eid.posid = v_posid;
	
	        ----tmm43
	        update tmm43_eid set sflg = '1' where eid = v_posid;
	        ----twh
	        update twh16_outdteid
	           set qcqty = 1
	         where outbillid in
	               (select outbillid from twh15_out where invtyp = '8')
	           and qcqty = 0 and eid = v_posid;
	      ELSE

          --判断新客户是否曾有该台POS 20180131
	        SELECT count(1) INTO v_pos FROM TMM35_CUST_POS_RL WHERE eid = v_posid AND CUSTCD = V_CUSTCD ;

          IF v_pos > 0 THEN
             update tmm35_cust_pos_rl set useflg = '1',MAINTENANCETYP = 'MO',
                                          maintenanceno = v_mid, maintenancedate = SYSDATE,
                                          posupddate = SYSDATE
             WHERE eid = v_posid AND CUSTCD = v_custcd ;--AND useflg = '0'
          Else
             --门店移机或者烟草直调
             insert into tmm35_cust_pos_rl
                        (custcd,         eid,          itemcd,       startdate,        sysinfo,
                         softinfo,       posupddate,   posinfo,      area,             status,
                         typflg,         maintenancedate,  maintenancetyp, opercd,     gendate,
                         upddate,        useflg)
                  select custcd,         v_posid,       v_itemcd,     v_startdate,       OPERSYSTEM,
                           '',           v_startdate,  '',           '',                '',
                           '',           '',           '',           as_userid,        sysdate,
                         sysdate,        '1'
                    from tmm22_customers
                   where custcard = v_custcard;
           End If;


           --移出门店设备无效化
	         IF V_NEW_CUSTCD = '00000389' THEN
	            DELETE tmm35_cust_pos_rl WHERE CUSTCD = V_NEW_CUSTCD AND EID = v_posid;
	         ELSE
	             UPDATE tmm35_cust_pos_rl SET USEFLG = '0',  UPDDATE = SYSDATE
	             WHERE CUSTCD = V_NEW_CUSTCD AND USEFLG = '1' ;
           END IF;
	
          --旧门店处理
          IF V_CUST_USEFLG = '1' THEN
             --移出门店客户无效化
             UPDATE TMM22_CUSTOMERS SET USEFLG = '0',  UPDDATE = SYSDATE, OPERCD = V_PLANERCD,POS_N = 0, POSSTATUS = '03',POSSTATUS1 = '31' --, S_STATUS = '4' , 使用新函数走一遍
             WHERE CUSTCD = V_NEW_CUSTCD AND USEFLG = '1' ;
          END IF;
	
	
	     END IF ;

        --附属配件 add by cbh 20171113 新增附属配件变更
        --SELECT IS_CHANGE,''''||regexp_replace(CHANGE_EID,',',''',''')||'''' INTO v_ischange,v_changeeid  FROM TIT14_EQUIPMENT_OPEN WHERE NEW_OPENING_ID = v_mid;
        SELECT IS_CHANGE,CHANGE_EID INTO v_ischange,v_changeeid  FROM TIT14_EQUIPMENT_OPEN WHERE NEW_OPENING_ID = v_mid;

        If v_ischange = '1' Then --生成配件确认数据
           V_FNRET := uf_insert_tranitem(v_posid,v_changeeid,as_userid,v_mid);
		   IF V_FNRET <> 'OK' THEN
		      as_return := '附属配件数据确认'||V_FNRET;
	          return;
		   END IF;
        End If;
        If v_ischange = '2' Then --门店旧配件直调
           V_FNRET := UF_INSERT_POSITEM(v_posid,v_changeeid,as_userid,v_mid);
		   IF V_FNRET <> 'OK' THEN
		      as_return := '附属配件数据确认'||V_FNRET;
	          return;
		   END IF;
        End If;
        ------------------------
        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
        V_FNRET := uf_update_cust(v_custcd,as_userid);
        IF V_FNRET <> 'OK' THEN
	        as_return := V_FNRET;
	        return;
        END IF ;
        ------------------------
      END IF;

 -----二、磁卡号变更
      IF v_tftype = '10' THEN
        SELECT STORE_ID INTO v_custcd FROM TIT16_DEVICE_CHANGE WHERE DEVICE_CHANGE_ID = v_mid;


        if V_NEW_POSID  is not null  then
          --旧设备无效,记录变更无效
          update tmm35_cust_pos_rl set useflg = '0',MAINTENANCETYP = 'BG', maintenanceno = v_mid, maintenancedate = sysdate
          WHERE eid = V_NEW_POSID AND CUSTCD = V_NEW_CUSTCD;
          --判断新客户是否曾有该台POS 20180131
            SELECT count(1) INTO v_pos FROM TMM35_CUST_POS_RL WHERE eid = V_NEW_POSID AND CUSTCD = V_CUSTCD ;

            IF v_pos > 0 THEN
                 update tmm35_cust_pos_rl set useflg = '1',MAINTENANCETYP = 'BG',
                                              maintenanceno = v_mid, maintenancedate = SYSDATE,
                                              posupddate = SYSDATE
               WHERE eid = V_NEW_POSID AND CUSTCD = V_CUSTCD AND useflg = '0';

            ELSE
              --生成新客户资产
              insert into tmm35_cust_pos_rl
                  (custcd,  eid,  itemcd,  startdate,  sysinfo, softinfo,
                   posupddate,  posinfo, area,  status,  typflg,
                   maintenancedate,  maintenancetyp, opercd,  gendate,   upddate,  useflg)
              select v_custcd,  eid,  itemcd,   startdate,  sysinfo,   softinfo,
                     posupddate,   posinfo,  area,   status,  typflg,
                     maintenancedate,  maintenancetyp,   opercd,  gendate,  sysdate,  '1'
                from tmm35_cust_pos_rl
               where eid = V_NEW_POSID AND CUSTCD = V_NEW_CUSTCD;
            End if;
        end if;



        update tmm22_customers
           set custcard = v_custcard, CUSTNM = v_custnm,
                ADDRESS = V_ADDRESS, PHONENO = V_PHONENO,
                REPLACEDATE = SYSDATE,S_STATUS = '1'
                --合同内也变化
         where custcd = v_custcd;

        update tmm22_customers
           set useflg = '0'
         where custcd = V_NEW_CUSTCD;

        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
	        V_FNRET := uf_update_cust(v_custcd,as_userid);
	        IF V_FNRET <> 'OK' THEN
		        as_return := V_FNRET;
		        return;
	        END IF ;
	        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
	        V_FNRET := uf_update_cust(V_NEW_CUSTCD,'');
	        IF V_FNRET <> 'OK' THEN
		        as_return := V_FNRET;
		        return;
	        END IF ;


      END IF;

 -----三、旧机翻新（20）
      IF v_tftype = '20' THEN
        select store_id, old_device_id,is_back into v_custcd, v_oldposid,v_back
          from tit15_maintenance_renovate where renew_id = v_mid;


        update tmm22_customers
           set replacedate = v_startdate
         where custcard = v_custcard;

         IF V_POS_FROM = '00'  or  V_POS_FROM = '04'   THEN --00仓库出 --04海晟 20241230

	         --机型复制
	         SELECT itemcd into v_itemcd FROM TMM43_EID WHERE EID =v_posid;
	        ------------------
	
           SELECT sum(case nvl(TMM35_CUST_POS_RL.Useflg,'0') when '1' then 1 when '0' then 0 end  ),max(TMM35_CUST_POS_RL.CUSTCD)
            INTO v_pos，v_tmp_cust FROM tmm43_eid left outer join  TMM35_CUST_POS_RL
           on tmm43_eid.eid= TMM35_CUST_POS_RL.EID
            WHERE tmm43_eid.eid = v_posid AND  TMM35_CUST_POS_RL.useflg='1' ;

             IF v_pos > 0 THEN
                 as_return := 'POS已在其他门店配置'||v_tmp_cust;
	               return;
             end if;
	          ----tmm35
	          insert into tmm35_cust_pos_rl
	                      (custcd,      eid,         itemcd,    startdate,           sysinfo,
	                       softinfo,    posupddate,  posinfo,   area,                status,
	                       typflg,      maintenancedate, maintenancetyp,    opercd,  gendate,
	                       upddate,  useflg)
	                select custcd,   v_posid,   v_itemcd,    v_startdate,    OPERSYSTEM,
	                       '',   v_startdate,    '',    '',   '',
	                       '',  '',    '',   as_userid,  sysdate,
	                       sysdate,     '1'
	                  from tmm22_customers
	                 where custcard = v_custcard;
	          ---tmm44
	          update tmm44_pos_r_eid
	             set tmm44_pos_r_eid.gendate = v_startdate,
	                 tmm44_pos_r_eid.upddate = v_startdate
	           where tmm44_pos_r_eid.posid = v_posid;
	
	          ----tmm43
	          update tmm43_eid set sflg = '1' where eid = v_posid;
	
	          -----twh
	          update twh16_outdteid
	             set qcqty = 1
	           where eid = v_posid
	             and qcqty = 0
	             and outbillid in
	                 (select outbillid from twh15_out where invtyp = '8');
	
	     ELSE
	
	        --机型复制
	         SELECT itemcd into v_itemcd FROM TMM43_EID WHERE EID =v_posid;
	
	
	        --判断新客户是否曾有该台POS 20180131
	        SELECT count(1) INTO v_pos FROM TMM35_CUST_POS_RL WHERE eid = v_posid AND CUSTCD = V_CUSTCD ;

            IF v_pos > 0 THEN
               update tmm35_cust_pos_rl set useflg = '1',MAINTENANCETYP = 'MR',
                                            maintenanceno = v_mid, maintenancedate = SYSDATE,
                                            posupddate = SYSDATE
	           WHERE eid = v_posid AND CUSTCD = v_custcd ;--AND useflg = '0'

	        ELSE
		        --门店或烟草移机
		        insert into tmm35_cust_pos_rl
		                      (custcd,      eid,         itemcd,    startdate,           sysinfo,
		                       softinfo,    posupddate,  posinfo,   area,                status,
		                       typflg,      maintenancedate, maintenancetyp,    opercd,  gendate,
		                       upddate,  useflg)
		                select custcd,   v_posid,   v_itemcd,    v_startdate,    OPERSYSTEM,
		                       '',   v_startdate,    '',    '',   '',
		                       '',  '',    '',   as_userid,  sysdate,
		                       sysdate,     '1'
		                  from tmm22_customers
		                 where custcard = v_custcard;
		          ---tmm44
		          update tmm44_pos_r_eid
		             set tmm44_pos_r_eid.gendate = v_startdate,
		                 tmm44_pos_r_eid.upddate = v_startdate
		           where tmm44_pos_r_eid.posid = v_posid;
		
		
			      --移机旧门店处理
		          IF V_CUST_USEFLG = '1' THEN
		             --移出门店客户无效化
		             UPDATE TMM22_CUSTOMERS SET USEFLG = '0',  UPDDATE = SYSDATE, OPERCD = V_PLANERCD,POS_N = 0, POSSTATUS = '03',POSSTATUS1 = '31'--, S_STATUS = '4' , 使用新函数走一遍
		             WHERE CUSTCD = V_NEW_CUSTCD AND USEFLG = '1' ;
		
		          END IF;
		      END IF ;
	
	         --移出门店设备无效化
	         IF V_NEW_CUSTCD = '00000389' THEN
	            DELETE tmm35_cust_pos_rl WHERE CUSTCD = V_NEW_CUSTCD AND EID = v_posid;
	         ELSE
	             UPDATE tmm35_cust_pos_rl SET USEFLG = '0',  UPDDATE = SYSDATE
	             WHERE CUSTCD = V_NEW_CUSTCD AND USEFLG = '1' ;
           END IF;

	     END IF ;

           --附属配件 add by cbh 20171113 新增附属配件变更
         SELECT IS_CHANGE,CHANGE_EID INTO v_ischange,v_changeeid  FROM TIT15_EQUIPMENT_RENOVATE WHERE RENOVATE_ID = v_mid;

        If v_ischange = '1' Then --生成配件确认数据
           V_FNRET := uf_insert_tranitem(v_posid,v_changeeid,as_userid,v_mid);
		   IF V_FNRET <> 'OK' THEN
		      as_return := '附属配件数据确认'||V_FNRET;
	          return;
		   END IF;
        End If;
        If v_ischange = '2' Then --门店旧配件直调
           V_FNRET := UF_INSERT_POSITEM(v_posid,v_changeeid,as_userid,v_mid);
		   IF V_FNRET <> 'OK' THEN
		      as_return := '附属配件数据确认'||V_FNRET;
	          return;
		   END IF;
        End If;

          IF trim(V_SOLVE_TYPE) = '0' THEN
             --旧机作废
             UPDATE TMM35_CUST_POS_RL SET maintenanceno = v_mid, maintenancedate = SYSDATE,
                                          USEFLG = '0',posupddate = SYSDATE
              WHERE EID = v_oldposid;

             --0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6:检验中 7:生产中 8:在库
             UPDATE TMM43_EID SET SFLG = '2', refid = v_mid WHERE EID = v_oldposid;
          END IF ;

      END IF;

 -----四、门店关闭（30）
      IF v_tftype = 'GB' THEN
        ----开通单状态
        update tsl01_extend set useflg = '2' where opbillid = v_plid;

        SELECT S.STORE_ID , CLOSE_TYPE INTO v_custcd, V_CLOSETYPE
          FROM TIT18_STORE_CLOSE S
         WHERE S.REQUSET_PAPER_ID = v_plid;

        IF V_CLOSETYPE = 'YJ' THEN
           update tmm22_customers T set T.s_status = '3', T.custnm = '(永久关闭)' || T.custnm
	        where T.custcd = v_custcd ;
        ELSE
	       update tmm22_customers T set T.s_status = '2', T.custnm = '(临时关闭)' || T.custnm
	        where T.custcd = v_custcd     ;
        END IF ;

        ------------------------
        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
        V_FNRET := uf_update_cust(v_custcd,as_userid);
        IF V_FNRET <> 'OK' THEN
	        as_return := V_FNRET;
	        return;
        END IF ;
        ------------------------
      end if;



 -------------------------------------业务逻辑--END-----------------------------------------
 	
      /***********************C.账目表状态更新********************************
      update sm_in_open_result set sys_status = '2' where id = v_id;
      ***********************C.账目表状态更新********************************/
      update sm_in_open_result set sys_status = '2' where id = v_id;

      update plan_cust set status = '01' where planno = v_plid; --计划完成

    END IF;
    /*========================整机顺流结束==========================*/



 --整机逆流--作废
    if v_startdate is null then

      /***********************B.计划块回写********************************
      update plan_cust set status = '09' where planno = v_plid;
      ***********************B.计划块回写********************************/
      update plan_cust set status = '09' where planno = v_plid; --计划作废

    end if;


  END IF;

---------取机
  if v_type = '3' THEN
     --取v_tftype 进行判断
	    select changetype, serialno, old_serialno, operflg, INSERT_TIME, case_no
	      into v_tftype, v_posid, v_oldeid, v_operflg, v_startdate, v_caseno
	      from sm_in_part_change
	     where id = v_id;

     select store_id,REQUSET_PAPER_ID into v_custcd,v_plid
	        from tit10_maintenanceday
	       where maintenance_id = v_caseno;
	
	
	 SELECT PLANTYP,   POS_FROM,   SOLVE_TYPE , CUST_USEFLG,   NEW_CUSTCARD  ,  NEW_POSID, NEW_POSITEM,
            OPERCD
       into v_tftype,  V_POS_FROM, V_SOLVE_TYPE,V_CUST_USEFLG, V_NEW_CUSTCARD, V_NEW_POSID, V_NEW_POSITEM,
            V_PLANERCD
     FROM PLAN_CUST WHERE PLANNO = v_plid;

      --2.旧机入库 并生成入库单记录 取消与门店对应关系
	    v_outbillid := uf_get_billnou('IN'); --生成入库单号
	    v_whcd := 'L1';
	    insert into twh13_in
	      (whcd,  indate,  inbillid,  refbillid, invtyp,
	       ptimes,  memo,  opercd,  gendate,   auditflg,
	       auditman,  auditdate,  optyp,  useflg,  suppcd)
	      select v_whcd,  sysdate,   v_outbillid,   v_caseno,  'C',
	             '0',  '',  'SYS',  sysdate,  '',
	             '',  '',  '1',   '1',  ''
	        from tmm43_eid
	       where eid = v_oldeid;
	
	    insert into twh14_checkindt
	      (whcd, inbillid, lineno, itemtyp, itemcd, prddate, inqty)
	      select v_whcd, v_outbillid, 1, 'DJ', itemcd, prddate, 1
	        from tmm43_eid
	       where eid = v_oldeid;
	
	    -----保存库存数
	    insert into tmp_wh_stock
	      (itemcd, whcd, itemtyp, prddate, stock)
	      select itemcd, whcd, itemtyp, prddate, itemqty
	        from twh11_detail
	       where exists
	       (select *
	                from twh14_checkindt
	               where twh14_checkindt.inbillid = v_outbillid
	                 and twh11_detail.itemcd = twh14_checkindt.itemcd
	                 and twh11_detail.prddate = twh14_checkindt.prddate
	                 and twh11_detail.whcd = twh14_checkindt.whcd
	                 and twh11_detail.itemtyp = twh14_checkindt.itemtyp);
	
	    ------更新批次主表
	    update twh11_detail
	       set upddate = sysdate,
	           itemqty = itemqty + (select inqty
	                        from twh14_checkindt
	                       where twh11_detail.itemcd = twh14_checkindt.itemcd
	                         and twh11_detail.prddate = twh14_checkindt.prddate
	                         and twh11_detail.whcd = twh14_checkindt.whcd
	                         and twh11_detail.itemtyp = twh14_checkindt.itemtyp
	                         and twh14_checkindt.inbillid = v_outbillid)
	     where exists
	     (select *
	              from twh14_checkindt
	             where twh14_checkindt.inbillid = v_outbillid
	               and twh11_detail.itemcd = twh14_checkindt.itemcd
	               and twh11_detail.prddate = twh14_checkindt.prddate
	               and twh11_detail.whcd = twh14_checkindt.whcd
	               and twh11_detail.itemtyp = twh14_checkindt.itemtyp);
	
	    ------插新批次主表
	    insert into twh11_detail
	      (seqno,  whcd,  itemtyp, itemcd,  prddate,
	       itemqty,  opercd,  gendate,  upddate,  useflg)
	      select twh11_seqno.nextval,  whcd,  itemtyp,  itemcd,  prddate,
	             inqty,  v_userid,  sysdate,  sysdate, '0'
	        from twh14_checkindt
	       where inbillid = v_outbillid
	         and not EXISTS (select * from twh11_detail
					               where twh11_detail.itemcd = twh14_checkindt.itemcd
					                 and twh11_detail.prddate = twh14_checkindt.prddate
					                 and twh11_detail.itemtyp = twh14_checkindt.itemtyp
					                 and twh11_detail.whcd = twh14_checkindt.whcd);
	
	    ------插新批次明细表
	    insert into twh12_detaildt
	      (seqno,  iotyp,  whcd, itemtyp, itemcd,
	       prddate,  billid,  invdate,  invtyp,  itemqty,
	       storeqty,   opercd,  gendate,   useflg)
	      select twh12_seqno.nextval,  '1',   a.whcd,  a.itemtyp,  a.itemcd,
	             a.prddate,  a.inbillid,  b.indate,   b.invtyp,  a.inqty,
	             nvl(c.stock, 0) + a.inqty,  v_userid,  sysdate,   '0'
	        from twh14_checkindt a
	       inner join twh13_in b  on a.inbillid = b.inbillid
	        left outer join tmp_wh_stock c  on a.whcd = c.whcd
	         and a.itemtyp = c.itemtyp
	         and a.itemcd = c.itemcd
	         and a.prddate = c.prddate
	       where a.inbillid = v_outbillid;
	
	
	------------------回写块------------
	    --取机门店处理
       IF V_CUST_USEFLG = '1' THEN
          --移出门店客户无效化
          UPDATE TMM22_CUSTOMERS SET USEFLG = '0',  UPDDATE = SYSDATE, OPERCD = V_PLANERCD,POS_N = 0--维护单已选设备状态, POSSTATUS = '03',POSSTATUS1 = '31' --, S_STATUS = '4' , 使用新函数走一遍
          WHERE CUSTCD = v_custcd AND USEFLG = '1' ;

       END IF;
	
	    --修改tmm43
	    update tmm43_eid
	       set whcd    = v_whcd,
	           sflg    = '8',
	           qcflg   = 'DJ',
	           itemtyp = 'DJ',
	           refid   = v_outbillid,
	           gendate = sysdate
	     where eid = v_oldeid;

	    --更新tmm35
	    update tmm35_cust_pos_rl
	       set useflg = '0',UPDDATE = SYSDATE
	     where eid = v_oldeid  and custcd = v_custcd;
	
	     --更新plan_cust
	    update plan_cust  set status = '01' where planno = v_plid;
	
	
	     DELETE FROM tmm35_cust_pos_rl WHERE EID = v_oldeid AND custcd = '00000389';
	    ------------------------------------------------------------------------------------------------
	


  end if;

  -------------------------
  as_return := 'OK';
  -------------------

EXCEPTION
  when others then
    as_return := sqlcode || sqlerrm;
END;
