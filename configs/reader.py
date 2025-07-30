import datetime
from pathlib import Path
from itertools import chain
import sys
import numpy as np
import yaml
import logging
_log = logging.getLogger(__name__)
script_dir = Path(__file__).parent.resolve()
module_dir = Path(__file__).parent.parent.resolve()

skip_projects = [
    "1_Folder_Template",
    "00_Folder_Template",
    "2_Simulations",
    "3_SAT_Missions",
    "10_Oman_001",
    "8_KAMI-KZ_001",
    "11_Amundsen_Sea",
    "40_OMG_Training",
    "temprary_data_store",
]


explained_missions = [('SEA067', 15),
                      ('SEA061', 63),
                      ('SEA056', 27),
                      ('SEA066', 31),
                      ('SEA045', 58),
                      ('SEA061', 48),
                      ('SEA045', 37),
                      ('SEA045', 54),
                      ('SEA044', 48),
                      ('SEA055', 16),
                      ('SEA063', 40),
                      ('SEA066', 45),
                      ('SEA045', 74),
                      ('SEA066', 50),
                      ('SEA055', 81),
                      ('SEA044', 23),
                      ('SEA056', 22),
                      ('SEA044', 43),
                      ]


failed_or_nonvoto_missions = [('SEA057', 58),
                      ('SEA078', 34),
                      ('SEA070', 29),
                      ('SEA057', 75),
                      ('SHW001', 35),
                      ]

def list_missions(to_skip=()):
    base = Path("/mnt/samba")
    projects = list(base.glob("*_*"))
    glider_dirs = []
    for proj in projects:
        good = True
        str_proj = str(proj)
        for skip in to_skip:
            if skip in str_proj:
                good = False
        if not good:
            continue
        non_proc = proj / "1_Downloaded"
        if non_proc.is_dir():
            proj_glider_dirs = non_proc.glob("S*")
            glider_dirs.append(list(proj_glider_dirs))
            continue
        sub_dirs = proj.glob("*")
        for sub_dir in sub_dirs:
            non_proc = sub_dir / "1_Downloaded"
            if non_proc.is_dir():
                for skip in to_skip:
                    if skip in str(non_proc):
                        continue
                proj_glider_dirs = non_proc.glob("S*")
                glider_dirs.append(list(proj_glider_dirs))

    glider_dirs = list(chain(*glider_dirs))

    all_mission_paths = []
    for glider_dir in glider_dirs:
        mission_dirs = list(glider_dir.glob("S*"))
        all_mission_paths.append(mission_dirs)
    all_mission_paths = list(chain(*all_mission_paths))
    good_missions = []
    for mission_path in all_mission_paths:
        mission_name = mission_path.parts[-1]
        try:
            glider_str, mission_str = mission_name.split("_")
            good_missions.append(mission_path)
        except:
            continue

    return good_missions

def read_nav_config(config_file):
    sea_msn = {}
    with open(config_file) as fin:
        for line in fin.readlines():
            for bad_char in [' ', '#', '\n']:
                line = line.replace(bad_char, '')
            if not line:
                continue
            if line[0] == ';':
                continue
            if "=" not in line:
                continue
            if ':' in line:
                key, var = line.rsplit(':', maxsplit=1)
                sea_msn[key] = var
            else:
                key, var = line.rsplit('=', maxsplit=1)
            sea_msn[key] = var
    return sea_msn


def read_pld_config(config_file):
    pld_params = {}
    read_device_params = True
    read_global = True
    device_used = True
    devices_dict = {}
    with open(config_file) as fin:
        for line in fin.readlines():
            for bad_char in [' ', '#', '\n']:
                line = line.replace(bad_char, '')
            if '---------------------------' in line:
                read_device_params = False
            if "Globalparameters" in line:
                read_global = True
            if 'Slotsconfiguration' in line:
                read_global = False
            if line[1:-1] in devices_dict.keys():
                read_device_params = True
                device_dict_key = line[1:-1]
                continue
            if "=" not in line:
                continue
            key, var = line.split('=', maxsplit=1)
            if key == 'used':
                device_used = True if var == 'yes' else False
                continue
            if key == 'device' and device_used:
                devices_dict[var] = {}
                continue
            if read_device_params:
                devices_dict[device_dict_key][key] = var
                continue

            if read_global:
                pld_params[key] = var
    return pld_params | devices_dict


