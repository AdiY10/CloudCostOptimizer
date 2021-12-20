import constants
from external_functions import sort_fleet_offers
from fleet_classes import Component, GroupedInstance, GroupedParam, Offer, ComponentOffer
from group_generator import create_groups, partition2
from single_instance_calculator import SpotInstanceCalculator, EbsCalculator
from BBAlgorithm import simplestComb, bestCurrentPrice

'''
this file handles the logic for fleet offers
'''

class FleetCalculator:
    def __init__(self,ec2_calculator:SpotInstanceCalculator):
        self.ec2_calculator = ec2_calculator
        self.calculated_combinations = dict()
        self.bestPrice = dict()
        self.rep = 0
        self.count = 0

    def calculate_limits_cpu(self,region):
        maxCPU = max(d['cpu'] for d in self.ec2_calculator.ec2.get(region))
        minCPU = min(d['cpu'] for d in self.ec2_calculator.ec2.get(region))
        return float(maxCPU)

    def calculate_limits_memory(self,region):
        maxMemory = max(d['cpu'] for d in self.ec2_calculator.ec2.get(region))
        minMemory = min(d['cpu'] for d in self.ec2_calculator.ec2.get(region))
        return float(maxMemory)

    def createComponentOffer(self,component: Component,region):
        # ebs = self.ebs_calculator.get_ebs_lowest_price(region,component.storage_type,component.iops, component.throughput)[region]
        # if ebs is None:
        #     return None
        # storage_price = component.storage_size*ebs['price']
        return ComponentOffer(component.app_name,component.component_name)

    def match_group(self,grouped_param:GroupedParam,region): ## finds best configuration for each combination
        sub_combination = []
        for singleComponent in grouped_param.params:
            sub_combination.append(singleComponent.get_component_name())
        sub_combination.append(region)
        sub_combination_str = str(sub_combination)
        if sub_combination_str in self.calculated_combinations:
            instances = self.calculated_combinations[sub_combination_str]
            # self.rep = self.rep + 1 ## check number of repetitive calculation
            # print('repetition: ', self.rep)
            # print(sub_combination_str)
        else:
            limitsCPU = self.calculate_limits_cpu(region)
            limitsMemory = self.calculate_limits_memory(region)
            if(grouped_param.total_vcpus <= limitsCPU and grouped_param.total_memory <= limitsMemory):
                instances = self.ec2_calculator.get_spot_estimations(grouped_param.total_vcpus, grouped_param.total_memory,
                                                                         region, 'all', grouped_param.behavior,
                                                                         grouped_param.interruption_frequency, grouped_param.network,grouped_param.burstable)
                combination = []
                for singleComponent in grouped_param.params:
                    combination.append(singleComponent.get_component_name())
                combination.append(region)
                combination_str = str(combination)
                self.calculated_combinations[combination_str] = instances
                # print(self.calculated_combinations.get(combination_str)[0].get('spot_price'))
                # self.bestPrice[combination_str] = instances
                # self.count = self.count + 1 ##check number of calculations
                # print ('number of first time calculations', self.count)
                # print(combination_str)
            else:
                return None
        components = list(grouped_param.params)
        if len(instances) == 0:
            return None
        return [[GroupedInstance(instances[i],components)] for i in range(min(len(instances),2))]

    ## match_group function of the first version. Should stay, in order to check times improvement
    # def match_group(self,grouped_param:GroupedParam,region):
    #     instances = self.ec2_calculator.get_spot_estimations(grouped_param.total_vcpus, grouped_param.total_memory,
    #                                                          region, 'all', grouped_param.behavior,
    #                                                          grouped_param.interruption_frequency, grouped_param.network,grouped_param.burstable)
    #     components = list(map(lambda g: g.storage_offer, grouped_param.params))
    #     if len(instances) == 0:
    #         return None
    #     return [[GroupedInstance(instances[i],components)] for i in range(min(len(instances),3))]


    def get_offers(self, group: Offer, region):
        instances = []
        for i in group.remaining_partitions:
            instances.append(self.match_group(i,region)) ## finds best configuration for each combination
            # for i in instances:
            #     print('the instance is=========> ',i)
            #     for j in i:
            #         for k in j:
            #             print('i-',i,'j-', j, 'k-', k, 'k info-', k.get_info()[0].get_component_name())
        result = []
        instances = list(filter(None,instances))
        for partition in partition2(instances):
            new_group = group.copy_group()
            new_group.total_price = sum(map(lambda i: i.total_price,partition))
            new_group.instance_groups = partition
            new_group.region = region
            result.append(new_group)
        return result ## result is a list of Offer objects

    def BB(self,group: Offer, region):
        instances = []
        return []


def get_fleet_offers(params,region,os,app_size,ec2):
    print('Finds best configuration')
    res = []
    regions = [region]
    calculator = FleetCalculator(ec2)
    if region == 'all':
        regions = constants.regions.copy()
    for region in regions:
        res_region = []
        # print('region: ', region)
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
        # groups = create_groups(updated_params, app_size) ## creates all the possible combinations
        # print('groups', groups) ## in order to view combinations- remove comments below
        # for i in groups: ##groups are Offer objects
        #     print('groups', i)
        #     for j in (i.get_info()): ## j are GroupedParam object
        #         print('components info: ', j)
        #         for k in (j.get_info()): ## k are Component objects
        #             print('components names: ', k.get_component_name())
        # for group in groups: ## for each combination (group) find N (=3) best offers ##Algorithm for optimal results
        #     res += calculator.get_offers(group,region) ##Algorithm for optimal results
        firstBranch = simplestComb(updated_params, app_size)
        for combination in firstBranch:
            # print(combination)
            res += calculator.get_offers(combination,region)
            # BestPrice = calculator.

        # BestPrice = bestCurrentPrice(res)
        # print(BestPrice)
    # print('number of possible combinations:', len(groups))
    # print('number of saved calculations:', len(groups) - len([*calculator.calculated_combinations]))
    # print('calculated sub combinations (once): ', [*calculator.calculated_combinations])
    res = filter(lambda g: g is not None, res)
    return sort_fleet_offers(res)


