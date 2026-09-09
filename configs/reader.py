import datetime
from pathlib import Path
from itertools import chain
import sys
import numpy as np
import yaml
import logging
_log = logging.getLogger(__name__)
table_log = logging.getLogger(name="table")
script_dir = Path(__file__).parent.resolve()
module_dir = Path(__file__).parent.parent.resolve()
yaml_dir = module_dir / 'yaml_from_cfg'
if not yaml_dir.exists():
    yaml_dir.mkdir(parents=True)

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

def read_nav_config(config_file, defaults_file=False):
    sea_msn = {}
    with open(config_file) as fin:
        for line in fin.readlines():
            for bad_char in [' ', '#', '\n']:
                line = line.replace(bad_char, '')
            if not line:
                continue
            if line[0] == ';':
                if defaults_file:
                    line = line[1:]
                else:
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


def read_pld_config(config_file, defaults_file=False):
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
            if len(line) > 4:
                if line[0] == '[' and line[-1] == ']' and defaults_file:
                    devices_dict[line[1:-1]] = {}
                    device_dict_key =line[1:-1]
                    read_device_params = True
                    continue
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
    if defaults_file:
        # Add values for the acq.2 that some gliders have
        for key, val in devices_dict.items():
            if type(val) is dict:
                extras = {}
                for sub_key, sub_val in val.items():
                    if 'acq.1' in sub_key:
                        extras[sub_key.replace('1', '2')] = sub_val
                devices_dict[key] = val | extras
    return pld_params | devices_dict


def expected_values_checker(cfg, expected_values, section=''):
    for key, var in cfg.items():
        if key not in expected_values.keys():
            continue
        if str(var) != str(expected_values[key]):
            _log.error(f"Bad value for {section} {key} = {var}. Expected {expected_values[key]}")
            
