procedure usp_c_hs_pos
(c_itemcd varchar2, c_number number, c_type varchar2 ,c_date varchar2 , as_return out varchar2)

as
c_max number ;
c_maxid  varchar2(20);
i number  ;
---- POSid  年月（6）+（01单、02双）+流水（5）   2024120100001
begin

    select nvl( substr(max(eid),9,5),'0')  into c_maxid  from tmm43_eid
    where itemcd=  c_itemcd   and substr(eid,1,8)=c_date||c_type ;


    if c_maxid=0  then

       FOR i IN 1..c_number LOOP
         insert into tmm43_eid
                ( itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, new_old, remark, manuf_seq, old_degree, isunit )
          values
                (c_itemcd,c_date||c_type||trim(to_char(i  ,'00000')),'sys',sysdate,'1','1','S','','GA','',trunc(sysdate,'dd'),'','1','','','','1'  ) ;


       insert into tmm44_pos_r_eid
        ( posid, itemcd, eid, opercd, gendate, upddate, useflg, muitem )
        values
        (c_date||c_type||trim(to_char(i  ,'00000')),c_itemcd,c_date||c_type||trim(to_char(i  ,'00000')),'sys',sysdate,sysdate,'1','');


       END LOOP;

    else
        c_max:=cast(c_maxid as number  ) + 1 ;
        FOR i IN c_max..c_max+c_number - 1  LOOP

             insert into tmm43_eid
                ( itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, new_old, remark, manuf_seq, old_degree, isunit )
          values
                (c_itemcd,c_date||c_type||trim(to_char(i  ,'00000')),'sys',sysdate,'1','1','S','','GA','',trunc(sysdate,'dd'),'','1','','','','1'  ) ;

         insert into tmm44_pos_r_eid
        ( posid, itemcd, eid, opercd, gendate, upddate, useflg, muitem )
        values
        (c_date||c_type||trim(to_char(i  ,'00000')),c_itemcd,c_date||c_type||trim(to_char(i  ,'00000')),'sys',sysdate,sysdate,'1','');


        END LOOP;



    end if ;




-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
