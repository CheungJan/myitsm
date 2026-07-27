procedure usp_wh
(as_typ char ,as_id char,as_user char ,as_return out varchar2)
as
v_typ char(1);--出入库操作类型
v_id  char(8);--单据号
v_user char(6);
v_tempid char(8);
v_optyp char(1);--具体是批次 =0  还是id=1
v_whcd  char(2);--仓库代码
v_refbillid    char(8); --对应单据
--v_return  varchar(255);--返回值

begin

v_typ:=as_typ;
v_id:=as_id;
v_user:=as_user;

delete from tmp_wh_stock;
---------invtyp 1:采购入库 2:质检出库3: 质检入库 4:维护出库 5：维护入库 6:生产入库
---------采购入库
if v_typ='1' then
             -----保存库存数

             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty=itemqty+(select inqty from twh14_checkindt  where  twh11_detail.itemcd=twh14_checkindt.itemcd and
                 twh11_detail.prddate=twh14_checkindt.prddate and
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0),v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新采购单状态
             --对应采购单号
             select refbillid into v_tempid from twh13_in where inbillid=v_id;
             --明细
             update tpc13_registerdt
             set inqty=inqty+(select inqty from twh14_checkindt where tpc13_registerdt.itemcd=twh14_checkindt.itemcd and twh14_checkindt.inbillid=v_id)
             where rgstbillid=v_tempid;

             --主表
             update tpc12_register
             set useflg=decode( (select sum( rgsqty - inqty ) from  tpc13_registerdt)  ,0,'2','0'   )
             where     rgstbillid=v_tempid;
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
                 twh11_detail.prddate=twh16_outdtprd.prddate and
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
                 twh11_detail.prddate=twh16_outdteid.prddate and
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

   end if ;
end if ;



if v_typ='3' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --生成入库单明细

             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', sum(inqty), 0
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate;
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', sum(inqty), 0
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate;
             end if ;
   --select qcbillid, itemcd, itemtyp, prddate, qcqty, qcstatus, inqty, opercd, gendate, useflg, lineno from tmp_qcresultdt

  -- select qcbillid, itemcd, itemtyp, prddate, qcqty, qcstatus, inqty, eid, gendate, upddate, opercd, lineno from tmp_qcresulteid

             -----保存库存数
             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty=itemqty+(select inqty from twh14_checkindt  where  twh11_detail.itemcd=twh14_checkindt.itemcd and
                 twh11_detail.prddate=twh14_checkindt.prddate and
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate );



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0),v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数
             --
              if v_optyp='0' then --批次
                 update tqc11_resultdt
                 set inqty= inqty + (select inqty from tmp_qcresultdt where  tqc11_resultdt.lineno=tmp_qcresultdt.lineno)
                 where qcbillid=v_refbillid;

              end if ;

              if v_optyp='1' then --eid
                 update tqc11_resulteid
                 set inqty= inqty + (select inqty from tmp_qcresulteid where  tqc11_resulteid.lineno=tmp_qcresulteid.lineno)
                 where qcbillid=v_refbillid;


              end if ;

            ------更新设备表状态 tmm43_eid
            --select itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp from tmm43_eid




end if ;



-------------------------
as_return:='OK';
-------------------

EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;








end ;

