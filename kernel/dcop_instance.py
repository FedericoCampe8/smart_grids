class DCOPInstance:
    def __init__(self):
        self.agent_id_hash_map = {}
        self.agent_hash_map = {}

    def add_agent(self, agent_state):
        self.agent_id_hash_map[agent_state.get_name()] = agent_state.get_id()
        self.agent_hash_map[agent_state.get_id()] = agent_state

    def get_agent(self, agent_name):
        return self.agent_hash_map[self.agent_id_hash_map[agent_name]]

    def get_dcop_agents(self):
        return self.agent_hash_map.values()
