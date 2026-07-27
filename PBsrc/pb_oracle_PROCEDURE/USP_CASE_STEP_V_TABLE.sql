procedure usp_case_step_v_table
( as_return out varchar2)

as

as_date date;

----
begin
select t.opendate into as_date from tmm01_company t;
------
/*
 insert into temp_case_step_v_table
 select
  "id" ,
  "org_id" ,
  "case_type_id" ,
  "itservice_config_id" ,
  "case_id",
 convert( "case_service_no" ,'zhs16gbk','utf8')  ,
  "customer_id",
  convert("customerName",'zhs16gbk','utf8') ,
  "area_id" ,
   convert("area_name" ,'zhs16gbk','utf8') ,
   "location_name",
  convert(  "location_cardcode",'zhs16gbk','utf8') ,
  "location_status" ,
   convert("location_status_name" ,'zhs16gbk','utf8') ,
  "location_type",
  convert( "location_type_name" ,'zhs16gbk','utf8') ,
  convert(  "location_address",'zhs16gbk','utf8') ,
 convert(  "location_phonenumber",'zhs16gbk','utf8') ,
 convert( "income2"  ,'zhs16gbk','utf8') ,
  "standardTime",
  "createdDate",
  "case_createddate",
  "case_requestdate",
  "buscatalog",
  convert("buscatalogName" ,'zhs16gbk','utf8') ,
  convert("isCheck" ,'zhs16gbk','utf8') ,
  convert( "tt_analysis" ,'zhs16gbk','utf8') ,
   convert("tt_workround" ,'zhs16gbk','utf8') ,
  convert(  "content",'zhs16gbk','utf8') ,
  convert( "result" ,'zhs16gbk','utf8') ,
  "comdate" ,
  "standard_completetime" ,
  "arrive_time" ,
  "leave_time" ,
  "time_cost" ,
  "quitduty" ,
  convert( "step_content" ,'zhs16gbk','utf8') ,
  convert( "quitdutyName" ,'zhs16gbk','utf8') ,
   convert("quitduty_term" ,'zhs16gbk','utf8') ,
  "quitduty_deptid" ,
  convert( "quitduty_dept",'zhs16gbk','utf8') ,
  "quitduty_type",
  convert( "change_upstandard_reason",'zhs16gbk','utf8') ,
  "action" ,
  convert( "actionName",'zhs16gbk','utf8') ,
  "is_on_site",
  "onsite_userid",
  convert( "onsite_engineer" ,'zhs16gbk','utf8') ,
  "onsite_result" ,
   convert("resultName" ,'zhs16gbk','utf8')
    from case_step_v_table@itsm
where "createdDate">=as_date ;
--convert(old_model,'zhs16gbk','utf8')
*/

select   "case_requestdate" into as_date from case_step_v_table@itsm ;
as_return:='case_step_v_table：  '||to_char(sql%rowcount)||' 条记录'||'       ';





EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
