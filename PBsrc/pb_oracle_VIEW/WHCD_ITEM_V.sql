select classcd, itemcd ,itemnm, itemtyp,whcd,tnumber,twhcd from (
                                    /*
                                    select twh11_detail.itemcd itemcd ,tmm12_items.itemnm itemnm ,itemtyp,'所有' whcd, sum(itemqty) tnumber from twh11_detail
                                    inner join tmm12_items
                                    on tmm12_items.itemcd=twh11_detail.itemcd
                                    group by twh11_detail.itemcd ,tmm12_items.itemnm,itemtyp
                                    union all */
                                    ---在库的
                                    select  tmm12_items.classcd classcd,twh11_detail.itemcd itemcd ,tmm12_items.itemnm itemnm,tmm31_syscodes.codenm itemtyp ,twh01_warehouse.whcd||twh01_warehouse.whnm whcd ,twh01_warehouse.whcd twhcd ,twh01_warehouse.whnm twhnm, sum(itemqty) tnumber from twh11_detail
                                    inner join tmm12_items
                                    on tmm12_items.itemcd=twh11_detail.itemcd
                                    inner join twh01_warehouse
                                    on twh01_warehouse.whcd=twh11_detail.whcd
                                    inner join tmm31_syscodes
                                    on twh11_detail.itemtyp=tmm31_syscodes.codecd and tmm31_syscodes.codetyp='QS'
                                    group by  tmm12_items.classcd, twh11_detail.itemcd ,tmm12_items.itemnm,tmm31_syscodes.codenm,twh01_warehouse.whcd||twh01_warehouse.whnm,twh01_warehouse.whcd,twh01_warehouse.whnm

                                    )
        ---不在库 生产 领用 质检出库 销售出库 借用 调拨
        -- 1:退货出库 2:质检出库3: 维护出库 4:生产出库 5：返修出库6：外借出库 7：调拨出库 8:销售出库 9 领用出库 s销售出库
                                    union all


select c.classcd, b.itemcd,c.itemnm,d.codenm,
decode(a.invtyp,'2','质检出库中','4','生产出库中','5','返修出库中','6','外借出库中','8','销售出库中',a.invtyp),
sum(b.outqty - nvl(b.qcqty,0)),'' twhcd
                         from twh15_out a
inner join  twh16_outdteid b
on a.outbillid=b.outbillid
inner join tmm12_items c
on b.itemcd=c.itemcd
 inner join tmm31_syscodes d
 on b.itemtyp=d.codecd and d.codetyp='QS'
where invtyp in ('2','4','5','6','8') and  b.outqty> b.qcqty
group   by c.classcd, b.itemcd,d.codenm,c.itemnm,
decode(a.invtyp,'2','质检出库中','4','生产出库中','5','返修出库中','6','外借出库中','8','销售出库中',a.invtyp)



                                    union all


select c.classcd, b.itemcd,c.itemnm,d.codenm,
decode(a.invtyp,'2','质检出库中','4','生产出库中','5','返修出库中','6','外借出库中','8','销售出库中',a.invtyp),
sum(b.outqty - nvl(b.qcqty,0)),'' twhcd
                         from twh15_out a
inner join  twh16_outdtprd b
on a.outbillid=b.outbillid
inner join tmm12_items c
on b.itemcd=c.itemcd
 inner join tmm31_syscodes d
 on b.itemtyp=d.codecd and d.codetyp='QS'
where invtyp in ('2','4','5','6','8') and  b.outqty> b.qcqty
group by c.classcd, b.itemcd,d.codenm,c.itemnm,
decode(a.invtyp,'2','质检出库中','4','生产出库中','5','返修出库中','6','外借出库中','8','销售出库中',a.invtyp)



----------------生产入库
union all

select c.classcd, b.itemcd,c.itemnm,d.codenm,'质检入库中',sum(b.qcqty-b.inqty),'' twhcd
 from tqc10_result   a
 inner join tqc11_resulteid b
 on a.qcbillid=b.qcbillid
      inner join tmm12_items c  on b.itemcd=c.itemcd
  inner join tmm31_syscodes d
 on b.itemtyp=d.codecd and d.codetyp='QS'
     where   a.optyp='C2'  and  a.useflg='1'
        group by  c.classcd, b.itemcd,c.itemnm,d.codenm

union all

select c.classcd, b.itemcd,c.itemnm,d.codenm,'质检入库中',sum(b.qcqty-b.inqty),'' twhcd
 from tqc10_result   a
 inner join tqc11_resulteid b
 on a.qcbillid=b.qcbillid
      inner join tmm12_items c  on b.itemcd=c.itemcd
  inner join tmm31_syscodes d
 on b.itemtyp=d.codecd and d.codetyp='QS'
     where   a.optyp='PJ'  and  a.useflg='1'
        group by  c.classcd, b.itemcd,c.itemnm,d.codenm

union all

select c.classcd, b.itemcd,c.itemnm,d.codenm,'质检入库中',sum(b.qcqty-b.inqty),'' twhcd
 from tqc10_result   a
 inner join tqc11_resultdt b
 on a.qcbillid=b.qcbillid
      inner join tmm12_items c  on b.itemcd=c.itemcd
  inner join tmm31_syscodes d
 on b.itemtyp=d.codecd and d.codetyp='QS'
     where   a.optyp='YH'  and  a.useflg='1'
        group by  c.classcd, b.itemcd,c.itemnm,d.codenm

union all
select c.classcd, a.itemcd,c.itemnm,d.codenm,'生产入库中',count(*),'' twhcd
 from tqc10_result   a

      inner join tmm12_items c  on a.itemcd=c.itemcd
  inner join tmm31_syscodes d
 on a.qcstatus=d.codecd and d.codetyp='QS'
     where   a.optyp='C1'  and  a.useflg='1'
        group by c.classcd, a.itemcd,c.itemnm,d.codenm

