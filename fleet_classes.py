import copy
from external_functions import calculate_group_score, calculate_offer_score

'''
this file contains the data classes that are used in the fleet offer search
'''

class Component(object):
    def __init__(self,app_index,app_name,component_specs):
        self.memory = float(component_specs['memory'])
        self.vCPUs = float(component_specs['vCPUs'])
        self.network = float(component_specs['network']) if 'network' in component_specs else 0.0
        self.behavior = component_specs['behavior'] if 'behavior' in component_specs else 'terminate'
        self.interruption_frequency = int(component_specs['frequency']) if 'frequency' in component_specs else 4
        self.storage_size = float(component_specs['size'])
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

class GroupedParam(object):
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
        self.score = calculate_group_score(params,app_sizes)
        self.burstable = False if False in map(lambda p:p.burstable,params) else True
        self.storage_price = sum(map(lambda p: p.storage_offer.storage_price,params))

class ComponentOffer(object):
    def __init__(self,app_name,component_name,storage_price,ebs_instance):
        self.app_name = app_name
        self.component_name = component_name
        self.ebs_instance = ebs_instance
        self.storage_price = storage_price


class GroupedInstance(object):
    def __init__(self, instance, components):
        self.spot_price = round(instance['spot_price'],4)
        self.components = components
        self.instance = instance
        self.total_price = self.spot_price + sum(map(lambda c: c.storage_price,components))




class Offer(object):
    def __init__(self,partitions,app_sizes):
       self.remaining_partitions = list(map(lambda p: GroupedParam(p,app_sizes), partitions))
       self.total_price = sum(map(lambda p: p.storage_price,self.remaining_partitions))
       self.instance_groups = []
       self.region = ''
       self.score = calculate_offer_score(self.remaining_partitions)

    def copy_group(self):
        return copy.deepcopy(self)

