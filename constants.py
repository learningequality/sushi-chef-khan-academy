import json
from collections import OrderedDict

from le_utils.constants.languages import getlang

TOPIC_ATTRIBUTES = [
    'childData',
    'deleted',
    'doNotPublish',
    'hide',
    'id',
    'kind',
    'slug',
    'translatedTitle',
    'translatedDescription',
    'curriculumKey'
]

EXERCISE_ATTRIBUTES = [
    'allAssessmentItems',
    'displayName',
    'fileName',
    'id',
    'kind',
    'name',
    'prerequisites',
    'slug',
    'usesAssessmentItems',
    'relatedContent',
    'translatedTitle',
    'translatedDescription',
    'suggestedCompletionCriteria',
    'kaUrl',
    'imageUrl'
]

VIDEO_ATTRIBUTES = [
    'id',
    'kind',
    'licenseName',
    'slug',
    'youtubeId',
    'translatedYoutubeLang',
    'translatedYoutubeId',
    'translatedTitle',
    'translatedDescription',
    'translatedDescriptionHtml',
    'downloadUrls',
    'imageUrl'
]
# Note (May 2020): we also want `sourceLanguage` but not avail. thorugh /api/v2/

# ARTICLE_ATTRIBUTES = [
#     'id',
#     'kind',
#     'slug',
#     'descriptionHtml',
#     'perseusContent',
#     'title',
#     'imageUrl'
# ]

PROJECTION_KEYS = json.dumps(OrderedDict([
    ("topics", [OrderedDict((key, 1) for key in TOPIC_ATTRIBUTES)]),
    ("exercises", [OrderedDict((key, 1) for key in EXERCISE_ATTRIBUTES)]),
    ("videos", [OrderedDict((key, 1) for key in VIDEO_ATTRIBUTES)]),
    # ("articles", [OrderedDict((key, 1) for key in ARTICLE_ATTRIBUTES)])
]))



SUPPORTED_LANGS = ['en', 'es', 'fr', 'hi', 'pt-PT', 'pt-BR', 'hy', 'ko', 'und', 'bn', 'gu', 'id']

# UNSUPPORTED_LANGS = ['ru', 'zu', 'my', 'fv', 'ur']
# These KA channels are not fully supported on the KA website, but content
# may be available as YouTube playlists and CrowdIn translations

# UNSUBTITLED_LANGS = ['es', 'fr', 'hi', 'pt-PT', 'pt-BR', 'hy', 'bn', 'id']
# Deprecated: previously we were skipping the download of subtitles for these
# KA channels because most of the videos are translated/dubbed. But we decided
# that it's better to include subtitles when available even videos are dubbed.

V2_API_URL = "http://www.khanacademy.org/api/v2/topics/topictree?lang={lang}&projection={projection}"
KA_LITE_DUBBED_LIST = "https://docs.google.com/spreadsheets/d/1haV0KK8313lG-_Ay2REplQuMquRStZumB3zxmmtYqO0/export?format=csv#gid=1632743521"
ASSESSMENT_URL = "http://www.khanacademy.org/api/v1/assessment_items/{assessment_item}?lang={lang}"
CROWDIN_URL = "https://api.crowdin.com/api/project/khanacademy/download/{lang_code}.zip?key={key}"
COMMON_CORE_SPREADSHEET = "https://storage.googleapis.com/ka_uploads/share/Common_Core_Spreadsheet.csv"


CHANNEL_TITLE_LOOKUP = {
    ("en", "us-cc"): "Khan Academy (English - US curriculum)",
    ("en", "in-in"): "Khan Academy (English - CBSE India Curriculum)",
    "pt-BR": "Khan Academy (Português - Brasil)",
}

def get_channel_title(lang=None, variant=None):
    """
    Return KA channel title for le-utils code `lang` and variant `variant`.
    """
    if variant and (lang, variant) in CHANNEL_TITLE_LOOKUP:
        return CHANNEL_TITLE_LOOKUP[(lang, variant)]
    elif lang in CHANNEL_TITLE_LOOKUP:
        return CHANNEL_TITLE_LOOKUP[lang]
    else:
        lang_obj = getlang(lang)
        title = "Khan Academy ({})".format(lang_obj.first_native_name)
        return title


