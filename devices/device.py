import json


class Device:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.active = False

    def get_name(self):
        return self.name

    def get_location(self):
        return self.location

    def is_active(self):
        return self.active

    def set_active(self, active):
        self.active = active

    def load_device_info(self, name, info):
        raise NotImplemented()
