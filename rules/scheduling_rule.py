from devices.sensor import *
from rules.predictive_model import *

def get_relation_from_string(rel):
    if rel == 'eq':
        return BinaryRelation.EQ
    elif rel == 'neq':
        return BinaryRelation.NEQ
    elif rel == 'lt':
        return BinaryRelation.LT
    elif rel == 'gt':
        return BinaryRelation.GT
    elif rel == 'leq':
        return BinaryRelation.LEQ
    elif rel == 'geq':
        return BinaryRelation.GEQ
    else:
        raise Exception('Unrecognized relation')


class BinaryRelation(Enum):
    EQ = 1
    NEQ = 2
    LT = 3
    GT = 4
    LEQ = 5
    GEQ = 6


class RuleTimePredicate(Enum):
    CONJUNCTION = 1
    DISJUNCTION = 2


class RuleTimePrefix(Enum):
    BEFORE = 1
    AFTER = 2
    AT = 3
    WITHIN = 4


class RuleType(Enum):
    PASSIVE = 1
    ACTIVE = 2


class SchedulingRule:
    def __init__(self, rule, agent_name, horizon):
        self.rule_id = id(self)

        # Activate this rule
        self.active = True

        # Agent owning this scheduling rule
        self.agent_name = agent_name
        self.horizon = horizon

        # Rule specifications
        self.type = ''
        self.location = ''
        self.property = None
        self.relation = None
        self.goal_state = 0
        self.time_prefix = None
        self.time_start = -1
        self.time_end = -1
        self.predicate = None

        # Initialize the rule
        self.init_rule(rule)

        # Link this rule to the predictive model and activate it
        self.predictive_model = PredictiveModel.predictive_model_map[self.agent_name, (self.location, self.property)]
        self.predictive_model.set_active(True)

    def get_rule_id(self):
        return self.rule_id

    def get_type(self):
        return self.type

    def get_location(self):
        return self.location

    def get_property(self):
        return self.property

    def get_time_start(self):
        return self.time_start

    def get_time_end(self):
        return self.time_end

    def get_goal_state(self):
        return self.goal_state

    def get_relation(self):
        return self.relation

    def get_predicate(self):
        return self.predicate

    def is_active(self):
        return self.active

    def set_active(self, active):
        self.active = active

    def get_predictive_model(self):
        return self.predictive_model

    def init_rule(self, rule):
        """
        Rule is a JSON object like the following:
        {
            'location': 'living_room',
            'state_property': 'cleanliness',
            'relation': 'geq',
            'goal_state': 75,
            'time_predicate': 'before'
            'time': '1800'
            'time_bound': '1900'
        }
        """
        # rule = json.loads(rule_json, encoding='utf-8')
        self.location = rule['location']
        self.property = get_sensor_property(rule['state_property'])
        self.relation = get_relation_from_string(rule['relation'])
        self.goal_state = int(rule['goal_state'])
        if 'time' in rule:
            self.type = RuleType.ACTIVE
            self.add_active_rule(rule)
        else:
            self.type = RuleType.PASSIVE
            self.add_passive_rule(rule)

    def add_active_rule(self, rule):
        self.time_prefix = self.get_time_prefix(rule['time_predicate'])
        if self.time_prefix == RuleTimePrefix.BEFORE:
            self.time_start = 0
            self.time_end = int(rule['time'])
            self.predicate = RuleTimePredicate.DISJUNCTION
        elif self.time_prefix == RuleTimePrefix.AFTER:
            self.time_start = int(rule['time'])
            self.time_end = self.horizon - 1
            self.predicate = RuleTimePredicate.DISJUNCTION
        elif self.time_prefix == RuleTimePrefix.AT:
            self.time_start = int(rule['time'])
            self.time_end = int(rule['time'])
            self.predicate = RuleTimePredicate.CONJUNCTION
        elif self.time_prefix == RuleTimePrefix.WITHIN:
            self.time_start = int(rule['time'])
            self.time_end = int(rule['time_bound'])
            self.predicate = RuleTimePredicate.CONJUNCTION
        else:
            raise Exception('Rule time prefix not found')

    def get_time_prefix(self, time_prefix):
        if time_prefix == 'before':
            return RuleTimePrefix.BEFORE
        elif time_prefix == 'after':
            return RuleTimePrefix.AFTER
        elif time_prefix == 'at':
            return RuleTimePrefix.AT
        else:
            return RuleTimePrefix.WITHIN

    def add_passive_rule(self, rule):
        self.time_start = 0
        self.time_end = self.horizon - 1
        self.predicate = RuleTimePredicate.CONJUNCTION

    def __str__(self):
        rule = 'location: ' + self.location + '\n'
        rule += 'type: ' + str(self.type) + '\n'
        rule += 'property: ' + str(self.property) + '\n'
        rule += 'relation: ' + str(self.relation) + '\n'
        rule += 'goal_state: ' + str(self.goal_state) + '\n'
        rule += 'time_prefix: ' + str(self.time_prefix) + '\n'
        rule += 'time_start: ' + str(self.time_start) + '\n'
        rule += 'time_end: ' + str(self.time_end) + '\n'
        rule += 'predicate: ' + str(self.predicate) + '\n'
        return rule

