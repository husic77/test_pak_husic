"""
Template Component main class.

"""
import csv
import logging
from datetime import datetime

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException

# configuration variables
# # test

# list of mandatory parameters => if some is missing,
# component will fail with readable message on initialization.
# REQUIRED_PARAMETERS = [KEY_PRINT_HELLO]
# REQUIRED_IMAGE_PARS = []


class Component(ComponentBase):
    """
        Extends base class for general Python components. Initializes the CommonInterface
        and performs configuration validation.

        For easier debugging the data folder is picked up by default from `../data` path,
        relative to working directory.

        If `debug` parameter is present in the `config.json`, the default logger is set to verbose DEBUG mode.
    """

    def __init__(self):
        super().__init__()

    def run(self):
        """
        Main execution code
        """

        import logging, csv, sys, datetime
        from lib import config, fee, payment, rate
        
        # logging setup
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, datefmt='%Y-%m-%d %H:%M:%S%z', format='%(asctime)s | %(module)s | %(levelname)s | %(message)s')
        
        # loading cost fee definitions
        fees = fee.Fees('../data/in/tables/payment_fees.csv').get_fees()

        # loading currency rates
        rates = rate.Rates( '../data/in/tables/gopay_rates.csv', # gopay rates loaded from CNB
                            '../data/in/tables/eur_rates.csv' # EUR from Keboola
                        ).set_rates()

        # config parameters
        cfg = config.Config().set_parameters()
        cfg_date_from = cfg.get_date_from()
        cfg_exceptions = cfg.get_cost_exceptions()

        # in/out file for payment sessions
        with open('../data/in/tables/payments-sessions-stage.csv', mode='r', encoding='utf-8') as ps, \
            open('../data/out/tables/payment_costs.csv' , mode='w', encoding='utf-8') as pc:
            
            payments = csv.DictReader(ps) # reader of payment sessions
            fieldnames = ['payment_session_id', 'amount', 'amount_czk',
                        'amount_refunded', 'amount_refunded_czk','cost_algorithm',
                        'interchange_fee', 'interchange_fee_czk', 'association_fee', 
                        'association_fee_czk', 'provider_transaction_fee', 'provider_transaction_fee_czk',
                        'provider_percent_fee', 'provider_percent_fee_czk','total_fee', 'total_fee_czk']
            writer = csv.DictWriter(pc, fieldnames=fieldnames)
            writer.writeheader()

            # counter
            stats = {'processed': 0, 'ignored': 0}
            
            # loop over payment sessions in in-file
            for ps in payments:

                # ignore ps before a date_performed_from set in config
                try:
                    ps_date_performed = datetime.datetime.strptime(ps['date_performed'][0:10],'%Y-%m-%d').date()
                    if cfg_date_from > ps_date_performed:
                        stats['ignored'] += 1
                        continue

                except Exception as e:
                    logging.error('Cannot parse date_performed for payment: {}' . format(ps))
                    raise e

                # only successful payments
                if ps['session_state'] in ('PAID', 'PARTIALLY_REFUNDED', 'REFUNDED'):

                    # prepare payment details
                    p = payment.Payment(ps, fees, rates, cfg_exceptions).process_payment()

                    # final payment output
                    p_final = {
                        'payment_session_id': p.parsed['payment_session_id'],
                        'amount': p.parsed['amount'],
                        'amount_czk': p.parsed['amount_czk'],
                        'amount_refunded': p.parsed['amount_refunded'],
                        'amount_refunded_czk': p.parsed['amount_refunded_czk'],
                        'cost_algorithm': p.parsed['cost_algorithm'],
                        'interchange_fee': p.parsed['interchange_fee'],
                        'interchange_fee_czk': p.parsed['interchange_fee_czk'],
                        'association_fee': p.parsed['association_fee'], 
                        'association_fee_czk': p.parsed['association_fee_czk'],
                        'provider_transaction_fee': p.parsed['provider_transaction_fee'], 
                        'provider_transaction_fee_czk': p.parsed['provider_transaction_fee_czk'],
                        'provider_percent_fee': p.parsed['provider_percent_fee'], 
                        'provider_percent_fee_czk': p.parsed['provider_percent_fee_czk'],
                        'total_fee': p.parsed['total_fee'], 
                        'total_fee_czk': p.parsed['total_fee_czk']
                    }

                    # writer row to file
                    writer.writerow(p_final)
                    
                    stats['processed'] += 1


        logging.info('Finished! Run stats: {}'. format(str(stats)))



"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = Component()
        # this triggers the run method by default and is controlled by the configuration.action parameter
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
