import json
from collections import OrderedDict

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

UNSUBTITLED_LANGS = ['es', 'fr', 'hi', 'pt-PT', 'pt-BR', 'hy', 'bn', 'id']

V2_API_URL = "http://www.khanacademy.org/api/v2/topics/topictree?lang={lang}&projection={projection}"
KA_LITE_DUBBED_LIST = "https://docs.google.com/spreadsheets/d/1haV0KK8313lG-_Ay2REplQuMquRStZumB3zxmmtYqO0/export?format=csv#gid=1632743521"
ASSESSMENT_URL = "http://www.khanacademy.org/api/v1/assessment_items/{assessment_item}?lang={lang}"
CROWDIN_URL = "https://api.crowdin.com/api/project/khanacademy/download/{lang_code}.zip?key={key}"
COMMON_CORE_SPREADSHEET = "https://storage.googleapis.com/ka_uploads/share/Common_Core_Spreadsheet.csv"

CHANNEL_DESCRIPTION_LOOKUP = {
    "en": "Khan Academy provides videos and exercises on math, physics, chemistry, biology, and history, aligned to the U.S. curriculum. Each topic is covered through intuitive video explanations and provides numerous practice exercises to help students achieve mastery of the subjects. Appropriate for middle and secondary students, as well as adult learners.",
    "fr": "Khan Academy propose des vidéos et des exercices sur les maths, la physique, la chimie, la biologie et l'histoire. Chaque sujet est couvert par des explications vidéo intuitives et comprend de nombreux exercices de pratique pour aider les étudiants à maîtriser les sujets. Convient aux élèves des niveaux primaire et secondaire ainsi qu'aux adultes.",
    "es": "Khan Academy ofrece videos y ejercicios sobre temas de matemáticas, física, química, biología y historia. Cada tema contiene videos explicativos y ejercicios para practicar y revisar. Apropiado para estudiantes de nivel medio y secundario, así para los adultos.",
    "pt-BR": "Khan Academy oferece cursos em matemática, física, química, biologia e história. Cada matéria contém vídeos explicativos e exercícios para para a prática e revisão. Próprio para alunos do ensino médio e secundário, bem como para adultos.",
    "pt-PT": "Khan Academy oferece cursos em matemática, física, química e biologia. Cada matéria contém vídeos explicativos e exercícios para para a prática e revisão. Próprio para alunos do ensino médio e secundário, bem como para adultos.",
}

CROWDIN_LANGUAGE_MAPPING = {
    "fuv": "fv"
}

ASSESSMENT_LANGUAGE_MAPPING = {
    "fuv": "fv"
}

# sometimes videos from youtube do not have the same language code as le-utils
VIDEO_LANGUAGE_MAPPING = {
    "pt-BR": "pt",
    "zh-CN": "zh-hans"
}
