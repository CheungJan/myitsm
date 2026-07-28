select 'temp_case_item_v_table',count(*)  from temp_case_item_v_table
union all
select 'temp_case_step_v_table',count(*)  from temp_case_step_v_table
union all
select 'temp_data_case_relationship',count(*) from temp_data_case_relationship
union all
select 'temp_data_case_step' ,count(*)  from temp_data_case_step
union all
select 'temp_asset_change_v_table' ,count(*)  from temp_asset_change_v_table

