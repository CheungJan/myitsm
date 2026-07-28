Function uf_wh_historykc(p_start_in char,
                                            p_end_in   char) Return Varchar2 As

  p_start   char(10) := p_start_IN;
  p_end     char(10) := p_end_IN;
  v_errno   Number(5);
  v_isamno  Number(5);
  v_errtext Varchar2(2000);
Begin
  Begin
 -------invtyp 1:采购入库 2: 质检入库 3:维护入库 4；生产入库 5：返修入库 6：外借入库7:调拨入库 8：销售退库9：生产退库
 -------invtyp  1:退货出库 2:质检出库3: 维护出库 4:生产出库 5：返修出库6：外借出库 7：调拨出库 8:销售出库 9 领用出库 s销售出库
    Delete From TMP_QUERY_ITEMTIV;
    Insert Into TMP_QUERY_ITEMTIV
      (whcd,itemtyp, itemcd, itemnm, itemsize, unitnm, classcd ,
 qckc ,qmkc , cgrk, cgth  ,xstk,xs,
  zjck, zjrk, scck, scrk, lyck, lyrk,
   whck, whrk, fxck, fxrk, wjck, wjrk,
    syck, syrk ,dbck,dbrk
)
   Select a.whcd, a.itemtyp, a.itemcd, tmm12_items.itemnm, tmm12_items.itemsize,tmm12_items.wunit, tmm12_items.classcd ,
   nvl( b.storeqty,0),nvl(c.storeqty,0),nvl(d.cgrk,0),nvl(e.cgth,0),nvl(d.xstk,0),nvl(e.xs,0),
   nvl(e.zjck,0),nvl(d.zjrk,0),nvl(e.scck,0),nvl(d.scrk,0),nvl(e.lyck,0),nvl(d.sctk,0),
   nvl( e.whck,0),nvl(d.whrk,0),nvl(e.fxck,0),nvl(d.fxrk,0),nvl(e.wjck,0),nvl(d.wjrk,0),
  nvl( e.syck,0),nvl(d.syrk,0),nvl( e.dbck,0),nvl(d.dbrk,0)
  From (select distinct whcd,  itemcd,itemtyp from twh11_detail) a
  -----期初库存
        Left Outer Join (Select a2.whcd, a2.ItemCd, a2.ItemTyp,
                                                     sum(nvl(a2.storeqty, 0)) storeqty
                                                From twh12_detaildt a2,
                                                     (Select Max(seqno) seqno, whcd, ItemCd, ItemTyp,prddate
                                                         From twh12_detaildt
                                                        Where to_char(invdate, 'yyyy-mm-dd') <
                                                           p_start
                                                        Group By  whcd,ItemCd, ItemTyp,prddate) b2
                                               Where a2.seqno = b2.seqno And a2.itemcd = b2.itemcd And
                                                     a2.itemtyp = b2.itemtyp and a2.whcd=b2.whcd group by a2.whcd, a2.ItemCd, a2.ItemTyp) b
                                                      On a.itemcd = b.itemcd And a.ItemTyp = b.ItemTyp and a.whcd=b.whcd
    ---期末库存
          Left Outer Join (Select a2.whcd, a2.ItemCd, a2.ItemTyp,
                                                     sum(nvl(a2.storeqty, 0)) storeqty
                                                From twh12_detaildt a2,
                                                     (Select Max(seqno) seqno, whcd, ItemCd, ItemTyp,prddate
                                                         From twh12_detaildt
                                                        Where to_char(invdate, 'yyyy-mm-dd') <=
                                                            p_end
                                                        Group By  whcd,ItemCd, ItemTyp,prddate) b2
                                               Where a2.seqno = b2.seqno And a2.itemcd = b2.itemcd And
                                                     a2.itemtyp = b2.itemtyp and a2.whcd=b2.whcd group by a2.whcd, a2.ItemCd, a2.ItemTyp)c
                                                      On a.itemcd = c.itemcd And a.ItemTyp = c.ItemTyp and a.whcd=c.whcd


     -- 入库数据     iotyp='1'
       -------invtyp 1:采购入库 2: 质检入库 3:维护入库 4；生产入库 5：返修入库 6：外借入库7:调拨入库 8：销售退库9：生产退库


              Left Outer Join (Select whcd, itemcd, itemtyp,
              Sum(decode(invtyp, '1', nvl(itemqty, 0), 0)) as cgrk ,
               Sum(decode(invtyp, '2', nvl(itemqty, 0), 0)) as zjrk ,
               Sum(decode(invtyp, '3', nvl(itemqty, 0), 0)) as whrk ,
                Sum(decode(invtyp, '4', nvl(itemqty, 0), 0)) as scrk ,
                 Sum(decode(invtyp, '5', nvl(itemqty, 0), 0)) as fxrk ,
                  Sum(decode(invtyp, '6', nvl(itemqty, 0), 0)) as wjrk ,
                   Sum(decode(invtyp, '7', nvl(itemqty, 0), 0)) as dbrk ,
                    Sum(decode(invtyp, '8', nvl(itemqty, 0), 0)) as xstk ,
                     Sum(decode(invtyp, '9', nvl(itemqty, 0), 0)) as sctk ,
                      Sum(decode(invtyp, 'O', nvl(itemqty, 0), 0)) as syrk
                                 From twh12_detaildt
                                Where
                                      to_char(invdate, 'yyyy-mm-dd') Between
                                      p_start And p_end  and     iotyp='1'
                                Group By whcd ,itemcd, itemtyp) d On a.whcd=d.whcd and a.itemcd = d.itemcd And a.itemtyp = d.itemtyp


      ---出库数据     iotyp='0'
 -------invtyp  1:退货出库 2:质检出库3: 维护出库 4:生产出库 5：返修出库6：外借出库 7：调拨出库 8:销售出库 9 领用出库 s销售出库

             Left Outer Join (Select whcd, itemcd, itemtyp,
                            Sum(decode(invtyp, '1', nvl(itemqty, 0), 0))as cgth ,
                             Sum(decode(invtyp, '2', nvl(itemqty, 0), 0)) as  zjck ,
                             Sum(decode(invtyp, '3', nvl(itemqty, 0), 0)) as  whck ,
                              Sum(decode(invtyp, '4', nvl(itemqty, 0), 0))  as scck ,
                               Sum(decode(invtyp, '5', nvl(itemqty, 0), 0)) as  fxck ,
                                Sum(decode(invtyp, '6', nvl(itemqty, 0), 0)) as  wjck ,
                                 Sum(decode(invtyp, '7', nvl(itemqty, 0), 0))  as dbck ,
                                  Sum(decode(invtyp, '8', nvl(itemqty, 0), 0))  as xsck ,
                                   Sum(decode(invtyp, '9', nvl(itemqty, 0), 0)) as lyck ,
                                    Sum(decode(invtyp, 'O', nvl(itemqty, 0), 0)) as syck ,
                                    Sum(decode(invtyp, 'S', nvl(itemqty, 0), 0)) as xs
                                 From twh12_detaildt
                                Where
                                      to_char(invdate, 'yyyy-mm-dd') Between
                                    p_start  And p_end   and    iotyp='0'
                                Group By  whcd,itemcd, itemtyp) e On a.whcd=e.whcd and  a.itemcd = e.itemcd And a.itemtyp = e.itemtyp

               inner join tmm12_items
        on  a.itemcd=  tmm12_items.itemcd


             ;

    Return 'ok';
  Exception
    When Others Then
      v_errno   := Sqlcode;
      v_isamno  := Sqlcode;
      v_errtext := Sqlerrm;
      Return v_errtext;
  End;
End uf_wh_historykc;
