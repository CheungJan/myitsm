procedure usp_trans_in_confrim_180416(as_type   char,
                                                 as_id     number,
                                                 as_userid char,
                                                 as_return out varchar2)

 as
  v_type        char(1);
  v_id          number(20);
  v_tftype      char(2);
  v_tfid        char(8);
  v_eid         varchar2(128);
  v_oldeid      varchar2(128);
  v_posid       varchar2(128);
  v_userid      varchar2(6);
  v_itemcd      varchar2(128);
  v_operflg     char(1);
  v_whcd        char(2);
  v_etype       char(1);
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
  v_outbillid   char(8);
  v_NAME        varchar2(100);
  v_PHONENO     varchar2(100);
  v_CONTACTOR   varchar2(100);
  v_caseno      varchar2(258);
  v_olddegree   number;
  v_enddate     date;
  v_sflg        char(1);
  v_mid         varchar2(8);
  v_back        char(1);
  v_oldposid    varchar2(13);
  v_ischange    char(1);
  v_changeeid   varchar2(50);
 -- v_changeeid1  varchar2(50);
  v_itemeid     varchar2(128);
  v_itemeidcd    varchar2(128);
  v_item         number(5);
  V_ENGINEER     CHAR (6); --上门工程师
  v_mr           CHAR (1);--是否翻新机
  V_FNRET        varchar2(200);
  V_CLOSETYPE    char(2); --关闭单类型
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
  辅助函数
  uf_add_item --新增配件
  uf_add_posunit  --新增pos
  uf_update_cust(客户代码、更新人(空为原更新人)、返回OK)  --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
  usp_insert_biz  --记录中间表 （想做流水表，目前只有翻新使用）
  ******************************************************/
  If v_type = '1' Then

    select plan_no, case_no, cardcode, serialno, COMPLETEDDATE
      into v_tfid, v_mid, v_custcard, v_str1, v_startdate
      from sm_in_open_result
     where id = v_id;

    IF substr(v_tfid,1,2) = 'PL' THEN
       SELECT PLANTYP into v_tftype FROM PLAN_CUST WHERE PLANNO = v_tfid;
    ELSE
	   select sltyp, itemcd
	     into v_tftype, v_itemcd
	     from tsl01_extend b
	    where opbillid = v_tfid;
    END IF ;
    /*========================整机顺流开始==========================*/
    if v_startdate is not null then

      /***********************A.业务块处理********************************
      一、门店开通（XZ）
      二、旧机翻新（GX）
      三、免费更换（GH）
      四、门店关闭（GB）
      五、门店搬迁（BQ）
      六、磁卡号变更（CK）
      七、设备变更（BG）
      ***********************A.业务块处理********************************/

      --门店开通
      IF v_tftype = 'XZ' THEN  ----开通单
      	select store_id into v_custcd
          from TIT13_MAINTENANCE_OPEN WHERE NEW_OPENING_ID = v_mid;

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
        update sm_in_open_result set sys_status = '2' where id = v_id;
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
              select custcd,         v_str1,       v_itemcd,     v_startdate,       OPERSYSTEM,
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
           V_FNRET := UF_INSERT_POSITEM(v_str1,v_changeeid,as_userid,v_mid);
           IF V_FNRET <> 'OK' THEN
	          as_return := V_FNRET;
	          return;
           END IF ;


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

      --回写开通单状态
      --回写pos门店关系表
      --------------------------------------------------

      --旧机翻新
      IF v_tftype = 'GX' THEN
        select store_id, old_device_id,is_back into v_custcd, v_oldposid,v_back
          from tit15_maintenance_renovate where renew_id = v_mid;

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

        update tmm22_customers
           set replacedate = v_startdate
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
                select custcd,   v_str1,   v_itemcd,    v_startdate,    OPERSYSTEM,
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

             V_FNRET := UF_INSERT_POSITEM(v_str1,v_changeeid,as_userid,v_mid);
	         IF V_FNRET <> 'OK' THEN
		        as_return := V_FNRET;
		        return;
	         END IF ;

          End If;

        END IF;

        ---翻新机回收   到虚拟库挂虚拟客户
        IF v_back = 'Y' THEN
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
          insert into tmm35_cust_pos_rl
	          (custcd,  eid,  itemcd,  startdate,  sysinfo, softinfo,
	           posupddate,  posinfo, area,  status,  typflg,
	           maintenancedate,  maintenancetyp, opercd,  gendate,   upddate,  useflg)
	          select '00000389',  eid,  itemcd,   startdate,  sysinfo,   softinfo,
	                 posupddate,   posinfo,  area,   status,  typflg,
	                 maintenancedate,  maintenancetyp,   opercd,  gendate,  sysdate,  '1'
	            from tmm35_cust_pos_rl
	           WHERE CUSTCD = V_CUSTCD  and eid = v_oldposid;

          UPDATE TMM35_CUST_POS_RL
             SET useflg = '0',
                 MAINTENANCETYP = 'MR'  --翻新机待取回
           WHERE EID = v_oldposid
             AND CUSTCD = V_CUSTCD;
       ELSE
          UPDATE TMM43_EID
             SET --WHCD    = 'DJ',  --直调报废
                 SFLG    = '2',
                 REFID   = v_mid,
                 ITEMTYP = 'DJ',
                 GENDATE = SYSDATE
           WHERE EID = v_oldposid;

          UPDATE TMM35_CUST_POS_RL
             SET USEFLG = '0'
           WHERE EID = v_oldposid
             AND CUSTCD = V_CUSTCD;
        END IF;


        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
        V_FNRET := uf_update_cust(v_custcd,as_userid);
        IF V_FNRET <> 'OK' THEN
	        as_return := V_FNRET;
	        return;
        END IF ;


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
            select custcd,  v_str1,  v_itemcd, v_startdate, OPERSYSTEM,  '',
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

        SELECT S.STORE_ID , CLOSE_TYPE INTO v_custcd, V_CLOSETYPE
          FROM TIT18_STORE_CLOSE S
         WHERE S.REQUSET_PAPER_ID = v_tfid;

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
      --门店搬迁
      IF v_tftype = 'BQ' THEN
        ----开通单状态
        update tsl01_extend set useflg = '2' where opbillid = v_tfid;

        select custcd  ,rtrim(newcustcard), newaddress, N_NAME, N_PHONENO, N_CONTACTOR
          into v_custcd,v_newcustcard     , v_address , v_NAME, v_PHONENO, v_CONTACTOR
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
        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
        V_FNRET := uf_update_cust(v_custcd,as_userid);
        IF V_FNRET <> 'OK' THEN
	        as_return := V_FNRET;
	        return;
        END IF ;
        ------------------------
      end if;

      --磁卡号变更
      IF v_tftype = 'CK' THEN
        ----开通单状态
        update tsl01_extend set useflg = '2' where opbillid = v_tfid;

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

        select newcustcard,    newcustcd, custcd,      eid,   mr
          into v_newcustcard,  v_custcd,  V_oldCUSTCD, v_eid, v_mr
          from tsl02_extenddt
         where opbillid = v_tfid;

        --变更 tmm35_cust_pos_rl
        IF nvl(v_mr,'0') = '0' THEN
	        --旧设备无效,记录变更无效
	        update tmm35_cust_pos_rl set useflg = '0',MAINTENANCETYP = 'BG', maintenanceno = v_mid, maintenancedate = sysdate
	        WHERE eid = v_eid AND CUSTCD = V_oldCUSTCD;
	
	        --判断新客户是否曾有该台POS 20180131
	        SELECT count(1) INTO v_pos FROM TMM35_CUST_POS_RL WHERE eid = v_eid AND CUSTCD = V_CUSTCD ;

            IF v_pos > 0 THEN
               update tmm35_cust_pos_rl set useflg = '1',MAINTENANCETYP = 'BG',
                                            maintenanceno = v_mid, maintenancedate = SYSDATE,
                                            posupddate = SYSDATE
	           WHERE eid = v_eid AND CUSTCD = V_CUSTCD AND useflg = '0';

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
		         where eid = v_eid AND CUSTCD = V_oldCUSTCD;
	        End if;
	
	        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
	        V_FNRET := uf_update_cust(v_custcd,as_userid);
	        IF V_FNRET <> 'OK' THEN
		        as_return := V_FNRET;
		        return;
	        END IF ;
	        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
	        V_FNRET := uf_update_cust(V_oldCUSTCD,'');
	        IF V_FNRET <> 'OK' THEN
		        as_return := V_FNRET;
		        return;
	        END IF ;
	
	     ELSE --翻新机变更处理
	        UPDATE tmm35_cust_pos_rl
	           SET CUSTCD = v_custcd, upddate = SYSDATE,
	               MAINTENANCETYP = 'BG', maintenanceno = v_mid, maintenancedate = sysdate
	        WHERE EID = v_eid AND CUSTCD = '00000389';
	
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
           SET STATUS = '1',  --0未处理 --1已变更 --2已回收   9--报废
               UPDATOR = as_userid,
               --REFNO处理单据号
               UPDDATE = SYSDATE
               WHERE MRPOSID = v_eid AND STATUS = '0';

            IF sql%rowcount<1 THEN
	             as_return := '数据异常,处理中间表失败!';
	             return;
	        End if;
	
	        --更新客户信息(更新人、更新时间、开通状态、台数)同步客户
	        V_FNRET := uf_update_cust(v_custcd,as_userid);
	        IF V_FNRET <> 'OK' THEN
		        as_return := V_FNRET;
		        return;
	        END IF ;
	
	      END IF;

	   END IF; --BG
	
      /***********************C.账目表状态更新********************************
      update sm_in_open_result set sys_status = '2' where id = v_id;
      ***********************C.账目表状态更新********************************/
      update sm_in_open_result set sys_status = '2' where id = v_id;

    END IF;
    /*========================整机顺流结束==========================*/



 --整机逆流--作废
    if v_startdate is null then

      /***********************B.计划块回写********************************
      update tsl01_extend set useflg = '2' where opbillid = v_tfid;
      ***********************B.计划块回写********************************/
      update tsl01_extend set useflg = '9' where opbillid = v_tfid;

      /***********************C.账目表状态更新********************************
      update sm_in_open_result set sys_status = '2' where id = v_id;
      ***********************C.账目表状态更新********************************/
      update sm_in_open_result set sys_status = '9' where id = v_id;
    end if;


  END IF;
  -----------------------------------------------------------------------------------------

  ---v_type='2' 配件
  ----------------------------------------------------------------

  if v_type = '2' then

    --取v_tftype 进行判断
    select changetype,  serialno,  old_serialno,  operflg,  INSERT_TIME,  case_no
      into v_tftype, v_posid, v_oldeid, v_operflg, v_startdate, v_caseno
      from sm_in_part_change
     where id = v_id;

    if v_tftype <> '4' then
      select changetype,  serialno, old_serialno, itemcd, operflg, INSERT_TIME, case_no
        into v_tftype, v_eid, v_posid, v_itemcd, v_operflg, v_startdate, v_caseno
        from sm_in_part_change
       inner join tmm43_eid  on sm_in_part_change.serialno = tmm43_eid.eid
       where id = v_id;

      ----v_tftype ='1','3'  v_posid   '2' v_oldeid
      v_oldeid := v_posid;
      ---------------------------------------------
      --新增 old_serialno=poseid
      ---------------------------------------
    end if;

    ---变更状态
    update sm_in_part_change
       set sys_status                 = 2,
           sm_in_part_change.syn_time = sysdate,
           AUDITERCD = v_userid
     where id = v_id;

    if v_tftype = '1' then

      -----更新设备IDtmm43_eid
      --Sflg  Char(1) 状态标志  0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6:检验中 7:生产中 8:在库

      --构建pos配件清单关系  gendate 质保起始日

      delete from tmm44_pos_r_eid
       where posid = v_posid
         and eid = v_eid;

      insert into tmm44_pos_r_eid
        (posid, itemcd, eid, opercd, gendate, upddate, useflg)
      values
        (v_posid, v_itemcd, v_eid, v_userid, v_startdate, v_startdate, '1');

      ----出库
      --新品仓库
      select whcd into v_whcd from tmm43_eid where eid = v_eid;

      if v_whcd is null then
        as_return := '-1 调换配件已不在库！';
        return;
      end if;

      v_outbillid := uf_get_billnou('OT');

      insert into twh15_out
        (whcd,
         outdate,
         outbillid,
         invtyp,
         ptimes,
         memo,
         opercd,
         gendate,
         auditflg,
         auditman,
         auditdate,
         optyp,
         useflg,
         targetwhcd,
         suppcd)

        select whcd,
               sysdate,
               v_outbillid,
               '3',
               '0',
               '新增配件itsm回单号(' || to_char(v_id) || '):' || v_caseno,
               as_userid,
               sysdate,
               '',
               '',
               '',
               'ID',
               '1',
               '',
               ''
          from tmm43_eid
         where eid = v_eid;

      insert into twh16_outdteid
        (whcd,
         outbillid,
         lineno,
         itemtyp,
         itemcd,
         prddate,
         eid,
         outqty,
         qcqty)
        select whcd, v_outbillid, 1, itemtyp, itemcd, prddate, eid, 1, 1
          from tmm43_eid
         where eid = v_eid;

      usp_wh_out('3', v_outbillid, 'SYS', as_return);

      if as_return <> 'OK' then
        return;
      end if;

      update tmm43_eid
         set sflg = '1', refid = v_id, gendate = sysdate, opercd = v_userid
       where eid = v_eid;
      -------写入通信表 回写itsm资产信息
      insert into o_tf_in_part
        (sm_no, asset_serialno, asset_model, name,  part_serialno, part_model,
         old_degree, enabled_date,  repair_date, cost,  deliverno,
         receiptno, description, insert_time, syn_time, sys_status,  checkflg)

        select lpad(to_char(tf_seqid.nextval), 10, 0),
               a.posid,
               a.itemcd,
               c.itemnm,
               b.eid,
               c.itemcd,
               12,
               a.gendate,
               a.gendate + c.newperiod,
               '',  '',  '', '',  sysdate, '',  1,  '0'
          from tmm43_eid b
     inner join tmm12_items c on b.itemcd = c.itemcd
     inner join tmm44_pos_r_eid a on a.eid = b.eid

         where b.eid = v_eid;

    end if;
    ---------------------------------------
    ----------调换
    ------------------------------------------
    if v_tftype = '2' then

      --新品仓库 也是旧品入的仓库
      select whcd, old_degree
        into v_whcd, v_olddegree
        from tmm43_eid
       where eid = v_eid;

      if v_whcd is null then

        as_return := '-1 调换配件已不在库！';
        return;

      end if;

      --计算质保期
      --如果出保 按调换品的新旧属性old_dregee 3=旧 12=新
      --保内 质保期延续旧品的

      --   select gendate into v_startdate from tmm44_pos_r_eid
      --   where  tmm44_pos_r_eid.eid=v_oldeid and tmm44_pos_r_eid.useflg='1';

      if v_olddegree is null then
        --老数据根据质检标志判断出保日期
        select decode(c.qcflg,
                      'GA',
                      a.gendate + b.newperiod,
                      'GB',
                      a.gendate + b.newperiod,
                      'GC',
                      a.gendate + b.oldperiod,
                      sysdate)

          into v_enddate

          from tmm44_pos_r_eid a
         inner join tmm12_items b  on a.itemcd = b.itemcd
         inner join tmm43_eid c  on a.eid = c.eid
         where a.eid = v_oldeid and a.useflg = '1';

      else

        if v_olddegree = 3 then
          select a.gendate + b.oldperiod
            into v_enddate
            from tmm44_pos_r_eid a
           inner join tmm12_items b  on a.itemcd = b.itemcd
           inner join tmm43_eid c  on a.eid = c.eid
           where a.eid = v_oldeid and a.useflg = '1';

        end if;

        if v_olddegree = 12 then
          select a.gendate + b.newperiod
            into v_enddate
            from tmm44_pos_r_eid a
           inner join tmm12_items b  on a.itemcd = b.itemcd
           inner join tmm43_eid c  on a.eid = c.eid
           where a.eid = v_oldeid  and a.useflg = '1';

        end if;

      end if;

      if v_startdate <= v_enddate then
        ----保内沿用老的质保时间

        select gendate
          into v_startdate
          from tmm44_pos_r_eid
         where tmm44_pos_r_eid.eid = v_oldeid  and tmm44_pos_r_eid.useflg = '1';

      end if;

      -----------新品出库

      v_outbillid := uf_get_billnou('OT');

      insert into twh15_out
        (whcd,
         outdate,
         outbillid,
         invtyp,
         ptimes,
         memo,
         opercd,
         gendate,
         auditflg,
         auditman,
         auditdate,
         optyp,
         useflg,
         targetwhcd,
         suppcd)

        select whcd,
               sysdate,
               v_outbillid,
               '3',
               '0',
               '调换配件itsm回单号(' || to_char(v_id) || '):' || v_caseno,
               'SYS',
               sysdate,
               '',
               '',
               '',
               'ID',
               '1',
               '',
               ''
          from tmm43_eid
         where eid = v_eid;

      insert into twh16_outdteid
        (whcd,
         outbillid,
         lineno,
         itemtyp,
         itemcd,
         prddate,
         eid,
         outqty,
         qcqty)
        select whcd, v_outbillid, 1, itemtyp, itemcd, prddate, eid, 1, 1
          from tmm43_eid
         where eid = v_eid;

      usp_wh_out('3', v_outbillid, 'SYS', as_return);

      if as_return <> 'OK' then
        return;
      end if;

      select posid
        into v_posid
        from tmm44_pos_r_eid a
       where eid = v_oldeid  and useflg = '1';

      ------变更新品的状态

      update tmm43_eid
         set sflg = '1', refid = v_id, gendate = sysdate, opercd = v_userid

       where eid = v_eid;

      -----------------------------------------------------------------------

      --处理旧的
      if v_operflg = '0' then
        ---旧品不入库
        --旧品报废
        update tmm43_eid
           set sflg    = '2',
               refid   = v_id,
               gendate = sysdate,
               opercd  = v_userid
         where eid = v_oldeid;

        --无效关系表
        update tmm44_pos_r_eid
           set useflg = '0'
         where eid = v_oldeid  and posid = v_posid;

        --构建pos配件清单关系 质保算新的
        -- delete from tmm44_pos_r_eid
        -- where posid=v_posid and  eid=v_eid;

        delete from tmm44_pos_r_eid
         where posid = v_posid
           and eid = v_eid;

        insert into tmm44_pos_r_eid
          (posid, itemcd, eid, opercd, gendate, upddate, useflg)
          select v_posid, itemcd, v_eid, v_userid, sysdate, sysdate, '1'
            from tmm43_eid
           where eid = v_eid;

      end if;

      if v_operflg = '1' then
        ---旧品入库

        --构建pos配件清单关系 沿用老的质保时间

        delete from tmm44_pos_r_eid  where posid = v_posid and eid = v_eid;

        insert into tmm44_pos_r_eid
          (posid, itemcd, eid, opercd, gendate, upddate, useflg)
          select v_posid,
                 itemcd,
                 v_eid,
                 v_userid,
                 v_startdate,
                 sysdate,
                 '1'
            from tmm43_eid
           where eid = v_eid;

        --增加库存
        v_outbillid := uf_get_billnou('IN');

        insert into twh13_in
          (whcd,
           indate,
           inbillid,
           refbillid,
           invtyp,
           ptimes,
           memo,
           opercd,
           gendate,
           auditflg,
           auditman,
           auditdate,
           optyp,
           useflg,
           suppcd)

          select v_whcd,
                 sysdate,
                 v_outbillid,
                 v_id,
                 '3',
                 '0',
                 '',
                 'SYS',
                 sysdate,
                 '',
                 '',
                 '',
                 '1',
                 '1',
                 ''
            from tmm43_eid
           where eid = v_oldeid;

        insert into twh14_checkindt
          (whcd, inbillid, lineno, itemtyp, itemcd, prddate, inqty)
          select v_whcd, v_outbillid, 1, 'DJ', itemcd, prddate, 1
            from tmm43_eid
           where eid = v_oldeid;

        usp_wh_in('3', v_outbillid, 'SYS', as_return);

        --旧品在库
        update tmm43_eid
           set sflg    = '8',
               refid   = v_outbillid,
               gendate = sysdate,
               opercd  = v_userid,
               qcflg   = 'DJ',
               itemtyp = 'DJ',
               whcd    = v_whcd
         where eid = v_oldeid;

        --无效关系表
        update tmm44_pos_r_eid
           set useflg = '0'
         where eid = v_oldeid  and posid = v_posid;

        if as_return <> 'OK' then
          return;
        end if;

      end if;
    end if;
    ------------------------------------
    ------------作废 删除资产数据
    -----------------------------------------
    if v_tftype = '3' then

      select eid, etyp, sflg
        into v_posid, v_etype, v_sflg
        from tmm43_eid
       where eid = v_eid;

      if sql%rowcount = 0 then
        as_return := '数据异常,仓储系统无此设备!';
        return;
      end if;

      if v_sflg <> '1' then
        as_return := '数据异常,该设备状态异常!';
        return;
      end if;

      if v_etype = '1' then
        --整机报废
        --旧品报废
        update tmm43_eid
           set sflg    = '2',
               refid   = v_id,
               gendate = sysdate,
               opercd  = v_userid

         where exists (select *
                  from tmm44_pos_r_eid
                 where tmm43_eid.eid = tmm44_pos_r_eid.eid
                   and tmm44_pos_r_eid.posid = v_posid);
        --无效关系表
        update tmm44_pos_r_eid set useflg = '0' where posid = v_posid;
      end if;

      if v_etype = '0' then
        --配件报废
        --旧品报废
        update tmm43_eid
           set sflg    = '2',
               refid   = v_id,
               gendate = sysdate,
               opercd  = v_userid

         where eid = v_eid;
        --无效关系表
        update tmm44_pos_r_eid set useflg = '0' where eid = v_eid;
      end if;

    end if;

    ------------------------------------
    ------------返回 旧配件入库
    -----------------------------------------
    if v_tftype = '4' then
      if v_operflg = '1' then

        --返回(返修)配件 默认进 待报废库
        v_whcd := 'L1';
        --增加库存
        v_outbillid := uf_get_billnou('IN');

        insert into twh13_in
          (whcd,
           indate,
           inbillid,
           refbillid,
           invtyp,
           ptimes,
           memo,
           opercd,
           gendate,
           auditflg,
           auditman,
           auditdate,
           optyp,
           useflg,
           suppcd)

          select v_whcd,
                 sysdate,
                 v_outbillid,
                 v_id,
                 '3',
                 '0',
                 '',
                 'SYS',
                 sysdate,
                 '',
                 '',
                 '',
                 '1',
                 '1',
                 ''
            from tmm43_eid
           where eid = v_oldeid;

        insert into twh14_checkindt
          (whcd, inbillid, lineno, itemtyp, itemcd, prddate, inqty)
          select v_whcd, v_outbillid, 1, 'DJ', itemcd, prddate, 1
            from tmm43_eid
           where eid = v_oldeid;

        usp_wh_in('3', v_outbillid, 'SYS', as_return);

        --旧品在库
        update tmm43_eid
           set sflg    = '8',
               refid   = v_outbillid,
               gendate = sysdate,
               opercd  = v_userid,
               qcflg   = 'DJ',
               itemtyp = 'DJ',
               whcd    = v_whcd
         where eid = v_oldeid;

        --无效关系表
        update tmm44_pos_r_eid
           set useflg = '0'
         where eid = v_oldeid  and posid = v_posid;

        if as_return <> 'OK' then
          return;
        end if;

      end if;
    end if;
  end if;

  if v_type = '3' then

    --取v_tftype 进行判断
    select changetype, serialno, old_serialno, operflg, INSERT_TIME, case_no
      into v_tftype, v_posid, v_oldeid, v_operflg, v_startdate, v_caseno
      from sm_in_part_change
     where id = v_id;
    if v_posid is not null then
      --判断新机状态是否为销售出库
      select sflg, itemcd
        into v_sflg, v_itemcd
        from tmm43_eid
       where eid = v_posid;
      if v_sflg <> 'S' then
        as_return := '数据异常,该设备状态异常! 非销售出库状态-->' || v_sflg;
        return;
      end if;

      select store_id
        into v_custcd
        from tit10_maintenanceday
       where maintenance_id = v_caseno;
      if v_custcd is null then
        as_return := '数据异常,获取对应门店异常!';
        return;
      end if;
      ---------------------------------------------------------------------------------
      --1.新机与门店建立对应关系 , 修改对应出库单数量
      ----tmm35
      insert into tmm35_cust_pos_rl
        (custcd,   eid,   itemcd,  startdate,  sysinfo,
         softinfo,   posupddate,  posinfo, area,  status,
         typflg,  maintenancedate,  maintenancetyp,  opercd,   gendate,
         upddate,  useflg)
        select custcd,   v_posid,  v_itemcd,  v_startdate,  '',
               '',    v_startdate,   '',   '',  '',
               '',    '',   '',  as_userid,   sysdate,
               sysdate,  '1'
          from tmm22_customers
         where custcd = v_custcd;

      ---tmm44
      update tmm44_pos_r_eid
         set tmm44_pos_r_eid.upddate = v_startdate --,tmm44_pos_r_eid.gendate=v_startdate
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
    end if;
    -----------------------------------------------------------------------------------

      -----------------------------------------------------------------------------------
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

    --修改tmm43
    update tmm43_eid
       set whcd    = v_whcd,
           sflg    = '8',
           qcflg   = 'DJ',
           itemtyp = 'DJ',
           refid   = v_outbillid,
           gendate = sysdate
     where eid = v_oldeid;

    --日常维护单做门店关闭旧机器回收时（新机id为空，旧机id不为空）要取得v_custcd值, add at 2016-04-27
    if v_oldeid is not null and v_posid is null then
      select store_id into v_custcd
        from tit10_maintenanceday
       where maintenance_id = v_caseno;
    end if;

    --更新tmm35
    update tmm35_cust_pos_rl
       set useflg = '0'
     where eid = v_oldeid  and custcd = v_custcd;

     DELETE FROM tmm35_cust_pos_rl WHERE EID = v_oldeid AND custcd = '00000389';
    ------------------------------------------------------------------------------------------------

    -- 更新门店换机日期
    update tmm22_customers
       set replacedate = v_startdate
     where custcd = v_custcd;

    ---变更记录状态
    update sm_in_part_change
       set sys_status                 = 2,
           sm_in_part_change.syn_time = sysdate,
           AUDITERCD = v_userid
     where id = v_id;

  end if;

  -------------------------
  as_return := 'OK';
  -------------------

EXCEPTION
  when others then
    as_return := sqlcode || sqlerrm;
END;
