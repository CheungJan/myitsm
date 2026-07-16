procedure usp_wh_changel1pos(as_type   char,
                                                 as_id     number,
                                                 as_userid char,
                                                 as_return out varchar2)

 as
  v_opid        number;
  v_poseid      varchar2(20);
  v_chtype      char(1);
  v_oldeid      varchar2(20);
  v_neweid      varchar2(20);
  v_whcd        char(2);
  v_sflg        char(1);
  v_itemcdpj    varchar2(20);
  v_outbillid   char(8);
  v_olddegree   number;
  v_startdate   date;
  v_enddate     date;
  v_operflg     char(1);
  ----
begin
  ---v_type='1'  确认   '9' 作废
  -------------------------------------------------------------------

  --确认
  if as_type = '1' then
    update twh21_pos_change set useflg = '1',remark='确认人id:'||as_userid||'('||to_char(trunc(sysdate),'yyyy-mm-dd')||')' where id=as_id;

    for lv_pcdt in (select operation_id,poseid,changetype,old_eid,new_eid from twh22_pos_change_dt where useflg='0' and id=as_id)
    loop
      v_opid  :=lv_pcdt.operation_id;
      v_poseid:=lv_pcdt.poseid;
      v_chtype:=lv_pcdt.changetype;
      v_oldeid:=lv_pcdt.old_eid;
      v_neweid:=lv_pcdt.new_eid;
      --v_chtype 新增  1/调换  2/作废  3/返回  4

      --新增------------------
      if v_chtype = '1' then
         --Sflg  Char(1) 状态标志  0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6:检验中 7:生产中 8:在库
         select sflg,itemcd,whcd
          into v_sflg,v_itemcdpj,v_whcd
          from tmm43_eid
         where useflg='1' and eid = v_neweid;

        if sql%rowcount = 0 then
          as_return := '数据异常,仓储系统无配件'||v_neweid||'，无法添加!';
          return;
        end if;
        if v_sflg = '1' then
          as_return := '数据异常,配件'||v_neweid||'，已是[已使用]状态，无法添加到在库POS机!';
          return;
        end if;

      --构建pos配件清单关系  gendate 质保起始日
      delete from tmm44_pos_r_eid
       where posid = v_poseid
         and eid = v_neweid;

      insert into tmm44_pos_r_eid
        (posid, itemcd, eid, opercd, gendate, upddate, useflg)
      values
        (v_poseid, v_itemcdpj, v_neweid, as_userid, sysdate, sysdate, '1');

      ----出库
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
               '新增配件(L1库)在库POS机配件变更单号(' || to_char(v_opid) || '):' || to_char(as_id),
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
         where eid = v_neweid;

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
         where eid = v_neweid;

      usp_wh_out('3', v_outbillid, 'SYS', as_return);

      if as_return <> 'OK' then
        return;
      end if;

      ---变更状态
      update tmm43_eid
         set sflg = '1', refid = as_id, gendate = sysdate, opercd = as_userid
       where eid = v_neweid;

       --o_tf开头的表已经不用，作废以下代码
 /*     -------写入通信表 回写itsm资产信息
      insert into o_tf_in_part
        (sm_no,
         asset_serialno,
         asset_model,
         name,
         part_serialno,
         part_model,
         old_degree,
         enabled_date,
         repair_date,
         cost,
         deliverno,
         receiptno,
         description,
         insert_time,
         syn_time,
         sys_status,
         checkflg)

        select lpad(to_char(tf_seqid.nextval), 10, 0),
               a.posid,
               a.itemcd,
               c.itemnm,
               b.eid,
               c.itemcd,
               12,
               a.gendate,
               a.gendate + c.newperiod,
               '',
               '',
               '',
               '',
               sysdate,
               '',
               1,
               '0'
          from tmm43_eid b
         inner join tmm12_items c
            on b.itemcd = c.itemcd

         inner join tmm44_pos_r_eid a
            on a.eid = b.eid

         where b.eid = v_neweid;*/
      end if;
      ------------------------


      --调换------------------
      if v_chtype = '2' then
        v_operflg := '1';--保证旧品入库
        --新品仓库 也是旧品入的仓库
        select whcd, old_degree
          into v_whcd, v_olddegree
          from tmm43_eid
         where eid = v_neweid;

        if v_whcd is null then

          as_return := '-1 调换配件已不在库！';
          return;

        end if;

        --计算质保期
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
           inner join tmm12_items b
              on a.itemcd = b.itemcd
           inner join tmm43_eid c
              on a.eid = c.eid
           where a.eid = v_oldeid
             and a.useflg = '1';

        else

          if v_olddegree = 3 then
            select a.gendate + b.oldperiod
              into v_enddate
              from tmm44_pos_r_eid a
             inner join tmm12_items b
                on a.itemcd = b.itemcd
             inner join tmm43_eid c
                on a.eid = c.eid
             where a.eid = v_oldeid
               and a.useflg = '1';

          end if;

          if v_olddegree = 12 then
            select a.gendate + b.newperiod
              into v_enddate
              from tmm44_pos_r_eid a
             inner join tmm12_items b
                on a.itemcd = b.itemcd
             inner join tmm43_eid c
                on a.eid = c.eid
             where a.eid = v_oldeid
               and a.useflg = '1';

          end if;

        end if;

        if v_startdate <= v_enddate then
          ----保内沿用老的质保时间

          select gendate
            into v_startdate
            from tmm44_pos_r_eid
           where tmm44_pos_r_eid.eid = v_oldeid
             and tmm44_pos_r_eid.useflg = '1';

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
                 '调换配件(L1库)在库POS机配件变更单号(' || to_char(v_opid) || '):' || to_char(as_id),
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
           where eid = v_neweid;

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
           where eid = v_neweid;

        usp_wh_out('3', v_outbillid, 'SYS', as_return);

        if as_return <> 'OK' then
          return;
        end if;

        select posid
          into v_poseid
          from tmm44_pos_r_eid a
         where eid = v_oldeid
           and useflg = '1';

        ------变更新品的状态

        update tmm43_eid
           set sflg = '1', refid = as_id, gendate = sysdate, opercd = as_userid
         where eid = v_neweid;

        -----------------------------------------------------------------------

        --处理旧的
        if v_operflg = '0' then
          ---旧品不入库
          --旧品报废
          update tmm43_eid
             set sflg    = '2',
                 refid   = as_id,
                 gendate = sysdate,
                 opercd  = as_userid
           where eid = v_oldeid;

          --无效关系表
          update tmm44_pos_r_eid
             set useflg = '0'
           where eid = v_oldeid
             and posid = v_poseid;

          --构建pos配件清单关系 质保算新的
          delete from tmm44_pos_r_eid
           where posid = v_poseid
             and eid = v_neweid;

          insert into tmm44_pos_r_eid
            (posid, itemcd, eid, opercd, gendate, upddate, useflg)
            select v_poseid, itemcd, v_neweid, as_userid, sysdate, sysdate, '1'
              from tmm43_eid
             where eid = v_neweid;
        end if;

        if v_operflg = '1' then
          ---旧品入库

          --构建pos配件清单关系 沿用老的质保时间
          delete from tmm44_pos_r_eid
           where posid = v_poseid
             and eid = v_neweid;

          insert into tmm44_pos_r_eid
            (posid, itemcd, eid, opercd, gendate, upddate, useflg)
            select v_poseid,
                   itemcd,
                   v_neweid,
                   as_userid,
                   v_startdate,
                   sysdate,
                   '1'
              from tmm43_eid
             where eid = v_neweid;

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
                   as_id,
                   '3',
                   '0',
                   '调换配件(L1库)在库POS机配件变更单号(' || to_char(v_opid) || '):' || to_char(as_id),
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
          if as_return <> 'OK' then
            return;
          end if;

          --旧品在库
          update tmm43_eid
             set sflg    = '8',
                 refid   = v_outbillid,
                 gendate = sysdate,
                 opercd  = as_userid,
                 qcflg   = 'DJ',
                 itemtyp = 'DJ',
                 whcd    = v_whcd
           where eid = v_oldeid;

          --无效关系表
          update tmm44_pos_r_eid
             set useflg = '0'
           where eid = v_oldeid
             and posid = v_poseid;
        end if;
      end if;
      ------------------------

      --作废------------------
      if v_chtype = '3' then
        select sflg
          into v_sflg
          from tmm43_eid
         where useflg='1' and eid = v_oldeid;

        if sql%rowcount = 0 then
          as_return := '数据异常,仓储系统无配件'||v_oldeid||'，无法作废!';
          return;
        end if;

        if v_sflg <> '1' then
          as_return := '数据异常,配件'||v_oldeid||'，不是[已使用]状态!';
          return;
        end if;

        --旧配件报废
        update tmm43_eid
           set sflg    = '2',
               refid   = as_id,
               gendate = sysdate,
               opercd  = as_userid,
               useflg = '0'
         where eid = v_oldeid;
        --无效关系表
        update tmm44_pos_r_eid set useflg = '0' where eid = v_oldeid;
      end if;
      ------------------------


      --返回------------------
      if v_chtype = '4' then
        select sflg
          into  v_sflg
          from tmm43_eid
         where useflg='1' and eid = v_oldeid;

        if sql%rowcount = 0 then
          as_return := '数据异常,仓储系统无配件'||v_oldeid||'，无法返回!';
          return;
        end if;

        ---旧品入库
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
                 as_id,
                 '3',
                 '0',
                 '返回配件(L1库)在库POS机配件变更单号(' || to_char(v_opid) || '):' || to_char(as_id),
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
        if as_return <> 'OK' then
          return;
        end if;

        --旧品在库
        update tmm43_eid
           set sflg    = '8',
               refid   = v_outbillid,
               gendate = sysdate,
               opercd  = as_userid,
               qcflg   = 'DJ',
               itemtyp = 'DJ',
               whcd    = v_whcd
         where eid = v_oldeid;

        --无效关系表
        update tmm44_pos_r_eid
           set useflg = '0'
         where eid = v_oldeid
           and posid = v_poseid;
      end if;
      ------------------------
    end loop;

    update twh22_pos_change_dt set useflg = '1',remark='确认人id:'||as_userid||'('||to_char(trunc(sysdate),'yyyy-mm-dd')||')' where id=as_id and useflg='0';
  end if;

  --作废
  if as_type = '9' then
    update twh21_pos_change set useflg = '9',remark='作废人id:'||as_userid||'('||to_char(trunc(sysdate),'yyyy-mm-dd')||')' where id=as_id;
    update twh22_pos_change_dt set useflg = '9',remark='作废人id:'||as_userid where id=as_id;
  end if;

  -------------------------
  as_return := 'OK';
  -------------------

EXCEPTION
  when others then
    as_return := sqlcode || sqlerrm;

end;
