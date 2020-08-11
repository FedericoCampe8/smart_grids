from devices.device import *
from devices.action import *
from devices.sensor import *


def action_sorting(action):
    return action.get_power_kwh()


class Actuator(Device):
    def __init__(self, name='', location=''):
        super().__init__(name, location)

        # Actions the actuator can take
        self.actions = []

    def load_device_info(self, name, info):
        self.name = name
        self.location = info['location']
        actions = info['actions']
        for act_name in actions:
            action_name = act_name
            action_power = actions[act_name]['power_consumed']
            action = Action(action_name, action_power)

            effect_list = actions[act_name]['effects']
            for effect in effect_list:
                action.add_effect(get_sensor_property(effect['property']), effect['delta'])
            self.add_action(action)

    def add_action(self, action):
        self.actions.append(action)

        # Sort actions based on their power consumption
        self.actions.sort(key=action_sorting)

    def get_actions(self):
        return self.actions

    def get_sensor_properties(self):
        """
        :return: all sensor properties affected by this device actions
        """
        prop = set()
        for action in self.actions:
            for effect in action.get_effects():
                prop.add(effect.get_property())
        return prop
