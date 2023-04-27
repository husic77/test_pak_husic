# app-gopay-payment-cost #

*Aplikace, která přepočítává COSTs pro jednotlivé platby*

## INPUT DATA ##
- payment sessions - `in.c-reporting.payments-sessions-stage`
- definice poplatků pro jednolité typy plateb - `in.c-keboola-ex-google-drive-259059282.payment-methods-cost-fees`
- gopay currency rates - `in.c-gopay-db.currency-rates`
- keboola currency rates (EUR) - `in.c-keboola-ex-currency-335520551.rates`

## OUTPUT data ##
- tabulka s vypočítaným rozpadem poplatků `in.c-gopay-db.payment-cost`

## config.json ##
- *date_performed_from* - `null` a nebo ve formátu `YYYY-MM-DD`. Platby z `in.c-reporting.payments-sessions-stage` před tímto datumem se ignorují 
- *partnership_cost_exceptions* - seznam `partnership_id`ček, kterým se krátí určitým poměrem shema fees
- příklad konfirurace zde: https://bitbucket.org/gopayreporting/app-gopay-payment-cost/src/master/test_data/config.json

ChangeLog
- 2019-10-08 - konfigurovatelnost pomocí `config.json`

