select '磁卡' c_type, requset_paper_id ,current_status,is_success,request_time,close_time from TIT16_DEVICE_CHANGE     --磁卡号变更
union all
select '新机' c_type,requset_paper_id ,current_status,is_success,request_time,close_time from TIT13_MAINTENANCE_OPEN     -- 新机开通单
union all
select '翻新' c_type,requset_paper_id ,current_status,is_success,request_time,close_time from tit15_maintenance_renovate  --旧机翻新
union all
select case b.plantyp when '00' then '新装' when '10' then '磁卡' when '20' then '旧机'
when '30' then '回收' when '40' then '关店'  end  c_type,requset_paper_id ,current_status,is_success,request_time,close_time from TIT10_MAINTENANCEDAY a   --回收旧机
inner join   plan_cust b
on a.requset_paper_id=b.planno

union all
select '关闭' c_type,requset_paper_id ,current_status,is_success,request_time,close_time from TIT18_STORE_CLOSE  --门店关闭

