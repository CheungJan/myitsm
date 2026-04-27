# -*- coding: utf-8 -*-
"""
代码表服务。
文件说明：实现 TIT03_SYSCODES 代码项查询、保存与作废业务编排。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.codetable_repository import CodeTableRepository

logger = logging.getLogger(__name__)


class CodeTableService:
    """代码表服务类。"""

    def __init__(self) -> None:
        self.repo = CodeTableRepository()

    def list_codes(
        self,
        codetyp: str,
        include_invalid: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询代码项列表。"""
        if not codetyp.strip():
            return {
                "success": False,
                "error": "codetyp 不能为空",
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

        try:
            result = self.repo.list_codes(
                codetyp=codetyp.strip(),
                include_invalid=include_invalid,
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询代码项列表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

    def get_code(self, codetyp: str, codecd: str) -> Dict[str, Any]:
        """查询代码项详情。"""
        if not codetyp.strip() or not codecd.strip():
            return {"success": False, "error": "codetyp/codecd 不能为空"}

        try:
            record = self.repo.get_code(codetyp.strip(), codecd.strip())
            if not record:
                return {"success": False, "error": "代码项不存在"}
            return {"success": True, "item": record}
        except Exception as exc:
            logger.error("查询代码项详情失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def save_code(
        self,
        codetyp: str,
        codecd: str,
        codenm: str,
        opercd: str,
        useflg: str = "1",
        memo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """保存代码项。"""
        if not codetyp.strip() or not codecd.strip() or not codenm.strip():
            return {"success": False, "error": "codetyp/codecd/codenm 不能为空"}
        if not opercd.strip():
            return {"success": False, "error": "opercd 不能为空"}
        if useflg not in {"0", "1"}:
            return {"success": False, "error": "useflg 仅允许 0/1"}

        try:
            saved = self.repo.save_code(
                codetyp=codetyp.strip(),
                codecd=codecd.strip(),
                codenm=codenm.strip(),
                opercd=opercd.strip(),
                useflg=useflg,
                memo=(memo or "").strip() or None,
            )
            if not saved:
                return {"success": False, "error": "保存失败"}
            return {
                "success": True,
                "codetyp": codetyp.strip(),
                "codecd": codecd.strip(),
                "message": "代码项保存成功",
            }
        except Exception as exc:
            logger.error("保存代码项失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def invalidate_code(self, codetyp: str, codecd: str, opercd: str) -> Dict[str, Any]:
        """作废代码项。"""
        if not codetyp.strip() or not codecd.strip():
            return {"success": False, "error": "codetyp/codecd 不能为空"}
        if not opercd.strip():
            return {"success": False, "error": "opercd 不能为空"}

        try:
            updated = self.repo.invalidate_code(
                codetyp=codetyp.strip(),
                codecd=codecd.strip(),
                opercd=opercd.strip(),
            )
            if not updated:
                return {"success": False, "error": "代码项不存在或无需作废"}
            return {
                "success": True,
                "codetyp": codetyp.strip(),
                "codecd": codecd.strip(),
                "message": "代码项作废成功",
            }
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.error("作废代码项失败: %s", exc)
            return {"success": False, "error": str(exc)}
