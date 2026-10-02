import os

from .setup import THERMIA_TEST_URL, setup_thermia_and_perform_basic_tests
from .utils import parse_debug_file

REGISTERS_URL = f"{THERMIA_TEST_URL}/api/v1/Registers/Installations/test-id/Registers"
COOLING_GROUP_URL = f"{THERMIA_TEST_URL}/api/v1/Registers/Installations/test-id/Groups/REG_GROUP_COOLING"


def test_diplomat_duo_921(requests_mock):
    heat_pump = setup_thermia_and_perform_basic_tests(
        requests_mock,
        "diplomat_duo_921.txt",
        expected_model="Diplomat / Diplomat Duo",
        expected_model_id="DHP H/L/C 921",
        expected_available_operational_modes=[
            "OFF",
            "AUTO",
            "COMPRESSOR",
            "AUXILIARY",
            "HOT_WATER",
        ],
        expected_available_operational_statuses=[
            "COMPR",
            "BRINEPUMP",
            "RADIATORPUMP",
            "COOLING",
            "HOT_WATER",
            "HEATING",
        ],
        expected_available_power_statuses=[
            "3KW",
            "6KW",
            "9KW",
            "12KW",
            "15KW",
        ],
    )

    # No REG_GROUP_COOLING at all
    assert heat_pump.cooling_switch_state is None
    assert heat_pump.cooling_temperature is None
    assert heat_pump.cooling_operational_time is None


def test_itec_iq(requests_mock):
    heat_pump = setup_thermia_and_perform_basic_tests(
        requests_mock,
        "iTec_IQ.txt",
        expected_model="iTec",
        expected_model_id="IQ",
        expected_available_operational_modes=[
            "OFF",
            "AUTO",
            "COMPRESSOR",
            "AUXILIARY",
            "HOT_WATER",
        ],
        expected_available_operational_statuses=[
            "COMPR",
            "RADIATORPUMP",
            "HOT_WATER",
            "HEATING",
            "DEFROST",
            "POOL",
            "COOLING",
        ],
        expected_available_power_statuses=[],
        expected_operational_status_pid_value=50,
    )

    # Empty REG_GROUP_COOLING
    assert heat_pump.cooling_switch_state is None
    assert heat_pump.cooling_temperature is None
    assert heat_pump.cooling_operational_time == 59


def test_ncp_1024(requests_mock):
    setup_thermia_and_perform_basic_tests(
        requests_mock,
        "ncp_1024.txt",
        expected_model="NCP 1024",
        expected_model_id="NCP 1024",
        expected_available_operational_modes=["OFF", "AUX_HEATER_ONLY", "AUTO"],
        expected_is_operation_mode_read_only=True,
        expected_available_operational_statuses=[
            "STATUS_MANUAL",
            "STATUS_DEFROST",
            "STATUS_HOTWATER",
            "STATUS_HEAT",
            "STATUS_COOL",
            "STATUS_POOL",
            "STATUS_LEGIONELLA",
            "STATUS_PASSIVE_COOL",
            "STATUS_STANDBY",
            "STATUS_NO_DEMAND",
            "OPERATION_MODE_OFF",
        ],
        expected_available_power_statuses=[],
    )


def test_ncp_1028(requests_mock):
    setup_thermia_and_perform_basic_tests(
        requests_mock,
        "ncp_1028.txt",
        expected_model="NCP 1028",
        expected_model_id="NCP 1028",
        expected_available_operational_modes=["OFF", "AUX_HEATER_ONLY", "AUTO"],
        expected_is_operation_mode_read_only=True,
        expected_available_operational_statuses=[
            "STATUS_MANUAL",
            "STATUS_DEFROST",
            "STATUS_HOTWATER",
            "STATUS_HEAT",
            "STATUS_COOL",
            "STATUS_POOL",
            "STATUS_LEGIONELLA",
            "STATUS_PASSIVE_COOL",
            "STATUS_STANDBY",
            "STATUS_NO_DEMAND",
            "OPERATION_MODE_OFF",
        ],
        expected_available_power_statuses=[],
    )


def test_atec_dhp_aq(requests_mock):
    heat_pump = setup_thermia_and_perform_basic_tests(
        requests_mock,
        "ATEC_DHP_AQ.txt",
        expected_model="ATEC",
        expected_model_id="DHP AQ",
        expected_available_operational_modes=[
            "OFF",
            "AUTO",
            "COMPRESSOR",
            "AUXILIARY",
            "HOT_WATER",
        ],
        expected_available_operational_statuses=[
            "COMPR",
            "RADIATORPUMP",
            "COOLING",
            "HOT_WATER",
            "HEATING",
            "DEFROST",
            "POOL",
        ],
        expected_available_power_statuses=[],
    )

    # Cooling switch only, no desired cooling temperature
    assert heat_pump.cooling_switch_state == 0
    assert heat_pump.cooling_temperature is None
    assert heat_pump.cooling_operational_time == 17


def __setup_itec_iq_cooling(requests_mock):
    return setup_thermia_and_perform_basic_tests(
        requests_mock,
        "iTec_IQ_cooling.txt",
        expected_model="iTec",
        expected_model_id="IQ",
        expected_available_operational_modes=[
            "OFF",
            "AUTO",
            "COMPRESSOR",
            "AUXILIARY",
            "HOT_WATER",
        ],
        expected_available_operational_statuses=[
            "COMPR",
            "RADIATORPUMP",
            "HOT_WATER",
            "HEATING",
            "DEFROST",
            "POOL",
            "COOLING",
        ],
        expected_available_power_statuses=[],
    )


