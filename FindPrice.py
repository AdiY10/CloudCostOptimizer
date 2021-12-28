from urllib.request import urlopen
import json
import pandas as pd
import numpy as np
# import boto3
#
#
# def boto3():
#     client = boto3.client('ec2', region_name = 'us-east-1')
#     filters = [{'Name': 'instance-type', 'Values': ['g4ad.2xlarge','m5zn.12xlarge'],'StartTime':}]
#     details = client.describe_spot_price(Filters=filters)
#     details2 = client.describe_spot_price_history(NextToken=details['NextToken'], Filters=filters)


class GetPriceFromAWS:
    def __init__(self):
        self.url = 'http://spot-price.s3.amazonaws.com/spot.js'
        self.df = pd.DataFrame()
        self.cpu = []
        self.cpu_score = []
        self.memory = []
        self.memory_score = []
        self.spotPrice = []


    def calculatePrice(self):
        print("Calculates spot prices")
        if not self.df.empty:
            return self.df
        ## extract callback file, and clean it
        fileToRead = urlopen(self.url)
        raw_data = fileToRead.read()
        raw_data = raw_data.lstrip(b'callback(').rstrip(b');')
        ## create json file
        data = json.loads(raw_data)
        ##normalize json into dataframe
        self.df = pd.json_normalize(data['config']['regions'], record_path=['instanceTypes', 'sizes', 'valueColumns'],
                               meta=['region', ['instanceTypes', 'type'], ['instanceTypes', 'sizes', 'size']])
        ## rename df columns
        self.df.rename(columns={'name': 'OS',
                           'prices.USD': 'Price',
                           'region': 'Region',
                           'instanceTypes.type': 'Family',
                           'instanceTypes.sizes.size': 'TypeName'
                           }, inplace=True)
        self.df.loc[(self.df['OS'] == 'linux'), 'OS'] = 'Linux'
        self.df.loc[(self.df['OS'] == 'mswin'), 'OS'] = 'Windows'
        self.df.loc[(self.df['Region'] == 'us-east'), 'Region'] = 'us-east-1'
        self.df.loc[(self.df['Region'] == 'us-west'), 'Region'] = 'us-west-1'
        self.df.loc[(self.df['Region'] == 'apac-sin'), 'Region'] = 'ap-southeast-1'
        self.df.loc[(self.df['Region'] == 'apac-syd'), 'Region'] = 'ap-southeast-2'
        self.df.loc[(self.df['Region'] == 'apac-tokyo'), 'Region'] = 'ap-northeast-1'
        self.df.loc[(self.df['Region'] == 'eu-ireland'), 'Region'] = 'eu-west-1'
        self.PricesExtracted = True
        return (self.df)

    def addScores(self,ec2):
        for k, v in ec2.items():
            values_cpu = [i['score_cpu_price'] for i in v]
            values_memory = [i['score_memory_price'] for i in v]
            minimum_cpu_score = min(values_cpu)
            maximum_cpu_score= max(values_cpu)
            minimum_memory_score = min(values_memory)
            maximum_memory_score = max(values_memory)
            for i in v:
                i['score_cpu_price'] = round((i['score_cpu_price']-minimum_cpu_score)/float(maximum_cpu_score-minimum_cpu_score),5)
                i['score_memory_price'] = round((i['score_memory_price'] - minimum_memory_score) / float(maximum_memory_score - minimum_memory_score),5)
                self.cpu.append(float(i['cpu']))
                self.memory.append(float(i['memory']))
                self.cpu_score.append(i['score_cpu_price'])
                self.memory_score.append(i['score_memory_price'])
        return ec2

    def calculateCorrelations(self):
        data = [self.spotPrice,self.cpu,self.cpu_score,self.memory,self.memory_score]
        print(np.corrcoef(data))


    def exportArraysToCsv(self):
        pd.DataFrame(self.spotPrice).to_csv("/home/ayehoshu/Calculator Work/spotPrice.csv")
        pd.DataFrame(self.cpu).to_csv("/home/ayehoshu/Calculator Work/cpu.csv")
        pd.DataFrame(self.cpu_score).to_csv("/home/ayehoshu/Calculator Work/cpu_score.csv")
        pd.DataFrame(self.memory).to_csv("/home/ayehoshu/Calculator Work/memory.csv")
        pd.DataFrame(self.memory_score).to_csv("/home/ayehoshu/Calculator Work/memory_score.csv")

    # def analysis(self):
    #     self.calculateCorrelations()
    #     self.exportArraysToCsv()

    def calculateSpotPrice(self,ec2):
        AWSData = self.calculatePrice()
        print('Join spot prices')
        for k, v in ec2.items():
            for price in v:
                spotPrice = AWSData[(AWSData['Region'] == price['region']) & (AWSData['TypeName'] == price['typeName']) & (AWSData['OS'] == price['os'])]
                if not spotPrice.empty:
                    if (spotPrice.iloc[0][1] == 'N/A*'):
                        SpotPriceValue = 100000 ## the instance is not available, therefore- high price
                    else:
                        SpotPriceValue = float(spotPrice.iloc[0][1])
                else:
                    SpotPriceValue = 100000  ## the instance is not available, therefore- high price
                price['spot_price'] = SpotPriceValue
                price['score_cpu_price'] = float(SpotPriceValue / float(price['cpu']))
                price['score_memory_price'] = float(SpotPriceValue / float(price['memory']))
                self.spotPrice.append(SpotPriceValue)
        print('Calculates CPU and Memory normalized Scores')
        ec2 = self.addScores(ec2)
        # self.analysis()
        return ec2