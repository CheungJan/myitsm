FUNCTION uf_storeposinfo_qj (
  v_billid    IN   CHAR -- 门店代码

)
  RETURN varchar2
AS
  ls_return       varchar2(500);
BEGIN
/*
SELECT
    substr( LISTAGG(  itemnm, '  ||  ') WITHIN GROUP(ORDER BY itemnm) ,1,500) AS posinfo into ls_return
      FROM ( Select a.custcd, b.ITEMNM||'('||to_char(a.startdate,'yyyy/mm/dd')||')'  itemnm  From tmm35_cust_pos_rl a , tmm12_items b
        Where custcd = v_custcd  And a.useflg = '1'
        And a.itemcd = b.itemcd order by a.startdate desc  ) group by custcd ;

*/
select b.itemnm into ls_return from  plan_cust a
inner join tmm12_items b
on a.pos_item=b.itemcd
        where   a.planno=v_billid  ;

        return ls_return;

EXCEPTION
when others then



   RETURN '-';
END uf_storeposinfo_qj;
