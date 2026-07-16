PROCEDURE SP_KQ_IMPA(I_MON    IN VARCHAR2,
                                       I_NUM    IN VARCHAR2,
                                       I_OPER   IN CHAR,
                                       O_RETURN OUT VARCHAR2)

 AS
  V_NUM     NUMBER;
  V_BEG     NUMBER;
  V_COUNT   NUMBER;
  V_DATE    DATE;

  V_ARR     VARCHAR2(4);
  V_LEAVE   VARCHAR2(4);
  V_IMP     TKQ01_ATTENDANCE%ROWTYPE;
BEGIN

  BEGIN
    V_DATE := LAST_DAY(TO_DATE(I_MON, 'YYYYMM'));
    V_NUM  := TO_NUMBER(TO_CHAR(V_DATE, 'DD'));
  EXCEPTION
    WHEN OTHERS THEN
      RAISE_APPLICATION_ERROR(-20010, '导入月份有误！');
      ROLLBACK;
      O_RETURN := '导入月份有误！';
      RETURN;
  END;

  --清除原有数据
  DELETE TKQ01_ATTENDANCE WHERE amonth  = I_MON  AND imp_num = I_NUM ;

  --循环开始值
  V_BEG := (TO_NUMBER(I_NUM) - 1) * 10;

  --循环结束值
  IF I_NUM < 3 THEN
    V_COUNT := 10;
  ELSE
    V_COUNT := V_NUM - 20;
  END IF;

  --按员工处理考勤记录
  FOR EXT IN (SELECT C1, MAX(C2) C2
                FROM PBPARATEMP
               WHERE C35 = I_MON
                 AND C36 = I_NUM
               GROUP BY C1
               ORDER BY C1) LOOP

    BEGIN
      --当前员工时间段内考勤信息写入
      FOR I IN 1 .. V_COUNT LOOP
        V_IMP := NULL;

        BEGIN
          EXECUTE IMMEDIATE 'SELECT MIN(C' || TO_CHAR(I+2) || ') ,MAX(C' || TO_CHAR(I+2) || '),
                            SUM(CASE WHEN C' || TO_CHAR(I+2) || ' IS NULL THEN 0 ELSE 1 END),
                            CONNSTR(C' || TO_CHAR(I+2) || ') FROM PBPARATEMP WHERE C1 = :1 AND C35 = :2 AND C36 = :3'
            INTO V_ARR, V_LEAVE, V_IMP.PUNCHNUM, V_IMP.PUNCHDETAIL
          -- 上班时间  ,下班时间  ,打卡次数 , 打卡明细
            USING EXT.C1,I_MON,I_NUM;
        END;

        V_IMP.AMONTH := I_MON; -- 考勤月份
        V_IMP.ADATE  := TO_DATE(I_MON || TO_CHAR(I + V_BEG ), 'YYYYMMDD'); -- 考勤日期
        V_IMP.OPERID := EXT.C1; -- 员工ID
        V_IMP.OPERNM := EXT.C2; -- 员工姓名

        -- 上班时间8:30  下班时间 17:00
        IF V_IMP.PUNCHNUM = 1 THEN
          V_IMP.ARR_TIME   := TO_DATE( I_MON || TO_CHAR(I+V_BEG,'00') ||V_ARR,'YYYYMMDDHH24MI');   -- 上班时间
          V_IMP.LEAVE_TIME := NULL;  -- 下班时间

          IF V_ARR > '0830' THEN
             V_IMP.LATECOUNT  := FLOOR(TO_NUMBER( V_IMP.ARR_TIME - TO_DATE( I_MON || TO_CHAR(I+V_BEG,'00') ||'0830','YYYYMMDDHH24MI'))*24*60) ; -- 迟到时长(分钟)
          END IF;
        ELSIF V_IMP.PUNCHNUM >= 2 THEN
          V_IMP.ARR_TIME   := TO_DATE( I_MON || TO_CHAR(I+V_BEG,'00') ||V_ARR,'YYYYMMDDHH24MI');   -- 上班时间
          V_IMP.LEAVE_TIME := TO_DATE( I_MON || TO_CHAR(I+V_BEG,'00') ||V_LEAVE,'YYYYMMDDHH24MI');  -- 下班时间

          IF V_ARR > '0830' THEN
             V_IMP.LATECOUNT  := FLOOR(TO_NUMBER( V_IMP.ARR_TIME - TO_DATE( I_MON || TO_CHAR(I+V_BEG,'00') ||'0830','YYYYMMDDHH24MI'))*24*60) ; -- 迟到时长(分钟)
          END IF;
          IF V_LEAVE < '1700' THEN
             V_IMP.leavecount  := FLOOR(TO_NUMBER( TO_DATE( I_MON || TO_CHAR(I+V_BEG,'00') ||'1700','YYYYMMDDHH24MI') - V_IMP.LEAVE_TIME)*24*60) ; -- 早退时长(分钟)
          END IF;
       END IF;

        V_IMP.IMP_NUM     := I_NUM; -- 导入次数
        V_IMP.WEEK        := substr(to_char(V_IMP.ADATE,'day'),3); -- 星期
        V_IMP.USEFLG      := '1'; -- 有效标记
        V_IMP.IMP_DATE    := SYSDATE; -- 导入日期
        V_IMP.UPDATE_TIME := NULL; -- 更新时间
        V_IMP.UPDATOR     := I_OPER; -- 更新人

        BEGIN
          INSERT INTO TKQ01_ATTENDANCE VALUES V_IMP;
        EXCEPTION
          WHEN OTHERS THEN
            RAISE_APPLICATION_ERROR(-20010, '写入考勤明细失败！');
            ROLLBACK;
            O_RETURN := '写入考勤明细失败！';
            RETURN;
        END;
      END LOOP;
    END;

  END LOOP;

  -------------------------
  O_RETURN := 'OK';
  -------------------

EXCEPTION
  WHEN OTHERS THEN
    O_RETURN := SQLCODE || SQLERRM;

END;
