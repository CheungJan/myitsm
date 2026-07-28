procedure usp_trans_out_new
(as_date  char ,as_return out varchar2)

as
v_date char(10);--'2012-01-01'


----发送数据


begin

v_date:=as_date;

----
----有限公司



insert into itsm_trans.tf_in_customer
( sm_no, customer_code, name, fullname, phone, fax, website, address, linkman, insert_time, syn_time, sys_status )
select sm_no, customer_code, name, fullname, phone, fax, website, address, linkman, insert_time, syn_time, sys_status
from o_tf_in_customer
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;

update tmm22_customers
set sttransflg='1'
where sttransflg='0' and custcd in (select  customer_code
from o_tf_in_customer
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1);


update o_tf_in_customer
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1 ;





--门店



insert into itsm_trans.tf_in_location
(sm_no, cardcode, name, status, type, area, ring,
phonenumber, mobile, customer_code,
 address, next_plan_time, opersystem, data_base, soft_edition, ad_video, insert_time, syn_time, sys_status, DESCRIPTION )
select sm_no, cardcode, name, status, type, area, ring,
phonenumber, mobile, customer_code,
 address, next_plan_time, opersystem, data_base, soft_edition, ad_video, insert_time, syn_time, sys_status, description

from o_tf_in_location
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;


update tmm22_customers
set sttransflg='1'
where sttransflg='0' and custcard in (select  custcard
from o_tf_in_location
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1);




update o_tf_in_location
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1'and  sys_status=1 ;

--资产表



insert into itsm_trans.tf_in_asset
( sm_no, serialno, name, model, cost, old_degree, enabled_date, repair_date, description, insert_time,
syn_time, sys_status ,cardcode)
select  sm_no, serialno, name, model, cost, old_degree, enabled_date, repair_date, description, insert_time,
syn_time, sys_status,cardcode
from o_tf_in_asset
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;

----改写状态不在生成tmm43
update sm_in_open_result
set sys_status=3
where exists(select *from o_tf_in_asset
where to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1 and
sm_in_open_result.id=o_tf_in_asset.id);

----改写发送标记
update o_tf_in_asset
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1 ;


insert into itsm_trans.tf_in_part
( sm_no, asset_serialno, asset_model, name, part_serialno, part_model, old_degree,
enabled_date, repair_date, cost, deliverno, receiptno,
description, insert_time, syn_time, sys_status)
select
 sm_no, asset_serialno, asset_model, name, part_serialno, part_model, old_degree,
enabled_date, repair_date, cost, deliverno, receiptno,
description, insert_time, syn_time, sys_status
from o_tf_in_part
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;


update o_tf_in_part
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1'and  sys_status=1 ;




--门店新开 TF_IN_LOCATION_OPEN


insert into itsm_trans.tf_in_location_open
( sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status,REQUEST_DATE  )

   select sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status,REQUEST_DATE

from o_tf_in_location_open
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;

update o_tf_in_location_open
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1'and  sys_status=1 ;


--旧机翻新 TF_IN_ASSET_RETREAD

insert into itsm_trans.TF_IN_ASSET_RETREAD
( sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status ,REQUEST_DATE )
   select sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status,REQUEST_DATE
   from
   o_TF_IN_ASSET_RETREAD

   where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;

   update o_TF_IN_ASSET_RETREAD
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1'and  sys_status=1 ;
--门店搬迁 TF_IN_LOCATION_MOVE

insert into itsm_trans.TF_IN_LOCATION_MOVE
(sm_no, plan_no, customer_code, cardcode,
type, area, ring, phonenumber, mobile, old_address, address,
next_plan_time, opersystem, data_base, soft_edition,
 ad_video, description, insert_time, syn_time, sys_status,REQUEST_DATE )
 select sm_no, plan_no, customer_code, cardcode,
type, area, ring, phonenumber, mobile, old_address, address,
next_plan_time, opersystem, data_base, soft_edition,
 ad_video, description, insert_time, syn_time, sys_status,REQUEST_DATE
 from o_TF_IN_LOCATION_MOVE

 where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;


    update o_TF_IN_LOCATION_MOVE
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1'and  sys_status=1 ;

--门店关闭 TF_IN_LOCATION_CLOSE

insert into itsm_trans.tf_in_location_close
( sm_no, plan_no, customer_code, cardcode, insert_time, syn_time, sys_status,REQUEST_DATE )
select sm_no, plan_no, customer_code, cardcode, insert_time, syn_time, sys_status, REQUEST_DATE

from o_tf_in_location_close
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;


    update o_tf_in_location_close
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1'and  sys_status=1 ;

--磁卡变更 TF_IN_LOCATION_CHANGE

insert into itsm_trans.TF_IN_LOCATION_CHANGE
( sm_no, plan_no, customer_code, old_cardcode, cardcode,
type, area, ring, phonenumber, mobile, address,
next_plan_time, opersystem, data_base, soft_edition, ad_video, description, insert_time, syn_time, sys_status,REQUEST_DATE )

select  sm_no, plan_no, customer_code, old_cardcode, cardcode,
type, area, ring, phonenumber, mobile, address,
next_plan_time, opersystem, data_base, soft_edition, ad_video, description, insert_time, syn_time, sys_status,REQUEST_DATE
from o_TF_IN_LOCATION_CHANGE
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;

    update o_TF_IN_LOCATION_CHANGE
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1'and  sys_status=1 ;
--设备变更 TF_IN_ASSET_CHANGE

insert into itsm_trans.tf_in_asset_change
(  sm_no, plan_no, close_cardcode, cardcode, name, serialno, model, cost,
 old_degree, enabled_date, repair_date, description, insert_time, syn_time, sys_status,REQUEST_DATE  )
 select
 sm_no, plan_no, close_cardcode, cardcode, name, serialno, model, cost,
 old_degree, enabled_date, repair_date, description, insert_time, syn_time, sys_status,REQUEST_DATE
 from o_tf_in_asset_change
 where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1' and  sys_status=1;

     update o_tf_in_asset_change
set sys_status=2
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1'and  sys_status=1 ;


-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
