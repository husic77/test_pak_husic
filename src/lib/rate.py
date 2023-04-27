# -*- coding: utf-8 -*-

import csv, datetime, logging
from decimal import *

D = Decimal
DECIMAL_PLACES = Decimal(10) ** -5 


class Rates():
    
    def __init__(self, gopay_rates_path, eur_rates_path):
        self.rates = None
        self.gopay_rates_path = gopay_rates_path
        self.eur_rates_path = eur_rates_path
    
    def set_rates(self):
        """
        Load rates
        """
        rates = {}
        
        # CNB data - gopay data
        with open(self.gopay_rates_path, mode='rt', encoding='utf-8') as czk_data:
            czk_data = csv.DictReader(czk_data)
            
            for d in czk_data:

                date =  datetime.datetime.strptime(d['relevant_date'], '%Y-%m-%d').date()

                # from other currencies to CZK
                if d['target_currency'] in rates:
                    if 'CZK' in rates[d['target_currency']]:
                        rates[d['target_currency']]['CZK'][date] = D(d['price'])/D(d['target_currency_amount'])
                    else:
                        rates[d['target_currency']]['CZK'] = {}
                        rates[d['target_currency']]['CZK'][date] = D(d['price'])/D(d['target_currency_amount'])
                else:
                    rates[d['target_currency']] = {}
                    rates[d['target_currency']]['CZK'] = {}
                    rates[d['target_currency']]['CZK'][date] = D(d['price'])/D(d['target_currency_amount'])

                # from CZK to other currencies
                if 'CZK' in rates:
                    if d['target_currency'] in rates['CZK']:
                        rates['CZK'][d['target_currency']][date] = D(1) / (D(d['price'])/D(d['target_currency_amount']))
                    else:
                        rates['CZK'][d['target_currency']] = {}
                        rates['CZK'][d['target_currency']][date] = D(1) / (D(d['price'])/D(d['target_currency_amount']))          
                else:
                    rates['CZK'] = {}
                    rates['CZK'][d['target_currency']] = {}
                    rates['CZK'][d['target_currency']][date] = D(1) / (D(d['price'])/D(d['target_currency_amount']))

        
        # ECB data - keboola data
        with open(self.eur_rates_path, mode='rt', encoding='utf-8') as eur_data:
            eur_data = csv.DictReader(eur_data)
                            
            for d in eur_data:
                date =  datetime.datetime.strptime(d['date'], '%Y-%m-%d').date()

                # ignore there rows 
                if d['toCurrency'] == 'CZK' or d['rate'] == '':
                    continue

                if 'EUR' in rates:
                    if d['toCurrency'] in rates['EUR']:
                        rates['EUR'][d['toCurrency']][date] = D(d['rate'])
                    else:
                        rates['EUR'][d['toCurrency']] = {}
                        rates['EUR'][d['toCurrency']][date] = D(d['rate'])

                else:
                    rates['EUR'] = {}
                    rates['EUR'][d['toCurrency']] = {}
                    rates['EUR'][d['toCurrency']][date] = D(d['rate'])
        
        self.rates = rates
        return self
    

    def get_rate(self, from_currency, to_currency, date):
        """
        Return currency rate
        """

        # check date
        if not isinstance(date, datetime.date):
            try:
                date =  datetime.datetime.strptime(date, '%Y-%m-%d').date()
            except:
                raise Exception('Error: date in a wrong format ' + date)

        try: 
            # if CZK
            if from_currency == to_currency:
                return D(1)

            # to_currency not in rates
            if from_currency in self.rates:
                
                if to_currency in self.rates[from_currency]:
                    # get closest date for the date 
                    closest_date = max(d for d in self.rates[from_currency][to_currency].keys() if d <= date)
                    return self.rates[from_currency][to_currency][closest_date] 
                
                else:
                    raise Exception('Error: no rates available for to_currency: ' + to_currency)
                    
            else:
                raise Exception('Error: no rates available for from_currency: ' + from_currency)    

        except:
            raise Exception('Error: finding rate from:' + from_currency + ' to: ' + to_currency +  ' for date: ' + str(date))
