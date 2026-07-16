select inbillid,decode (invtyp,'1','采购入库','2','质检入库','3','维护入库','4','生产入库',
'5','返修入库','6','外借入库','7','调拨入库','8','销售退库','9','生产退库','S','销售撤消'),tmc13_users.usernm
from twh13_in
left outer join tmc13_users
on  twh13_in.opercd=tmc13_users.usercd

union all
---------invtyp  1:退货出库 2:质检出库3: 维护出库 4:生产出库 5：返修出库6：外借出库 7：调拨出库 8:销售出库 9 领用出库 s销售出库

select outbillid,decode (invtyp,'1','退货出库','2','质检出库','3','维护出库','4','生产出库',
'5','返修出库','6','外借出库','7','调拨出库','8','销售出库','9','领用出库','S','销售出库'),tmc13_users.usernm
from twh15_out
left outer join tmc13_users
on  twh15_out.opercd=tmc13_users.usercd
union all


select olbillid,decode(olsign,'0','损','1','溢'),tmc13_users.usernm
from twh17_overlost
left outer join tmc13_users
on  twh17_overlost.opercd=tmc13_users.usercd

