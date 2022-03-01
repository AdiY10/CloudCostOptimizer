import grequests
import requests
import constants

'''
This class handles calls and parses data from EC2 and the SpotAdvisor
'''

class Ec2Parser:
    def __init__(self):
        self.spot_data = self.get_spot_data()

    def get_spot_data(self):
        url = 'https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json'
        return requests.get(url).json()['spot_advisor']

    def get_ec2_region(self, region, os):
        url = 'https://calculator.aws/pricing/1.0/ec2/region/' + region + '/ondemand/' + os + '/index.json'
        return grequests.get(url)

    def get_ec2_for_region(self, os, region):
        return {region: list(self.parse_ec2_response(requests.get('https://calculator.aws/pricing/1.0/ec2/region/' + region + '/ondemand/' + os + '/index.json')))}

    def get_ec2(self, os, region):
        if isinstance(region, list):
            regions = region
        else:
            regions = constants.regions.copy()
        res = grequests.map(self.get_ec2_region(region, os) for region in regions)
        # res = [i for i in res if i]
        res = list(map(self.parse_ec2_response, res))
        return {res[i][0]['region']: res[i] for i in range(0, len(res))}


    def parse_ec2_response(self, response):
        res = list(filter(lambda p: p is not None, map(self.parse_ec2_object, response.json()['prices'])))
        return res

    def parse_ec2_object(self, object):
        arr = object['attributes']
        if arr['aws:ec2:instanceType'] not in self.spot_data[arr['aws:region']][arr['aws:ec2:operatingSystem']]:
            return
        current_spot = self.spot_data[arr['aws:region']][arr['aws:ec2:operatingSystem']][arr['aws:ec2:instanceType']]
        type_major = arr['aws:ec2:instanceType'].split('.')[0]
        if type_major in ['t2','t3','c4','c5','c5a','c5ad','c5d','c5n','c6i','d2','d3','g3','g3s','g4ad','g4dn','h1'
                          ,'hpc6a','i2','i3','i3en','inf1','m4','m5','m5a','m5ad','m5d','m5dn','m5n','m5zn','m6i'
                          ,'p2','p3','p4d','r3','r4','r5','r5a','r5ad','r5b','r5d','r5dn','r5n','r6i','t3a','x1'
                          ,'x1e','z1d']:
            Architecute = 'x86_64'
        elif type_major in ['a1','c6g','c6gd','im4gn','is4gen','m6g','m6gd','r6g','r6gd','t4g','x2gd']:
            Architecute = 'arm64'
        elif type_major in ['mac1']:
            Architecute = 'x86_64_mac'
        else:
            Architecute = 'x86_64'
        return {
            'onDemandPrice': round(float(object['price']['USD']),4),
            'region': arr['aws:region'],
            'cpu': arr['aws:ec2:vcpu'],
            'ebsOnly': arr['aws:ec2:storage'] == 'EBS only',
            'family': arr['aws:ec2:instanceFamily'],
            'memory': arr['aws:ec2:memory'].split(' ')[0],
            'network': arr['aws:ec2:networkPerformance'],
            'os': arr['aws:ec2:operatingSystem'],
            'typeMajor': arr['aws:ec2:instanceType'].split('.')[0],
            'typeMinor': arr['aws:ec2:instanceType'].split('.')[1],
            'storage': arr['aws:ec2:storage'],
            'typeName': arr['aws:ec2:instanceType'],
            'physicalProcessor': arr['aws:ec2:physicalProcessor'],
            'processorArchitecture': arr['aws:ec2:processorArchitecture'],
            'Architecture': Architecute,
            'discount': current_spot['s'],
            'interruption_frequency': self.interruption_frequency(current_spot['r']),
            'interruption_frequency_filter': float(current_spot['r']),
        }

    def interruption_frequency(self,index):
        return {
            0: '<5%',
            1: '5%-10%',
            2: '10%-15%',
            3: '15%-20%',
            4: '<20%'
        }[index]

