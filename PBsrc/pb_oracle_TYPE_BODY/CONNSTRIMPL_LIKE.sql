type body connstrImpl_like is
      static function ODCIAggregateInitialize(sctx IN OUT connstrImpl_like)
      return number is
      begin
        sctx := connstrImpl_like('',',');
        return ODCIConst.Success;
      end;
      member function ODCIAggregateIterate(self IN OUT connstrImpl_like, value IN VARCHAR2) return number is
      begin
        if self.currentstr is null then
          self.currentstr := value;
        else
          self.currentstr := self.currentstr ||currentseprator || value;
        end if;
        if length(self.currentstr)>250 then
          self.currentstr := substr(self.currentstr,1,250) ||'...';
        end if;
        return ODCIConst.Success;
      end;
      member function ODCIAggregateTerminate(self IN connstrImpl_like, returnValue OUT VARCHAR2, flags IN number) return number is
      begin
        returnValue := self.currentstr;
        return ODCIConst.Success;
      end;
      member function ODCIAggregateMerge(self IN OUT connstrImpl_like, ctx2 IN connstrImpl_like) return number is
      begin
        if ctx2.currentstr is null then
          self.currentstr := self.currentstr;
        elsif self.currentstr is null then
          self.currentstr := ctx2.currentstr;
        else
          self.currentstr := self.currentstr || currentseprator || ctx2.currentstr;
        end if;

        if length(self.currentstr)>250 then
          self.currentstr := substr(self.currentstr,1,250)||'...';
        end if;

        return ODCIConst.Success;
      end;
      end;
