#!/usr/bin/env python
import os

from le_utils.constants.languages import getlang
from ricecooker.chefs import SushiChef
from ricecooker.classes.nodes import ChannelNode
from ricecooker.config import LOGGER

from common_core_tags import generate_common_core_mapping
from constants import get_channel_title
from constants import get_channel_description

from tsvkhan import TSVManager




class KhanAcademySushiChef(SushiChef):
    """
    Khan Academy sushi chef.
    """
    slug_blacklist = []      # spec about `KhanTopic`s to be skipped
    topics_by_slug = {}      # lookup table { slug --> KhanTopic }
    topic_replacements = {}  # spec about `KhanTopic`s to be replaced


    def parse_lang_and_variant_from_kwargs(self, kwargs):
        """
        Helper method to parse and validate the `lang` and `variant` options.
        Returns: (lang, variant), where `lang` uses internal repr. from le-utils
        and `variant` (str or None) identifies different channel version.
        """
        if "lang" not in kwargs:
            raise ValueError('Khan Academy chef must be run with lang=<code>')
        lang = kwargs["lang"]
        assert getlang(lang), 'Language code ' + lang + ' not recognized'
        variant = kwargs.get("variant", None)
        return lang, variant


    def get_channel_dict(self, kwargs):
        """
        Returns the channel info as a Python dictionary (to avoid duplication).
        """
        lang, variant = self.parse_lang_and_variant_from_kwargs(kwargs)
        if variant:
            channel_source_id = "KA ({}/{})".format(lang, variant)
        else:
            channel_source_id = "KA ({})".format(lang)
        # Build dict with all the info required to create the ChannelNode object
        channel_dict = dict(
            source_id=channel_source_id,
            source_domain="khanacademy.org",
            title=get_channel_title(lang=lang, variant=variant),
            description=get_channel_description(lang=lang, variant=variant),
            thumbnail=os.path.join("chefdata", "khan-academy-logo.png"),
            language=lang,
        )
        return channel_dict

    def get_channel(self, **kwargs):
        """
        Override the base class method to load the same data as in `pre_run`.
        """
        channel_dict = self.get_channel_dict(kwargs)
        return ChannelNode(**channel_dict)


    def get_json_tree_path(self, **kwargs):
        """
        Return path to file that contains the ricecooker json tree.
        """
        lang, variant = self.parse_lang_and_variant_from_kwargs(kwargs)
        if variant:
            filename_suffix = "{}_{}".format(lang, variant)
        else:
            filename_suffix = lang
        RICECOOKER_JSON_TREE_TPL = "ricecooker_json_tree_{}.json"
        json_filename = RICECOOKER_JSON_TREE_TPL.format(filename_suffix)
        json_tree_path = os.path.join(self.TREES_DATA_DIR, json_filename)
        return json_tree_path

    def construct_channel(self, *args, **options):
        """
        This is where all the works happens for this chef:
        - Load the source tree from the Khan Academy API
        - Convert the tree of Khan-objects in ricecooker_json dicts objects
        - Write ricecooker json tree to the appropriate file
        """
        lang, variant = self.parse_lang_and_variant_from_kwargs(options)

        if lang == "en" and variant != "in-in":
            generate_common_core_mapping()

        channel = self.get_channel(**options)

        LOGGER.info("Downloading KA topic tree")
        # Obtain the complete topic tree for lang=lang from the KA API
        TSVManager(channel, lang=lang, variant=variant)

        return channel

if __name__ == "__main__":
    chef = KhanAcademySushiChef()
    chef.main()
