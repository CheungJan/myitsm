select itemcd,whcd,itemtyp,prddate,count(*) from tmm43_eid
where  useflg='1' and sflg= '8'
group by itemcd,whcd,itemtyp,prddate

