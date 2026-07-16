procedure usp_create_itsm_report
( as_date in char,  as_return out varchar2)

as

as_temp varchar2(4000);
v_date char(10);

begin
v_date:=as_date;

delete from temp_itsm_report;
delete from temp_itsm_report_step;
insert into  temp_itsm_report
( custcard, SERVICE_ID, create_date, service_group, service_no,
case_createdate, left_date, arr_date, complete_date,
result_status, oper, seriver_type, location_type,
 remark1, remark2, cust_nm, location_nm, content, result,work_log )

 select location_cardcode,no,createddate,'','',
 '','','','',
 '',engineer,'','',
content,result,customername,requester,'','',''

 from case_item_v_table
 where to_char(createddate,'yyyy-mm-dd')>=v_date --and no='IN13065890'
 and not exists (select * from itsm_report where itsm_report.SERVICE_ID =case_item_v_table.no) ;


for c_1 in (select service_id  from temp_itsm_report order by create_date)
loop
-----------------------------------------------------

             insert into  temp_itsm_report_step
            ( custcard, SERVICE_ID, create_date, service_group, service_no,
            case_createdate, left_date, arr_date, complete_date,
            result_status, oper, seriver_type, location_type,
             remark1, remark2, cust_nm, location_nm, content, result )

             select location_cardcode,case_service_no,case_createddate,'',rownum,
             createddate,leave_time,arrive_time,standard_completetime,
             resultname,onsite_engineer,
             decode(case_step_v_table.itservice_config_id,4830,'视频',5116,'保养',4804,'维护',5117,'开通',
             5118,'开通',5119,'开通',5120,'开通',5121,'开通',5122,'开通',5123,'开通','error'),
             decode(location_type,1,'直属',2,'延伸',3,'捷强',4,'捷强'),
            '','',customername,location_name,step_content,''

             from case_step_v_table
             where to_char(createddate,'yyyy-mm-dd')>=v_date and case_service_no=c_1.service_id
             and not exists (select * from itsm_report_step where itsm_report_step.SERVICE_ID =case_step_v_table.case_service_no)    ;
-----------------------------------------------------------------------------------------------------------------------------------

           insert into  temp_itsm_report_step
            ( custcard, SERVICE_ID, create_date, service_group, service_no,
            case_createdate, left_date, arr_date, complete_date,
            result_status, oper, seriver_type, location_type,
             remark1, remark2, cust_nm, location_nm, content, result )

             select location_cardcode,case_service_no,createddate,'',rownum,
             createddate,'','','',
             '',engineer,
             '开通',
            decode(location_type,1,'直属',2,'延伸',3,'捷强',4,'捷强'),
            '','',customername,location_name,'',''

             from asset_change_v_table
             where to_char(createddate,'yyyy-mm-dd')>=v_date and case_service_no=c_1.service_id
             and not exists (select * from itsm_report_step where itsm_report_step.SERVICE_ID =asset_change_v_table.case_service_no);


-----------------------------------------------------
   for c_2 in (
   select case_id  from (select distinct case_id  from case_step_v_table
   where  case_step_v_table.case_service_no=c_1.service_id
   union all
   select distinct case_id  from   asset_change_v_table
   where  asset_change_v_table.case_service_no=c_1.service_id )  order by case_id  )
       loop

           for c_3 in (select content ,op_date,op_id,onsite_engineer,arrive_time,leave_time from data_case_step where
           case_id =c_2.case_id order by id )
               loop
                  as_temp:=as_temp||'操作员：'||c_3.op_id ||'操作时间：'||to_char(c_3.op_date,'yyyy-mm-dd hh24:mi:ss') || chr(13)||chr(10)||
                    c_3.content||chr(13)||chr(10)||
                    nvl('工程师：'   ||c_3.onsite_engineer,' ' )||
                    nvl('到达时间：' ||to_char(c_3.arrive_time,'yyyy-mm-dd hh24:mi:ss'),' ')  ||
                    nvl('离开时间：' ||to_char(c_3.leave_time,'yyyy-mm-dd hh24:mi:ss'),' ')  ||   chr(13)||chr(10);

               end loop;




       end loop;

           update temp_itsm_report
           set work_log=as_temp
           where service_id=c_1.service_id;

              as_temp:='';
              as_return:=c_1.service_id;
end loop;


insert into itsm_report
select * from temp_itsm_report;

---------------------------------------------------------------------------------
/*
insert into  temp_itsm_report_step
( custcard, SERVICE_ID, create_date, service_group, service_no,
case_createdate, left_date, arr_date, complete_date,
result_status, oper, seriver_type, location_type,
 remark1, remark2, cust_nm, location_nm, content, result )

 select location_cardcode,no,createddate,'','',
 '','','','',
 '',engineer,'','',
content,result,customername,requester,'',''

 from case_item_v_table
 where to_char(createddate,'yyyy-mm-dd')>=v_date --and no='IN13065890'
 and not exists (select * from itsm_report where itsm_report.SERVICE_ID =case_item_v_table.no) ;

updte temp_itsm_report_step
set temp_itsm_report_step.service_group='',temp_itsm_report_step.seriver_type='',
temp_itsm_report_step.remark1='',temp_itsm_report_step.remark2=''
*/
update temp_itsm_report_step
set temp_itsm_report_step.service_group='捷强服务组一线'
where SERIVER_TYPE='维护' and LOCATION_TYPE='捷强';

update temp_itsm_report_step
set temp_itsm_report_step.service_group='零售业务POS服务组一线'
where SERIVER_TYPE='维护' and LOCATION_TYPE<>'捷强';

update temp_itsm_report_step
set temp_itsm_report_step.service_group='零售业务POS实施组'
where SERIVER_TYPE='开通' and LOCATION_TYPE<>'捷强';

update temp_itsm_report_step
set temp_itsm_report_step.service_group='设备保养组'
where SERIVER_TYPE='保养' ;

/*
updte temp_itsm_report_step
set temp_itsm_report_step.service_group='话务组'
where SERIVER_TYPE='保养' ;
*/
update temp_itsm_report_step
set temp_itsm_report_step.service_group='捷强实施组'
where SERIVER_TYPE='开通' and LOCATION_TYPE='捷强';

update temp_itsm_report_step
set temp_itsm_report_step.service_group='视频业务组'
where SERIVER_TYPE='视频' ;



insert into itsm_report_step
select * from temp_itsm_report_step;

as_return:='OK';


EXCEPTION
 when others then
    as_return:=as_return||sqlcode||sqlerrm;


    end ;
