import sys
import pprint
from typing import Tuple, List, Optional

import tldextract
import validators
import requests
from bs4 import BeautifulSoup


def validate_url(url: str) -> None:
    if not validators.url(url, public=True):
        sys.exit('Invalid URL.')


def parse_url(url: str) -> Tuple[str, str]:
    protocol = url.split(':')[0]
    domain_name = tldextract.extract(url).domain
    return protocol, domain_name


def make_request(url: str) -> requests.Response:
    try:
        # Selenium would be a better choice here since it can lazy-load
        # images, but because its installation goes beyond a simple pip
        # install, requests library is used instead (for convenience).
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.InvalidSchema:
        sys.exit('Invalid URL scheme.')
    except requests.RequestException as error:
        sys.exit(f'Connection error: {error}.')

    return response


def validate_response_type(response: requests.Response) -> None:
    content_type = response.headers['Content-Type']
    if 'html' not in content_type:
        sys.exit('Response type error: must be an HTML document.')


def get_image_urls(soup: BeautifulSoup, response_url: str) -> List[str]:
    image_urls = []
    image_tags = soup('img')
    for image in image_tags:
        source = image['src']
        full_url = generate_full_image_url(source, response_url)
        image_urls.append(full_url)

    return image_urls


def generate_full_image_url(source: str, response_url: str) -> str:
    if source.startswith('http') or source.startswith('data:'):
        return source
    else:
        return response_url + source


def get_stylesheet_count(soup: BeautifulSoup) -> int:
    stylesheets = soup('link', rel='stylesheet')
    return len(stylesheets)


def get_page_title(soup: BeautifulSoup) -> Optional[str]:
    if soup.title:
        return soup.title.string
    else:
        return None


def main() -> None:
    url = input('Enter a URL: ')
    validate_url(url)

    response = make_request(url)
    validate_response_type(response)

    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else None
    stylesheet_count = get_stylesheet_count(soup)
    image_urls = get_image_urls(soup, response.url)

    protocol, domain_name = parse_url(url)

    result = {
        'protocol': protocol, 
        'domain_name': domain_name, 
        'title': title,
        'image': image_urls,
        'stylesheets': stylesheet_count
    }
    pprint.pprint(result)


if __name__ == '__main__':
    main()
