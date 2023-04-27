# -*- coding: utf-8 -*-

import logging, csv, datetime
from decimal import *

D = Decimal
DECIMAL_PLACES = Decimal(10) ** -5 


class Fees():
    
    def __init__(self, fee_path):
        self.fee_path = fee_path
    
    
    def load_fees(self):
        """
        Load fees
        """
        try:
            # open file and load rows to list of dics
            with open(self.fee_path, mode='rt', encoding='utf-8') as pf:
                data = list(csv.DictReader(pf))
            return data

        except Exception as e:
            logging.error('Cannot load the fees from the file.')
            raise e

    
    def get_fees(self):
        """
        Parse cost fees. Return data in a proper format.
        """
        raw_fees = self.load_fees()
        
        # result
        data_prepared = []

        #iterate over rows
        for row in raw_fees:

            # iterate over columns and parse the data
            row_prepared = {}
            for k, v in row.items():

                value = v

                # empty strings replacement
                value = None if value == '' else v

                # dates -> date data type
                if k in ('valid_from', 'valid_to'):

                    if value is not None:
                        value =  datetime.datetime.strptime(value, '%Y-%m-%d').date()

                # numbers -> Decimal data type
                if k in ('MIN_amount', 'transaction_fee','fee'):
                    if value is not None:

                        value = value.replace('%', '')
                        value = value.replace(' ', '')
                        value = value.replace(',', '.')
                        value = value.replace('\xa0', '')
                        value = D(value)
                
                # is_business
                if k in ('card_is_business'):
                    if value is not None:
                        value = True if value == 'TRUE' else True

                # add a parsed column       
                row_prepared[k] = value

            # add a parsed row
            data_prepared.append(row_prepared)

        return data_prepared
    