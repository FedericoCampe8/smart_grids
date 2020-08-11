import sys
from ortools.sat.python import cp_model
from local_solver.cp_solver import CPSolver, PRICE_SCHEMA
from local_solver.rules_schedule import *
from rules.predictive_model import PredictiveModel
from local_solver.actuator_schedule import *
from rules.scheduling_rule import *

DEBUG = False


class RuleSchedulerSolver(CPSolver):
    def __init__(self, agent_name, scheduling_rules, horizon, background_load_consumption=[]):
        super().__init__()

        # List of rules to schedule
        self.rules = []

        self.horizon = horizon

        # Name of the agent running this solver
        self.agent_name = agent_name

        # Matrix of decision variables
        # x[a][t] is the decision (action) for actuator a at time t
        self.x = []

        # Weights on objective function
        self.alpha_price = 1
        self.alpha_power = 1

        # CP models
        self.cp_model_id = {}
        self.model_map = {}

        # Sensors map
        self.cp_sensor_id = {}
        self.sensor_map = {}

        # Actuator map
        self.cp_actuator_id = {}
        self.actuator_map = {}

        # delta[s][aID][debug] gives the quantitative effect on the sensor
        # property s caused by the device aID on action debug
        self.delta = None

        # power[aID][debug] gives the power (in Watts) consumed by actuator a on action debug
        self.power = None

        # Background load consumption in KWh
        self.bgLoadsKWh = []
        self.powerPriceKWh = [0.198, 0.198, 0.198, 0.198, 0.225, 0.225, 0.249, 0.849, 0.849, 0.225, 0.225, 0.198]

        # EVERSOURCE
        # self.powerPriceKWh = [0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]

        self.aggregated_power_bounds = [0, 0]
        self.aggregated_price_bounds = [0, 0]

        self.init_solver(scheduling_rules, background_load_consumption)
        self.init_domains()
        self.model_declaration()

        # Model variables
        # 'var_predictive_model' will contain the states of each sensor/predictive model
        # for each time-step. These states are calculate/constrained to be the recursive relation
        self.var_predictive_model = None

        # Auxiliary interface variable (x_j_t), to represent the aggregated energy consumed by all the devices
        # in the home at each time step t
        self.var_aggr_power = None

        # Price and energy variables
        self.obj_price = None
        self.obj_power_diff = None
        self.cost_fcn_var = None


    def set_weights(self, w_price, w_power):
        self.alpha_price = w_price
        self.alpha_power = w_power

    def init_solver(self, scheduling_rules, background_load_consumption):
        if background_load_consumption:
            self.bgLoadsKWh = background_load_consumption
        else:
            self.bgLoadsKWh = [0.0] * self.horizon

        # Initialize all(activated) SchedulingRules
        for rule in scheduling_rules:
            if rule.is_active():
                self.rules.append(rule)

        if DEBUG:
            for rule in self.rules:
                print(rule)

        # Initialize predictive models
        model_id = 0
        for rule in self.rules:
            if rule.get_predictive_model() not in self.cp_model_id:
                self.cp_model_id[rule.get_predictive_model()] = model_id
                self.model_map[model_id] = rule.get_predictive_model()
                model_id += 1

        # Populate set of sensors and actuator of the smart-home
        actuator_set = set()
        sensor_id = 0
        for rule in self.rules:
            sensor = rule.get_predictive_model().get_sensor()
            if sensor not in self.sensor_map:
                self.cp_sensor_id[sensor] = sensor_id
                self.sensor_map[sensor_id] = sensor
                sensor_id += 1
            for actuator in rule.get_predictive_model().get_actuators():
                actuator_set.add(actuator)

        actuator_id = 0
        for actuator in actuator_set:
            if actuator not in self.actuator_map:
                self.cp_actuator_id[actuator] = actuator_id
                self.actuator_map[actuator_id] = actuator
                actuator_id += 1

    def init_domains(self):
        aggr_max = 0
        for key, actuator in self.actuator_map.items():
            max_power = 0
            for action in actuator.get_actions():
                max_power = max(max_power, self.scale_and_round_power(action.get_power_kwh()))
            aggr_max += max_power
        self.aggregated_power_bounds[1] = aggr_max

        mp = 0
        for p in PRICE_SCHEMA:
            mp = max(mp, self.scale_and_round_price(p))

        # Max price for energy * sum of max power consumed among all devices
        self.aggregated_price_bounds[1] = mp * aggr_max

    def model_declaration(self):
        # Number of active actuators
        num_actuators = len(self.actuator_map)

        # Properties associated to the rules
        num_predictive_models = len(self.cp_model_id)

        # Max num of actions for any actuator device in the pool of active actuators
        num_actions = 0
        for _, actuator in self.actuator_map.items():
            num_actions = max(num_actions, len(actuator.get_actions()))
        self.populate_delta_array(num_predictive_models, num_actuators, num_actions)
        self.populate_power_array(num_actuators, num_actions)

    def populate_delta_array(self, num_predictive_models, num_actuators, num_actions):
        """
        Populate the array delta:
        delta[s][aID][debug] gives the quantitative effect on the sensor property s (MODEL)
        caused by the device aID on action debug.
        NOTE: each delta value is scaled by 'deltaScale'
        :param num_predictive_models: total number of predictive models (from scheduling rules)
        :param num_actuators: total number of actuators
        :param num_actions: maximum number of actions among all actuators
        """
        if DEBUG:
            print("Populate Delta array")

        self.delta = []
        for _ in range(num_predictive_models):
            s_list = []
            for _ in range(num_actuators):
                s_list.append([0] * num_actions)
            self.delta.append(s_list)
        for m_id in range(num_predictive_models):
            model = self.model_map[m_id]
            sensor_property = model.get_property()
            if DEBUG:
                print("Sensor property of the model: ", print(sensor_property))
            for actuator in model.get_actuators():
                if DEBUG:
                    print("Actuator: ", actuator.get_name())
                a_id = self.cp_actuator_id[actuator]
                s_id = 0
                for action in actuator.get_actions():
                    self.delta[m_id][a_id][s_id] = self.scale_and_round_delta(action.get_delta_of(sensor_property))
                    if DEBUG:
                        print("Delta[" + str(m_id) + "][" + str(a_id) + "][" + str(s_id) + "] = " +
                              str(self.delta[m_id][a_id][s_id]))
                        print("\tDelta[" + str(sensor_property) + "][" + actuator.get_name() +
                              "][" + action.get_name() + "] = " +
                              str(self.delta[m_id][a_id][s_id]))
                    s_id += 1

    def populate_power_array(self, num_actuators, num_actions):
        """
        It populate the array power, used in the constraint solver.
        power[aID][debug] gives the power (in Watts) consumed by actuator a on action debug
        :param num_actuators: total number of actuators
        :param num_actions: maximum number of actions among all actuators
        :return:
        """
        if DEBUG:
            print("Populate Power array")

        self.power = []
        for _ in range(num_actuators):
            self.power.append([0] * num_actions)

        for a_id in range(num_actuators):
            actuator = self.actuator_map[a_id]
            s_id = 0
            for action in actuator.get_actions():
                self.power[a_id][s_id] = self.scale_and_round_power(action.get_power_kwh())
                if DEBUG:
                    print("actuator " + actuator.get_name() + ": action = " + action.get_name() + " pw " +
                          str(self.power[a_id][s_id]) + ' (' + str(a_id) + ', ' + str(s_id) + ')')
                s_id += 1

    def build_model(self, neighbor_power):
        # Number of active actuators
        num_actuators = len(self.actuator_map)

        # Properties associated to the rules
        predictive_model_size = len(self.cp_model_id)

        max_neighbors_power_consumption = self.scale_and_round_power(max(neighbor_power))
        min_neighbors_power_consumption = self.scale_and_round_power(max(neighbor_power))
        max_background_load = self.scale_and_round_power(max(self.bgLoadsKWh))
        min_background_load = self.scale_and_round_power(min(self.bgLoadsKWh))

        # CP declarations: variables
        # Predictive model variables: these variables constrain the predictive models,
        # i.e., these variables are used to ensure that each schedule of a set of actuators affecting the
        # state property 'p' and described by its predictive model satisfies the scheduling rule
        # over the state property 'p'.
        # In other words, 'var_predictive_model' will contain the states of each sensor/predictive model
        # for each time-step. These states are calculate/constrained to be the recursive relation
        self.var_predictive_model = self.create_int_var_2d_array(predictive_model_size,
                                                                 self.horizon,
                                                                 self.get_domain_neg_inf(),
                                                                 self.get_domain_pos_inf(),
                                                                 'predModel_')

        # Auxiliary interface variable (x_j_t), to represent the aggregated energy consumed by all the devices
        # in the home at each time step t
        self.var_aggr_power = self.create_int_var_array(self.horizon,
                                                        self.aggregated_power_bounds[0] + min_background_load,
                                                        self.aggregated_power_bounds[1] + max_background_load,
                                                        'aggrPower_')

        # For each actuator z and for each time step t, create a variable
        # x_z_t whose domain is the set of actions in A_z
        for a_id in range(num_actuators):
            actuator = self.actuator_map[a_id]
            if DEBUG:
                print("For ", actuator.get_name(), " var 0.. ", len(actuator.get_actions()) - 1)
            self.x.append(self.create_int_var_array(self.horizon, 0, len(actuator.get_actions()) - 1,
                                                    'x_' + actuator.get_name()))

        # Objective variable: the dollar price of the final solution
        lb_obj_price = self.aggregated_price_bounds[0]
        ub_obj_price = self.aggregated_price_bounds[1]
        self.obj_price = self.create_int_var(lb_obj_price, ub_obj_price, 'price')

        # Objective variable (penalty): the power difference objective with domains
        # min = (0) all off + min_neighb^2
        # max = ((maxAggrPw all on at t) + (max_neighb_pw))^2
        lb_obj_power_diff = int(
            pow(self.aggregated_power_bounds[0] + min_neighbors_power_consumption, 2)) * self.horizon
        ub_obj_power_diff = int(
            pow(self.aggregated_power_bounds[1] + max_neighbors_power_consumption, 2)) * self.horizon
        self.obj_power_diff = self.create_int_var(lb_obj_power_diff, ub_obj_power_diff, 'pwDiff')

        # CP declarations: constraints
        # Predictive model constraints (local hard constraints).
        # This constraint models the recursive relation of the predictive models, for each state property p
        # according to the scheduling represented by x
        for pmodel_id in self.cp_model_id.values():
            self.create_predictive_model_constraints(self.model_map[pmodel_id],
                                                     self.var_predictive_model[pmodel_id],
                                                     self.delta[pmodel_id],
                                                     self.x)

        # Active rules (local soft constraints).
        # These constraints involve only variables controlled by the agent. These costs correspond
        # to the weighted summation of monetary costs.
        # In other words, the constraint before bounded 'var_predictive_model' to the predictive model
        # recursive relation, while this constraint bounds 'var_predictive_model' to the final value
        # imposed by the rule defined by the user of the smart device
        for rule in self.rules:
            # For all scheduling rules defined by the user of the device
            predictive_model = PredictiveModel.predictive_model_map[
                self.agent_name, (rule.get_location(), rule.get_property())]
            model_id = self.cp_model_id[predictive_model]
            self.create_rule_constraint(rule, self.var_predictive_model[model_id])

        # Global soft constraints: aggregate power reduction.
        # These constraints correspond to the peak energy consumption
        for time_step in range(self.horizon):
            self.create_aggregate_power_constraint(self.var_aggr_power[time_step], self.x, time_step, self.power,
                                                   self.bgLoadsKWh[time_step])

        # CP declarations: objective
        # 1. Minimize sum_t1 sum_t2 |power(t1) - power(t2)| -> this is the overall energy peak
        self.create_objective_peaks(self.obj_power_diff, self.var_aggr_power, neighbor_power)

        # 2. Total power price
        self.create_objective_price(self.obj_price, self.var_aggr_power, self.powerPriceKWh)

        # Constrain the (total) cost function variable
        max_cost_fcn_dom = (self.alpha_power * ub_obj_power_diff + self.alpha_price * ub_obj_price)
        self.cost_fcn_var = self.create_int_var(0, max_cost_fcn_dom, 'costFcn')

        # To run optimization based on the price only uncomment the following
        # self.alpha_power = 0
        self.model.Add(self.alpha_power * self.obj_power_diff + self.alpha_price * self.obj_price == self.cost_fcn_var)

    def create_predictive_model_constraints(self, pmodel, var_pmodel, delta_pmodel, x):
        # Get initial state of the sensor within the predictive model for that sensor

        # Constrain the initial state of the predictive model to be the initial state of the sensor.
        # This is the base of the recursion, the value is simply the initial state of the sensor
        cp_initial_state = self.scale_and_round_delta(pmodel.get_sensor().get_current_state())
        self.model.Add(var_pmodel[0] == cp_initial_state)

        # Constrain all other steps of the predictive model to respect the predictive model recursive properties
        time_step = 1
        for _ in range(self.horizon - 1):
            # Use aux var to compute the sum of property[t] + sum_delta[action_a]
            aux_vars = []

            # Constraint sum
            for actuator in pmodel.get_actuators():
                actuator_id = self.cp_actuator_id[actuator]
                name = 'aux_delta_' + actuator.get_name() + '(t=' + str(time_step) + ')'
                var_aux = self.create_int_var(min(delta_pmodel[actuator_id]), max(delta_pmodel[actuator_id]), name)

                x_dom = len(actuator.get_actions())
                local_delta = delta_pmodel[actuator_id]
                if x_dom > len(local_delta):
                    local_delta += [0] * (x_dom - len(local_delta))
                elif x_dom < len(local_delta):
                    local_delta = local_delta[:x_dom]

                # Constrain the auxiliary variable 'var_aux' to be the delta of the given action
                # at the given time step (x_z_t):
                # var_aux = delta[x_z_t]
                self.model.AddElement(x[actuator_id][time_step], local_delta, var_aux)
                aux_vars.append(var_aux)

            # Assign previous element to aux_vars[time_step]
            aux_vars.append(var_pmodel[time_step - 1])

            # Sum variables to create:
            # var_pmodel[time_step + 1] = var_pmodel[time_step] + Sum delta[action_a]
            # This holds for each time-step. In other words, this constraint ensure the
            # recursive definition of the predictive model where
            # state[t + 1] = state[t] + delta('all actuators affecting state p')
            self.model.Add(cp_model.LinearExpr.Sum(aux_vars) == var_pmodel[time_step])
            # self.model.Add(sum(aux_vars) == var_pmodel[time_step])

            # Next time step
            time_step += 1

    def create_rule_constraint(self, rule, var_pmodel):
        constraint_list = []
        for time_step in range(rule.get_time_start(), rule.get_time_end() + 1):
            goal_state = self.scale_and_round_delta(rule.get_goal_state())
            rule_relation = rule.get_relation()
            bool_var_name = 'b_' + str(rule.get_rule_id())
            bool_var = self.model.NewBoolVar(bool_var_name)
            if rule_relation == BinaryRelation.EQ:
                self.model.Add(var_pmodel[time_step] == goal_state).OnlyEnforceIf(bool_var)
            elif rule_relation == BinaryRelation.NEQ:
                self.model.Add(var_pmodel[time_step] != goal_state).OnlyEnforceIf(bool_var)
            elif rule_relation == BinaryRelation.LT:
                self.model.Add(var_pmodel[time_step] < goal_state).OnlyEnforceIf(bool_var)
            elif rule_relation == BinaryRelation.GT:
                self.model.Add(var_pmodel[time_step] > goal_state).OnlyEnforceIf(bool_var)
            elif rule_relation == BinaryRelation.LEQ:
                self.model.Add(var_pmodel[time_step] <= goal_state).OnlyEnforceIf(bool_var)
            elif rule_relation == BinaryRelation.GEQ:
                self.model.Add(var_pmodel[time_step] >= goal_state).OnlyEnforceIf(bool_var)
            else:
                raise Exception('Unspecified scheduling rule')
            constraint_list.append(bool_var)
        if rule.get_predicate() == RuleTimePredicate.CONJUNCTION:
            self.model.AddBoolAnd(constraint_list)
        else:
            self.model.AddBoolOr(constraint_list)

    def create_aggregate_power_constraint(self, var_aggr_power, x, time_step, power, background_load_kw):
        aux_vars = []
        num_actuators = len(power)
        idx = 0
        for actuator_id in range(num_actuators):
            var_name = 'aux_aggr_power_' + str(actuator_id) + '_' + str(idx)
            var_aux = self.create_int_var(min(power[actuator_id]), max(power[actuator_id]), var_name)

            power_actuator = power[actuator_id]
            x_dom = len(self.actuator_map[actuator_id].get_actions())
            if x_dom > len(power_actuator):
                power_actuator += [0] * (x_dom - len(power_actuator))
            elif x_dom < len(power_actuator):
                power_actuator = power_actuator[:x_dom]

            # For each time-step the action x_z_t takes a certain power.
            # Map power to action:
            # var_aux = power_actuator[x_z_t]
            self.model.AddElement(x[actuator_id][time_step], power_actuator, var_aux)
            aux_vars.append(var_aux)

            idx += 1

        # Add the background load
        var_aux_background = self.create_int_var(self.scale_and_round_power(background_load_kw),
                                                 self.scale_and_round_power(background_load_kw),
                                                 'background_load_' + str(time_step))
        aux_vars.append(var_aux_background)

        # The sum of all the actuator's power consumption plus the background load must equal var_aggr_power
        # var_aggr_power = sum action's power + background load
        self.model.Add(cp_model.LinearExpr.Sum(aux_vars) == var_aggr_power)

    def create_objective_peaks(self, obj_power_peak, var_aggr_power, neighbors_kw):
        # Note:
        # var_aggr_power ia an auxiliary interface variable (x_j_t), to represent the aggregated energy
        # consumed by all the devices in the home at each time step.
        # This was constrained to be equal to all devices power consumption plus the background load

        # stores vars to sum (external summation)
        aux_vars = []

        #  stores aggregated power of this agent + neighbor agents per time step
        aux_vars_power = []
        for time_step in range(self.horizon):
            aggr_power_lb = self.aggregated_power_bounds[0] + self.scale_and_round_power(neighbors_kw[time_step])
            aggr_power_ub = self.aggregated_power_bounds[1] + self.scale_and_round_power(neighbors_kw[time_step])

            # Current agent power consumed at time time_step + neighbors' agent power consumed at time time_step
            aux_vars_power.append(self.create_int_var(aggr_power_lb, aggr_power_ub, 'aux_power_' + str(time_step)))
            self.model.Add(var_aggr_power[time_step] + self.scale_and_round_power(neighbors_kw[time_step]) ==
                           aux_vars_power[time_step])

            # Square auxVarsPower
            var_square_aux = self.create_int_var(aggr_power_lb * aggr_power_lb,
                                                 aggr_power_ub * aggr_power_ub,
                                                 'var_square_aux' + str(time_step))
            self.model.AddMultiplicationEquality(var_square_aux, [aux_vars_power[time_step], aux_vars_power[time_step]])
            aux_vars.append(var_square_aux)

        # Sum the squares of aux_vars_power[time_step]
        self.model.Add(cp_model.LinearExpr.Sum(aux_vars) == obj_power_peak)

    def create_objective_price(self, obj_price, var_aggr_power, power_price_kwh):
        scaled_price = []
        for time_step in range(self.horizon):
            if DEBUG:
                print("price at ", str(time_step), "is ", power_price_kwh[time_step], "rounded ",
                      self.scale_and_round_price(power_price_kwh[time_step]))
            scaled_price.append(self.scale_and_round_price(power_price_kwh[time_step]))

        # Sum the current aggregated power per time step (in Watts) * the price (in KwH)
        self.model.Add(cp_model.LinearExpr.ScalProd(var_aggr_power, scaled_price) == obj_price)

    def get_schedule(self, neighbor_power):
        self.build_model(neighbor_power)

        # Run optimization on the energy model
        self.search_opt(self.cost_fcn_var)

        if self.get_status() == cp_model.FEASIBLE or self.get_status() == cp_model.OPTIMAL:
            if DEBUG:
                print("Home ", self.agent_name, "run satisfied")
                self.print_predictive_models()
                print(self.obj_price.Name() + ' = ' + str(self.solver.Value(self.obj_price)))
                print(self.obj_power_diff.Name() + ' = ' + str(self.solver.Value(self.obj_power_diff)))
                print(self.cost_fcn_var.Name() + ' = ' + str(self.solver.Value(self.cost_fcn_var)))
            return self.construct_schedule()
        else:
            if DEBUG:
                print("Home ", self.agent_name, "no solutions")

            # If search fails, create a generic RulesSchedule object and set cost to max size of double
            rule_schedule = RulesSchedule(self.horizon, self.powerPriceKWh)
            return rule_schedule

    def get_first_schedule(self):
        """
        Similar to 'get_schedule' but with no neighbor power.
        :return: the schedule.
        """
        neighbor_power = [0] * self.horizon
        self.build_model(neighbor_power)

        # Run optimization on the energy model
        # self.search_opt(self.cost_fcn_var)

        # Run satisfaction on the energy model
        self.search_sat()
        if self.get_status() == cp_model.FEASIBLE or self.get_status() == cp_model.OPTIMAL:
            if DEBUG:
                print("Home ", self.agent_name, "run satisfied")
                self.print_predictive_models()
                print(self.obj_price.Name() + ' = ' + str(self.solver.Value(self.obj_price)))
                print(self.obj_power_diff.Name() + ' = ' + str(self.solver.Value(self.obj_power_diff)))
                print(self.cost_fcn_var.Name() + ' = ' + str(self.solver.Value(self.cost_fcn_var)))
            return self.construct_schedule()
        else:
            if DEBUG:
                print("Home ", self.agent_name, "no solutions")

            # If search fails, create a generic RulesSchedule object and set cost to max size of double
            rule_schedule = RulesSchedule(self.horizon, self.powerPriceKWh)
            return rule_schedule

    def get_baseline_schedule(self, neighbor_power):
        """
        Similar to 'get_schedule' but with search_smallest_domain.
        :param neighbor_power: neighborhood power.
        :return: the schedule.
        """
        self.build_model(neighbor_power)

        x_vars = []
        for x_list in self.x:
            for var_elem in x_list:
                x_vars.append(var_elem)

        self.search_smallest_domain(x_vars)
        if self.get_status() == cp_model.FEASIBLE or self.get_status() == cp_model.OPTIMAL:
            if DEBUG:
                print("Home ", self.agent_name, "run satisfied")
                self.print_predictive_models()
                print(self.obj_price.Name() + ' = ' + str(self.solver.Value(self.obj_price)))
                print(self.obj_power_diff.Name() + ' = ' + str(self.solver.Value(self.obj_power_diff)))
                print(self.cost_fcn_var.Name() + ' = ' + str(self.solver.Value(self.cost_fcn_var)))
            return self.construct_schedule()
        else:
            if DEBUG:
                print("Home ", self.agent_name, "no solutions")

            # If search fails, create a generic RulesSchedule object and set cost to max size of double
            rule_schedule = RulesSchedule(self.horizon, self.powerPriceKWh)
            return rule_schedule

    def construct_schedule(self):
        rule_schedule = RulesSchedule(self.horizon, self.powerPriceKWh)
        num_actuators = len(self.actuator_map)
        for actuator_id in range(num_actuators):
            actuator = self.actuator_map[actuator_id]
            actuator_schedule = ActuatorSchedule(actuator, self.horizon)
            for time_step in range(self.horizon):
                actuator_schedule.set_action(time_step, self.solver.Value(self.x[actuator_id][time_step]))

            # Store schedule for device actuator_id
            rule_schedule.insert(actuator_schedule)

        # Store power result in the rule_schedule
        power_cost = 0
        price_cost = 0
        for time_step in range(self.horizon):
            power = self.solver.Value(self.var_aggr_power[time_step]) / (self.get_kilowatt_to_watt() * 1.0)
            rule_schedule.set_power_consumption_kw(time_step, power)
            power_cost += power * power
            price_cost += power * self.powerPriceKWh[time_step]

        # Set cost of this schedule
        rule_schedule.set_cost(power_cost + price_cost)
        return rule_schedule

    def print_predictive_models(self):
        for model, model_id in self.cp_model_id.items():
            print("Model ", str(model_id), '-', model.get_sensor().get_name())
            str_model = '\t'
            for time_step in range(self.horizon):
                str_model += str(self.solver.Value(self.var_predictive_model[model_id][time_step]) / 10) + ' '
            print(str_model)
