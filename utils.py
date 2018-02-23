
import json
from collections import OrderedDict

from constants import V2_API_URL
from le_utils.constants.languages import _LANGLOOKUP, getlang
from network import make_request


def get_lang_code_list(lang):
    """
    Returns a list of language codes that has a similar language name to the specified language code.

    Example 1: Swahili language has {
                "sw":{ "name":"Swahili", "native_name":"Kiswahili" },
                "swa":{ "name":"Swahili", "native_name":"Kiswahili" },
            }
            Function call is `get_lang_code_list("sw")`.
            Return is `["sw", "swa"]`.

    Example 2: Somali language has {
                "som":{ "name":"Somali", "native_name":"Soomaaliga" },
                "so":{ "name":"Somali", "native_name":"Soomaaliga, af Soomaali" },
            }
            Function call is `get_lang_code_list("so")`.
            Return is `["so", "som"]`.
    """
    lang_name = getlang(lang).name

    # TODO: Replace with list comprehension?
    # lang_code_list = [obj[0] for obj in langlookup.items() if obj[1]["name"] == lang_name]

    lang_code_list = []
    for obj in _LANGLOOKUP.items():
        name = obj[1].name.split(',')[0]
        if name == lang_name:
            lang_code_list.append(obj[0])
    # MUST: Return a sorted list to make debugging easier.
    return sorted(lang_code_list)


def get_video_id_english_mappings():
    projection = json.dumps({"videos": [
        OrderedDict(
            [("youtubeId", 1),
             ("id", 1)]
        )]})

    r = make_request(V2_API_URL.format(lang='en', projection=projection), timeout=120)
    english_video_data = r.json()
    english_video_data = english_video_data["videos"]

    mapping = {n["id"]: n["youtubeId"] for n in english_video_data}

    return mapping
