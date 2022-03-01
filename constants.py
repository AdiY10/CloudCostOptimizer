regions = ['us-east-2', 'us-east-1', 'us-west-1', 'us-west-2', 'af-south-1',
                   'ap-east-1', 'ap-south-1', 'ap-northeast-3', 'ap-northeast-2',
                   'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ca-central-1',
                   'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-south-1',
                   'eu-west-3', 'eu-north-1', 'me-south-1', 'sa-east-1']

'''
regionsSpotPrices = ['us-east-2', 'us-east', 'us-west', 'us-west-2', 'af-south-1','us-west-2-lax-1a',
                   'ap-east-1', 'ap-south-1', 'ap-northeast-3', 'ap-northeast-2',
                   'apac-sin', 'apac-syd', 'apac-tokyo', 'ca-central-1',
                   'eu-central-1', 'eu-ireland', 'eu-west-2', 'eu-south-1',
                   'eu-west-3', 'eu-north-1', 'me-south-1', 'sa-east-1']

'''
architecture = ['arm64','i386','x86_64','x86_64_mac'] ##All possible Architectures

physicalProcessor = ['AMD EPYC 7571', 'Intel Xeon Platinum 8151', 'Intel Xeon Platinum 8252',
                         'AMD EPYC 7R13 Processor', 'Intel Xeon Family', 'Intel Xeon E5-2676 v3 (Haswell)',
                         'Intel Xeon E5-2686 v4 (Broadwell)', 'Intel Skylake E5 2686 v5',
                         'Intel Xeon Scalable (Skylake)', 'High Frequency Intel Xeon E7-8880 v3 (Haswell)',
                         'Intel Xeon Platinum 8175 (Skylake)', 'AMD EPYC 7R32', 'Intel Xeon Platinum 8259CL',
                         'Intel Xeon Platinum 8259 (Cascade Lake)', 'Intel Xeon E5-2666 v3 (Haswell)',
                         'Intel Xeon Platinum 8124M', 'Intel Xeon Platinum 8275L', 'AWS Graviton Processor',
                         'Intel Xeon 8375C (Ice Lake)', 'Intel Xeon Platinum 8275CL (Cascade Lake)',
                         'AWS Graviton2 Processor'] ##All possible physicalProcessor

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