import sys
import pathlib
from unittest import TestCase
import pytest

script_dir = pathlib.Path(__file__).parent.absolute()
parent_dir = script_dir.parents[0]
sys.path.append(str(parent_dir))
from yaml_checker import check_yaml


class TestCheckYamlLog(TestCase):
    """ A class to capture the log output of check_yaml to test its content"""
    def __init__(self, yaml_file):
        super().__init__()
        self.yaml_file = yaml_file

    def check_yaml_log_error(self):
        with self.assertLogs() as captured:
            check_yaml(self.yaml_file, check_urls=False)
        # There should be at least 5 lines of INFO output by yaml checker
        assert len(captured.records) > 5
        for record in captured.records:
            # Fail if there is an ERROR detected by check_yaml
            assert record.levelname is not 'ERROR'

skip_missions = ["SEA045_M100", "SEA077_M46", "SEA077_M44"]

all_mission_yaml_list = list((parent_dir / 'mission_yaml').glob('*.yml'))
mission_yaml_list = []
for mission_path in all_mission_yaml_list:
    if mission_path.name.split('.')[0] in skip_missions:
        continue
    mission_yaml_list.append(mission_path)


@pytest.mark.parametrize("yaml_file", mission_yaml_list)
def test_log(yaml_file):
    # Loop through each yaml file in mission_yaml and run check_yaml on them, then look for ERRORs in the log
    LogInst = TestCheckYamlLog(str(yaml_file))
    LogInst.check_yaml_log_error()
