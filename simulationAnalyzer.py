import numpy as np
import pandas as pd
from scipy.stats import norm,lognorm,ks_2samp
import matplotlib.pyplot as plt
pd.set_option('display.max_columns', None)


# Load the simulation data
df = pd.read_csv('simulationResults.csv',index_col=0)

print(df)

# Process the simulation data
n = np.unique(np.array([int(c.split('-')[0]) for c in df.columns]))
for c in df.columns:
    if c.split('-')[1] in ["nothing","outright"]:
        continue
    i = c.split('-')[0]
    df[c] = df[c]-df["{0}-outright".format(i)]

print(df)

l = ["-".join(i.split('-')[1:]) for i in df.columns]
un = list(np.unique(np.array(l)))
df.columns = l
d = {i:df[i].values.T.ravel() for i in un}
df = pd.DataFrame(d)


logdf = np.log(df)
logdf.dropna(inplace=True)

for c in logdf.columns:

    data = logdf[c]
    mean,std = norm.fit(data)

    # Generate Gaussian Data
    x = np.linspace(min(data)*0.95,max(data)*1.05,1000)
    y = norm.pdf(x,mean,std)
    x = np.exp(x)

    # Calculate Mode Of Distribution
    mode = x[y.argmax()]

    plt.plot(x, y,label=c+" - ${0}".format(round(mode,2)))



# KS Testing

#nvf = round(100*ks_2samp(logdf['nothing'],logdf['financed']).pvalue,2)
#nvo = round(100*ks_2samp(logdf['nothing'],logdf['outright']).pvalue,2)
#fvo = round(100*ks_2samp(logdf['financed'],logdf['outright']).pvalue,2)
#print('{0}% chance that Nothing & Financed are the same distribution.'.format(nvf))
#print('{0}% chance that Nothing & Outright are the same distribution.'.format(nvo))
#print('{0}% chance that Outright & Financed are the same distribution.'.format(fvo))

plt.legend()
plt.show()


