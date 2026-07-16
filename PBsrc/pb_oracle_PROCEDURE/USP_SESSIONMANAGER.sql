PROCEDURE usp_SessionManager(in_Opercd  in varchar2,
                                               in_Process in varchar2,
                                               in_UseFLG  in varchar2,
                                               out_Result out varchar2) as
  /*
  过程说明：
  过程名称：usp_SessionManager
  参数：
      输入参数：
        in_Opercd 操作员
        in_Process 进程号
        in_UseFLG  进入系统标志
      输出参数：
        out_Result '0'成功 '-1' 失败
  功能说明：根据不同的用户登陆创建不同的全局临时表，临时表涉及到三个列
  分别为登陆用户、登陆时间、登陆标志
  作者：吴军  日期：2007-07-20
  */
  ai_i       int;
  ai_process int;
  as_alllogon varchar(2);
begin

  out_Result := '-1';
  ai_i       := 0;
  --根据系统参数是否控制相同用户同时登陆
  select  a.allowmultilogon into as_alllogon from tmc71_sysparm a ;

  /*
  as_alllogon '0'不允许,'1'允许
  */
  if as_alllogon = '0' then
  if in_UseFLG = '1' then
    insert into tmc_all_sessionmanager
      (usercd, loarddt, loardflg, seqno, loardprocess)
    values
      (in_Opercd, sysdate, '1', tmc_sessionmanager_seq.nextval, in_Process);

    for c_process in (select a.LOARDPROCESS
                        from tmc_all_sessionmanager a
                       where trim(a.usercd) = trim(in_Opercd)) loop

      select count(1)
        into ai_process
        from v$session
       where username = 'FYGL' and process = c_process.LOARDPROCESS;
      if ai_process > 0 then
        ai_i := ai_i + 1;
      end if;
    end loop;

    if ai_i = 1 then
      out_Result := '0';
    end if;
  end if;

  if in_UseFLG = '-1' then
    delete from tmc_all_sessionmanager
     where trim(usercd) = trim(in_Opercd);
    out_Result := '0';
  end if;
  end if;


  out_Result := '0';

EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK;
    out_result := SUBSTR(SQLERRM(), 1, 100);
END usp_SessionManager;
