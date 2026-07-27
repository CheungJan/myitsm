select to_char(id) , b.itemcd,b.eid from sm_in_part_change a  inner join tmm43_eid b
on a.old_serialno=b.eid

union all

select a.outbillid,a.itemcd,a.eid from twh16_outdteid a
inner join twh15_out b
on a.outbillid=b.outbillid

