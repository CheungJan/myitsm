procedure usp_trans_out
(as_date  char ,as_return out varchar2)

as
v_date char(10);--'2012-01-01'


----发送数据


begin

v_date:=as_date;

----
----有限公司
--convert('字符串', 'UTF8', 'ZHS16GBK');
for c_1 in (select sm_no, customer_code, convert(name,'utf8','ZHS16GBK') name , fullname, phone, fax, website, address, linkman, insert_tim, syn_tiem, syn_status
from tf_in_customer
where  to_char(insert_tim,'yyyy-mm-dd')=v_date and checkflg='1')
loop
insert into tf_in_customer@itsm
( sm_no, customer_code, name, fullname, phone, fax, website, address, linkman, insert_time, syn_time, sys_status )
values( c_1.sm_no, c_1.customer_code,c_1.name, c_1.fullname, c_1.phone, c_1.fax, c_1.website,
c_1.address, c_1.linkman, c_1.insert_tim, c_1.syn_tiem, c_1.syn_status);


end loop;


/*insert into tf_in_customer@itsm
( sm_no, customer_code, name, fullname, phone, fax, website, address, linkman, insert_time, syn_time, sys_status )
select sm_no, customer_code, name, fullname, phone, fax, website, address, linkman, insert_tim, syn_tiem, syn_status
from tf_in_customer
where  to_char(insert_tim,'yyyy-mm-dd')=v_date and checkflg='1';
*/
--门店

