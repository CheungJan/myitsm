PROCEDURE usp_wh_out_allocate_fix
(as_typ CHAR, as_id CHAR, as_user CHAR, as_return OUT VARCHAR2)
AS
    v_typ CHAR(1);
    v_id CHAR(8);
    v_user CHAR(6);
    v_optyp CHAR(1);
    v_whcd CHAR(2);
    v_inbillid CHAR(8);
    v_detail_count NUMBER;
BEGIN
    v_typ := as_typ;
    v_id := as_id;
    v_user := as_user;
    as_return := 'OK';

    -- 只处理调拨出库类型 
    IF v_typ <> '7' THEN
        as_return := 'Error: Only for allocate out (typ=7)';
        RETURN;
    END IF;

    -- 获取出库单信息 
    SELECT DECODE(optyp, 'PC', '0', 'ID', '1', 'err'), targetwhcd
    INTO v_optyp, v_whcd
    FROM twh15_out
    WHERE outbillid = v_id;

    IF v_optyp = 'err' THEN
        as_return := 'Error: Invalid optyp';
        RETURN;
    END IF;

    -- 检查是否已生成入库单（避免重复生成） 
    SELECT COUNT(*) INTO v_detail_count
    FROM twh13_in
    WHERE refbillid = v_id AND invtyp = '7' AND useflg IN ('0', '1');

    IF v_detail_count > 0 THEN
        as_return := 'Warning: Allocate in bill already exists';
        RETURN;
    END IF;

    -- 生成入库单号
    v_inbillid := uf_get_billnou('IN');

    -- 【修复1】插入入库单主表（useflg='0' 待接收）
    INSERT INTO twh13_in (
        whcd, indate, inbillid, refbillid, invtyp, ptimes, memo,
        opercd, gendate, auditflg, auditman, auditdate,
        optyp, useflg, suppcd
    )
    SELECT
        targetwhcd,      -- 目标仓库
        SYSDATE,         -- 入库日期
        v_inbillid,      -- 新生成的入库单号
        outbillid,       -- 关联出库单号
        '7',             -- 调拨入库类型
        '0',             -- 次数
        'AutoGen-WaitReceive',  -- 备注
        v_user,          -- 操作员 
        SYSDATE,         -- 生成日期
        '',              -- 审核标志（空） 
        '',              -- 审核人（空）
        NULL,            -- 审核日期（空） 
        optyp,           -- 操作类型（批次/ID） 
        '0',             -- 【修改】useflg='0' 待接收（原来是'1'） 
        ''               -- 供应商代码 
    FROM twh15_out
    WHERE outbillid = v_id;

    -- 【修复2】处理 EID 模式明细
    -- 只有当出库明细在 twh16_outdteid 表中存在时才插入
    SELECT COUNT(*) INTO v_detail_count
    FROM twh16_outdteid
    WHERE outbillid = v_id;

    IF v_detail_count > 0 THEN
        INSERT INTO twh14_checkindt (
            whcd, inbillid, lineno, itemtyp, itemcd, prddate, inqty
        )
        SELECT
            v_whcd,          -- 目标仓库
            v_inbillid,      -- 入库单号
            ROW_NUMBER() OVER (ORDER BY itemcd, prddate),  -- 行号
            itemtyp,         -- 商品属性 
            itemcd,          -- 商品代码
            prddate,         -- 批次日期
            COUNT(*)         -- 数量（EID模式按个数）
        FROM twh16_outdteid
        WHERE outbillid = v_id
        GROUP BY itemtyp, itemcd, prddate;
    END IF;

    -- 【修复3】处理批次模式明细 
    -- 只有当出库明细在 twh16_outdtprd 表中存在时才插入
    SELECT COUNT(*) INTO v_detail_count
    FROM twh16_outdtprd
    WHERE outbillid = v_id;

    IF v_detail_count > 0 THEN
        INSERT INTO twh14_checkindt (
            whcd, inbillid, lineno, itemtyp, itemcd, prddate, inqty
        )
        SELECT
            v_whcd,          -- 目标仓库
            v_inbillid,      -- 入库单号
            ROW_NUMBER() OVER (ORDER BY itemcd, prddate),  -- 行号
            itemtyp,         -- 商品属性 
            itemcd,          -- 商品代码
            prddate,         -- 批次日期
            outqty           -- 数量（批次模式直接取outqty） 
        FROM twh16_outdtprd
        WHERE outbillid = v_id;
    END IF;

    -- 【修复4】删除：不再自动调用 usp_wh_in
    -- 原来：usp_wh_in('7', v_inbillid, 'SYS', as_return);
    -- 改为：等待用户在调拨入库窗口确认后手工调用 

    -- 【修复5】暂不更新 tmm43_eid，确认接收后再更新 
    -- 原来：UPDATE tmm43_eid ...
    -- 改为：在确认接收时更新 

    -- 验证明细是否生成成功
    SELECT COUNT(*) INTO v_detail_count
    FROM twh14_checkindt
    WHERE inbillid = v_inbillid;

    IF v_detail_count = 0 THEN
        -- 如果明细生成失败，回滚主表插入 
        DELETE FROM twh13_in WHERE inbillid = v_inbillid;
        as_return := 'Error: No detail generated for allocate in bill ' || v_inbillid;
        RETURN;
    END IF;

    as_return := 'OK-Generated:' || v_inbillid;

EXCEPTION
    WHEN OTHERS THEN
        -- 发生异常时清理已插入的数据 
        DELETE FROM twh13_in WHERE inbillid = v_inbillid;
        DELETE FROM twh14_checkindt WHERE inbillid = v_inbillid;
        as_return := 'Error:' || SQLCODE || '-' || SQLERRM;
END;
