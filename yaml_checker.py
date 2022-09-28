import yaml
import sys
from datetime import datetime, timedelta
from urllib import request
import logging


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
    for item in ['metadata', 'glider_devices', 'netcdf_variables', 'profile_variables']:
        if item not in deployment.keys():
            _log.error(f'{item} not found')
            failures += 1
    meta = deployment['metadata']
    _log.info('Checking metadata')
    metadata_keys = ('acknowledgement', 'institution', 'license', 'format_version', 'glider_model',
                     'glider_instrument_name', 'keywords', 'keywords_vocabulary', 'metadata_link',
                     'Metadata_Conventions', 'naming_authority', 'platform', 'processing_level', 'publisher_email',
                     'publisher_name', 'publisher_url', 'references', 'source', 'standard_name_vocabulary',
                     'transmission_system', 'glider_name', 'glider_serial', 'wmo_id', 'comment', 'contributor_name',
                     'contributor_role', 'creator_email', 'creator_name', 'creator_url', 'deployment_id',
                     'deployment_name', 'deployment_start', 'deployment_end', 'project', 'project_url', 'summary',
                     'sea_name')


    for key in metadata_keys:
        if key not in deployment['metadata'].keys():
            _log.error(f'{key} not found in metadata')
            failures += 1
    if 'deployment_id' in metadata_keys and 'glider_serial' in meta.keys():
        yaml_file_name = yaml_path.split('/')[-1]
        yml_glider, yml_mission = yaml_file_name.split("_")
        if meta['deployment_id'] not in yml_mission:
            _log.error(f'deployment_id {meta["deployment_id"]} does not match yaml filename {yaml_file_name}')
        if meta['glider_serial'] not in yml_glider:
            _log.error(f'glider_serial {meta["glider_serial"]} does not match yaml filename {yaml_file_name}')

    _log.info('Checking dates')
    start = deployment['metadata']['deployment_start']
    end = deployment['metadata']['deployment_end']
    try:
        start_time = datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        _log.error(f'deployment_start {start} incorrectly formatted. Should be YYYY-MM-DD')
        failures += 1
    try:
        end_time = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        _log.error(f'deployment_end {end} incorrectly formatted. Should be YYYY-MM-DD')
        failures += 1
    try:
        deployment_duration = end_time - start_time
        if deployment_duration < timedelta(0):
            _log.error('deployment_end date is sooner than deployment_start date')
            failures += 1
        if deployment_duration > timedelta(days=365):
            _log.warning('inferred deployment duration > 1 year, please check deployment_start and deployment_end')
    except ValueError:
        pass
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
    check_strings(deployment, _log)
    check_against_meta(meta, _log)
    check_keep_variables(deployment, _log)
    check_variables(deployment['netcdf_variables'], _log)


def check_against_meta(deployment_meta, _log):
    _log.info('Checking against meta.yaml')
    with open('meta.yaml') as fin:
        meta = yaml.safe_load(fin)['metadata']
    constant_vals = ('acknowledgement', 'institution', 'license', 'format_version', 'glider_model',
                     'glider_instrument_name', 'keywords', 'keywords_vocabulary', 'metadata_link',
                     'Metadata_Conventions', 'naming_authority', 'platform', 'processing_level', 'publisher_email',
                     'publisher_name', 'publisher_url', 'references', 'source', 'standard_name_vocabulary',
                     'transmission_system', 'sea_name')
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
