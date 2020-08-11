class Solver:
    def __init__(self):
        pass

    def get_schedule(self, neighbor_power):
        """
        Get a valid schedule if the solver terminates within timeout.
        Otherwise it returns a schedule with null actions and high cost.
        """
        raise NotImplemented()

    def get_first_schedule(self):
        """
        Ignore time-out
        :return: first schedule
        """
        raise NotImplemented()

    def get_baseline_schedule(self, neighbor_power):
        """
        :return: baseline comparison schedule
        """
        raise NotImplemented()

    def check(self):
        """
        :return: True if the current instance is satisfied w.r.t. problem constraints.
        Returns false otherwise.
        """
        raise NotImplemented()

    def build_model(self, neighbor_power):
        """
        Constructs a model for the problem instance.
        """
        raise NotImplemented()
