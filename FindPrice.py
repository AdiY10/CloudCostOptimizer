from urllib.request import urlopen
import json
import pandas as pd
import datetime

class GetPriceFromAWS:
    def __init__(self):
        self.url = 'http://spot-price.s3.amazonaws.com/spot.js'
        self.df = pd.DataFrame()

    def calculatePrice(self):
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

        self.df.rename(columns={'name': 'OS',
                           'prices.USD': 'Price',
                           'region': 'Region',
                           'instanceTypes.type': 'Family',
                           'instanceTypes.sizes.size': 'TypeName'
                           }, inplace=True)
        self.df.loc[(self.df['OS'] == 'linux'), 'OS'] = 'Linux'
        self.df.loc[(self.df['OS'] == 'mswin'), 'OS'] = 'Windows'
        self.PricesExtracted = True
        return (self.df)