class ConfigReader:
    def __init__(self, mission_dir):
        self.mission_dir = Path(mission_dir)
        self.invalid_mission = False
        if 'SEA' in self.mission_dir.parts[-1] or 'SHW' in self.mission_dir.parts[-1] :
            mission_str_raw = self.mission_dir.parts[-1]
            raw_mission_dirs = list(self.mission_dir.glob("20*"))
            if raw_mission_dirs:
                self.mission_raw_dir = raw_mission_dirs[0]
            else:
                self.mission_raw_dir = self.mission_dir

        else:
            if list(self.mission_dir.glob("seapayload_SEA*")):
                mission_str_raw =  list(self.mission_dir.glob("seapayload_SEA*"))[0].name.split('.')[0].split('_', maxsplit=1)[1]
            elif list(self.mission_dir.glob("SEA*pdf")):
                mission_str_raw = list(self.mission_dir.glob("SEA*pdf"))[0].name.split('.')[0]
            elif list(self.mission_dir.glob("SEA*docx")):
                mission_str_raw = list(self.mission_dir.glob("SEA*docx"))[0].name.split('.')[0]
            else:
                mission_str_raw = ""
        if not mission_str_raw or "XX" in mission_str_raw:
            _log.error(f"No valid files found in {mission_dir}. ABORT")
            self.invalid_mission = True
            return
        self.platform_id =  mission_str_raw.split('_')[0]
        self.mission_num = int(mission_str_raw.split('_M')[-1])
        self.mission_str = f"{self.platform_id}_M{self.mission_num}"
        self.config_dict = {}
        self.yaml_dir =  module_dir /'yaml_from_cfg'
        self.yaml_path = self.yaml_dir  / f"{self.mission_str}.yml"
        self.write_yaml_to_mission_dir = False
        log_formatter = logging.Formatter(f"[%(levelname)s] {self.mission_str} %(message)s")
        for handler in _log.handlers:
            handler.setFormatter(log_formatter)

    def init_local_logger(self):
        logging.basicConfig(
            level=logging.INFO,
            format=f"[%(levelname)s] {self.mission_str} %(message)s",
            handlers=[
                logging.FileHandler(f"{str(self.mission_dir / 'config_check.log')}", mode='w'),
                logging.StreamHandler()
            ]
        )
    def read_configs(self):
        if 'docs/1_Operations' in str(self.mission_dir):
            sea_msn = self.mission_dir / 'sea.msn'
            sea_cfg = self.mission_dir / 'sea.cfg'
            sea_pld = list(self.mission_dir.glob("seapayload*"))[0]
        else:
            sea_msn = self.mission_raw_dir / 'NAV' / 'configs'  / 'sea.msn'
            sea_cfg = self.mission_raw_dir / 'NAV' / 'configs'  / 'sea.cfg'
            sea_pld = self.mission_raw_dir / 'PLD' / 'configs'  / 'seapayload.cfg'

        for fn in [sea_msn, sea_cfg]:
            if not fn.exists():
                _log.error(f"did not find input file {fn}")
            else:
                cfg_dict = read_nav_config(fn)
                self.config_dict = self.config_dict | cfg_dict
        if not sea_pld.exists():
            _log.error(f"did not find input file {sea_pld}")
        else:
            cfg_dict = read_pld_config(sea_pld)
            self.config_dict = self.config_dict | cfg_dict

    def check_mission_id(self):
        if not 'id' in self.config_dict.keys() or not 'mission.num' in self.config_dict.keys():
            _log.warning(f"Did not find id and/or mission.num in config files")
            return
        mission_str_config = f"{self.config_dict['id'].upper()}_M{self.config_dict['mission.num']}"
        if mission_str_config != self.mission_str:
            _log.error(f"mission id {mission_str_config} from config files != {self.mission_str} from filepath for {self.mission_dir}")
    

    def check_default_params(self):
        expected_values = {
            "iridium.timeout.inactivity2": "600",
            'security.batteries.low': '23',
            'mission.mode': '0',
        }
        cfg = self.config_dict
        for key, var in cfg.items():
            if key not in expected_values.keys():
                continue
            if str(var) != str(expected_values[key]):
                _log.error(f"Bad value for {key} = {var}. Expected {expected_values[key]}")
        return

    def compare_last_mission(self):
        existing_yml = list(self.yaml_dir.glob(f"{self.platform_id}*yml"))
        if len(existing_yml) < 2:
            return
        mission_numbers = [int(m_string.name.split('.')[0].split('_M')[-1]) for m_string in existing_yml]
        mission_numbers = np.array(mission_numbers)
        previous_missions = mission_numbers[mission_numbers < self.mission_num]
        if len(previous_missions) == 0:
            return
        last_mission = max(previous_missions)
        last_yaml = self.yaml_path.parent / f'{self.platform_id}_M{last_mission}.yml'
        prev = last_yaml.name.split('.')[0].split('_M')[-1]
        with open(last_yaml) as fin:
            previous = yaml.safe_load(fin)

        combi_dict = previous | self.config_dict
        cfg = self.config_dict
        for key in combi_dict.keys():
            if key in ['mission.num', 'config_file_directory']:
                continue
            if key not in cfg.keys() and key in previous.keys():
                    _log.warning(f"Removed value for {key}. Previous mission  (M{prev}). {key} = {previous[key]} in previous mission")
                    continue
            if key in cfg.keys():
                if key not in previous.keys():
                    _log.warning(f"New value {key} = {cfg[key]}. {key} not present in previous mission (M{prev})")
                    continue

                if type(cfg[key]) is dict:
                    for sub_key, sub_var in cfg[key].items():
                        if sub_key not in previous[key].keys():
                            continue
                        if previous[key][sub_key] != sub_var:
                            _log.warning(
                                f"Changed value. {key}: {sub_key} = {sub_var}. Previous mission (M{prev}) {key}: {sub_key}  = {previous[key][sub_key]}")
                    continue
                if previous[key] != cfg[key]:
                    _log.warning(f"Changed value. {key} = {cfg[key]}. Previous mission (M{prev}) {key} = {previous[key]}")

    def compare_pyglider_yaml(self):
        pyglider_yaml = module_dir / "mission_yaml" / self.yaml_path.name
        if not pyglider_yaml.exists():
            _log.error(f"no pyglider yaml {pyglider_yaml} found")
            return
        with open(pyglider_yaml) as fin:
            deployment = yaml.safe_load(fin)
        devices = deployment['glider_devices']
        alseamar_devices = convert_sensors_dict(self.config_dict)
        for key, val in alseamar_devices.items():
            if key not in devices.keys():
                _log.error(f"missing calib info for {key}")
            for cal_key, cal_val in val.items():
                if cal_val != devices[key][cal_key]:
                    _log.error(f"Missmatch calibration value {key}: {cal_key}: {cal_val}. Expected {devices[key][cal_key]} from pyglider yaml")


        return

    def write_configs(self):
        self.config_dict = {"config_file_directory": str(self.mission_dir)} | self.config_dict
        with open(self.yaml_path, "w") as fout:
            yaml.dump(self.config_dict, fout, sort_keys=False)
        if self.write_yaml_to_mission_dir:
            with open(self.mission_dir / f"{self.mission_str}.yml", "w") as fout:
                yaml.dump(self.config_dict, fout, sort_keys=False)

    def run(self):
        _log.info(f"START check at {str(datetime.datetime.now())[:19]} in {self.mission_dir}")
        self.read_configs()
        #self.check_mission_id()
        self.check_default_params()
        self.compare_last_mission()
        self.compare_pyglider_yaml()
        self.write_configs()
        _log.info(f"COMPLETE check at {str(datetime.datetime.now())[:19]}")


