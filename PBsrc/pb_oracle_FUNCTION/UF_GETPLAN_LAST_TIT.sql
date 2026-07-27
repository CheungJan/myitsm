FUNCTION uf_getplan_last_tit(
  v_palnid    IN   varCHAR2 -- 预计话单号

)
  RETURN varchar2
AS

  ls_return       varchar2(1000);
BEGIN

--c_type, requset_paper_id ,current_status,is_success,request_time,close_time
select
'请求时间:'||to_char(request_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'关单时间:'||to_char(close_time,'yyyy-mm-dd')||chr(10)||chr(13)||
'当前状态:'||case current_status when '1' then '新建' when '2' then  '分配' when '3' then '关闭' when '4' then '未解决'when '5' then   '已解决'    when '9' then   '作废'   end ||chr(10)||chr(13)||
'最终结果:'||case is_success when  '1' then '成功' when '0' then '不成功'  else  '-' end

into ls_return

 from V_TIT_SATUS
where requset_paper_id=v_palnid ;

        return ls_return;

EXCEPTION
when others then



   RETURN '-';
END uf_getplan_last_tit;
