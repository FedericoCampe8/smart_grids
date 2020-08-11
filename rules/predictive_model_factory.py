from rules.predictive_model import *


def create_predictive_model(sensor, actuator_list, agent_name):
    model_actuators = []

    # Get the list of actuators that are in the same location of the sensor
    # and that affect the properties of the sensor.
    # Note: a sensor's location can be within the actuator itself.
    # Therefore, sensor.get_location() can be the same as the actuator.get_name()
    for actuator in actuator_list:
        if ((actuator.get_location() == sensor.get_location()) or
                (sensor.get_location() == actuator.get_name()) and
                (sensor.get_sensor_property() in actuator.get_sensor_properties())):
            model_actuators.append(actuator)
    if model_actuators:
        return PredictiveModel(sensor, model_actuators, agent_name)
    else:
        return None

