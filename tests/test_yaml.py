import sys
import pathlib
from unittest import TestCase

script_dir = pathlib.Path(__file__).parent.absolute()
parent_dir = script_dir.parents[0]
sys.path.append(str(parent_dir))
from yaml_checker import check_yaml


def test_yaml_check():
    check_yaml('/home/callum/Documents/data-flow/raw-to-nc/deployment-yaml/mission_yaml/SEA44_M45.yml')

#mission_yaml_list = list((parent_dir / 'mission_yaml').glob('*.yml'))
#@pytest.mark.parametrize("yaml_file", mission_yaml_list)
class TestCheckYamlLog(TestCase):
    def test_check_yaml_log_error(self):
        with self.assertLogs() as captured:
            check_yaml('/home/callum/Documents/data-flow/raw-to-nc/deployment-yaml/mission_yaml/SEA44_M45.yml')
        assert len(captured.records) > 5
        for record in captured.records:
            assert record.levelname is not 'ERROR'
