import datetime
import yaml
import pandas as pd
from pathlib import Path
df_cal = pd.read_csv('new_cal.csv')
df_comments = pd.read_csv('piloting_comments.csv')
df_missions = pd.read_csv('https://erddap.observations.voiceoftheocean.org/erddap/tabledap/meta_users_table.csv')
expected_failures = [(70, 29), (57, 58), (57, 75)]
import sys
sys.path.append("/home/callum/Documents/data-flow/raw-to-nc/deployment-yaml")
from yaml_checker import expected_units

def correct_yaml(yaml_path):
    with open(yaml_path) as fin:
        deployment = yaml.safe_load(fin)
    meta = deployment['metadata']
    df_glider = df_missions[df_missions['glider_serial'] == f"SEA{meta['glider_serial'].zfill(3)}"]
    mission = df_glider[df_glider['deployment_id'] == int(meta['deployment_id'])]
    if mission.empty:
        if (int(meta['glider_serial']), int(meta['deployment_id'])) in expected_failures:
            return
        print(f"fail SEA{meta['glider_serial']} M{meta['deployment_id']} ")
        return
    start = str(mission['deployment_start'].values[0])[:10]
    devices = deployment['glider_devices']
    for device_name, cal_dict in devices.items():
        if cal_dict['model'] not in df_cal.model.values:
            continue
        df_model = df_cal[df_cal['model'] == cal_dict['model']]
        try:
            serial = str(int(cal_dict['serial']))
        except ValueError:
            serial = cal_dict['serial']
        # fix for incorrect serial number
        if serial == '2110556':
            serial = '210556'
            cal_dict['serial'] = serial
        df_serial = df_model[df_model['serial'] == serial]
        df_serial = df_serial.sort_values('calibration_date')
        if cal_dict['calibration_date'] in df_serial['calibration_date'].values:
            continue
        df_pre_deployment_cals = df_serial[df_serial['calibration_date'] < start]
        new_cal_date = df_pre_deployment_cals['calibration_date'].values[-1]
        old_cal_date = cal_dict['calibration_date']
        time_diff = (datetime.datetime.strptime(new_cal_date, '%Y-%m-%d') - datetime.datetime.strptime(old_cal_date,
                                                                                                       '%Y-%m-%d')).days
        # fix the calibration date
        deployment['glider_devices'][device_name]['calibration_date'] = new_cal_date
        # Don't warn if time difference is small
        if abs(time_diff) < 30:
            continue
        # Don't warn if calibration month-days are just switched american style
        if old_cal_date == new_cal_date[:5] + new_cal_date[8:] + new_cal_date[4:7]:
            continue
        print(
            f"CORRECTION {old_cal_date} >> {new_cal_date}. {yaml_path.name.split('.')[0]} {cal_dict['model']} {serial}. {time_diff} days ")
    df_glider_comment = df_comments[df_comments['Glider'] == f"SEA{meta['glider_serial'].zfill(3)}"]
    df_mission_comment = df_glider_comment[df_glider_comment['Mission'] == f"M{meta['deployment_id']}"]
    if df_mission_comment.empty:
        print(f"no comment found for {yaml_path.name}")
    if not df_mission_comment.empty:
        comment = df_mission_comment['Comments'].values[0]
        try:
            comment = comment.replace('\n', '. ')
        except:
            print(f'failed to strip comment: {yaml_path} {comment}')
        deployment['metadata']['comment'] = comment
    if 'qc' in deployment:
        if 'cdom' in deployment['qc']:
            if 'Previous deployments with this sensor showed a temporal decrease in CDOM' in deployment['qc']['cdom'][
                'comment']:
                deployment['qc'].pop('cdom')
            if 'Previous deployments with this sensor showed a temporal decrease in CDOM' in \
                    deployment['qc']['cdom_raw']['comment']:
                deployment['qc'].pop('cdom_raw')
    if 'qc' in deployment:
        if not deployment['qc']:
            deployment.pop('qc')

    with open(yaml_path, "w") as fout:
        yaml.dump(deployment, fout, sort_keys=False)


def correct_units(yaml_path):
    with open(yaml_path) as fin:
        deployment = yaml.safe_load(fin)

    variables = deployment['netcdf_variables']
    for key, val in variables.items():
        if key in ['keep_variables', 'timebase', 'time', 'ad2cp_time']:
            continue
        source = val['source']
        if 'units' not in val.keys():
            print(f"no units for {key}")
            continue
        unit = val['units']
        if source not in expected_units.keys():
            print(f"no unit for {yaml_path}: {source}")
            continue
        if expected_units[source] != unit:
            print(f"bad unit {source}: {unit}")
            deployment['netcdf_variables'][key]['units'] = expected_units[source]
    with open(yaml_path, "w") as fout:
       yaml.dump(deployment, fout, sort_keys=False)


if __name__ == '__main__':
    for yml in list(Path("../mission_yaml").glob("*.yml")):
        correct_units(yml)