def check_config_alseamar_defaults(mission_cfg, alseamar_cfg):
    skips_keys = ['config_file_directory', 'id']
    for key, val in mission_cfg.items():
        if key in skips_keys:
            continue
        if key not in alseamar_cfg.keys():
            _log.error(f"Did not find `{key}` in alseamar default config. Possibly a typo or bad value")
            continue
        if type(val) is dict:
            for sub_key, sub_val in val.items():
                if sub_key not in alseamar_cfg[key].keys():
                    _log.error(f"Did not find `{key}`:`{sub_key}` in alseamar default config. Possibly a typo or bad value")
    return


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
        elif 'SEA' in self.mission_dir.parts[-2] or 'SHW' in self.mission_dir.parts[-2] :
            platform =  self.mission_dir.parts[-2].split('_')[0]
            mission =  self.mission_dir.parts[-1].split('_M')[1]
            mission_str_raw = f"{platform}_M{mission}"
            self.mission_raw_dir = self.mission_dir

        else:
            if list(self.mission_dir.glob("seapayload_S*")):
                mission_str_raw =  list(self.mission_dir.glob("seapayload_S*"))[0].name.split('.')[0].split('_', maxsplit=1)[1]
            elif list(self.mission_dir.glob("S*pdf")):
                mission_str_raw = list(self.mission_dir.glob("S*pdf"))[0].name.split('.')[0]
            elif list(self.mission_dir.glob("S*docx")):
                mission_str_raw = list(self.mission_dir.glob("S*docx"))[0].name.split('.')[0]
            elif list(self.mission_dir.glob("S*_M*.yml")):
                mission_str_raw = list(self.mission_dir.glob("S*_M*.yml"))[0].name.split('.')[0]
            else:
                mission_str_raw = ""
        if not mission_str_raw or "XX" in mission_str_raw:
            _log.error(f"No valid files found in {mission_dir}. ABORT")
            self.invalid_mission = True
            return
        self.platform_id =  mission_str_raw.split('_')[0]
        self.mission_num = int(mission_str_raw.split('_M')[-1])
        self.mission_str = f"{self.platform_id}_M{self.mission_num}"
        self.config_dict = {"config_file_directory": str(self.mission_dir)}
        self.alseamar_config = {}
        self.yaml_dir = yaml_dir
        self.yaml_path = self.yaml_dir  / f"{self.mission_str}.yml"
        self.write_yaml_to_mission_dir = False
        class ContextFilter(logging.Filter):
            def filter(self, record):
                record.mission_str = mission_str_raw
                return True
        f = ContextFilter()
        _log.addFilter(f)
        table_log.addFilter(f)

    def init_local_logger(self):
        ch = logging.FileHandler(f"{str(self.mission_dir / 'config_check.log')}", mode='w')
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(f"%(levelname)-10s %(mission_str)-12s %(message)s"))
        _log.addHandler(ch)
        ch = logging.FileHandler(f"{str(self.mission_dir / 'table_config_check.log')}", mode='w')
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(f"%(levelname)s	%(mission_str)s	%(message)s"))
        table_log.addHandler(ch)

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
                self.invalid_mission = True
            else:
                cfg_dict = read_nav_config(fn)
                self.config_dict = self.config_dict | cfg_dict
        if not sea_pld.exists():
            _log.error(f"did not find input file {sea_pld}")
            self.invalid_mission = True
        else:
            cfg_dict = read_pld_config(sea_pld)
            self.config_dict = self.config_dict | cfg_dict
            
    def read_alseamar_configs(self):
        _log.info("Check against alseamar defaults")
        alseamar_dir = script_dir / 'alseamar'
        self.alseamar_config = self.alseamar_config | read_nav_config(alseamar_dir / 'sea.msn', defaults_file=True)
        self.alseamar_config = self.alseamar_config | read_nav_config(alseamar_dir / 'sea.cfg', defaults_file=True)
        self.alseamar_config = self.alseamar_config | read_pld_config(alseamar_dir / 'seapayload.cfg', defaults_file=True)
        # Add values missing from alseamar conf files
        for extra_key in [
            'CCUversion:>',
            'seanav', 
            'drf.dtpid.kp',
            'drf.dtpid.kd',
            'drf.dtpid.ki',
            'drf.ppid.ki',
            'drf.bal.inc.coef',
            'security.fly.timeout',
            'vspeed.inib.immersion',
            'inflecting.fly.enable',
          ]:
            self.alseamar_config[extra_key] = ''

        check_config_alseamar_defaults(self.config_dict, self.alseamar_config)

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
            'iridium.call.main': '00881600005212',
            'iridium.call.rescue': '00881600005212',
        }
        cfg = self.config_dict
        expected_values_checker(cfg, expected_values)
        expected_sensor_values = {
            'AROD_FT': {'cfg.analog': '1'},
        }
        for sensor, expected_values in expected_sensor_values.items():
            if sensor in cfg.keys():
                expected_values_checker(cfg[sensor], expected_values, section=sensor)
        return


    def spell_check(self):
        _log.info("Spellcheck")
        # spell checking for some terms in the sensors
        base_setting_strings = {
            'acq.1': ['depth', 'period', 'phase', 'yo'],
            'acq.2': ['depth', 'period', 'phase', 'yo'],
            'cfg': ['WarmUpPeriod', 'phaseswitch', 'periodswitch']
        }
        sensor_specific_setting_strings = {
            'AD2CP': {
                'cfg': ['computeBI', 'log_pld', 'log_ad2cp', 'cells_sub', 'PLAN', 'AVG', 'BT', 'TMAVG', 'TMBT', 'BURST', 'TMBURST'],
            },
            'AROD_FT': {
                'cfg': ['analog'],
            },
            'GPCTD': {
                'cfg': ['oxygenInstalled', 'log_gpctd']
            },
            'LEGATO': {
                'cfg': ['codaInstalled', 'tridenteInstalled', 'log_legato', 'computeSV'],
                'cfg.TRIDENTE': [f'channel{x}' for x in range(7)],
            },
            'LEGATO4': {
                'cfg': ['log_legato'],
                'cfg.sensor1': ['installed', 'prefix', 'ch1', 'ch2', 'ch3'],
                'cfg.sensor2': ['installed', 'prefix', 'ch1', 'ch2', 'ch3'],
            },
            'MPE-PAR': {},
            'TRIDENTE': {
                'cfg': ['frequency', 'log_tridente', 'channel1', 'channel2', 'channel3'],
            },
        }
        sensor_setting_strings = {}
        for sensor, settings in sensor_specific_setting_strings.items():
            settings_dict = base_setting_strings.copy()
            for key, val in sensor_specific_setting_strings[sensor].items():
                if key in base_setting_strings.keys():
                    settings_dict[key] = base_setting_strings[key] + val
                else:
                    settings_dict[key] = val
            sensor_setting_strings[sensor] = settings_dict

        cfg = self.config_dict
        for key, val in cfg.items():
            if type(val) is not dict:
                continue
            if key not in sensor_setting_strings.keys():
                _log.warning(f"Did not find spellchecks for sensor {key}, not checking")
                continue
            acceptable_setting_strings = sensor_setting_strings[key]

            for sensor_setting, setting_value in val.items():
                if len(sensor_setting.split('.')) == 3:
                    setting_group, setting_str = sensor_setting.rsplit('.', maxsplit=1)
                elif len(sensor_setting.split('.')) == 2:
                    setting_group, setting_str = sensor_setting.split('.')
                else:
                    continue
                if setting_group not in acceptable_setting_strings.keys():
                    _log.error(f"SPELLCHECK Did not find spellings in {key} for {sensor_setting}")
                    continue
                if setting_str not in acceptable_setting_strings[setting_group]:
                    _log.error(f"SPELLCHECK Possible spelling error in {key}: {sensor_setting} expected one of {acceptable_setting_strings[setting_group]}")


    def compare_last_mission(self):
        existing_yml = list(self.yaml_dir.glob(f"{self.platform_id}*yml"))
        if len(existing_yml) < 2:
            _log.error("No prior configs found for this glider! Cannot compare config values")
            return
        mission_numbers = [int(m_string.name.split('.')[0].split('_M')[-1]) for m_string in existing_yml]
        mission_numbers = np.array(mission_numbers)
        previous_missions = mission_numbers[mission_numbers < self.mission_num]
        if len(previous_missions) == 0:
            return
        last_mission = max(previous_missions)
        last_yaml = self.yaml_path.parent / f'{self.platform_id}_M{last_mission}.yml'
        prev = last_yaml.name.split('.')[0].split('_M')[-1]
        _log.info(f"Comparing to previous mission (M{prev}) file {last_yaml}")
        with open(last_yaml) as fin:
            previous = yaml.safe_load(fin)

        combi_dict = previous | self.config_dict
        cfg = self.config_dict
        for key in combi_dict.keys():
            if key == 'config_file_directory':
                if previous[key] == cfg[key]:
                    _log.error(f"Previous mission M{prev} was made in this directory! Consider deleting {last_yaml}")
                continue
            if key not in cfg.keys() and key in previous.keys():
                    _log.warning(f"Removed value for {key}. Previous mission  (M{prev}). {key} = {previous[key]} in previous mission")
                    table_log.warning(f"removed\t{key}\tNone\t{previous[key]}")
                    continue
            if key in cfg.keys():
                value = cfg[key]
                if 'channel' in str(value) and type(value) is dict:
                    for sub_key, sub_var in value.items():
                        if 'channel' not in sub_key:
                            continue
                        if sub_var.lower() != sub_var:
                            _log.error(f"Channel value {key}:{sub_key}:{sub_var} is not lowercase")
                if key not in previous.keys():
                    _log.warning(f"New value {key} = {cfg[key]}. {key} not present in previous mission (M{prev})")
                    table_log.warning(f"new\t{key}\t{cfg[key]}\tNone")
                    continue

                if type(cfg[key]) is dict:
                    for sub_key, sub_var in cfg[key].items():
                        if sub_key not in previous[key].keys():
                            continue
                        if previous[key][sub_key] != sub_var:
                            _log.warning(
                                f"Changed value {key}: {sub_key} = {sub_var}. Previous mission (M{prev}) {key}: {sub_key}  = {previous[key][sub_key]}")
                            table_log.warning(f"change\t{key}: {sub_key}\t{sub_var}\t{previous[key][sub_key]}")
                    continue
                if previous[key] != cfg[key]:
                    _log.warning(f"Changed value {key} = {cfg[key]}. Previous mission (M{prev}) {key} = {previous[key]}")
                    table_log.warning(f"change\t{key}\t{cfg[key]}\t{previous[key]}")

    def compare_pyglider_yaml(self):
        pyglider_yaml = module_dir / "mission_yaml" / self.yaml_path.name
        if not pyglider_yaml.exists():
            _log.warning(f"no pyglider yaml {pyglider_yaml} found")
            return
        _log.info(f"Compare with pyglider yaml {pyglider_yaml}")
        with open(pyglider_yaml) as fin:
            deployment = yaml.safe_load(fin)
        devices = deployment['glider_devices']
        alseamar_devices = convert_sensors_dict(self.config_dict)
        for key, val in alseamar_devices.items():
            if key not in devices.keys():
                _log.error(f"missing calib info for {key}")
            for cal_key, cal_val in val.items():
                if cal_val != devices[key][cal_key]:
                    msg = f"Missmatch calibration value {key}: {cal_key}: {cal_val}. Expected {devices[key][cal_key]} from pyglider yaml"
                    table_msg = f"missmatch\tcalibration value {key}: {cal_key}\t{cal_val}\t{devices[key][cal_key]}"
                    if cal_key=='calibration_date':
                        _log.warning(msg)
                        table_log.warning(table_msg)
                    else:
                        _log.error(msg)
                        table_log.error(table_msg)
        return

    def write_configs(self):
        with open(self.yaml_path, "w") as fout:
            yaml.dump(self.config_dict, fout, sort_keys=False)
        if self.write_yaml_to_mission_dir:
            with open(self.mission_dir / f"{self.mission_str}.yml", "w") as fout:
                yaml.dump(self.config_dict, fout, sort_keys=False)

    def run(self):
        _log.info(f"START check at {str(datetime.datetime.now())[:19]} in {self.mission_dir}")
        self.read_configs()
        self.read_alseamar_configs()
        self.spell_check()
        self.check_default_params()
        self.compare_last_mission()
        self.compare_pyglider_yaml()
        self.write_configs()
        _log.info(f"COMPLETE check at {str(datetime.datetime.now())[:19]}")


