import os
import json
from rules.predictive_model_factory import *
from rules.scheduling_rule import *
from devices.actuator import *
from devices.sensor import *

DEVICE_FILE = "data/devices_updated.json"


class Home:
    def __init__(self, home_name, horizon):
        self.name = home_name
        self.actuators = []
        self.sensors = []
        self.predictive_models = []
        self.scheduling_rules = []
        self.horizon = horizon
        self.read_devices()
        self.create_predictive_models()

    def get_name(self):
        return self.name

    def get_horizon(self):
        return self.horizon

    def get_scheduling_rules(self):
        return self.scheduling_rules

    def add_rule(self, rule):
        self.scheduling_rules.append(rule)

    def activate_passive_rules(self):
        # Once all the scheduling rules have been read, we activate a "passive rule" R if and only if
        # there exists an "active rule" which involves devices whose influence the property of R
        for pr in self.scheduling_rules:
            if pr.get_type() == RuleType.PASSIVE:
                pr.set_active(False)

                found = False
                for ar in self.scheduling_rules:
                    if ar.get_type() == RuleType.PASSIVE:
                        continue
                    for actuator in ar.get_predictive_model().get_actuators():
                        # Check if the actuator affects the property of the passive rule
                        if pr.get_property() in actuator.get_sensor_properties():
                            pr.set_active(True)
                            found = True
                            break
                    if found:
                        break

    def read_devices(self):
        device_file_path = os.path.join(os.path.dirname(__file__), DEVICE_FILE)
        with open(device_file_path) as json_file:
            data = json.load(json_file)
            for device_name in data['devices']:
                device_info = data['devices'][device_name]
                if device_info['type'] == 'sensor':
                    device = Sensor()
                    device.load_device_info(device_name, device_info)
                    self.sensors.append(device)
                else:
                    device = Actuator()
                    device.load_device_info(device_name, device_info)
                    self.actuators.append(device)

    def create_predictive_models(self):
        for sensor in self.sensors:
            model = create_predictive_model(sensor, self.actuators, self.name)
            self.predictive_models.append(model)


