"""SingleInstanceCalculator matches instances to a single component And EbsCalculator matches an ebs volume."""

import re

# import boto3


def set_string_filter(type, key):
    """Set_string_filter function."""
    if type == "all":
        return lambda x: True
    else:
        return lambda x: type.lower() == x[key].lower()


class SpotInstanceCalculator:
    """SpotInstanceCalculator class."""

    def __init__(self, ec2):
        """Initialize class."""
        self.ec2 = ec2
        # self.client = boto3.client('ec2')

    def get_spot_estimations(
        self,
        v_cpus,
        memory,
        architecture,
        type_major,
        provider,
        region,
        type,
        behavior="terminate",
        frequency=4,
        network=0,
        burstable=True,
    ):
        """Get_spot_estimations function."""
        ec2 = self.get_spot_filter(
            v_cpus,
            memory,
            architecture,
            type_major,
            provider,
            region,
            type,
            behavior,
            frequency,
            network,
            burstable,
        )
        # lst = []
        # for price in ec2:
        #     lst.append(price)
        return sorted(ec2, key=lambda p: float(p["spot_price"]))

    def advanced_filter(self, fi, v_cpus):
        """Advanced_filter function."""
        fi = filter(lambda price: float(price["cpu"]) <= (2 * v_cpus), fi)
        return fi

    # def botoFilter(self,instance):
    #     filters = [{'Name': 'instance-type', 'Values': instance}]
    #     details = self.client.describe_spot_price_history(Filters=filters)
    #     # details2 = client.describe_spot_price_history(NextToken=details['NextToken'], Filters=filters)
    #     if details['SpotPriceHistory']:
    #         for i in range(len(details['SpotPriceHistory'])):
    #             print(details['SpotPriceHistory'][i])
    #         print('min', (min(details['SpotPriceHistory'], key=lambda x: x['SpotPrice']))['SpotPrice'])

    def get_spot_filter(
        self,
        v_cpus,
        memory,
        architecture,
        type_major,
        aws_provider,
        region="all",
        type="all",
        behavior="terminate",
        frequency=4,
        network=0,
        burstable=True,
    ):
        """Get_spot_filter function."""
        ec2_data = self.ec2
        result = []
        if region == "all":
            for k, v in ec2_data.items():
                result.extend(v)
        else:
            result.extend(ec2_data[region])
        if aws_provider == "AWS":
            fi = filter(
                lambda price: float(price["cpu"]) >= v_cpus
                and float(price["memory"]) >= memory
                and price["interruption_frequency_filter"] <= frequency,
                result,
            )
            if architecture != "all":
                fi = filter(
                    lambda price: price["architecture"] in (architecture), result
                )
            if type_major != "all":
                fi = filter(lambda price: price["typeMajor"] in (type_major), result)
            fi = filter(self.network_filter(network, burstable), fi)
            fi = filter(self.interruption_filter(behavior), fi)
            fi = filter(set_string_filter(type, "family"), fi)
            # self.botoFilter([a_dict['typeName'] for a_dict in list(fi)])
            fi = list(fi)
            # fi = self.advanced_filter(fi,v_cpus)
            # print('after filtering',len(fi))
        else:
            fi = filter(
                lambda price: float(price["cpu"]) >= v_cpus
                and float(price["memory"]) >= memory,
                result,
            )
        return fi

    def network_filter(self, network, burstable):
        """Network_filter function."""
        if network == 0:
            return lambda x: True
        if network <= 1:
            return lambda x: True
        if burstable:
            return (
                lambda x: len(re.findall(r"\d+", x["network"].lower())) > 0
                and int(re.findall(r"\d+", x["network"].lower())[0]) >= network
            )
        else:
            return (
                lambda x: len(re.findall(r"\d+", x["network"].lower())) > 0
                and int(re.findall(r"\d+", x["network"].lower())[0]) >= network
                and len(re.findall(r"up to", x["network"].lower())) == 0
            )

    def interruption_filter(self, behavior):
        """Interruption_filter function."""
        if behavior == "terminate":
            return lambda x: True
        if behavior == "stop":
            return lambda x: True
        if behavior == "hibernate":
            return (
                lambda x: x["typeMajor"] in ["c3", "c4", "c4", "m4", "m5", "r4", "r4"]
                and float(x["memory"]) <= 100
            )
        return lambda x: False


class EbsCalculator:
    """EbsCalculator class."""

    def __init__(self, ebs):
        """Initialize class."""
        self.ebs = ebs

    def get_ebs_lowest_price(self, region="all", type="all", iops=250, throughput=250):
        """Get_ebs_lowest_price function."""
        ebs_prices = self.ebs
        filter_function = self.create_filters(type, iops, throughput)
        return {
            k: self.lowest_ebs(filter(filter_function, v))
            for k, v in ebs_prices.items()
        }

    def create_filters(self, type, iops, throughput):
        """Create_filters function."""
        return (
            lambda x: set_string_filter(type, "type")(x)
            and self.set_num_filter(iops, "IOPS")(x)
            and self.set_num_filter(throughput, "throughput")
        )

    def set_num_filter(self, num, key):
        """Set_num_filter function."""
        return lambda x: num <= float(x[key])

    def lowest_ebs(self, prices):
        """lowest_ebs function."""
        list = sorted(prices, key=lambda p: float(p["price"]))
        return list[0] if len(list) > 0 else None