sensors_converrsion_dict = {
    'LEGATO': {'dict_name': 'ctd'},
    'TRIDENTE': {'dict_name': 'optics'},
    'FLBBCD': {'dict_name': 'optics'},
    'FLNTU': {'dict_name': 'optics'},
    'FLBBPC': {'dict_name': 'optics'},
    'AROD_FT': {'dict_name': 'oxygen'},
    'MPE-PAR': {'dict_name': 'irradiance'},
    'OCR504': {'dict_name': 'irradiance'},
    'AD2CP': {'dict_name': 'AD2CP'},
}

def convert_sensors_dict(config_dict):
    sensors_dict = {}
    for key, val in config_dict.items():
        if type(val) is not dict:
            continue
        sensors_dict[key] = val
    dict_out = {}
    for key, sensor_orig in sensors_dict.items():
        if key not in sensors_converrsion_dict.keys():
            _log.error(f"{key} sensor not found in conversion table")
            continue
        conversion_dict = sensors_converrsion_dict[key]
        sensor_new = {}
        calib_date = ''
        if 'calibrationdate' in sensor_orig.keys():
            calib_date = sensor_orig['calibrationdate']
        elif 'dateofcalibration' in sensor_orig.keys():
            calib_date = sensor_orig['dateofcalibration']
        if calib_date:
            sensor_new['calibration_date'] = f"{calib_date[:4]}-{calib_date[4:6]}-{calib_date[6:8]}"
        sensor_new['serial'] = sensor_orig['serialnumber']
        dict_out[conversion_dict['dict_name']] = sensor_new
    return dict_out



