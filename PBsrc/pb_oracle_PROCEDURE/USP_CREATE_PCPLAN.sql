PROCEDURE USP_create_pcplan(
    as_slbillid char,
    as_type  char,
    as_user  char,
     as_Result    out varchar2)

AS
  p_slbillid char(8); --销售订单号
    p_type  char(1);--类型 0 销售订单 1 库存下限 2 其他
    p_user  char(6); --做成人
    p_ppid  char(8);--采购计划单号
    ls_itemcd char(6);--机型代码
    ll_rowount int ;
    ll_qty     int; --订单数量


begin

--根据销售订单 或 库存下限生成采购计划单
p_ppid:=uf_get_billnou('PP');
p_slbillid :=as_slbillid;
p_type :=as_type;
p_user  :=as_user;


------------------------------根据销售单
if p_type= '0' then
   begin
-------------------------------  根据销售单号
--回写销售单号采购计划标记 X

select count(*) into ll_rowount
from tmp_pcplan
 where slbillid=p_slbillid;

if ll_rowount<>0 then
   as_Result:='异常';
   return ;
end if ;


update tsl10_slbill
set pcplanflg='X'
where slbillid=p_slbillid   and  pcplanflg='0';



         --判断是不是当月第一张采购计划单
         ll_rowount:=0;


         select count(*) into ll_rowount  from  tpc01_pcplan
                where   trunc(plandate,'mm')= trunc(sysdate,'mm')  and pctyp='0'  and useflg='1';

         select  itemcd, rgsqty
         into ls_itemcd,ll_qty
         from tsl10_slbill
         where slbillid=p_slbillid;



         ---生成主表
         insert into tmp_pcplan
                ( pcplanid, slbillid, pctyp, ptimes, opercd, memo, gendate, useflg, plandate,auditflg ,type)
           values
                (p_ppid,p_slbillid,'0',0,p_user,'',sysdate,'1',trunc(sysdate,'dd'),'0' ,p_type);

         --明细
          if    ll_rowount=0 then

          --扣除库存
                 insert into tmp_pcplandt
                       (pcplanid, lineno, itemcd, rgstqty, units, storeqty, lowlimit, upperlimit)
                 select  p_ppid,rownum,itemcd,
               nvl( (bomqty*ll_qty) -    case when (nvl(twh.storeqty,0) -tmm12.lowerlimit )> 0
                then (nvl(twh.storeqty,0) -tmm12.lowerlimit )else 0 end  ,0),
                 tmm12.wunit ,nvl(twh.storeqty,0) ,tmm12.lowerlimit,tmm12.upperlimit
                 from tmm42_bomdt
                 left outer  join (select itemcd,sum(itemqty) storeqty from twh11_detail
                 where whcd='01' and itemtyp='ZC'  ---新品仓 正常品
                 group by itemcd) twh
                 on twh.itemcd=tmm42_bomdt.itemcd
                 inner join  tmm12_items  tmm12
                 on tmm42_bomdt.itemcd=tmm12.itemcd

                 where bomcd=ls_itemcd;




          else

          --全额采购
                insert into tmp_pcplandt
                       (pcplanid, lineno, itemcd, rgstqty, units, storeqty, lowlimit, upperlimit)
                 select  p_ppid,rownum,itemcd,nvl(bomqty*ll_qty,0),tmm12.wunit,nvl(twh.storeqty,0) ,tmm12.lowerlimit,tmm12.upperlimit
                 from tmm42_bomdt
                 left outer  join (select itemcd,sum(itemqty) storeqty from twh11_detail
                 where whcd='01' and itemtyp='ZC'  ---新品仓 正常品
                 group by itemcd) twh
                 on twh.itemcd=tmm42_bomdt.itemcd
                 inner join  tmm12_items  tmm12
                 on tmm42_bomdt.itemcd=tmm12.itemcd

                 where bomcd=ls_itemcd;



          end if ;

   end ;

end if ;


------------------------------- 根据最低库存

if p_type= '1' then
   begin
           --创建主表
           insert into tmp_pcplan
                ( pcplanid, slbillid, pctyp, ptimes, opercd, memo, gendate, useflg, plandate,auditflg,type)
           values
                (p_ppid,p_slbillid,'0',0,p_user,'',sysdate,'1',trunc(sysdate,'dd'),'0',p_type);


           --创建明细表

            insert into tmp_pcplandt
                 (pcplanid, lineno, itemcd, rgstqty, units, storeqty, lowlimit, upperlimit)
                 select  p_ppid,rownum,tmm12.itemcd,
               -- case when  nvl(tmm12.upperlimit - nvl(twh.storeqty ,0) ,0) > 0
                --     then  nvl(tmm12.upperlimit - nvl(twh.storeqty ,0) ,0) else 0 end ,--采购直接慢最高上限
                 tmm12.upperlimit,--上限采购
                 tmm12.wunit,nvl(twh.storeqty,0) ,tmm12.lowerlimit,tmm12.upperlimit
                 from  tmm12_items  tmm12

                 left outer  join (select itemcd,sum(itemqty) storeqty from twh11_detail
                 where whcd='01' and itemtyp='ZC'  ---新品仓 正常品
                 group by itemcd) twh
                 on twh.itemcd=tmm12.itemcd

                 where   nvl(twh.storeqty,0) <tmm12.lowerlimit  and tmm12.useflg='1' and tmm12.purchasetyp='1' and tmm12.typflg='0'
                 and tmm12.lowerlimit<>0;


   end ;

end if ;



as_Result:=p_ppid;

end ;
