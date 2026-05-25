# -*- coding: utf-8 -*-
"""八字排盘核心：历法转换、四柱、大运、纳音、十神等。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from lunar_python import Lunar, Solar

Gender = Literal["male", "female"]
DateType = Literal["solar", "lunar"]

PILLAR_NAMES = ("year", "month", "day", "hour")
PILLAR_LABELS = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}

TIANGAN_WUXING: dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
DIZHI_WUXING: dict[str, str] = {
    "寅": "木", "卯": "木", "巳": "火", "午": "火",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
    "申": "金", "酉": "金", "亥": "水", "子": "水",
}
DIZHI_CANGGAN: dict[str, list[str]] = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"],
    "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
    "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"],
}
WUXING_COLOR: dict[str, str] = {
    "木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water",
}


@dataclass
class BirthInput:
    date_type: DateType
    year: int
    month: int
    day: int
    hour: int
    minute: int
    gender: Gender


class BaziService:
    """八字排盘服务。"""

    @staticmethod
    def validate_datetime(year: int, month: int, day: int, hour: int, minute: int) -> bool:
        try:
            datetime(year, month, day, hour, minute)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_lunar(year: int, month: int, day: int) -> bool:
        try:
            Lunar.fromYmd(year, month, day)
            return True
        except Exception:
            return False

    @classmethod
    def resolve_solar(cls, data: BirthInput) -> tuple[Solar, Lunar]:
        if data.date_type == "lunar":
            if not cls.validate_lunar(data.year, data.month, data.day):
                raise ValueError("无效的农历日期")
            solar_obj = Lunar.fromYmd(data.year, data.month, data.day).getSolar()
            solar = Solar.fromYmdHms(
                solar_obj.getYear(), solar_obj.getMonth(), solar_obj.getDay(),
                data.hour, data.minute, 0,
            )
        else:
            if not cls.validate_datetime(data.year, data.month, data.day, data.hour, data.minute):
                raise ValueError("无效的公历日期时间")
            solar = Solar.fromYmdHms(data.year, data.month, data.day, data.hour, data.minute, 0)
        return solar, solar.getLunar()

    @staticmethod
    def _stem_branch(ganzhi: str) -> tuple[str, str]:
        return ganzhi[0], ganzhi[1] if len(ganzhi) > 1 else ""

    @classmethod
    def _canggan_list(cls, dizhi: str) -> list[dict[str, str]]:
        return [
            {
                "name": g,
                "wuxing": TIANGAN_WUXING.get(g, ""),
                "color": WUXING_COLOR.get(TIANGAN_WUXING.get(g, ""), ""),
            }
            for g in DIZHI_CANGGAN.get(dizhi, [])
        ]

    @classmethod
    def _build_pillar(
        cls,
        key: str,
        ganzhi: str,
        shishen: str,
        nayin: str,
        xunkong: str = "",
    ) -> dict[str, Any]:
        tg, dz = cls._stem_branch(ganzhi)
        tg_wx = TIANGAN_WUXING.get(tg, "")
        dz_wx = DIZHI_WUXING.get(dz, "")
        return {
            "key": key,
            "label": PILLAR_LABELS[key],
            "ganzhi": ganzhi,
            "shishen": shishen,
            "nayin": nayin,
            "xunkong": xunkong,
            "tiangan": {"name": tg, "wuxing": tg_wx, "color": WUXING_COLOR.get(tg_wx, "")},
            "dizhi": {
                "name": dz,
                "wuxing": dz_wx,
                "color": WUXING_COLOR.get(dz_wx, ""),
                "canggan": cls._canggan_list(dz),
            },
        }

    @classmethod
    def build_chart(cls, data: BirthInput) -> dict[str, Any]:
        solar, lunar = cls.resolve_solar(data)
        ec = lunar.getEightChar()
        gender_num = 1 if data.gender == "male" else 0
        yun = ec.getYun(gender_num)

        pillars = [
            cls._build_pillar("year", ec.getYear(), ec.getYearShiShenGan(), ec.getYearNaYin()),
            cls._build_pillar("month", ec.getMonth(), ec.getMonthShiShenGan(), ec.getMonthNaYin()),
            cls._build_pillar("day", ec.getDay(), "日主", ec.getDayNaYin()),
            cls._build_pillar("hour", ec.getTime(), ec.getTimeShiShenGan(), ec.getTimeNaYin()),
        ]

        dayun_list: list[dict[str, Any]] = []
        for dy in yun.getDaYun():
            gz = dy.getGanZhi()
            if not gz:
                continue
            liunian = [
                {"ganzhi": ln.getGanZhi(), "year": ln.getYear(), "age": ln.getAge()}
                for ln in dy.getLiuNian()
            ]
            dayun_list.append({
                "ganzhi": gz,
                "start_year": dy.getStartYear(),
                "end_year": dy.getEndYear(),
                "start_age": dy.getStartAge(),
                "end_age": dy.getEndAge(),
                "liunian": liunian,
            })

        xiaoyun_list: list[dict[str, Any]] = []
        for dy in yun.getDaYun():
            if dy.getGanZhi():
                continue
            for xy, ln in zip(dy.getXiaoYun(), dy.getLiuNian()):
                g = xy.getGanZhi()
                xiaoyun_list.append({
                    "year": xy.getYear(),
                    "ganzhi": g,
                    "age": xy.getAge(),
                    "liunian": {
                        "ganzhi": ln.getGanZhi(),
                        "year": ln.getYear(),
                        "wuxing": cls._pillar_wuxing_summary(ln.getGanZhi()),
                    },
                })
            break

        birth_year = solar.getYear()
        current_year = datetime.now().year
        solar_str = (
            f"{solar.getYear()}年{solar.getMonth()}月{solar.getDay()}日 "
            f"{solar.getHour()}时{solar.getMinute()}分"
        )
        lunar_str = (
            f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月"
            f"{lunar.getDayInChinese()} {lunar.getTimeZhi()}时"
        )

        return {
            "meta": {
                "gender": data.gender,
                "gender_label": "男" if data.gender == "male" else "女",
                "date_type": data.date_type,
                "zodiac": lunar.getYearShengXiao(),
                "age": current_year - birth_year + 1,
                "birth_time": {"solar": solar_str, "lunar": lunar_str},
                "day_master": ec.getDayGan(),
                "day_master_wuxing": TIANGAN_WUXING.get(ec.getDayGan(), ""),
                "day_dishi": ec.getDayDiShi(),
                "ming_gong": ec.getMingGong(),
                "shen_gong": ec.getShenGong(),
                "tai_yuan": ec.getTaiYuan(),
            },
            "pillars": pillars,
            "dayun": dayun_list,
            "xiaoyun": xiaoyun_list,
            "wuxing_stats": cls._wuxing_stats(pillars),
        }

    @classmethod
    def _pillar_wuxing_summary(cls, ganzhi: str) -> str:
        tg, dz = cls._stem_branch(ganzhi)
        parts = []
        if tg in TIANGAN_WUXING:
            parts.append(TIANGAN_WUXING[tg])
        if dz in DIZHI_WUXING:
            parts.append(DIZHI_WUXING[dz])
        return "-".join(parts)

    @classmethod
    def _wuxing_stats(cls, pillars: list[dict[str, Any]]) -> dict[str, int]:
        stats = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        for p in pillars:
            for wx in (p["tiangan"]["wuxing"], p["dizhi"]["wuxing"]):
                if wx in stats:
                    stats[wx] += 1
            for cg in p["dizhi"]["canggan"]:
                wx = cg.get("wuxing", "")
                if wx in stats:
                    stats[wx] += 0.5
        return {k: int(v) if v == int(v) else v for k, v in stats.items()}
