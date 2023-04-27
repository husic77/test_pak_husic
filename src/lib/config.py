import logging, datetime, pytz
# from keboola import docker
from keboola.component import CommonInterface

# init the interface
# A ValueError error is raised if the data folder path does not exist.
# ci = CommonInterface(data_folder_path='../data')


class Config:

    def __init__(self):
        # self.config_path = config_path
        self.ci = CommonInterface(data_folder_path='../data')
        self.params = None

    def set_parameters(self):
        """ Getting config from /data/config.json file
            Returns     dict with config
        """

        parameters = self.ci.configuration.parameters

        configFields = ['date_performed_from', 'partnership_cost_exceptions']
        config = {}

        for field in configFields:

            if field in parameters:
                config[field] = parameters.get(field)
            else:
                logging.error('Missing config paramater: {}' . format(field))
                raise Exception('Missing config paramater: {}' . format(field))
        
        self.params = config
        return self

    def get_date_from(self):
        """ config - recalculate only payments from a particular performed date 
            Returns     date_from 
        """

        try:
            if self.params['date_performed_from'] is None or self.params['date_performed_from'] == '':
                d = '2000-01-01' 
                logging.info('date_performed_from is not set, so we consider all the payments from \'{}\'' . format(d))
            else:
                d = self.params['date_performed_from']
                logging.info('date_performed_from is set. We consider only payments from \'{}\'' . format(d))
            
            d_from = datetime.datetime.strptime(d, '%Y-%m-%d').date()
            return d_from

        except Exception as e:
            logging.error('date_performed_from in config has a wrong format. It has to be \'%Y-%m-%d\' or null !')
            raise e


    def get_cost_exceptions(self):
        """ config - cost exceptions, i.e. skylink scheme costs are divided between GOPAY and TP
            Returns     dict with a cost exceptions
        """
        cost_exceptions = {}

        for k, excs in self.params['partnership_cost_exceptions'].items():

            cost_exceptions[k] = []
            for e in excs:

                try:
                    d_from = datetime.datetime.strptime(e['date_from'],'%Y-%m-%d').date()
                    d_to = datetime.datetime.now(pytz.timezone('Europe/Prague')).date() if e['date_to'] is None or e['date_to'] == '' else datetime.datetime.strptime(e['date_to'],'%Y-%m-%d').date()
                except Exception as e:
                    logging.error('Wrong date values in cost exceptions!')
                    raise e

                if d_from > d_to:
                    logging.error('Date_from is greater then date_to!')
                    raise Exception('Date_from is greater then date_to!')

                try:
                    gp_percent = float(e['gopay_percent'])
                except Exception as e:
                    logging.error('Wrong value in config! Expecting float, but it is probably a string.')
                    raise e

                cost_exceptions[k].append({'date_from': d_from, 'date_to': d_to, 'gopay_percent': gp_percent})

        return cost_exceptions

