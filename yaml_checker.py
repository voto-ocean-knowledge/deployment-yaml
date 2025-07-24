import yaml
import sys
from datetime import datetime, timedelta
from urllib import request
import logging
expected_units = {'AD2CP_HEADING': 'degrees',
                  'AD2CP_PITCH': 'degrees',
                  'AD2CP_PRESSURE': 'dbar',
                  'AD2CP_ROLL': 'degrees',
                  'AD2CP_V1_CN1': 'm s-1',
                  'AD2CP_V1_CN2': 'm s-1',
                  'AD2CP_V2_CN1': 'm s-1',
                  'AD2CP_V2_CN2': 'm s-1',
                  'AD2CP_V3_CN1': 'm s-1',
                  'AD2CP_V3_CN2': 'm s-1',
                  'AD2CP_V4_CN1': 'm s-1',
                  'AD2CP_V4_CN2': 'm s-1',
                  'AROD_FT_DO': 'mmol m-3',
                  'AROD_FT_TEMP': 'Celsius',
                  'Altitude': 'm',
                  'AngCmd': 'degrees',
                  'AngPos': 'degrees',
                  'BallastCmd': 'ml',
                  'BallastPos': 'ml',
                  'DeadReckoning': 'None',
                  'Declination': 'degrees',
                  'DesiredH': 'degrees',
                  'FLBBCD_BB_700_COUNT': 'counts',
                  'FLBBCD_BB_700_SCALED': 'm-1 sr-1',
                  'FLBBCD_CDOM_COUNT': 'counts',
                  'FLBBCD_CDOM_SCALED': 'mg m-3',
                  'FLBBCD_CHL_COUNT': 'counts',
                  'FLBBCD_CHL_SCALED': 'mg m-3',
                  'FLBBPC_BB_700_COUNT': 'counts',
                  'FLBBPC_BB_700_SCALED': 'm-1 sr-1',
                  'FLBBPC_CHL_COUNT': 'counts',
                  'FLBBPC_CHL_SCALED': 'mg m-3',
                  'FLBBPC_PC_COUNT': 'counts',
                  'FLBBPC_PC_SCALED': 'mg m-3',
                  'FLBBPE_BB_700_COUNT': 'counts',
                  'FLBBPE_BB_700_SCALED': 'm-1 sr-1',
                  'FLBBPE_CHL_COUNT': 'counts',
                  'FLBBPE_CHL_SCALED': 'mg m-3',
                  'FLBBPE_PE_COUNT': 'counts',
                  'FLBBPE_PE_SCALED': 'mg m-3',
                  'FLNTU_CHL_COUNT': 'counts',
                  'FLNTU_CHL_SCALED': 'mg m-3',
                  'FLNTU_NTU_COUNT': 'counts',
                  'FLNTU_NTU_SCALED': 'NTU',
                  'fnum': 'None',
                  'GPCTD_CONDUCTIVITY': 'S m-1',
                  'GPCTD_DOF': 'Hz',
                  'GPCTD_PRESSURE': 'dbar',
                  'GPCTD_TEMPERATURE': 'Celsius',
                  'Heading': 'degrees',
                  'LEGATO_CODA_CORR_PHASE': 'degrees',
                  'LEGATO_CODA_DO': 'mmol m-3',
                  'LEGATO_CODA_TEMPERATURE': 'Celsius',
                  'LEGATO_CONDUCTIVITY': 'mS cm-1',
                  'LEGATO_PRESSURE': 'dbar',
                  'LEGATO_SALINITY': 'PSU',
                  'LEGATO_TEMPERATURE': 'Celsius',
                  'LEGATO_TRIDENTE_CHLOROPHYLL': 'mg m-3',
                  'LEGATO_TRIDENTE_PHYCOCYANIN': 'mg m-3',
                  'LEGATO_TRIDENTE_TURBIDITY': 'FTU',
                  'TRIDENTE_CHLOROPHYLL': 'mg m-3',
                  'TRIDENTE_FDOM': 'ppb',
                  'TRIDENTE_BACKSCATTER': 'm-1 sr-1',
                  'LinCmd': 'cm',
                  'LinPos': 'cm',
                  'METS_METHANE_SCALED': 'mg m-3',
                  'METS_METHANE_VOLT': 'V',
                  'METS_TEMP_SCALED': 'Celsius',
                  'METS_TEMP_VOLT': 'V',
                  'MPE-PAR_IRRADIANCE': 'μE cm-2 s-1',
                  'MPE-PAR_TEMPERATURE': 'Celsius',
                  'MR1000G-RDL_EPS1': 'W kg-1',
                  'MR1000G-RDL_EPS2': 'W kg-1',
                  'MR1000G-RDL_LOG10_EPS1': 'log10 W kg-1',
                  'MR1000G-RDL_LOG10_EPS2': 'log10 W kg-1',
                  'NANOFLU_CONCENTRATION': 'µg L-1',
                  'NANOFLU_TEMPERATURE': 'Celsius',
                  'NAV_LATITUDE': 'degrees_north',
                  'NAV_LONGITUDE': 'degrees_east',
                  'NAV_RESOURCE': 'None',
                  'OCR504_Ed1': 'W m-2 nm-1',
                  'OCR504_Ed2': 'W m-2 nm-1',
                  'OCR504_Ed3': 'W m-2 nm-1',
                  'OCR504_Ed4': 'μE m-2 s-1',
                  'Pa': 'Pa',
                  'Pitch': 'degrees',
                  'Roll': 'degrees',
                  'SEAOWL_BB_700_COUNT': 'counts',
                  'SEAOWL_BB_700_SCALED': 'm-1 sr-1',
                  'SEAOWL_CHL_COUNT': 'counts',
                  'SEAOWL_CHL_SCALED': 'mg m-3',
                  'SEAOWL_FDOM_COUNT': 'counts',
                  'SEAOWL_FDOM_SCALED': 'ppb Quinine Sulfate Equivalent',
                  'SUNA_HUMIDITY_NITRATE': '%',
                  'SUNA_MOLAR_NITRATE': 'µM',
                  'SUNA_NITRATE': 'mg L-1',
                  'SUNA_TEMP_NITRATE': 'Celsius',
                  'SecurityLevel': 'None',
                  'Temperature': 'Celsius',
                  'Voltage': 'V',
                  'AROD_FT_DO_AN': 'counts',
                  'AROD_FT_LED': 'counts',
                  }


