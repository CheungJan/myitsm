procedure usp_create_contract_month
( as_date in char,  as_return out varchar2)

as

as_temp varchar2(4000);
v_date char(10);
v_days number;
v_lastday date ;
v_arg1 number ; --通信日低于 不算有效
v_arg2 number ; --维修耗时大于 不算有效硬件 3天
v_arg3 number ; --软件维修 3小时
begin
v_arg1:=15 ; --开机天数
v_arg2:=3 ; --硬件维修
v_arg3:=0.125 ;
v_lastday:=last_day(to_date(as_date,'yyyymm')) ;

delete from TEMP_CONTRACT_REPORT1 ;
delete from TEMP_CONTRACT_REPORT2 ;
delete from TEMP_CONTRACT_REPORT3 ;
delete from TEMP_CONTRACT_REPORT4 ;


select add_months(to_date(as_date, 'YYYYMM'),1)-to_date(as_date, 'YYYYMM') into v_days from dual;



delete from t_contract_month
where v_month=as_date ;

---------------抽取基础数据  tmm31  whtransflg='1'用于控制集团是否在报表体现
 insert into t_contract_month
(v_month, custcd, custnm, in_date, out_date, repair_times, repair_dates, remark, create_time, company_cd, company_nm,CUSTCARD)

select as_date,a.custcd,a.custnm,'','','','','',sysdate,b.classcd  ,b.classnm,a.custcard
from tmm22_customers a
left outer join TMM21_CUSTCLASS b
on a.classcd=b.classcd
where  a.busityp='YS' and b.whtransflg='1' ; --- 只针对延伸门店做收费统计 ;


-----------根据 TMM22_CONTRACT_C_LIST 确定具体 in_date  out_date
insert into TEMP_CONTRACT_REPORT1
select tmm22.custcd ,max(tmm22_c_c.c_date) from tmm22_customers tmm22
left outer join TMM22_CONTRACT_C_LISt tmm22_c_c
on tmm22.custcd =tmm22_c_c.custcd
and  tmm22_c_c.new_s='1' and tmm22_c_c.old_s='0' and to_char(c_date,'yyyymmdd')<=as_date
group by tmm22.custcd;


insert into TEMP_CONTRACT_REPORT2
select TEMP_CONTRACT_REPORT1.custcd ,min(tmm22_c_c.c_date) from TEMP_CONTRACT_REPORT1
left outer join TMM22_CONTRACT_C_LISt tmm22_c_c
on TEMP_CONTRACT_REPORT1.Custcd=tmm22_c_c.custcd
and  tmm22_c_c.new_s='0' and tmm22_c_c.old_s='1' and tmm22_c_c.c_date>=TEMP_CONTRACT_REPORT1.S_DATE
group by  TEMP_CONTRACT_REPORT1.custcd;

------在报表日期后退网的
update TEMP_CONTRACT_REPORT2
set edate = null
where to_char(edate,'yyyymm')>as_date ;



---------------------最近一次入网
update t_contract_month
set in_date=(select s_date from TEMP_CONTRACT_REPORT1 where TEMP_CONTRACT_REPORT1.custcd=t_contract_month.custcd)
where v_month=as_date ;
-----------------入网后最近一次退网
update t_contract_month
set out_date=(select edate from TEMP_CONTRACT_REPORT2 where TEMP_CONTRACT_REPORT2.custcd=t_contract_month.custcd)
where v_month=as_date ;

----------------删除考核日期前已退网的
delete from  t_contract_month
where to_char(out_date,'yyyymm')< as_date and v_month=as_date ;

delete from  t_contract_month
where in_date is null and v_month=as_date ;


--------------- 入网还没退
update t_contract_month
set  c_status='1'
where v_month=as_date  and out_date is null and c_status is null ;
---------------

update t_contract_month
set CONTRACT_DAYS =  round( out_date -  case when  in_date<to_date( as_date||'01','yyyymmdd') then  to_date(as_date||'01','yyyymmdd')else  in_date end )
where v_month=as_date  ;

update t_contract_month
set CONTRACT_DAYS =  v_days
where v_month=as_date and CONTRACT_DAYS is null   ;


update t_contract_month
set in_date=null
where v_month=as_date and to_char( in_date,'yyyymmdd')='20240201' ;
------------------------在网15天
update t_contract_month
set  c_status='1'
where v_month=as_date  and  CONTRACT_DAYS>=v_arg1;

update t_contract_month
set  c_status='0'
where v_month=as_date  and c_status is null;



---------------维修
insert into TEMP_CONTRACT_REPORT3
select  store_id,count(*),
 sum( round(a.close_time - case when  a.request_time is null then v_lastday else ( case when   a.request_time >  v_lastday then   v_lastday else   a.request_time  end ) end       ) ) ,
 max( round(a.close_time - case when  a.request_time is null then v_lastday else ( case when   a.request_time >  v_lastday then   v_lastday else   a.request_time  end ) end       ) )
   from tit10_maintenanceday a
where to_char(a.create_time,'yyyymm')=as_date  and a.fault_type='1' --- 只统计故障类型是pos的
group by store_id ;

update t_contract_month
set ( repair_times ,repair_dates,max_days ) =
( select repair_times ,repair_dates,max_days    from TEMP_CONTRACT_REPORT3
where TEMP_CONTRACT_REPORT3.CUSTCD=t_contract_month.custcd
  )
  where  v_month=as_date  ;
--------------------------------
insert into TEMP_CONTRACT_REPORT4
select  store_id , a.maintenance_id||'/'||a.store_id||'/'||'软件'||'/'||round((a.close_time - a.request_time)*24,1)  from tit10_maintenanceday a
where  to_char(a.create_time,'yyyymm')=as_date  and a.fault_type='1' and memo='02' and  a.close_time - a.request_time >=0.125
union all
select  store_id , a.maintenance_id||'/'||a.store_id||'/'||'硬件'||'/'||round((a.close_time - a.request_time)*24,1)  from tit10_maintenanceday a
where  to_char(a.create_time,'yyyymm')=as_date  and   a.fault_type='1' and memo='01' and  a.close_time - a.request_time >=3;



-----------------
update t_contract_month
set c_status='0'
where v_month=as_date and max_days>v_arg2 ;




update t_contract_month
set c_status='0',remark=(select  LISTAGG(remark, ', ') WITHIN GROUP (ORDER BY storecd) AS employees  from TEMP_CONTRACT_REPORT4
  where TEMP_CONTRACT_REPORT4.STORECD=t_contract_month.custcd
  group by storecd )
where v_month=as_date and exists (select * from TEMP_CONTRACT_REPORT4 where TEMP_CONTRACT_REPORT4.Storecd=t_contract_month.custcd );




------------------------------
commit;

as_return:='OK';


EXCEPTION
 when others then
    as_return:=as_return||sqlcode||sqlerrm;


    end ;
