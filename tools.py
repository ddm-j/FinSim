# Business Analysis & Forecasting
# Written by Brandon Johnson aka ddm-j

import mortgage as mtg
from dateutil.rrule import *
import dateutil
from _datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from calendar import monthrange
import uuid

def subclass_check(test,obj):
    return issubclass(test,obj)

class Expense(object):

    def __init__(self, name = None):

        self.Name = name

class Revenue(object):

    def __init__(self, amount, account, mode='simple', distribution='triangular', rule='biweekly', name='None'):

        self.Name = name
        self.Amount = amount
        self.Account = account
        self.Rule = rule
        self.Mode = mode
        self.Distribution = getattr(np.random,distribution)

        # Type Check Argument values
        if self.Mode == 'distribution':
            if not (isinstance(self.Amount,tuple) or isinstance(self.Amount,list)):
                raise ValueError('If using distribution mode, pass distribution arguments in place of amount.')
        elif self.Mode == 'dataframe':
            if not isinstance(self.Amount,pd.DataFrame):
                raise ValueError('If using dataframe mode, pass dataframe of revenues in place of amount.')
        elif self.Mode == 'simple':
            if not (isinstance(self.Amount,float) or isinstance(self.Amount,int)):
                raise ValueError('If using simple mode, amount must be of type int or float.')
        else:
            raise ValueError('{0} is not a supported mode. Please use either simple, distribution, or dataframe.')

    def getAmount(self,date):

        if self.Mode == 'simple':
            return self.Amount
        elif self.Mode == 'distribution':
            return self.Distribution(*self.Amount)
        elif self.Mode == 'dataframe':
            return self.Amount[date]

    def update(self,date):

        date = pd.to_datetime(date)

        if not hasattr(self,'Schedule'):
            if self.Mode == 'dataframe':
                # Generate a custom schedule
                self.Schedule = Schedule(self.Amount,date)
            else:
                self.Schedule = Schedule(self.Rule, date)

        # Make the deposit if on schedule
        if self.Schedule.onSchedule(date):
            self.Account.deposit(date, self.getAmount(date))

class BankAccount(object):

    def __init__(self, balance, rule='yearly', rate=0.06, name='None'):
        self.Name = name
        self.InitialBalance = balance
        self.Rate = rate
        self.Period = rule

    def _year(self,date):
        if [date.month, date.day] == [12, 31]:
            return date.replace(month=1,day=1)
        return False

    def _month(self,date):
        if date == (date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1):
            return date.replace(day=1)
        return False

    def _week(self,date):
        if date.weekday() == 6:
            return date - timedelta(days=6)
        return False

    def _day(self,date):
        return date

    def deposit(self, date, amount):
        self.updateLedger('Deposit',date,amount)

    def initialize(self, date):

        # Create the ledger
        self.Ledger = pd.DataFrame(columns=['date', 'num', 'action',
                                            'amount',
                                            'balance',
                                            'id'])
        self.Ledger.loc[0] = [date, 0, 'Open', 0.00, 0.00, "None"]
        self.Ledger.set_index(['date', 'num'], inplace=True)
        self.updateLedger('Deposit', date, self.InitialBalance)

        # Create the schedule
        self.Schedule = Schedule(self.Period, date)

    def withdraw(self, date, amount):
        if self.Ledger.iloc[-1].balance < amount:
            print('Insufficient funds for withdrawal.')
            return False
        self.updateLedger('Withdraw',date,-amount)
        return True

    def transfer(self, date, amount, name):
        self.updateLedger('Transfer from '+name,date,amount)

    def update(self, date):

        date = pd.to_datetime(date)

        # Check if Ledger Exists. If not, initialize ledger and schedule
        if not hasattr(self, 'Ledger'):
            self.initialize(date)

        # Determine if interest is scheduled for today
        date_range = self.Schedule.onSchedule(date)
        if date_range:
            self.compound(*date_range)

    def compound(self, start, end):
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)

        # Slice the ledger and forward fill balances
        df = self.Ledger.groupby(level=0).tail(1).reset_index(level=1).balance
        ind = pd.DatetimeIndex(pd.date_range(start,end))
        df = df.reindex(ind)
        df.ffill(inplace=True)

        # Get last balance before start date if needed, fill previous balance
        if start < self.Ledger.first_valid_index()[0]:
            last_balance = 0.00
        else:
            diff = pd.Series(self.Ledger.index.get_level_values(level=0)-start)
            if not self.Ledger.index.get_level_values(level=0).is_unique:
                idx = -1
            else:
                idx = (diff[(diff < pd.to_timedelta(0))].idxmax())

            last_balance = self.Ledger.iloc[idx].groupby(level=0).tail(1).balance

        df.fillna(value=last_balance,inplace=True)

        # Calculate Interest
        rate = self.Rate/365
        interest = sum(df*rate)

        # Debit interest to the account
        self.updateLedger('Interest', end, interest)

    def total(self,action):

        total = self.Ledger[self.Ledger['action']==action]['amount'].sum()
        return total

    def updateLedger(self, action, date, amount):

        date = pd.to_datetime(date)

        if date in self.Ledger.index.get_level_values(0):
            num = self.Ledger.xs((date,)).index.max()+1
        else:
            num = 0
        id = uuid.uuid1()
        self.Ledger.loc[(date,num),:] = [action,amount,self.Ledger.iloc[-1].balance+amount,id.int]

    def getHistory(self,column, transaction=None):

        if column not in self.Ledger.columns:
            raise ValueError('{0} is not in Ledger columns: {1}'.format(column,', '.join(self.Ledger.columns)))

        df = getattr(self.Ledger,column).groupby(level=0).tail(1).droplevel(level=1)

        return df

