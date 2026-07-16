procedure USP_plan_rp
( as_sdate VARCHAR2 ,as_edate VARCHAR2,  as_return out varchar2)






AS
  --V_RET     VARCHAR2(100);
  V_min     NUMBER;
  v_max     number;
v_c1  number; v_c2  number; v_c3  number; v_c4  number; v_c5  number; v_c6  number;  v_c7  number;
 -- V_ITEM    NUMBER;
  --V_OPERCD  CHAR(6);
 -- V_STR     VARCHAR2(128);
 -- v_itemeid VARCHAR2(13);

  --
    --附属配件生成确认数据
  --
BEGIN
  delete  from T_PLAN_STATUS_RP ;

  insert into T_PLAN_STATUS_RP
  (planid,c_type,custcard,custname,c_1,c1_s,c1_sd,c1_ed)
  select planno,case plantyp
  when '00' then '全新开通'
  when '10' then '磁卡变更'
  when '20' then '旧机翻新'
  when '30' then '旧机回收'
  when '40' then '旧机关店' end  ,
  custcard,custnm,
  '开始时间：'||to_char(gendate,'yyyy-mm-dd')||chr(10)||chr(13)||
  '结束时间：'||case status when '01' then to_char(uf_getplan_f_time(planno),'yyyy-mm-dd') else '-' end||chr(10)||chr(13)||
  '状    态：'||
  case status
    when '00' then '（计划中）'
      when '01' then '（计划完成）'
        when '02' then '（分派中）'
          when '03' then '（实施完成）'
            when '04' then '（实施中）'
              when '08' then '（计划退回）'
   when '09' then '（已作废）' end  , status,gendate,uf_getplan_f_time(planno)

  from plan_cust
  where to_char(gendate,'yyyy-mm-dd') between as_sdate and as_edate  and  status<>'09' ;
----------------全新开通----------------------------------------------------------------------------

------押金
select c1,c2,c3,c4,c5 into v_c1,v_c2,v_c3,v_c4,v_c5 from t_plan_report_arg
where c_type='00' ;


  update T_PLAN_STATUS_RP
  set (c_2,c2_s,c2_sd,c2_ed)=(select
'原 押 金：'||nvl(cast(a.old_a as varchar2(10)), '-')||chr(10)||chr(13)||
'应收金额：'||nvl(cast(a.change_a as varchar2(10)),'-')||chr(10)||chr(13)||
'实收金额：'||nvl(cast(a.confirm_a as varchar2(10)),'-')||chr(10)||chr(13)||
'财务确认：'||nvl(b.c_m,'-')||CHR(10)||
'收    据：'||nvl(b.c_s,'-')||CHR(10) , case a.useflg when '0' then '未确认' when '1' then '已确认' end ,
a.gendate,a.updatetime
 from tmm61_deposit_dtl a  left outer join tmm61_deposit_list b
on a.r_billid=b.billid
where T_PLAN_STATUS_RP.PLANID=a.r_billid )
where c_type='全新开通'
;
------- 呼出
update T_PLAN_STATUS_RP
set c_3=uf_getplan_last_srvback(PLANID)
where c_type='全新开通';

delete from  TMP_PLAN_RP ;

insert into TMP_PLAN_RP
(  planid  ,minid ,maxid)
select planno ,min(dtlid),max(dtlid)
from PLAN_SERVE
where planno in (select planid from  T_PLAN_STATUS_RP  where c_type='全新开通')
group by planno;

update TMP_PLAN_RP
set ( sdate)= (select  GENDATE from  PLAN_SERVE  where PLAN_SERVE.DTLID=minid ) ,
(edate,status)= (select OPDATE, status from  PLAN_SERVE  where PLAN_SERVE.DTLID=maxid  )  ;

update T_PLAN_STATUS_RP
set (C3_Sd,c3_ed,c3_s)=(select sdate,edate,status from TMP_PLAN_RP where TMP_PLAN_RP.PLANID=T_PLAN_STATUS_RP.PLANID)
where c_type='全新开通';


