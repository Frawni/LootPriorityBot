"""
Code was copied from https://github.com/mikeStr8s/ClassicBot but modifications were required since
    wowhead's search api was changed.
"""

import logging
import json
import re

import requests
from bs4 import BeautifulSoup, NavigableString

from open_search.constants import SEARCH_OBJECT_TYPE, OPEN_SEARCH, TOOLTIP, Q_COLORS, TOOLTIP_ARGS
from open_search.tooltip import build_tooltip

logger = logging.getLogger(__name__)


class OpenSearchError(Exception):
    pass


class SearchObjectError(Exception):
    pass


class OpenSearch:
    def __init__(self, command, search_query):
        if not isinstance(command, str):
            raise OpenSearchError('The command: {} is not a string.'.format(command))
        if not isinstance(search_query, str):
            raise OpenSearchError('The query: {} is not a string.'.format(search_query))

        self.search_query = search_query
        self.command = command
        self.results = []
        self.search(SEARCH_OBJECT_TYPE[command])

    def search(self, type_id):
        """
        Search for an object that complies with the correct command type and search query.

        If the search finds an exact match, it returns early because you always want the most
        accurate result.

        If the search does not find and exact match, then it will return the first result from
        the open search.

        Args:
            type_id (int): Integer representation of the object type WoWhead uses in their databases

        Returns:
            SearchObject: The resulting search object being either the exact match or first response
        """
        resp = requests.get(OPEN_SEARCH.format(self.search_query))
        # Why the heck this is needed I dont know, atleast wowhead returns what can be considered 99% json,
        content = resp.content.decode().replace("items:", '"items":')
        try:
            resp_results = json.loads(content)
        except json.JSONDecodeError:
            logger.exception(f"Failed to decode wowhead json. Wowhead response was: |{resp.content}| with status code: {resp.status_code}")
            raise

        try:
            for result in resp_results[1]["items"]:
                result_name = result["name"].lstrip("1234567890")
                self.results.append(self.build_search_object(result_name, self.command, result))
        except KeyError:
            print("KeyError:", resp_results)
            raise OpenSearchError(
                '{}, the {} you searched for returned no results.'.format(self.search_query, self.command))

    @staticmethod
    def build_search_object(name, command, result):
        """
        Attempts to build a search object with as much information as it can from the resulting search.

        Args:
            name (str): The name of the object
            command (str): The command used to search for the object
            result (list): The attribute container that is returned by the search

        Returns:
            SearchObject: The search object that is populated with the resulting attributes

        result = {"classs": 2, "displayid": 29698, "dps": 80.41, "flags2": 8192, "id": 17182,
            "level": 80, "name": "3Sulfuras, Hand of Ragnaros", "reqlevel": 60, "slot": 17,
            "slotbak": 17, "speed": 3.7, "subclass": 5, "dmgmax1": 372, "dmgmin1": 223,
            "dmgrange": 1.0, "dmgtype1": 0, "dura": 145, "firres": 30, "maxcount": 1,
            "mledmgmax": 372, "mledmgmin": 223, "mledps": 80.41, "mlespeed": 3.7,
            "sellprice": 332623, "sheathtype": 1, "sta": 12, "str": 12,
            "icon": "inv_hammer_unique_sulfuras", "attainable": 0,
            "statsInfo": {
                "4": {"qty": 12, "alloc": 0, "socketMult": 0},
                "7": {"qty": 12, "alloc": 0, "socketMult": 0}
            },
            "chanceBonuses": []}

        """
        return SearchObject(name=name, obj_type=command, obj_id=result["id"], icon_name=result["icon"])