CHANNEL_DESCRIPTION_LOOKUP = {
    "en": "Khan Academy provides videos and exercises on math, physics, chemistry, biology, and history, aligned to U.S. and India curricular standards. Each topic is covered through intuitive video explanations and provides numerous practice exercises to help students achieve mastery of the subjects. Appropriate for middle and secondary students, as well as adult learners.",
    ("en", "us-cc"): "Khan Academy provides videos and exercises on math, physics, chemistry, biology, and history, aligned to the U.S. curriculum. Each topic is covered through intuitive video explanations and provides numerous practice exercises to help students achieve mastery of the subjects. Appropriate for middle and secondary students, as well as adult learners.",
    ("en", "in-in"): "Khan Academy provides videos and exercises on math, physics, chemistry, biology, and history, aligned to the CBSE India curriculum. Each topic is covered through intuitive video explanations and provides numerous practice exercises to help students achieve mastery of the subjects. Appropriate for middle and secondary students, as well as adult learners.",
    "fr": "Khan Academy propose des vidéos et des exercices sur les maths, la physique, la chimie, la biologie et l'histoire. Chaque sujet est couvert par des explications vidéo intuitives et comprend de nombreux exercices de pratique pour aider les étudiants à maîtriser les sujets. Convient aux élèves des niveaux primaire et secondaire ainsi qu'aux adultes.",
    "es": "Khan Academy ofrece videos y ejercicios sobre matemáticas, ciencias, y finanzas para estudiantes de nivel medio y secundario, así para los adultos. También se encuentran los materiales de Khan Academy Perú, los cuales están alineados al Currículo Nacional de Educación Básica, así como materiales preparatorios para la educación superior, y también Khan Academy México, enfocado en matemáticas.",
    "pt-BR": "Khan Academy oferece cursos em matemática, física, química, biologia e história. Cada matéria contém vídeos explicativos e exercícios para para a prática e revisão. Próprio para alunos do ensino médio e secundário, bem como para adultos.",
    "pt-PT": "Khan Academy oferece cursos em matemática, física, química e biologia. Cada matéria contém vídeos explicativos e exercícios para para a prática e revisão. Próprio para alunos do ensino médio e secundário, bem como para adultos.",
    "zh-CN": "可汗学院提供与美国课程一致的视频和习题，涵盖数学、物理、化学、生物和历史。每一个主题都包括了直观的视频解释和大量的练习题目以帮助学生掌握这些学科。这些内容适合初中生、高中生和成年人学习。",
    "it": "Khan Academy offre i video e gli esercizi di matematica, allineati al curriculum degli Stati Uniti. Ogni argomento è trattato in modo intuitivo attraverso spiegazioni video, e fornisce numerosi esercizi pratici per aiutare gli studenti raggiungere la competenza sulla materia. Adatto agli studenti di scuola elementare, media e secondaria, nonché agli adulti.",
    "bn": "খান একাডেমিতে বাংলাদেশের শিক্ষাক্রম অনুযায়ী গণিতের ভিডিও এবং অনুশীলনী রয়েছে। প্রতিটি অধ্যায়ে বিষয়ভিত্তিক মূল ধারণার ভিডিও এবং অসংখ্য অনুশীলনী রয়েছে যা নিয়মিত চর্চার মাধ্যমে শিক্ষার্থীরা ঐ বিষয়ে দক্ষতা অর্জন করতে পারে। প্রাথমিক ও মাধ্যমিক শিক্ষার্থীদের জন্য উপযোগী, সেইসাথে বয়স্ক শিক্ষার্থীরাও এটি ব্যবহার করতে পারবে।",
    "bg": "Khan Academy предоставя видео уроци и упражнения по математика, физика, химия и биология, съобразени с българските учебни стандарти. Темите са представени чрез лесно разбираеми обяснения и многобройни упражнения за самооценка на наученото. Материалите са подходящи както за ученици от началните и стредните класове, така и за студенти.",
    "hi": "खान अकादमी वीडियो और अभ्यास के माध्यम से हर शिक्षक को गणित का ज्ञान देती हैं। ये वीडियो वास्तविक जीवन अनुप्रयोगों के साथ अवधारणाओं की व्याख्या करते हैं।"
}


def get_channel_description(lang=None, variant=None):
    """
    Find KA channel description for le-utils code `lang` and variant `variant`.
    """
    if variant and (lang, variant) in CHANNEL_DESCRIPTION_LOOKUP:
        return CHANNEL_DESCRIPTION_LOOKUP[(lang, variant)]
    elif lang in CHANNEL_DESCRIPTION_LOOKUP:
        return CHANNEL_DESCRIPTION_LOOKUP[lang]
    else:
        lang_obj = getlang(lang)
        description = "Khan Academy content for {}.".format(lang_obj.name)
        return description


# map from le-utils language codes to language codes used on CROWDIN
CROWDIN_LANGUAGE_MAPPING = {
    "fuv": "fv",            # Fulfulde Mbororo (note different from ful and ff)
}

# map  to codes used to get assesment items from the KA API
ASSESSMENT_LANGUAGE_MAPPING = {
    "fuv": "fv",            # Fulfulde Mbororo (note different from ful and ff)
}

# map from le-utils codes to language codes for video nodes translated_  from youtube do not have the same language code as le-utils
VIDEO_LANGUAGE_MAPPING = {
    "fuv": "fv",            # Fulfulde Mbororo (note different from ful and ff)
    "pt-BR": "pt",
    "zh-CN": "zh-hans"
}