def check_yaml(yaml_path, check_urls=False, log_level='INFO'):
    """
    Simple yaml checker for expected SeaExplorer deployment yaml.
    THIS IS NOT A SUBSTITUTE FOR CHECKING YOUR YAML!
    But it will flag some values you might have missed.

    Parameters
    ----------
    yaml_path: path to your yaml file
    check_urls: boolean. If True, checks that urls are reachable. Default: False
    log_level: default to 'INFO'. Can be 'WARNING', or 'ERROR'
    """
    logging.basicConfig(level=log_level)
    _log = logging.getLogger(__name__)
    failures = 0
    _log.info(f'Checking deployment yaml at: {yaml_path}')
    with open(yaml_path) as fin:
        deployment = yaml.safe_load(fin)
    _log.info('read yaml successfully')
    _log.info('Checking top level items')
    for item in ['metadata', 'glider_devices', 'netcdf_variables']:
        if item not in deployment.keys():
            _log.error(f'{item} not found')
            failures += 1
    meta = deployment['metadata']
    _log.info('Checking metadata')
    metadata_keys = ('acknowledgement', 'institution', 'license', 'format_version', 'glider_model',
                     'glider_instrument_name', 'keywords', 'keywords_vocabulary', 'metadata_link',
                     'Metadata_Conventions', 'naming_authority', 'platform', 'processing_level', 'publisher_email',
                     'publisher_name', 'publisher_url', 'references', 'source', 'standard_name_vocabulary',
                     'transmission_system', 'glider_name', 'platform_serial', 'wmo_id', 'comment', 'contributor_name',
                     'contributor_role', 'creator_email', 'creator_name', 'creator_url', 'deployment_id',
                     'deployment_name', 'project', 'project_url', 'summary',
                     'sea_name')

    for key in metadata_keys:
        if key not in deployment['metadata'].keys():
            _log.error(f'{key} not found in metadata')
            failures += 1
    if 'deployment_id' in metadata_keys and 'platform_serial' in meta.keys():
        yaml_file_name = yaml_path.split('/')[-1]
        yml_glider, yml_mission = yaml_file_name.split("_")
        if meta['deployment_id'] not in yml_mission:
            _log.error(f'deployment_id {meta["deployment_id"]} does not match yaml filename {yaml_file_name}')
        if meta['platform_serial'] not in yml_glider:
            _log.error(f'platform_serial {meta["platform_serial"]} does not match yaml filename {yaml_file_name}')

    if check_urls:
        _log.info('Checking urls')
        for url_id in ['creator_url','project_url', 'publisher_url', 'metadata_link']:
            url = deployment['metadata'][url_id]
            try:
                http_code = request.urlopen(url).getcode()
                if int(http_code / 100) != 2:
                    _log.info(f'Warning, did not receive 200 html response from {url}')
            except ValueError:
                _log.error(f"ERROR could not reach {url_id}: {url}")
                failures += 1
    else:
        _log.warning(
            'Warning, not checking urls. Enable this time-consuming check by calling: '
            'python yaml_check.py deployment.yaml True')

    _log.info('Checking glider_devices')
    devices = deployment['glider_devices']
    for name, device in devices.items():
        for field in ('make', 'model', 'serial'):
            if field not in device.keys():
                _log.error(f'{field} not present for glider_devices: {name}')
                failures += 1
        if "calibration_date" in device.keys():
            try:
                date = device["calibration_date"]
                time = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                _log.error(f'sensor {name} calibration date incorrectly formatted. Should be YYYY-MM-DD')
                failures += 1
    check_strings(deployment, _log)
    check_against_meta(meta, _log)
    check_keep_variables(deployment, _log)
    check_variables(deployment['netcdf_variables'], _log)
    check_qc(deployment, _log)
    check_sensor_serials(deployment['glider_devices'], _log)
    check_units(deployment['netcdf_variables'], _log)


