import yaml
from pathlib import Path


def main():
    yaml_files = list(Path("mission_yaml").glob("*.yml"))
    yaml_files.sort()
    for yml in yaml_files:
        mission_id = yml.name.split('.')[0]
        platform = yml.name.split('_')[0]
        if platform == 'OG':
            continue
        with open(yml) as fin:
            deployment = yaml.safe_load(fin)
        meta = deployment['metadata']
        info = {}
        try:
            info['wmo_id'] = int(meta['wmo_id'])
        except:
            info['wmo_id'] = meta['wmo_id']

        info['glider_name'] = meta['glider_name']
        info['platform'] = 'sub-surface gliders'
        info['platform_vocabulary'] = 'http://vocab.nerc.ac.uk/collection/L06/current/27/'
        if platform[:3] == 'SEA':
              info['platform_model'] = 'Alseamar SeaExplorer X2 glider'
              info['platform_model_vocabulary'] = 'http://vocab.nerc.ac.uk/collection/B76/current/B7600035/'
        elif platform[:3] == 'SHW':
            info['platform_model'] = 'Alseamar SeaExplorer X3 shallow glider'
            info['platform_model_vocabulary'] = 'http://vocab.nerc.ac.uk/collection/B76/current/B7600037/'
        print(mission_id)
        with open(Path('yaml_components') / 'platform' / f'{platform}.yaml', 'w') as fout:
            yaml.dump(info, fout)
        mission = {}
        comment = meta['comment']
        if not comment:
            comment = 'None'
        elif type(comment) != str:
            comment = 'None'
        else:
            comment = comment.lstrip(' ').rstrip(' ')
        if not comment:
            comment = 'None'
        metadata = {}
        metadata['comment'] = comment
        metadata['project'] = meta['project'].lstrip(' ').rstrip(' ')
        mission['metadata'] = metadata
        og1_sensors = {}
        original_sensors = deployment['glider_devices']
        for name, ddict in original_sensors.items():
            sensor = {}
            serial = ddict['serial'].lstrip(' ').rstrip(' ')
            sensor['sensor_serial_number'] = serial
            if name == 'altimeter':
                og1_sensors[name] = sensor
                continue
            calibration_date = ddict['calibration_date']
            sensor['sensor_calibration_date'] = calibration_date
            sensor['make_model'] = ddict['make_model']
            if 'calibration_parameters' in ddict.keys():
                sensor['calibration_parameters'] = ddict['calibration_parameters']
            og1_sensors[name] = sensor
        mission['platform_devices'] = og1_sensors
        if 'qc' in deployment.keys():
            mission['qc'] = deployment['qc']
        variables = {}
        for var_name, ddict in deployment['netcdf_variables'].items():
            if var_name in ['keep_variables', 'timebase']:
                continue
            variables[var_name] = ddict['source']
        mission['variables'] = variables


        with open(Path('yaml_components') / 'mission' / f'{mission_id}.yaml', 'w') as fout:
            yaml.dump(mission, fout, allow_unicode=True)

if __name__ == '__main__':
    main()
