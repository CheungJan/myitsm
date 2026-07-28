PROCEDURE usp_itsm_trans_in(i_master_id In varchar2,
i_detail_id     In number,
i_type     In varchar2,
as_return   out varchar2)

as

v_newid varchar2(13);
v_typ number;
v_posflg varchar2(1);
Begin

---i_type = 'xz'新装
IF i_type = 'MO' THEN

  INSERT INTO tmp_sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT SM_OPEN_SEQNO.NEXTVAL , m.requset_paper_id, e.NEW_OPENING_ID, c.custcard, e.DEVICE_ID, e.CREATE_TIME,'' ,e.CREATE_TIME, e.CREATE_TIME, '1'
    FROM  TIT14_EQUIPMENT_OPEN  e,TIT13_MAINTENANCE_OPEN  m,tmm22_customers c
    WHERE e.NEW_OPENING_ID = m.NEW_OPENING_ID
    AND  c.custcd = m.STORE_ID
    AND e.new_opening_id = i_master_id
    AND e.business_operation_id = i_detail_id  ;


  INSERT INTO sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT id, plan_no, case_no, cardcode, serialno, completeddate, result, sysdate, syn_time, sys_status
    FROM    tmp_sm_in_open_result
    Where NOT Exists (SELECT * FROM sm_in_open_result Where  sm_in_open_result.case_no = tmp_sm_in_open_result.case_no);
    --旧机翻新
ELSIF i_type = 'MR' THEN
  INSERT INTO tmp_sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT SM_OPEN_SEQNO.NEXTVAL , m.requset_paper_id, e.renovate_id, c.custcard, e.new_device_id,e.CREATE_TIME,'' ,e.CREATE_TIME, e.CREATE_TIME, '1'
    FROM  TIT15_EQUIPMENT_RENOVATE  e,TIT15_MAINTENANCE_RENOVATE  m,tmm22_customers c
    WHERE e.renovate_id = m.renew_id
    AND  c.custcd = m.STORE_ID
    AND e.renovate_id = i_master_id
    AND e.business_operation_id = i_detail_id ;


  INSERT INTO sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT id, plan_no, case_no, cardcode, serialno, completeddate, result, sysdate, syn_time, sys_status
    FROM    tmp_sm_in_open_result;

ELSIF i_type = 'MD' THEN

---i_type = 'MD'日常维护

  INSERT INTO tmp_sm_in_part_change
    (id, changetype, name, serialno, model, old_name, old_serialno, old_model, case_no,
     posname ,posid ,pos_model ,insert_time, syn_time, sys_status,OPERFLG)
    SELECT
    SM_PART_SEQNO.NEXTVAL ,
    (case when posflg ='1'then 5
          when posflg ='0' and old_accessories_id is null then 1
          when posflg ='0' and new_accessories_id is null then 4 else 2 end),
    (SELECT I.ITEMNM FROM TMM12_ITEMS I,TMM43_EID E WHERE I.ITEMCD = E.ITEMCD AND E.EID = A.NEW_ACCESSORIES_ID),
    A.NEW_ACCESSORIES_ID,
    (SELECT I.ITEMCD FROM TMM12_ITEMS I,TMM43_EID E WHERE I.ITEMCD = E.ITEMCD AND E.EID = A.NEW_ACCESSORIES_ID),
    (SELECT I.ITEMNM FROM TMM12_ITEMS I,TMM43_EID E WHERE I.ITEMCD = E.ITEMCD AND E.EID = A.OLD_ACCESSORIES_ID),
    A.OLD_ACCESSORIES_ID,
    (SELECT I.ITEMCD FROM TMM12_ITEMS I,TMM43_EID E WHERE I.ITEMCD = E.ITEMCD AND E.EID = A.OLD_ACCESSORIES_ID),
    A.MAINTENANCE_ID,
    (SELECT I.ITEMNM FROM TMM12_ITEMS I,TMM43_EID E WHERE I.ITEMCD = E.ITEMCD AND E.EID = A.device_id),
    A.device_id ,
    (SELECT I.ITEMCD FROM TMM12_ITEMS I,TMM43_EID E WHERE I.ITEMCD = E.ITEMCD AND E.EID = A.device_id),
    CREATE_TIME, CREATE_TIME, '1',in_wh
    FROM TIT25_ACCESSORIES_UPDATE A
    WHERE  A.MAINTENANCE_ID = i_master_id
    AND A.BUSINESS_OPERATION_ID = i_detail_id ;

    ------更新新配件新旧状态
    begin

      select posflg,new_accessories_id ,(CASE WHEN IS_NEW ='1' THEN 12 WHEN IS_NEW ='0' THEN 3 ELSE 3 END )
             into v_posflg,v_newid,v_typ
      from  TIT25_ACCESSORIES_UPDATE
      WHERE  MAINTENANCE_ID = i_master_id
      AND BUSINESS_OPERATION_ID = i_detail_id ;

      if not v_newid is null and v_posflg ='0' then
        update tmm43_eid
        set old_degree=v_typ
        where eid= v_newid;
      end if ;

    exception
      when others then
        raise_application_error(-20010, 'itsm更新新配件状态 获取数据错误 ！');
        rollback;
        as_return := 'itsm更新新配件状态 获取数据错误！';
        return;

    end;

    update tmp_sm_in_part_change
    set tmp_sm_in_part_change.memo   =case when v_posflg = '1' then '整机更换' else uf_itsm_checkperiod_memo(old_serialno,serialno,case_no ) end
   /* where tmp_sm_in_part_change.changetype =2*/;


    INSERT INTO sm_in_part_change
      (id, changetype, name, serialno, model, old_name, old_serialno, old_model, case_no,
      insert_time, syn_time, sys_status,OPERFLG,memo )
      SELECT id, changetype, DECODE(changetype,4,posname,name), DECODE(changetype,4,POSID,serialno), DECODE(changetype,4,POS_MODEL,model),
       DECODE(changetype,1,posname,old_name),DECODE(changetype,1,POSID,old_serialno) ,DECODE(changetype,1,POS_MODEL,old_model) , case_no,
      sysdate, syn_time, '1', OPERFLG , 'ITSM系统:'||memo
      FROM tmp_sm_in_part_change ;

    if v_posflg ='1' then
      --记录新旧设备 配件明细
      insert into TIT10_POS_DETAIL
      (bill_id,sm_id ,noflg,device_id,itemcd,accessories_id,create_time,creator)
      select case_no ,ID,(case when p.posid = s.serialno then '1' else '0' end),
             p.posid,p.itemcd,p.eid,sysdate,'sys'
      from tmm44_pos_r_eid p,tmp_sm_in_part_change s
      where (p.posid = s.serialno or p.posid = s.old_serialno)
      and p.useflg = '1';
    end if;

    --i_type = 'GB'门店关闭