def check_qc(deployment, _log):
    if "qc" not in deployment.keys():
        return
    _log.info("Check qc")
    variables = deployment['netcdf_variables']
    qc_items = deployment["qc"]
    for qc_var, qc_dict in qc_items.items():
        if qc_var not in variables:
            _log.error(f"qc variable {qc_var} not present in netcdf variables")
        if qc_dict["value"] not in [1, 2, 3, 4, 9]:
            _log.error(f"qc var {qc_var}  value {qc_dict['value']} invalid. Must be in [1, 2, 3, 4, 9]")
        if "comment" not in qc_dict.keys():
            _log.error(f"qc var {qc_var} has no comment")
        if "start" in qc_dict.keys():
            _log.info('Checking qc start')
            start = qc_dict['start']
            try:
                start_time = datetime.strptime(start, "%Y-%m-%d")
            except ValueError:
                _log.error(f'qc {qc_var} {start} incorrectly formatted. Should be YYYY-MM-DD')
        if "end" in qc_dict.keys():
            end =qc_dict['end']
            try:
                end_time = datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                _log.error(f'qc {qc_var} {end} incorrectly formatted. Should be YYYY-MM-DD')
        if "start" in qc_dict.keys() and "end" in qc_dict.keys():
                deployment_duration = end_time - start_time
                if deployment_duration < timedelta(0):
                    _log.error(f'qc {qc_var} end is sooner than start')
    

def check_against_meta(deployment_meta, _log):
    meta_file = 'meta.yaml'
    if 'shallow' in deployment_meta['glider_model'].lower():
        meta_file = 'meta_shallow.yaml'
    _log.info('Checking against meta.yaml')
    with open(meta_file) as fin:
        meta = yaml.safe_load(fin)['metadata']
    constant_vals = ('acknowledgement', 'institution', 'license', 'format_version', 'glider_model',
                     'glider_instrument_name', 'keywords', 'keywords_vocabulary', 'metadata_link',
                     'Metadata_Conventions', 'naming_authority', 'platform', 'processing_level', 'publisher_email',
                     'publisher_name', 'publisher_url', 'references', 'source', 'standard_name_vocabulary',
                     'transmission_system')
    for key in constant_vals:
        if deployment_meta[key] != meta[key]:
            _log.error(f'{key}: {deployment_meta[key]} does not match value {meta[key]} in meta.yaml')


def check_keep_variables(deployment, _log):
    _log.info('Checking timebase and keep vars')
    devices = deployment['glider_devices']
    variables = deployment['netcdf_variables']
    if variables['timebase']['source'] != 'NAV_LATITUDE':
        _log.error('timebase:source must be NAV_LATITUDE')
    if 'altimeter' in devices:    
        num_sensors = len(devices) - 1
    else:
        num_sensors = len(devices)    
    keeps = variables['keep_variables']
    if len(keeps) != num_sensors:
        _log.error("Number of sensors in glider_devices does not match number of keep variables. Some data will be lost in conversion")
    for var in keeps:
        if var not in variables.keys():
            _log.error(f"keep_variable {var} not found in netcdf_variables")


def check_strings(d, _log):
    for k, v in d.items():
        if isinstance(v, dict):
            _log = check_strings(v, _log)
        else:
            if type(v) is float:
                continue
            if not bool(v):
                _log.error(f'{k} is empty')
    return _log


def check_variables(variables, _log):
    if 'ad2cp_altitude' in variables.keys():
        _log.error('ad2cp_altitude found in variables. We are not currently distributing altitude data. Please remove')
    for name in variables.keys():
        if name in ["keep_variables", "timebase"]:
            continue
        var = variables[name]
        if "irradiance" in var["long_name"] or "PAR" in var["long_name"]:
            if var["average_method"] != "geometric mean":
                _log.error(f"{name} avergage_method should be 'geometric mean'")


def check_sensor_serials(sensors, _log):
    for sensor, attrs in sensors.items():
        if type(attrs['serial']) is not str:
            _log.error(f"type of {sensor} serial number must be a string. It is {type(attrs['serial'])}")


def check_units(variables, _log):
    for key, val in variables.items():
        if key in ['keep_variables', 'timebase', 'time', 'ad2cp_time']:
            continue
        source = val['source']
        if 'units' not in val.keys():
            _log.error(f"no units in yaml for variable {key}")
            continue
        unit = val['units']
        if source not in expected_units.keys():
            _log.error(f"No unit found for {source}")
            continue
        if source == 'TRIDENTE_FDOM':
            if unit not in ['ppb', 'mg m-3']:
                _log.error(f"Bad unit {source}: {unit}")
        else:
            if expected_units[source] != unit:
                _log.error(f"Bad unit {source}: {unit}")


if __name__ == '__main__':
    args = sys.argv
    url_check = False
    if len(args) > 1:
        yaml_file = args[1]
    else:
        sys.exit('Must specify yaml file to parse')
    if len(args) > 2:
        url_check = args[2]
    check_yaml(yaml_file, check_urls=url_check)
