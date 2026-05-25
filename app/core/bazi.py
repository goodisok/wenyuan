# -*- coding: utf-8 -*-
"""八字排盘核心：历法转换、四柱、大运、纳音、十神等。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from lunar_python import Lunar, Solar

from app.core.changsheng import changsheng
from app.core.constants import DIZHI_CANGGAN, DIZHI_WUXING, TIANGAN_WUXING, WUXING_COLOR
from app.core.relations import compute_pillar_relations

Gender = Literal["male", "female"]
DateType = Literal["solar", "lunar"]

PILLAR_NAMES = ("year", "month", "day", "hour")
PILLAR_LABELS = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}


@dataclass
class BirthInput:
    date_type: DateType
    year: int
    month: int
    day: int
    hour: int
    minute: int
    gender: Gender
    is_leap_month: bool = False


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
    def validate_lunar(year: int, month: int, day: int, is_leap_month: bool = False) -> bool:
        try:
            lunar_month = -month if is_leap_month else month
            Lunar.fromYmd(year, lunar_month, day)
            return True
        except Exception:
            return False

    @classmethod
    def resolve_solar(cls, data: BirthInput) -> tuple[Solar, Lunar]:
        if data.date_type == "lunar":
            if not cls.validate_lunar(data.year, data.month, data.day, data.is_leap_month):
                raise ValueError("无效的农历日期")
            lunar_month = -data.month if data.is_leap_month else data.month
            solar_obj = Lunar.fromYmd(data.year, lunar_month, data.day).getSolar()
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
    def _canggan_list(cls, dizhi: str, shishen_list: list[str] | None = None) -> list[dict[str, str]]:
        stems = DIZHI_CANGGAN.get(dizhi, [])
        result = []
        for i, g in enumerate(stems):
            item: dict[str, str] = {
                "name": g,
                "wuxing": TIANGAN_WUXING.get(g, ""),
                "color": WUXING_COLOR.get(TIANGAN_WUXING.get(g, ""), ""),
            }
            if shishen_list and i < len(shishen_list):
                item["shishen"] = shishen_list[i]
            result.append(item)
        return result

    @classmethod
    def _build_pillar(
        cls,
        key: str,
        ganzhi: str,
        shishen: str,
        nayin: str,
        xunkong: str = "",
        hide_shishen: list[str] | None = None,
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
                "canggan": cls._canggan_list(dz, hide_shishen),
            },
        }

    @classmethod
    def _lunar_age(cls, birth_lunar: Lunar) -> int:
        now_lunar = Solar.fromDate(datetime.now()).getLunar()
        return now_lunar.getYear() - birth_lunar.getYear() + 1

    @classmethod
    def _qiyun_info(cls, yun: Any) -> dict[str, Any]:
        start_solar = yun.getStartSolar()
        years = yun.getStartYear()
        months = yun.getStartMonth()
        days = yun.getStartDay()
        direction = "顺行" if yun.isForward() else "逆行"
        desc = f"{direction}，{years}年{months}月{days}天起运，交运约 {start_solar.toYmd()}"
        return {
            "direction": direction,
            "start_years": years,
            "start_months": months,
            "start_days": days,
            "start_solar_date": start_solar.toYmd(),
            "start_year": start_solar.getYear(),
            "description": desc,
        }

    @staticmethod
    def _jieqi_str(jq_obj: Any) -> str:
        if jq_obj is None:
            return ""
        if hasattr(jq_obj, "getName"):
            return jq_obj.getName() or ""
        return str(jq_obj)

    @classmethod
    def build_chart(cls, data: BirthInput) -> dict[str, Any]:
        solar, lunar = cls.resolve_solar(data)
        ec = lunar.getEightChar()
        gender_num = 1 if data.gender == "male" else 0
        yun = ec.getYun(gender_num)

        pillar_specs = [
            ("year", ec.getYear(), ec.getYearShiShenGan(), ec.getYearNaYin(), ec.getYearXunKong(), ec.getYearShiShenZhi()),
            ("month", ec.getMonth(), ec.getMonthShiShenGan(), ec.getMonthNaYin(), ec.getMonthXunKong(), ec.getMonthShiShenZhi()),
            ("day", ec.getDay(), "日主", ec.getDayNaYin(), ec.getDayXunKong(), ec.getDayShiShenZhi()),
            ("hour", ec.getTime(), ec.getTimeShiShenGan(), ec.getTimeNaYin(), ec.getTimeXunKong(), ec.getTimeShiShenZhi()),
        ]
        pillars = [
            cls._build_pillar(key, gz, ss, ny, xk, list(hs))
            for key, gz, ss, ny, xk, hs in pillar_specs
        ]
        day_gan = ec.getDayGan()
        for p in pillars:
            p["changsheng"] = changsheng(day_gan, p["dizhi"]["name"])

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

        solar_str = (
            f"{solar.getYear()}年{solar.getMonth()}月{solar.getDay()}日 "
            f"{solar.getHour()}时{solar.getMinute()}分"
        )
        lunar_str = (
            f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月"
            f"{lunar.getDayInChinese()} {lunar.getTimeZhi()}时"
        )

        chart: dict[str, Any] = {
            "meta": {
                "gender": data.gender,
                "gender_label": "男" if data.gender == "male" else "女",
                "date_type": data.date_type,
                "is_leap_month": data.is_leap_month,
                "zodiac": lunar.getYearShengXiao(),
                "age": cls._lunar_age(lunar),
                "birth_time": {"solar": solar_str, "lunar": lunar_str},
                "day_master": ec.getDayGan(),
                "day_master_wuxing": TIANGAN_WUXING.get(ec.getDayGan(), ""),
                "day_dishi": ec.getDayDiShi(),
                "ming_gong": ec.getMingGong(),
                "shen_gong": ec.getShenGong(),
                "tai_yuan": ec.getTaiYuan(),
                "jieqi": {
                    "prev": cls._jieqi_str(lunar.getPrevJieQi()),
                    "next": cls._jieqi_str(lunar.getNextJieQi()),
                    "current_jie": lunar.getCurrentJie() or "",
                    "current_qi": lunar.getCurrentQi() or "",
                },
            },
            "pillars": pillars,
            "dayun": dayun_list,
            "xiaoyun": xiaoyun_list,
            "wuxing_stats": cls._wuxing_stats(pillars),
            "qiyun": cls._qiyun_info(yun),
        }
        chart["pillars_relations"] = compute_pillar_relations(pillars)
        from app.core.insight import build_insight

        chart["insight"] = build_insight(chart)
        return chart

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
    def _wuxing_stats(cls, pillars: list[dict[str, Any]]) -> dict[str, int | float]:
        stats: dict[str, float] = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        for p in pillars:
            for wx in (p["tiangan"]["wuxing"], p["dizhi"]["wuxing"]):
                if wx in stats:
                    stats[wx] += 1
            for cg in p["dizhi"]["canggan"]:
                wx = cg.get("wuxing", "")
                if wx in stats:
                    stats[wx] += 0.5
        return {k: int(v) if v == int(v) else v for k, v in stats.items()}
