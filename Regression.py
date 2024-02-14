import statsmodels.api as sm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.iolib.summary2 import summary_col

df = pd.read_csv("Cleaned_2019_2023_without_delete_small_market.csv")

df["B6AA"] = 1 * df.loc[:, "OpCarrierGroup"].str.contains("B6") * df.loc[:, "OpCarrierGroup"].str.contains("AA")

# df["Missing_Code"] = 1 * df.loc[:, "OpCarrierGroup"].str.contains("--")


df = df.loc[df["Missing_Code"] == 0]
# the city pair where they do codeshare
df['NEA_market'] = 1 * (df.groupby("market")['B6AA'].transform('sum') > 0)
df['NEA_market'] = df['NEA_market'].astype(int)

df['NEA_market_codeshared'] = 1 * (df.groupby(["market", "Year", "Quarter"])['B6AA'].transform('sum') > 0)

output = df.describe()
output.to_csv('output.csv')

#####################################


# start regression

df['total_quantity'] = df.groupby(["market", "Year", "Quarter"])['Passengers'].transform('sum')
df = df[df['total_quantity'] >= 100]

market_counts = df.groupby(['market', 'Year', 'Quarter']).size().reset_index(name='count')

print(market_counts.describe())
# delete the market with less than 100 passengers transported
df["TicketCarrier"] = df.loc[:, "TkCarrierGroup"].apply(lambda x: list(set(x.split(":"))))
df["TicketCarrier"] = df["TicketCarrier"].apply(lambda x: ':'.join(x))

TkGroup_counts = df.groupby(['TicketCarrier'])['Passengers'].sum().reset_index(name='count').sort_values(by='count',
                                                                                                         ascending=False)

TKGroup_Dummy = ["WN", "AA", "DL", "UA", "NK", "AS", "B6", "F9", "G4", "HA", "SY", "XP", "MX", "MM"]
carrier_dummy = pd.get_dummies(df.loc[:, "TicketCarrier"])  # 264 --> 190
carrier_dummy = carrier_dummy[[col for col in carrier_dummy.columns if col in TKGroup_Dummy]]

# market_dummy = pd.get_dummies(df.loc[:, "market"]) the data gets too large
# 11609866 --> 6839666
X = df[["RoundTrip", "OnLine_new", "MktDistance", "Year"]]
X = pd.concat([X, carrier_dummy], axis=1)
y = df["AveFare"]
mod = sm.OLS(y, X).fit()
print(mod.summary())
# regression OLS with ((X'*X)\X')*Y to solve memory issue
# beta_r = np.linalg.inv(X.transpose().dot(X)).dot(X.transpose()).dot(y)

X = df[["RoundTrip", "OnLine_new", "MktDistance", "Year", "B6AA"]]
X = pd.concat([X, carrier_dummy], axis=1)
mod2 = sm.OLS(y, X).fit()
print(mod2.summary())

# with market fixed effects, do it in the TopMarket Analysis

X = df[["RoundTrip", "OnLine_new", "MktDistance", "Year", "B6AA"]]
X = pd.concat([X, carrier_dummy], axis=1)
mod3 = sm.OLS(y, df[["RoundTrip", "OnLine_new", "MktDistance", "Year", "B6AA", "NEA_market"]]).fit()
print(mod3.summary())

# add the interactive term
# NEA market_codeshared will the vairable of interest
X = df[["RoundTrip", "OnLine_new", "MktDistance", "Year", "B6AA", "NEA_market", "NEA_market_codeshared"]]
X = pd.concat([X, carrier_dummy], axis=1)
mod4 = sm.OLS(y, X).fit()
print(mod4.summary())


res = summary_col([mod, mod2, mod3,mod4], regressor_order=mod.params.index.tolist())
res.tables[0].to_csv("output2.csv")
print(mod.summary())