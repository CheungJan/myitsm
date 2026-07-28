procedure usp_wh_in
(as_typ varchar2 ,as_id varchar2,as_user varchar2 ,as_return out varchar2)
as
v_typ varchar2(1);--出入库操作类型
v_id  varchar2(8);--单据号
v_user varchar2(6);
v_tempid varchar2(8);
v_optyp varchar2(1);--具体是批次 =0  还是id=1
v_whcd  varchar2(2);--仓库代码
v_refbillid    varchar2(8); --对应单据
v_custcard   varchar2(15);
v_temp  number  (10);
--v_return  varchar(255);--返回值

begin

v_typ:=as_typ;
v_id:=as_id;
v_user:=as_user;

delete from tmp_wh_stock;
---------invtyp 1:采购入库 2: 质检入库 3:维护入库 4；生产入库 5：返修入库 6：外借入库7:调拨入库 8：销售退库9：生产退库
--Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中 8:在库
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id)
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
             (seqno, iotyp,whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
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
             set inqty=nvl(inqty,0)+(select inqty from twh14_checkindt where tpc13_registerdt.itemcd=twh14_checkindt.itemcd and twh14_checkindt.inbillid=v_id)
             where rgstbillid=v_tempid;

             --主表
             update tpc12_register
             set useflg=case when ( select sum(  rgsqty -   nvl(inqty,0) ) from  tpc13_registerdt where   rgstbillid=v_tempid)>0 then'0' else '2'end
             where     rgstbillid=v_tempid;
end if ;

-----------------  质检入库
if v_typ='2' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --生成入库单明细

             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0
                   from (
                   select qcstatus itemtyp, itemcd, prddate, sum(inqty) inqty
                   from tmp_qcresultdt
                   group by itemcd,qcstatus,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  qcstatus  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,qcstatus,prddate);

                     insert into tmp_qcresulteid_a
                     select * from tmp_qcresulteid;


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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数
             --
              if v_optyp='0' then --批次
                 update tqc11_resultdt
                 set inqty= nvl(inqty,0) + (select inqty from tmp_qcresultdt where  tqc11_resultdt.lineno=tmp_qcresultdt.lineno),
                 gendate=sysdate
                 where qcbillid=v_refbillid;

              end if ;

              if v_optyp='1' then --eid
                 update tqc11_resulteid
                 set inqty= nvl(inqty,0) + nvl((select inqty from tmp_qcresulteid  where tmp_qcresulteid.eid=tqc11_resulteid.eid ),0),
                 upddate=sysdate
                 where qcbillid=v_refbillid;


              end if ;

            --更新设备表状态 tmm43_eid
            update tmm43_eid
            set (sflg,refid,qcflg,whcd,prddate,itemtyp,gendate)=(select '8',v_id,a.qcstatus,v_whcd,a.prddate,qcstatus ,sysdate  from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;
            --select itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp from tmm43_eid




end if ;

------------------------------------生产
if v_typ='4' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --生成入库单明细


             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0) + a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验
/*
            insert into tmm43_eid
            (itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp)
            select a.itemcd,a.eid,v_user,sysdate,'1',  '0'   ,  '0'   ,
            v_id,'GA'  ,v_whcd,trunc(sysdate,'dd'),'ZC'
            from tqc10_result  a
            where  a.qcbillid=v_refbillid  and  not exists
            (select * from tmm43_eid where    a.eid= tmm43_eid.eid  );
*/
            update tqc10_result
            set refbillid=v_id ,useflg='2'
            where qcbillid=v_refbillid  and OPTYP='C1';


            update tqc10_result
            set useflg='2'
            where qcbillid=v_refbillid  and OPTYP='C2';
            /*
            update     tmm43_eid
            set useflg='1',refid =v_id, whcd=v_whcd--, prddate=trunc(sysdate,'dd'), itemtyp='ZC'
            where  eid=(select eid from tqc10_result   where qcbillid=v_refbillid)  ;
            */
            update  tmm43_eid
            set (sflg,useflg,refid, whcd, prddate, itemtyp,GENDATE)=
            (select '8' ,'1',v_id,v_whcd ,tmp_qcresulteid.prddate,tmp_qcresulteid.itemtyp , sysdate from tmp_qcresulteid where tmp_qcresulteid.eid= tmm43_eid.eid )
            where eid in (select eid from tmp_qcresulteid);

          --as_return:=v_refbillid;

end if ;
------------------------------------维护
if v_typ='3' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --维护入库单明细
             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0
                   from (
                   select  itemtyp, itemcd, prddate, sum(inqty) inqty
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中

            update tmm43_eid
            set (sflg,refid,qcflg,whcd,prddate,itemtyp,gendate)=(select '8',v_id,a.qcstatus,v_whcd,a.prddate,'DJ' ,sysdate  from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;

            --as_return:=v_refbillid;

end if ;





------------------------------------调拨
if v_typ='7' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --维护入库单明细
             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0
                   from (
                   select  itemtyp, itemcd, prddate, sum(inqty) inqty
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0) + a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中

            update tmm43_eid
            set (sflg,refid,whcd,gendate,itemtyp)=(select '8', v_id,v_whcd ,sysdate ,a.itemtyp from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;

            ----更新挑拨出库单状态
             if v_optyp='0' then --批次
                 update twh16_outdtprd
                set qcqty=outqty
                where outbillid=v_refbillid;
            end if ;
            if v_optyp='1' then --批次
                 update twh16_outdteid
                set qcqty=outqty
                where outbillid=v_refbillid;
            end if ;
            --as_return:=v_refbillid;

             ----【2026-05-21】调拨入库确认：更新主表状态为已入库，记录当前操作用户
           update twh13_in
             set useflg='1',
                 opercd=v_user,
                 auditflg='2',
                 auditman=v_user,
                 auditdate=sysdate
             where inbillid=v_id;

end if ;
----------------------------------------
------------------------------------生产退库
if v_typ='9' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --维护入库单明细
             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0
                   from (
                   select  itemtyp, itemcd, prddate, sum(inqty) inqty
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp ,whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中

            update tmm43_eid
            set (refid,whcd,gendate,Sflg,qcflg,itemtyp)=(select v_id,v_whcd ,sysdate,'8','DJ','DJ'  from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;

            ----更新生产退库单状态
            if v_optyp='0' then --批次
                update twh16_outdtprd
                set qcqty=qcqty+ (select inqty from tmp_qcresultdt where  twh16_outdtprd.lineno=tmp_qcresultdt.lineno and
                twh16_outdtprd.outbillid=tmp_qcresultdt.qcbillid )
                where outbillid=v_refbillid;
            end if ;
            if v_optyp='1' then --批次
                 update twh16_outdteid
                set qcqty=qcqty+nvl((select inqty from tmp_qcresulteid where twh16_outdteid.eid=tmp_qcresulteid.eid ) ,0)
                where outbillid=v_refbillid   ;
            end if ;
            --as_return:=v_refbillid;

end if ;
----------------------------------------
------------------------------------返修入库
if v_typ='5' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --维护入库单明细
             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno, s_money)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0 , s_money
                   from (
                   select  itemtyp, itemcd, prddate, sum(inqty) inqty ,sum(s_money) s_money
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno , s_money )
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0 ,s_money
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty ,sum(s_money) s_money
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中

            update tmm43_eid
            set (refid,whcd,gendate,Sflg,qcflg,itemtyp)=(select v_id,v_whcd ,sysdate,'8','DJ','DJ'  from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;

            ----更新返修出库单状态
            if v_optyp='0' then --批次
                update twh16_outdtprd
                set qcqty=qcqty+ nvl((select inqty from tmp_qcresultdt where  twh16_outdtprd.lineno=tmp_qcresultdt.lineno and
                twh16_outdtprd.outbillid=tmp_qcresultdt.qcbillid ),0) , s_money=(select s_money from tmp_qcresultdt where  twh16_outdtprd.lineno=tmp_qcresultdt.lineno and
                twh16_outdtprd.outbillid=tmp_qcresultdt.qcbillid),reflineno=(select lineno from tmp_qcresultdt where  twh16_outdtprd.lineno=tmp_qcresultdt.lineno and
                twh16_outdtprd.outbillid=tmp_qcresultdt.qcbillid)
                where outbillid=v_refbillid;
            end if ;
            if v_optyp='1' then --批次
                 update twh16_outdteid
                set qcqty=qcqty+nvl((select inqty from tmp_qcresulteid where twh16_outdteid.eid=tmp_qcresulteid.eid ) ,0),
                s_money=(select s_money from tmp_qcresulteid where twh16_outdteid.eid=tmp_qcresulteid.eid),
                  reflineno=(select reflineno from tmp_qcresulteid where twh16_outdteid.eid=tmp_qcresulteid.eid)
                where outbillid=v_refbillid   ;
            end if ;
            --as_return:=v_refbillid;

end if ;

----------------------------------------
------------------------------------外借入库
if v_typ='6' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --维护入库单明细
             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0
                   from (
                   select  itemtyp, itemcd, prddate, sum(inqty) inqty
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中

            update tmm43_eid
            set (refid,whcd,gendate,Sflg,qcflg,itemtyp)=(select v_id,v_whcd ,sysdate,'8','DJ','DJ'  from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;

            ----更新返修出库单状态
            if v_optyp='0' then --批次
                update twh16_outdtprd
                set qcqty=qcqty+ nvl((select inqty from tmp_qcresultdt where  twh16_outdtprd.lineno=tmp_qcresultdt.lineno and
                twh16_outdtprd.outbillid=tmp_qcresultdt.qcbillid ),0)
                where outbillid=v_refbillid;
            end if ;
            if v_optyp='1' then --批次
                 update twh16_outdteid
                set qcqty=qcqty+nvl((select inqty from tmp_qcresulteid where twh16_outdteid.eid=tmp_qcresulteid.eid ) ,0)
                where outbillid=v_refbillid   ;
            end if ;
            --as_return:=v_refbillid;

end if ;


----------------------------------------
------------------------------------销售退货入库
if v_typ='8' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --维护入库单明细
             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0
                   from (
                   select  itemtyp, itemcd, prddate, sum(inqty) inqty
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中

            update tmm43_eid
            set (refid,whcd,gendate,Sflg,qcflg,itemtyp)=(select v_id,v_whcd ,sysdate,'8','DJ','DJ'  from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;

            ----更新销售出库单状态
            if v_optyp='0' then --批次
                update twh16_outdtprd
                set qcqty=qcqty+ (select inqty from tmp_qcresultdt where  twh16_outdtprd.lineno=tmp_qcresultdt.lineno and
                twh16_outdtprd.outbillid=tmp_qcresultdt.qcbillid )
                where outbillid=v_refbillid;
            end if ;
            if v_optyp='1' then --批次
                 update twh16_outdteid
                set qcqty=qcqty+nvl((select inqty from tmp_qcresulteid where twh16_outdteid.eid=tmp_qcresulteid.eid ) ,0)
                where outbillid=v_refbillid   ;
            end if ;
            --as_return:=v_refbillid;

            ---如果资产已到门店作变更
           -- update tmm35_cust_pos_rl
           -- set useflg='0'
           -- where exists (select * from  tmp_qcresulteid where tmm35_cust_pos_rl.eid=tmp_qcresulteid.eid ) ;
            ---找到对应的销售单号变更开通计划


end if ;


----------------------------------------
------------------------------------销售撤销入库
if v_typ='S' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --维护入库单明细
             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0
                   from (
                   select  itemtyp, itemcd, prddate, sum(inqty) inqty
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中

            update tmm43_eid
            set (refid,whcd,gendate,Sflg,qcflg,itemtyp)=(select v_id,v_whcd ,sysdate,'8','DJ','DJ'  from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;

           ---找到对应的销售单号变更开通计划

           --itsm 返回 磁卡号
           select sm_in_open_result.cardcode into v_custcard from sm_in_open_result
           where sm_in_open_result.plan_no=v_refbillid;

           select  count(*) into v_temp from tmp_qcresulteid ;

           ---

           update tsl02_extenddt
           set  tsl02_extenddt.clqty= nvl(tsl02_extenddt.clqty,0)+ v_temp ,tsl02_extenddt.opqty=nvl(tsl02_extenddt.opqty,0) - v_temp

           where tsl02_extenddt.opbillid=v_refbillid and tsl02_extenddt.custcard=v_custcard;

           /* if v_optyp='0' then --批次
                update twh16_outdtprd
                set qcqty=qcqty+ (select inqty from tmp_qcresultdt where  twh16_outdtprd.lineno=tmp_qcresultdt.lineno and
                twh16_outdtprd.outbillid=tmp_qcresultdt.qcbillid )
                where outbillid=v_refbillid;
            end if ;
            if v_optyp='1' then --批次
                 update twh16_outdteid
                set qcqty=qcqty+nvl((select inqty from tmp_qcresulteid where twh16_outdteid.eid=tmp_qcresulteid.eid ) ,0)
                where outbillid=v_refbillid   ;
            end if ;
            */
            --as_return:=v_refbillid;

            --如果资产已到门店作变更
            update tmm35_cust_pos_rl
            set useflg='0'
            where exists (select * from  tmp_qcresulteid where tmm35_cust_pos_rl.eid=tmp_qcresulteid.eid )  ;


 end if ;

------------------------------------维护
if v_typ='C' then

             select whcd,optyp,refbillid into v_whcd,v_optyp,v_refbillid from twh13_in where inbillid=v_id;

             --维护入库单明细
             if v_optyp='0' then --批次

                   insert into twh14_checkindt
                   (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)

                   select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '',inqty, 0
                   from (
                   select  itemtyp, itemcd, prddate, sum(inqty) inqty
                   from tmp_qcresultdt
                   group by itemcd,itemtyp,prddate );
             end if ;

             if v_optyp='1' then --eid
                     insert into twh14_checkindt
                     (inbillid, whcd, lineno, itemtyp, itemcd, prddate, batchid, inqty, reflineno)
                     select v_id, v_whcd, rownum, itemtyp, itemcd, prddate, '', inqty, 0
                     from
                     (select  itemtyp, itemcd, prddate,sum( inqty) inqty
                     from tmp_qcresulteid
                     group by itemcd,itemtyp,prddate);
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
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_id )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_id
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_user,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_id  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);



             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_user,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_id;


             ---更新质检单入库数


          ---质检结果创建新pos设备ID

            --Etyp	Char(1)	设备类型	0：配件1：主机
            --Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6：检验中 7： 生产中

            update tmm43_eid
            set (sflg,refid,qcflg,whcd,prddate,itemtyp,gendate)=(select '8',v_id,a.qcstatus,v_whcd,a.prddate,'DJ' ,sysdate  from tmp_qcresulteid a
            where  tmm43_eid.eid=a.eid)
            where  exists (select * from  tmp_qcresulteid where tmm43_eid.eid=tmp_qcresulteid.eid ) ;

            --as_return:=v_refbillid;

end if ;



-------------------------
as_return:='OK';
-------------------

EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;








end ;