---实施
--磁卡 新机 翻新  旧机 回收 关闭
 /*update T_PLAN_STATUS_RP
set c_4=uf_getplan_last_tit('新机',PLANID)
where c_type='全新开通';
select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end

into ls_return

 from V_TIT_SATUS
where requset_paper_id=v_palnid and c_type= v_type ;
*/
update T_PLAN_STATUS_RP
set (c_4,c4_sd,c4_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,nvl(close_time,sysdate)
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP.PLANID and c_type= '新机'
)
where c_type='全新开通';

----资产配置

update T_PLAN_STATUS_RP
set (c_5,c5_sd,c5_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_open_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13) ,
syn_time,nvl(sm_open_f_time.update_time,sysdate)
  from sm_in_open_result
  left outer join (select planid,min(update_time) update_time from   sm_open_f_time group by planid ) sm_open_f_time
     on sm_open_f_time.planid=sm_in_open_result.plan_no
where plan_no=T_PLAN_STATUS_RP.PLANID
)
where c_type='全新开通';


update T_PLAN_STATUS_RP
set C1_Limit=C1_Ed - c1_sd - v_c1,
    C2_Limit=C2_Ed - c2_sd - v_c2,
    C3_Limit=C3_Ed - c3_sd - v_c3,
    C4_Limit=C4_Ed - c4_sd - v_c4,
    C5_Limit=C5_Ed - c5_sd - v_c5
where c_type='全新开通';

--------------磁卡变更-------------------------------------------------------------------------------------
------------------------- 呼出
select c1,c2,c3,c4 into v_c1,v_c2,v_c3,v_c4 from t_plan_report_arg
where c_type='10' ;


update T_PLAN_STATUS_RP
set c_2=uf_getplan_last_srvback(PLANID)
where c_type='磁卡变更';

delete from  TMP_PLAN_RP ;

insert into TMP_PLAN_RP
(  planid  ,minid ,maxid)
select planno ,min(dtlid),max(dtlid)
from PLAN_SERVE
where planno in (select planid from  T_PLAN_STATUS_RP  where c_type='磁卡变更')
group by planno;

update TMP_PLAN_RP
set ( sdate)= (select  GENDATE from  PLAN_SERVE  where PLAN_SERVE.DTLID=minid ) ,
(edate,status)= (select OPDATE, status from  PLAN_SERVE  where PLAN_SERVE.DTLID=maxid  )  ;

update T_PLAN_STATUS_RP
set (C2_Sd,c2_ed,c2_s)=(select sdate,edate,status from TMP_PLAN_RP where TMP_PLAN_RP.PLANID=T_PLAN_STATUS_RP.PLANID)
where c_type='磁卡变更';
-----------------------实施
update T_PLAN_STATUS_RP
set (c_3,c3_sd,c3_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,nvl(close_time,sysdate)
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP.PLANID and c_type= '磁卡'
)
where c_type='磁卡变更';
----------------------------资产配置

update T_PLAN_STATUS_RP
set (c_4,c4_sd,c4_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_open_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13) ,
syn_time,nvl(sm_open_f_time.update_time,sysdate)
  from sm_in_open_result
  left outer join (select planid,min(update_time) update_time from   sm_open_f_time group by planid ) sm_open_f_time
     on sm_open_f_time.planid=sm_in_open_result.plan_no
where plan_no=T_PLAN_STATUS_RP.PLANID
)
where c_type='磁卡变更';


update T_PLAN_STATUS_RP
set C1_Limit=C1_Ed - c1_sd - v_c1,
    C2_Limit=C2_Ed - c2_sd - v_c2,
    C3_Limit=C3_Ed - c3_sd - v_c3,
    C4_Limit=C4_Ed - c4_sd - v_c4

where c_type='磁卡变更';

------------------旧机翻新----------------------------------------------------------------------------

