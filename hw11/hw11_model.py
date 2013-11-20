# disasters
# DisasterModel.py

"""
A model for coal mining disaster time series with a changepoint

switchpoint: s ~ U(0,111)
early_mean: e ~ Exp(1.)
late_mean: l ~ Exp(1.)
disasters: D[t] ~ Poisson(early if t <= s, l otherwise)
"""

import pymc 
import numpy as np
import pandas as pd


#load in data
D = pd.DataFrame.from_csv('laa_2011_april.txt', sep='	').sort('Player')
X = D['AVG']
num_hits = D['H']
N = D['AB']


mus = dict() #priors
xs = dict() #liklihood


#mus = pymc.Beta('mus', alpha=10, beta = 40)
#xs = pymc.Binomial('xs' , n=N, p=mus, value=num_hits, observed=True) 

for i in np.arange(len(X)):
  # prior on mu_i
  mus['mu'+ str(i)] = pymc.Beta('mu%i' %i, alpha=43.5, beta = 127)

  # likelihood
  xs['x' + str(i)] = pymc.Binomial('x%i' %i , n=N[i], p=mus['mu'+str(i)], value=num_hits[i], observed=True) 





#@pymc.deterministic(plot=False)
#def r(s=s, e=e, l=l):
#    """Concatenate Poisson means"""
#    out = np.empty(len(disasters_array))
#    out[:s] = e
#    out[s:] = l
#    return out


# likelihood
#D = pymc.Poisson('D', mu=r, value=disasters_array, observed=True)
#liklihood
#hood





