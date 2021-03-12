from tools import *
import matplotlib.pyplot as plt
from tqdm import tqdm
pd.set_option('display.max_columns', None)
from itertools import product
import sys
import multiprocessing as mp
import time

def main(n,simpleIn,simpleOut,financeParams,financeIn,financeOut):
    ## Simulation Inputs
    # Finance Settings
    finPrice = 15000
    finGas = 726 / 12

    # Outright Settings
    outPrice = 8000
    outGas = 1055 / 12

    # Nothing Settings
    jeepValue = 4000
    jeepGas = 2288 / 12
    jeepDep = -0.05

    # General Settings
    acnBalance = 22000
    marketRet = 0.2
    dep = -0.11
    income = 1030

    # Start and stop points
    start = "2021-01-01"
    end = "2031-01-01"
    n_loops = 200

    with tqdm(total=n_loops) as progress_bar:
        for x in tqdm(range(0,n_loops),desc='#{0}'.format(n),position=n,leave=True):

            investment1 = Investment(acnBalance-outPrice,time_value=marketRet,name="Invest1")
            car1 = Liability(outPrice, outPrice, rule='monthly', time_value=dep, name='Car')
            revenue1 = Cashflow(income, investment1, mode='simple', rule='biweekly', name='Roadrunner 3D Income')
            gas1 = Cashflow(-outGas,investment1,rule='monthly')

            investment2 = Investment(acnBalance,time_value=marketRet,name="Invest2",following=investment1)
            car2 = Liability(jeepValue, jeepValue, rule='monthly', time_value=jeepDep, name='Jeep')
            revenue2 = Cashflow(income, investment2, mode='simple', rule='biweekly', name='Roadrunner 3D Income')
            gas2 = Cashflow(-finGas,investment2,rule='monthly')

            simpleIn['outright'] = [investment1,car1,revenue1,gas1]
            simpleIn['nothing'] = [investment2,car2,revenue2,gas2]

            # Generate Finance Input
            for d in financeParams:
                if int(d.split('-')[0]) != n:
                    continue
                p = financeParams[d]

                acc = acnBalance-finPrice*p[0]

                inv = Investment(acc,time_value=marketRet,name="Invest.{0}".format(d),following=investment1)
                car = Liability(finPrice,finPrice*p[0], rule='monthly', term=p[2], rate=p[1], time_value=dep, name='Car.{0}'.format(d))
                rev = Cashflow(income, inv, mode='simple', rule='biweekly', name='Roadrunner.{0}'.format(d))
                carPay = Payment(inv,car,rule='monthly')
                gasf = Cashflow(-finGas,inv,rule='monthly')

                financeIn.update({d:[inv,car,rev,carPay,gasf]})


            for _ in pd.date_range(start, end):

                # Calculate Simple Outcomes
                for d in simpleIn:
                    for i in simpleIn[d]:
                        i.update(_)

                # Calculate Financed Outcomes
                for d in financeIn:
                    for i in financeIn[d]:
                        i.update(_)

            progress_bar.update(1)

            # Collate Simple Results

            networth1 = investment1.currentBalance() + car1.EquityHistory.iloc[-1].equity
            simpleOut['{0}-outright'.format(n)].append(networth1)

            networth2 = investment2.currentBalance() + car2.EquityHistory.iloc[-1].equity
            simpleOut['{0}-nothing'.format(n)].append(networth2)

            for d in financeIn:
                net = financeIn[d][0].currentBalance() + financeIn[d][1].EquityHistory.iloc[-1].equity
                financeOut[d].append(net)

        progress_bar.close()

if __name__ == "__main__":
    #mp.freeze_support()
    with mp.Manager() as manager:

        # Generate Finance inputs
        down = [0.1, 0.15, 0.20]
        interest = [0.04]
        term = [2, 4, 6]
        combs = list(product(down, interest, term))

        # Storage of Results
        n_cores = 5

        financeParams = {}
        financeIn = {}
        financeOut = manager.dict()
        simpleOut = manager.dict()
        for n in range(0,n_cores):
            simpleOut['{0}-nothing'.format(n)] = manager.list()
            simpleOut['{0}-outright'.format(n)] = manager.list()
            for comb in combs:
                label = "{0}-{1}-{2}-{3}".format(n,str(comb[0]), str(round(comb[1], 4)), str(comb[2]))

                financeParams.update({label: [comb[0], round(comb[1], 4), comb[2]]})
                financeOut.update({label: manager.list()})

        print(dict(financeOut))
        simpleIn = {
            'outright': [],
            'nothing': []
        }



        # Multiprocess
        jobs = []
        for i in range(0,n_cores):
            p = mp.Process(target=main,args=(i,simpleIn,simpleOut,financeParams,financeIn,financeOut))
            jobs.append(p)
            p.start()
            time.sleep(0.5)

        for j in jobs:
            j.join()


        # Results

        simpleOut.update(financeOut)

        #Convert
        output = {}
        for d in simpleOut:
            output.update({d:list(simpleOut[d])})

        df = pd.DataFrame.from_dict(output)
        df.to_csv('simulationResults.csv')