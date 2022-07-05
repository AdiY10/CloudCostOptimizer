import numpy as np

class NormDistInt:
    def __init__(self, mean: int, div: int, cutoff_start: int, cutoff_end: int):
        if cutoff_start >= cutoff_end:
            raise Exception("NormDistInt error: cutoff range start should be samller than cutoff range end.")

        self.mean = mean
        self.div = div
        self.cutoff_start = cutoff_start
        self.cutoff_end = cutoff_end
        


    def __call__(self)->int:
        while True:
            res = int(np.random.normal(self.mean, self.div, size=(1,))[0])
            if self.cutoff_start < res and res < self.cutoff_end:
                return res
