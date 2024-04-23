import fnmatch
import glob
import os
import shutil
import sys
import tempfile
import zipfile

import polib
from constants import CROWDIN_URL, SUPPORTED_LANGS, KHAN_ACADEMY_LANGUAGE_MAPPING
from network import make_request
from ricecooker.config import LOGGER


CROWDIN_CACHE_DIR = os.path.join("chefdata", "crowdin")
if not os.path.exists(CROWDIN_CACHE_DIR):
    os.makedirs(CROWDIN_CACHE_DIR, exist_ok=True)


# monkey patch polib.POEntry.merge
def new_merge(self, other):
    """
    Add the non-plural msgstr of `other` rather than an empty string.
    Basically, re-add the change in
    https://github.com/learningequality/ka-lite/commit/9f0aa49579a5d4c98df548863d20a252ed93220e
    but using monkey patching rather than editing the source file directly.
    """
    self.old_merge(other)
    self.msgstr = other.msgstr if other.msgstr else self.msgstr


POEntry_class = polib.POEntry
POEntry_class.old_merge = POEntry_class.merge
POEntry_class.merge = new_merge


class Catalog(dict):
    """
    Just like a dict, but computes some additional metadata specific to i18n catalog files.
    """

    def __init__(self, pofile=None):
        """
        Extract the strings from the given pofile, and computes the metadata.
        """
        # Add an entry for the empty message
        self[""] = ""
        if not pofile:
            pofile = []
        else:
            self.update({m.msgid: m.msgstr for m in pofile if m.translated()})

        super().__init__()


def retrieve_translations(lang, includes="*.po"):

    if lang in SUPPORTED_LANGS:
        return {}

    lang_code = KHAN_ACADEMY_LANGUAGE_MAPPING.get(lang, lang)

    if "CROWDIN_USERNAME" not in os.environ or "CROWDIN_ACCOUNT_KEY" not in os.environ:
        LOGGER.error(
            "Error missing Crowdin creds needed to get KA contnet translations."
        )
        LOGGER.error("Must set ENV vars CROWDIN_USERNAME and/or CROWDIN_ACCOUNT_KEY")
        LOGGER.error(
            "get from /data/sushi-chef-khan-academy/credentials/crowdinkeys.env on vader"
        )
        LOGGER.error(
            "or crate an account and get from https://crowdin.com/settings#api-key"
        )
        sys.exit(1)
    username = os.environ["CROWDIN_USERNAME"]
    account_key = os.environ["CROWDIN_ACCOUNT_KEY"]
    url = CROWDIN_URL.format(
        lang_code=lang_code, username=username, account_key=account_key
    )

    filename = "khanacademy_{lang_code}.zip".format(lang_code=lang_code)
    filepath = os.path.join(CROWDIN_CACHE_DIR, filename)

    # GET
    LOGGER.debug("Getting translations from the khanacademy project...")
    r = make_request(url, timeout=180)
    with open(filepath, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    # UNZIP
    zip_extraction_path = tempfile.mkdtemp()
    with zipfile.ZipFile(filepath) as zf:
        zf.extractall(zip_extraction_path)
    all_filenames = glob.iglob(os.path.join(zip_extraction_path, "**"), recursive=True)
    filenames = fnmatch.filter(all_filenames, includes)

    # use the polib library, since it's much faster at concatenating
    # po files.  it doesn't have a dict interface though, so we'll
    # reread the file using babel.Catalog.
    with tempfile.NamedTemporaryFile() as f:
        main_pofile = polib.POFile(fpath=f.name)

        for filename in filenames:
            pofile = polib.pofile(filename)
            main_pofile.merge(pofile)

        for entry in main_pofile:
            entry.obsolete = False

        main_pofile.save()

    shutil.rmtree(zip_extraction_path)

    msgid_mapping = Catalog(main_pofile)

    return msgid_mapping
