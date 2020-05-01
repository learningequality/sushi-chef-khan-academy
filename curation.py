"""
This file contains special instructions for selection, subsetting, and hoisting
rules for the Khan Academy nodes that are applied as part of the creation of the
corresponding Kolibri channel.
"""
from ricecooker.config import LOGGER

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
    "pixar",
    "pixar-latam",
    "wi-phi",  # see https://wi-phi.com/videos/ could not find info on licensing
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
    #
    "brazil-math-grades",  # Special empty topics in pt-BR topic tree
    "ciencias-por-ano",
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
        # Note: no need to list in math topics since handled by tree replacement
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
            {"slug": "science", "translatedTitle": "Физика (България)", "children": [
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
