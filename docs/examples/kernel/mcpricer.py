import numpy as N
from math import *

class MCOptionPricer(object):
    def __init__(self, S=100.0, K=100.0, sigma=0.25, r=0.05, days=260, paths=10000):
        self.S = S
        self.K = K
        self.sigma = sigma
        self.r = r
        self.days = days
        self.paths = paths
        self.h = 1.0/self.days
        self.const1 = exp((self.r-0.5*self.sigma**2)*self.h)
        self.const2 = self.sigma*sqrt(self.h)
        
    def run(self):
        stock_price = self.S*N.ones(self.paths, dtype='float64')
        stock_price_sum = N.zeros(self.paths, dtype='float64')
        for j in range(self.days):
            growth_factor = self.const1*N.exp(self.const2*N.random.standard_normal(self.paths))
            stock_price = stock_price*growth_factor
            stock_price_sum = stock_price_sum + stock_price
        stock_price_avg = stock_price_sum/self.days
        zeros = N.zeros(self.paths, dtype='float64')
        r_factor = exp(-self.r*self.h*self.days)
        self.vanilla_put = r_factor*N.mean(N.maximum(zeros,self.K-stock_price))
        self.asian_put = r_factor*N.mean(N.maximum(zeros,self.K-stock_price_avg))
        self.vanilla_call = r_factor*N.mean(N.maximum(zeros,stock_price-self.K))
        self.asian_call = r_factor*N.mean(N.maximum(zeros,stock_price_avg-self.K))


def main():
    op = MCOptionPricer()
    op.run()
    print "Vanilla Put Price = ", op.vanilla_put
    print "Asian Put Price = ", op.asian_put
    print "Vanilla Call Price = ", op.vanilla_call
    print "Asian Call Price = ", op.asian_call


if __name__ == '__main__':
    main()

