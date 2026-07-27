procedure usp_overlost_audit
(as_id varchar2 ,as_return out varchar2)
as

v_id  varchar2(8);--损益单号
v_optyp char(1);--批次、id
v_sign char(1); --0损 1溢
v_user  varchar2(10);
v_whcd  char(2);


begin
v_id:=as_id;

-----损
 select decode(optyp ,'PC','0','ID','1','err'),olsign ,whcd into v_optyp ,v_sign , v_whcd from twh17_overlost where olbillid=as_id;

--twh18_overlostdt
--twh18_overlosteid
if v_sign='0' then --


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh18_overlostdt  where twh18_overlostdt.olbillid=v_id
             and twh11_detail.itemcd=twh18_overlostdt.itemcd and   twh11_detail.prddate=twh18_overlostdt.prddate and
             twh11_detail.whcd=twh18_overlostdt.whcd  and   twh11_detail.itemtyp=twh18_overlostdt.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select olqty from twh18_overlostdt  where  twh11_detail.itemcd=twh18_overlostdt.itemcd and
                 twh11_detail.prddate=twh18_overlostdt.prddate and twh18_overlostdt.olbillid=v_id and
                 twh11_detail.whcd=twh18_overlostdt.whcd  and   twh11_detail.itemtyp=twh18_overlostdt.itemtyp  )
                 where exists
             (select * from twh18_overlostdt  where twh18_overlostdt.olbillid=v_id
             and twh11_detail.itemcd=twh18_overlostdt.itemcd and   twh11_detail.prddate=twh18_overlostdt.prddate and
             twh11_detail.whcd=twh18_overlostdt.whcd  and   twh11_detail.itemtyp=twh18_overlostdt.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.olbillid,b.oldate,'O',a.olqty,nvl(c.stock,0)- a.olqty ,v_user,sysdate,'0'
             from twh18_overlostdt  a
             inner join twh17_overlost  b
             on a.olbillid=b.olbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.olbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh18_overlosteid  where twh18_overlosteid.olbillid=v_id
             and twh11_detail.itemcd=twh18_overlosteid.itemcd and   twh11_detail.prddate=twh18_overlosteid.prddate and
             twh11_detail.whcd=twh18_overlosteid.whcd  and   twh11_detail.itemtyp=twh18_overlosteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty - (select sum(olqty) from twh18_overlosteid  where  twh11_detail.itemcd=twh18_overlosteid.itemcd and
                 twh11_detail.prddate=twh18_overlosteid.prddate and twh18_overlosteid.olbillid=v_id and
                 twh11_detail.whcd=twh18_overlosteid.whcd  and   twh11_detail.itemtyp=twh18_overlosteid.itemtyp
                  )
                 where exists
             (select * from twh18_overlosteid  where twh18_overlosteid.olbillid=v_id
             and twh11_detail.itemcd=twh18_overlosteid.itemcd and   twh11_detail.prddate=twh18_overlosteid.prddate and
             twh11_detail.whcd=twh18_overlosteid.whcd  and   twh11_detail.itemtyp=twh18_overlosteid.itemtyp  );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'0',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.olbillid,b.oldate,'O',a.outqty,nvl(c.stock,0) - a.outqty ,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,olbillid ,sum(olqty) outqty from   twh18_overlosteid
             where olbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,olbillid ) a
             inner join twh17_overlost  b
             on a.olbillid=b.olbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.olbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中
            update tmm43_eid
            set whcd='',itemtyp='',refid=v_id,gendate=sysdate,sflg='2'--,qcflg='BF'
            where exists (select * from twh18_overlosteid  where twh18_overlosteid.eid=tmm43_eid.eid
            and  twh18_overlosteid.olbillid=v_id );




   end if ;
end if ;
-----益

