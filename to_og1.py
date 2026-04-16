import yaml
from pathlib import Path
import extract_old_pyglider_yaml_metadata

with open(Path("/home/callum/Documents/community/ocean-gliders-format-vocabularies/yaml/validated_yaml/og1_sensors.yaml")) as fin:
    sensors = yaml.safe_load(fin)

sensor_model_conversion = {
    'Nortek AD2CP': 'Nortek Glider1000 AD2CP Acoustic Doppler Current Profiler',
    'Biospherical MPE-PAR': 'Biospherical Instruments MPE underwater PAR sensor',
    'Franatech METS': 'Franatech METS Methane Sensor',
    'JFE Advantech AROD_FT': 'JFE Advantech Rinko FT ARO-FT oxygen sensor',
    'RBR coda TODO': 'RBR Coda T.ODO Temperature and Dissolved Oxygen Sensor',
    'RBR legato CTD': 'RBR Legato3 CTD',
    'RBR Tridente': 'RBR tridente scattering fluorescence sensor',
    'Rockland Scientific MR1000G-RDL': 'Rockland Scientific MicroRider-1000G turbulence microstructure profiler',
    'SeaBird OCR504': 'Satlantic {Sea-Bird} OCR-504 multispectral radiometer',
    'Seabird Deep SUNA': 'Satlantic {Sea-Bird} Submersible Ultraviolet Nitrate Analyser V2 (SUNA V2) nutrient analyser series',
    'Seabird SlocumCTD': 'Sea-Bird Slocum Glider Payload {GPCTD} CTD',
    'Wetlabs FLNTU': 'WET Labs {Sea-Bird WETLabs} ECO Puck FLNTU-SLC fluorescence turbidity sensor',
    'Wetlabs FLBBPC': 'WET Labs {Sea-Bird WETLabs} ECO Puck Triplet FLBBPC scattering fluorescence sensor',
    'Wetlabs FLBBPE': 'WET Labs {Sea-Bird WETLabs} ECO Puck Triplet FLBBPC scattering fluorescence sensor',
    'Wetlabs FLBBCD': 'WET Labs {Sea-Bird WETLabs} ECO Puck Triplet FLBBCD-SLC scattering fluorescence sensor',
    'hello': 'WET Labs {Sea-Bird WETLabs} SeaOWL UV-A Sea Oil-in-Water Locator',
}


def convert_devices(devices):
    og1_devices = {}
    for name, device in devices.items():
        if name == 'altimeter':
            continue
        if 'NANOFLU' in device['make_model']:
            continue
        sensor_model = sensor_model_conversion[device['make_model']]
        sensor_dict = sensors[sensor_model]

        sensor_type_cf = sensor_dict['sensor_type'].upper().replace(' ', '_').replace('-', '_')
        serial = device['sensor_serial_number']
        sensor_dict['sensor_serial_number'] = serial
        sensor_dict['sensor_calibration_date'] = device['sensor_calibration_date']
        if 'calibration_parameters' in device.keys():
            sensor_dict['calibration_parameters'] = str(device['calibration_parameters'])
        device_name = f"SENSOR_{sensor_type_cf}_{serial}"
        og1_devices[device_name] = sensor_dict

    return og1_devices

with open(Path("/home/callum/Documents/community/ocean-gliders-format-vocabularies/yaml/validated_yaml/og1_variables.yaml")) as fin:
    og1_variables = yaml.safe_load(fin)

