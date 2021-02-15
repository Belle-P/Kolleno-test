import sys
import json
from io import StringIO
from decimal import Decimal
from xml.etree import ElementTree
from datetime import date, timedelta
from typing import Dict, Optional

import requests


# BTC exchange rates
BTC_URL = 'https://blockchain.info/ticker'

# Average monthly GBP to EUR exchange rates
ECB_URL = 'https://sdw-wsrest.ecb.europa.eu/service/data/EXR/M.GBP.EUR.SP00.A'


def make_api_request(url: str,
                     params: Dict[str, str] = None) -> requests.Response:
    try:
        response = requests.get(url, params=params)
    except requests.RequestException as error:
        sys.exit(f'Connection error for resource {url}: {error}')

    if response.status_code == 200:
        return response
    else:
        sys.exit(f'Invalid response code for resource {url}')


def get_delayed_btc_price_in_eur() -> Optional[str]:
    response = make_api_request(BTC_URL)

    data = json.loads(response.content)
    price = data.get('EUR', {}).get('15m')

    if isinstance(price, float):
        return str(price)
    else:
        return None


def last_month_date() -> str:
    today = date.today()
    first_day_of_current_month = today.replace(day=1)
    last_month = first_day_of_current_month - timedelta(days=1)
    return last_month.strftime("%Y-%m")


def get_xml_namespaces(xml_string: str) -> Dict[str, str]:
    namespace_events = ElementTree.iterparse(
        StringIO(xml_string),
        events=['start-ns']
    )
    namespaces = dict([node for _, node in namespace_events])
    return namespaces


def get_gbp_to_eur_rate() -> Optional[str]:
    last_month = last_month_date()
    params = {
        'startPeriod': last_month,
        'endPeriod': last_month,
    }
    response = make_api_request(ECB_URL, params=params)

    xml_root = ElementTree.fromstring(response.text)

    # ECB's XML response is namespaced.
    # Fetch all values dynamically in case they are changed in the future.
    namespaces = get_xml_namespaces(response.text)

    namespace_key = 'generic'
    element_name = 'ObsValue'
    xpath = f'.//{namespace_key}:{element_name}[@value]'
    element = xml_root.find(xpath, namespaces=namespaces)
    if element is None:
        return None

    rate = element.get('value')
    return rate


def convert_btc_price(btc_price: str, exchange_rate: str) -> Decimal:
    price = Decimal(btc_price) * Decimal(exchange_rate)
    # Round to two decimal places to match the BTC rate format
    price = price.quantize(Decimal('0.01'))
    return price


def main() -> None:
    btc_price_in_eur = get_delayed_btc_price_in_eur()
    if btc_price_in_eur is None:
        sys.exit('Error: BTC exchange rate format has changed')

    gbp_to_eur_rate = get_gbp_to_eur_rate()
    if gbp_to_eur_rate is None:
        sys.exit('Error: ECB exchange rate format has changed')

    btc_price_in_gbp = convert_btc_price(btc_price_in_eur, gbp_to_eur_rate)

    print(btc_price_in_eur)
    print(gbp_to_eur_rate)
    print(btc_price_in_gbp)


if __name__ == '__main__':
    main()
