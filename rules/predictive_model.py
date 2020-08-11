class PredictiveModel:
    """
    Model of an environment. A prediction model has:
    - a sensor s;
    - a set of actuators;
    Each actuator is such that its location is equal to the location of the sensor,
    and so that it has at least one state in its possible states which is associated
    to the property of the sensor.
    The model describes the transition of state property 'p' from state w at time step 't'
    to time step 't+1' when it is affected by a set of actuators.
    """
    predictive_model_map = {}

    def __init__(self, sensor, actuator_list, agent_name):
        self.location = sensor.get_location()

        # Agent owning this predictive model
        self.agent_name = agent_name

        # Sensor
        self.sensor = sensor

        # Sensor property
        self.property = sensor.get_sensor_property()

        # List of actuators
        self.actuators = actuator_list

        # By default set this predictive model as non active
        self.active = False

        # Map this predictive model
        PredictiveModel.predictive_model_map[self.agent_name, (self.location, self.property)] = self

    def get_agent_name(self):
        return self.agent_name

    def get_location(self):
        return self.location

    def get_sensor(self):
        return self.sensor

    def get_property(self):
        return self.property

    def get_actuators(self):
        return self.actuators

    def is_active(self):
        return self.active

    def set_active(self, active):
        self.active = active
        for actuator in self.actuators:
            actuator.set_active(active)