sensor_variables = {
    'SeaExplorer': {
        'TIME': 'time',
        'LATITUDE': 'NAV_LATITUDE',
        'LONGITUDE': 'NAV_LONGITUDE',
        'NAV_RESOURCE': 'NAV_RESOURCE',
        'DIVE_NUMBER': 'fnum',
        # lots more here obvs
    },
    'RBR legato CTD': {
        'PRES': 'LEGATO_PRESSURE',
        'TEMP': 'LEGATO_TEMPERATURE',
        'CNDC': 'LEGATO_CONDUCTIVITY',
    },
    'Seabird SlocumCTD': {
        'PRES': 'GPCTD_PRESSURE',
        'TEMP': 'GPCTD_TEMPERATURE',
        'CNDC': 'GPCTD_CONDUCTIVITY',
        # todo this is bad because conductivity has different units here
    },
    'Seabird Deep SUNA':{},# todo currently no nitrate in NVS OG1
    'JFE Advantech AROD_FT': {
        'DOXY': 'AROD_FT_DO',
        'TEMPDOXY': 'AROD_FT_TEMP',
    },
    'RBR coda TODO': {
        'DOXY': 'LEGATO_CODA_DO',
        'TEMPDOXY': 'LEGATO_CODA_TEMPERATURE',
    },
    'Nortek AD2CP': {
        'AD2CP_HEADING': 'AD2CP_HEADING',
        'AD2CP_ROLL': 'AD2CP_ROLL',
        'AD2CP_PITCH': 'AD2CP_PITCH',
      #  'AD2CP_TIME': 'AD2CP_TIME',
    },
    'Wetlabs FLBBPC': {
        'CHLA': 'FLBBPC_CHL_SCALED',
        'FLUOCHLA': 'FLBBPC_CHL_COUNT',
        'PHYCOCYANIN': 'FLBBPC_PC_SCALED',
        #'FLUOPHYCOCYANIN': 'FLBBPC_PC_COUNT',
        'BBP700': 'FLBBPC_BB_700_SCALED',
        'RBBP700': 'FLBBPC_BB_700_COUNT',
    },
    'Wetlabs FLBBPC no raw': {
        'CHLA': 'FLBBPC_CHL_SCALED',
        'PHYCOCYANIN': 'FLBBPC_PC_SCALED',
        'BBP700': 'FLBBPC_BB_700_SCALED',
    },
    'Wetlabs FLBBPE': {
        'CHLA': 'FLBBPE_CHL_SCALED',
        'FLUOCHLA': 'FLBBPE_CHL_COUNT',
        'PHYC': 'FLBBPE_PE_SCALED',
        'FLUOPHYC': 'FLBBPE_PE_COUNT',
        'BBP700': 'FLBBPE_BB_700_SCALED',
        'RBBP700': 'FLBBPE_BB_700_COUNT',
    },
    'Wetlabs FLBBCD': {
        'CHLA': 'FLBBCD_CHL_SCALED',
        'FLUOCHLA': 'FLBBCD_CHL_COUNT',
        'CDOM': 'FLBBCD_CDOM_SCALED',
        'FLUOCDOM': 'FLBBCD_CDOM_COUNT',
        'BBP700': 'FLBBCD_BB_700_SCALED',
        'RBBP700': 'FLBBCD_BB_700_COUNT',
    },
    'Wetlabs FLNTU': {
        'CHLA': 'FLNTU_CHL_SCALED',
        'FLUOCHLA': 'FLNTU_CHL_COUNT',
        'TURB': 'FLNTU_NTU_SCALED',
        #'FLUOTURB': 'FLNTU_NTU_COUNT',
    },
    'Biospherical MPE-PAR': {
        'DPAR': 'MPE-PAR_IRRADIANCE',
    },
    'RBR Tridente': {
        'CHLA': 'TRIDENTE_CHLOROPHYLL',
        'BBP700': 'TRIDENTE_BACKSCATTER',
        'PHYCOCYANIN': 'TRIDENTE_PHYCOCYANIN',
    },
    'RBR Tridente two channel': {
        'CHLA': 'TRIDENTE_CHLOROPHYLL',
        'BBP700': 'TRIDENTE_BACKSCATTER',
    },
    'SeaBird OCR504': {
        'ED380': 'OCR504_Ed1',
        'ED490': 'OCR504_Ed2',
        'ED532': 'OCR504_Ed3',
        'DPAR': 'OCR504_Ed4',
    },
    'RBR Tridente LEGATO': {
        'CHLA': 'LEGATO_TRIDENTE_CHLOROPHYLL',
        'BBP700': 'LEGATO_TRIDENTE_BACKSCATTER',
        'PHYCOCYANIN': 'LEGATO_TRIDENTE_PHYCOCYANIN',
    },
    'RBR Tridente LEGATO_TRIDENTE_PHYCOCYANIN': {
        'CHLA': 'TRIDENTE_CHLOROPHYLL',
        'BBP700': 'TRIDENTE_BACKSCATTER',
        'PHYCOCYANIN': 'LEGATO_TRIDENTE_PHYCOCYANIN',
    },
    'RBR Tridente TRIDENTE_PHYCOCYANIN_FDOM': {
        'CHLA': 'TRIDENTE_CHLOROPHYLL',
        'BBP700': 'TRIDENTE_BACKSCATTER',
        'PHYCOCYANIN': 'TRIDENTE_FDOM',
    },
    'RBR Tridente TRIDENTE_FDOM': {
        'CHLA': 'TRIDENTE_CHLOROPHYLL',
        'BBP700': 'TRIDENTE_BACKSCATTER',
        'FDOM': 'TRIDENTE_FDOM',
    },

}

