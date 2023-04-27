# -*- coding: utf-8 -*-

import logging, datetime
from decimal import *

D = Decimal
DECIMAL_PLACES = Decimal(10) ** -5 

class Payment():
    
    def __init__(self, payment, fees, rates, exceptions ):
        self.raw = payment
        self.rates = rates
        self.fees = fees
        self.exceptions  = exceptions 
        
        self.parsed = None
        self.fee = None
    
    def parse_payment(self):
        """
        Parse the payment
        """

        # dict for the result
        parsed_payment = {}

        #iterate over payment columns
        for k,v in self.raw.items():

            # column value
            value = v

            try:  
                # empty strings replacement
                value = None if value == '' else v

                # dates -> date data type
                if k in ('date_created', 'date_performed'):

                    if value is not None:
                        value =  datetime.datetime.strptime(value[0:19], '%Y-%m-%d %H:%M:%S')

                # numbers -> Decimal data type
                if k in ('amount_refunded', 'amount', 'interchange_fee', 'association_fee'):
                    if value is not None:
                        value = value.replace('%', '')
                        value = value.replace(' ', '')
                        value = value.replace(',', '.')
                        value = value.replace('\xa0', '')
                        value = D(value) # Decimal

                # is_business
                if k in ('card_is_business'):
                    if value is not None:
                        value = False if value == 'FALSE' else True
            except:
                raise Exception('Error: parse column: '+ k + ', value: ' + v )

            parsed_payment[k] = value

        self.parsed = parsed_payment
        return self

    
    def get_fee(self):
        """
        find an applied fee
        """   
        
        def find_fee_other():
            """
            get relevant fees - for all payment channels excl. cards
            """ 

            # 1. only fees w/ relevant payment_channel
            possible_fees = [f for f in self.fees if 
                             self.parsed['payment_channel'] == f['payment_channel']]

            # 2. only fees w/ relevant currency
            possible_fees = [f for f in possible_fees if 
                             f['currency'] is None or f['currency'] == self.parsed['currency']]
            
            # 3. only fees w/ relevant dates from/to
            possible_fees = [f for f in possible_fees if 
                             self.parsed['date_performed'].date() >= f['valid_from'] and 
                             (f['valid_to'] is None or self.parsed['date_performed'].date() <= f['valid_to'])]

            # 4. only fees w/ relevant mid
            possible_fees = [f for f in possible_fees if 
                             f['MID'] is None or f['MID'] == self.parsed['mid']]

            
            # 5. only fees w/ relevant MIN amount
            possible_fees = [f for f in possible_fees 
                             if f['MIN_amount'] is None or f['MIN_amount'] <= self.parsed['amount']]
            
            return possible_fees


        def find_fee_card():
            """
            get relevant fees - card methods
            """

            # all in initial_reduction()
            possible_fees = find_fee_other()
            
            # card_type
            possible_fees = [f for f in possible_fees if 
                             self.parsed['card_type'] in [i.strip() for i in f['card_type'].split(',')]]

            # MID is the king if there is a match of MIDs!!! - more important than is_business, card_service_type, aoe
            possible_fees = mid(possible_fees)
            
            # card_is_business - only relevant
            possible_fees = [f for f in possible_fees if 
                             f['card_is_business'] is None 
                             or f['card_is_business'] == self.parsed['card_is_business']]
            
            # card_service_type
            possible_fees = [f for f in possible_fees if 
                             f['card_service_type'] is None or 
                             f['card_service_type'] == self.parsed['card_service_type']]
            
            # area of event
            possible_fees = [f for f in possible_fees if 
                             f['area_of_event'] is None or
                             self.parsed['card_aoe'] in [i.strip() for i in f['area_of_event'].split(',')]]
            
            if len(possible_fees)>1:
                possible_fees = card_is_byz(possible_fees)
                possible_fees = card_service_type(possible_fees)
                possible_fees = aoe(possible_fees)
            
            return possible_fees


        def card_is_byz(possible_fees):
            """
            return only relevant fees - card_is_business
            """
            result = []
            for f in possible_fees:
                if self.parsed['card_is_business'] is True and f['card_is_business'] is True:
                    result.append(f)
            
            if len(result)>0:
                return result
            else:
                return possible_fees
        
        
        def card_service_type(possible_fees):
            """
            return only relevant fees - card_service_type
            """
            result = []
            for f in possible_fees:
                if self.parsed['card_service_type'] is not None and f['card_service_type'] == self.parsed['card_service_type']:
                    result.append(f)
            
            if len(result)>0:
                return result
            else:
                return possible_fees
        
        def aoe(possible_fees):
            """
            return only relevant fees - aoe
            """
            result = []
            for f in possible_fees:
                if self.parsed['card_aoe'] is not None and f['area_of_event'] == self.parsed['card_aoe']:
                    result.append(f)

            if len(result)>0:
                return result
            else:
                return possible_fees
        
        def mid(possible_fees):
            """
            return only relevant fees - mid
            """
            result = []

            for f in possible_fees:
                if self.parsed['mid'] is not None and f['MID'] == self.parsed['mid']:
                    result.append(f)

            if len(result)>0:
                return result
            else:
                return possible_fees


        def min_amount(possible_fees):
            """
            return only relevant fees - min_amount
            """
            amounts = [f['MIN_amount'] for f in possible_fees if  
                       f['MIN_amount'] is not None and f['MIN_amount'] <= self.parsed['amount']]

            if amounts == []:    
                return possible_fees 
            else:
                for f in possible_fees:
                    if f['MIN_amount'] == max(amounts):
                        return [f] 


        def return_final_fee(result_fees):
            """ 
            return the result
            """

            # only 1 fee is applicable -> JUPIIIII
            if len(result_fees) == 1: 
                return result_fees[0]

            # fee needs to be defined
            elif len(result_fees) == 0:
                raise Exception("Error: no fee details specified for payment: \n"+str(self.parsed))

            # more than 1 fee applicable
            else:
                raise Exception("Error: there are "+ str(len(result_fees))+" fees applicable for the payment: \n\n"+str(self.parsed)+"\n\nDostupné fees:\n"+str(result_fees))
        
        # get_fee_detail() flow
        if self.parsed['card_type'] is None:
            f = find_fee_other()
            self.fee = return_final_fee(min_amount(mid(f)))
            return self

        else:
            f = find_fee_card()
            self.fee = return_final_fee(f)
            return self
        
    def get_exception_multiplier(self):

        if self.parsed['partnership_id'] not in self.exceptions:
            return D(1).quantize(DECIMAL_PLACES)
        else:
            date_tested = self.parsed['date_performed'].date()

            for i in self.exceptions[self.parsed['partnership_id']]:
                
                if date_tested >= i['date_from'] and date_tested <= i['date_to']:
                    return D(i['gopay_percent']).quantize(DECIMAL_PLACES)

            # when there is no exception for the payment
            return D(1).quantize(DECIMAL_PLACES)



    def process_payment(self):
        """
        Process payment - calculate the fees
        """

        self.parse_payment() # parse the raw payment data
        self.get_fee() # find the fee scheme
        schema_cost_multiplier = self.get_exception_multiplier() # schema cost multiplier - i.e. scheme costs of skylink payments are being divided between TP and GP

        #rate - payment currency -> CZK
        czk_rate = self.rates.get_rate(self.parsed['currency'], 'CZK', self.parsed['date_performed'].date())
        
        #rate - transaction fee currency  -> CZK
        fee_cur = self.parsed['currency'] if self.fee['transaction_fee_currency'] is None else self.fee['transaction_fee_currency']
        czk_rate_fee = self.rates.get_rate(fee_cur, 'CZK', self.parsed['date_performed'].date())
        
        #rate - transaction fee currency  -> payment currency
        rate_fee = self.rates.get_rate(fee_cur, self.parsed['currency'], self.parsed['date_performed'].date())

        #amounts
        self.parsed['amount'] = D(0).quantize(DECIMAL_PLACES) if self.parsed['amount'] is None else self.parsed['amount'].quantize(DECIMAL_PLACES)
        self.parsed['amount_czk'] = D(0).quantize(DECIMAL_PLACES) if self.parsed['amount'] is None else (self.parsed['amount'] * czk_rate).quantize(DECIMAL_PLACES)
        self.parsed['amount_refunded'] = D(0).quantize(DECIMAL_PLACES) if self.parsed['amount_refunded'] is None else self.parsed['amount_refunded'].quantize(DECIMAL_PLACES)
        self.parsed['amount_refunded_czk'] = D(0).quantize(DECIMAL_PLACES) if self.parsed['amount_refunded'] is None else (self.parsed['amount_refunded'] * czk_rate).quantize(DECIMAL_PLACES)

        # costs
        if self.fee['cost_algorithm'] == 'STD':
            self.parsed['cost_algorithm'] = 'STD'
            self.parsed['provider_transaction_fee'] = D(0).quantize(DECIMAL_PLACES) if self.fee['transaction_fee'] is None else (self.fee['transaction_fee'] * rate_fee).quantize(DECIMAL_PLACES)
            self.parsed['provider_transaction_fee_czk'] = (self.parsed['provider_transaction_fee'] * czk_rate_fee).quantize(DECIMAL_PLACES)
            self.parsed['provider_percent_fee'] = (self.parsed['amount'] * (self.fee['fee'] / 100)).quantize(DECIMAL_PLACES)
            self.parsed['provider_percent_fee_czk'] = (self.parsed['amount_czk'] * (self.fee['fee'] / 100)).quantize(DECIMAL_PLACES)
            self.parsed['interchange_fee_czk'] = D(0).quantize(DECIMAL_PLACES) 
            self.parsed['association_fee_czk'] = D(0).quantize(DECIMAL_PLACES) 
            self.parsed['interchange_fee'] = D(0).quantize(DECIMAL_PLACES)  
            self.parsed['association_fee'] = D(0).quantize(DECIMAL_PLACES) 
            self.parsed['total_fee'] = (self.parsed['provider_transaction_fee'] + self.parsed['provider_percent_fee']).quantize(DECIMAL_PLACES) 
            self.parsed['total_fee_czk'] = (self.parsed['provider_transaction_fee_czk'] + self.parsed['provider_percent_fee_czk']).quantize(DECIMAL_PLACES) 
            
            return self
        
        elif self.fee['cost_algorithm'] == 'STD-MAX':
            self.parsed['cost_algorithm'] = 'STD-MAX'
            transaction_fee = D(0).quantize(DECIMAL_PLACES) if self.fee['transaction_fee'] is None else (self.fee['transaction_fee'] * rate_fee).quantize(DECIMAL_PLACES)
            volume_fee = (self.parsed['amount'] * (self.fee['fee'] / 100)).quantize(DECIMAL_PLACES)
            max_fee = max([transaction_fee, volume_fee])
            self.parsed['provider_transaction_fee'] = D(0).quantize(DECIMAL_PLACES) 
            self.parsed['provider_transaction_fee_czk'] = D(0).quantize(DECIMAL_PLACES)
            self.parsed['provider_percent_fee'] = max_fee
            self.parsed['provider_percent_fee_czk'] = (max_fee * czk_rate).quantize(DECIMAL_PLACES)
            self.parsed['interchange_fee_czk'] = D(0).quantize(DECIMAL_PLACES) 
            self.parsed['association_fee_czk'] = D(0).quantize(DECIMAL_PLACES)
            self.parsed['interchange_fee'] = D(0).quantize(DECIMAL_PLACES) 
            self.parsed['association_fee'] = D(0).quantize(DECIMAL_PLACES)
            self.parsed['total_fee'] = self.parsed['provider_percent_fee']
            self.parsed['total_fee_czk'] = self.parsed['provider_percent_fee_czk']
            
            return self

        elif self.fee['cost_algorithm'] == 'IFPP':
            self.parsed['cost_algorithm'] = 'IFPP'
            # provider fees
            self.parsed['provider_transaction_fee'] = D(0).quantize(DECIMAL_PLACES) if self.fee['transaction_fee'] is None else (self.fee['transaction_fee'] * rate_fee).quantize(DECIMAL_PLACES)
            self.parsed['provider_transaction_fee_czk'] = D(0).quantize(DECIMAL_PLACES) if self.fee['transaction_fee'] is None else (self.fee['transaction_fee'] * czk_rate_fee).quantize(DECIMAL_PLACES)
            self.parsed['provider_percent_fee'] = (self.parsed['amount'] * (self.fee['fee'] / 100)).quantize(DECIMAL_PLACES)
            self.parsed['provider_percent_fee_czk'] = (self.parsed['provider_percent_fee'] * czk_rate).quantize(DECIMAL_PLACES)
            self.parsed['interchange_fee'] = self.parsed['interchange_fee'].quantize(DECIMAL_PLACES) * schema_cost_multiplier if self.parsed['interchange_fee'] is not None else D(0).quantize(DECIMAL_PLACES) 
            self.parsed['association_fee'] = self.parsed['association_fee'].quantize(DECIMAL_PLACES) * schema_cost_multiplier if self.parsed['association_fee'] is not None else D(0).quantize(DECIMAL_PLACES)
            self.parsed['interchange_fee_czk'] = (self.parsed['interchange_fee'] * czk_rate).quantize(DECIMAL_PLACES) 
            self.parsed['association_fee_czk'] = (self.parsed['association_fee'] * czk_rate).quantize(DECIMAL_PLACES) 
            self.parsed['total_fee'] = (self.parsed['provider_transaction_fee'] + self.parsed['provider_percent_fee'] + self.parsed['interchange_fee'] + self.parsed['association_fee']).quantize(DECIMAL_PLACES)
            self.parsed['total_fee_czk'] = (self.parsed['provider_transaction_fee_czk'] + self.parsed['provider_percent_fee_czk'] + self.parsed['interchange_fee_czk'] + self.parsed['association_fee_czk']).quantize(DECIMAL_PLACES)
            
            return self
        
        elif self.fee['cost_algorithm'] == 'IFPP_FIX_CP':
            self.parsed['cost_algorithm'] = 'IFPP_FIX_CP'
            self.parsed['interchange_fee'] = self.parsed['interchange_fee'].quantize(DECIMAL_PLACES) * schema_cost_multiplier if self.parsed['interchange_fee'] is not None else D(0).quantize(DECIMAL_PLACES) 
            self.parsed['association_fee'] = self.parsed['association_fee'].quantize(DECIMAL_PLACES) * schema_cost_multiplier if self.parsed['association_fee'] is not None else D(0).quantize(DECIMAL_PLACES)
            self.parsed['interchange_fee_czk'] = (self.parsed['interchange_fee'] * czk_rate).quantize(DECIMAL_PLACES)
            self.parsed['association_fee_czk'] = (self.parsed['association_fee'] * czk_rate).quantize(DECIMAL_PLACES)
            self.parsed['provider_transaction_fee'] = D(0).quantize(DECIMAL_PLACES) if self.fee['transaction_fee'] is None else (self.fee['transaction_fee'] * rate_fee).quantize(DECIMAL_PLACES)
            self.parsed['provider_transaction_fee_czk'] = D(0).quantize(DECIMAL_PLACES) if self.fee['transaction_fee'] is None else (self.fee['transaction_fee'] * czk_rate_fee).quantize(DECIMAL_PLACES)
            self.parsed['provider_percent_fee'] = ((self.parsed['amount'] * (self.fee['fee'] / 100)) - (self.parsed['interchange_fee'] + self.parsed['association_fee'])).quantize(DECIMAL_PLACES)
            self.parsed['provider_percent_fee_czk'] = ((self.parsed['amount_czk'] * (self.fee['fee'] / 100)) - (self.parsed['interchange_fee_czk'] + self.parsed['association_fee_czk'])).quantize(DECIMAL_PLACES)
            self.parsed['total_fee'] = ((self.parsed['amount'] * (self.fee['fee'] / 100)) + self.parsed['provider_transaction_fee']).quantize(DECIMAL_PLACES)
            self.parsed['total_fee_czk'] = ((self.parsed['amount_czk'] * (self.fee['fee'] / 100)) + self.parsed['provider_transaction_fee_czk']).quantize(DECIMAL_PLACES)
            
            return self
        
        elif self.fee['cost_algorithm'] == 'DEPRECATED':
            raise Exception('Error: Deprecated fee')

        else:
            raise Exception('Error: cost algorithm not recognized')