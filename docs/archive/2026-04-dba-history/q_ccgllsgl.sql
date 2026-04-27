set pagesize 0 feedback off verify off heading off echo off linesize 4000 trimspool on
spool e:/project/myitsm/src/docs/db_ccgllsgl_tables.csv
select table_name from user_tables order by table_name;
spool off
spool e:/project/myitsm/src/docs/db_ccgllsgl_columns.csv
select table_name||','||column_name||','||data_type||','||data_length||','||nvl(data_precision,'')||','||nvl(data_scale,'')||','||nullable from user_tab_columns order by table_name,column_id;
spool off
exit
