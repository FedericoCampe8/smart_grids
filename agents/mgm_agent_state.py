from kernel.agent_state import *


class MGMAgentState(AgentState):
    def __init__(self, name, agent_id, home, background_loads):
        super().__init__(name, agent_id)

        # Home this agent is modeling
        self.home = home

        self.background_loads = background_loads

        # Current and best schedule for this agent
        self.curr_schedule = None
        self.best_schedule = None

        self.gain = -1

    def get_home(self):
        return self.home

    def get_background_load(self):
        return self.background_loads

    def set_current_schedule(self, schedule):
        self.curr_schedule = schedule

    def get_current_schedule(self):
        return self.curr_schedule

    def set_best_schedule(self, schedule):
        self.best_schedule = schedule

    def get_best_schedule(self):
        return self.best_schedule

    def set_gain(self, gain):
        self.gain = gain

    def get_gain(self):
        return self.gain