ELSIF i_type = 'GB'THEN
  INSERT INTO tmp_sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT SM_OPEN_SEQNO.NEXTVAL , m.requset_paper_id, m.STORE_CLOSE_ID, c.custcard,'', m.CREATE_TIME,'' ,m.CREATE_TIME, m.CREATE_TIME, '1'
    FROM  TIT18_STORE_CLOSE m,tmm22_customers c
    WHERE c.custcd = m.STORE_ID
    AND m.STORE_CLOSE_ID = i_master_id ;

  INSERT INTO sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT id, plan_no, case_no, cardcode, serialno, completeddate, result, sysdate, syn_time, sys_status
    FROM    tmp_sm_in_open_result
    Where NOT Exists (SELECT * FROM sm_in_open_result Where  sm_in_open_result.id = tmp_sm_in_open_result.id);

    --i_type = 'BG'设备变更
ELSIF i_type = 'BG'THEN
  INSERT INTO tmp_sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT SM_OPEN_SEQNO.NEXTVAL , m.requset_paper_id, m.DEVICE_CHANGE_ID, c.custcard,'', m.CREATE_TIME,'' ,m.CREATE_TIME, m.CREATE_TIME, '1'
    FROM  TIT16_DEVICE_CHANGE  m,tmm22_customers c
    WHERE  c.custcd = m.STORE_ID
    AND m.DEVICE_CHANGE_ID = i_master_id ;

  INSERT INTO sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT id, plan_no, case_no, cardcode, serialno, completeddate, result, sysdate, syn_time, sys_status
    FROM    tmp_sm_in_open_result
    Where NOT Exists (SELECT * FROM sm_in_open_result Where  sm_in_open_result.id = tmp_sm_in_open_result.id);

    --免费更换
ELSIF i_type = 'GH' THEN
  INSERT INTO tmp_sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT SM_OPEN_SEQNO.NEXTVAL , m.requset_paper_id, e.renovate_id, c.custcard, e.new_device_id,e.CREATE_TIME,'' ,e.CREATE_TIME, e.CREATE_TIME, '1'
    FROM  TIT28_FREE_REPLACE_DT  e,TIT28_FREE_REPLACE  m,tmm22_customers c
    WHERE e.renovate_id = m.renew_id
    AND  c.custcd = m.STORE_ID
    AND e.renovate_id = i_master_id
    AND e.business_operation_id = i_detail_id ;


  INSERT INTO sm_in_open_result
    (id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
    SELECT id, plan_no, case_no, cardcode, serialno, completeddate, result, sysdate, syn_time, sys_status
    FROM    tmp_sm_in_open_result;


ELSE
  ROLLBACK;
  as_return := '数据插入错误！';
  RETURN;
END IF;

as_return:= 'OK';


EXCEPTION
when others THEN
as_return:= SQLCode||sqlerrm;

END ;
