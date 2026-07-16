procedure usp_check
(  as_return out varchar2)

as



begin

update o_tf_in_asset
set checkflg='1'
where checkflg='0';

update o_tf_in_part
set checkflg='1'
where checkflg='0';


update o_tf_in_asset_change
set checkflg='1'
where checkflg='0';

update O_tf_in_asset_retread
set checkflg='1'
where checkflg='0';

update o_tf_in_customer
set checkflg='1'
where checkflg='0';


update o_tf_in_location
set checkflg='1'
where checkflg='0';

update o_tf_in_location_change
set checkflg='1'
where checkflg='0';


update o_tf_in_location_close
set checkflg='1'
where checkflg='0';

update o_tf_in_location_move
set checkflg='1'
where checkflg='0';


update O_tf_in_location_open
set checkflg='1'
where checkflg='0';



-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;

