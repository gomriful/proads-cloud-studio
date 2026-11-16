import copy
import json

import pytest

from proads import cli
from proads.config import ConfigError, expand_text, load_config, normalize, timeline, validate

SAMPLE = "configs/dream_house_meuble.json"


def minimal():
    return {
        "business": {"name": "Shop", "phone": "", "price": "100"},
        "scenes": [
            {"id": "a", "type": "color", "colors": ["#112233"], "duration": 3,
             "texts": [{"text": "{name}"}]},
            {"id": "b", "type": "color", "colors": ["#112233", "#445566"], "duration": 4,
             "transition": {"type": "slideleft", "duration": 1.0}},
        ],
    }


def test_sample_config_is_structurally_valid():
    errors, warnings = validate(load_config(SAMPLE), check_media=False)
    assert errors == []
    assert any("phone" in w for w in warnings), "a missing phone number must be reported, not invented"


def test_sample_config_matches_the_brief():
    cfg = load_config(SAMPLE)
    b = cfg["business"]
    assert b["name"] == "Dream House Meuble"
    assert b["price"] == "2950"
    assert not b["phone"], "no phone number may be invented"
    assert "مدنين" in b["address"] and "سوق ليبيا" in b["address"]
    assert set(cfg["output"]["formats"]) == {"vertical", "horizontal"}
    all_text = json.dumps(cfg, ensure_ascii=False)
    for product in ("بيت نوم", "صالون", "تلفزة", "صبابط"):
        assert product in all_text


def test_minimal_config_is_valid():
    errors, _ = validate(minimal())
    assert errors == []


def test_timeline_overlaps_scenes_by_their_transition():
    starts, total = timeline(normalize(minimal()))
    assert starts == [0.0, 2.0]
    assert total == 6.0


def test_placeholders_expand_and_empty_values_drop_the_line():
    business = {"name": "Shop", "phone": None, "price": "100"}
    assert expand_text("{name}: {price}", business)[0] == "Shop: 100"
    text, unknown, empty = expand_text("Tel {phone}", business)
    assert text is None and empty == ["phone"] and unknown == []
    assert expand_text("{nope}", business)[1] == ["nope"]


@pytest.mark.parametrize("mutate, expected", [
    (lambda c: c.pop("scenes"), "scenes"),
    (lambda c: c["business"].pop("name"), "business.name"),
    (lambda c: c["scenes"][0].update(type="gif"), "type must be one of"),
    (lambda c: c["scenes"][0].update(duration=0), "duration"),
    (lambda c: c["scenes"][0].update(colors=["red"]), "#RRGGBB"),
    (lambda c: c["scenes"][1]["transition"].update(type="spin"), "transition.type"),
    (lambda c: c["scenes"][1]["transition"].update(duration=2.5), "shorter than half"),
    (lambda c: c["scenes"][0]["texts"][0].update(text="{whatsapp}"), "placeholder {whatsapp}"),
    (lambda c: c["scenes"][0]["texts"][0].update(position="middle"), "unknown position"),
    (lambda c: c["scenes"][0]["texts"][0].update(animation={"in": "spin"}), "unknown animation"),
    (lambda c: c["scenes"][0]["texts"][0].update(start=9), "after the end of the scene"),
    (lambda c: c.update(output={"formats": ["cinema"]}), "unknown format"),
    (lambda c: c.update(output={"fps": 500}), "output.fps"),
    (lambda c: c["scenes"].append({"type": "image", "source": "media/missing.jpg"}), "file not found"),
    (lambda c: c["scenes"].append({"type": "image", "source": "README.md"}), "not a supported image type"),
    (lambda c: c.update(audio={"music": {"path": "media/missing.mp3"}}), "file not found"),
])
def test_invalid_configs_are_rejected_with_a_clear_message(mutate, expected):
    cfg = copy.deepcopy(minimal())
    mutate(cfg)
    errors, _ = validate(cfg)
    assert any(expected in e for e in errors), errors


def test_load_config_reports_json_syntax_errors(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"scenes": [}', encoding="utf-8")
    with pytest.raises(ConfigError) as exc:
        load_config(bad)
    assert "not valid JSON" in str(exc.value) and "line 1" in str(exc.value)


def test_cli_validate_exit_codes(tmp_path, capsys):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(minimal()), encoding="utf-8")
    assert cli.main(["validate", str(good)]) == 0
    broken = minimal()
    broken["scenes"][0]["type"] = "gif"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(broken), encoding="utf-8")
    assert cli.main(["validate", str(bad)]) == 2
    captured = capsys.readouterr()
    assert "type must be one of" in captured.out + captured.err
