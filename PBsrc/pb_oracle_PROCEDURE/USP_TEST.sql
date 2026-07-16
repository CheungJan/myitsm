procedure usp_test
(  as_return out varchar2)

as

v_date date;

begin
v_date:=sysdate;
/*
for  c_1 in(select id from tmp_sm_in_open_result)
loop

update sm_in_open_result@itsm
set sys_status=2
where id=c_1.id;
end loop;
*/

/*
update sm_in_open_result@itsm
set sys_status=2
where id in (select id from tmp_sm_in_open_result);
*/

update sm_in_open_result@itsm  a
set sys_status=2--,insert_time=v_date
where sys_status=1;



update sm_in_part_change@itsm  a
set sys_status=2--,insert_time=v_date
where sys_status=1;


-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
