select a.itemcd, b.itemnm,c.whnm,a.itemqty
from (
select itemcd ,whcd ,sum(itemqty) itemqty from twh11_detail
group by itemcd ,whcd
having sum(itemqty)>0 ) a
inner join tmm12_items b
on a.itemcd=b.itemcd
inner join twh01_warehouse c
on a.whcd=c.whcd
where c.defaultflg='Y'

