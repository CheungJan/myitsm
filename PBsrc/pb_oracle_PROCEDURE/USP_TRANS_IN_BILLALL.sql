procedure usp_trans_in_billall
( as_return out varchar2)

as

as_temp varchar2(500);
begin

insert into  case_item_v_table
select * from temp_case_item_v_table
where not exists (select * from  case_item_v_table  where case_item_v_table.id=temp_case_item_v_table.id);

insert into  case_step_v_table
select * from temp_case_step_v_table
where not exists (select * from  case_step_v_table  where case_step_v_table.id=temp_case_step_v_table.id);

insert into  data_case_relationship
select * from temp_data_case_relationship
where not exists (select * from  data_case_relationship  where data_case_relationship.id=temp_data_case_relationship.id);


insert into  data_case_step
select * from temp_data_case_step
where not exists (select * from  data_case_step  where data_case_step.id=temp_data_case_step.id);



insert into  asset_change_v_table
select * from temp_asset_change_v_table
where not exists (select * from  asset_change_v_table  where asset_change_v_table.id=temp_asset_change_v_table.id);





EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
