import sys
from kernel.agent_actions import *
from local_solver.rule_scheduler_solver import RuleSchedulerSolver

DEBUG = False


class MGMAgentActions(AgentActions):
    def __init__(self, agent_state, solver_timeout, w_price, w_power):
        super().__init__(agent_state)

        # Get home of this agent
        self.home = agent_state.get_home()

        # Initialize the solver run by the agent
        self.solver = RuleSchedulerSolver(self.home.get_name(), self.home.get_scheduling_rules(),
                                          self.home.get_horizon(),
                                          self.agent_state.get_background_load())
        self.solver.set_timeout_msec(solver_timeout)
        self.solver.set_weights(int(w_price), int(w_power))

    def update_best_schedule(self, schedule):
        self.agent_state.set_best_schedule(schedule)

    def get_current_schedule(self):
        return self.agent_state.get_current_schedule()

    def compute_first_schedule(self):
        if DEBUG:
            print('run solver')
        schedule = self.solver.get_first_schedule()
        if DEBUG:
            print(schedule)

        self.agent_state.set_current_schedule(schedule)
        return schedule.get_cost() < sys.float_info.max

    def compute_schedule(self, cycle):
        neighbor_loads = [0] * self.home.get_horizon()
        for agent_state in self.agent_state.get_neighbors():
            # Received energy profile...
            for time_step in range(self.home.get_horizon()):
                neighbor_loads[time_step] += 0 #agent_state.

        schedule = self.solver.get_schedule(neighbor_loads)
        self.agent_state.set_current_schedule(schedule)
        return schedule.get_cost() < sys.float_info.max

    def compute_gain(self):
        self.agent_state.set_gain(max(
            0, self.agent_state.get_best_schedule().get_cost() - self.agent_state.get_current_schedule().get_cost()))

    def is_best_gain(self):
        return True