def run_all_samba():
    missions = list_missions(to_skip=skip_projects)
    for mission in missions:
        conf = ConfigReader(mission)
        if conf.invalid_mission:
            continue
        if (conf.platform_id, conf.mission_num) in explained_missions:
            _log.debug(f"Known bad mission {conf.mission_str}. Skipping")
            continue
        if not conf.yaml_path.exists():
            conf.run()


def run_all_docs_dir():
    msn_files = list(Path("/mnt/docs/1_Operations/Missions/").rglob("*sea.msn"))
    for fn in msn_files:
        mission = fn.parent
        conf = ConfigReader(mission)
        if conf.invalid_mission:
            continue
        if not conf.yaml_path.exists():
            conf.run()

def missions_without_cfg():
    mission_yaml_paths = list((module_dir / "mission_yaml").glob("*.yml"))
    mission_yaml = [yaml_file.name.split('.')[0] for yaml_file in mission_yaml_paths]
    cfg_yaml_paths = list((module_dir / "yaml_from_cfg").glob("*.yml"))
    cfg_yaml = [yml_file.name.split('.')[0] for yml_file in cfg_yaml_paths]
    missing_yaml = set(mission_yaml).difference(cfg_yaml)
    failed_str = [f"{glider_mission[0]}_M{glider_mission[1]}" for glider_mission in failed_or_nonvoto_missions]
    unexplained_yaml = missing_yaml.difference(failed_str)
    _log.error(f"Missing yaml from {unexplained_yaml}")

def run_all():
    run_all_docs_dir()
    missions_without_cfg()
    run_all_samba()
    missions_without_cfg()

if __name__ == '__main__':

    args = sys.argv
    if len(args) > 1:
        config = ConfigReader(args[1])
        config.init_local_logger()
        config.write_yaml_to_mission_dir = True
        config.run()
    else:

        logging.basicConfig(
            level=logging.INFO,
            format=f"[%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(f'all_files.log', mode='w'),
                logging.StreamHandler()
            ]
        )
        run_all()
