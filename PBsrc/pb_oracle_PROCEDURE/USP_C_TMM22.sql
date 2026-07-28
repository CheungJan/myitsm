procedure usp_c_tmm22
(as_return out varchar2)

as


begin

delete from o_tf_in_customer
where sys_status=1;

delete from o_tf_in_location
where sys_status=1;


----有限公司
insert into o_tf_in_customer
( sm_no, customer_code, name, fullname, phone, fax, website, address, linkman, insert_time, syn_time, sys_status,checkflg )
select lpad(to_char(tf_seqid.nextval),10,0),custcd,custanm,custnm,phoneno,faxno,'',address,contactor,sysdate,'',1,'0'
from tmm22_customers
where busityp='YX' and sttransflg='0' ;

--门店
--useflg门店状态 1：正常 2：临时关闭 3：关闭 4：未开通
--busityp 门店类型 1：烟草直属门店2：延伸加盟门店 3：捷强直属门店 4：捷强加盟门店
--ring区域所在位置 1：内环 2：中环 3：外环
--门店状态 1：正常 2：临时关闭 3：关闭 4：未开通
insert into o_tf_in_location
(sm_no, cardcode, name, status, type, area, ring,
phonenumber, mobile, customer_code,
 address, next_plan_time, opersystem, data_base, soft_edition, ad_video, insert_time, syn_time, sys_status, description ,checkflg)
 select lpad(to_char(tf_seqid.nextval),10,0),a.custcard,a.custnm,decode ( a.useflg,'0',3,'1', to_number(a.s_status)),
 decode(a.busityp,'ZS',1,'YS',2),to_number(a.area),nvl(to_number(a.location),3),
 a.phoneno,'',b.custcd,a.address,'',a.opersystem,a.data_base,a.soft_edition,
 '',sysdate,'',1,'','0'
 from tmm22_customers a
 inner join (select custcd,classcd from tmm22_customers where busityp='YX' ) b
 on a.classcd=b.classcd
where a.busityp<>'YX' and  a.classcd<>'08'   and sttransflg='0';

--捷强
insert into o_tf_in_location
(sm_no, cardcode, name, status, type, area, ring,
phonenumber, mobile, customer_code,
 address, next_plan_time, opersystem, data_base, soft_edition, ad_video, insert_time, syn_time, sys_status, description ,checkflg)
 select lpad(to_char(tf_seqid.nextval),10,0),a.custcard,a.custnm,decode ( a.useflg,'0',3,'1', to_number(a.s_status)),
 decode(a.busityp,'ZS',3,'YS',4),to_number(a.area),nvl(to_number(a.location),3),
 a.phoneno,'',b.custcd,a.address,'',a.opersystem,a.data_base,a.soft_edition,
 '',sysdate,'',1,'','0'
 from tmm22_customers a
 inner join (select custcd,classcd from tmm22_customers where busityp='YX' ) b
 on a.classcd=b.classcd
where a.busityp<>'YX' and  a.classcd='08'   and sttransflg='0';



-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;

