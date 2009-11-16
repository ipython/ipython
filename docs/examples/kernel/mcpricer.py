import numpy as np
from math import *


def price_options(S=100.0, K=100.0, sigma=0.25, r=0.05, days=260, paths=10000):
    """
    Price vanilla and asian options using a Monte Carlo method.
    """
    h = 1.0/days
    const1 = exp((r-0.5*sigma**2)*h)
    const2 = sigma*sqrt(h)
    stock_price = S*np.ones(paths, dtype='float64')
    stock_price_sum = np.zeros(paths, dtype='float64')
    for j in range(days):
        growth_factor = const1*np.exp(const2*np.random.standard_normal(paths))
        stock_price = stock_price*growth_factor
        stock_price_sum = stock_price_sum + stock_price
    stock_price_avg = stock_price_sum/days
    zeros = np.zeros(paths, dtype='float64')
    r_factor = exp(-r*h*days)
    vanilla_put = r_factor*np.mean(np.maximum(zeros, K-stock_price))
    asian_put = r_factor*np.mean(np.maximum(zeros, K-stock_price_avg))
    vanilla_call = r_factor*np.mean(np.maximum(zeros, stock_price-K))
    asian_call = r_factor*np.mean(np.maximum(zeros, stock_price_avg-K))
    return (vanilla_call, vanilla_put, asian_call, asian_put)


if __name__ == '__main__':
    (vc, vp, ac, ap) = price_options()
    print "Vanilla Put Price = ", vp
    print "Asian Put Price = ", ap
    print "Vanilla Call Price = ", vc
    print "Asian Call Price = ", ac
