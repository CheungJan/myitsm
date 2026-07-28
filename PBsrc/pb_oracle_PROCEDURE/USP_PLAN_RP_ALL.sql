procedure USP_plan_rp_all
(   as_return out varchar2)






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
  delete  from T_PLAN_STATUS_RP_all ;

  insert into T_PLAN_STATUS_RP_all
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
   when '09' then '（已作废）' end  , status,gendate,nvl(uf_getplan_f_time(planno),sysdate)

  from plan_cust
  where   status<>'09' and  status<>'01' ;
----------------全新开通----------------------------------------------------------------------------

------押金
select c1,c2,c3,c4,c5 into v_c1,v_c2,v_c3,v_c4,v_c5 from t_plan_report_arg
where c_type='00' ;


  update T_PLAN_STATUS_RP_all
  set (c_2,c2_s,c2_sd,c2_ed)=(select
'原 押 金：'||nvl(cast(a.old_a as varchar2(10)), '-')||chr(10)||chr(13)||
'应收金额：'||nvl(cast(a.change_a as varchar2(10)),'-')||chr(10)||chr(13)||
'实收金额：'||nvl(cast(a.confirm_a as varchar2(10)),'-')||chr(10)||chr(13)||
'财务确认：'||nvl(b.c_m,'-')||CHR(10)||
'收    据：'||nvl(b.c_s,'-')||CHR(10) , case a.useflg when '0' then '未确认' when '1' then '已确认' end ,
a.gendate,a.updatetime
 from tmm61_deposit_dtl a  left outer join tmm61_deposit_list b
on a.r_billid=b.billid
where T_PLAN_STATUS_RP_all.PLANID=a.r_billid )
where c_type='全新开通'
;
------- 呼出
update T_PLAN_STATUS_RP_all
set c_3=uf_getplan_last_srvback(PLANID)
where c_type='全新开通';

delete from  TMP_PLAN_RP ;

insert into TMP_PLAN_RP
(  planid  ,minid ,maxid)
select planno ,min(dtlid),max(dtlid)
from PLAN_SERVE
where planno in (select planid from  T_PLAN_STATUS_RP_all  where c_type='全新开通')
group by planno;

update TMP_PLAN_RP
set ( sdate)= (select  GENDATE from  PLAN_SERVE  where PLAN_SERVE.DTLID=minid ) ,
(edate,status)= (select case Serve_Back when 'N' then sysdate when 'O' then sysdate else  OPDATE end  , status from  PLAN_SERVE where PLAN_SERVE.DTLID=maxid  )  ;

update T_PLAN_STATUS_RP_all
set (C3_Sd,c3_ed,c3_s)=(select sdate,edate,status from TMP_PLAN_RP where TMP_PLAN_RP.PLANID=T_PLAN_STATUS_RP_all.PLANID)
where c_type='全新开通';