------押金
select c1,c2,c3,c4,c5,c6,c7 into v_c1,v_c2,v_c3,v_c4,v_c5,v_c6,v_c7 from t_plan_report_arg
where c_type='20' ;

  update T_PLAN_STATUS_RP
  set (c_2,c2_s,c2_sd,c2_ed)=(select
'原 押 金：'||nvl(cast(a.old_a as varchar2(10)), '-')||CHR(10)||
'应收金额：'||nvl(cast(a.change_a as varchar2(10)),'-')||CHR(10)||
'实收金额：'||nvl(cast(a.confirm_a as varchar2(10)),'-')||CHR(10)||
'财务确认：'||nvl(b.c_m,'-')||CHR(10)||
'收    据：'||nvl(b.c_s,'-')||CHR(10) , case a.useflg when '0' then '未确认' when '1' then '已确认' end ,
a.gendate,a.updatetime
 from tmm61_deposit_dtl a  left outer join tmm61_deposit_list b
on a.r_billid=b.billid
where T_PLAN_STATUS_RP.PLANID=a.r_billid )
where c_type='旧机翻新'
;
------- 呼出
update T_PLAN_STATUS_RP
set c_3=uf_getplan_last_srvback(PLANID)
where c_type='旧机翻新';

delete from  TMP_PLAN_RP ;

insert into TMP_PLAN_RP
(  planid  ,minid ,maxid)
select planno ,min(dtlid),max(dtlid)
from PLAN_SERVE
where planno in (select planid from  T_PLAN_STATUS_RP  where c_type='旧机翻新')
group by planno;

update TMP_PLAN_RP
set ( sdate)= (select  GENDATE from  PLAN_SERVE  where PLAN_SERVE.DTLID=minid ) ,
(edate,status)= (select OPDATE, status from  PLAN_SERVE  where PLAN_SERVE.DTLID=maxid  )  ;

update T_PLAN_STATUS_RP
set (C3_Sd,c3_ed,c3_s)=(select sdate,edate,status from TMP_PLAN_RP where TMP_PLAN_RP.PLANID=T_PLAN_STATUS_RP.PLANID)
where c_type='旧机翻新';
----------装机实施
update T_PLAN_STATUS_RP
set (c_4,c4_sd,c4_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,nvl(close_time,sysdate)
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP.PLANID and c_type= '翻新'
)
where c_type='旧机翻新';
----------新资产确认
update T_PLAN_STATUS_RP
set (c_5,c5_sd,c5_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_open_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13) ,
syn_time,nvl(sm_open_f_time.update_time,sysdate)
  from sm_in_open_result
  left outer join (select planid,min(update_time) update_time from   sm_open_f_time group by planid ) sm_open_f_time
     on sm_open_f_time.planid=sm_in_open_result.plan_no
where plan_no=T_PLAN_STATUS_RP.PLANID
)
where c_type='旧机翻新';

----------旧机实施
update T_PLAN_STATUS_RP
set (c_6,c6_sd,c6_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,nvl(close_time,sysdate)
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP.PLANID and c_type= '旧机'
)
where c_type='旧机翻新';
-----------旧机入库

update T_PLAN_STATUS_RP
set (c_7,c7_sd,c7_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_part_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13)||uf_sm_part_errinfo(T_PLAN_STATUS_RP.Planid) ,
syn_time,nvl(sm_part_f_time.update_time,sysdate)
  from    (   select b.requset_paper_id  plan_no ,a.case_no case_no ,a.syn_time syn_time,a.insert_time  insert_time  from SM_IN_PART_CHANGE a
                          inner join TIT10_MAINTENANCEDAY b
                          on a.case_no=b.maintenance_id
                          where b.requset_paper_id is not null  )  sm_in_part

  left outer join (select planid,min(update_time) update_time from   sm_part_f_time group by planid ) sm_part_f_time
     on sm_part_f_time.planid=sm_in_part.case_no
where plan_no=T_PLAN_STATUS_RP.PLANID
)
where c_type='旧机翻新';


update T_PLAN_STATUS_RP
set C1_Limit=C1_Ed - c1_sd - v_c1,
    C2_Limit=C2_Ed - c2_sd - v_c2,
    C3_Limit=C3_Ed - c3_sd - v_c3,
    C4_Limit=C4_Ed - c4_sd - v_c4,
    C5_Limit=C5_Ed - c5_sd - v_c5,
     C6_Limit=C6_Ed - c6_sd - v_c6,
      C7_Limit=C7_Ed - c7_sd - v_c7
where c_type='旧机翻新';
-------------------旧机回收----------------------------------------------------------------------
select c1,c2,c3,c4,c5 into v_c1,v_c2,v_c3,v_c4,v_c5 from t_plan_report_arg
where c_type='30' ;

