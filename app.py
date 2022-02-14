from flask import Flask, jsonify, request
import json
from flask_cors import CORS, cross_origin
from gevent import monkey

monkey.patch_all() ##internal use- Prevent an Error "greenlet.error: cannot switch to a different thread"

from fleet_classes import Offer, ComponentOffer
from fleet_offers import Component
from get_spot import SpotCalculator

'''
This script is for the web-based optimizer
'''

calc = SpotCalculator()
app = Flask(__name__)
CORS(app)


@app.route('/getAWSData', methods=['POST'])
@cross_origin()
def get_AWS_Data_ToJson():
    print('Extracting Data- Linux')
    AWSData_Linux = calc.get_ec2_from_cache('all','linux')
    print('Extracting Data- Windows')
    AWSData_Windows = calc.get_ec2_from_cache('all', 'windows')
    with open('ec2_data_Linux.json', 'w', encoding='utf-8') as f:
        json.dump(AWSData_Linux, f, ensure_ascii=False, indent=4)
    with open('ec2_data_Windows.json', 'w', encoding='utf-8') as f:
        json.dump(AWSData_Windows, f, ensure_ascii=False, indent=4)
    return jsonify()

## single instance
@app.route('/getPrices', methods=['POST'])
@cross_origin()
def get_spot_prices():
    if(request.method == 'POST'):
        filter = request.get_json() ## In case of using the GUI
        # file = open('input_Single_instance.json') ## In case of using external json file
        # input = json.load(file)
        # os = input['os']
        # vCPUs = input['vCPUs']
        os = filter['selectedOs']
        vCPUs = float(filter['vCPUs'])
        memory = float(filter['memory'])
        storage_size = float(filter['size']) if 'size' in filter else 0
        region = filter['selectedRegion'] if 'selectedRegion' in filter else 'all'
        type = filter['type'] if 'type' in filter else 'all'
        behavior = filter['behavior'] if 'behavior' in filter else 'terminate'
        storage_type = filter['storageType'] if 'storageType' in filter and filter['storageType'] is not None else 'all'
        iops = float(filter['iops']) if 'iops' in filter and filter['iops'] is not None else 0
        throughput = float(filter['throughput']) if 'throughput' in filter and filter['throughput'] is not None else 0
        frequency = float(filter['frequency']) if 'frequency' in filter else 4
        network = float(filter['network']) if 'network' in filter else 0
        burstable  = True
        if network > 0:
            burstable = filter['burstable'] == True if 'burstable' in filter else False
        res = calc.get_spot_estimations(os, vCPUs, memory,storage_size , region, type, behavior, storage_type, iops, throughput, frequency, network,burstable)
        with open('SingleInstanceECresults.json', 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
        return jsonify(res)
    else:
        return jsonify()


## fleet search
@app.route('/getFleet', methods=['POST'])
@cross_origin()
def get_fleet_prices():
    if(request.method == 'POST'):
        filter = request.get_json() ## In case of using the GUI
        # file = open('input_Fleet.json') ## In case of using external json file
        # filter = json.load(file)
        shared_apps = [] # list of components of shared apps
        partitions = [] ## list of ALL components
        app_size = dict() ##size of each app
        for i,a in enumerate(filter['apps']):
            app_size[i]=len(a['components'])
            if 'share' in a and a['share'] == True:
                for c in a['components']:
                    shared_apps.append(Component(i,a['app'],c))
            else:
                app = []
                for c in a['components']:
                    app.append(Component(i,a['app'],c))
                if len(app) > 0:
                    partitions.append(app)
        if len(shared_apps) > 0:
            partitions.append(shared_apps)
        os = filter['selectedOs']
        region = filter['region'] if 'region' in filter else 'all'
        pricing = filter['spot/onDemand'] if 'spot/onDemand' in filter else 'spot'
        listOfOffers = calc.get_fleet_offers(os,region,app_size,partitions, pricing)
        res = list(map(lambda g: serialize_group(g),listOfOffers))
        with open('FleetECresults.json', 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
        return jsonify(res)
    else:
        return jsonify()

def serialize_group(group:Offer):
    res = dict()
    res['price'] = round(group.total_price,5)
    res['instances'] = list(map(lambda i:serializeInstance(i),group.instance_groups))
    res['region'] = group.region
    return res

def serializeInstance(instance):
    result = instance.instance.copy()
    result['spot_price'] = instance.instance['spot_price']
    # result['CPU/Price_Score'] = round(instance.instance['score_cpu_price'],5)
    # result['Memory/Price_Score'] = round(instance.instance['score_memory_price'],5)
    result['components'] = list(map(lambda param: serializeComponent(param),instance.components))
    return result

def serializeComponent(component: ComponentOffer):
    result = dict()
    result['appName'] = component.app_name
    result['componentName'] = component.component_name
    return result



if __name__ == '__main__':
    app.run()



"""
POST endpoint to get spot fleet hourly price estimations
body: configuration for fleet, i.e apps,components and other optional configurations
    dto = {
        selectedOs: <str>               REQUIRED, requested instances os. options: linux,windows
        region: <str>                   OPTIONAL, region for instances. options: us-east-2 etc. (see readme for full options)
        apps: [                         REQUIRED, list of app specifications
            {
            name: <str>                 REQUIRED, name of app
            share: <str>                REQUIRED, set to true if app can share instances with other apps
            components:[                REQUIRED, list of component specifications
                {
                    name: <str>         REQUIRED, name of component
                    cpu: <int>          REQUIRED, required cpu for component
                    memory: <int>       REQUIRED, required memory for component (GB)
                    network: <int>      OPTIONAL, component network consumption (GBs)
                    behavior: <str>     OPTIONAL, component required interruption behavior: options: terminate,stop,hibernation
                    interruptionFrequency: <int>    OPTIONAL, limit interruption frequency of the instances. options: 0-4 (see readme)
                    storageSize: <int>  OPTIONAL, component storage size (GB)
                    IOPS: <int>         OPTIONAL, component required IOPS (MiB I/O)
                    throughput: <int>   OPTIONAL, component required throughput (MB/s)

                }
                ]
            }
        ]


"""