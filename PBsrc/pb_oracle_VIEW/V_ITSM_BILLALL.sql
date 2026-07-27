SELECT 'WHD' BILLTYPE,
       U.AREAID USEAREA,
       W.MAINTENANCE_ID AS MASTER_ID,
       NVL(TRIM(W.FIRSTOR), '无名氏') AS FIRSTOR,
       W.IS_SUCCESS,
       C.BUSITYP,
       C.CLASSCD,
       C.AREA,
       CREATE_TIME,
       CREATOR,
       CLOSE_TIME ,
       (SELECT COUNT(*)
          FROM TIT21_MAINTENANCE_DISPATCH D
         WHERE D.MAINTENANCE_ID = W.MAINTENANCE_ID) PDCS,
      -- firstor,
       first_time ,
       leave_time ,
       revisit_time ,
       memo ,
       request_time ,
       expected_completion_time ,
       is_old ,
       c.custnm ,
       c.address ,
       c.custcard,
       CURRENT_STATUS,
       fault_type ,
       short_description ,
       detail_description ,
       C.CUSTCD,c.USEFLG ,
       NULL CHANGE_TYPE,
       c.IS_CONTRACT
  FROM TIT10_MAINTENANCEDAY W, TMM22_CUSTOMERS C, TIT06_USERAREA U
 WHERE W.STORE_ID = C.CUSTCD
   AND W.FIRSTOR = U.USERCD(+)
   AND W.CURRENT_STATUS <> '9'

UNION ALL

---保养单
SELECT 'BYD' BILLTYPE,
       U.AREAID USEAREA,
       M.DAILY_MAINTENANCE_ID,
       NVL(TRIM(M.FIRSTOR), '无名氏') AS FIRSTOR,
       M.IS_SUCCESS,
       C.BUSITYP,
       C.CLASSCD,
       C.AREA,
       CREATE_TIME,
       CREATOR,
       CLOSE_TIME ,
       0,
       --firstor,
       first_time ,
       leave_time ,
       revisit_time ,
       null ,
       request_time ,
       null ,
       is_old ,
       c.custnm ,
       c.address ,
       c.custcard,
       CURRENT_STATUS,
       null,
       short_description ,
       detail_description ,
       C.CUSTCD,c.USEFLG,
       NULL CHANGE_TYPE,
       c.IS_CONTRACT
  FROM TIT17_MAINTENANCE M, TMM22_CUSTOMERS C, TIT06_USERAREA U
 WHERE M.STORE_ID = C.CUSTCD
   AND M.FIRSTOR = U.USERCD(+)
   AND M.CURRENT_STATUS <> '9'

UNION ALL

---开通单
SELECT 'KTD' BILLTYPE,
       U.AREAID USEAREA,
       M.NEW_OPENING_ID ,
       NVL(TRIM(M.FIRSTOR), '无名氏') AS FIRSTOR,
       M.IS_SUCCESS,
       C.BUSITYP,
       C.CLASSCD,
       C.AREA,
       CREATE_TIME,
       CREATOR,
       CLOSE_TIME ,
       0,
       --firstor,
       first_time ,
       leave_time ,
       revisit_time ,
       null ,
       request_time ,
       null ,
       is_old ,
       c.custnm ,
       c.address ,
       c.custcard,
       CURRENT_STATUS,
       null ,
       short_description ,
       detail_description ,
       C.CUSTCD,c.USEFLG,
       NULL CHANGE_TYPE,
       c.IS_CONTRACT
  FROM TIT13_MAINTENANCE_OPEN M, TMM22_CUSTOMERS C, TIT06_USERAREA U
 WHERE M.STORE_ID = C.CUSTCD
   AND M.FIRSTOR = U.USERCD(+)
   AND M.CURRENT_STATUS <> '9'

UNION ALL

