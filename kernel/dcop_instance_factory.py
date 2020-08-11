import json
from kernel.dcop_instance import *
from agents.mgm_agent_state import *
from home import *

DEBUG = False


class DCOPInstanceFactory:
    def __init__(self):
        pass

    def import_dcop_instance(self, file):
        return self.create_shds_instance(file)

    def create_shds_instance(self, file):
        dcop_instance = DCOPInstance()

        with open(file) as json_file:
            data = json.load(json_file)
            horizon = data['horizon']
            agent_list = data['agents']

            agent_id = 0
            for agent_name in agent_list:
                agent = agent_list[agent_name]
                if DEBUG:
                    print(agent)
                background_load = agent['backgroundLoad']

                # Create home
                home = Home(agent_name, horizon)

                # Load rules
                for rule in agent['rules']:
                    # Create a dictionary representing the rule
                    split_rule = rule.split()
                    rule_descriptor = {'location': split_rule[1], 'state_property': split_rule[2],
                                       'relation': split_rule[3], 'goal_state': split_rule[4]}
                    if len(split_rule) > 5:
                        rule_descriptor['time_predicate'] = split_rule[5]
                        rule_descriptor['time'] = split_rule[6]
                        if len(split_rule) == 8:
                            rule_descriptor['time_bound'] = split_rule[7]

                    sched_rule = SchedulingRule(rule_descriptor, home.get_name(), home.get_horizon())
                    home.add_rule(sched_rule)

                # Activate all passive rules
                home.activate_passive_rules()

                # Create and store Agent in DCOP instance
                mgm_agent_state = MGMAgentState(agent_name, agent_id, home, background_load)
                agent_id += 1

                # Add the agent to the DCOP instance
                dcop_instance.add_agent(mgm_agent_state)

            # Link neighborhood
            for agent_state in dcop_instance.get_dcop_agents():
                neighbors = agent_list[agent_state.get_name()]['neighbors']
                for neighbor_name in neighbors:
                    neighbor_agent = dcop_instance.get_agent(neighbor_name)
                    agent_state.register_neighbor(neighbor_agent)

        return dcop_instance
