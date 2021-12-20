import sys
import pathlib
from unittest import TestCase
import pytest

script_dir = pathlib.Path(__file__).parent.absolute()
parent_dir = script_dir.parents[0]
sys.path.append(str(parent_dir))
from yaml_checker import check_yaml




class TestCheckYamlLog(TestCase):
    def __init__(self, yaml_file):
        super().__init__()
        self.yaml_file = yaml_file

    def check_yaml_log_error(self):
        with self.assertLogs() as captured:
            check_yaml(self.yaml_file, check_urls=True)
        assert len(captured.records) > 5
        for record in captured.records:
            assert record.levelname is not 'ERROR'



mission_yaml_list = list((parent_dir / 'mission_yaml').glob('*.yml'))


@pytest.mark.parametrize("yaml_file", mission_yaml_list)
def test_log(yaml_file):
    LogInst = TestCheckYamlLog(str(yaml_file))
    LogInst.check_yaml_log_error()
