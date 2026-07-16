PROCEDURE USP_ITSM_WHD_AUTO(O_RETURN OUT VARCHAR2) AS
  V_LIAB TIT10_MAINTENANCE_LIABILITY%ROWTYPE;
BEGIN
  -------------------------
  O_RETURN := 'OK';
  -------------------
  FOR EXT IN (SELECT T.*
                FROM TIT10_MAINTENANCEDAY T
               WHERE T.CURRENT_STATUS IN ('1', '2', '5')
                 AND T.FAULT_TYPE = '1' -- 1 POS
                    --   AND T.IS_SUCCESS IS NULL
                 AND T.REQUEST_TIME > TO_DATE('20140719', 'YYYYMMDD')
                 AND T.EXPECTED_COMPLETION_TIME < SYSDATE
                 AND NOT EXISTS
               (SELECT MAINTENANCE_ID
                        FROM TIT10_MAINTENANCE_LIABILITY B
                       WHERE T.MAINTENANCE_ID = B.MAINTENANCE_ID
                         AND B.TYPE = '2')
                 AND NOT EXISTS
               (SELECT MAINTENANCE_ID
                        FROM TIT24_MAINTENANCE_RV C
                       WHERE T.MAINTENANCE_ID = C.MAINTENANCE_ID)) LOOP
    BEGIN
      V_LIAB := NULL;

      V_LIAB.MAINTENANCE_ID := EXT.MAINTENANCE_ID; --维护单ID
      V_LIAB.UPDDATE        := SYSDATE; --更新时间
      V_LIAB.ASSESSFLG      := 'Y'; --是否考核
      V_LIAB.EXEMPTFLG      := 'N'; --是否豁免
      V_LIAB.IS_FINISH      := '0'; --当前状态(0未处理 1已分配 2已处理 3已审核)
      V_LIAB.TYPE           := '2'; --类型(1未完成2未达标)
      V_LIAB.USEFLG         := '1'; --有效标记
      V_LIAB.SETFROM        := 'SYS'; --来源
      BEGIN
        INSERT INTO TIT10_MAINTENANCE_LIABILITY VALUES V_LIAB;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE_APPLICATION_ERROR(-20010, '添加未达标免责记录错误！');
          ROLLBACK;
          O_RETURN := EXT.MAINTENANCE_ID || '添加未达标免责记录错误！';
      END;
    END;
    COMMIT;
  END LOOP;
EXCEPTION
  WHEN OTHERS THEN
    O_RETURN := SQLCODE || SQLERRM;

END;
