"""This script extracts AWS Spot prices."""

from urllib.request import urlopen
import json

# import pandas as pd
import constants

# import numpy as np
# import boto3


class GetPriceFromAWS:
    """GetPriceFromAWS class."""

    def __init__(self):
        """Initialize class."""
        self.url = "http://spot-price.s3.amazonaws.com/spot.js"
        # self.df = pd.DataFrame()
        self.cpu = []
        self.cpu_score = []
        self.memory = []
        self.memory_score = []
        self.spot_price = []

    # def boto3(self, region, instance,os):
    #     # print(region, instance)
    #     client = boto3.client('ec2', region_name=region)
    #     filters = [{'Name': 'instance-type', 'Values': [instance]}]
    #     details = client.describe_spot_price_history(Filters=filters)
    #     if (details['SpotPriceHistory']):
    #         return(float((min(details['SpotPriceHistory'], key=lambda x:x['spot_price']))['spot_price']))
    #     return None

    ## latest version of data extraction
    # def calculate_price(self):
    #     """Calculate price function."""
    #     print("Extracting Data from AWS")
    #     if not self.df.empty:
    #         return self.df
    #     ## extract callback file, and clean it
    #     file_to_read = urlopen(self.url)
    #     raw_data = file_to_read.read()
    #     raw_data = raw_data.lstrip(b"callback(").rstrip(b");")
    #     ## create json file
    #     data = json.loads(raw_data)
    #     ##normalize json into dataframe
    #     self.df = pd.json_normalize(
    #         data["config"]["regions"],
    #         record_path=["instanceTypes", "sizes", "valueColumns"],
    #         meta=[
    #             "region",
    #             ["instanceTypes", "type"],
    #             ["instanceTypes", "sizes", "size"],
    #         ],
    #     )
    #     ## rename df columns
    #     self.df.rename(
    #         columns={
    #             "name": "OS",
    #             "prices.USD": "Price",
    #             "region": "Region",
    #             "instanceTypes.type": "Family",
    #             "instanceTypes.sizes.size": "TypeName",
    #         },
    #         inplace=True,
    #     )
    #     self.df.loc[(self.df["OS"] == "linux"), "OS"] = "Linux"
    #     self.df.loc[(self.df["OS"] == "mswin"), "OS"] = "Windows"
    #     self.df.loc[(self.df["Region"] == "us-east"), "Region"] = "us-east-1"
    #     self.df.loc[(self.df["Region"] == "us-west"), "Region"] = "us-west-1"
    #     self.df.loc[(self.df["Region"] == "apac-sin"), "Region"] = "ap-southeast-1"
    #     self.df.loc[(self.df["Region"] == "apac-syd"), "Region"] = "ap-southeast-2"
    #     self.df.loc[(self.df["Region"] == "apac-tokyo"), "Region"] = "ap-northeast-1"
    #     self.df.loc[(self.df["Region"] == "eu-ireland"), "Region"] = "eu-west-1"
    #     self.PricesExtracted = True
    #     return self.df

    def add_scores(self, ec2):
        """Add scores function."""
        for k, v in ec2.items():
            values_cpu = [i["Price_per_CPU"] for i in v]
            values_memory = [i["Price_per_memory"] for i in v]
            minimum_cpu_score = min(values_cpu)
            maximum_cpu_score = max(values_cpu)
            minimum_memory_score = min(values_memory)
            maximum_memory_score = max(values_memory)
            for i in v:
                i["Price_per_CPU"] = round(
                    (i["Price_per_CPU"] - minimum_cpu_score)
                    / float(maximum_cpu_score - minimum_cpu_score),
                    5,
                )
                i["Price_per_memory"] = round(
                    (i["Price_per_memory"] - minimum_memory_score)
                    / float(maximum_memory_score - minimum_memory_score),
                    5,
                )
                self.cpu.append(float(i["cpu"]))
                self.memory.append(float(i["memory"]))
                self.cpu_score.append(i["Price_per_CPU"])
                self.memory_score.append(i["Price_per_memory"])
        return ec2

    # def calculateCorrelations(self):
    #     data = [self.spot_price,self.cpu,self.cpu_score,self.memory,self.memory_score]
    #     print(np.corrcoef(data))

    # def exportArraysToCsv(self):
    #     pd.DataFrame(self.spot_price).to_csv("/home/ayehoshu/Calculator Work/spotPrice.csv")
    #     pd.DataFrame(self.cpu).to_csv("/home/ayehoshu/Calculator Work/cpu.csv")
    #     pd.DataFrame(self.cpu_score).to_csv("/home/ayehoshu/Calculator Work/cpu_score.csv")
    #     pd.DataFrame(self.memory).to_csv("/home/ayehoshu/Calculator Work/memory.csv")
    #     pd.DataFrame(self.memory_score).to_csv("/home/ayehoshu/Calculator Work/memory_score.csv")

    # def analysis(self):
    #     self.calculateCorrelations()
    #     self.exportArraysToCsv()

    def join_spot_prices(self, ec2, aws_data):
        """Join spot prices function."""
        for k, v in ec2.items():
            for price in v:
                # ##boto3
                # spot_price_value = self.boto3(price['region'],price['typeName'],price['os'])
                # if not spot_price_value:
                #     spot_price_value = 100000
                ## web
                spot_price = aws_data[
                    (aws_data["Region"] == price["region"])
                    & (aws_data["TypeName"] == price["typeName"])
                    & (aws_data["OS"] == price["os"])
                ]
                if not spot_price.empty:
                    if spot_price.iloc[0][1] == "N/A*" or None:
                        spot_price_value = 100000  ## the instance is not available, therefore- high price
                    else:
                        spot_price_value = float(spot_price.iloc[0][1])
                else:
                    spot_price_value = (
                        100000  ## the instance is not available, therefore- high price
                    )
                price["spot_price"] = spot_price_value
                # print('spot_price',spot_price_value)
                price["Price_per_CPU"] = round(
                    float(spot_price_value / float(price["cpu"])), 4
                )
                price["Price_per_memory"] = round(
                    float(spot_price_value / float(price["memory"])), 4
                )
                self.spot_price.append(spot_price_value)
        return ec2

    def correct_region(self, region):
        """Correct region function."""
        if region == "us-east":
            region = "us-east-1"
        elif region == "us-west":
            region = "us-west-1"
        elif region == "apac-sin":
            region = "ap-southeast-1"
        elif region == "apac-syd":
            region = "ap-southeast-2"
        elif region == "apac-tokyo":
            region = "ap-northeast-1"
        elif region == "eu-ireland":
            region = "eu-west-1"
        return region

    def correct_os(self, os):
        """Correct os function."""
        if os == "linux":
            os = "Linux"
        elif os == "mswin":
            os = "Windows"
        else:
            print("the os is wrong")
        return os

    def aws_data_extraction(self, ec2, region):
        """Aws_data_extraction function."""
        file_to_read = urlopen(self.url)
        raw_data = file_to_read.read()
        raw_data = raw_data.lstrip(b"callback(").rstrip(b");")
        prices = json.loads(raw_data)
        if region != "all" and not isinstance(region, list):  ##case of one region
            data_region = ec2[region]
            for item in data_region:
                # selecting searching criteria form ec2 file
                os_type = item["os"]
                type_name = item["typeName"]
                # looping through the Prices JSON to find a match
                for ec2_region in prices["config"]["regions"]:
                    # check if the region is matching
                    prices_region = self.correct_region(ec2_region["region"])
                    if prices_region == region:
                        for instance_type in ec2_region["instanceTypes"]:
                            for size in instance_type["sizes"]:
                                # check if the instance type is matching
                                if size["size"].lower() == type_name.lower():
                                    for value in size["valueColumns"]:
                                        # check if the os is matching
                                        os_name = self.correct_os(value["name"])
                                        if os_name == os_type:
                                            index = data_region.index(item)
                                            # updating the item details with spot prices
                                            if isinstance(
                                                value["prices"]["USD"], str
                                            ):  ## check if string
                                                item["spot_price"] = "N/A"
                                                item["Price_per_CPU"] = "N/A"
                                                item["Price_per_memory"] = "N/A"
                                            else:
                                                item["spot_price"] = float(
                                                    value["prices"]["USD"]
                                                )
                                                item["Price_per_CPU"] = float(
                                                    item["spot_price"]
                                                    / float(item["cpu"])
                                                )
                                                item["Price_per_memory"] = float(
                                                    item["spot_price"]
                                                    / float(item["memory"])
                                                )
                                            ec2[region][index] = item
        else:  ##case of multiple regions
            if isinstance(region, list):
                regions = region
            else:
                regions = constants.AWS_REGIONS.copy()
            for region in regions:
                region = self.correct_region(region)
                data_region = ec2[region]
                for item in data_region:
                    # selecting searching criteria form ec2 file
                    os_type = item["os"]
                    type_name = item["typeName"]
                    # looping through the Prices JSON to find a match
                    for ec2_region in prices["config"]["regions"]:
                        # check if the region is matching
                        prices_region = self.correct_region(ec2_region["region"])
                        if prices_region == region:
                            for instance_type in ec2_region["instanceTypes"]:
                                for size in instance_type["sizes"]:
                                    # check if the instance type is matching
                                    if size["size"].lower() == type_name.lower():
                                        for value in size["valueColumns"]:
                                            # check if the os is matching
                                            os_name = self.correct_os(value["name"])
                                            if os_name == os_type:
                                                index = data_region.index(item)
                                                # updating the item details with spot prices
                                                try:
                                                    item["spot_price"] = float(
                                                        value["prices"]["USD"]
                                                    )
                                                    item["Price_per_CPU"] = float(
                                                        item["spot_price"]
                                                        / float(item["cpu"])
                                                    )
                                                    item["Price_per_memory"] = float(
                                                        item["spot_price"]
                                                        / float(item["memory"])
                                                    )
                                                except Exception as e:
                                                    print(e)
                                                    item["spot_price"] = "N/A"
                                                    item["Price_per_CPU"] = "N/A"
                                                    item["Price_per_memory"] = "N/A"
                                                ec2[region][index] = item
        return ec2

    def calculate_spot_price(self, ec2, region):
        """Calculate spot price function."""
        print("Extracting Data from AWS")
        ec2 = self.aws_data_extraction(ec2, region)
        return ec2
