PROCEDURE SP_ITSM_DATAMOVE(O_RETURN OUT VARCHAR2)

 AS
  V_COUNT    NUMBER := 0;
  V_GROUP    NUMBER(3);
  V_NUM      NUMBER;
  V_MIDCURR  VARCHAR2(10);
  V_MD       TIT10_MAINTENANCEDAY%ROWTYPE; --日常维护单
  V_DISPATCH TIT21_MAINTENANCE_DISPATCH%ROWTYPE; --派单表
  V_D2D      TIT23_MAINTENANCE_D2D%ROWTYPE; --上门记录
  V_RV       TIT24_MAINTENANCE_RV%ROWTYPE; --回访表
  V_ACCUP    TIT25_ACCESSORIES_UPDATE%ROWTYPE; --配件更换表

  --  V_QY_WHD SJQY_WHD%ROWTYPE; --ITSM WHD
  V_QY_D2D SJQY_D2D%ROWTYPE; --ITSM 派单 上门 关单
  V_QY_RV  SJQY_RV%ROWTYPE; --ITSM 回访
  V_QY_ACC SJQY_ACC%ROWTYPE; --ITSM 换配件

  CURSOR C_D2DINFO(IN_MID IN VARCHAR2) IS
    SELECT * FROM SJQY_D2D WHERE MID = IN_MID ORDER BY MID, CREATE_TIME;

  CURSOR C_RVINFO(IN_MID IN VARCHAR2) IS
    SELECT * FROM SJQY_RV WHERE MID = IN_MID;

