"""
This file contains special instructions for selection, subsetting, and hoisting
rules for the Khan Academy nodes that are applied as part of the creation of the
corresponding Kolibri channel.
"""


# these topics are not relevant
GLOBAL_SLUG_BLACKLIST = [
    "new-and-noteworthy",
    "talks-and-interviews",
    "coach-res",
]


# we don't support scratchpad content so we skip the programming topics
GLOBAL_SLUG_BLACKLIST += [
    "cs",
    "towers-of-hanoi",
    "computing",
]  


# TODO(ivan): review recent tree to check for new parner content to add to this list
# KA partner content for which we don't have explicit permission to redistribute
GLOBAL_SLUG_BLACKLIST += [
    "MoMA",
    "getty-museum",
    "stanford-medicine",
    "crash-course1",
    "mit-k12",
    "hour-of-code",
    "metropolitan-museum",
    "bitcoin",
    "tate",
    "crash-course1",
    "crash-course-bio-ecology",
    "british-museum",
    "aspeninstitute",
    "asian-art-museum",
    "amnh",
    "nova",
]


# Skip NWEA duplicate MAP Growth trees, see https://www.nwea.org/map-growth/
GLOBAL_SLUG_BLACKLIST += [
    'mappers',      # https://www.khanacademy.org/mappers
    'kmap'          # https://www.khanacademy.org/kmap
]


# common core
# GLOBAL_SLUG_BLACKLIST += ["cc-third-grade-math", "cc-fourth-grade-math", "cc-fifth-grade-math", "cc-sixth-grade-math",
#                    "cc-seventh-grade-math", "cc-eighth-grade-math"]


# TODO(jamalex): re-check these videos later and remove them from here if they've recovered
# errors on video downloads
# GLOBAL_SLUG_BLACKLIST += ["mortgage-interest-rates", "factor-polynomials-using-the-gcf", "inflation-overview",
#                    "time-value-of-money", "changing-a-mixed-number-to-an-improper-fraction",
#                    "applying-the-metric-system"]



# Additional slugs to skip for specific languages (by internal language code)
SLUG_BLACKLIST_PER_LANG = {
    'zh-CN': [
        "money-and-banking",  # Mar 25: contains mostly non-public youtube videos
    ],
}



def get_slug_blacklist(lang=None, variant=None):
    """
    Returns a list of KA slugs to skip when creating the channel.
    Combines the "global" slug blacklist that applies for all channels, and 
    additional customization for specific languages or curriculum variants.
    """
    SLUG_BLACKLIST = GLOBAL_SLUG_BLACKLIST
    if lang in SLUG_BLACKLIST_PER_LANG.keys():
        SLUG_BLACKLIST.extend(SLUG_BLACKLIST_PER_LANG[lang])
    return SLUG_BLACKLIST
