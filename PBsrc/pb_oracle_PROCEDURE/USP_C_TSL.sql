procedure usp_c_tsl
(as_date  char ,as_return out varchar2)

as
v_date char(10);--'2012-01-01'
v_temp number;--

----开通单数据
begin

v_date:=as_date;

delete from tmp_TSL01_EXTEND;

delete from o_tf_in_location_open
where  sys_status=1;

delete from o_TF_IN_ASSET_RETREAD
where  sys_status=1;

delete from o_TF_IN_LOCATION_MOVE
where  sys_status=1;

delete from o_TF_IN_LOCATION_CLOSE
where  sys_status=1;

delete from o_TF_IN_LOCATION_CHANGE
where  sys_status=1;

delete from o_TF_IN_ASSET_CHANGE
where  sys_status=1;


insert into tmp_TSL01_EXTEND
select * from tsl01_extend a
where  a.auditflg='2';
 dbms_output.put_line(sql%rowcount);

--sltyp:      XZ：新装   GX:更新     BQ：搬迁 GB ：关闭 BG：设备变更  CK 磁卡变更

--门店新开 TF_IN_LOCATION_OPEN
insert into o_tf_in_location_open
( sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status ,checkflg,REQUEST_DATE)
   select  lpad(to_char(tf_seqid.nextval),10,0),a.opbillid,a.custcd,b.custcard,a.itemcd,
   b.planqty,decode(c.busityp,'ZS',1,'YS',2),to_number(c.area),to_number(c.location),c.phoneno,'',c.address,
   '','','','','',
   '',sysdate,'',1,'0',b.IMPDATE
   from tmp_TSL01_EXTEND  a
   inner join tsl02_extenddt b
   on a.opbillid=b.opbillid
   inner join tmm22_customers c
   on c.custcd=b.custcd

   where a.sltyp= 'XZ' and not exists (select * from o_tf_in_location_open
   where o_tf_in_location_open.plan_no=a.Opbillid  );




--旧机翻新 TF_IN_ASSET_RETREAD
insert into o_TF_IN_ASSET_RETREAD
( sm_no, plan_no, customer_code, cardcode, asset_model,
 asset_num, type, area, ring, phonenumber, mobile, address,
  next_plan_time, opersystem, data_base, soft_edition, ad_video,
   description, insert_time, syn_time, sys_status,checkflg,REQUEST_DATE )
   select  lpad(to_char(tf_seqid.nextval),10,0),a.opbillid,a.custcd,b.custcard,a.itemcd,
   b.planqty,decode(c.busityp,'ZS',1,'YS',2),to_number(c.area),to_number(c.location),c.phoneno,'',c.address,
   '','','','','',
   '',sysdate,'',1,'0',b.IMPDATE
   from tmp_TSL01_EXTEND  a
   inner join tsl02_extenddt b
   on a.opbillid=b.opbillid
   inner join tmm22_customers c
   on c.custcd=b.custcd

   where a.sltyp= 'GX' and not exists (select * from o_TF_IN_ASSET_RETREAD
   where o_TF_IN_ASSET_RETREAD.plan_no=a.Opbillid  );


--门店搬迁 TF_IN_LOCATION_MOVE

insert into o_TF_IN_LOCATION_MOVE
(sm_no, plan_no, customer_code, cardcode,
type, area, ring, phonenumber, mobile, old_address, address,
next_plan_time, opersystem, data_base, soft_edition,
 ad_video, description, insert_time, syn_time, sys_status,checkflg,REQUEST_DATE)
 select lpad(to_char(tf_seqid.nextval),10,0),a.opbillid,a.custcd,b.custcard,
   decode(c.busityp,'ZS',1,'YS',2),to_number(c.area),to_number(c.location),c.phoneno,'',c.address ,b.newaddress,
   '','','','',
   '','',sysdate,'',1,'0',b.IMPDATE
 from tmp_TSL01_EXTEND  a
  inner join tsl02_extenddt b
   on a.opbillid=b.opbillid
   inner join tmm22_customers c
   on c.custcd=b.custcd

   where a.sltyp= 'BQ' and not exists (select * from o_TF_IN_LOCATION_MOVE
   where o_TF_IN_LOCATION_MOVE.plan_no=a.Opbillid  );




--门店关闭 TF_IN_LOCATION_CLOSE
insert into o_tf_in_location_close
( sm_no, plan_no, customer_code, cardcode, insert_time, syn_time, sys_status,checkflg,REQUEST_DATE)
 select
 lpad(to_char(tf_seqid.nextval),10,0),a.opbillid,a.custcd,b.custcard,sysdate,'',1,'0',b.IMPDATE
 from
tmp_TSL01_EXTEND  a
  inner join tsl02_extenddt b
   on a.opbillid=b.opbillid
   inner join tmm22_customers c
   on c.custcd=b.custcd

   where a.sltyp= 'GB' and not exists (select * from o_tf_in_location_close
   where o_tf_in_location_close.plan_no=a.Opbillid  );


--磁卡变更 TF_IN_LOCATION_CHANGE
insert into o_TF_IN_LOCATION_CHANGE
( sm_no, plan_no, customer_code, old_cardcode, cardcode,
type, area, ring, phonenumber, mobile, address,
next_plan_time, opersystem, data_base, soft_edition, ad_video, description, insert_time, syn_time, sys_status,checkflg,REQUEST_DATE)
select lpad(to_char(tf_seqid.nextval),10,0),a.opbillid,a.custcd,b.custcard , b.newcustcard,
 decode(c.busityp,'ZS',1,'YS',2),to_number(c.area),to_number(c.location),c.phoneno,'',c.address,
 '','','','','','',sysdate,'',1,'0',b.IMPDATE
  from
tmp_TSL01_EXTEND  a
  inner join tsl02_extenddt b
   on a.opbillid=b.opbillid
   inner join tmm22_customers c
   on c.custcd=b.custcd


   where a.sltyp= 'CK' and not exists (select * from o_TF_IN_LOCATION_CHANGE
   where o_TF_IN_LOCATION_CHANGE.plan_no=a.Opbillid  );







--设备变更 TF_IN_ASSET_CHANGE

insert into o_tf_in_asset_change
(  sm_no, plan_no, close_cardcode, cardcode, name, serialno, model, cost,
 old_degree, enabled_date, repair_date, description, insert_time, syn_time, sys_status ,checkflg,REQUEST_DATE)
select lpad(to_char(tf_seqid.nextval),10,0),a.opbillid,b.custcard,b.newcustcard,e.itemnm,b.eid,d.itemcd,0,
3,'','','',sysdate,'',1,'0',b.IMPDATE
  from
tmp_TSL01_EXTEND  a
  inner join tsl02_extenddt b
   on a.opbillid=b.opbillid
   inner join tmm22_customers c
   on c.custcd=b.custcd
   inner join tmm43_eid  d
   on b.eid=d.eid
   inner join tmm12_items e
   on d.itemcd=e.itemcd

   where a.sltyp= 'BG' and not exists (select * from o_tf_in_asset_change
   where o_tf_in_asset_change.plan_no=a.Opbillid  );






-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;

