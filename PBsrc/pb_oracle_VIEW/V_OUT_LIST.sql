select
'设备变更',PLAN_NO, SM_NO ,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from O_TF_IN_ASSET_CHANGE
union all
select
'磁卡变更' ,PLAN_NO, SM_NO ,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from O_TF_IN_LOCATION_CHANGE
union all
select
'门店关闭',PLAN_NO, SM_NO ,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from   O_TF_IN_LOCATION_CLOSE
union all
select
'门店搬迁',PLAN_NO, SM_NO ,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from   O_TF_IN_LOCATION_MOVE
union all
select
'旧机翻新',PLAN_NO, SM_NO ,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from  O_TF_IN_ASSET_RETREAD
union all
select
'门店新开',PLAN_NO, SM_NO ,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from  O_TF_IN_LOCATION_OPEN
union all
select
'有限公司',name,SM_NO, to_char(INSERT_TIMe,'yyyy-mm-dd'),SYs_STATUS,checkflg from O_tf_in_customer

union all
select
'门店信息' ,name,SM_NO,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from O_tf_in_location


union all
select
'POS信息' ,name,serialno,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from O_tf_in_asset

union all
select
'配件信息' ,name,part_serialno,to_char(INSERT_TIME,'yyyy-mm-dd'),sys_status,checkflg from O_tf_in_part

