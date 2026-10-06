from datetime import datetime, timezone
import os

import pytest

from .. import Thermia
from .setup import THERMIA_TEST_URL, __mock_auth_requests, __mock_data_requests
from .utils import parse_debug_file


def __setup_heat_pump(requests_mock, test_data_file: str):
    __mock_auth_requests(requests_mock)
    __mock_data_requests(requests_mock, test_data_file)

    return Thermia("username", "password").heat_pumps[0]


def __set_device_data_last_online(requests_mock, test_data_file: str, last_online):
    absolute_path = os.path.dirname(os.path.abspath(__file__))
    device_data = parse_debug_file(f"{absolute_path}/debug_files/{test_data_file}")[
        "device_data"
    ]

    if last_online is None:
        device_data.pop("lastOnline", None)
    else:
        device_data["lastOnline"] = last_online

    requests_mock.get(
        f"{THERMIA_TEST_URL}/api/v1/InstallationsInfo",
        json={"items": [{**device_data, "id": "test-id"}]},
    )


@pytest.mark.parametrize(
    ("test_data_file", "expected_last_online_utc"),
    [
        (
            "ATEC_DHP_AQ.txt",
            datetime(2024, 12, 12, 16, 43, 29, tzinfo=timezone.utc),
        ),
        (
            "diplomat_duo_921.txt",
            datetime(2024, 10, 13, 13, 44, 16, tzinfo=timezone.utc),
        ),
        (
            "iTec_IQ.txt",
            datetime(2024, 10, 12, 17, 54, 34, tzinfo=timezone.utc),
        ),
        (
            "ncp_1024.txt",
            datetime(2024, 2, 24, 9, 14, 3, tzinfo=timezone.utc),
        ),
        (
            "ncp_1028.txt",
            datetime(2024, 1, 16, 22, 45, 34, tzinfo=timezone.utc),
        ),
    ],
)
def test_last_online_utc(requests_mock, test_data_file, expected_last_online_utc):
    heat_pump = __setup_heat_pump(requests_mock, test_data_file)

    assert heat_pump.last_online_utc == expected_last_online_utc
    assert heat_pump.last_online_utc.tzinfo == timezone.utc


def test_last_online_keeps_local_time_string(requests_mock):
    heat_pump = __setup_heat_pump(requests_mock, "iTec_IQ.txt")

    # Unchanged: the installation's local time (UTC+2 here) as a string
    assert heat_pump.last_online == "2024-10-12T19:54:34.249"


@pytest.mark.parametrize(
    ("last_online", "expected_last_online_utc"),
    [
        ("2026-10-06T14:40:03", datetime(2026, 10, 6, 14, 40, 3, tzinfo=timezone.utc)),
        (
            "2026-10-06T14:40:03.69",
            datetime(2026, 10, 6, 14, 40, 3, tzinfo=timezone.utc),
        ),
        ("2026-10-06T14:40:03Z", datetime(2026, 10, 6, 14, 40, 3, tzinfo=timezone.utc)),
        (
            "2026-10-06T14:40:03.69Z",
            datetime(2026, 10, 6, 14, 40, 3, tzinfo=timezone.utc),
        ),
        # A value with an offset is rejected rather than misread
        ("2026-10-06T16:40:03.69+02:00", None),
        ("2026-10-06T14:40:03+00:00", None),
        ("not a date", None),
        (None, None),
    ],
)
def test_last_online_utc_formats(requests_mock, last_online, expected_last_online_utc):
    heat_pump = __setup_heat_pump(requests_mock, "iTec_IQ.txt")

    __set_device_data_last_online(requests_mock, "iTec_IQ.txt", last_online)
    heat_pump.update_data()

    assert heat_pump.last_online_utc == expected_last_online_utc
