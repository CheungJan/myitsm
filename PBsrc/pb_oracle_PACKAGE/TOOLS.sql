package tools is
  -- public constant declarations
  errcode constant integer := -20012;

  function fmidn(p_str in varchar2,p_sep in varchar2) return integer;
  function fmid(p_str in varchar2,p_n in number,p_null in char,p_sep in varchar2) return varchar2;
end tools;
