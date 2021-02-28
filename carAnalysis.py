from tools import *
import matplotlib.pyplot as plt
from tqdm import tqdm
pd.set_option('display.max_columns', None)

outright = []
finance = []
# Case 1: Buy car outright
print('Simulating')
for x in tqdm(range(0,1000)):

    investment1 = Investment(12000,time_value=(-0.03,0.07,0.15))
    car1 = Liability(8000, 8000, rule='monthly', time_value=(-0.13, -0.11, -0.08), name='Car')
    revenue1 = Revenue(1030, investment1, mode='simple', rule='biweekly', name='Roadrunner 3D Income')

    investment2 = Investment(19000,time_value=(-0.03,0.07,0.15))
    car2 = Liability(8000, 1000, rule='monthly', time_value=(-0.15, -0.11, -0.05), rate = 0.06, term=5, name='Car')
    revenue2 = Revenue(1030, investment2, mode='simple', rule='biweekly', name='Roadrunner 3D Income')
    carPayment = Payment(investment2, car2, rule='monthly')

    for _ in pd.date_range("2021-01-01", "2026-01-01"):
        investment1.update(_)
        car1.update(_)
        revenue1.update(_)

        investment2.update(_)
        car2.update(_)
        revenue2.update(_)
        carPayment.update(_)

    networth = investment1.getHistory('balance') + car1.EquityHistory.equity.reindex_like(investment1.getHistory('balance')).fillna(method='ffill')
    outright.append(networth.iloc[-1])

    networth = investment2.getHistory('balance') + car2.EquityHistory.equity.reindex_like(investment2.getHistory('balance')).fillna(method='ffill')
    finance.append(networth.iloc[-1])

    #plt.plot(investment2.getHistory('balance'))
    #plt.plot(car2.EquityHistory.equity)
    #plt.plot(networth)
    #plt.show()

plt.hist(outright, 50, alpha=0.5, label='Outright Purchase')
plt.hist(finance, 50, alpha=0.5, label="Financed")
plt.legend(loc="upper right")
plt.show()