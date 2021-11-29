from urllib.request import urlopen
import json
import pandas as pd
import datetime

class GetPriceFromAWS:
    def __init__(self):
        self.url = 'http://spot-price.s3.amazonaws.com/spot.js'

    def calculatePrice(self):
        ## extract callback file, and clean it
        fileToRead = urlopen(self.url)
        raw_data = fileToRead.read()
        raw_data = raw_data.lstrip(b'callback(').rstrip(b');')
        ## create json file
        data = json.loads(raw_data)
        ##normalize json into dataframe
        df = pd.json_normalize(data['config']['regions'], record_path=['instanceTypes', 'sizes', 'valueColumns'],
                               meta=['region', ['instanceTypes', 'type'], ['instanceTypes', 'sizes', 'size']])

        df.rename(columns={'name': 'OS',
                           'prices.USD': 'Price',
                           'region': 'Region',
                           'instanceTypes.type': 'Family',
                           'instanceTypes.sizes.size': 'TypeName'
                           }, inplace=True)
        df.loc[(df['OS'] == 'linux'), 'OS'] = 'Linux'
        df.loc[(df['OS'] == 'mswin'), 'OS'] = 'Windows'
        return (df)