sensors_conversion_dict = {
    'LEGATO': {'dict_name': 'ctd'},
    'LEGATO4': {'dict_name': 'ctd'},
    'GPCTD': {'dict_name': 'ctd'},
    'TRIDENTE': {'dict_name': 'optics'},
    'FLBBCD': {'dict_name': 'optics'},
    'FLNTU': {'dict_name': 'optics'},
    'FLBBPC': {'dict_name': 'optics'},
    'SEAOWL': {'dict_name': 'optics'},
    'NANOFLU': {'dict_name': 'optics_nanoflu'},
    'SUNA': {'dict_name': 'nitrate'},
    'AROD_FT': {'dict_name': 'oxygen'},
    'MPE-PAR': {'dict_name': 'irradiance'},
    'OCR504': {'dict_name': 'irradiance'},
    'AD2CP': {'dict_name': 'AD2CP'},
    'METS': {'dict_name': 'methane'},
    'MR1000G-RDL': {'dict_name': 'turbulence'},
}

def convert_sensors_dict(config_dict):
    sensors_dict = {}
    for key, val in config_dict.items():
        if type(val) is not dict:
            continue
        sensors_dict[key] = val
    dict_out = {}
    for key, sensor_orig in sensors_dict.items():
        if key not in sensors_conversion_dict.keys():
            _log.error(f"{key} sensor not found in conversion table")
            continue
        conversion_dict = sensors_conversion_dict[key]
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
    _log.error(f"Missing config files from missions: {unexplained_yaml}")

