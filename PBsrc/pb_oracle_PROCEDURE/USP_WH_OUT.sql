procedure usp_wh_out
(as_typ char ,as_id char,as_user char ,as_return out varchar2)
as
v_typ char(1);--出入库操作类型
v_id  char(8);--单据号
v_user char(6);
-- v_tempid char(8);
v_optyp char(1);--具体是批次 =0  还是id=1
v_whcd  char(2);--仓库代码
-- v_refbillid    char(8); --对应单据
v_inbillid     char(8); --调拨对应入库单
--v_return  varchar(255);--返回值

begin

v_typ:=as_typ;
v_id:=as_id;
v_user:=as_user;

delete from tmp_wh_stock;
---------invtyp  1:退货出库 2:质检出库3: 维护出库 4:生产出库 5：返修出库6：外借出库 7：调拨出库 8:销售出库 9 领用出库 s销售出库
--invtyp  1:退货出库
if v_typ='1' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0) - a.outqty,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp ,whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中  8 在库 9 出库
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='4'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
end if ;








---------invtyp 2:质检出库
---------质检出库
if v_typ='2' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0) - a.outqty,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0) - a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中  8 在库 9 出库
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='6'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
end if ;


---------维护出库

if v_typ='3' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



                -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中  8 在库 9 出库
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='9'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );


   end if ;
end if ;
-------------------------------------------生产出库
if v_typ='4' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno, iotyp,whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='7'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
end if ;

-------------------------------------------返修出库6：外借出库 7：调拨出库 8:销售出库 9 领用出库
if v_typ='5' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty ,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno, iotyp,whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
             -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中  8 在库 9 出库
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='9'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
end if ;


-------------------------------------------外借出库
if v_typ='6' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='9'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
end if ;
-------------------------------------------7：调拨出库
if v_typ='7' then

   select decode(optyp ,'PC','0','ID','1','err'),TARGETWHCD into v_optyp,v_whcd from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='9'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
   -------------同时作调拨入库
    v_inbillid := uf_get_billnou('IN')  ;


          insert into twh13_in
          ( whcd,indate, inbillid, refbillid,invtyp, ptimes, memo, opercd, gendate, auditflg, auditman, auditdate,
           optyp, useflg, suppcd )

       /*    2026
           select targetwhcd,sysdate, v_inbillid,outbillid,'7','0','','SYS',sysdate,'','','',
           '1','1',''*/
           select targetwhcd,sysdate, v_inbillid,outbillid,'7','0','','SYS',sysdate,'','','', '1','0',''
           from twh15_out
           where outbillid=v_id ;



           insert into twh14_checkindt
           ( whcd, inbillid, lineno, itemtyp, itemcd,
           prddate, inqty  )
           select whcd,inbillid,rownum,itemtyp,itemcd,prddate,inqty
           from (
           select v_whcd whcd,v_inbillid inbillid ,a.itemtyp itemtyp,
           itemcd itemcd,prddate prddate,count(*) inqty
           from twh16_outdteid  a
           where a.outbillid=v_id
           group by v_whcd,v_inbillid ,a.itemtyp,itemcd,prddate
           ) ;

           -- 【2026 新增2】批次模式明细插入（解决批次模式明细丢失问题）
           insert into twh14_checkindt
           ( whcd, inbillid, lineno, itemtyp, itemcd, prddate, inqty )
           select v_whcd, v_inbillid,
               ROW_NUMBER() OVER (ORDER BY itemcd, prddate),
               itemtyp, itemcd, prddate, outqty
           from twh16_outdtprd
           where outbillid=v_id
           and not exists (
               select 1 from twh16_outdteid b where b.outbillid=v_id
           );

   /*      --  2026
           usp_wh_in('7',v_inbillid,'SYS',as_return );

            update tmm43_eid
            set (sflg,refid,whcd,gendate,itemtyp)=(select '8', v_inbillid,v_whcd ,sysdate ,a.itemtyp from twh16_outdteid a
            where  tmm43_eid.eid=a.eid  and a.outbillid=v_id)
            where  exists (select * from  twh16_outdteid
            where tmm43_eid.eid=twh16_outdteid.eid and twh16_outdteid.outbillid=v_id ) ;
   */
end if ;

-------------------------------------------8:销售出库
if v_typ='8' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno, iotyp,whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0) - a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='S'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
end if ;
-------------------------------------------9 领用出库
if v_typ='9' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0)- a.outqty,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='9'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
end if ;

-------------------------------------------9 领用出库
/*if v_typ='1' then

   select decode(optyp ,'PC','0','ID','1','err') into v_optyp from twh15_out where outbillid=as_id;


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select outqty from twh16_outdtprd  where  twh11_detail.itemcd=twh16_outdtprd.itemcd and
                 twh11_detail.prddate=twh16_outdtprd.prddate and twh16_outdtprd.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  )
                 where exists
             (select * from twh16_outdtprd  where twh16_outdtprd.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdtprd.itemcd and   twh11_detail.prddate=twh16_outdtprd.prddate and
             twh11_detail.whcd=twh16_outdtprd.whcd  and   twh11_detail.itemtyp=twh16_outdtprd.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0),v_user,sysdate,'0'
             from twh16_outdtprd  a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(outqty) from twh16_outdteid  where  twh11_detail.itemcd=twh16_outdteid.itemcd and
                 twh11_detail.prddate=twh16_outdteid.prddate and twh16_outdteid.outbillid=v_id and
                 twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp
                  )
                 where exists
             (select * from twh16_outdteid  where twh16_outdteid.outbillid=v_id
             and twh11_detail.itemcd=twh16_outdteid.itemcd and   twh11_detail.prddate=twh16_outdteid.prddate and
             twh11_detail.whcd=twh16_outdteid.whcd  and   twh11_detail.itemtyp=twh16_outdteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,a.whcd,a.itemtyp,a.itemcd,a.prddate,a.outbillid,b.outdate,b.invtyp,a.outqty,nvl(c.stock,0),v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,outbillid ,sum(outqty) outqty from   twh16_outdteid
             where outbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,outbillid ) a
             inner join twh15_out  b
             on a.outbillid=b.outbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.outbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='4'
            where exists (select * from twh16_outdteid  where twh16_outdteid.eid=tmm43_eid.eid
            and  twh16_outdteid.outbillid=v_id );




   end if ;
end if ;
*/
-------------------------
as_return:='OK';
-------------------

EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;








end ;

