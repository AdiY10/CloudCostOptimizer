import json
from get_spot import SpotCalculator

'''
This script extracts data from AWS 
'''

calc = SpotCalculator()

if __name__ == '__main__':
    print('Extracting Data- Linux')
    AWSData_Linux = calc.get_ec2_from_cache('all' ,'linux')
    print('Extracting Data- Windows')
    AWSData_Windows = calc.get_ec2_from_cache('all', 'windows')
    with open('ec2_data_Linux.json', 'w', encoding='utf-8') as f:
        json.dump(AWSData_Linux, f, ensure_ascii=False, indent=4)
    with open('ec2_data_Windows.json', 'w', encoding='utf-8') as f:
        json.dump(AWSData_Windows, f, ensure_ascii=False, indent=4)