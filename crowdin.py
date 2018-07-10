import fnmatch
import glob
import os
import shutil
import tempfile
import zipfile

import polib
from constants import CROWDIN_URL, SUPPORTED_LANGS
from network import make_request
from ricecooker.utils.caching import (CacheControlAdapter,
                                      CacheForeverHeuristic, FileCache)


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


def retrieve_translations(lang_code, includes="*.po"):

    if lang_code in SUPPORTED_LANGS:
        return {}

    r = make_request(CROWDIN_URL.format(key=os.environ['KA_CROWDIN_SECRET_KEY'], lang_code=lang_code), timeout=180)

    with open('crowdin.zip', "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    zip_extraction_path = tempfile.mkdtemp()

    with zipfile.ZipFile('crowdin.zip') as zf:
        zf.extractall(zip_extraction_path)

    all_filenames = glob.iglob(
        os.path.join(zip_extraction_path, "**"),
        recursive=True
    )
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
