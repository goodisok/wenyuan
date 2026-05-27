# -*- coding: utf-8 -*-
"""断语发布：分级呈现（直断 / 结构提示 /  withheld）。"""
from __future__ import annotations

from typing import Any

from app.core.reading import publish_duanshi_tiered, publish_sanguan_tiered

# 兼容旧 import
publish_duanshi = publish_duanshi_tiered
publish_sanguan = publish_sanguan_tiered

__all__ = ["publish_duanshi", "publish_sanguan", "publish_duanshi_tiered", "publish_sanguan_tiered"]
