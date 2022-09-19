"""
This file contains special instructions for selection, subsetting, and hoisting
rules for the Khan Academy nodes that are applied as part of the creation of the
corresponding Kolibri channel.
"""
from ricecooker.config import LOGGER

# these topics are not relevant or impossible to import through the API
GLOBAL_SLUG_BLACKLIST = [
    "new-and-noteworthy",
    "talks-and-interviews",
    "coach-res",
    "teacher-essentials",       # Contains info specific to KA website
    "khan-kids-page",           # Link to KA Kids app (skip to avoid empty topic)
    "khan-kids-app-page",       # Link to KA Kids app (skip to avoid empty topic)
    "indiacourse",              # India-specific KA resources
    "talent-search",            # India-specific KA resources
    "students",                 # login-requiring page on KA site
    "parents-mentors-1",        # articles-only (revisit once we support article)
    "teacher-toolbox",          # special info webpage on KA site
    "educator-toolbox",         # special info webpage on KA site
    "our-content",              # special info webpage on KA site
    "product-tour-videos",      # special info webpage on KA site
    "get-started",              # skip non-essential college topics (July 2020)
    "making-high-school-count", # skip non-essential college topics (July 2020)
    "paying-for-college",       # skip non-essential college topics (July 2020)
    "wrapping-up",              # skip non-essential college topics (July 2020)
    "careers-and-personal-finance",  # skip non-essential $$$ topic (July 2020)
    "internal-courses",         # KA internal domain
]

# we don't support scratchpad content so we skip the programming topics
GLOBAL_SLUG_BLACKLIST += [
    "cs",
    "towers-of-hanoi",
    "computing",
]

# July 2020: Skip the "Partner content" and "Test prep" Level 1 topics since
# these materials will no longer be maintained upsteam. For more info, see the
# KA announcement https://khanacademy.zendesk.com/hc/en-us/articles/360043801271
GLOBAL_SLUG_BLACKLIST += [
    "partner-content",
    "test-prep",
    "math-for-fun-and-glory",
    "ap-world-history",
    "music",
    "all-star-orchestra",
]

# KA partner content for which we don't have explicit permission to redistribute
# (these detailed exclusions are no longer necessary since we exclude the entire
# "partner-content" slug above: leaving here for information purposes )
GLOBAL_SLUG_BLACKLIST += [
    "MoMA",                             # already covered by `partner-content`
    "getty-museum",                     # already covered by `partner-content`
    "stanford-medicine",                # already covered by `partner-content`
    "mit-k12",                          # already covered by `partner-content`
    "hour-of-code",                     # already covered by `partner-content`
    "metropolitan-museum",              # already covered by `partner-content`
    "tate",                             # already covered by `partner-content`
    "british-museum",                   # already covered by `partner-content`
    "aspeninstitute",                   # already covered by `partner-content`
    "asian-art-museum",                 # already covered by `partner-content`
    "amnh",                             # already covered by `partner-content`
    "nova",                             # already covered by `partner-content`
    "pixar",                            # already covered by `partner-content`
    "pixar-latam",                      # already covered by `partner-content`
    "wi-phi",                           # already covered by `partner-content`
    "science-engineering-partners",     # already covered by `partner-content`
    "arts-humanities-partners",         # already covered by `partner-content`
    "computing-partners",               # already covered by `partner-content`
    "crash-course1",
    "crash-course-bio-ecology",
    "bitcoin",                  # TODO: revisit; videos seem to be CC BY-NC-SA
]


# Skip NWEA duplicate MAP Growth trees, see https://www.nwea.org/map-growth/
GLOBAL_SLUG_BLACKLIST += [
    'mappers',      # https://www.khanacademy.org/mappers
    'kmap'          # https://www.khanacademy.org/kmap
]


# Empty/placeholder topics that are handled by TOPIC_TREE_REPLACMENTS_PER_LANG
GLOBAL_SLUG_BLACKLIST += [
    "brazil-math-grades",               # empty topic in pt-BR topic tree
    "ciencias-por-ano",                 # empty topic in pt-BR topic tree
    #
    "in-math-by-grade",                 # empty topic in the en/in-in topic tree
    "hindi",                            # empty topic in the en/in-in topic tree
    "math-hindi",                       # empty topic in the en/in-in topic tree
    "science-hindi",                    # empty topic in the en/in-in topic tree
    "science-india",                    # empty topic in the en/in-in topic tree
]


# TODO(jamalex): re-check these videos later and remove them from here if they've recovered
# errors on video downloads
# GLOBAL_SLUG_BLACKLIST += ["mortgage-interest-rates", "factor-polynomials-using-the-gcf", "inflation-overview",
#                    "time-value-of-money", "changing-a-mixed-number-to-an-improper-fraction",
#                    "applying-the-metric-system"]



# Additional SLUG_BLACKLIST for specific languages and variants
# The keys are either internal lang codes (str) or (lang, variant) tuples (str, str)
SLUG_BLACKLIST_PER_LANG = {
    "zh-CN": [
        "money-and-banking",  # Mar 25 contains mostly non-public youtube videos
    ],
    "en": [],       # put general skippable things from the English channel here
    ("en", "us-cc"): [
        # Note: no need to list math and science topics since these are handled
        #       by the tree replacement logic in TOPIC_TREE_REPLACMENTS_PER_LANG
        "iit-jee-subject",
    ],
    ("en", "in-in"): [
        # Note: no need to list math and science topics since these are handled
        #       by the tree replacement logic in TOPIC_TREE_REPLACMENTS_PER_LANG
        "ap-us-history",                           # US-specific history lessons
        "ap-us-government-and-politics",           # US-specific history lessons
        "cahsee-subject",              # California High School Exit Examination
    ],
    "es": [
        "matematicas-innova-schools",  # specialized for private schools in Perú
        "4-grado-innova-schools",
        "5-grado-innova-schools",
        "6-grado-innova-schools",
        "10-grado-innova-schools",
        "piloto-innova-4-grado",
        "recursos",                       # Contains info specific to KA website
        "khan-for-educators",             # Contains info specific to KA website
        "khan-para-maestros",             # Contains info specific to KA website
        "new-spanish-content-es",         # seems to be a draft/unfinished topic
    ],
    "pt-BR": [
        "art-history",
    ]
}

def get_slug_blacklist(lang=None, variant=None):
    """
    Returns a list of KA slugs to skip when creating the channel.
    Combines the "global" slug blacklist that applies for all channels, and
    additional customization for specific languages or curriculum variants.
    """
    SLUG_BLACKLIST = GLOBAL_SLUG_BLACKLIST
    if variant and (lang, variant) in SLUG_BLACKLIST_PER_LANG:
        SLUG_BLACKLIST.extend(SLUG_BLACKLIST_PER_LANG[(lang, variant)])
    elif lang in SLUG_BLACKLIST_PER_LANG:
        SLUG_BLACKLIST.extend(SLUG_BLACKLIST_PER_LANG[lang])
    else:
        LOGGER.warning('No slugs for lang=' + lang + ' variant=' + str(variant))
    return SLUG_BLACKLIST


