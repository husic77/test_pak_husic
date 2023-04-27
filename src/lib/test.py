import keboola

# from keboola import docker

print(dir(keboola))

import config

cfg = config.Config().set_parameters()
cfg_date_from = cfg.get_date_from()
cfg_exceptions = cfg.get_cost_exceptions()