if v_sign='1' then


   if v_optyp='0' then --批次

             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh18_overlostdt  where twh18_overlostdt.olbillid=v_id
             and twh11_detail.itemcd=twh18_overlostdt.itemcd and   twh11_detail.prddate=twh18_overlostdt.prddate and
             twh11_detail.whcd=twh18_overlostdt.whcd  and   twh11_detail.itemtyp=twh18_overlostdt.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty + (select olqty from twh18_overlostdt  where  twh11_detail.itemcd=twh18_overlostdt.itemcd and
                 twh11_detail.prddate=twh18_overlostdt.prddate and twh18_overlostdt.olbillid=v_id and
                 twh11_detail.whcd=twh18_overlostdt.whcd  and   twh11_detail.itemtyp=twh18_overlostdt.itemtyp  )
                 where exists
             (select * from twh18_overlostdt  where twh18_overlostdt.olbillid=v_id
             and twh11_detail.itemcd=twh18_overlostdt.itemcd and   twh11_detail.prddate=twh18_overlostdt.prddate and
             twh11_detail.whcd=twh18_overlostdt.whcd  and   twh11_detail.itemtyp=twh18_overlostdt.itemtyp  );
             -----------插新的批次

             insert into   twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,v_whcd,a.itemtyp,a.itemcd,a.prddate,a.itemqty,v_user,sysdate,sysdate,'1'
             from (select  itemtyp,itemcd,prddate, sum(olqty)itemqty from twh18_overlostdt
               where  twh18_overlostdt.olbillid=v_id   and not exists (select * from  twh11_detail
               where twh11_detail.itemcd=twh18_overlostdt.itemcd and   twh11_detail.prddate=twh18_overlostdt.prddate and
             twh11_detail.whcd=v_whcd  and   twh11_detail.itemtyp = twh18_overlostdt.itemtyp
               )
               group by  itemtyp,itemcd,prddate    ) a       ;

             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.olbillid,b.oldate,'O',a.olqty,nvl(c.stock,0) + a.olqty,v_user,sysdate,'0'
             from twh18_overlostdt  a
             inner join twh17_overlost  b
             on a.olbillid=b.olbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.olbillid=v_id;



   end if ;


   if v_optyp='1' then --id
                    -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh18_overlosteid  where twh18_overlosteid.olbillid=v_id
             and twh11_detail.itemcd=twh18_overlosteid.itemcd and   twh11_detail.prddate=twh18_overlosteid.prddate and
             twh11_detail.whcd=twh18_overlosteid.whcd  and   twh11_detail.itemtyp=twh18_overlosteid.itemtyp  );

                ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty= itemqty + (select sum(olqty) from twh18_overlosteid  where  twh11_detail.itemcd=twh18_overlosteid.itemcd and
                 twh11_detail.prddate=twh18_overlosteid.prddate and twh18_overlosteid.olbillid=v_id and
                 twh11_detail.whcd=twh18_overlosteid.whcd  and   twh11_detail.itemtyp=twh18_overlosteid.itemtyp
                  )
                 where exists
             (select * from twh18_overlosteid  where twh18_overlosteid.olbillid=v_id
             and twh11_detail.itemcd=twh18_overlosteid.itemcd and   twh11_detail.prddate=twh18_overlosteid.prddate and
             twh11_detail.whcd=twh18_overlosteid.whcd  and   twh11_detail.itemtyp=twh18_overlosteid.itemtyp  );
             -----------插新的批次

             insert into   twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,v_whcd,a.itemtyp,a.itemcd,a.prddate,a.itemqty,v_user,sysdate,sysdate,'1'
             from (select  itemtyp,itemcd,prddate, sum(olqty)itemqty from twh18_overlosteid
               where  twh18_overlosteid.olbillid=v_id   and not exists (select * from  twh11_detail
               where twh11_detail.itemcd=twh18_overlosteid.itemcd and   twh11_detail.prddate=twh18_overlosteid.prddate and
             twh11_detail.whcd=v_whcd  and   twh11_detail.itemtyp = twh18_overlosteid.itemtyp
               )
               group by  itemtyp,itemcd,prddate    ) a       ;


             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.olbillid,b.oldate,'O',a.outqty,nvl(c.stock,0)+ a.outqty ,v_user,sysdate,'0'
             from (select  whcd,itemtyp,itemcd,prddate,olbillid ,sum(olqty) outqty from   twh18_overlosteid
             where olbillid=v_id
              group by  whcd,itemtyp,itemcd,prddate,olbillid ) a
             inner join twh17_overlost  b
             on a.olbillid=b.olbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.olbillid=v_id;

             ------更新 tmm43_eid 状态
            -- sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回 5已检验  6检验中 7 生产中
------如果是已报废的损益入
update tmm43_eid
set sflg='8',whcd=v_whcd,itemtyp='DJ',qcflg='DJ',refid=v_id,prddate= (select prddate from twh18_overlosteid where
twh18_overlosteid.olbillid=v_id and
 tmm43_eid.eid=twh18_overlosteid.eid  )

where exists (select * from twh18_overlosteid  where twh18_overlosteid.olbillid=v_id and
 tmm43_eid.eid=twh18_overlosteid.eid);




---没有eid的全新配件序号损益入
             insert into tmm43_eid
            (itemcd, eid, opercd, gendate, useflg, etyp, sflg,
            refid, qcflg, whcd, prddate, itemtyp)
            select twh18_overlosteid.itemcd,eid,v_user,sysdate,'1',  tmm12_items.typflg   ,  '8'   ,
            v_id,'DJ'  ,v_whcd,prddate,'DJ'

             from twh18_overlosteid  inner join tmm12_items
             on twh18_overlosteid.itemcd=tmm12_items.itemcd
               where  twh18_overlosteid.olbillid=v_id   and
               not exists (select * from tmm43_eid where tmm43_eid.eid=twh18_overlosteid.eid) ;



            --as_return:=v_refbillid;
         end  if ;

end if ;
-------------------------
as_return:='OK';
-------------------

EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;
end ;