# Topic tree replacments (slug --> list of subtrees of slug include directives)
# If a slug is encountered in the tree replacements data for the current channel
# the KhanNode is dropped from the tree and replced by the list of TopicNodes
# which are then populated with children from the list of include directives.
# Usually the "math" KhanNode gets replaced by usual "Math by Subject" and
# one or more "Math by Grade" topic subtrees populated from localized topic trees.
#
# The keys are either internal lang codes (str) or (lang, variant) tuples (str, str)
# For most channels there is only one variant --- the `None` variant,
# except for English where the "in-in" variant contains materials specialized to
# the India curriculum, with certain videos available both in English and Hindi.
TOPIC_TREE_REPLACMENTS_PER_LANG = {
    "en": {
        "math": [
            {"slug": "math", "translatedTitle": "Math", "children": [
                {"slug": "early-math", "translatedTitle": "Early math"},
                {"slug": "arithmetic", "translatedTitle": "Arithmetic"},
                {"slug": "pre-algebra", "translatedTitle": "Pre-algebra"},
                {"slug": "get-ready-for-algebra-i", "translatedTitle": "Get ready for Algebra 1"},
                {"slug": "algebra", "translatedTitle": "Algebra 1"},
                {"slug": "get-ready-for-geometry", "translatedTitle": "Get ready for Geometry"},
                {"slug": "geometry", "translatedTitle": "Geometry"},
                {"slug": "get-ready-for-algebra-ii", "translatedTitle": "Get ready for Algebra 2"},
                {"slug": "algebra2", "translatedTitle": "Algebra 2"},
                {"slug": "trigonometry", "translatedTitle": "Trigonometry"},
                {"slug": "get-ready-for-precalculus", "translatedTitle": "Get ready for Precalculus"},
                {"slug": "precalculus", "translatedTitle": "Precalculus"},
                {"slug": "statistics-probability", "translatedTitle": "Statistics & probability"},
                {"slug": "get-ready-for-ap-calc", "translatedTitle": "Get ready for AP® Calculus"},
                {"slug": "ap-calculus-ab", "translatedTitle": "AP®︎ Calculus AB"},
                {"slug": "ap-calculus-bc", "translatedTitle": "AP®︎ Calculus BC"},
                {"slug": "get-ready-for-ap-statistics", "translatedTitle": "Get ready for AP® Statistics"},
                {"slug": "ap-statistics", "translatedTitle": "AP®︎ Statistics"},
                {"slug": "multivariable-calculus", "translatedTitle": "Multivariable calculus"},
                {"slug": "differential-equations", "translatedTitle": "Differential equations"},
                {"slug": "linear-algebra", "translatedTitle": "Linear algebra"},
            ]},
            {"slug": "k-8-grades", "translatedTitle": "Math by grade (USA)", "children": [
                {"slug": "cc-kindergarten-math", "translatedTitle": "Kindergarten"},
                {"slug": "cc-1st-grade-math", "translatedTitle": "1st grade"},
                {"slug": "cc-2nd-grade-math", "translatedTitle": "2nd grade"},
                {"slug": "get-ready-for-3rd-grade", "translatedTitle": "Get ready for 3rd grade"},
                {"slug": "cc-third-grade-math", "translatedTitle": "3rd grade"},
                {"slug": "get-ready-for-4th-grade", "translatedTitle": "Get ready for 4th grade"},
                {"slug": "cc-fourth-grade-math", "translatedTitle": "4th grade"},
                {"slug": "get-ready-for-5th-grade", "translatedTitle": "Get ready for 5th grade"},
                {"slug": "cc-fifth-grade-math", "translatedTitle": "5th grade"},
                {"slug": "get-ready-for-6th-grade", "translatedTitle": "Get ready for 6th grade"},
                {"slug": "cc-sixth-grade-math", "translatedTitle": "6th grade"},
                {"slug": "get-ready-for-7th-grade", "translatedTitle": "Get ready for 7th grade"},
                {"slug": "cc-seventh-grade-math", "translatedTitle": "7th grade"},
                {"slug": "get-ready-for-8th-grade", "translatedTitle": "Get ready for 8th grade"},
                {"slug": "cc-eighth-grade-math", "translatedTitle": "8th grade"},
                {"slug": "illustrative-math", "translatedTitle": "Illustrative Mathematics", "children": [
                    {"slug": "6th-grade-illustrative-math"},
                    {"slug": "7th-grade-illustrative-math"},
                    {"slug": "8th-grade-illustrative-math"},
                ]},
                {"slug": "engageny", "translatedTitle": "Eureka Math/EngageNY", "children": [
                    {"slug": "get-ready-for-3rd-grade", "translatedTitle": "Get ready for 3rd grade"},
                    {"slug": "get-ready-for-4th-grade", "translatedTitle": "Get ready for 4th grade"},
                    {"slug": "get-ready-for-5th-grade", "translatedTitle": "Get ready for 5th grade"},
                    {"slug": "get-ready-for-6th-grade", "translatedTitle": "Get ready for 6th grade"},
                    {"slug": "get-ready-for-7th-grade", "translatedTitle": "Get ready for 7th grade"},
                    {"slug": "get-ready-for-8th-grade", "translatedTitle": "Get ready for 8th grade"},
                    {"slug": "3rd-grade-foundations-engageny"},
                    {"slug": "4th-grade-foundations-engageny"},
                    {"slug": "5th-grade-foundations-engageny"},
                    {"slug": "6th-grade-foundations-engageny"},
                    {"slug": "7th-grade-foundations-engageny"},
                    {"slug": "8th-grade-foundations-engageny"},
                    {"slug": "3rd-engage-ny"},
                    {"slug": "4th-engage-ny"},
                    {"slug": "5th-engage-ny"},
                    {"slug": "6th-engage-ny"},
                    {"slug": "7th-engage-ny"},
                    {"slug": "8th-engage-ny"},
                    {"slug": "get-ready-for-algebra-i", "translatedTitle": "Get ready for Algebra 1"},
                    {"slug": "engageny-alg-1"},
                    {"slug": "get-ready-for-geometry", "translatedTitle": "Get ready for Geometry"},
                    {"slug": "engageny-geo"},
                    {"slug": "get-ready-for-algebra-ii", "translatedTitle": "Get ready for Algebra 2"},
                    {"slug": "engageny-alg2"},
                    {"slug": "get-ready-for-precalculus", "translatedTitle": "Get ready for Precalculus"},
                    {"slug": "engageny-precalc"},
                ]},
                {"slug": "high-school-math", "translatedTitle": "High school", "children": [
                    {"slug": "math1"},
                    {"slug": "math2"},
                    {"slug": "math3"},
                    {"slug": "get-ready-for-algebra-i", "translatedTitle": "Get ready for Algebra 1"},
                    {"slug": "algebra"},
                    {"slug": "get-ready-for-geometry", "translatedTitle": "Get ready for Geometry"},
                    {"slug": "geometry"},
                    {"slug": "get-ready-for-algebra-ii", "translatedTitle": "Get ready for Algebra 2"},
                    {"slug": "algebra2"},
                    {"slug": "get-ready-for-precalculus", "translatedTitle": "Get ready for Precalculus"},
                    {"slug": "probability"},
                    {"slug": "trigonometry"},
                    {"slug": "precalculus"},
                ]},
            ]},
            {"slug": "in-math-by-grade", "translatedTitle": "Math by grade (India)", "children": [
                {"slug": "in-in-class-1st-math-cbse", "translatedTitle": "Class 1"},
                {"slug": "in-in-class-2nd-math-cbse", "translatedTitle": "Class 2"},
                {"slug": "in-in-class-3rd-math-cbse", "translatedTitle": "Class 3"},
                {"slug": "in-in-class-4th-math-cbse", "translatedTitle": "Class 4"},
                {"slug": "in-in-class-5th-math-cbse", "translatedTitle": "Class 5"},
                {"slug": "in-in-class-6th-math-cbse", "translatedTitle": "Class 6"},
                {"slug": "in-in-class-7th-math-cbse", "translatedTitle": "Class 7"},
                {"slug": "in-in-class-8th-math-cbse", "translatedTitle": "Class 8"},
                {"slug": "in-in-grade-9-ncert", "translatedTitle": "Class 9"},
                {"slug": "in-in-grade-10-ncert", "translatedTitle": "Class 10"},
                {"slug": "in-in-grade-11-ncert", "translatedTitle": "Class 11"},
                {"slug": "in-in-grade-12-ncert", "translatedTitle": "Class 12"},
            ]},
            {"slug": "math-hindi", "translatedTitle": "Learn math with Hindi videos", "children": [
                {"slug": "in-in-class-6-math-cbse-hindi"},
                {"slug": "in-in-class-7th-math-cbse-hindi"},
                {"slug": "in-in-class-8-math-india-hindi"},
                {"slug": "in-in-class-9-math-india-hindi"},
                {"slug": "in-in-class-10-math-cbse-hindi"},
                {"slug": "in-in-class-11-math-cbse-hindi"},
            ]},
        ],
        "science": [
            {"slug": "science", "translatedTitle": "Science & Engineering", "children": [
                {"slug": "physics", "translatedTitle": "Physics"},
                {"slug": "ap-physics-1", "translatedTitle": "AP®︎ Physics 1"},
                {"slug": "ap-physics-2", "translatedTitle": "AP®︎ Physics 2"},
                {"slug": "cosmology-and-astronomy", "translatedTitle": "Cosmology & astronomy"},
                {"slug": "chemistry", "translatedTitle": "Chemistry"},
                {"slug": "ap-chemistry-beta", "translatedTitle": "AP®︎ Chemistry beta"},
                {"slug": "ap-chemistry", "translatedTitle": "AP®︎ Chemistry"},
                {"slug": "organic-chemistry", "translatedTitle": "Organic chemistry"},
                {"slug": "biology", "translatedTitle": "Biology"},
                {"slug": "high-school-biology", "translatedTitle": "High school biology"},
                {"slug": "ap-biology", "translatedTitle": "AP®︎ Biology"},
                {"slug": "electrical-engineering", "translatedTitle": "Electrical engineering"},
            ]},
            {"slug": "science-india", "translatedTitle": "Science (India)", "children": [
                {"slug": "in-in-class9th-physics-india", "translatedTitle": "Physics class 9"},
                {"slug": "in-in-class10th-physics", "translatedTitle": "Physics class 10"},
                {"slug": "in-in-class-10-chemistry-india", "translatedTitle": "Chemistry class 10"},
                {"slug": "in-in-class-10-biology", "translatedTitle": "Biology class 10"},
                {"slug": "in-in-class11th-physics", "translatedTitle": "Physics class 11"},
                {"slug": "class-11-chemistry-india", "translatedTitle": "Chemistry class 11"},
                {"slug": "in-in-class-12th-physics-india", "translatedTitle": "Physics class 12"},
            ]},
            {"slug": "science-hindi", "translatedTitle": "Learn science with Hindi videos", "children": [
                {"slug": "in-in-class-10-physics-india-hindi"},
                {"slug": "in-in-class-11-physics-cbse-hindi"},
            ]},
        ],
        "ela": [
            {"slug": "ela", "translatedTitle": "English Language Arts (USA)", "children": [
                {"slug": "cc-2nd-reading-vocab", "translatedTitle": "2nd grade reading & vocabulary"},
                {"slug": "cc-3rd-reading-vocab", "translatedTitle": "3rd grade reading & vocabulary"},
                {"slug": "cc-4th-reading-vocab", "translatedTitle": "4th grade reading & vocabulary"},
                {"slug": "cc-5th-reading-vocab", "translatedTitle": "5th grade reading & vocabulary"},
                {"slug": "cc-6th-reading-vocab", "translatedTitle": "6th grade reading & vocabulary"},
                {"slug": "cc-7th-reading-vocab", "translatedTitle": "7th grade reading & vocabulary"},
                {"slug": "cc-8th-reading-vocab", "translatedTitle": "8th grade reading & vocabulary"},
                {"slug": "cc-9th-reading-vocab", "translatedTitle": "9th grade reading & vocabulary"},
                {"slug": "grammar", "translatedTitle": "Grammar"},
            ]},
        ],
    },
    ("en", "us-cc"): {
        "math": [
            {"slug": "math", "translatedTitle": "Math", "children": [
                {"slug": "early-math", "translatedTitle": "Early math"},
                {"slug": "arithmetic", "translatedTitle": "Arithmetic"},
                {"slug": "pre-algebra", "translatedTitle": "Pre-algebra"},
                {"slug": "get-ready-for-algebra-i", "translatedTitle": "Get ready for Algebra 1"},
                {"slug": "algebra", "translatedTitle": "Algebra 1"},
                {"slug": "get-ready-for-geometry", "translatedTitle": "Get ready for Geometry"},
                {"slug": "geometry", "translatedTitle": "Geometry"},
                {"slug": "get-ready-for-algebra-ii", "translatedTitle": "Get ready for Algebra 2"},
                {"slug": "algebra2", "translatedTitle": "Algebra 2"},
                {"slug": "trigonometry", "translatedTitle": "Trigonometry"},
                {"slug": "get-ready-for-precalculus", "translatedTitle": "Get ready for Precalculus"},
                {"slug": "precalculus", "translatedTitle": "Precalculus"},
                {"slug": "statistics-probability", "translatedTitle": "Statistics & probability"},
                {"slug": "get-ready-for-ap-calc", "translatedTitle": "Get ready for AP® Calculus"},
                {"slug": "ap-calculus-ab", "translatedTitle": "AP®︎ Calculus AB"},
                {"slug": "ap-calculus-bc", "translatedTitle": "AP®︎ Calculus BC"},
                {"slug": "get-ready-for-ap-statistics", "translatedTitle": "Get ready for AP® Statistics"},
                {"slug": "ap-statistics", "translatedTitle": "AP®︎ Statistics"},
                {"slug": "multivariable-calculus", "translatedTitle": "Multivariable calculus"},
                {"slug": "differential-equations", "translatedTitle": "Differential equations"},
                {"slug": "linear-algebra", "translatedTitle": "Linear algebra"},
            ]},
            {"slug": "k-8-grades", "translatedTitle": "Math by grade", "children": [
                {"slug": "cc-kindergarten-math", "translatedTitle": "Kindergarten"},
                {"slug": "cc-1st-grade-math", "translatedTitle": "1st grade"},
                {"slug": "cc-2nd-grade-math", "translatedTitle": "2nd grade"},
                {"slug": "get-ready-for-3rd-grade", "translatedTitle": "Get ready for 3rd grade"},
                {"slug": "cc-third-grade-math", "translatedTitle": "3rd grade"},
                {"slug": "get-ready-for-4th-grade", "translatedTitle": "Get ready for 4th grade"},
                {"slug": "cc-fourth-grade-math", "translatedTitle": "4th grade"},
                {"slug": "get-ready-for-5th-grade", "translatedTitle": "Get ready for 5th grade"},
                {"slug": "cc-fifth-grade-math", "translatedTitle": "5th grade"},
                {"slug": "get-ready-for-6th-grade", "translatedTitle": "Get ready for 6th grade"},
                {"slug": "cc-sixth-grade-math", "translatedTitle": "6th grade"},
                {"slug": "get-ready-for-7th-grade", "translatedTitle": "Get ready for 7th grade"},
                {"slug": "cc-seventh-grade-math", "translatedTitle": "7th grade"},
                {"slug": "get-ready-for-8th-grade", "translatedTitle": "Get ready for 8th grade"},
                {"slug": "cc-eighth-grade-math", "translatedTitle": "8th grade"},
                {"slug": "illustrative-math", "translatedTitle": "Illustrative Mathematics", "children": [
                    {"slug": "6th-grade-illustrative-math"},
                    {"slug": "7th-grade-illustrative-math"},
                    {"slug": "8th-grade-illustrative-math"},
                ]},
                {"slug": "engageny", "translatedTitle": "Eureka Math/EngageNY", "children": [
                    {"slug": "get-ready-for-3rd-grade", "translatedTitle": "Get ready for 3rd grade"},
                    {"slug": "get-ready-for-4th-grade", "translatedTitle": "Get ready for 4th grade"},
                    {"slug": "get-ready-for-5th-grade", "translatedTitle": "Get ready for 5th grade"},
                    {"slug": "get-ready-for-6th-grade", "translatedTitle": "Get ready for 6th grade"},
                    {"slug": "get-ready-for-7th-grade", "translatedTitle": "Get ready for 7th grade"},
                    {"slug": "get-ready-for-8th-grade", "translatedTitle": "Get ready for 8th grade"},
                    {"slug": "3rd-grade-foundations-engageny"},
                    {"slug": "4th-grade-foundations-engageny"},
                    {"slug": "5th-grade-foundations-engageny"},
                    {"slug": "6th-grade-foundations-engageny"},
                    {"slug": "7th-grade-foundations-engageny"},
                    {"slug": "8th-grade-foundations-engageny"},
                    {"slug": "3rd-engage-ny"},
                    {"slug": "4th-engage-ny"},
                    {"slug": "5th-engage-ny"},
                    {"slug": "6th-engage-ny"},
                    {"slug": "7th-engage-ny"},
                    {"slug": "8th-engage-ny"},
                    {"slug": "engageny-alg-1"},
                    {"slug": "engageny-geo"},
                    {"slug": "engageny-alg2"},
                    {"slug": "engageny-precalc"},
                ]},
                {"slug": "high-school-math", "translatedTitle": "High school", "children": [
                    {"slug": "math1"},
                    {"slug": "math2"},
                    {"slug": "math3"},
                    {"slug": "get-ready-for-algebra-i", "translatedTitle": "Get ready for Algebra 1"},
                    {"slug": "algebra"},
                    {"slug": "get-ready-for-geometry", "translatedTitle": "Get ready for Geometry"},
                    {"slug": "geometry"},
                    {"slug": "get-ready-for-algebra-ii", "translatedTitle": "Get ready for Algebra 2"},
                    {"slug": "algebra2"},
                    {"slug": "get-ready-for-precalculus", "translatedTitle": "Get ready for Precalculus"},
                    {"slug": "probability"},
                    {"slug": "trigonometry"},
                    {"slug": "precalculus"},
                ]},
            ]},
        ],
        "science": [
            {"slug": "science", "translatedTitle": "Science & Engineering", "children": [
                {"slug": "ms-physics", "translatedTitle": "Middle school physics - NGSS"},
                {"slug": "physics", "translatedTitle": "Physics"},
                {"slug": "ap-physics-1", "translatedTitle": "AP®︎ Physics 1"},
                {"slug": "ap-physics-2", "translatedTitle": "AP®︎ Physics 2"},
                {"slug": "middle-school-earth-and-space-science", "translatedTitle": "Middle school Earth and space science - NGSS"},
                {"slug": "cosmology-and-astronomy", "translatedTitle": "Cosmology & astronomy"},
                {"slug": "chemistry", "translatedTitle": "Chemistry"},
                {"slug": "ap-chemistry-beta", "translatedTitle": "AP®︎ Chemistry beta"},
                {"slug": "ap-chemistry", "translatedTitle": "AP®︎ Chemistry"},
                {"slug": "organic-chemistry", "translatedTitle": "Organic chemistry"},
                {"slug": "ms-biology", "translatedTitle": "Middle school biology - NGSS"},
                {"slug": "biology", "translatedTitle": "Biology"},
                {"slug": "high-school-biology", "translatedTitle": "High school biology"},
                {"slug": "ap-biology", "translatedTitle": "AP®︎ Biology"},
                {"slug": "electrical-engineering", "translatedTitle": "Electrical engineering"},
            ]},
        ],
        "ela": [
            {"slug": "ela", "translatedTitle": "English Language Arts", "children": [
                {"slug": "cc-2nd-reading-vocab", "translatedTitle": "2nd grade reading & vocabulary"},
                {"slug": "cc-3rd-reading-vocab", "translatedTitle": "3rd grade reading & vocabulary"},
                {"slug": "cc-4th-reading-vocab", "translatedTitle": "4th grade reading & vocabulary"},
                {"slug": "cc-5th-reading-vocab", "translatedTitle": "5th grade reading & vocabulary"},
                {"slug": "cc-6th-reading-vocab", "translatedTitle": "6th grade reading & vocabulary"},
                {"slug": "cc-7th-reading-vocab", "translatedTitle": "7th grade reading & vocabulary"},
                {"slug": "cc-8th-reading-vocab", "translatedTitle": "8th grade reading & vocabulary"},
                {"slug": "cc-9th-reading-vocab", "translatedTitle": "9th grade reading & vocabulary"},
                {"slug": "grammar", "translatedTitle": "Grammar"},
            ]},
        ],
    },
    ("en", "in-in"): {
        "math": [
            {"slug": "math", "translatedTitle": "Math", "children": [
                {"slug": "early-math", "translatedTitle": "Early math"},
                {"slug": "arithmetic", "translatedTitle": "Arithmetic"},
                {"slug": "pre-algebra", "translatedTitle": "Pre-algebra"},
                {"slug": "algebra", "translatedTitle": "Algebra 1"},
                {"slug": "geometry-home", "translatedTitle": "Geometry"},
                {"slug": "algebra2", "translatedTitle": "Algebra 2"},
                {"slug": "trigonometry", "translatedTitle": "Trigonometry"},
                {"slug": "statistics-probability", "translatedTitle": "Statistics & probability"},
                {"slug": "precalculus", "translatedTitle": "Precalculus"},
                {"slug": "calculus-1", "translatedTitle": "Calculus"},
                {"slug": "multivariable-calculus", "translatedTitle": "Multivariable calculus"},
                {"slug": "differential-equations", "translatedTitle": "Differential equations"},
                {"slug": "linear-algebra", "translatedTitle": "Linear algebra"},
            ]},
            {"slug": "in-math-by-grade", "translatedTitle": "Math by grade (India)", "children": [
                {"slug": "in-in-class-1st-math-cbse", "translatedTitle": "Class 1"},
                {"slug": "in-in-class-2nd-math-cbse", "translatedTitle": "Class 2"},
                {"slug": "in-in-class-3rd-math-cbse", "translatedTitle": "Class 3"},
                {"slug": "in-in-class-4th-math-cbse", "translatedTitle": "Class 4"},
                {"slug": "in-in-class-5th-math-cbse", "translatedTitle": "Class 5"},
                {"slug": "in-in-class-6th-math-cbse", "translatedTitle": "Class 6"},
                {"slug": "in-in-class-7th-math-cbse", "translatedTitle": "Class 7"},
                {"slug": "in-in-class-8th-math-cbse", "translatedTitle": "Class 8"},
                {"slug": "in-in-grade-9-ncert", "translatedTitle": "Class 9"},
                {"slug": "in-in-grade-10-ncert", "translatedTitle": "Class 10"},
                {"slug": "in-in-grade-11-ncert", "translatedTitle": "Class 11"},
                {"slug": "in-in-grade-12-ncert", "translatedTitle": "Class 12"},
            ]},
            {"slug": "math-hindi", "translatedTitle": "Learn math with Hindi videos", "children": [
                {"slug": "in-in-class-6-math-cbse-hindi"},
                {"slug": "in-in-class-7th-math-cbse-hindi"},
                {"slug": "in-in-class-8-math-india-hindi"},
                {"slug": "in-in-class-9-math-india-hindi"},
                {"slug": "in-in-class-10-math-cbse-hindi"},
                {"slug": "in-in-class-11-math-cbse-hindi"},
            ]},
        ],
        "science": [
            {"slug": "science-india", "translatedTitle": "Science (India)", "children": [
                {"slug": "in-in-class9th-physics-india", "translatedTitle": "Physics class 9"},
                {"slug": "in-in-class10th-physics", "translatedTitle": "Physics class 10"},
                {"slug": "in-in-class-10-chemistry-india", "translatedTitle": "Chemistry class 10"},
                {"slug": "class-10-biology", "translatedTitle": "Biology class 10"},
                {"slug": "in-in-class11th-physics", "translatedTitle": "Physics class 11"},
                {"slug": "class-11-chemistry-india", "translatedTitle": "Chemistry class 11"},
                {"slug": "in-in-class-12th-physics-india", "translatedTitle": "Physics class 12"},
            ]},
            {"slug": "science-hindi", "translatedTitle": "Learn science with Hindi videos", "children": [
                {"slug": "in-in-class-10-physics-india-hindi"},
                {"slug": "in-in-class-11-physics-cbse-hindi"},
            ]},
            {"slug": "science", "translatedTitle": "Science & Engineering", "children": [
                {"slug": "physics", "translatedTitle": "Physics"},
                {"slug": "cosmology-and-astronomy", "translatedTitle": "Cosmology & astronomy"},
                {"slug": "chemistry", "translatedTitle": "Chemistry"},
                {"slug": "organic-chemistry", "translatedTitle": "Organic chemistry"},
                {"slug": "biology", "translatedTitle": "Biology"},
                {"slug": "electrical-engineering", "translatedTitle": "Electrical engineering"},
            ]},
        ],
        "ela": [
            {"slug": "ela", "translatedTitle": "English Language Arts (USA)", "children": [
                {"slug": "cc-2nd-reading-vocab", "translatedTitle": "2nd grade reading & vocabulary"},
                {"slug": "cc-3rd-reading-vocab", "translatedTitle": "3rd grade reading & vocabulary"},
                {"slug": "cc-4th-reading-vocab", "translatedTitle": "4th grade reading & vocabulary"},
                {"slug": "cc-5th-reading-vocab", "translatedTitle": "5th grade reading & vocabulary"},
                {"slug": "cc-6th-reading-vocab", "translatedTitle": "6th grade reading & vocabulary"},
                {"slug": "cc-7th-reading-vocab", "translatedTitle": "7th grade reading & vocabulary"},
                {"slug": "cc-8th-reading-vocab", "translatedTitle": "8th grade reading & vocabulary"},
                {"slug": "cc-9th-reading-vocab", "translatedTitle": "9th grade reading & vocabulary"},
            ]},
        ],
    },
    "es": {
        "math": [
            {"slug": "math", "translatedTitle": "Matemáticas", "children": [
                {"slug": "early-math", "translatedTitle": "Matemáticas elementales"},
                {"slug": "arithmetic", "translatedTitle": "Aritmética"},
                {"slug": "pre-algebra", "translatedTitle": "Preálgebra"},
                {"slug": "algebra-basics", "translatedTitle": "Fundamentos de álgebra"},
                {"slug": "algebra", "translatedTitle": "Álgebra I"},
                {"slug": "algebra2", "translatedTitle": "Álgebra II"},
                {"slug": "basic-geo", "translatedTitle": "Geometría básica"},
                {"slug": "geometry", "translatedTitle": "Geometría"},
                {"slug": "trigonometry", "translatedTitle": "Trigonometría"},
                {"slug": "precalculus", "translatedTitle": "Precálculo"},
                {"slug": "probability", "translatedTitle": "Probabilidad y estadística"},
                {"slug": "ap-calculus-ab", "translatedTitle": "Cálculo I"},
                {"slug": "ap-calculus-bc", "translatedTitle": "Cálculo II"},
                {"slug": "ap-statistics", "translatedTitle": "Estadística avanzada"},
                {"slug": "multivariable-calculus", "translatedTitle": "Cálculo multivariable"},
                {"slug": "differential-equations", "translatedTitle": "Ecuaciones diferenciales"},
                {"slug": "linear-algebra", "translatedTitle": "Álgebra linear"},
            ]},
            {"slug": "mx-math-by-grade", "translatedTitle": "Matemáticas por grado (México)", "children": [
                {"slug": "eb-1-primaria", "translatedTitle": "1° Primaria"},
                {"slug": "eb-2-primaria", "translatedTitle": "2° Primaria"},
                {"slug": "eb-3-primaria", "translatedTitle": "3° Primaria"},
                {"slug": "eb-4-primaria", "translatedTitle": "4° Primaria"},
                {"slug": "eb-5-primaria", "translatedTitle": "5° Primaria"},
                {"slug": "eb-6-primaria", "translatedTitle": "6° Primaria"},
                {"slug": "eb-1-secundaria", "translatedTitle": "1° Secundaria"},
                {"slug": "eb-2-secundaria", "translatedTitle": "2° Secundaria"},
                {"slug": "eb-3-secundaria", "translatedTitle": "3° Secundaria"},
                {"slug": "eb-1-semestre-bachillerato", "translatedTitle": "1° Semestre Bachillerato"},
                {"slug": "eb-2-semestre-bachillerato", "translatedTitle": "2° Semestre Bachillerato"},
                {"slug": "eb-3-semestre-bachillerato", "translatedTitle": "3° Semestre Bachillerato"},
                {"slug": "eb-4-semestre-bachillerato", "translatedTitle": "4° Semestre Bachillerato"},
                {"slug": "eb-5-semestre-bachillerato", "translatedTitle": "5° Semestre Bachillerato"},
                {"slug": "eb-6-semestre-bachillerato", "translatedTitle": "6° Semestre Bachillerato"},
            ]},
            {"slug": "matematicas-por-grado-pe", "translatedTitle": "Matemáticas por grado (Perú)", "children": [
                {"slug": "1-primaria-pe", "translatedTitle": "1º Primaria"},
                {"slug": "2-primaria-pe", "translatedTitle": "2° Primaria"},
                {"slug": "3-primaria-pe", "translatedTitle": "3° Primaria"},
                {"slug": "4-primaria-pe", "translatedTitle": "4° Primaria"},
                {"slug": "5-primaria-pe", "translatedTitle": "5° Primaria"},
                {"slug": "6-primaria-pe", "translatedTitle": "6° Primaria"},
                {"slug": "1-secundaria-pe", "translatedTitle": "1º Secundaria"},
                {"slug": "2-secundaria-pe", "translatedTitle": "2º Secundaria"},
                {"slug": "3-secundaria-pe", "translatedTitle": "3º Secundaria"},
                {"slug": "4-secundaria-pe", "translatedTitle": "4º Secundaria"},
                {"slug": "5-secundaria-pe", "translatedTitle": "5º Secundaria"},
            ]},
            {"slug": "matematicas-avanzadas", "translatedTitle": "Matemáticas avanzadas", "children": [
                {"slug": "ap-calculus-ab", "translatedTitle": "Cálculo I"},
                {"slug": "ap-calculus-bc", "translatedTitle": "Cálculo II"},
                {"slug": "ap-statistics", "translatedTitle": "Estadística avanzada"},
            ]},
            {"slug": "preparacion-para-la-educacion-superior", "translatedTitle": "Preparación para la educación superior", "children": [
                {"slug": "matematicas-preparacion-educacion-superior", "translatedTitle": "Matemáticas", "children": [
                    {"slug": "aritmetica-pe-pre-u", "translatedTitle": "Aritmética"},
                    {"slug": "estadistica-y-probabilidad-pe-pre-u", "translatedTitle": "Estadística y probabilidad"},
                    {"slug": "geometria-pe-pre-u", "translatedTitle": "Geometría"},
                    {"slug": "algebra-i-pe-pre-u", "translatedTitle": "Algebra I"},
                    {"slug": "algebra-ii-pe-pre-u", "translatedTitle": "Algebra II"},
                    {"slug": "trigonometria-pe-pre-u", "translatedTitle": "Trigonometría"},
                    {"slug": "razonamiento-matematico-pe-pre-u", "translatedTitle": "Razonamiento matemático"},
                ]},
                {"slug": "ciencias-preparacion-educacion-superior", "translatedTitle": "Ciencias", "children": [
                    {"slug": "biologia-pe-pre-u", "translatedTitle": "Biología"},
                    {"slug": "fisica-pe-pre-u", "translatedTitle": "Física"},
                    {"slug": "quimica-pe-pre-u", "translatedTitle": "Química"},
                ]},
            ]},
        ],
        "science": [
            {"slug": "science", "translatedTitle": "Ciencia", "children": [
                {"slug": "physics", "translatedTitle": "Física"},
                # May24: does not seem to be available form API
                # {"slug": "cosmology-and-astronomy", "translatedTitle": "Cosmología y astronomía"},
                {"slug": "chemistry", "translatedTitle": "Química"},
                # May24: does not seem to be available form API
                # {"slug": "ap-chemistry", "translatedTitle": "Química avanzada"},
                {"slug": "organic-chemistry", "translatedTitle": "Química orgánica"},
                {"slug": "biology", "translatedTitle": "Biología"},
                {"slug": "high-school-biology", "translatedTitle": "Biología de secundaria"},
                # May24: does not seem to be available form API
                # {"slug": "ap-biology", "translatedTitle": "Biología avanzada"},
                {"slug": "electrical-engineering", "translatedTitle": "Ingeniería eléctrica"},
            ]},
        ],
    },
    "pt-BR": {
        "math": [
            {"slug": "brazil-math-grades", "translatedTitle": "Matemática por ano (Alinhada à BNCC)", "children": [
                {"slug": "pt-1-ano", "translatedTitle": "1° ano"},
                {"slug": "pt-2-ano", "translatedTitle": "2° ano"},
                {"slug": "pt-3-ano", "translatedTitle": "3° ano"},
                {"slug": "pt-4-ano", "translatedTitle": "4° ano"},
                {"slug": "pt-5-ano", "translatedTitle": "5° ano"},
                {"slug": "6-ano-matematica", "translatedTitle": "6° ano"},
                {"slug": "pt-7-ano", "translatedTitle": "7° ano"},
                {"slug": "pt-8-ano", "translatedTitle": "8° ano"},
                {"slug": "pt-9-ano", "translatedTitle": "9° ano"},
            ]},
            {"slug": "math", "translatedTitle": "Matemática", "children": [
                {"slug": "early-math", "translatedTitle": "Fundamentos de matemática"},
                {"slug": "arithmetic-home", "translatedTitle": "Aritmética"},
                {"slug": "pre-algebra", "translatedTitle": "Pré-álgebra"},
                {"slug": "algebra-basics", "translatedTitle": "Noções de álgebra"},
                {"slug": "basic-geo", "translatedTitle": "Geometria básica"},
                {"slug": "geometry-home", "translatedTitle": "Geometria"},
                {"slug": "geometry", "translatedTitle": "Geometria do Ensino Médio"},
                {"slug": "trigonometry", "translatedTitle": "Trigonometria"},
                {"slug": "statistics-probability", "translatedTitle": "Estatística e probabilidade"},
                {"slug": "math1", "translatedTitle": "Matemática I (Ensino Médio)"},
                {"slug": "math2", "translatedTitle": "Matemática II (Ensino Médio)"},
                {"slug": "math3", "translatedTitle": "Matemática III (Ensino Médio)"},
                {"slug": "probability", "translatedTitle": "Estatística do Ensino Médio"},
            ]},
            {"slug": "math-avancada", "translatedTitle": "Matemática avançada", "children": [
                {"slug": "precalculus", "translatedTitle": "Pré-cálculo"},
                {"slug": "differential-calculus", "translatedTitle": "Cálculo diferencial"},
                {"slug": "integral-calculus", "translatedTitle": "Cálculo integral"},
                {"slug": "differential-equations", "translatedTitle": "Equações diferenciais"},
                {"slug": "multivariable-calculus", "translatedTitle": "Cálculo multivariável"},
                {"slug": "linear-algebra", "translatedTitle": "Álgebra linear"},
            ]},
        ],
        "science": [
            {"slug": "ciencias-por-ano", "translatedTitle": "Ciências por ano (Alinhada à BNCC)", "children": [
                {"slug": "1-ano", "translatedTitle": "1° ano"},
                {"slug": "2-ano", "translatedTitle": "2° ano"},
                {"slug": "3-ano", "translatedTitle": "3° ano"},
                {"slug": "4-ano", "translatedTitle": "4° ano"},
                {"slug": "5-ano", "translatedTitle": "5° ano"},
                {"slug": "6-ano", "translatedTitle": "6° ano"},
                {"slug": "7-ano", "translatedTitle": "7° ano"},
                {"slug": "8-ano", "translatedTitle": "8° ano"},
                {"slug": "9-ano", "translatedTitle": "9° ano"},
            ]},
            {"slug": "science", "translatedTitle": "Ciências e engenharia", "children": [
                {"slug": "physics", "translatedTitle": "Física"},
                {"slug": "chemistry", "translatedTitle": "Química"},
                {"slug": "organic-chemistry", "translatedTitle": "Química orgânica"},
                {"slug": "biology", "translatedTitle": "Biologia"},
                {"slug": "health-and-medicine", "translatedTitle": "Saúde e medicina"},
                {"slug": "electrical-engineering", "translatedTitle": "Engenharia elétrica"},
            ]},
        ],
        "humanities": [
            {"slug": "humanities", "translatedTitle": "Ciências humanas", "children": [
                {"slug": "art-history", "translatedTitle": "História da arte", "children": [
                    {"slug": "art-history-basics"},
                    {"slug": "prehistoric-art"},
                ]},
                {"slug": "lp-3-ano"},
                {"slug": "lp-4-ano"},
            ]},
            {"slug": "portugues-por-ano-bncc-ef", "translatedTitle": "Português por ano (Alinhado à BNCC)", "children": [
                {"slug": "lp-3-ano"},
                {"slug": "lp-4-ano"},
            ]},
        ],
    },
    "fr": {
        "math": [
            {"slug": "math", "translatedTitle": "Maths", "children": [
                {"slug": "early-math", "translatedTitle": "Bases en calcul"},
                {"slug": "arithmetic-home", "translatedTitle": "Arithmétique"},
                {"slug": "algebra-home", "translatedTitle": "Algèbre"},
                {"slug": "geometry-home", "translatedTitle": "Géométrie"},
                {"slug": "trigonometry", "translatedTitle": "Trigonométrie"},
                {"slug": "statistics-probability", "translatedTitle": "Probabilités et statistiques"},
                {"slug": "calculus-home", "translatedTitle": "Analyse"},
                {"slug": "differential-equations", "translatedTitle": "Équations différentielles"},
                {"slug": "linear-algebra", "translatedTitle": "Algèbre linéaire"},
            ]},
            {"slug": "k-8-grades", "translatedTitle": "Maths (France)", "children": [
                {"slug": "cycle-1b", "translatedTitle": "Cycle 1"},
                {"slug": "fr-v2-cycle-2", "translatedTitle": "Cycle 2 (CP, CE1, CE2)"},
                {"slug": "cycle-3-v2", "translatedTitle": "Cycle 3 (CM1, CM2, 6e)"},
                {"slug": "cycle-4-v2", "translatedTitle": "Cycle 4 (5e, 4e, 3e)"},
                {"slug": "fr-v2-seconde-s", "translatedTitle": "Seconde"},
                {"slug": "fr-v2-premiere-s", "translatedTitle": "Première générale"},
                {"slug": "fr-v2-terminale-s", "translatedTitle": "Terminale S"},
                {"slug": "fr-terminale-es-et-l", "translatedTitle": "Terminale ES et L"},
            ]},
            {"slug": "grades-belges", "translatedTitle": "Maths (Belgique)", "children": [
                {"slug": "be-1ere-primaire2", "translatedTitle": "1ère primaire"},
                {"slug": "be-2eme-primaire2", "translatedTitle": "2ème primaire"},
                {"slug": "be-3eme-primaire2", "translatedTitle": "3ème primaire"},
                {"slug": "be-4eme-primaire2", "translatedTitle": "4ème primaire"},
                {"slug": "be-5eme-primaire2", "translatedTitle": "5ème primaire"},
                {"slug": "be-6eme-primaire2", "translatedTitle": "6ème primaire"},
                {"slug": "revisions-ceb", "translatedTitle": "Révisions CEB"},
                {"slug": "be-1ere-secondaire2", "translatedTitle": "1ère année secondaire"},
                {"slug": "be-2eme-secondaire2", "translatedTitle": "2ème année secondaire"},
                {"slug": "revisions-ce1dv2", "translatedTitle": "Révisions CE1D "},
                {"slug": "3eme-annee-secondaire", "translatedTitle": "3ème année secondaire"},
                {"slug": "be-4eme-secondaire2", "translatedTitle": "4ème année secondaire"},
                {"slug": "be-5eme-secondaire2h2", "translatedTitle": "5ème année secondaire - 2h"},
                {"slug": "be-5eme-secondaire4h2", "translatedTitle": "5ème année secondaire - 4h"},
                {"slug": "be-5eme-secondaire6h2", "translatedTitle": "5ème année secondaire - 6h"},
                {"slug": "be-6eme-secondaire2h2", "translatedTitle": "6ème année secondaire - 2h"},
                {"slug": "be-6eme-secondaire4h2", "translatedTitle": "6ème année secondaire - 4h"},
                {"slug": "be-6eme-secondaire6h2", "translatedTitle": "6ème année secondaire - 6h"},
            ]},
        ],
    },
    "bg": {
        "math": [
            {"slug": "math", "translatedTitle": "Математика", "children": [
                {"slug": "early-math", "translatedTitle": "Начална математика"},
                {"slug": "arithmetic", "translatedTitle": "Аритметика"},
                {"slug": "pre-algebra", "translatedTitle": "Въведение в алгебрата"},
                {"slug": "algebra-basics", "translatedTitle": "Основи на алгебрата"},
                {"slug": "algebra", "translatedTitle": "Алгебра I"},
                {"slug": "algebra2", "translatedTitle": "Алгебра II"},
                {"slug": "basic-geo", "translatedTitle": "Основи на геометрията"},
                {"slug": "geometry", "translatedTitle": "Геометрия"},
                {"slug": "trigonometry", "translatedTitle": "Тригонометрия"},
                {"slug": "precalculus", "translatedTitle": "Въведение в математически анализ"},
                {"slug": "statistics-probability", "translatedTitle": "Статистика и вероятности"},
                {"slug": "differential-calculus", "translatedTitle": "Диференциално смятане"},
                {"slug": "arithmetic-home", "translatedTitle": "Аритметика (цялото съдържание)"},
                {"slug": "algebra-home", "translatedTitle": "Алгебра (цялото съдържание)"},
                {"slug": "geometry-home", "translatedTitle": "Геометрия (цялото съдържание)"},
            ]},
            {"slug": "bg-math-by-grade", "translatedTitle": "Математика (България)", "children": [
                {"slug": "preduchilishtna", "translatedTitle": "Предучилищна подготовка"},
                {"slug": "1-klas", "translatedTitle": "1. клас (България)"},
                {"slug": "2-klas", "translatedTitle": "2. клас (България)"},
                {"slug": "3-klas", "translatedTitle": "3. клас (България)"},
                {"slug": "4-klas", "translatedTitle": "4. клас (България)"},
                {"slug": "5-klas", "translatedTitle": "5. клас (България)"},
                {"slug": "6-klas", "translatedTitle": "6. клас (България)"},
                {"slug": "7-klas", "translatedTitle": "7. клас (България)"},
                {"slug": "8-klas", "translatedTitle": "8. клас (България)"},
                {"slug": "9-klas", "translatedTitle": "9. клас (България)"},
                {"slug": "10-klas", "translatedTitle": "10. клас (България)"},
                {"slug": "11-klas", "translatedTitle": "11. клас (България)"},
                {"slug": "geometry", "translatedTitle": "Гимназиална геометрия"},
                {"slug": "probability", "translatedTitle": "Гимназиална статистика"},
            ]},
        ],
        "science": [
            {"slug": "science", "translatedTitle": "Наука", "children": [
                {"slug": "cosmology-and-astronomy", "translatedTitle": "Астрономия и космология"},
                {"slug": "physics", "translatedTitle": "Физика"},
                {"slug": "chemistry", "translatedTitle": "Химия"},
                {"slug": "organic-chemistry", "translatedTitle": "Органична химия"},
                {"slug": "biology", "translatedTitle": "Биология"},
                {"slug": "health-and-medicine", "translatedTitle": "Здраве и медицина"},
            ]},
            {"slug": "bg-physics-by-grade", "translatedTitle": "Физика (България)", "children": [
                {"slug": "fizika-7-klas", "translatedTitle": "7. клас (България)"},
                {"slug": "8-klas-fizika", "translatedTitle": "8. клас (България)"},
                {"slug": "9-klas-fizika", "translatedTitle": "9. клас (България)"},
                {"slug": "fizika-10-klas", "translatedTitle": "10. клас (България)"},
                {"slug": "fizika-11-klas", "translatedTitle": "11. клас (България)"},
                {"slug": "fizika-12-klas", "translatedTitle": "12. клас (България)"},
            ]},
        ],
        "resources": [
            {"slug": "resources", "translatedTitle": "Ресурси", "children": [
                {"slug": "teacher-essentials", "translatedTitle": "Първи стъпки за учители"},
                {"slug": "students", "translatedTitle": "Първи стъпки за ученици"},
                {"slug": "parents-mentors-1", "translatedTitle": "Първи стъпки за родители"},
            ]},
        ],
    },
    "de": {
        "math": [
            {"slug": "math", "translatedTitle": "Mathe nach Themen", "children": [
                {"slug": "early-math", "translatedTitle": "Einstieg in die Mathematik"},
                {"slug": "arithmetic", "translatedTitle": "Arithmetik"},
                {"slug": "pre-algebra", "translatedTitle": "Algebra - Vorkenntnisse"},
                {"slug": "algebra-basics", "translatedTitle": "Algebra - Grundlagen"},
                {"slug": "algebra", "translatedTitle": "Algebra 1"},
                {"slug": "algebra2", "translatedTitle": "Algebra 2"},
                {"slug": "basic-geo", "translatedTitle": "Geometrie - Grundlagen"},
                {"slug": "geometry", "translatedTitle": "Geometrie - Weiterführende Kenntnisse"},
                {"slug": "trigonometry", "translatedTitle": "Trigonometrie"},
                {"slug": "probability", "translatedTitle": "Statistik - Weiterführende Kenntnisse"},
                {"slug": "precalculus", "translatedTitle": "Analysis - Vorkenntnisse"},
                {"slug": "statistics-probability", "translatedTitle": "Statistik und Wahrscheinlichkeitsrechnung"},
                {"slug": "geometry-home", "translatedTitle": "Geometrie (alle Inhalte)"},
            ]},
            {"slug": "de-math-by-grade", "translatedTitle": "Mathe nach Klassen", "children": [
                {"slug": "cc-kindergarten-math", "translatedTitle": "Vorschule"},
                {"slug": "cc-1st-grade-math", "translatedTitle": "1. Klasse"},
                {"slug": "cc-2nd-grade-math", "translatedTitle": "2. Klasse"},
                {"slug": "cc-third-grade-math", "translatedTitle": "3. Klasse"},
                {"slug": "cc-fourth-grade-math", "translatedTitle": "4. Klasse"},
                {"slug": "cc-fifth-grade-math", "translatedTitle": "5. Klasse"},
                {"slug": "cc-sixth-grade-math", "translatedTitle": "6. Klasse"},
                {"slug": "cc-seventh-grade-math", "translatedTitle": "7. Klasse"},
                {"slug": "cc-eighth-grade-math", "translatedTitle": "8. Klasse"},
            ]},
        ],
    },
    "hi": {
        "math": [
            {"slug": "math", "translatedTitle": "गणित", "children": [
                {"slug": "in-in-class-6th-math-cbse", "translatedTitle": "कक्षा 6 (इंडिया)"},
                {"slug": "in-in-class-7th-math-cbse", "translatedTitle": "कक्षा 7 (इंडिया)"},
                {"slug": "in-in-class-8th-math-cbse", "translatedTitle": "कक्षा 8 (इंडिया)"},
                {"slug": "in-in-grade-9-ncert", "translatedTitle": "कक्षा 9 (इंडिया)"},
                {"slug": "in-in-grade-10-ncert", "translatedTitle": "कक्षा 10 (इंडिया)"},
            ]},
            {"slug": "math-foundation", "translatedTitle": "गणित (आधार)", "children": [
                {"slug": "in-class-6-math-foundation", "translatedTitle": "कक्षा 6 (आधार)"},
                {"slug": "in-class-7-math-foundation", "translatedTitle": "कक्षा 7 (आधार)"},
                {"slug": "in-class-8-math-foundation", "translatedTitle": "कक्षा 8 (आधार)"},
                {"slug": "class-8th-math-revision", "translatedTitle": "कक्षा 9 (आधार)"},
                {"slug": "class-9th-math-revision", "translatedTitle": "कक्षा 10 (आधार)"},
            ]},
        ]
    },
    "km": {
        "math": [
            {"slug": "math", "translatedTitle": "គណិតវិទ្យា", "children": [
                {"slug": "early-math", "translatedTitle": "គណិតវិទ្យាថ្នាក់បឋម"},
                {"slug": "arithmetic", "translatedTitle": "លេខនព្វន្ធ"},
                # Jul 15 (Ivan) I added the following manually even thought they
                # are not in the website menu yet since they are 80%+ transalted
                {"slug": "cc-kindergarten-math"},
                {"slug": "cc-1st-grade-math"},
                {"slug": "cc-2nd-grade-math"},
                {"slug": "cc-third-grade-math"},
                {"slug": "cc-fourth-grade-math"},
                {"slug": "cc-fifth-grade-math"},
            ]},
        ]
    },
}

def get_topic_tree_replacements(lang=None, variant=None):
    """
    Returns a dictionary of replacements directives for the KA language `lang`
    and channel variant `variant` taken from TOPIC_TREE_REPLACMENTS_PER_LANG.
    """
    if variant and (lang, variant) in TOPIC_TREE_REPLACMENTS_PER_LANG:
        return TOPIC_TREE_REPLACMENTS_PER_LANG[(lang, variant)]
    elif lang in TOPIC_TREE_REPLACMENTS_PER_LANG:
        return TOPIC_TREE_REPLACMENTS_PER_LANG[lang]
    else:
        LOGGER.warning('No replacements found for lang=' + lang + ' variant=' + str(variant))
        return {}
