from ebs_prices import get_ebs_for_region, get_ebs
from ec2_prices import Ec2Parser
from fleet_offers import Component, get_fleet_offers
from single_instance_calculator import SpotInstanceCalculator, EbsCalculator
from FindPrice import GetPriceFromAWS
import json


'''
Main calculator class, handles caching and calls to the singleInstanceCalculator and fleetOffers 
'''

class SpotCalculator:

    def __init__(self):
        self.AWSPrice = GetPriceFromAWS()
        self.ec2_cache = {}
        self.ebs_cache = {}
        self.cached_os = {'linux': False, 'windows': False}
        self.all_ebs = False

    ##single instance
    def get_spot_estimations(self, os, vCPUs, memory, storage_size , region='all', type='all', behavior='terminate',
                             storage_type='all', iops=250, throughput=250, frequency=4, network=0, burstable = True):
        # ec2_data = self.get_ec2_from_cache(region, os)
        if os == 'linux':
            file = open('ec2_data_Linux.json')
        else:
            file = open('ec2_data_Windows.json')
        ec2_data = json.load(file)
        ## ec2_data attributes- onDemandPrice, region, cpu, ebsOnly, family, memory, network, os, typeMajor, typeMinor,
        ## storage, typeName, discount, interruption_frequency, interruption_frequency_filter
        # ebs_data = self.get_ebs_from_cache(region)
        ec2 = SpotInstanceCalculator(ec2_data).get_spot_estimations(vCPUs, memory, region, type, behavior,
                                                                      frequency, network,burstable)
        #ebs = EbsCalculator(ebs_data).get_ebs_lowest_price(region, storage_type, iops, throughput)
        lst = []
        for price in ec2:
            ## price attributes- onDemandPrice, region, cpu, ebsOnly, family, memory, network, os, typeMajor, typeMinor,
            ## storage, typeName, discount, interruption_frequency, interruption_frequency_filter
            # if ebs[price['region']] is None:
            #     continue
            # price['volumeType'] = ebs[price['region']]['volumeType']
            # price['storagePrice'] = ebs[price['region']]['price']
            price['total_price'] = price['spot_price']
            price['CPU_Score'] = round(price['Price_per_CPU'],5)
            price['Memory_Score'] = round(price['Price_per_memory'],5)
            lst.append(price)
        lst = sorted(lst, key=lambda p: p['total_price'])
        return lst[0:30]

    ##fleet offers
    def get_fleet_offers(self, os, region, app_size, params): ## params- list of all components
        # ec2_data = self.get_ec2_from_cache(region, os)
        if os == 'linux':
            file = open('ec2_data_Linux.json')
        else:
            file = open('ec2_data_Windows.json')
        ec2_data = json.load(file)
        ec2 = SpotInstanceCalculator(ec2_data)
        # ebs_data = self.get_ebs_from_cache(region) ## get EBS volumes from AWS
        # ebs = EbsCalculator(ebs_data)
        return get_fleet_offers(params,region,os,app_size, ec2)

    def is_cached(self, os, region):
        if self.cached_os[os]:
            return True
        if os not in self.ec2_cache:
            return False
        return region in self.ec2_cache[os]

    # ##Currently not relevant
    # def get_ebs_from_cache(self, region):
    #     if self.all_ebs or region in self.ebs_cache:
    #         return self.ebs_cache
    #     else:
    #         ebs_prices = get_ebs_for_region(region) if region != 'all' else get_ebs()
    #         if region != 'all':
    #             self.ebs_cache[region] = ebs_prices[region]
    #         else:
    #             self.ebs_cache = ebs_prices
    #             self.all_ebs = True
    #         return self.ebs_cache

    def get_ec2_from_cache(self, region, os):
        if self.is_cached(os, region):
            return self.ec2_cache[os]
        else:
            ec2 = Ec2Parser()
            if region != 'all':
                ec2_data = ec2.get_ec2_for_region(os, region)
                ec2_data = self.AWSPrice.calculateSpotPrice(ec2_data)
                # with open('ec2_data.json', 'w', encoding='utf-8') as f:
                #     json.dump(ec2_data, f, ensure_ascii=False, indent=4)
                if os not in self.ec2_cache:
                    self.ec2_cache[os] = {}
                self.ec2_cache[os][region] = ec2_data[region]
                return ec2_data
            else:
                ec2_data = ec2.get_ec2(os)
                ec2_data = self.AWSPrice.calculateSpotPrice(ec2_data)
                # with open('ec2_data.json', 'w', encoding='utf-8') as f:
                #     json.dump(ec2_data, f, ensure_ascii=False, indent=4)
                self.ec2_cache[os] = ec2_data
                self.cached_os[os] = True
                return ec2_data
