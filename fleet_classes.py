import copy
from external_functions import calculate_group_score, calculate_offer_score

'''
This script contains the data classes that are used in the fleet offer search
'''

class Component(object):
    def __init__(self,app_index,app_name,component_specs):
        self.memory = float(component_specs['memory'])
        self.vCPUs = float(component_specs['vCPUs'])
        self.network = float(component_specs['network']) if 'network' in component_specs else 0.0
        self.behavior = component_specs['behavior'] if 'behavior' in component_specs else 'terminate'
        self.interruption_frequency = int(component_specs['frequency']) if 'frequency' in component_specs else 4
        self.storage_size = float(component_specs['size']) if 'size' in component_specs else 0
        self.iops = float(component_specs['iops']) if 'iops' in component_specs and component_specs['iops'] is not None else 0
        self.throughput = float(component_specs['throughput']) if 'throughput' in component_specs and component_specs['throughput'] is not None else 0
        self.storage_type = component_specs['storageType'] if 'storageType' in component_specs and component_specs['storageType'] is not None else 'all'
        self.burstable = True
        if self.network > 0:
            self.burstable = component_specs['burstable'] == True if 'burstable' in component_specs else False
        self.app_index = app_index
        self.app_name = app_name
        self.component_name = component_specs['name']
        self.storage_offer = None

    def get_component_name(self):
        return (self.component_name)

class GroupedParam(object): ## group (sum) all the parameters values together
    def __init__(self, params:[Component],app_sizes):
        self.params = params
        self.total_vcpus = 0
        self.total_memory = 0
        for p in params:
            self.total_vcpus += p.vCPUs
            self.total_memory += p.memory
        self.network = sum(map(lambda p: p.network,params))
        behaviors = map(lambda p: p.behavior,params)
        self.behavior = 'hibernation' if 'hibernation' in behaviors else ('stop' if 'stop' in behaviors else 'terminate')
        self.interruption_frequency = min(map(lambda p: p.interruption_frequency,params))
        # self.score = calculate_group_score(params,app_sizes)
        self.burstable = False if False in map(lambda p:p.burstable,params) else True
        self.storage_price = 0 ## intead of 0 = sum(map(lambda p: p.storage_offer.storage_price,params)) in case EBS should be calculated

    def get_info(self):
        return self.params

class ComponentOffer(object):
    def __init__(self,app_name,component_name):
        self.app_name = app_name
        self.component_name = component_name
        #self.ebs_instance = ebs_instance
        self.storage_price = 0 ## = storage_price # in case EBS should be calculated

    def get_component(self):
        return([self.component_name])


class GroupedInstance(object):
    def __init__(self, instance, components, pricing): ## Offer for each combination
        self.spot_price = round(instance['spot_price'],5)
        self.components = components
        self.instance = instance
        # self.region = instance['region'] ##cross region option
        self.onDemand = round(instance['onDemandPrice'],5)
        if pricing == 'spot':
            self.total_price = self.spot_price  ##+ sum(map(lambda c: c.storage_price,components)) in case EBS should be calculated
        else:
            self.total_price = self.onDemand ##+ sum(map(lambda c: c.storage_price,components)) in case EBS should be calculated

    def get_info(self):
        return(self.components)

class Offer(object):
    def __init__(self,partitions,app_sizes):
       self.remaining_partitions = list(map(lambda p: GroupedParam(p,app_sizes), partitions))
       # self.onDemand = sum(map(lambda p: p.storage_price,self.remaining_partitions))
       # self.total_price = sum(map(lambda p: p.storage_price,self.remaining_partitions))
       self.instance_groups = []
       self.region = ''
       #self.score = calculate_offer_score(self.remaining_partitions) ## currently not relevant

    def get_info(self):
        return self.remaining_partitions

    def copy_group(self):
        return copy.deepcopy(self)

