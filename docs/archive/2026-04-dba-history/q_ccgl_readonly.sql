set heading off
set feedback off
set verify off
set echo off
set termout off
set pagesize 50000
set linesize 4000
set trimspool on
set tab off

spool e:/project/myitsm/src/docs/db_ccgl_tables.csv
select table_name from user_tables order by table_name;
spool off

spool e:/project/myitsm/src/docs/db_ccgl_columns.csv
select table_name||','||column_name||','||data_type||','||data_length||','||nvl(data_precision,'')||','||nvl(data_scale,'')||','||nullable
from user_tab_columns
order by table_name,column_id;
spool off

exit
