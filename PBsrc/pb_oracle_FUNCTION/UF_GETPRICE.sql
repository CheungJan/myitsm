FUNCTION uf_GetPrice (
	v_itemcd    IN   CHAR, -- 商品代码
	v_busityp   IN   CHAR -- 业务类型
)
	RETURN NUMBER
AS
	v_price        DECIMAL (16, 8);
BEGIN
	v_price := NULL;

	IF v_price IS NULL THEN
	BEGIN
		SELECT itemprice
		  INTO v_price
		  FROM tip01_price
		 WHERE busityp = v_busityp AND itemcd = v_itemcd AND useflg = '1';
		EXCEPTION
		WHEN NO_DATA_FOUND
		THEN
			v_price := NULL;
	END;
  END IF;

   RETURN nvl(v_price,0);
END uf_getprice;

