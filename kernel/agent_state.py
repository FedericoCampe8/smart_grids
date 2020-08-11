def neighbor_sorting(neighbor):
    return neighbor.get_id()


class AgentState:
    def __init__(self, name, agent_id):
        self.name = name
        self.agent_id = agent_id
        self.neighbors = []

    def get_name(self):
        return self.name

    def get_id(self):
        return self.agent_id

    def register_neighbor(self, agent_state):
        if agent_state == self:
            return
        if agent_state not in self.neighbors:
            self.neighbors.append(agent_state)
            self.neighbors.sort(key=neighbor_sorting)

    def get_neighbors(self):
        return self.neighbors

