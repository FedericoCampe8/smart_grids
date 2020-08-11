from communication.dcop_agent import *
from agents.mgm_agent_actions import *


class MGMAgent(DCOPAgent):
    def __init__(self, agent_state):
        super().__init__(agent_state.get_name(), agent_state.get_id())

        # Agent's state
        self.agent_state = agent_state

        # Agent actions
        self.actions = None
        self.add_agent_actions()

        # MGM cycle
        self.current_cycle = 0

    def add_agent_actions(self):
        self.actions = MGMAgentActions(self.agent_state, solver_timeout=10000, w_price=1.0, w_power=1.0)

    def run(self):
        print("Agent ", self.get_name(), " running")
        if not self.actions.compute_first_schedule():
            print("Failed computing first schedule")
            return

        # print(self.actions.get_current_schedule())

        # Send energy profile
        # ...
        # Wait to receive energy profiles
        # ...
        # Compute current schedule and update best one
        if self.actions.compute_schedule(self.current_cycle):
            # NOTE: REPLACE THE BELOW WITH THE RIGHT SCHEDULE
            print(self.actions.get_current_schedule())
            self.actions.update_best_schedule(self.actions.get_current_schedule())
        else:
            print("Error: schedule not found")

        # Start the MGM loop
        while not self.termination_condition():
            self.current_cycle += 1
            self.mgm_cycle()

    def termination_condition(self):
        # return self.current_cycle >= 5
        return True

    def mgm_cycle(self):
        # Send energy profile of the best schedule
        # for neighbor in self.get_neighbors_reference():
            #neighbor.send_message(...)

        # Wait to receive energy profiles
        if self.actions.compute_schedule(self.current_cycle):
            self.actions.compute_gain()

            # Send gain message to neighbors
            # ...
            # Wait to receive gains

            # Check if this agent has the best gain: if so, best_schedule <- current_schedule
            if self.actions.is_best_gain(self.current_cycle):
                self.actions.update_best_schedule(self.actions.get_current_schedule())
        else:
            print("Error: schedule not found")
