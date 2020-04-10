"""
This file contains special instructions for selection, subsetting, and hoisting
rules for the Khan Academy nodes that are applied as part of the creation of the
corresponding Kolibri channel.
"""


# these topics are not relevant or importable
GLOBAL_SLUG_BLACKLIST = [
    "new-and-noteworthy",
    "talks-and-interviews",
    "coach-res",
    "khan-kids-page",       # link to KA Kids app (skip to avoid empty topic)
    "khan-kids-app-page",   # link to KA Kids app (skip to avoid empty topic)
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


# Empty placeholders from the API; handled in TOPIC_TREE_REPLACMENTS_PER_LANG
GLOBAL_SLUG_BLACKLIST += [
    "k-8-grades",
    "engageny",
    "topic-foundations-engageny",
    "on-grade-engageny",
    "high-school-math",
    #
    "hindi",                # Parallel structure for in-in curriculum in Hindi
    "math-hindi",
    "science-hindi",
    "science-india",
    "in-math-by-grade",
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
        "money-and-banking",    # Mar 25: contains mostly non-public youtube videos
    ],
    "en": [
        # Note: no need for in-in math topics since handled by tree replacement
        "in-in-class9th-physics-india",       # specific to the in-in curriculum
        "in-in-class10th-physics",
        "in-in-class-10-biology",
        "in-in-class-10-chemistry-india",
        "in-in-class11th-physics",
        "in-in-class-12th-physics-india",
        "in-in-class-10-physics-india-hindi",
        "in-in-class-11-physics-cbse-hindi",
        "science-hindi",
        "science-india",
        "class-11-chemistry-india",
        "indiacourse",
        "talent-search",
    ],
    ("en", "in-in"): [],
}

def get_slug_blacklist(lang=None, variant=None):
    """
    Returns a list of KA slugs to skip when creating the channel.
    Combines the "global" slug blacklist that applies for all channels, and 
    additional customization for specific languages or curriculum variants.
    """
    SLUG_BLACKLIST = GLOBAL_SLUG_BLACKLIST
    if lang in SLUG_BLACKLIST_PER_LANG.keys():
        SLUG_BLACKLIST.extend(SLUG_BLACKLIST_PER_LANG[(lang, variant)])
    return SLUG_BLACKLIST


# Topic tree replacments (slug --> list of subtrees of slug includes)
# If a slug is encountered in the tree replacements data for the current channel
# the KhanNode is dropped from the tree and replced by the list of TopicNodes
# which are then populated with children from list of slugs
# e.g. "math" KhanNode gets replaced by "Math by Subject" and "Math by Grade"
#      topic nodes populated with appropriate subsets of the math node.
#
# The keys are either internal lang codes (str) or (lang, variant) tuples (str, str)
TOPIC_TREE_REPLACMENTS_PER_LANG = {
    "en": {
        "math": [
            {"slug": "math", "translatedTitle": "Math", "children": [
                {"slug": "early-math", "translatedTitle": "Early math"},
                {"slug": "arithmetic", "translatedTitle": "Arithmetic"},
                {"slug": "pre-algebra", "translatedTitle": "Pre-algebra"},
                {"slug": "algebra", "translatedTitle": "Algebra 1"},
                {"slug": "geometry", "translatedTitle": "Geometry"},
                {"slug": "algebra2", "translatedTitle": "Algebra 2"},
                {"slug": "trigonometry", "translatedTitle": "Trigonometry"},
                {"slug": "precalculus", "translatedTitle": "Precalculus"},
                {"slug": "statistics-probability", "translatedTitle": "Statistics & probability"},
                {"slug": "ap-calculus-ab", "translatedTitle": "AP®︎ Calculus AB"},
                {"slug": "ap-calculus-bc", "translatedTitle": "AP®︎ Calculus BC"},
                {"slug": "ap-statistics", "translatedTitle": "AP®︎ Statistics"},
                {"slug": "multivariable-calculus", "translatedTitle": "Multivariable calculus"},
                {"slug": "differential-equations", "translatedTitle": "Differential equations"},
                {"slug": "linear-algebra", "translatedTitle": "Linear algebra"},
            ]},
            {"slug": "k-8-grades", "translatedTitle": "Math by grade (USA)", "children": [
                {"slug": "kids", "translatedTitle": "Preschool app"},
                {"slug": "cc-kindergarten-math", "translatedTitle": "Kindergarten"},
                {"slug": "cc-1st-grade-math", "translatedTitle": "1st grade"},
                {"slug": "cc-2nd-grade-math", "translatedTitle": "2nd grade"},
                {"slug": "cc-third-grade-math", "translatedTitle": "3rd grade"},
                {"slug": "cc-fourth-grade-math", "translatedTitle": "4th grade"},
                {"slug": "cc-fifth-grade-math", "translatedTitle": "5th grade"},
                {"slug": "cc-sixth-grade-math", "translatedTitle": "6th grade"},
                {"slug": "cc-seventh-grade-math", "translatedTitle": "7th grade"},
                {"slug": "cc-eighth-grade-math", "translatedTitle": "8th grade"},
                {"slug": "illustrative-math", "translatedTitle": "Illustrative Mathematics", "children": [
                    {"slug": "6th-grade-illustrative-math"},
                    {"slug": "7th-grade-illustrative-math"},
                    {"slug": "8th-grade-illustrative-math"},
                ]},
                {"slug": "engageny", "translatedTitle": "Eureka Math/EngageNY", "children": [
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
                    {"slug": "algebra"},
                    {"slug": "geometry"},
                    {"slug": "algebra2"},
                    {"slug": "probability"},
                    {"slug": "trigonometry"},
                    {"slug": "precalculus"},
                ]},
            ]},
        ]
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
                {"slug": "math-for-fun-and-glory", "translatedTitle": "Math for fun and glory"},
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
            {"slug": "science", "translatedTitle": "Science & engineering", "children": [
                {"slug": "physics", "translatedTitle": "Physics"},
                {"slug": "cosmology-and-astronomy", "translatedTitle": "Cosmology & astronomy"},
                {"slug": "chemistry", "translatedTitle": "Chemistry"},
                {"slug": "organic-chemistry", "translatedTitle": "Organic chemistry"},
                {"slug": "biology", "translatedTitle": "Biology"},
                {"slug": "health-and-medicine", "translatedTitle": "Health & medicine"},
                {"slug": "electrical-engineering", "translatedTitle": "Electrical engineering"},
            ]},
        ],
    }
}

