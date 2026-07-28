FUNCTION uf_getplan_last_srvback(
  v_palnid    IN   CHAR -- 预计话单号

)
  RETURN varchar2
AS
  as_id number ;
  as_count number ;
  ls_return       varchar2(500);
BEGIN

 select max(dtlid),count(*) into as_id ,as_count from PLAN_SERVE t
where planno=v_palnid
group by planno     ;

select
'呼叫次数：'||as_count||chr(10)||chr(13)||
'最后呼叫:'||to_char(OPDATE,'yyyy-mm-dd hh24:mm')||chr(10)||chr(13)||
'状态: '||case STATUS when '00' then '待呼出' when '01' then  '提交' when '09' then '作废'   end ||chr(10)||chr(13)||
'门店反馈:'||case SERVE_BACK when  'Y' then '同意' when 'N' then '不同意'  end ||chr(10)||chr(13)||
'反馈内容:'||SERVE_MARK
into ls_return

 from PLAN_SERVE
where dtlid=as_id ;

        return ls_return;

EXCEPTION
when others then



   RETURN '-';
END uf_getplan_last_srvback;

