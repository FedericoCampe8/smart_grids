from devices.sensor import *


class Effect:
    def __init__(self, sensor_property, delta):
        self.property = sensor_property
        self.delta = delta

    def get_property(self):
        return self.property

    def get_delta(self):
        return self.delta


class Action:
    def __init__(self, name, power_kwh):
        self.name = name
        self.power_kwh = power_kwh
        self.effects = []

    def get_name(self):
        return self.name

    def get_power_kwh(self):
        return self.power_kwh

    def get_effects(self):
        return self.effects

    def add_effect(self, sensor_property, delta):
        self.effects.append(Effect(sensor_property, delta))

    def contains(self, effect_property):
        for e in self.get_effects():
            if e.get_property() == effect_property:
                return True
        return False

    def get_delta_of(self, effect_property):
        for e in self.get_effects():
            if e.get_property() == effect_property:
                return e.get_delta()
        return 0