def __register_writes(requests_mock):
    requests_mock.post(REGISTERS_URL, status_code=200)

    return lambda: [
        request.json()
        for request in requests_mock.request_history
        if request.method == "POST" and request.url == REGISTERS_URL
    ]


def __change_cooling_registers(requests_mock, heat_pump, change):
    absolute_path = os.path.dirname(os.path.abspath(__file__))
    test_data = parse_debug_file(f"{absolute_path}/debug_files/iTec_IQ_cooling.txt")
    cooling_group = test_data["groups"]["REG_GROUP_COOLING"]

    for register in cooling_group:
        change(register)

    requests_mock.get(COOLING_GROUP_URL, json=cooling_group)
    heat_pump.update_data()


def test_itec_iq_cooling(requests_mock):
    heat_pump = __setup_itec_iq_cooling(requests_mock)

    assert heat_pump.cooling_switch_state == 1
    assert heat_pump.cooling_temperature == 21
    assert heat_pump.cooling_min_temperature_value == 12
    assert heat_pump.cooling_max_temperature_value == 40
    assert heat_pump.cooling_temperature_step == 1
    assert heat_pump.cooling_operational_time == 740


def test_set_cooling_switch_state(requests_mock):
    heat_pump = __setup_itec_iq_cooling(requests_mock)
    register_writes = __register_writes(requests_mock)

    heat_pump.set_cooling_switch_state(0)

    assert register_writes() == [
        {
            "registerSpecificationId": 110044,
            "registerValue": 0,
            "clientUuid": "api-client-uuid",
        }
    ]


def test_set_cooling_temperature(requests_mock):
    heat_pump = __setup_itec_iq_cooling(requests_mock)
    register_writes = __register_writes(requests_mock)

    heat_pump.set_cooling_temperature(22)

    assert register_writes() == [
        {
            "registerSpecificationId": 110121,
            "registerValue": 22,
            "clientUuid": "api-client-uuid",
        }
    ]


def test_set_cooling_temperature_outside_range_is_not_sent(requests_mock):
    heat_pump = __setup_itec_iq_cooling(requests_mock)
    register_writes = __register_writes(requests_mock)

    heat_pump.set_cooling_temperature(11)
    heat_pump.set_cooling_temperature(41)
    heat_pump.set_cooling_switch_state(2)

    assert register_writes() == []


def test_set_cooling_without_cooling_registers_is_not_sent(requests_mock):
    heat_pump = setup_thermia_and_perform_basic_tests(
        requests_mock,
        "diplomat_duo_921.txt",
        expected_model="Diplomat / Diplomat Duo",
        expected_model_id="DHP H/L/C 921",
        expected_available_operational_modes=[
            "OFF",
            "AUTO",
            "COMPRESSOR",
            "AUXILIARY",
            "HOT_WATER",
        ],
        expected_available_operational_statuses=[
            "COMPR",
            "BRINEPUMP",
            "RADIATORPUMP",
            "COOLING",
            "HOT_WATER",
            "HEATING",
        ],
        expected_available_power_statuses=[
            "3KW",
            "6KW",
            "9KW",
            "12KW",
            "15KW",
        ],
    )
    register_writes = __register_writes(requests_mock)

    heat_pump.set_cooling_switch_state(1)
    heat_pump.set_cooling_temperature(22)

    assert register_writes() == []


def test_set_cooling_temperature_off_step_is_not_sent(requests_mock):
    heat_pump = __setup_itec_iq_cooling(requests_mock)
    register_writes = __register_writes(requests_mock)

    heat_pump.set_cooling_temperature(21.5)

    assert register_writes() == []


def test_cooling_temperature_without_limits_is_not_sent(requests_mock):
    heat_pump = __setup_itec_iq_cooling(requests_mock)
    register_writes = __register_writes(requests_mock)

    def remove_limits(register):
        register["minValue"] = None
        register["maxValue"] = None

    __change_cooling_registers(requests_mock, heat_pump, remove_limits)
    heat_pump.set_cooling_temperature(22)

    assert heat_pump.cooling_temperature == 21
    assert register_writes() == []


def test_read_only_cooling_registers_are_not_written(requests_mock):
    heat_pump = __setup_itec_iq_cooling(requests_mock)
    register_writes = __register_writes(requests_mock)

    def make_read_only(register):
        register["isReadOnly"] = True

    __change_cooling_registers(requests_mock, heat_pump, make_read_only)
    heat_pump.set_cooling_switch_state(0)
    heat_pump.set_cooling_temperature(22)

    assert heat_pump.cooling_switch_state == 1
    assert register_writes() == []


def test_cooling_switch_with_other_states_is_not_a_switch(requests_mock):
    heat_pump = __setup_itec_iq_cooling(requests_mock)
    register_writes = __register_writes(requests_mock)

    def change_states(register):
        if register["registerName"] == "REG_ACTIVATE_COOLING":
            register["valueNames"][1]["value"] = 2

    __change_cooling_registers(requests_mock, heat_pump, change_states)
    heat_pump.set_cooling_switch_state(1)

    assert heat_pump.cooling_switch_state is None
    assert register_writes() == []
