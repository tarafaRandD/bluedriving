#!/usr/bin/env python3
"""Geocoding helper for bluedriving.
Updated for Python 3 and modern requests-based HTTP client.
"""

import argparse
import re
import sys
from urllib.parse import quote_plus

try:
    import requests
except ImportError:
    raise ImportError('requests library is required: pip install requests')


def getCoordinates(address, api_key=None):
    """Resolve an address to coordinates and formatted address."""
    if not isinstance(address, str):
        raise TypeError('address must be a string')

    text = address.strip()
    if not text:
        raise ValueError('address cannot be empty')

    if len(text) > 255:
        raise ValueError('address is too long (max 255 chars)')

    if not re.match(r'^[a-zA-Z0-9, .\-]+$', text):
        raise ValueError('address contains invalid characters')

    encoded = quote_plus(text)
    if api_key:
        url = f'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address={encoded}&key={api_key}'
    else:
        url = f'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address={encoded}'

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get('status') not in ('OK', 'ZERO_RESULTS'):
        raise RuntimeError(f"Geocoding API error: {data.get('status')}")

    results = data.get('results', [])
    if not results:
        return '', ''

    location = results[0]['geometry']['location']
    formatted = results[0].get('formatted_address', '')
    coords = f"{location.get('lat')},{location.get('lng')}"
    return coords, formatted


def main():
    parser = argparse.ArgumentParser(description='Get coordinates from address')
    parser.add_argument('-a', '--address', required=True, help='Address to geocode')
    parser.add_argument('-k', '--key', required=False, help='Optional Google API key')
    args = parser.parse_args()

    coords, formatted = getCoordinates(args.address, api_key=args.key)

    if not coords and not formatted:
        print('No location found')
        sys.exit(1)

    print(f'Address: {formatted}')
    print(f'Coordinates: {coords}')


if __name__ == '__main__':
    main()
