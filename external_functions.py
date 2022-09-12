"""Currently not in use."""

from itertools import groupby


def calculate_group_score(params, app_sizes):
    """Calculate group score function."""
    apps = {
        i: len(list(j))
        for i, j in groupby(
            sorted(params, key=lambda k: k.app_index), key=lambda k: k.app_index
        )
    }
    res = 0
    for k, v in apps.items():
        res += v / (app_sizes[k] * len(apps))
    return res


def calculate_offer_score(groups):
    """Calculate offer score function."""
    return sum(map(lambda g: g.score, groups)) / len(groups)


def sort_fleet_offers(offers):
    """Sort fleet offers function."""
    return sorted(offers, key=lambda g: g.total_price)[:20]
    # return sorted(offers,key=lambda g: g.total_price)[:20] ## not needed in case of one option per region