for c_2 in (select sm_no, cardcode, name, status, type, area, ring,
phonenumber, mobile, customer_code,
 address, next_plan_time, opersystem, data_base, soft_edition, ad_video, insert_time, syn_time, sys_status, description

from tf_in_location
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop
insert into tf_in_location@itsm
(sm_no, cardcode, name, status, type, area, ring,
phonenumber, mobile, customer_code,
 address, next_plan_time, opersystem, data_base, soft_edition, ad_video, insert_time, syn_time, sys_status, DESCRIPTION )
values( c_2.sm_no, c_2.cardcode, c_2.name, c_2.status, c_2.type, c_2.area, c_2.ring,
c_2.phonenumber, c_2.mobile, c_2.customer_code,
 c_2.address, c_2.next_plan_time, c_2.opersystem, c_2.data_base, c_2.soft_edition, c_2.ad_video, c_2.insert_time, c_2.syn_time, c_2.sys_status, c_2.description );


end loop;
/*
insert into tf_in_location@itsm
(sm_no, cardcode, name, status, type, area, ring,
phonenumber, mobile, customer_code,
 address, next_plan_time, opersystem, data_base, soft_edition, ad_video, insert_time, syn_time, sys_status, DESCRIPTION )
select sm_no, cardcode, name, status, type, area, ring,
phonenumber, mobile, customer_code,
 address, next_plan_time, opersystem, data_base, soft_edition, ad_video, insert_time, syn_time, sys_status, description

from tf_in_location
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';*/

--资产表

for c_3 in (select  sm_no, serialno, name, model, cost, old_degree, enabled_date, repair_date, description, insert_time,
syn_time, sys_status
from tf_in_asset
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop
insert into tf_in_asset@itsm
( sm_no, serialno, name, model, cost, old_degree, enabled_date, repair_date, description, insert_time,
syn_time, sys_status)
values(  c_3.sm_no, c_3.serialno, c_3.name,c_3. model, c_3.cost, c_3.old_degree, c_3.enabled_date, c_3.repair_date, c_3.description, c_3.insert_time,
c_3.syn_time, c_3.sys_status);
end loop;



for c_4 in(select
 sm_no, asset_serialno, asset_model, name, part_serialno, part_model, old_degree,
enabled_date, repair_date, cost, deliverno, receiptno,
description, insert_time, syn_time, sys_status
from tf_in_part
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop

insert into tf_in_part@itsm
( sm_no, asset_serialno, asset_model, name, part_serialno, part_model, old_degree,
enabled_date, repair_date, cost, deliverno, receiptno,
description, insert_time, syn_time, sys_status)
values(
 c_4.sm_no, c_4.asset_serialno, c_4.asset_model, c_4.name, c_4.part_serialno, c_4.part_model, c_4.old_degree,
c_4.enabled_date, c_4.repair_date, c_4.cost, c_4.deliverno, c_4.receiptno,
c_4.description, c_4.insert_time, c_4.syn_time, c_4.sys_status);
end loop;

/*
insert into tf_in_asset@itsm
( sm_no, serialno, name, model, cost, old_degree, enabled_date, repair_date, description, insert_time,
syn_time, sys_status)
select  sm_no, serialno, name, model, cost, old_degree, enabled_date, repair_date, description, insert_time,
syn_time, sys_status
from tf_in_asset
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';


insert into tf_in_part@itsm
( sm_no, asset_serialno, asset_model, name, part_serialno, part_model, old_degree,
enabled_date, repair_date, cost, deliverno, receiptno,
description, insert_time, syn_time, sys_status)
select
 sm_no, asset_serialno, asset_model, name, part_serialno, part_model, old_degree,
enabled_date, repair_date, cost, deliverno, receiptno,
description, insert_time, syn_time, sys_status
from tf_in_part
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';
*/
--门店新开 TF_IN_LOCATION_OPEN

for c_5 in (select sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status

from tf_in_location_open
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop
insert into tf_in_location_open@itsm
( sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status )

   values( c_5.sm_no, c_5.plan_no, c_5.customer_code, c_5.cardcode, c_5.asset_model,
 c_5.asset_num, c_5.type, c_5.area, c_5.ring, c_5.phonenumber, c_5.mobile, c_5.address,
  c_5.next_plan_time, c_5.opersystem, c_5.data_base, c_5.soft_edition, c_5.ad_video,
   c_5.description, c_5.insert_time, c_5.syn_time, c_5.sys_status);
end loop;
/*insert into tf_in_location_open@itsm
( sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status )

   select sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status

from tf_in_location_open
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';*/
--旧机翻新 TF_IN_ASSET_RETREAD
for c_6 in ( select sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status
   from
   TF_IN_ASSET_RETREAD

   where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop

insert into TF_IN_ASSET_RETREAD@itsm
( sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status )
   values( c_6.sm_no, c_6.plan_no, c_6.customer_code, c_6.cardcode, c_6.asset_model,
 c_6.asset_num, c_6.type, c_6.area, c_6.ring, c_6.phonenumber, c_6.mobile, c_6.address,
  c_6.next_plan_time, c_6.opersystem, c_6.data_base, c_6.soft_edition, c_6.ad_video,
   c_6.description, c_6.insert_time, c_6.syn_time, c_6.sys_status);
end loop;
/*insert into TF_IN_ASSET_RETREAD@itsm
( sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status )
   select sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status
   from
   TF_IN_ASSET_RETREAD

   where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';*/
--门店搬迁 TF_IN_LOCATION_MOVE
for c_7 in(select sm_no, plan_no, customer_code, cardcode,
type, area, ring, phonenumber, mobile, old_address, address,
next_plan_time, opersystem, data_base, soft_edition,
 ad_video, description, insert_time, syn_time, sys_status
 from TF_IN_LOCATION_MOVE

 where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop
insert into TF_IN_LOCATION_MOVE@itsm
(sm_no, plan_no, customer_code, cardcode,
type, area, ring, phonenumber, mobile, old_address, address,
next_plan_time, opersystem, data_base, soft_edition,
 ad_video, description, insert_time, syn_time, sys_status)
 values( c_7.sm_no, c_7.plan_no, c_7.customer_code, c_7.cardcode,
c_7.type, c_7.area, c_7.ring, c_7.phonenumber, c_7.mobile, c_7.old_address, c_7.address,
c_7.next_plan_time, c_7.opersystem, c_7.data_base, c_7.soft_edition,
 c_7.ad_video, c_7.description, c_7.insert_time, c_7.syn_time, c_7.sys_status);
end loop;
/*insert into TF_IN_LOCATION_MOVE@itsm
(sm_no, plan_no, customer_code, cardcode,
type, area, ring, phonenumber, mobile, old_address, address,
next_plan_time, opersystem, data_base, soft_edition,
 ad_video, description, insert_time, syn_time, sys_status)
 select sm_no, plan_no, customer_code, cardcode,
type, area, ring, phonenumber, mobile, old_address, address,
next_plan_time, opersystem, data_base, soft_edition,
 ad_video, description, insert_time, syn_time, sys_status
 from TF_IN_LOCATION_MOVE

 where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';*/

--门店关闭 TF_IN_LOCATION_CLOSE
for c_9 in(select sm_no, plan_no, customer_code, cardcode, insert_time, syn_time, sys_status

from tf_in_location_close
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop
insert into tf_in_location_close@itsm
( sm_no, plan_no, customer_code, cardcode, insert_time, syn_time, sys_status)
values( c_9.sm_no, c_9.plan_no, c_9.customer_code, c_9.cardcode, c_9.insert_time, c_9.syn_time, c_9.sys_status);
end loop;
/*insert into tf_in_location_close@itsm
( sm_no, plan_no, customer_code, cardcode, insert_time, syn_time, sys_status)
select sm_no, plan_no, customer_code, cardcode, insert_time, syn_time, sys_status

from tf_in_location_close
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';*/

--磁卡变更 TF_IN_LOCATION_CHANGE
for c_10 in(select  sm_no, plan_no, customer_code, old_cardcode, cardcode,
type, area, ring, phonenumber, mobile, address,
next_plan_time, opersystem, data_base, soft_edition, ad_video, description, insert_time, syn_time, sys_status
from TF_IN_LOCATION_CHANGE
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop
insert into TF_IN_LOCATION_CHANGE@itsm
( sm_no, plan_no, customer_code, old_cardcode, cardcode,
type, area, ring, phonenumber, mobile, address,
next_plan_time, opersystem, data_base, soft_edition, ad_video, description, insert_time, syn_time, sys_status)

values(  c_10.sm_no,  c_10.plan_no,  c_10.customer_code,  c_10.old_cardcode,  c_10.cardcode,
 c_10.type,  c_10.area,  c_10.ring,  c_10.phonenumber,  c_10.mobile,  c_10.address,
 c_10.next_plan_time,  c_10.opersystem,  c_10.data_base,  c_10.soft_edition,  c_10.ad_video,  c_10.description,  c_10.insert_time,  c_10.syn_time,  c_10.sys_status);

end loop;
/*insert into TF_IN_LOCATION_CHANGE@itsm
( sm_no, plan_no, customer_code, old_cardcode, cardcode,
type, area, ring, phonenumber, mobile, address,
next_plan_time, opersystem, data_base, soft_edition, ad_video, description, insert_time, syn_time, sys_status)

select  sm_no, plan_no, customer_code, old_cardcode, cardcode,
type, area, ring, phonenumber, mobile, address,
next_plan_time, opersystem, data_base, soft_edition, ad_video, description, insert_time, syn_time, sys_status
from TF_IN_LOCATION_CHANGE
where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';*/
--设备变更 TF_IN_ASSET_CHANGE
for c_11 in(select
 sm_no, plan_no, close_cardcode, cardcode, name, serialno, model, cost,
 old_degree, enabled_date, repair_date, description, insert_time, syn_time, sys_status
 from tf_in_asset_change
 where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1')
loop
insert into tf_in_asset_change@itsm
(  sm_no, plan_no, close_cardcode, cardcode, name, serialno, model, cost,
 old_degree, enabled_date, repair_date, description, insert_time, syn_time, sys_status )
 values
 (c_11.sm_no, c_11.plan_no, c_11.close_cardcode, c_11.cardcode, c_11.name, c_11.serialno, c_11.model, c_11.cost,
 c_11.old_degree, c_11.enabled_date, c_11.repair_date, c_11.description, c_11.insert_time, c_11.syn_time, c_11.sys_status);
end loop;
/*insert into tf_in_asset_change@itsm
(  sm_no, plan_no, close_cardcode, cardcode, name, serialno, model, cost,
 old_degree, enabled_date, repair_date, description, insert_time, syn_time, sys_status )
 select
 sm_no, plan_no, close_cardcode, cardcode, name, serialno, model, cost,
 old_degree, enabled_date, repair_date, description, insert_time, syn_time, sys_status
 from tf_in_asset_change
 where  to_char(insert_time,'yyyy-mm-dd')=v_date and checkflg='1';
*/

-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
