FUNCTION getFirstPy(p_cnStr in varchar2) return varchar2 is
        i        number(12);
        lv_spell varchar2(100);
        lv_char  varchar2(100);
        li_bytes number(12);
        lv_temp  varchar2(100);
    begin
        lv_spell := '';
        for i in 1 .. length(p_cnStr) loop

            lv_char := substr(p_cnStr,
                              i,
                              1);
            if lengthb(lv_char) = 1 then
                lv_spell := lv_spell || lower(lv_char);
            else
                Select ascii(lv_char) - 256 * 256
                  Into li_bytes
                  From dual;
                case
                    when li_bytes between - 20319 and - 20284 then
                        lv_temp := 'a';
                    when li_bytes between - 20283 and - 19776 then
                        lv_temp := 'b';
                    when li_bytes between - 19775 and - 19219 then
                        lv_temp := 'c';
                    when li_bytes between - 19218 and - 18711 then
                        lv_temp := 'd';
                    when li_bytes between - 18710 and - 18527 then
                        lv_temp := 'e';
                    when li_bytes between - 18526 and - 18240 then
                        lv_temp := 'f';
                    when li_bytes between - 18239 and - 17923 then
                        lv_temp := 'g';
                    when li_bytes between - 17922 and - 17418 then
                        lv_temp := 'h';
                    when li_bytes between - 17417 and - 16475 then
                        lv_temp := 'j';
                    when li_bytes between - 16474 and - 16213 then
                        lv_temp := 'k';
                    when li_bytes between - 16212 and - 15641 then
                        lv_temp := 'l';
                    when li_bytes between - 15640 and - 15166 then
                        lv_temp := 'm';
                    when li_bytes between - 15165 and - 14923 then
                        lv_temp := 'n';
                    when li_bytes between - 14922 and - 14915 then
                        lv_temp := 'o';
                    when li_bytes between - 14914 and - 14631 then
                        lv_temp := 'p';
                    when li_bytes between - 14630 and - 14150 then
                        lv_temp := 'q';
                    when li_bytes between - 14149 and - 14091 then
                        lv_temp := 'r';
                    when li_bytes between - 14090 and - 13319 then
                        lv_temp := 's';
                    when li_bytes between - 13318 and - 12839 then
                        lv_temp := 't';
                    when li_bytes between - 12838 and - 12557 then
                        lv_temp := 'w';
                    when li_bytes between - 12556 and - 11848 then
                        lv_temp := 'x';
                    when li_bytes between - 11847 and - 11056 then
                        lv_temp := 'y';
                    when li_bytes between - 11055 and - 10002 then
                        lv_temp := 'z';

        ----如果ascii码找不到 则查询字库
                    else

                        begin
                            lv_temp := lower(PG_PUB_GETPINYINBYHANZI.GetHzPYCAP(lv_char));

                        exception
                            when others then
                                lv_temp := lv_char;
                        end;
                        if lv_temp is null then
                            lv_temp := lv_char;
                        end if;
                end case;
                lv_spell := lv_spell || substr(lv_temp,
                                               1,
                                               1);
                /*
                select max(v1) Into lv_temp from rm.t_cnc_tmp
                    where li_bytes between to_number(v2) and to_number(v3);
                  if lv_temp is not null then
                    lv_spell:=lv_spell||substr(lv_temp,1,1);
                  else
                     lv_spell:=lv_spell||lv_char;
                  end if;*/

            end if;
        end loop;
        return upper(lv_spell);
    end;
