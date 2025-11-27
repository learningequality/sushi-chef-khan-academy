#!/usr/bin/env python
import argparse
import os
import subprocess
import sys

from le_utils.constants.languages import getlang
from ricecooker.chefs import SushiChef
from ricecooker.classes.nodes import ChannelNode
from ricecooker.config import LOGGER

from common_core_tags import generate_common_core_mapping
from constants import get_channel_title
from constants import get_channel_description
from constants import LANGUAGE_CURRICULUM_MAP

from tsvkhan import TSVManager


def get_supported_language_variants():
    """
    Get all supported language and variant combinations.

    Returns:
        list: List of tuples (lang, variant) where variant is None for languages without curricula
    """
    result = []
    for entry in LANGUAGE_CURRICULUM_MAP:
        le_lang = entry["le_lang"]
        if "curricula" in entry:
            # Language has curricula - include only supported variants
            for curriculum in entry["curricula"]:
                if curriculum.get("supported", False):
                    result.append((le_lang, curriculum["curriculum_key"]))
        else:
            # Language without curricula - include if supported
            if entry.get("supported", False):
                result.append((le_lang, None))
    return result


def get_all_language_variants(include_all_variants=False):
    """
    Get all language and variant combinations.

    Args:
        include_all_variants: If True, include all curriculum variants.
                            If False, only include supported curriculum variants.

    Returns:
        list: List of tuples (lang, variant) where variant is None for languages without curricula
    """
    result = []
    for entry in LANGUAGE_CURRICULUM_MAP:
        le_lang = entry["le_lang"]
        if "curricula" in entry:
            # Language has curricula
            for curriculum in entry["curricula"]:
                if include_all_variants or curriculum.get("supported", False):
                    result.append((le_lang, curriculum["curriculum_key"]))
        else:
            # Language without curricula - always include
            result.append((le_lang, None))
    return result


def get_language_variants_to_run(lang_arg, variant_arg):
    """
    Determine which language/variant combinations to run based on arguments.

    Args:
        lang_arg: Value of --lang argument
        variant_arg: Value of --variant argument

    Returns:
        list of (lang, variant) tuples, or None for single-language mode
    """
    if lang_arg == "supported":
        return get_supported_language_variants()
    elif lang_arg == "all":
        include_all_variants = (variant_arg == "all")
        return get_all_language_variants(include_all_variants=include_all_variants)
    else:
        return None  # Single language mode


def run_chef_for_multiple_languages(combinations, mode_description):
    """
    Run chef in subprocess for each language/variant combination.

    Args:
        combinations: List of (lang, variant) tuples
        mode_description: Description for logging (e.g., "all supported languages")
    """
    LOGGER.info(f"Running chef for {mode_description}")
    LOGGER.info(f"Found {len(combinations)} language/variant combinations")

    for lang, variant in combinations:
        LOGGER.info(f"\n{'='*80}")
        LOGGER.info(f"Starting chef run for lang={lang}, variant={variant}")
        LOGGER.info(f"{'='*80}\n")

        # Build subprocess command
        cmd = [sys.executable, __file__]
        cmd.extend(["--lang", lang])
        if variant:
            cmd.extend(["--variant", variant])

        # Add all other arguments except --lang and --variant
        skip_next = False
        for arg in sys.argv[1:]:
            if skip_next:
                skip_next = False
                continue
            if arg in ["--lang", "--variant"]:
                skip_next = True
                continue
            if arg in ["supported", "all"]:
                continue
            cmd.append(arg)

        # Run subprocess
        result = subprocess.run(cmd)
        if result.returncode != 0:
            LOGGER.warning(f"Chef run failed for lang={lang}, variant={variant}")

    LOGGER.info(f"\n{'='*80}")
    LOGGER.info(f"Completed {mode_description}")
    LOGGER.info(f"{'='*80}\n")


class KhanAcademySushiChef(SushiChef):
    """
    Khan Academy sushi chef.
    """

    slug_blacklist = []  # spec about `KhanTopic`s to be skipped
    topics_by_slug = {}  # lookup table { slug --> KhanTopic }
    topic_replacements = {}  # spec about `KhanTopic`s to be replaced
    DOMAIN_AUTH_HEADERS = {
        "amara.org": {
            "X-api-key": "AMARA_API_KEY",
        },
    }

    def parse_lang_and_variant_from_kwargs(self, kwargs):
        """
        Helper method to parse and validate the `lang` and `variant` options.
        Returns: (lang, variant), where `lang` uses internal repr. from le-utils
        and `variant` (str or None) identifies different channel version.
        """
        if "lang" not in kwargs:
            raise ValueError("Khan Academy chef must be run with lang=<code>")
        lang = kwargs["lang"]
        assert getlang(lang), "Language code " + lang + " not recognized"
        variant = kwargs.get("variant", None)
        hires = bool(kwargs.get("hires", False))
        return lang, variant, hires

    def get_channel_dict(self, kwargs):
        """
        Returns the channel info as a Python dictionary (to avoid duplication).
        """
        lang, variant, hires = self.parse_lang_and_variant_from_kwargs(kwargs)
        variant_id = lang
        if variant:
            variant_id += "/" + variant
        if hires:
            variant_id += "/hires"
        channel_source_id = "KA ({})".format(variant_id)
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
        lang, variant, _ = self.parse_lang_and_variant_from_kwargs(kwargs)
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
        lang, variant, hires = self.parse_lang_and_variant_from_kwargs(options)

        if lang == "en" and variant == "us-cc":
            generate_common_core_mapping()

        channel = self.get_channel(**options)

        LOGGER.info("Downloading KA topic tree")
        # Obtain the complete topic tree for lang=lang from the KA API
        verbose = options.get('verbose', False)
        TSVManager(channel, lang=lang, variant=variant, hires=hires, verbose=verbose)

        return channel


if __name__ == "__main__":
    # Parse args to check for special lang values
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", help="Language code or special value (supported/all)")
    parser.add_argument("--variant", help="Curriculum variant or special value (all)")
    args, unknown = parser.parse_known_args()

    # Determine which combinations to run
    combinations = get_language_variants_to_run(args.lang, args.variant)

    if combinations is not None:
        # Multi-language mode - determine description for logging
        if args.lang == "supported":
            mode_desc = "all supported languages and variants"
        elif args.variant == "all":
            mode_desc = "all languages and all variants"
        else:
            mode_desc = "all languages (supported variants only)"

        run_chef_for_multiple_languages(combinations, mode_desc)
    else:
        # Normal single-language run
        chef = KhanAcademySushiChef()
        chef.main()