---旧机翻新
SELECT 'KTD' BILLTYPE,
       U.AREAID USEAREA,
       M.RENEW_ID  ,
       NVL(TRIM(M.FIRSTOR), '无名氏') AS FIRSTOR,
       M.IS_SUCCESS,
       C.BUSITYP,
       C.CLASSCD,
       C.AREA,
       CREATE_TIME,
       CREATOR,
       CLOSE_TIME ,
       0,
       --firstor,
       first_time ,
       leave_time ,
       revisit_time ,
       null ,
       request_time ,
       null ,
       is_old ,
       c.custnm ,
       c.address ,
       c.custcard ,
       CURRENT_STATUS,
       null,
       short_description ,
       detail_description ,
       C.CUSTCD,c.USEFLG,
       NULL CHANGE_TYPE,
       c.IS_CONTRACT
  FROM TIT15_MAINTENANCE_RENOVATE M, TMM22_CUSTOMERS C, TIT06_USERAREA U
 WHERE M.STORE_ID = C.CUSTCD
   AND M.FIRSTOR = U.USERCD(+)
   AND M.CURRENT_STATUS <> '9'

UNION ALL

---免费更换
SELECT 'KTD' BILLTYPE,
       U.AREAID USEAREA,
       M.RENEW_ID   ,
       NVL(TRIM(M.FIRSTOR), '无名氏') AS FIRSTOR,
       M.IS_SUCCESS,
       C.BUSITYP,
       C.CLASSCD,
       C.AREA,
       CREATE_TIME,
       CREATOR,
       CLOSE_TIME ,
       0,
      -- firstor,
       first_time ,
       leave_time ,
       revisit_time ,
       null ,
       request_time ,
       null ,
       is_old ,
       c.custnm ,
       c.address ,
       c.custcard ,
       CURRENT_STATUS,
       null,
       short_description ,
       detail_description ,
       C.CUSTCD,c.USEFLG,
       NULL CHANGE_TYPE,
       c.IS_CONTRACT
  FROM TIT28_FREE_REPLACE M, TMM22_CUSTOMERS C, TIT06_USERAREA U
 WHERE M.STORE_ID = C.CUSTCD
   AND M.FIRSTOR = U.USERCD(+)
   AND M.CURRENT_STATUS <> '9'

UNION ALL

---设备变更
SELECT 'KTD' BILLTYPE,
       U.AREAID USEAREA,
       M.DEVICE_CHANGE_ID    ,
       NVL(TRIM(M.FIRSTOR), '无名氏') AS FIRSTOR,
       M.IS_SUCCESS,
       C.BUSITYP,
       C.CLASSCD,
       C.AREA,
       CREATE_TIME,
       CREATOR,
       CLOSE_TIME ,
       0,
       --firstor,
       first_time ,
       leave_time ,
       revisit_time ,
       null ,
       request_time ,
       null ,
       is_old ,
       c.custnm ,
       c.address ,
       c.custcard ,
       CURRENT_STATUS,
       null,
       short_description ,
       detail_description ,
       C.CUSTCD,c.USEFLG,
       CHANGE_TYPE,
       c.IS_CONTRACT
  FROM TIT16_DEVICE_CHANGE M, TMM22_CUSTOMERS C, TIT06_USERAREA U
 WHERE M.STORE_ID = C.CUSTCD
   AND M.FIRSTOR = U.USERCD(+)
   AND M.CURRENT_STATUS <> '9'


UNION ALL

SELECT 'KTD' BILLTYPE,
       U.AREAID USEAREA,
       M.STORE_CLOSE_ID     ,
       NVL(TRIM(M.FIRSTOR), '无名氏') AS FIRSTOR,
       M.IS_SUCCESS,
       C.BUSITYP,
       C.CLASSCD,
       C.AREA,
       CREATE_TIME,
       CREATOR,
       CLOSE_TIME ,
       0,
      -- firstor,
       first_time ,
       leave_time ,
       revisit_time ,
       null ,
       request_time ,
       null ,
       is_old ,
       c.custnm ,
       c.address ,
       c.custcard,
       CURRENT_STATUS,
       null ,
       short_description ,
       detail_description ,
       C.CUSTCD,c.USEFLG,
       NULL CHANGE_TYPE,
       c.IS_CONTRACT
  FROM TIT18_STORE_CLOSE M, TMM22_CUSTOMERS C, TIT06_USERAREA U
 WHERE M.STORE_ID = C.CUSTCD
   AND M.FIRSTOR = U.USERCD(+)
   AND M.CURRENT_STATUS <> '9'

