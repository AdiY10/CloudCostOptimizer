import re
import pandasql as ps
'''
this file has the SingleInstanceCalculator that matches instances to a single component 
and the EbsCalculator which matchs an ebs volume to the instance
'''

def set_string_filter( type, key):
    if type == 'all':
        return lambda x: True
    else:
        return lambda x: type.lower() == x[key].lower()


class SpotInstanceCalculator:
    def __init__(self,ec2):
        self.ec2 = ec2

    def get_spot_estimations(self, vCPUs, memory, region='all', type='all', behavior='terminate', frequency=4, network=0,burstable = True):
        ec2 = self.get_spot_filter( vCPUs, memory, region, type, behavior, frequency, network, burstable)
        # lst = []
        # for price in ec2:
        #     lst.append(price)
        return sorted(ec2, key= lambda p:p['spot_price'])

    def advancedFilter(self,fi,vCPUs):
        fi = filter(lambda price: float(price['cpu']) <= (2 * vCPUs), fi)
        return fi

    def get_spot_filter(self, vCPUs, memory, region='all', type='all', behavior='terminate', frequency = 4, network = 0,burstable = True):
        ec2_data = self.ec2
        result = []
        if region == 'all':
            for k, v in ec2_data.items():
                result.extend(v)
        else:
            result.extend(ec2_data[region])
        # print(region)
        # print('before filtering',len(result))
        fi = filter(lambda price: float(price['cpu']) >= vCPUs and float(price['memory']) >= memory and price['interruption_frequency_filter'] <= frequency, result)
        fi = filter(self.networkFilter(network,burstable), fi)
        fi = filter(self.interruptionFilter(behavior), fi)
        fi = filter(set_string_filter(type, 'family'), fi)
        fi = self.advancedFilter(fi,vCPUs)
        fi = list(fi)
        # print('after filtering',len(fi))
        return fi

    def networkFilter(self,network,burstable):
        if network == 0:
            return lambda x: True
        if network <= 1:
            return lambda x: True
        if burstable:
            return lambda x: len(re.findall(r'\d+',x['network'].lower())) > 0 and int(re.findall(r'\d+',x['network'].lower())[0]) >= network
        else:
            return lambda x: len(re.findall(r'\d+', x['network'].lower())) > 0 and int(re.findall(r'\d+', x['network'].lower())[0]) >= network and len(re.findall(r'up to',x['network'].lower())) == 0


    def interruptionFilter(self, behavior):
        if behavior == 'terminate':
            return lambda x: True
        if behavior == 'stop':
            return lambda x: True
        if behavior == 'hibernate':
            return lambda x: x['typeMajor'] in ['c3', 'c4', 'c4', 'm4', 'm5', 'r4', 'r4'] and float(x['memory']) <= 100
        return lambda x: False



class EbsCalculator:
    def __init__(self,ebs):
        self.ebs = ebs

    def get_ebs_lowest_price(self, region='all', type='all', iops=250, throughput=250):
        ebs_prices = self.ebs
        filter_function = self.create_filters(type, iops, throughput)
        return {k: self.lowest_ebs(filter(filter_function, v)) for k, v in ebs_prices.items()}

    def create_filters(self, type, iops, throughput):
        return lambda x: set_string_filter(type, 'type')(x) and \
                         self.set_num_filter(iops, 'IOPS')(x) and self.set_num_filter(throughput, 'throughput')

    def set_num_filter(self, num,key):
        return lambda x: num <= float(x[key])

    def lowest_ebs(self, prices):
        list = sorted(prices, key=lambda p: float(p['price']))
        return list[0] if len(list) > 0 else None