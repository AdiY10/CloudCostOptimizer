import grequests
import requests
import constants

'''
This file handles and parses data from EBS
'''

def get_ebs_region(region):
    url = 'https://calculator.aws/pricing/1.0/ec2/region/' + region + '/ebs/index.json'
    return grequests.get(url)


def get_ebs_for_region(region):
    return {region: parse_ebs_response(requests.get('https://calculator.aws/pricing/1.0/ec2/region/' + region + '/ebs/index.json'))}


def get_ebs():
    regions = constants.regions.copy()
    res = grequests.map(get_ebs_region(region) for region in regions)
    res = list(map(parse_ebs_response, res))
    return {res[i][0]['region']: res[i] for i in range(0, len(res))}


def parse_ebs_response(response):
    return list(map(parse_ebs_object, filter(lambda o: o['attributes']['aws:productFamily'] == 'Storage', response.json()['prices'])))


def parse_ebs_object(object):
    arr = object['attributes']
    usage_type = 'previous generation' if arr['aws:ec2:volumeType'] == 'Magnetic' else arr['aws:ec2:usagetype'].split('.')[1]
    hardware = constants.hardware[usage_type].copy()
    hardware['price'] = round(float(object['price']['USD']) / 760.0,7)
    hardware['region'] = arr['aws:region']
    hardware['usageType'] = usage_type
    hardware['volumeType'] = arr['aws:ec2:volumeType']
    hardware['productFamily'] = arr['aws:productFamily']
    return hardware

