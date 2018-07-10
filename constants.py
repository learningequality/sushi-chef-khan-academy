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
    'translatedDescription'
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
    'prerequisites',
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

SUPPORTED_LANGS = ['en', 'es', 'fr', 'hi', 'pt-pt']

V2_API_URL = "http://www.khanacademy.org/api/v2/topics/topictree?lang={lang}&projection={projection}"
KA_LITE_DUBBED_LIST = "https://docs.google.com/spreadsheets/d/1haV0KK8313lG-_Ay2REplQuMquRStZumB3zxmmtYqO0/export?format=csv#gid=1632743521"
ASSESSMENT_URL = "http://www.khanacademy.org/api/v1/assessment_items/{assessment_item}?lang={lang}"
CROWDIN_URL = "https://api.crowdin.com/api/project/khanacademy/download/{lang_code}.zip?key={key}"
