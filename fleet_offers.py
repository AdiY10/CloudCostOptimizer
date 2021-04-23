import constants
from external_functions import sort_fleet_offers
from fleet_classes import Component, GroupedInstance, GroupedParam, Offer, ComponentOffer
from group_generator import create_groups, partition2

from single_instance_calculator import SingleInstanceCalculator, EbsCalculator

'''
this file handles the logic for fleet offers
'''

class FleetCalculator:
    def __init__(self,ec2_calculator:SingleInstanceCalculator,ebs_calculator: EbsCalculator):
        self.ec2_calculator = ec2_calculator
        self.ebs_calculator = ebs_calculator

    def createComponentOffer(self,component: Component,region):
        ebs = self.ebs_calculator.get_ebs_lowest_price(region,component.storage_type,component.iops, component.throughput)[region]
        if ebs is None:
            return None
        storage_price = component.storage_size*ebs['price']
        return ComponentOffer(component.app_name,component.component_name,storage_price,ebs)

    def match_group(self,grouped_param:GroupedParam,region):
        instances = self.ec2_calculator.get_spot_estimations(grouped_param.total_vcpus, grouped_param.total_memory,
                                                             region, 'all', grouped_param.behavior,
                                                             grouped_param.interruption_frequency, grouped_param.network,grouped_param.burstable)
        components = list(map(lambda g: g.storage_offer, grouped_param.params))
        if len(instances) == 0:
            return None
        return [[GroupedInstance(instances[i],components)] for i in range(min(len(instances),3))]


    def get_offers(self, group: Offer, region):
        instances = []
        for i in group.remaining_partitions:
            instances.append(self.match_group(i,region))
        result = []
        for partition in partition2(list(filter(lambda p: None not in p ,instances))):
            new_group = group.copy_group()
            new_group.total_price = sum(map(lambda i: i.total_price,partition))
            new_group.instance_groups = partition
            new_group.region = region
            result.append(new_group)
        return result

def get_fleet_offers(params:[[Component]],region,os,app_size,ebs, ec2 ):
    res = []
    regions = [region]
    calculator = FleetCalculator(ec2, ebs)
    if region == 'all':
        regions = constants.regions.copy()
    for region in regions:
        updated_params = params.copy()
        for pl in updated_params:
            for p in pl:
                storage_offer = calculator.createComponentOffer(p,region)
                if storage_offer is None:
                    p.iops = 0
                    p.throughput = 0
                    p.storage_type = 'all'
                    storage_offer = calculator.createComponentOffer(p,region)
                p.storage_offer = storage_offer
        groups = create_groups(updated_params, app_size)
        for group in groups:
            res += calculator.get_offers(group,region)
    res = filter(lambda g: g is not None, res)
    return sort_fleet_offers(res)


