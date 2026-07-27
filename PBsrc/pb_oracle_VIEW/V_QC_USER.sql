select a.usercd,a.usernm  from tmc13_users  a inner join tmc21_usergroup b
on a.usercd=b.usercd
where b.groupcd in ('07','08')
order by  a.usercd

