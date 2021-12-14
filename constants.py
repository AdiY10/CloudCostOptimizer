regions = ['us-east-2', 'us-east-1', 'us-west-1', 'us-west-2', 'af-south-1',
                   'ap-east-1', 'ap-south-1', 'ap-northeast-3', 'ap-northeast-2',
                   'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ca-central-1',
                   'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-south-1',
                   'eu-west-3', 'eu-north-1', 'me-south-1', 'sa-east-1'] ##currently there are issues with stockholm eu-north-1 and milan eu-south-1, and bahrian me-south-1 (fleet)

regionsSpotPrices = ['us-east-2', 'us-east', 'us-west', 'us-west-2', 'af-south-1','us-west-2-lax-1a',
                   'ap-east-1', 'ap-south-1', 'ap-northeast-3', 'ap-northeast-2',
                   'apac-sin', 'apac-syd', 'apac-tokyo', 'ca-central-1',
                   'eu-central-1', 'eu-ireland', 'eu-west-2', 'eu-south-1',
                   'eu-west-3', 'eu-north-1', 'me-south-1', 'sa-east-1']


hardware = {
        'gp2': {
            'IOPS': 250,
            'throughput': 250,
            'type': 'gp2'
        },
        'gp3': {
            'IOPS': 250,
            'throughput': 1000,
            'type': 'gp3'
        },
        'piops': {
            'IOPS': 1000,
            'throughput': 1000,
            'type': 'piops'
        },
        'io2': {
            'IOPS': 1000,
            'throughput': 1000,
            'type': 'io2'
        },
        'st1': {
            'IOPS': 500,
            'throughput': 500,
            'type': 'st1'
        },
        'sc1': {
            'IOPS': 250,
            'throughput': 250,
            'type': 'sc1'
        },
        'previous generation': {
            'IOPS': 200,
            'throughput': 90,
            'type': 'magnetic'
        }
    }