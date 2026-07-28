select '业务回馈单','',count(*) from sm_in_open_result
where sys_status ='9'

 union all
select '配件变更单','',count(*) from sm_in_part_change
where sys_status='9'