class SearchObject:
    def __init__(self, name, obj_type, obj_id, icon_name=None, quality=None):
        if not isinstance(name, str):
            raise SearchObjectError('The object name type {}, not str as expected'.format(type(name)))
        if not isinstance(obj_type, str):
            raise SearchObjectError('The object type {}, not str as expected'.format(type(name)))
        if not isinstance(obj_id, int):
            raise SearchObjectError('The object object id was type {}, not int as expected'.format(type(obj_id)))

        if icon_name is not None:
            if not isinstance(icon_name, str):
                raise SearchObjectError('The icon name was type {}, not a str as expected'.format(type(icon_name)))
        if quality is not None:
            if not isinstance(quality, (str, int)):
                raise SearchObjectError('The argument provided was not of type str or int: {}'.format(type(quality)))

        self.name = name
        self.object_type = obj_type
        self.id = obj_id
        self.icon_name = icon_name
        self.quality = quality
        self.tooltip = None
        self.image = None

    def get_tooltip_data(self):
        response = json.loads(requests.get(TOOLTIP.format(self.object_type, self.id)).content)
        try:
            raw_tooltip = self.clean_tooltip_data(response['tooltip'])
        except AttributeError:
            raise SearchObjectError(
                '{0} {1} does not comply with parser structure. Please refine search if this was not the {1} that was intended.\n'
                'If you believe this to be an error, please submit an issue here: https://github.com/mikeStr8s/ClassicBot/issues'.format(
                    self.object_type, self.name))
        self.tooltip = self.parse_tooltip(raw_tooltip)
        self.build_image()

    def build_image(self):
        self.image = build_tooltip(self.tooltip, self.icon_name)

    @staticmethod
    def clean_tooltip_data(tooltip):
        cleaned = tooltip.replace('\n', '')
        cleaned = cleaned.replace('    ', '')
        cleaned = re.sub('((<!--)([a-z0-9:]+)(-->))|(<a ([a-z0-9\/=\-\" \.])+>)|(<\/a>)', '', cleaned)

        rebuild = ''
        pattern = re.compile('<br(\s\/)*>')
        idx = 0
        for match in pattern.finditer(cleaned):
            indices = match.span()
            start = indices[0]
            stop = indices[1]
            if cleaned[stop:stop + 1] == '<':
                rebuild = rebuild + cleaned[idx:start]
                idx = stop
            else:
                rebuild = rebuild + cleaned[idx:start]
                idx = cleaned.find('<', stop)
                if idx == -1:
                    idx = len(cleaned)
                text = cleaned[stop:idx]
                rebuild = rebuild + '<span>' + text + '</span>'
        cleaned = rebuild + cleaned[idx:]

        if 'table' in cleaned[:6]:
            body = ''
            soup = BeautifulSoup(cleaned, 'html.parser')
            for content in soup.children:
                body += str(content.next.next)[4:-5]
            cleaned = body

        soup = BeautifulSoup(cleaned, 'html.parser')
        for table in soup.find_all('table'):
            table.unwrap()

        for tr in soup.find_all('tr'):
            split_div = soup.new_tag('div')
            split_div.attrs['class'] = ['split']
            split_div.contents = tr.contents
            tr.replace_with(split_div)
        return soup.contents

    def parse_tooltip(self, raw_tooltip):
        tooltip = []
        for line_item in raw_tooltip:
            if isinstance(line_item, NavigableString):
                tooltip.append(self.parse_nav_string(line_item))
            else:
                if self.no_nav_strings(line_item.contents):
                    if line_item.name == 'div' or line_item.name == 'span':
                        tooltip.extend(self.parse_elements(line_item))
                else:
                    tooltip.extend(self.parse_elements(line_item))
        return tooltip

    def parse_nav_string(self, element):
        return self.build_tooltip_line_item(Q_COLORS[2], element)

    def parse_elements(self, element):
        try:
            color = self.intersection(element.attrs['class'], Q_COLORS)[0]
        except (KeyError, IndexError):
            color = Q_COLORS[2]
        try:
            args = self.determine_style(self.intersection(element.attrs['class'], TOOLTIP_ARGS)[0], element)
        except (KeyError, IndexError):
            args = None

        if args is not None:
            if args['style'] == 'indent':
                pieces = []
                for elem in element.contents:
                    if isinstance(elem, NavigableString):
                        pieces.append(self.build_tooltip_line_item(color, str(elem), args))
                    else:
                        pieces.append(self.build_tooltip_line_item(color, elem.text, args))
                return pieces
            elif args['style'] == 'split' or args['style'] == 'whtt-sellprice':
                return [self.build_tooltip_line_item(color, element.text, args)]
        else:
            pieces = []
            for elem in element.contents:
                if isinstance(elem, NavigableString):
                    pieces.append(self.build_tooltip_line_item(color, str(elem)))
                else:
                    pieces.append(self.build_tooltip_line_item(color, elem.text))
            return pieces

    @staticmethod
    def build_tooltip_line_item(color, text, args=None):
        return {'color': color, 'text': text, 'args': args}

    @staticmethod
    def no_nav_strings(elements):
        for element in elements:
            if isinstance(element, NavigableString):
                return False
        return True

    @staticmethod
    def intersection(one, two):
        temp = set(two)
        return [x for x in one if x in temp]

    @staticmethod
    def determine_style(style, element):
        style_args = {'style': style, 'value': []}
        if style == 'indent':
            style_args['value'].append(15)
        elif style == 'split':
            idx = len(element.contents[0].text)
            style_args['value'].append(idx)
        elif style == 'whtt-sellprice':
            for item in element.contents:
                if isinstance(item, NavigableString):
                    style_args['value'].append({'pre': len(item)})
                else:
                    currency = item.attrs['class'][0]
                    if currency == 'moneygold':
                        style_args['value'].append({'gold': len(item.text)})
                    elif currency == 'moneysilver':
                        style_args['value'].append({'silver': len(item.text)})
                    elif currency == 'moneycopper':
                        style_args['value'].append({'copper': len(item.text)})
        else:
            return None
        return style_args
