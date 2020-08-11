import sys


class RulesSchedule:
    def __init__(self, horizon, price_schema):
        self.time_steps = horizon
        self.price_schema = price_schema

        self.power_consumption_kw = [0.0] * self.time_steps
        self.price_per_time_step = [0.0] * self.time_steps
        self.cost = sys.float_info.max

        self.map_schedules = {}

    def insert(self, schedule):
        self.map_schedules[schedule.get_actuator().get_name()] = schedule

    def get(self, actuator_name):
        return self.map_schedules[actuator_name]

    def get_power_consumption_kw(self):
        return self.power_consumption_kw

    def set_power_consumption_kw(self, time, power):
        self.power_consumption_kw[time] = power
        self.price_per_time_step[time] = power * self.price_schema[time]

    def get_schedule_price(self):
        return sum(self.price_per_time_step)

    def get_schedule_power_consumption_kw(self):
        return sum(self.power_consumption_kw)

    def get_price_per_time_step(self):
        return self.price_per_time_step

    def get_cost(self):
        return self.cost

    def set_cost(self, cost):
        self.cost = cost

    def get_schedule(self):
        return self.map_schedules.values()

    def __str__(self):
        sched_str = ''
        for schedule in self.map_schedules.values():
            sched_str += str(schedule) + '\n'
        sched_str += '\tcost: ' + str(self.cost) + '\n'
        sched_str += '\tpower consumption: ' + str(self.power_consumption_kw) + '\n'
        sched_str += '\tprice per time-step: ' + str(self.price_per_time_step) + '\n'
        sched_str += '\ttotal price: ' + str(self.get_schedule_price()) + '\n'
        sched_str += '\ttotal power: ' + str(self.get_schedule_power_consumption_kw()) + '\n'
        return sched_str
