from urllib.request import urlopen
import json
import pandas as pd
import datetime

class GetPriceFromAWS:
    def __init__(self):
        self.url = 'http://spot-price.s3.amazonaws.com/spot.js'
        self.df = pd.DataFrame()

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
                i['score_cpu_price'] = (i['score_cpu_price']-minimum_cpu_score)/float(maximum_cpu_score-minimum_cpu_score)
                i['score_memory_price'] = (i['score_memory_price'] - minimum_memory_score) / float(maximum_memory_score - minimum_memory_score)
        return ec2


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
        print('Calculates CPU and Memory normalized Scores')
        ec2 = self.addScores(ec2)
        return ec2