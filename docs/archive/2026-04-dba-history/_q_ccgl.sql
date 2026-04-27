set pagesize 0 feedback off verify off heading on echo off linesize 4000 trimspool on
set markup csv on delimiter ',' quote on
spool e:/project/myitsm/src/docs/?????_CCGL.csv
select table_name from user_tables order by table_name;
spool off
spool e:/project/myitsm/src/docs/??????_CCGL.csv
select table_name,column_name,data_type,data_length,data_precision,data_scale,nullable from user_tab_columns order by table_name,column_id;
spool off
exit
