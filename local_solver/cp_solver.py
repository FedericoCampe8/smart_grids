import sys
from local_solver.solver import Solver
from ortools.sat.python import cp_model

PRICE_SCHEMA = [0.198, 0.198, 0.198, 0.198, 0.225, 0.225, 0.249, 0.849, 0.849, 0.225, 0.225, 0.198]


class CPSolver(Solver):
    def __init__(self):
        super().__init__()

        # CP model
        self.model = None

        # CP solver
        self.solver = cp_model.CpSolver()

        # Status of the search process
        self.status = cp_model.UNKNOWN

        # List of decision variables
        self.vars = []

        # Cost function decision variable
        self.cost_function = None

        # Best cost (upper bound)
        self.best_cost = sys.maxsize

        # Timeout on the solver
        self.timeout_ms = 30000

        # Precision factors for rounding doubles
        # - power
        self.kilowatt_to_watt = 10
        # - price
        self.cents_to_dollars = 100
        # - deltas
        self.delta_scale = 10
        self.scale_factor = self.kilowatt_to_watt * self.cents_to_dollars

        # Initialize the model
        self.model = cp_model.CpModel()

    def get_domain_neg_inf(self):
        return cp_model.INT32_MIN

    def get_domain_pos_inf(self):
        return cp_model.INT32_MAX

    def get_cost_function(self):
        return self.cost_function

    def get_best_cost(self):
        return self.best_cost

    def get_status(self):
        return self.status

    def get_kilowatt_to_watt(self):
        return self.kilowatt_to_watt

    def scale_and_round_power(self, val):
        return int(val * self.kilowatt_to_watt)

    def scale_and_round_price(self, val):
        return int(val * self.cents_to_dollars)

    def scale_and_round_delta(self, val):
        return int(val * self.delta_scale)

    def set_timeout_msec(self, msec):
        self.timeout_ms = msec

    def set_variables(self, var_list):
        self.vars = var_list

    def get_variables(self):
        return self.vars

    def create_int_var(self, min_dom, max_dom, name='v'):
        var = self.model.NewIntVar(min_dom, max_dom, name)
        self.vars.append(var)
        return var

    def create_int_var_array(self, len_array, min_dom, max_dom, name='v_'):
        var_array = []
        for idx in range(len_array):
            var_name = name + str(idx)
            var = self.model.NewIntVar(min_dom, max_dom, var_name)
            self.vars.append(var)
            var_array.append(var)
        return var_array

    def create_int_var_2d_array(self, num_rows, num_cols, min_dom, max_dom, name='v_'):
        var_array = []
        for r_idx in range(num_rows):
            row_array = []
            for c_idx in range(num_cols):
                var_name = name + str(r_idx) + "_" + str(c_idx)
                var = self.model.NewIntVar(min_dom, max_dom, var_name)
                self.vars.append(var)
                row_array.append(var)
            var_array.append(row_array)
        return var_array

    def search_sat(self):
        """
        Search for a sat solution
        :return: the status of the search
        """
        print(type(self.model.Proto()))
        self.status = self.solver.Solve(self.model)
        return self.status

    def search_opt(self, cost_fcn, minimize=True):
        self.cost_function = cost_fcn
        if minimize:
            self.model.Minimize(self.cost_function)
        else:
            self.model.Maximize(self.cost_function)

        self.search_sat()
        self.cost_function = self.solver.ObjectiveValue()
        return self.status

    def search_smallest_domain(self, x):
        self.model.AddDecisionStrategy(x, cp_model.CHOOSE_FIRST, cp_model.CHOOSE_MIN_DOMAIN_SIZE)
        self.solver.parameters.search_branching = cp_model.FIXED_SEARCH
        return self.search_sat()

    def __str__(self):
        model_values = ''
        model_values += str(self.cost_function) + '\n'
        for var in self.vars:
            model_values += var.Name() + ' = ' + str(self.solver.Value(var)) + '\n'
        return model_values
