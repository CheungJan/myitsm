procedure usp_case_item_v_table
( as_return out varchar2)

as

as_date date;

----
begin
select t.opendate into as_date from tmm01_company t;
------

insert into temp_case_item_v_table
 select
  "id" ,
  "org_id" ,
  "type_id" ,
  convert("type",'zhs16gbk','utf8') ,
  convert("no",'zhs16gbk','utf8') ,
  "cfg_id" ,
  convert("cfg",'zhs16gbk','utf8') ,
  "case_catalog_id",
  convert("catalog",'zhs16gbk','utf8') ,
  "area_id" ,
   convert("area_name",'zhs16gbk','utf8') ,
  "location_id" ,
  convert("location_name",'zhs16gbk','utf8') ,
  "location_type" ,
   convert("location_type_name",'zhs16gbk','utf8') ,
   convert("location_cardcode",'zhs16gbk','utf8') ,
  "location_status" ,
  convert("location_status_name",'zhs16gbk','utf8') ,
  convert("location_address",'zhs16gbk','utf8') ,
  convert("location_phonenumber",'zhs16gbk','utf8') ,
  "customer_id" ,
   convert("customerName",'zhs16gbk','utf8') ,
  "requester_id" ,
   convert("requester",'zhs16gbk','utf8') ,
  convert("dept" ,'zhs16gbk','utf8') ,
   convert("contact",'zhs16gbk','utf8') ,
  convert("address",'zhs16gbk','utf8') ,
  "reqdate" ,
  "status_id",
  convert("status",'zhs16gbk','utf8') ,
   convert("substatus",'zhs16gbk','utf8') ,
  convert("title",'zhs16gbk','utf8') ,
  convert("content",'zhs16gbk','utf8') ,
  convert("result",'zhs16gbk','utf8') ,
  convert("remark" ,'zhs16gbk','utf8') ,
  convert("code",'zhs16gbk','utf8') ,
  convert("incident_code",'zhs16gbk','utf8') ,
  "comdate",
  "createddate" ,
  "standard_completetime" ,
  "buscatalog" ,
  convert("isCheck" ,'zhs16gbk','utf8') ,
  "satisfaction" ,
   convert("satisfactionName",'zhs16gbk','utf8') ,
  convert("timecost",'zhs16gbk','utf8') ,
  "step_id" ,
  "engineer_id" ,
   convert("engineer",'zhs16gbk','utf8') ,
  "action" ,
   convert("actionName",'zhs16gbk','utf8') ,
  "on_site_result" ,
  convert("on_site_result_name" ,'zhs16gbk','utf8') ,
  "on_site_arriveTime" ,
  "on_site_number" ,
  "on_site_leaveTime" ,
  "upStandard",
  convert( "upStandard_label",'zhs16gbk','utf8') ,
  "change_upstandard",
 convert( "change_upstandard_label",'zhs16gbk','utf8') ,
  convert("quitduty_term" ,'zhs16gbk','utf8') ,
  "quitduty_deptid" ,
  convert("change_upstandard_reason" ,'zhs16gbk','utf8') ,
  convert( "quitduty_dept",'zhs16gbk','utf8') ,
  "created_id" ,
  convert("creater" ,'zhs16gbk','utf8') ,
  convert( "buscatalogName",'zhs16gbk','utf8') ,
  "asset_id" ,
   convert("asset_name",'zhs16gbk','utf8') ,
  "asset_enabled_date",
  "close_code" ,
  "changed_beforepart",
   convert("changed_beforepart_name",'zhs16gbk','utf8') ,
  convert("changed_beforepart_model",'zhs16gbk','utf8') ,
  "changed_afterpart" ,
  convert( "changed_afterpart_name",'zhs16gbk','utf8') ,
 convert( "changed_afterpart_model",'zhs16gbk','utf8') ,
  "expect_completetime"

    from case_item_v_table@itsm

where "createddate">=as_date ;
--convert(old_model,'zhs16gbk','utf8')

as_return:='case_item_v_table：  '||to_char(sql%rowcount)||' 条记录'||'       ';



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
