"""Main calculator class, handles caching and calls to the singleInstanceCalculator and fleetOffers."""

from ExtractData.ec2_prices import Ec2Parser
from fleet_offers import get_fleet_offers

# from fleet_offers import Component
from single_instance_calculator import SpotInstanceCalculator

# from single_instance_calculator import EbsCalculator
from ExtractData.aws_spot_prices import GetPriceFromAWS

# from ExtractData.ebs_prices import get_ebs_for_region, get_ebs
import json


class SpotCalculator:
    """SpotCalculator class."""

    def __init__(self):
        """Initialize class."""
        self.aws_price = GetPriceFromAWS()
        self.ec2_cache = {}
        self.ebs_cache = {}
        self.cached_os = {"linux": False, "windows": False}
        self.all_ebs = False

    ##single instance
    def get_spot_estimations(
        self,
        payment,
        provider,
        os,
        v_cpus,
        memory,
        storage_size,
        region,
        type,
        behavior="terminate",
        storage_type="all",
        iops=250,
        throughput=250,
        frequency=4,
        network=0,
        burstable=True,
    ):
        """Get_spot_estimations function."""
        if provider == "AWS":
            ec2_data = self.get_ec2_from_cache(region, os)
        elif provider == "Azure":
            file = open("AzureData/Azure_data_v2.json")
            ec2_data = json.load(file)
        elif provider == "Hybrid":
            if os == "linux":
                file_aws = open("AWSData/ec2_data_Linux.json")
            else:
                file_aws = open("AWSData/ec2_data_Windows.json")
            file_azure = open("AzureData/Azure_data_v2.json")
            aws_data = json.load(file_aws)
            azure_data = json.load(file_azure)
            ec2_data = dict()
            ec2_data["hybrid"] = []
            for k, v in aws_data.items():
                for instance in v:
                    if os.lower() in instance["os"].lower():
                        ec2_data["hybrid"].append(instance)
            for k, v in azure_data.items():
                for instance in v:
                    if os.lower() in instance["os"].lower():
                        ec2_data["hybrid"].append(instance)
        else:
            print("Provider error")
        # if provider != "Hybrid":
        #     ec2_data = self.calculate_discount(ec2_data, provider, os)
        # if os == 'linux':
        #     file = open('ec2_data_Linux.json')
        # else:
        #     file = open('ec2_data_Windows.json')
        # ec2_data = json.load(file)
        ## ec2_data attributes- onDemandPrice, region, cpu, ebsOnly, family, memory, network, os,
        ## type_major, typeMinor,storage, typeName, discount, interruption_frequency,
        ## interruption_frequency_filter
        # ebs_data = self.get_ebs_from_cache(region)
        ec2 = SpotInstanceCalculator(ec2_data).get_spot_estimations(
            v_cpus,
            memory,
            "all",
            "all",
            provider,
            region,
            type,
            behavior,
            frequency,
            network,
            burstable,
        )
        # ebs = EbsCalculator(ebs_data).get_ebs_lowest_price(region, storage_type, iops, throughput)
        lst = []
        for price in ec2:
            ## price attributes- onDemandPrice, region, cpu, ebsOnly, family, memory, network, os,
            ## type_major,typeMinor, storage, typeName, discount, interruption_frequency,
            ## interruption_frequency_filter
            # if ebs[price['region']] is None:
            #     continue
            # price['volumeType'] = ebs[price['region']]['volumeType']
            # price['storagePrice'] = ebs[price['region']]['price']
            if isinstance(price["spot_price"], str):
                price["total_price"] = "N/A"
                # price["CPU_Score"] = "N/A"
                # price["Memory_Score"] = "N/A"
            if isinstance(price["onDemandPrice"], str):
                price["total_price"] = "N/A"
                # price["CPU_Score"] = "N/A"
                # price["Memory_Score"] = "N/A"
            else:
                if payment == "spot":
                    price["total_price"] = round(
                        price["spot_price"] * (100 - price["discount"]) / 100, 6
                    )
                    if price["onDemandPrice"] == 1000000:
                        price["onDemandPrice"] = "N/A"
                else:
                    price["total_price"] = round(
                        price["onDemandPrice"] * (100 - price["discount"]) / 100, 6
                    )
                    if price["spot_price"] == 1000000:
                        price["spot_price"] = "N/A"
                # price["CPU_Score"] = round(price["Price_per_CPU"], 5)
                # price["Memory_Score"] = round(price["Price_per_memory"], 5)
                lst.append(price)
        lst = sorted(lst, key=lambda p: p["total_price"])
        return lst[0:30]

    ##fleet offers
    def get_fleet_offers(
        self,
        user_os,
        region,
        app_size,
        params,
        payment,
        architecture,
        type_major,
        filter_instances,
        provider,
        bruteforce,
        **kw
    ):  ## params- list of all components
        """Get_fleet_offers function."""
        import os.path
        import datetime

        file = open("config_file.json")
        config_file = json.load(file)
        if provider == "AWS":
            if config_file["Data Extraction (always / onceAday)"] == "onceAday":
                if user_os == "linux":
                    if (
                        datetime.datetime.now()
                        - datetime.datetime.fromtimestamp(
                            os.path.getmtime("AWSData/ec2_data_Linux.json")
                        )
                    ).days != 0:  ## if the file hasn't modified today
                        ec2_data = self.get_ec2_from_cache(region, user_os)
                    else:
                        file = open("AWSData/ec2_data_Linux.json")
                        ec2_data = json.load(file)
                else:
                    if (
                        datetime.datetime.now()
                        - datetime.datetime.fromtimestamp(
                            os.path.getmtime("AWSData/ec2_data_Windows.json")
                        )
                    ).days != 0:  ## if the file hasn't modified today
                        ec2_data = self.get_ec2_from_cache(region, user_os)
                    else:
                        file = open("AWSData/ec2_data_Windows.json")
                        ec2_data = json.load(file)
            elif config_file["Data Extraction (always / onceAday)"] == "always":
                ec2_data = self.get_ec2_from_cache(region, user_os)
            else:
                print(
                    "Data Extraction parameter in configuration file is not defined well"
                )
            if filter_instances != "NA":
                for k, v in ec2_data.items():
                    list_of_relevant_instances = []
                    for i in v:
                        if (
                            i["typeMajor"] not in filter_instances
                            and i["typeMinor"] not in filter_instances
                            and i["typeName"] not in filter_instances
                        ):
                            list_of_relevant_instances.append(i)
                    ec2_data[k] = list_of_relevant_instances
        elif provider == "Azure":
            file = open("AzureData/Azure_data_v2.json")
            all_vms = json.load(file)
            ec2_data = dict()
            for k, v in all_vms.items():
                ec2_data[k] = []
                for instance in v:
                    if user_os.lower() in instance["os"].lower():
                        ec2_data[k].append(instance)
        else:
            if user_os == "linux":
                file_aws = open("AWSData/ec2_data_Linux.json")
            else:
                file_aws = open("AWSData/ec2_data_Windows.json")
            file_azure = open("AzureData/Azure_data_v2.json")
            aws_data = json.load(file_aws)
            azure_data = json.load(file_azure)
            ec2_data = dict()
            ec2_data["hybrid"] = []
            for k, v in aws_data.items():
                for instance in v:
                    if user_os.lower() in instance["os"].lower():
                        ec2_data["hybrid"].append(instance)
            for k, v in azure_data.items():
                for instance in v:
                    if user_os.lower() in instance["os"].lower():
                        ec2_data["hybrid"].append(instance)
        # if provider != "Hybrid":
        #     ec2_data = self.calculate_discount(ec2_data, provider, user_os)
        print("calculating best configuration")
        ec2 = SpotInstanceCalculator(ec2_data)
        # ebs_data = self.get_ebs_from_cache(region) ## get EBS volumes from AWS
        # ebs = EbsCalculator(ebs_data)
        return get_fleet_offers(
            params,
            region,
            user_os,
            app_size,
            ec2,
            payment,
            architecture,
            type_major,
            config_file,
            provider,
            bruteforce,
            **kw
        )

    def calculate_discount(self, ec2_data, provider, user_os):
        """Calculate discount per user."""
        if provider == "AWS":
            if user_os == "linux":
                file = open("AWSData/ec2_discount_Linux.json")
            else:
                file = open("AWSData/ec2_discount_Windows.json")
            discount = json.load(file)
        elif provider == "Azure":
            file = open("AzureData/vm_discount.json")
            discount = json.load(file)
        else:  ##Hybrid
            if user_os == "linux":
                file_aws = open("AWSData/ec2_data_Linux.json")
            else:
                file_aws = open("AWSData/ec2_data_Windows.json")
            file_azure = open("AzureData/Azure_data_v2.json")
            aws_data = json.load(file_aws)
            azure_data = json.load(file_azure)
            discount = dict()
            discount["hybrid"] = []
            for k, v in aws_data.items():
                for instance in v:
                    if user_os.lower() in instance["os"].lower():
                        discount["hybrid"].append(instance)
            for k, v in azure_data.items():
                for instance in v:
                    if user_os.lower() in instance["os"].lower():
                        discount["hybrid"].append(instance)
        if provider != "Hybrid":
            for k, v in discount.items():
                for single_discount in v:
                    d = next(
                        item
                        for item in ec2_data[k]
                        if item["typeName"] == single_discount["typeName"]
                    )
                    d["discount"] = single_discount["discount"]
        else:
            for k, v in discount.items():
                for single_discount in v:
                    d = next(
                        item
                        for item in ec2_data["hybrid"]
                        if item["typeName"] == single_discount["typeName"]
                        and item["region"] == single_discount["region"]
                    )
                    d["discount"] = single_discount["discount"]
        return ec2_data

    def is_cached(self, os, region):
        """Check if cached function."""
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
        """Get_ec2_from_cache function."""
        if self.is_cached(os, region):
            return self.ec2_cache[os]
        else:
            ec2 = Ec2Parser()
            if region != "all" and not isinstance(region, list):
                ec2_data = ec2.get_ec2_for_region(os, region)
                ec2_data = self.aws_price.calculate_spot_price(ec2_data, region)
                if os == "linux":
                    with open(
                        "AWSData/ec2_data_Linux.json", "w", encoding="utf-8"
                    ) as f:
                        json.dump(ec2_data, f, ensure_ascii=False, indent=4)
                else:
                    with open(
                        "AWSData/ec2_data_Windows.json", "w", encoding="utf-8"
                    ) as f:
                        json.dump(ec2_data, f, ensure_ascii=False, indent=4)
                if os not in self.ec2_cache:
                    self.ec2_cache[os] = {}
                self.ec2_cache[os][region] = ec2_data[region]
                return ec2_data
            else:
                ec2_data = ec2.get_ec2(os, region)
                ec2_data = self.aws_price.calculate_spot_price(ec2_data, region)
                if os == "linux":
                    with open(
                        "AWSData/ec2_data_Linux.json", "w", encoding="utf-8"
                    ) as f:
                        json.dump(ec2_data, f, ensure_ascii=False, indent=4)
                else:
                    with open(
                        "AWSData/ec2_data_Windows.json", "w", encoding="utf-8"
                    ) as f:
                        json.dump(ec2_data, f, ensure_ascii=False, indent=4)
                self.ec2_cache[os] = ec2_data
                self.cached_os[os] = True
                return ec2_data