def run_all():
    run_all_docs_dir()
    missions_without_cfg()
    run_all_samba()
    missions_without_cfg()


def run_checker_on_dir(file_dir):
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(levelname)-10s %(mission_str)-12s %(message)s",
        handlers=[
            logging.FileHandler(f'/data/log/config_checker_all_files.log', mode='a'),
            logging.StreamHandler()
        ]
    )
    conf = ConfigReader(file_dir)
    if conf.invalid_mission:
        return False
    conf.read_configs()
    if conf.invalid_mission:
        return False
    conf.init_local_logger()
    conf.write_yaml_to_mission_dir = True
    conf.run()
    handlers = _log.handlers[:]
    for handler in handlers:
        _log.removeHandler(handler)
        handler.close()
    handlers = table_log.handlers[:]
    for handler in handlers:
        table_log.removeHandler(handler)
        handler.close()

    return True

def run_local(all_files=False):
    if all_files:
        msn_files = list(Path("/mnt/docs/1_Operations/Missions/").rglob("*sea.msn"))
        directories = [fn.parent for fn in msn_files]
    else:
        directories = [
        '/mnt/docs/1_Operations/Missions/03_SAMBA_02/07_SAMBA_02_007/SHW004_PLD175/202609DD_M10',
        '/mnt/docs/1_Operations/Missions/03_SAMBA_02/07_SAMBA_02_007/SHW003_PLD174/20260729_M14',
        '/mnt/docs/1_Operations/Missions/21_InTail/SEA076_PLD090/20260614_M48',
        "/mnt/docs/1_Operations/Missions/03_SAMBA_02/07_SAMBA_02_007/SEA056_PLD073/20260314_M103",
    ]
    for file_dir in directories:
        conf = ConfigReader(file_dir)
        conf.init_local_logger()
        conf.write_yaml_to_mission_dir = True
        conf.run()

def main():
    args = sys.argv
    if len(args) > 1:
        config = ConfigReader(args[1])
        config.init_local_logger()
        config.write_yaml_to_mission_dir = True
        config.run()
    else:
        class ContextFilter(logging.Filter):
            def filter(self, record):
                record.mission_str = ""
                return True
        f = ContextFilter()
        _log.addFilter(f)
        logging.basicConfig(
            level=logging.ERROR,
            format=f"%(levelname)-10s %(mission_str)-12s %(message)s",
            handlers=[
                logging.FileHandler(f'/data/log/config_checker_all_files.log', mode='w'),
                logging.StreamHandler()
            ]
        )
        run_local(all_files=False)


if __name__ == '__main__':
    main()
