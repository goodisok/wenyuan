from app.core.ai_validate import validate_analysis


def test_collect_allowed_years_range():
    from app.core.ai_validate import collect_allowed_years

    insight = {
        "duanshi": {
            "items": [{
                "topic": "父母",
                "display_tier": "assert",
                "windows": [{"years": "2002-2011"}],
            }],
        },
        "sanguan": {"gates": []},
    }
    assert collect_allowed_years(insight) == list(range(2002, 2012))


def test_validate_year_outside_window():
    insight = {
        "duanshi": {
            "items": [{
                "topic": "父母",
                "display_tier": "assert",
                "windows": [{"years": "2002-2011"}],
            }],
        },
        "sanguan": {"gates": []},
        "citable_years": list(range(2002, 2012)),
    }
    vr = validate_analysis("父母离异约在 1995 年发生。", insight)
    assert any("1995" in w for w in vr["warnings"])


def test_validate_unpublished_marriage():
    insight = {"duanshi": {"items": []}, "sanguan": {"gates": []}}
    vr = validate_analysis("此命必离婚再婚。", insight)
    assert any("婚姻" in w for w in vr["warnings"])