class Asset(BankAccount):

    def __init__(self, principal, equity, rule='monthly', rate=0.06, term=30, name=None,
                 time_value=0.03, distribution='triangular'):

        self.Name = name
        self.Principal = principal
        self.Equity = equity
        self.EquityHistory = pd.DataFrame(columns=['date','market_value','equity'])
        self.EquityHistory.set_index('date', inplace=True)
        self.TimeValue = time_value
        self.Distribution = getattr(np.random,distribution)
        self.Appreciation = self.Distribution(*self.TimeValue) if type(time_value) == tuple else time_value
        self.Own = True

        if principal == equity:
            super().__init__(balance=equity, rule=rule, rate=0, name=name)
        else:
            super().__init__(balance=principal-equity, rule=rule, rate=rate, name=name)

            # Finance the asset
            self.Own = False
            loan = mtg.Loan(principal - equity, rate, term)
            self.MonthlyPayment = float(loan.monthly_payment)
            self.Interest2Principal = float(loan.interest_to_principle)

    def payment(self, date, amount):
        if self.Ledger.iloc[-1].balance < amount:
            print('Loan paid off!')
            self.updateLedger('Payment',date,-self.Ledger.iloc[-1].balance)
            self.Own = True
        else:
            self.updateLedger('Payment',date,-amount)

    def update(self,date):

        date = pd.to_datetime(date)
        super().update(date)

        # Update property value & equity
        if len(self.EquityHistory) == 0:
            self.EquityHistory.loc[self.Ledger.index.get_level_values(0)[0]] = [self.Principal, self.Equity]
        else:
            if self.Schedule.onSchedule(date):
                market_value = self.EquityHistory.iloc[-1].market_value*(1+self.Appreciation/12)
                if date not in self.Ledger.index.get_level_values(level=0):
                    equity = market_value
                else:
                    equity = market_value - self.Ledger.groupby(level=0).tail(1).loc[date].balance.iloc[0]
                self.EquityHistory.loc[date] = [market_value,
                                                equity]

        # Update appreciation rate for the year if today is a new year
        if super()._year(date):
            self.Appreciation = self.Distribution(*self.TimeValue) if type(self.TimeValue) == tuple else self.TimeValue

class Schedule(object):

    """Is used to create schedules for any simulation component. This includes accounts, assets, revenues, expenses,
    and anything that relies on periodic recurrence. Schedule rules are made using dateutil.rrule"""

    def __init__(self, rule, date=None):

        """
        :param rule: A dictionary of arguments corresponding to a dateutil.rrule.rrule schedule.
        """

        # Create the schedule
        if type(rule)==str:
            divs = dict(
                yearly=365,
                monthly=12,
                weekly=52,
                biweekly=26,
                daily=1
            )
            if rule == 'biweekly':
                kwargs = dict(
                    freq=WEEKLY,
                    interval=2,
                    wkst=MO,
                    dtstart=date,
                    count=36500/divs[rule]
                )
            else:
                kwargs = dict(
                    freq=getattr(dateutil.rrule,rule.upper()),
                    dtstart=date,
                    count=36500 / divs[rule]
                )

            self.Schedule = self.rule(kwargs)
        elif isinstance(rule,pd.DataFrame):
            self.Schedule = list(rule.index)
        else:
            self.Schedule = self.rule(rule)

    def format(self, schedule):

        """Takes an rrule schedule and converts it to a list of date objects."""

        return [i.date() for i in list(schedule)]

    def rule(self, kwargs):

        return self.format(rrule(**kwargs))

    def onSchedule(self, date):

        # Check if date is on the schedule
        if date.date() in set(self.Schedule):
            # Send back the range of dates from last scheduled event till date
            ind = self.Schedule.index(date)
            if ind != 0:
                start = self.Schedule[ind-1]+timedelta(days=1)
            else:
                start = self.Schedule[0]
            end = self.Schedule[ind]

            return start, end

        return False

class Transfer(object):

    def __init__(self, from_account, to_account, amount, rule):

        self.FromAccount = from_account
        self.ToAccount = to_account
        self.Amount = amount
        self.Rule = rule

    def update(self, date):

        date = pd.to_datetime(date)

        if not hasattr(self,'Schedule'):
            self.Schedule = Schedule(self.Rule,date)

        if self.Schedule.onSchedule(date):

            # Withdraw from first account
            success = self.FromAccount.withdraw(date, self.Amount)

            # Deposit the transfer into the second account
            self.ToAccount.transfer(date, self.Amount, self.FromAccount.Name) if success else 1

class Payment(object):

    def __init__(self, from_account, to_account, rule, amount=None):

        self.FromAccount = from_account
        self.ToAccount = to_account
        self.Rule = rule

        # Type Checking
        if type(to_account) != Asset:
            raise ValueError('to_account must be of type Asset to make payments!')
        if amount:
            self.Amount = amount
        else:
            self.Amount = self.ToAccount.MonthlyPayment

    def update(self, date):

        date = pd.to_datetime(date)

        if not hasattr(self,'Schedule'):
            self.Schedule = Schedule(self.Rule,date)

        # Do not make payment if we own the asset
        if not self.ToAccount.Own:

            if self.Schedule.onSchedule(date):

                # Check if we are less than a payment away
                if self.Amount > self.ToAccount.Ledger.iloc[-1].balance:
                    amount = self.ToAccount.Ledger.iloc[-1].balance

                    # Withdraw from first account
                    success = self.FromAccount.withdraw(date, amount)

                    # Make the payment to the second account
                    self.ToAccount.payment(date,amount) if success else 1

                else:

                    # Withdraw from first account
                    success = self.FromAccount.withdraw(date, self.Amount)

                    # Make the payment to the second account
                    self.ToAccount.payment(date, self.Amount) if success else 1







