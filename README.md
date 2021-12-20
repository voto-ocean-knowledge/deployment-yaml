# deployment-yaml
Master yaml files for all VOTO gliders & deployments

### meta

Top level metadata describing the dataset. Much of this will be constant across the missions, fields such as glider name and deploymend dates must be updated however

### devices

Information on the devices in the glider payload, including calibration dates. This should remain constant for each glider  only changing when sensors are calibrated

### variables

This is the critical section that defines data processing. Only variables enetered correctly in this section will be processed. Pay particular attention to the `timebase` section which defines which timesteps from the raw data will be retained.

# Development

New yaml files should be added to **mission_yaml**. Each file must be named SEA{glider number}_M{mission number}.yml

You can test your yaml by running `yaml_checker.py` and checking the log output in your terminal for potential issues.