------- 呼出
update T_PLAN_STATUS_RP
set c_2=uf_getplan_last_srvback(PLANID)
where c_type='旧机回收';

delete from  TMP_PLAN_RP ;

insert into TMP_PLAN_RP
(  planid  ,minid ,maxid)
select planno ,min(dtlid),max(dtlid)
from PLAN_SERVE
where planno in (select planid from  T_PLAN_STATUS_RP  where c_type='旧机回收')
group by planno;

update TMP_PLAN_RP
set ( sdate)= (select  GENDATE from  PLAN_SERVE  where PLAN_SERVE.DTLID=minid ) ,
(edate,status)= (select OPDATE, status from  PLAN_SERVE  where PLAN_SERVE.DTLID=maxid  )  ;

update T_PLAN_STATUS_RP
set (C2_Sd,c2_ed,c2_s)=(select sdate,edate,status from TMP_PLAN_RP where TMP_PLAN_RP.PLANID=T_PLAN_STATUS_RP.PLANID)
where c_type='旧机回收';


---实施
--磁卡 新机 翻新  旧机 回收 关闭
 /*update T_PLAN_STATUS_RP
set c_4=uf_getplan_last_tit('新机',PLANID)
where c_type='全新开通';
select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end

into ls_return

 from V_TIT_SATUS
where requset_paper_id=v_palnid and c_type= v_type ;
*/
-------------实施
update T_PLAN_STATUS_RP
set (c_3,c3_sd,c3_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,nvl(close_time,sysdate)
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP.PLANID and c_type= '回收'
)
where c_type='旧机回收';

----旧机入库

update T_PLAN_STATUS_RP
set (c_4,c4_sd,c4_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_part_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13)||uf_sm_part_errinfo(T_PLAN_STATUS_RP.Planid) ,
syn_time,nvl(sm_part_f_time.update_time,sysdate)
  from    (   select b.requset_paper_id  plan_no ,a.case_no case_no ,a.syn_time syn_time,a.insert_time  insert_time  from SM_IN_PART_CHANGE a
                          inner join TIT10_MAINTENANCEDAY b
                          on a.case_no=b.maintenance_id
                          where b.requset_paper_id is not null  )  sm_in_part

  left outer join (select planid,min(update_time) update_time from   sm_part_f_time group by planid ) sm_part_f_time
     on sm_part_f_time.planid=sm_in_part.case_no
where plan_no=T_PLAN_STATUS_RP.PLANID
)
where c_type='旧机回收';

-------押金

  update T_PLAN_STATUS_RP
  set (c_5,c5_s,c5_sd,c5_ed)=(select
'原 押 金：'||nvl(cast(a.old_a as varchar2(10)), '-')||CHR(10)||
'应收金额：'||nvl(cast(a.change_a as varchar2(10)),'-')||CHR(10)||
'实收金额：'||nvl(cast(a.confirm_a as varchar2(10)),'-')||CHR(10)||
'财务确认：'||nvl(b.c_m,'-')||CHR(10)||
'收    据：'||nvl(b.c_s,'-')||CHR(10) , case a.useflg when '0' then '未确认' when '1' then '已确认' end ,
a.gendate,a.updatetime
 from tmm61_deposit_dtl a  left outer join tmm61_deposit_list b
on a.r_billid=b.billid
where T_PLAN_STATUS_RP.PLANID=a.r_billid )
where c_type='旧机回收'
;
-----------------------------

update T_PLAN_STATUS_RP
set C1_Limit=C1_Ed - c1_sd - v_c1,
    C2_Limit=C2_Ed - c2_sd - v_c2,
    C3_Limit=C3_Ed - c3_sd - v_c3,
    C4_Limit=C4_Ed - c4_sd - v_c4,
    C5_Limit=C5_Ed - c5_sd - v_c5
where c_type='旧机回收';


--------------------门店关闭--------------------------------------------------------------------------


------------------


------- 呼出



/* plan_cust  status
计划中	00
计划完成	01
分派中	02
实施完成	03
实施中	04
计划退回	08
计划作废	09
  */

commit;
-------------------------
as_return:='OK';
-------------------

EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;
END ;
