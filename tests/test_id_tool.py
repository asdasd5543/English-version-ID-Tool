import importlib.util
from datetime import datetime
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def load_id_tool(script_name):
    script_path = REPOSITORY_ROOT / script_name
    spec = importlib.util.spec_from_file_location("id_tool", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(params=["id-tool-v1.0.0-en.py", "id-tool-v1.0.1-en.py"])
def id_tool(request):
    return load_id_tool(request.param)


def test_calculate_check_digit_returns_expected_value(id_tool):
    assert id_tool.calculate_check_digit("11000020000101123") == "0"


@pytest.mark.parametrize("value", ["", "123", "1100002000010112X", "1" * 18])
def test_calculate_check_digit_rejects_invalid_input(id_tool, value):
    with pytest.raises(ValueError):
        id_tool.calculate_check_digit(value)


def test_random_id_sequence_generates_requested_number_of_valid_samples(id_tool):
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2000, 1, 3)
    samples = list(
        id_tool.random_id_sequence(
            ["110000"],
            start_date,
            end_date,
            5,
        )
    )

    assert len(samples) == 5
    for full_id, birthday, area_code in samples:
        assert len(full_id) == 18
        assert area_code == "110000"
        birthday_date = None
        for date_format in ("%Y-%m-%d", "%Y年%m月%d日"):
            try:
                birthday_date = datetime.strptime(birthday, date_format)
                break
            except ValueError:
                continue
        assert birthday_date is not None
        assert start_date <= birthday_date < end_date
        assert id_tool.calculate_check_digit(full_id[:17]) == full_id[-1]


def test_random_id_sequence_rejects_empty_area_code_list(id_tool):
    with pytest.raises(ValueError, match="No area codes provided"):
        list(
            id_tool.random_id_sequence(
                [],
                datetime(2000, 1, 1),
                datetime(2000, 1, 2),
                1,
            )
        )
