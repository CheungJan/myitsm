select nvl(a.whcd , b.whcd)  whcd,    nvl(a.itemtyp,b.itemtyp) itemtyp ,
nvl( a.itemcd, b.itemcd)  itemcd   ,  nvl(a.prddate,to_date('1900-01-01','yyyy-mm-dd')) prddate ,nvl(a.itemqty,0) whqty , nvl(b.tmm43qty,0)  tmm43qty from twh11_detail a
full outer join
(select whcd,itemcd, nvl(prddate,to_date('1900-01-01','yyyy-mm-dd')) prddate,itemtyp,count(*) tmm43qty from tmm43_eid
where sflg='8' and useflg='1'
group by   whcd,itemcd,prddate,itemtyp  ) b
on   a.whcd= b.whcd   and a.itemtyp=b.itemtyp   and  a.itemcd=b.itemcd    and   a.prddate=b.prddate
where nvl(a.itemqty,0) <> nvl(b.tmm43qty,0)