def add_variables(devices, original_vars):
    variables = {}
    variables['timebase'] = {'source': 'NAV_LATITUDE'}
    keep_vars = []
    devices.pop('altimeter', None)
    devices_to_add = [device['make_model'] for device in devices.values()]
    devices_to_add.append('SeaExplorer')
    for device_name in devices_to_add:
        if device_name not in sensor_variables.keys():
            print("oh no", device_name)
            continue
        if "tridente" in device_name.lower():
            if ('chlorophyll', 'LEGATO_TRIDENTE_CHLOROPHYLL') in original_vars.items():
                device_name = 'RBR Tridente LEGATO'
            elif ('phycocyanin', 'LEGATO_TRIDENTE_PHYCOCYANIN') in original_vars.items():
                device_name = 'RBR Tridente LEGATO_TRIDENTE_PHYCOCYANIN'
            elif ('fdom', 'TRIDENTE_FDOM') in original_vars.items():
                device_name = 'RBR Tridente TRIDENTE_PHYCOCYANIN_FDOM'
            elif ('phycocyanin', 'TRIDENTE_FDOM') in original_vars.items():
                device_name = 'RBR Tridente TRIDENTE_PHYCOCYANIN_FDOM'
            elif 'phycocyanin' not in original_vars.keys() and 'fdom' not in original_vars.keys():
                device_name = 'RBR Tridente two channel'
        if 'flbbpc' in device_name.lower():
            if 'FLBBPC_CHL_COUNT' not in original_vars.values():
                device_name = 'Wetlabs FLBBPC no raw'
        device_variables = sensor_variables[device_name]
        for var_name, source in device_variables.items():
            variable_dict = og1_variables[var_name]
            variable_dict['source'] = source
            if var_name in ['LATITUDE', 'LONGITUDE']:
                variable_dict['conversion'] = 'nmea2deg'
            variables[var_name] = variable_dict
        if device_name not in ['SeaExplorer']:
            if var_name == 'CNDC':
                var_name = 'conductivity'
            keep_vars.append(var_name)
    variables['keep_variables'] = keep_vars
    return variables

def convert_to_og1(yaml_path):
    yaml_out_dir = Path('og1')
    yaml_name = yaml_path.name
    yaml_out = yaml_out_dir / yaml_name.replace('.yml', '.yaml')
    with open('yaml_components/global_metadata.yaml') as fin:
        meta = yaml.safe_load(fin)['metadata']
    out = {}
    platform_deployment_id = yaml_name.split('.')[0]
    platform_serial, deployment_number = yaml_name.split('.')[0].split('_M')
    meta['deployment_id'] = int(deployment_number)
    meta['platform_serial_number'] = platform_serial

    # add platform meta
    with open(Path("yaml_components") / "platform" / f"{platform_serial}.yaml") as fin:
        platform_meta = yaml.safe_load(fin)
    meta = meta | platform_meta

    # add mission meta
    with open(Path("yaml_components") / "mission" / f"{platform_deployment_id}.yaml") as fin:
        mission_meta = yaml.safe_load(fin)
    meta = meta | mission_meta['metadata']
    out['metadata'] = meta

    # convert and add devices
    original_devices = mission_meta['platform_devices']
    og1_devices = convert_devices(original_devices)
    out['glider_devices'] = og1_devices

    # determine variables to add and add them
    original_variables = mission_meta['variables']
    variables = add_variables(original_devices, original_variables)
    out['netcdf_variables'] = variables

    # add pilot QC if present
    if 'qc' in mission_meta.keys():
        out['qc'] = mission_meta['qc']

    # any special exceptions etc.

    with open(yaml_out, "w") as fout:
        yaml.dump(out, fout, allow_unicode=True)

def convert_all_yaml():
    yaml_files = list(Path("mission_yaml").glob("*.yml"))
    yaml_files.sort()
    for yml in yaml_files:
        if "OG" in str(yml):
            continue
        if "SEA070" in str(yml):
            print("Skip, we'll come back to this")
            # todo deal with all the extra sensors on this one
            continue
        print(yml)
        convert_to_og1(yml)

if __name__ == '__main__':
    extract_old_pyglider_yaml_metadata.main()
    convert_to_og1(Path('mission_yaml/SEA066_M60.yml'))
    convert_all_yaml()
