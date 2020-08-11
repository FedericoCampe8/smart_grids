class ComAgent:
    def __init__(self, agent_name, agent_id):
        self.name = agent_name
        self.agent_id = agent_id

    def get_name(self):
        return self.name

    def get_id(self):
        return self.agent_id

    def run(self):
        raise NotImplemented()