# Videos with misleading translatedYoutubeLang organized by le-utils lang code.
# Use this list to override the should-be-included logic and include the videos.
# TODO: read the `sourceLanguage` property from the future KA API insead of list
DUBBED_VIDEOS_BY_LANG = {
    'pt-BR': [
        'UnPpFw3natI', 'LYUmHD__MRg', 'N8qRX_7po9U', 'VjhbocJYyOI', 'awyS59G8uZA',
        'DfBjGvdUMVM', '39m4SSfP2Y0', 'rsoMED7zHME', 'fFRvZI0K4wQ', 'mO4senTBFbc',
        'uikYPJw0tnE', '50q4iKwnLe8', 'R--9PJ355jY', 'CPhXo-7Qilk', 'TSZ4H5Hd9-M',
        'VdIlzUigamE', 'dGZTQxyfwPI', '9HZz32sBAvA', 'pliaCSX-B4I', 'NSZ8oGkfO14',
        '5rkJ4Ve_2gc', 'iheXqmtLhts', 'WzHBBfxl6zo', '19G_f9oHIeg', 'Bvq4pfmP03s',
        '7sp1--UsVoY', 'eviU0iRKcck', 'v_joLaJ-cfM', 'kfikcE4eJMI', '9_o8Lw9BU_U',
        'N0IO9b-xnzc', 'GCTea37THw0', 'FllpnWMCeCw', 'seR3m7RNRRA', 'QM13R2YhyD0',
        'P4n36FnlQ18', '5j7QWssTZTM', 'C7Uw4g8GCkU', 'Y3qLdwRY5RY', 'rp1E8idtvJY',
        'bDxYr6LWL5A', 'v1RBFkoLD0w', 'L2Z-1EeXAjo', 'x5j19Dd5jWU', 'OLkz5WfQHG4',
        'cQT8ZZAbrow', 'XCaw6TxgLoQ', 'Z7nh2e5dVYE', 'eQNhW0t_R-k', 'q1-7lYXirHs',
        '296y0W2lu4w', '3dOVJCtN1kE', 'Qne5wRW20VA', 'dTsUyXXudvA', 'Iya-2bS14ho',
        'bm65xCS5ivo', 'oW8Ts9N5E-o', 'ENc3fmAQG5Q', 'a4o-3vvTOkU', 'o9e7U1IQ7Ek',
        '1jJBfzVQ-qQ', 'jnyOVKseNNw', 'Z3xs9saGdTQ', 'sSNu75F5JeQ', 'TXHr1h356Ps',
        'BWjWEDvTB7g', 'B8HhdnIhAVg', 'wXQ3vPrKer0', 'XZ9Zw9_cTII', 'r2mm0vTjD3k',
        'B-vlVXbS_4Y', 'Qz2-5pi1PcM', '0uPgRLUAiuU', 'J8Pvc6JB5ts', 'W6w5S-bAmwM',
        'yRh_Pah7AHo', 'qlGjA9p1UAM', '36Xv2JyPyqA', 'OKc64ezg1uU', 'vPj9S6XsLUM',
        'AmUiEjPEaiM', 'lrnXQXCLpAQ', 'Qite1chTX2s', 'ngQ_luLpeWI', 'BnxcORk2tLc',
        'X4MaFYJUYYk', 'e3H_nqrPuUQ', 'kTgKXsA_klo', 'g6NEzuwZ-0Q', 'FqxyxAq4OMU',
        'Z4sirIWw3Lk', '7AQ3rUb3gWg', 'gYHUrpmB-L4', 'h1bG6zy8ENY', '5MOn8X-tyFw',
        '7JuoW8Pz7gU', 'qtbb4YBJbJM', '2HZKYXXyHJQ', '8BBcQ67myf0', 'NUG1JzxL7jw',
        'e7Cf9eepOTQ', 'o4bXSA7vrd8', 'bsIzwvKHZPc', 'xx8w1WStqpg', 'Om5nvig9Ahs',
        'tO6UMCo8LVU', '4YB_zVM23XA', 'lZiEcMJaw5c', 'oJ4PhVSkEzg', 'LnA0NhBB7pk',
        '50f8X_52O-E', 'YXL6IFa1TJg', 'DJVJQAgXsGg', '2B4A4kigi4Q', 'kXSyFWk_0T4',
        'oeAvj4P6S8o', 'EOPbuL73G4s', 'T2hO0qO3qLc', '-J41zkn-HlU', 'l4oStl_JYlU',
        'U5vAO_f2LDQ', '9REQTbtrwpc', 'm0tdMIz_UHA', 'Qd2n_vZdXuA', 'Z5GoBku8hUo',
        'MyEFnkuxViU', 'eRN2gy-Je18', 'c2-kabi2_ao', 'FS3FSxG_Am0', 'h2NKJK8wjU0',
        'KpK5GVXtF8g', 'YhzH8iVMHl0', '1XlW-7WdHfA', '1U6Aqc0U3OM', 'GMLP5jOnqAI',
        'tYP_e2IitEA', 'JVOU_sh0qpA', 'z7hVq6OdwOg', 'BTudzgYleUI', 'CYJ5sq8AZFI',
        'JeuaB4iryqU', 'H51OAPifRiw', 'TPqE9qP7aHU', 'J2reLNBqoK0', 'HkZ7y05ycEo',
        '_1RUYZ8Ic0E', '1l2yttNDYtc', '402Irx3SMRc',
    ]
}
# To add to this list, look for ERROR message in the logs after a complete chef
# like "Untranslated video {youtube_id} and no subs available. Skipping." and
# add the `{youtube_id}` to the above list if the video is actually transalted.
