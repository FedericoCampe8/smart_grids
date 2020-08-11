class ActuatorSchedule:
    def __init__(self, device, horizon):
        self.actuator = device
        self.horizon = horizon
        self.schedule = []
        for time_step in range(self.horizon):
            self.schedule.append(-1)

    def set_schedule(self, schedule):
        self.schedule = schedule

    def set_action(self, time, action_idx):
        self.schedule[time] = action_idx

    def get_actuator(self):
        return self.actuator

    def get_schedule(self):
        return self.schedule

    def __str__(self):
        return 'ActuatorSchedule{' + \
        'device:' + self.actuator.get_name() + \
        ', schedule = ' + str(self.schedule) + '}'