BEGIN
  FOR V_QY_WHD IN (SELECT T.*, C.CUSTCD, C.CLASSCD
                     FROM SJQY_WHD T, TMM22_CUSTOMERS C
                    WHERE T.CUSTCARD = C.CUSTCARD /* AND T.MID='MDA07100'*/
                    ORDER BY T.MID) LOOP
    V_COUNT   := V_COUNT + 1;
    V_GROUP   := 1;
    V_MD      := NULL;
    V_NUM     := 2;
    V_MIDCURR := V_QY_WHD.MID;

    V_MD.MAINTENANCE_ID           := V_QY_WHD.MID; --维护单ID
    V_MD.COMPANY_ID               := V_QY_WHD.CLASSCD; --所属区域公司ID
    V_MD.STORE_ID                 := V_QY_WHD.CUSTCD; --门店ID
    V_MD.TEMP_CONTRACT            := V_QY_WHD.TEMP_CONTRACT; --临时联系电话
    V_MD.FAULT_TYPE               := '1'; --故障类型   1 pos 2 视频
    V_MD.SERVRITY                 := V_QY_WHD.SERVRITY; --严重程度
    V_MD.EMERGENCY_LEVEL          := V_QY_WHD.EMERGENCY_LEVEL; --紧急程度
    V_MD.PRIORITY                 := V_QY_WHD.PRIORITY; --优先级
    V_MD.REQUESTER                := NULL; --请求人员
    V_MD.REQUEST_TIME             := V_QY_WHD.REQUEST_TIME; --请求时间
    V_MD.EXPECTED_COMPLETION_TIME := V_QY_WHD.EXPECTED_COMPLETION_TIME; --合同要求完成时间
    V_MD.DELIVER_NO               := NULL; --送货单号
    V_MD.SHORT_DESCRIPTION        := SUBSTR(V_QY_WHD.SHORT_DESCRIPTION,
                                            0,
                                            30) || '|' ||
                                     V_QY_WHD.MAINTENANCE_ID; --故障简述
    V_MD.DETAIL_DESCRIPTION       := SUBSTR(V_QY_WHD.DETAIL_DESCRIPTION,
                                            0,
                                            100); --详细描述
    V_MD.DEVICE_ID                := V_QY_WHD.DEVICE_ID; --故障设备编号

    IF V_QY_WHD.CURRENT_STATUS = '已取消' THEN
      V_MD.CURRENT_STATUS := '9'; --当前状态 (默认值)
    ELSE
      V_MD.CURRENT_STATUS := '1'; --当前状态 (默认值)
    END IF;

    --    V_MD.IS_SUCCESS     := V_QY_WHD.; --成功标志
    IF V_QY_WHD.IS_OLD = '1' THEN
      V_MD.IS_OLD := 'Y'; --是否补单
    ELSE
      V_MD.IS_OLD := 'N'; --是否补单
    END IF;
    V_MD.FAULTCODE   := NULL; --故障编码
    V_MD.CREATE_TIME := V_QY_WHD.CREATE_TIME; --创建时间

    V_MD.CREATOR := V_QY_WHD.CREATORNM; --创建人

    V_MD.UPDATE_TIME  := NULL; --更新时间
    V_MD.UPDATOR      := NULL; --更新人
    V_MD.FIRSTOR      := NULL; --第一次上门工程师ID   (后面回填)
    V_MD.FIRST_TIME   := V_QY_WHD.FIRST_TIME; --第一次上门时间
    V_MD.LEAVE_TIME   := V_QY_WHD.LEAVE_TIME; --第一次离店时间
    V_MD.CLOSE_TIME   := V_QY_WHD.CLOSE_TIME; --关单时间
    V_MD.REVISIT_TIME := NULL; --回访时间  (后面回填)
    V_MD.IS_ARCHIVE   := NULL; --是否归档  (后面回填)

    -- 派单 上门  关单
    OPEN C_D2DINFO(V_QY_WHD.MID);
    LOOP
      FETCH C_D2DINFO
        INTO V_QY_D2D;
      EXIT WHEN C_D2DINFO%NOTFOUND OR C_D2DINFO%NOTFOUND IS NULL;
      V_QY_ACC     := NULL;
      V_D2D        := NULL;
      V_DISPATCH   := NULL;

      --分派
      IF V_QY_D2D.ACTION = 7 AND V_QY_D2D.D2D_ENGINEER IS NOT NULL THEN
        V_DISPATCH.MAINTENANCE_ID        := V_QY_D2D.MID; --维护单ID
        V_DISPATCH.BUSINESS_OPERATION_ID := V_NUM; --业务操作流水表ID
        V_DISPATCH.MAINTENANCE_TYPE      := NULL; --维护类型
        V_DISPATCH.OPERATOR              := V_QY_D2D.CREATORNM; --操作人
        V_DISPATCH.ACCPECTD_GROUP        := 'A1'; --分派组

        V_DISPATCH.ACCPECTDER := V_QY_D2D.D2D_ENGINEER; --分派人

        V_DISPATCH.DISPATCH_TIME := V_QY_D2D.CREATE_TIME; --分派时间
        V_DISPATCH.CREATE_TIME   := V_QY_D2D.CREATE_TIME; --创建时间
        V_DISPATCH.CREATOR       := V_QY_D2D.D2D_ENGINEER; --创建人
        V_DISPATCH.UPDATE_TIME   := NULL; --更新时间
        V_DISPATCH.UPDATOR       := NULL; --更新人

        INSERT INTO TIT21_MAINTENANCE_DISPATCH VALUES V_DISPATCH;
        V_NUM := V_NUM + 1;

        V_MD.CURRENT_STATUS := '2'; --当前状态
      END IF;

      --上门
      IF V_QY_D2D.ACTION = 12 THEN
        --到店

        IF V_GROUP = 1 THEN
          V_MD.FIRSTOR := V_QY_D2D.D2D_ENGINEER; --第一次上门工程师ID   (回填)
        END IF;

        V_D2D.MAINTENANCE_ID        := V_QY_D2D.MID; --维护单ID
        V_D2D.BUSINESS_OPERATION_ID := V_NUM; --业务操作流水表ID
        V_D2D.D2D_ENGINEER          := V_QY_D2D.D2D_ENGINEER; --上门工程师
        V_D2D.ARRIVE_TIME           := V_QY_D2D.ARRIVE_TIME; --到达时间
        V_D2D.LEAVE_TIME            := NULL; --离店时间
        V_D2D.JJBZ                  := NULL; --解决标志
        V_D2D.D2D_DESCRIPITON       := NULL; --处理过程描述
        V_D2D.D2D_GROUP             := V_GROUP; --分组
        V_D2D.D2D_TYPE              := '1'; --类型(到店,离店)
        V_D2D.CREATE_TIME           := V_QY_D2D.CREATE_TIME; --创建时间
        V_D2D.CREATOR               := V_QY_D2D.CREATORNM; --创建人
        V_D2D.USEFLG                := V_QY_D2D.USEFLG; --有效状态
        INSERT INTO TIT23_MAINTENANCE_D2D VALUES V_D2D;
        V_NUM := V_NUM + 1;

        --离店
        IF V_QY_D2D.LEAVE_TIME IS NOT NULL THEN
          V_D2D.MAINTENANCE_ID        := V_QY_D2D.MID; --维护单ID
          V_D2D.BUSINESS_OPERATION_ID := V_NUM; --业务操作流水表ID
          V_D2D.D2D_ENGINEER          := V_QY_D2D.D2D_ENGINEER; --上门工程师
          V_D2D.ARRIVE_TIME           := NULL; --到达时间
          V_D2D.LEAVE_TIME            := V_QY_D2D.LEAVE_TIME; --离店时间
          IF INSTR(V_QY_D2D.D2D_DESCRIPITON, '<失败>') > 0 THEN
            V_D2D.JJBZ          := '4'; --解决标志(失败)
            V_MD.CURRENT_STATUS := '4'; --当前状态
          ELSE
            V_D2D.JJBZ          := '5'; --解决标志(成功)
            V_MD.CURRENT_STATUS := '5'; --当前状态
          END IF;
          V_D2D.D2D_DESCRIPITON := SUBSTR(V_QY_D2D.D2D_DESCRIPITON, 0, 100); --处理过程描述
          V_D2D.D2D_GROUP       := V_GROUP; --分组
          V_D2D.D2D_TYPE        := '2'; --类型(到店,离店)
          V_D2D.CREATE_TIME     := V_QY_D2D.CREATE_TIME; --创建时间
          V_D2D.CREATOR         := V_QY_D2D.CREATORNM; --创建人
          V_D2D.USEFLG          := V_QY_D2D.USEFLG; --有效状态
          INSERT INTO TIT23_MAINTENANCE_D2D VALUES V_D2D;
          V_NUM := V_NUM + 1;
        END IF;
        V_GROUP := V_GROUP + 1;
      END IF;
      --配件更换
      IF V_QY_D2D.ACTION = 15 THEN
        BEGIN
          SELECT distinct *
            INTO V_QY_ACC
            FROM SJQY_ACC A
           WHERE A.GLGX = V_QY_D2D.GLGX;

          V_ACCUP.MAINTENANCE_ID        := V_QY_D2D.MID; -- 维修单ID
          V_ACCUP.BUSINESS_OPERATION_ID := V_NUM; -- 业务流水操作表ID
          V_ACCUP.STORE_ID              := V_QY_WHD.CUSTCD; -- 门店ID
          V_ACCUP.DEVICE_ID             := V_QY_ACC.device_id; -- 整机ID
          V_ACCUP.OLD_ACCESSORIES_ID    := V_QY_ACC.OLDEID; -- 旧配件ID
          V_ACCUP.ACCESSORIES_TYPE      := V_QY_ACC.ACCTYPE; -- 配件类型名称
          V_ACCUP.NEW_ACCESSORIES_ID    := V_QY_ACC.NEWEID; -- 新配件ID
          V_ACCUP.IS_NEW                := nvl(V_QY_ACC.ISNEW, 0); -- 新配件是否为新品
          V_ACCUP.DESCRIPTION           := V_QY_ACC.MS || '|' ||
                                           V_QY_ACC.SERVICE_NO; -- 过程描述
          V_ACCUP.PRICE                 := V_QY_ACC.ccost; -- 价格
          V_ACCUP.ENGINEER_ID           := V_QY_ACC.OPER; -- 工程师ID
          V_ACCUP.IN_WH                 := nvl(V_QY_ACC.ISRK, 0); -- 是否入库
          V_ACCUP.INVFLG                := V_QY_ACC.ISINV; -- 是否开票
          V_ACCUP.RECEIPTID             := V_QY_ACC.RECEIPTNO; -- 收据号
          V_ACCUP.DELIVERYID            := V_QY_ACC.DELIVERNO; -- 送货单号
          V_ACCUP.CREATE_TIME           := V_QY_ACC.CREATED_DATE; -- 创建时间
          V_ACCUP.CREATOR               := V_QY_ACC.CREATORNM; -- 创建人
          V_ACCUP.AUDITFLG              := '1'; -- 提交标志
          INSERT INTO TIT25_ACCESSORIES_UPDATE VALUES V_ACCUP;
          V_NUM := V_NUM + 1;
        EXCEPTION
          WHEN OTHERS THEN
            V_QY_ACC := NULL;
        END;
      END IF;

      --关单 (暂不写入关单表)
      IF V_QY_D2D.ACTION = 4 THEN
        V_MD.CURRENT_STATUS := '3'; --当前状态
        V_MD.IS_SUCCESS     := '1'; --成功标志
      END IF;

    END LOOP;
    CLOSE C_D2DINFO;

    OPEN C_RVINFO(V_QY_WHD.MID);
    LOOP
      FETCH C_RVINFO
        INTO V_QY_RV;
      EXIT WHEN C_RVINFO%NOTFOUND OR C_RVINFO%NOTFOUND IS NULL;
      IF V_QY_RV.RV_OPERATOR IS NOT NULL THEN
        V_MD.REVISIT_TIME := V_QY_RV.CREATE_TIME;

        V_RV.MAINTENANCE_ID        := V_QY_RV.MID; -- 维护单ID
        V_RV.BUSINESS_OPERATION_ID := V_NUM; -- 业务操作流水表ID
        V_RV.RV_TIME               := V_QY_RV.CREATE_TIME; -- 回访时间
        V_RV.RV_OPERATOR           := SUBSTR(V_QY_RV.RV_OPERATOR, 0, 5); -- 回访人员
        V_RV.FEEDBACK              := V_QY_RV.RV_OPERATOR; -- 客户反馈
        IF V_QY_RV.SATISFACTION = 3 THEN
          V_RV.SATISFACTION := '1'; -- 满意度
        ELSE
          V_RV.SATISFACTION := '2'; -- 满意度
        END IF;
        V_RV.CREATE_TIME := V_QY_RV.CREATE_TIME; -- 创建时间
        V_RV.CREATOR     := V_QY_RV.CREATORNM; -- 创建人
        INSERT INTO TIT24_MAINTENANCE_RV VALUES V_RV;
        V_NUM := V_NUM + 1;
      END IF;

    END LOOP;
    CLOSE C_RVINFO;

    IF V_MD.CURRENT_STATUS <> '1' AND V_MD.IS_SUCCESS IS NULL THEN
      V_MD.IS_SUCCESS := '1'; --当前状态
    END IF;

    INSERT INTO TIT10_MAINTENANCEDAY VALUES V_MD;

    IF MOD(V_COUNT, 100) = 0 THEN
      COMMIT;
    END IF;

  END LOOP;
  COMMIT;

EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK;
    O_RETURN := TO_CHAR(V_COUNT) || '==>' || V_MIDCURR || '==>' || SQLCODE ||
                SQLERRM;
END;
