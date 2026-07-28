procedure usp_asset_c_a
 (
 as_id          char,
 as_custcd          char,
 as_useid         char,
 as_Result    out varchar2)

AS
v_id char(8);--作废单号
v_custcd char(8);--客户号
v_useid varchar2(6);
v_oldeid varchar2(13);
v_whcd varchar(2);
v_outbillid char(8);
v_back char(1);
v_sltyp varchar2(4);
begin
v_id:=as_id;
v_custcd:= as_custcd;
v_useid:=as_useid;
v_whcd:='L1'; --临时库
-------------------------
select twh20_asset_c_a_dtl.eid into v_oldeid  from twh20_asset_c_a_dtl
where twh20_asset_c_a_dtl.opbillid=v_id and twh20_asset_c_a_dtl.custcd =v_custcd;

select t.sltyp into v_sltyp from twh19_asset_c_a t where opbillid = v_id and rownum = 1;

if  v_sltyp = 'BG' then
  --来源为作废申请的单子 默认入库
  v_back   := 'Y';
else
  ----判断是否返回设备
  SELECT nvl(is_back, 'Y') into v_back from TSL02_EXTENDDT where opbillid = v_id and custcd =v_custcd ;
end if;

IF v_back <> 'N' THEN
    v_outbillid := uf_get_billnou('IN')  ;


          insert into twh13_in
          ( whcd,indate, inbillid, refbillid,invtyp, ptimes, memo, opercd, gendate, auditflg, auditman, auditdate,
           optyp, useflg, suppcd )

           select v_whcd,sysdate, v_outbillid,v_id,'C','0','','SYS',sysdate,'','','',
           '1','1',''
           from tmm43_eid
           where eid=v_oldeid ;



           insert into twh14_checkindt
           ( whcd, inbillid, lineno, itemtyp, itemcd,
           prddate, inqty  )
           select v_whcd,v_outbillid,1,'DJ',itemcd
           ,prddate,1
           from tmm43_eid
           where eid=v_oldeid ;

   --        usp_wh_in('C',v_outbillid,'SYS',as_Result );

            -----保存库存数
             insert into  tmp_wh_stock
             (itemcd, whcd, itemtyp, prddate, stock)
             select itemcd ,whcd,itemtyp,prddate,itemqty from twh11_detail
             where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_outbillid
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );
             ------更新批次主表

             update twh11_detail
             set upddate=sysdate,
                 itemqty=itemqty+(select inqty from twh14_checkindt  where  twh11_detail.itemcd=twh14_checkindt.itemcd and
                 twh11_detail.prddate=twh14_checkindt.prddate and
                 twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  and twh14_checkindt.inbillid=v_outbillid )
                 where exists
             (select * from twh14_checkindt  where twh14_checkindt.inbillid=v_outbillid
             and twh11_detail.itemcd=twh14_checkindt.itemcd and   twh11_detail.prddate=twh14_checkindt.prddate and
             twh11_detail.whcd=twh14_checkindt.whcd  and   twh11_detail.itemtyp=twh14_checkindt.itemtyp  );


             ------插新批次主表
             insert into twh11_detail
             (seqno, whcd, itemtyp, itemcd, prddate, itemqty, opercd, gendate, upddate, useflg)
             select twh11_seqno.nextval,whcd,itemtyp,itemcd,prddate,inqty,v_useid,sysdate,sysdate,'0' from twh14_checkindt
             where inbillid=v_outbillid  and not exists
             (select * from twh11_detail where twh11_detail.itemcd=twh14_checkindt.itemcd and
               twh11_detail.prddate=twh14_checkindt.prddate and  twh11_detail.itemtyp=twh14_checkindt.itemtyp and
             twh11_detail.whcd=twh14_checkindt.whcd);


             ------插新批次明细表
             insert into twh12_detaildt
             (seqno,iotyp, whcd, itemtyp, itemcd, prddate, billid, invdate, invtyp, itemqty, storeqty, opercd, gendate, useflg)
             select twh12_seqno.nextval,'1',a.whcd,a.itemtyp,a.itemcd,a.prddate,a.inbillid,b.indate,b.invtyp,a.inqty,nvl(c.stock,0)+ a.inqty,v_useid,sysdate,'0' from twh14_checkindt  a
             inner join twh13_in  b
             on a.inbillid=b.inbillid
             left outer  join  tmp_wh_stock c
             on a.whcd=c.whcd and  a.itemtyp=c.itemtyp  and a.itemcd=c.itemcd and  a.prddate= c.prddate
             where a.inbillid=v_outbillid;

           --修改tmm43
           update tmm43_eid
           set whcd=v_whcd,sflg='8',qcflg='DJ',itemtyp='DJ',refid = v_outbillid,gendate=sysdate
           where eid=v_oldeid;
ELSE
-----修改tmm43  whcd=v_whcd,
           update tmm43_eid
           set sflg='2',qcflg='DJ',itemtyp='DJ',gendate=sysdate
           where eid=v_oldeid;
END IF;

-----删除tmm35_cust_pos_rl信息


        update tmm35_cust_pos_rl
        set useflg='0'
        where  eid=v_oldeid and custcd= v_custcd ;


as_Result:= v_useid;

-------------------

EXCEPTION
 when others then
    as_Result:=sqlcode||sqlerrm;

end ;
