procedure usp_trans_itsm_confrim(as_type   char,
                                                 as_id     number,
                                                 as_userid char,
                                                 as_return out varchar2)

 as
  v_type        char(1);
  v_id          number(20);
  v_tftype      char(2);

  v_eid         varchar2(128);
  v_oldeid      varchar2(128);
  v_posid       varchar2(128);
  v_userid      varchar2(6);
  v_itemcd      varchar2(128);
  v_operflg     char(1);
  v_whcd        char(2);
  v_etype       char(1);
  v_custcd      char(8);

  v_startdate   date;
  v_outbillid   char(8);


  v_caseno      varchar2(258);
  v_olddegree   number;
  v_enddate     date;
  v_sflg        char(1);

begin

  v_userid := as_userid;
  v_type   := as_type;
  v_id     := as_id;

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
           sm_in_part_change.case_no  = sm_in_part_change.case_no ||
                                        '   审核人id:' || v_userid
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
        (custcd,
         eid,
         itemcd,
         startdate,
         sysinfo,
         softinfo,
         posupddate,
         posinfo,
         area,
         status,
         typflg,
         maintenancedate,
         maintenancetyp,
         opercd,
         gendate,
         upddate,
         useflg)
        select custcd,
               v_posid,
               v_itemcd,
               v_startdate,
               '',
               '',
               v_startdate,
               '',
               '',
               '',
               '',
               '',
               '',
               as_userid,
               sysdate,
               sysdate,
               '1'
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
             v_caseno,
             'C',
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
      (seqno,
       whcd,
       itemtyp,
       itemcd,
       prddate,
       itemqty,
       opercd,
       gendate,
       upddate,
       useflg)
      select twh11_seqno.nextval,
             whcd,
             itemtyp,
             itemcd,
             prddate,
             inqty,
             v_userid,
             sysdate,
             sysdate,
             '0'
        from twh14_checkindt
       where inbillid = v_outbillid
         and not exists
       (select *
                from twh11_detail
               where twh11_detail.itemcd = twh14_checkindt.itemcd
                 and twh11_detail.prddate = twh14_checkindt.prddate
                 and twh11_detail.itemtyp = twh14_checkindt.itemtyp
                 and twh11_detail.whcd = twh14_checkindt.whcd);

    ------插新批次明细表
    insert into twh12_detaildt
      (seqno,
       iotyp,
       whcd,
       itemtyp,
       itemcd,
       prddate,
       billid,
       invdate,
       invtyp,
       itemqty,
       storeqty,
       opercd,
       gendate,
       useflg)
      select twh12_seqno.nextval,
             '1',
             a.whcd,
             a.itemtyp,
             a.itemcd,
             a.prddate,
             a.inbillid,
             b.indate,
             b.invtyp,
             a.inqty,
             nvl(c.stock, 0) + a.inqty,
             v_userid,
             sysdate,
             '0'
        from twh14_checkindt a
       inner join twh13_in b
          on a.inbillid = b.inbillid
        left outer join tmp_wh_stock c
          on a.whcd = c.whcd
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
      select store_id
        into v_custcd
        from tit10_maintenanceday
       where maintenance_id = v_caseno;
    end if;

    --更新tmm35
    update tmm35_cust_pos_rl
       set useflg = '0'
     where eid = v_oldeid  and custcd = v_custcd;
    ------------------------------------------------------------------------------------------------

    -- 更新门店换机日期
    update tmm22_customers
       set replacedate = v_startdate
     where custcd = v_custcd;

    ---变更记录状态
    update sm_in_part_change
       set sys_status                 = 2,
           sm_in_part_change.syn_time = sysdate,
           sm_in_part_change.case_no  = sm_in_part_change.case_no ||
                                        '   审核人id:' || v_userid
     where id = v_id;

  end if;

  -------------------------
  as_return := 'OK';
  -------------------

EXCEPTION
  when others then
    as_return := sqlcode || sqlerrm;
END;
