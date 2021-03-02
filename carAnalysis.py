from tools import *
import matplotlib.pyplot as plt
from tqdm import tqdm
pd.set_option('display.max_columns', None)

outright = []
finance = []
# Case 1: Buy car outright
print('Simulating')
for x in tqdm(range(0,1000)):

    # Account to simulate gas expenses
    gas = BankAccount(0,rate=0)

    investment1 = Investment(15000,time_value=0.07)
    car1 = Liability(8000, 8000, rule='monthly', time_value=-0.11, name='Car')
    revenue1 = Revenue(1030, investment1, mode='simple', rule='biweekly', name='Roadrunner 3D Income')
    gas1 = Transfer(investment1,gas,1055/12,rule='monthly')

    investment2 = Investment(20000,time_value=0.07)
    car2 = Liability(15000, 3000, rule='monthly', time_value=-0.11, rate=0.06, term=3, name='Car')
    revenue2 = Revenue(1030, investment2, mode='simple', rule='biweekly', name='Roadrunner 3D Income')
    carPayment = Payment(investment2, car2, rule='monthly')
    gas2 = Transfer(investment2,gas,726/12,rule='monthly')

    for _ in pd.date_range("2021-01-01", "2026-01-01"):
        investment1.update(_)
        car1.update(_)
        revenue1.update(_)

        investment2.update(_)
        car2.update(_)
        revenue2.update(_)
        carPayment.update(_)

    networth = investment1.currentBalance() + car1.EquityHistory.iloc[-1].equity
    outright.append(networth)

    networth = investment2.currentBalance() + car2.EquityHistory.iloc[-1].equity
    finance.append(networth)

    #plt.plot(investment2.getHistory('balance'))
    #plt.plot(car2.EquityHistory.equity)
    #plt.plot(networth)
    #plt.show()

npur, binpur, _ = plt.hist(outright, 35, alpha=0.5, label='Outright Purchase')
nfin, binfin, _ = plt.hist(finance, 35, alpha=0.5, label="Financed")
plt.legend(loc="upper right")

idxp = npur.argmax()
idxf = nfin.argmax()

modep = (binpur[idxp] + binpur[idxp+1])/2
modef = (binfin[idxf] + binfin[idxf+1])/2

print('Mode for outright purchase: ${0}'.format(round(modep,2)))
print('Mode for financed purchase: ${0}'.format(round(modef,2)))

plt.show()