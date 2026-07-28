PROCEDURE USP_ADJPRICE(
    as_pabillid char,
   	ai_Result    out int)

AS
	ai_Row	int;

begin


	select count(*) into ai_Row from tip03_adjprice
	where pabillid = as_pabillid ;
	if ai_Row > 0 then


		insert into Tmp_AdjPrice_items(itemcd,unitcd,busityp,itemprice,opercd)
		select a.itemcd,'01',a.busityp,a.newprice,a.opercd
		from tip03_adjprice a,tmm12_items b
		where  a.itemcd=b.itemcd
    and a.pabillid = as_pabillid
    and a.useflg = '0';

		FOR c_adjprice_items IN (select itemcd,unitcd,busityp,itemprice,opercd
		                      from tmp_adjprice_items order by itemcd)
		LOOP
			-- 判断公共价格表中该商品该价类是否存在
			select count(*) into ai_Row from tip01_price
			where itemcd = c_adjprice_items.itemcd
			and busityp = c_adjprice_items.busityp;
			if ai_Row < 1 then
				insert into tip01_price(itemcd,busityp,unitcd,itemprice,opercd,
							gendate,upddate,useflg,whtransflg,sttransflg)
				select c_adjprice_items.itemcd,c_adjprice_items.busityp ,c_adjprice_items.unitcd,
				c_adjprice_items.itemprice,c_adjprice_items.opercd,sysdate,sysdate,'1','1','1'
				from tmp_adjprice_items
				where itemcd = c_adjprice_items.itemcd and busityp = c_adjprice_items.busityp;
			else
				update tip01_price set itemprice = c_adjprice_items.itemprice ,upddate = sysdate
				where itemcd = c_adjprice_items.itemcd and busityp = c_adjprice_items.busityp ;
		 end if;

	 END LOOP;

   update tip03_adjprice set useflg = '1'
    where useflg = '0'
    and pabillid = as_pabillid;

	end if;


ai_Result :=1;

end;

