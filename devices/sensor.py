from devices.device import *
from enum import Enum


def get_sensor_property(prop):
    if prop == 'none':
        return SensorProperty.NONE
    elif prop == 'charge':
        return SensorProperty.CHARGE
    elif prop == 'temperature':
        return SensorProperty.TEMPERATURE
    elif prop == 'temperature_heat':
        return SensorProperty.TEMPERATURE_HEAT
    elif prop == 'temperature_cool':
        return SensorProperty.TEMPERATURE_COOL
    elif prop == 'cleanliness':
        return SensorProperty.CLEANLINESS
    elif prop == 'laundry':
        return SensorProperty.LAUNDRY
    elif prop == 'laundry_wash':
        return SensorProperty.LAUNDRY_WASH
    elif prop == 'laundry_dry':
        return SensorProperty.LAUNDRY_DRY
    elif prop == 'bake':
        return SensorProperty.BAKE
    elif prop == 'water_temp':
        return SensorProperty.WATER_TEMP
    elif prop == 'dish_wash':
        return SensorProperty.DISH_WASH


class SensorProperty(Enum):
    NONE = 1
    CHARGE = 2
    TEMPERATURE = 3
    TEMPERATURE_HEAT = 4
    TEMPERATURE_COOL = 5
    CLEANLINESS = 6
    LAUNDRY = 7
    LAUNDRY_WASH = 8
    LAUNDRY_DRY = 9
    BAKE = 10
    WATER_TEMP = 11
    DISH_WASH = 12


class Sensor(Device):
    def __init__(self, name='', location='', sensor_property=None, measurement=0):
        super().__init__(name, location)

        self.sensor_property = sensor_property

        # Measurement on the current state sensed by this device
        self.current_state = measurement

    def get_sensor_property(self):
        return self.sensor_property

    def get_current_state(self):
        return self.current_state

    def update_state(self, state):
        self.current_state = state

    def load_device_info(self, name, info):
        self.name = name
        self.location = info['location']
        self.current_state = info['current_state']
        self.sensor_property = get_sensor_property(info['sensing_properties'][0])

    def __str__(self):
        str_sensor = "Sensor:\n\tname: " + self.get_name() + '\n'
        str_sensor += "\tlocation: " + self.get_location() + '\n'
        str_sensor += "\tsensor property: " + str(self.sensor_property) + '\n'
        str_sensor += "\tcurrent state: " + str(self.current_state) + '\n'
        return str_sensor