---实施
--磁卡 新机 翻新  旧机 回收 关闭
 /*update T_PLAN_STATUS_RP_all
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
update T_PLAN_STATUS_RP_all
set (c_4,c4_sd,c4_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,close_time
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP_all.PLANID and c_type= '新机'
)
where c_type='全新开通';

----资产配置

update T_PLAN_STATUS_RP_all
set (c_5,c5_sd,c5_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_open_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13) ,
syn_time,sm_open_f_time.update_time
  from sm_in_open_result
  left outer join (select planid,min(update_time) update_time from   sm_open_f_time group by planid ) sm_open_f_time
     on sm_open_f_time.planid=sm_in_open_result.plan_no
where plan_no=T_PLAN_STATUS_RP_all.PLANID
)
where c_type='全新开通';


update T_PLAN_STATUS_RP_all
set C1_Limit=nvl(round(C1_Ed - c1_sd - v_c1,1),0),
    C2_Limit=nvl(round(nvl(C2_Ed,sysdate) - c2_sd - v_c2,1),0),
    C3_Limit=nvl(round(nvl(C3_Ed,sysdate) - c3_sd - v_c3,1),0),
    C4_Limit=nvl(round(nvl(C4_Ed,sysdate) - c4_sd - v_c4,1),0),
    C5_Limit=nvl(round(nvl(C5_Ed,sysdate) - c5_sd - v_c5,1),0)
where c_type='全新开通';

--------------磁卡变更-------------------------------------------------------------------------------------
------------------------- 呼出
select c1,c2,c3,c4 into v_c1,v_c2,v_c3,v_c4 from t_plan_report_arg
where c_type='10' ;


update T_PLAN_STATUS_RP_all
set c_2=uf_getplan_last_srvback(PLANID)
where c_type='磁卡变更';

delete from  TMP_PLAN_RP ;

insert into TMP_PLAN_RP
(  planid  ,minid ,maxid)
select planno ,min(dtlid),max(dtlid)
from PLAN_SERVE
where planno in (select planid from  T_PLAN_STATUS_RP_all  where c_type='磁卡变更')
group by planno;

update TMP_PLAN_RP
set ( sdate)= (select  GENDATE from  PLAN_SERVE  where PLAN_SERVE.DTLID=minid ) ,
(edate,status)= (select case Serve_Back when 'N' then sysdate when 'O' then sysdate else  OPDATE end, status from  PLAN_SERVE  where PLAN_SERVE.DTLID=maxid  )  ;

update T_PLAN_STATUS_RP_all
set (C2_Sd,c2_ed,c2_s)=(select sdate,edate,status from TMP_PLAN_RP where TMP_PLAN_RP.PLANID=T_PLAN_STATUS_RP_all.PLANID)
where c_type='磁卡变更';
-----------------------实施
update T_PLAN_STATUS_RP_all
set (c_3,c3_sd,c3_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,close_time
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP_all.PLANID and c_type= '磁卡'
)
where c_type='磁卡变更';
----------------------------资产配置

update T_PLAN_STATUS_RP_all
set (c_4,c4_sd,c4_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_open_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13) ,
syn_time,sm_open_f_time.update_time
  from sm_in_open_result
  left outer join (select planid,min(update_time) update_time from   sm_open_f_time group by planid ) sm_open_f_time
     on sm_open_f_time.planid=sm_in_open_result.plan_no
where plan_no=T_PLAN_STATUS_RP_all.PLANID
)
where c_type='磁卡变更';


update T_PLAN_STATUS_RP_all
set C1_Limit=nvl(round(C1_Ed - c1_sd - v_c1,1),0),
   C2_Limit=nvl(round(nvl(C2_Ed,sysdate) - c2_sd - v_c2,1),0),
    C3_Limit=nvl(round(nvl(C3_Ed,sysdate) - c3_sd - v_c3,1),0),
    C4_Limit=nvl(round(nvl(C4_Ed,sysdate) - c4_sd - v_c4,1),0),
    C5_Limit=nvl(round(nvl(C5_Ed,sysdate) - c5_sd - v_c5,1),0)
where c_type='磁卡变更';

------------------旧机翻新----------------------------------------------------------------------------

------押金
select c1,c2,c3,c4,c5,c6,c7 into v_c1,v_c2,v_c3,v_c4,v_c5,v_c6,v_c7 from t_plan_report_arg
where c_type='20' ;

  update T_PLAN_STATUS_RP_all
  set (c_2,c2_s,c2_sd,c2_ed)=(select
'原 押 金：'||nvl(cast(a.old_a as varchar2(10)), '-')||CHR(10)||
'应收金额：'||nvl(cast(a.change_a as varchar2(10)),'-')||CHR(10)||
'实收金额：'||nvl(cast(a.confirm_a as varchar2(10)),'-')||CHR(10)||
'财务确认：'||nvl(b.c_m,'-')||CHR(10)||
'收    据：'||nvl(b.c_s,'-')||CHR(10) , case a.useflg when '0' then '未确认' when '1' then '已确认' end ,
a.gendate,a.updatetime
 from tmm61_deposit_dtl a  left outer join tmm61_deposit_list b
on a.r_billid=b.billid
where T_PLAN_STATUS_RP_all.PLANID=a.r_billid )
where c_type='旧机翻新'
;
------- 呼出
update T_PLAN_STATUS_RP_all
set c_3=uf_getplan_last_srvback(PLANID)
where c_type='旧机翻新';

delete from  TMP_PLAN_RP ;

insert into TMP_PLAN_RP
(  planid  ,minid ,maxid)
select planno ,min(dtlid),max(dtlid)
from PLAN_SERVE
where planno in (select planid from  T_PLAN_STATUS_RP_all  where c_type='旧机翻新')
group by planno;

update TMP_PLAN_RP
set ( sdate)= (select  GENDATE from  PLAN_SERVE  where PLAN_SERVE.DTLID=minid ) ,
(edate,status)= (select case Serve_Back when 'N' then sysdate when 'O' then sysdate else  OPDATE end, status from  PLAN_SERVE  where PLAN_SERVE.DTLID=maxid  )  ;

update T_PLAN_STATUS_RP_all
set (C3_Sd,c3_ed,c3_s)=(select sdate,edate,status from TMP_PLAN_RP where TMP_PLAN_RP.PLANID=T_PLAN_STATUS_RP_all.PLANID)
where c_type='旧机翻新';
----------装机实施
update T_PLAN_STATUS_RP_all
set (c_4,c4_sd,c4_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,close_time
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP_all.PLANID and c_type= '翻新'
)
where c_type='旧机翻新';
----------新资产确认
update T_PLAN_STATUS_RP_all
set (c_5,c5_sd,c5_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_open_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13) ,
syn_time,sm_open_f_time.update_time
  from sm_in_open_result
  left outer join (select planid,min(update_time) update_time from   sm_open_f_time group by planid ) sm_open_f_time
     on sm_open_f_time.planid=sm_in_open_result.plan_no
where plan_no=T_PLAN_STATUS_RP_all.PLANID
)
where c_type='旧机翻新';

----------旧机实施
update T_PLAN_STATUS_RP_all
set (c_6,c6_sd,c6_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,close_time
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP_all.PLANID and c_type= '旧机'
)
where c_type='旧机翻新';
-----------旧机入库

update T_PLAN_STATUS_RP_all
set (c_7,c7_sd,c7_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_part_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13)||uf_sm_part_errinfo(T_PLAN_STATUS_RP_all.Planid) ,
syn_time,sm_part_f_time.update_time
  from    (   select b.requset_paper_id  plan_no ,a.case_no case_no ,a.syn_time syn_time,a.insert_time  insert_time  from SM_IN_PART_CHANGE a
                          inner join TIT10_MAINTENANCEDAY b
                          on a.case_no=b.maintenance_id
                          where b.requset_paper_id is not null  )  sm_in_part

  left outer join (select planid,min(update_time) update_time from   sm_part_f_time group by planid ) sm_part_f_time
     on sm_part_f_time.planid=sm_in_part.case_no
where plan_no=T_PLAN_STATUS_RP_all.PLANID
)
where c_type='旧机翻新';


update T_PLAN_STATUS_RP_all
set C1_Limit=nvl(round(C1_Ed - c1_sd - v_c1,1),0),
   C2_Limit=nvl(round(nvl(C2_Ed,sysdate) - c2_sd - v_c2,1),0),
    C3_Limit=nvl(round(nvl(C3_Ed,sysdate) - c3_sd - v_c3,1),0),
    C4_Limit=nvl(round(nvl(C4_Ed,sysdate) - c4_sd - v_c4,1),0),
    C5_Limit=nvl(round(nvl(C5_Ed,sysdate) - c5_sd - v_c5,1),0),
     C6_Limit=nvl(round(nvl(C6_Ed,sysdate) - c6_sd - v_c6,1),0),
      C7_Limit=nvl(round(nvl(C7_Ed,sysdate) - c7_sd - v_c7,1),0)
where c_type='旧机翻新';
-------------------旧机回收----------------------------------------------------------------------
select c1,c2,c3,c4,c5 into v_c1,v_c2,v_c3,v_c4,v_c5 from t_plan_report_arg
where c_type='30' ;

------- 呼出
update T_PLAN_STATUS_RP_all
set c_2=uf_getplan_last_srvback(PLANID)
where c_type='旧机回收';

delete from  TMP_PLAN_RP ;

insert into TMP_PLAN_RP
(  planid  ,minid ,maxid)
select planno ,min(dtlid),max(dtlid)
from PLAN_SERVE
where planno in (select planid from  T_PLAN_STATUS_RP_all  where c_type='旧机回收')
group by planno;

update TMP_PLAN_RP
set ( sdate)= (select  GENDATE from  PLAN_SERVE  where PLAN_SERVE.DTLID=minid ) ,
(edate,status)= (select case Serve_Back when 'N' then sysdate when 'O' then sysdate else  OPDATE end , status from  PLAN_SERVE  where PLAN_SERVE.DTLID=maxid  )  ;

update T_PLAN_STATUS_RP_all
set (C2_Sd,c2_ed,c2_s)=(select sdate,edate,status from TMP_PLAN_RP where TMP_PLAN_RP.PLANID=T_PLAN_STATUS_RP_all.PLANID)
where c_type='旧机回收';


---实施
--磁卡 新机 翻新  旧机 回收 关闭
 /*update T_PLAN_STATUS_RP_all
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
update T_PLAN_STATUS_RP_all
set (c_3,c3_sd,c3_ed)=(select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end ,request_time,close_time
 from V_TIT_SATUS
where requset_paper_id=T_PLAN_STATUS_RP_all.PLANID and c_type= '回收'
)
where c_type='旧机回收';

----旧机入库

update T_PLAN_STATUS_RP_all
set (c_4,c4_sd,c4_ed)=(select
'请求时间:'||to_char(syn_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(sm_part_f_time.update_time,'yyyy-mm-dd')||chr(10)||chr(13)||uf_sm_part_errinfo(T_PLAN_STATUS_RP_all.Planid) ,
syn_time,sm_part_f_time.update_time
  from    (   select b.requset_paper_id  plan_no ,a.case_no case_no ,a.syn_time syn_time,a.insert_time  insert_time  from SM_IN_PART_CHANGE a
                          inner join TIT10_MAINTENANCEDAY b
                          on a.case_no=b.maintenance_id
                          where b.requset_paper_id is not null  )  sm_in_part

  left outer join (select planid,min(update_time) update_time from   sm_part_f_time group by planid ) sm_part_f_time
     on sm_part_f_time.planid=sm_in_part.case_no
where plan_no=T_PLAN_STATUS_RP_all.PLANID
)
where c_type='旧机回收';

-------押金

  update T_PLAN_STATUS_RP_all
  set (c_5,c5_s,c5_sd,c5_ed)=(select
'原 押 金：'||nvl(cast(a.old_a as varchar2(10)), '-')||CHR(10)||
'应收金额：'||nvl(cast(a.change_a as varchar2(10)),'-')||CHR(10)||
'实收金额：'||nvl(cast(a.confirm_a as varchar2(10)),'-')||CHR(10)||
'财务确认：'||nvl(b.c_m,'-')||CHR(10)||
'收    据：'||nvl(b.c_s,'-')||CHR(10) , case a.useflg when '0' then '未确认' when '1' then '已确认' end ,
a.gendate,a.updatetime
 from tmm61_deposit_dtl a  left outer join tmm61_deposit_list b
on a.r_billid=b.billid
where T_PLAN_STATUS_RP_all.PLANID=a.r_billid )
where c_type='旧机回收'
;
-----------------------------

update T_PLAN_STATUS_RP_all
set C1_Limit=nvl(round(C1_Ed - c1_sd - v_c1,1),0),
   C2_Limit=nvl(round(nvl(C2_Ed,sysdate) - c2_sd - v_c2,1),0),
    C3_Limit=nvl(round(nvl(C3_Ed,sysdate) - c3_sd - v_c3,1),0),
    C4_Limit=nvl(round(nvl(C4_Ed,sysdate) - c4_sd - v_c4,1),0),
    C5_Limit=nvl(round(nvl(C5_Ed,sysdate) - c5_sd - v_c5,1),0)
where c_type='旧机回收';


--------------------门店关闭--------------------------------------------------------------------------
------------------
------- 呼出

----------------------------------------------------------------------------------------------------
------------------全新开通------------------------------------------------------------------------------------------------------
  delete from T_PLAN_STATUS_ED1 ;
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8)
values( 1, '全新开通','' ,'总单', '押金' ,'呼出','计划确认' ,'新装实施', '资产配置' ) ;
---------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8)
select  2, '全新开通','无问题' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  ) ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  ) ,
sum(case when c3_ed is not null and c4_sd is null then 1 else 0 end ) ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  )

from T_PLAN_STATUS_RP_all
 where c_type='全新开通' and C1_Limit<=0 and C2_Limit<=0 and C3_Limit<=0 and C4_Limit<=0 and C5_Limit<=0;
--------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8)
select  3, '全新开通','预 警' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  )||'/'||sum(case when C2_Limit >0 then 1 else 0 end)  ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  )||'/'||sum(case when C3_Limit >0 then 1 else 0 end )  ,
sum(case when c3_ed is not null and c4_sd is null then 1 else 0 end ) ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )||'/'||sum(case when C4_Limit >0 then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  )||'/'||sum(case when C5_Limit >0 then 1 else 0 end  )

from T_PLAN_STATUS_RP_all
 where c_type='全新开通' and C1_Limit<=0 and （C2_Limit>0 or  C3_Limit>0 or  C4_Limit>0 or C5_Limit>0);
-------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8)
select  4, '全新开通','已超时' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  )||'/'||sum(case when C2_Limit >0 then 1 else 0 end)  ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  )||'/'||sum(case when C3_Limit >0 then 1 else 0 end )  ,
sum(case when c3_ed is not null and c4_sd is null then 1 else 0 end ) ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )||'/'||sum(case when C4_Limit >0 then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  )||'/'||sum(case when C5_Limit >0 then 1 else 0 end  )
from T_PLAN_STATUS_RP_all
 where c_type='全新开通' and C1_Limit>0 ;
--------------------------------------------------------------------------------------
-----------'磁卡变更----------------------------------------------------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6,c7)
values( 5, '磁卡变更','' ,'总单' ,'呼出','计划确认' ,'实施', '资产配置' ) ;
--------
---------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6,c7)
select  6, '磁卡变更','无问题' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  ) ,
sum(case when c2_ed is not null and c3_sd is null then 1 else 0 end ) ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  ) ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )

from T_PLAN_STATUS_RP_all
 where c_type='磁卡变更' and C1_Limit<=0 and C2_Limit<=0 and C3_Limit<=0 and C4_Limit<=0 ;
--------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6,c7)
select  7, '磁卡变更','预 警' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  )||'/'||sum(case when C2_Limit >0 then 1 else 0 end)  ,
sum(case when c2_ed is not null and c3_sd is null then 1 else 0 end ) ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  )||'/'||sum(case when C3_Limit >0 then 1 else 0 end )  ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )||'/'||sum(case when C4_Limit >0 then 1 else 0 end  )
from T_PLAN_STATUS_RP_all
 where c_type='磁卡变更' and C1_Limit<=0 and （C2_Limit>0 or  C3_Limit>0 or  C4_Limit>0 );
-------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6,c7)
select  8, '磁卡变更','已超时' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  )||'/'||sum(case when C2_Limit >0 then 1 else 0 end)  ,
sum(case when c2_ed is not null and c3_sd is null then 1 else 0 end ) ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  )||'/'||sum(case when C3_Limit >0 then 1 else 0 end )  ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )||'/'||sum(case when C4_Limit >0 then 1 else 0 end  )
from T_PLAN_STATUS_RP_all
 where c_type='磁卡变更' and C1_Limit>0 ;


-----------------------------------------------------------------------------------------------------------------
---------------旧机翻新--------------------------------------------------------------------------------------------------

insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6,c7,c8,c9,c10)
values( 9, '旧机翻新','' ,'总单' , '押金' ,'呼出' ,'计划确认','翻新实施', '装机资产配置', '旧机回收实施', '旧机入库') ;
---------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8,c9,c10)
select  10, '旧机翻新','无问题' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  ) ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  ) ,
sum(case when c3_ed is not null and c4_sd is null then 1 else 0 end )  ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  ) ,
sum(case when C6_sd is not null and C6_ed is null then 1 else 0 end  ) ,
sum(case when C7_sd is not null and C7_ed is null then 1 else 0 end  )

from T_PLAN_STATUS_RP_all
 where c_type='旧机翻新' and C1_Limit<=0 and C2_Limit<=0 and C3_Limit<=0 and C4_Limit<=0 and C5_Limit<=0 and C6_Limit<=0 and C7_Limit<=0;
--------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8,c9,c10)
select  11, '旧机翻新','预 警' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  )||'/'||sum(case when C2_Limit >0 then 1 else 0 end)  ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  )||'/'||sum(case when C3_Limit >0 then 1 else 0 end )  ,
sum(case when c3_ed is not null and c4_sd is null then 1 else 0 end )  ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )||'/'||sum(case when C4_Limit >0 then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  )||'/'||sum(case when C5_Limit >0 then 1 else 0 end  ),
sum(case when C6_sd is not null and C6_ed is null then 1 else 0 end  )||'/'||sum(case when C6_Limit >0 then 1 else 0 end  ) ,
sum(case when C7_sd is not null and C7_ed is null then 1 else 0 end  )||'/'||sum(case when C7_Limit >0 then 1 else 0 end  )
from T_PLAN_STATUS_RP_all
 where c_type='旧机翻新' and C1_Limit<=0 and （C2_Limit>0 or  C3_Limit>0 or  C4_Limit>0 or C5_Limit>0 or  C6_Limit>0 or C7_Limit>0);
-------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8,c9,c10)
select  12, '旧机翻新','已超时' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  )||'/'||sum(case when C2_Limit >0 then 1 else 0 end)  ,
sum(case when C3_sd is not null and C3_ed is null then 1 else 0 end  )||'/'||sum(case when C3_Limit >0 then 1 else 0 end )  ,
sum(case when c3_ed is not null and c4_sd is null then 1 else 0 end )  ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )||'/'||sum(case when C4_Limit >0 then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  )||'/'||sum(case when C5_Limit >0 then 1 else 0 end  ),
sum(case when C6_sd is not null and C6_ed is null then 1 else 0 end  )||'/'||sum(case when C6_Limit >0 then 1 else 0 end  ) ,
sum(case when C7_sd is not null and C7_ed is null then 1 else 0 end  )||'/'||sum(case when C7_Limit >0 then 1 else 0 end  )
from T_PLAN_STATUS_RP_all
 where c_type='旧机翻新' and C1_Limit>0 ;

-----------------------------------------------------------------------------------------------------------------
-----------------旧机回收------------------------------------------------------------------------------------------------

insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6,c7,c8)
values( 13, '旧机回收','' ,'总单' ,'呼出','计划确认'  ,'实施', '旧机入库', '押金') ;
-------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8)
select  14, '旧机回收','无问题' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  ) ,
sum(case when C2_ed is not null and C3_sd is null then 1 else 0 end  ) ,
sum(case when c3_sd is not null and c3_ed is null then 1 else 0 end )  ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  )
from T_PLAN_STATUS_RP_all
 where c_type='旧机回收' and C1_Limit<=0 and C2_Limit<=0 and C3_Limit<=0 and C4_Limit<=0 and C5_Limit<=0;
--------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8)
select  15, '旧机回收','预 警' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  )||'/'||sum(case when C2_Limit >0 then 1 else 0 end)  ,
sum(case when C2_ed is not null and C3_sd is null then 1 else 0 end  ),
sum(case when c3_sd is not null and c3_ed is null then 1 else 0 end ) ||'/'||sum(case when C3_Limit >0 then 1 else 0 end )  ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )||'/'||sum(case when C4_Limit >0 then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  )||'/'||sum(case when C5_Limit >0 then 1 else 0 end  )
from T_PLAN_STATUS_RP_all
 where c_type='旧机回收' and C1_Limit<=0 and （C2_Limit>0 or  C3_Limit>0 or  C4_Limit>0 or C5_Limit>0);
-------------
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6, c7,c8)
select  16, '旧机回收','已超时' ,count(*),
sum(case when C2_sd is not null and C2_ed is null then 1 else 0 end  )||'/'||sum(case when C2_Limit >0 then 1 else 0 end)  ,
sum(case when C2_ed is not null and C3_sd is null then 1 else 0 end  ),
sum(case when c3_sd is not null and c3_ed is null then 1 else 0 end ) ||'/'||sum(case when C3_Limit >0 then 1 else 0 end )  ,
sum(case when C4_sd is not null and C4_ed is null then 1 else 0 end  )||'/'||sum(case when C4_Limit >0 then 1 else 0 end  ) ,
sum(case when C5_sd is not null and C5_ed is null then 1 else 0 end  )||'/'||sum(case when C5_Limit >0 then 1 else 0 end  )
from T_PLAN_STATUS_RP_all
 where c_type='旧机回收' and C1_Limit>0 ;

-----------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------

insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3, c4, c5, c6)
values( 17, '旧机关店','' ,'总单' ,'呼出' ,'实施', '旧机入库' ) ;



------------------------维护单
select c1 into v_c1 from t_plan_report_arg
where c_type='99' ;

--insert into T_PLAN_STATUS_COUNT
insert into T_PLAN_STATUS_ED1
(c_idx, c1, c2, c3)
select 30,'维护单'，'已超时' , count(*)
from TIT10_MAINTENANCEDAY
where CURRENT_STATUS='5' and sysdate - request_time > v_c1 ;
---------------------

/*
新建	1
分配	2
关闭	3
未解决	4
已解决	5
作废	9
*/

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
