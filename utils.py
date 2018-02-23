
import json
from collections import OrderedDict

from constants import V2_API_URL
from le_utils.constants.languages import _LANGLOOKUP, getlang
from network import make_request


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
