import os
from home import *
from kernel.dcop_instance_factory import *
from agents.mgm_agent import MGMAgent
from test import sat_test

INSTANCE_FILE = "instance/instance_PI_0.json"


def solve(file):
    dcop_factory = DCOPInstanceFactory()
    dcop_instance = dcop_factory.import_dcop_instance(file)

    # Get an agent and run DCOP
    for agent_state in dcop_instance.get_dcop_agents():
        dcop_agent = MGMAgent(agent_state)
        dcop_agent.run()
        break


def main():
    # sat_test()
    # return

    file_instance = os.path.join(os.path.dirname(__file__), INSTANCE_FILE)
    solve(file_instance)

    #home = Home('smart_home')

    #solver = CPSolver()
    #solver.set_variables(solver.create_int_var_array(3, 0, 3))
    #vars = solver.get_variables()
    #solver.search_opt(2*vars[0] + 2*vars[1] + 2 * vars[2], minimize=False)
    #print(solver)


if __name__ == '__main__':
    main()
