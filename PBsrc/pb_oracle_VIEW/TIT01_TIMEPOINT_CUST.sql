SELECT c.custcd, a.timepoint, a.beforetm, a.aftertm, a.useflg FROM CCGL.TMM22_CUSTOMERS c JOIN CCGL.TIT01_TIMEPOINT_AREA a ON 1 = 1 AND a.levels = c.levels WHERE c.useflg = '1' AND a.useflg = '1'
