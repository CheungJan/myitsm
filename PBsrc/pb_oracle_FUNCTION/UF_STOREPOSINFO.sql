FUNCTION uf_storeposinfo (
  v_custcd    IN   CHAR -- 门店代码

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
select ITEMNM into ls_return from (
     Select   b.ITEMNM    From tmm35_cust_pos_rl a , tmm12_items b
        Where custcd = v_custcd  And a.useflg = '1' and a.itemcd=b.itemcd

        order by a.startdate desc )
        where    rownum =1  ;
        return ls_return ;

EXCEPTION
when others then



   RETURN nvl(ls_return,'-');
END uf_storeposinfo;
