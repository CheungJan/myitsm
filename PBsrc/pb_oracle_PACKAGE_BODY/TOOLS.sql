package body tools is
  function fmidn(p_str in varchar2,p_sep in varchar2) return integer is
  --help:
  --tools.fmidn('/123/123/123/','/')=5
  --tools.fmidn(null,'/')=0
  --tools.fmidn('','/')=0
  --tools.fmidn('null','/')=1
    i integer;
    n integer:=1;
  begin
    if trim(p_str) is null then
      return 0;
    else
      for i in 1..length(p_str)
      loop
        if substr(p_str,i,1)=p_sep then
          n := n +1;
        end if;
      end loop;
    end if;

    return n;
  end;

  function fmid(p_str in varchar2,p_n in number,p_null in char,p_sep in varchar2) return varchar2 is
  --help:
  --tools.fmid('/null/123/321/456/',2,'N','/')='null'
  --tools.fmid('/null/123/321/456/',2,'Y','/')=NULL
    vstr arr;
    vintstr varchar2(1000);
    i number;
  begin
    for i in 1..length(p_str)
    loop
      if substr(p_str,i,1)=p_sep then
         if p_null='Y' then
         if lower(vintstr)='null' then
            vintstr := null;
         end if;
         end if;
         if vstr is null then
           vstr := arr(vintstr);
         else
           vstr.extend;
           vstr(vstr.last) := vintstr;
         end if;
         vintstr := null;
      elsif i=length(p_str) then
         if vstr is null then
           vstr := arr(vintstr||substr(p_str,i,1));
         else
           vstr.extend;
           vstr(vstr.last) := vintstr||substr(p_str,i,1);
         end if;
      else
         vintstr := vintstr||substr(p_str,i,1);
      end if;
    end loop;
    return trim(vstr(p_n));
  exception when others then
    return null;
  end;

end tools;
