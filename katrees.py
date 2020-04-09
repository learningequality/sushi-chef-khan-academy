#!/usr/bin/env python
from collections import OrderedDict
from contextlib import redirect_stdout
import io
import json
import os
import requests
import pprint
import subprocess

from constants import TOPIC_ATTRIBUTES, EXERCISE_ATTRIBUTES, VIDEO_ATTRIBUTES

from constants import CROWDIN_LANGUAGE_MAPPING, ASSESSMENT_LANGUAGE_MAPPING, VIDEO_LANGUAGE_MAPPING
from constants import V2_API_URL, PROJECTION_KEYS
from curation import get_slug_blacklist
from khan import _recurse_create, KhanTopic, KhanExercise, KhanVideo


KA_CHEF_DIR = os.path.dirname(__file__)
KHAN_API_CACHE_DIR = os.path.join(KA_CHEF_DIR, "reports", "khanapicache")


def get_khan_api_json(lang, update=False):
    filename = 'khan_academy_json_{}.json'.format(lang)
    filepath = os.path.join(KHAN_API_CACHE_DIR, filename)
    if os.path.exists(filepath) and not update:
        print('Loaded KA API json from cache', filepath)
        data = json.load(open(filepath))
    else:
        print('Downloading KA API json to', filepath)
        url = V2_API_URL.format(lang=lang, projection=PROJECTION_KEYS)
        print('url=', url)
        retry_count = 0
        max_retry = 3
        while retry_count < max_retry:
            try:
                response = requests.get(url)
                data = response.json()
                break
            except json.decoder.JSONDecodeError as e:
                print('Network error retrying', str(retry_count+1)+'/'+str(max_retry), 'HTTP code', response.status_code)
                retry_count += 1
        data = {}
        json.dump(data, open(filepath, 'w'), ensure_ascii=False, indent=4)
    return data


def get_topic_slug_set(data):
    all_topic_slugs = set()
    for topic in data['topics']:
        topic_slug = topic.get("slug", None)
        all_topic_slugs.add(topic_slug)
    return all_topic_slugs



def report_from_raw_data(lang, data, all_en_topic_slugs=set()):
    """
    Basic report on data from API.
    """
    report = {'lang': lang}
    #
    # general counts
    report['#topics'] = len(data['topics'])
    report['#videos'] = len(data['videos'])
    report['#exercises'] = len(data['exercises'])
    #
    # video stats
    translated_videos = []
    untranslated_videos = []
    has_mp4 = []
    has_mp4_low = []
    has_mp4_low_ios = []
    for v in data['videos']:
        vid = v['id']
        if v['translatedYoutubeLang'] != 'en':
            translated_videos.append(vid)
        else:
            untranslated_videos.append(vid)
        durls = v['downloadUrls']
        if 'mp4' in durls:
            has_mp4.append(vid)
        if 'mp4-low' in durls:
            has_mp4_low.append(vid)
        if 'mp4-low-ios' in durls:
            has_mp4_low_ios.append(vid)
    report['#translated_videos'] = len(translated_videos)
    report['#untranslated_videos'] = len(untranslated_videos)
    report['#has_mp4'] = len(has_mp4)
    report['#has_mp4_low'] = len(has_mp4_low)
    report['#has_mp4_low_ios'] = len(has_mp4_low_ios)
    #
    # LTT-related metadata
    en_topic_slugs = []
    ltt_topic_slugs = []
    for topic in data['topics']:
        topic_slug = topic.get("slug", None)
        if topic_slug not in all_en_topic_slugs:
            ltt_topic_slugs.append(topic_slug)
        else:
            en_topic_slugs.append(topic_slug)
    report['#en_topic_slugs'] = len(en_topic_slugs)
    report['#ltt_topic_slugs'] = len(ltt_topic_slugs)

    report['curriculum_keys'] = []
    for topic in data['topics']:
        curriculum = topic.get("curriculumKey", None)
        if curriculum and curriculum not in report['curriculum_keys']:
            report['curriculum_keys'].append(curriculum)
    #
    return report


def get_khan_topic_tree(lang="en", curr_key=None):
    """
    Copied from khan.get_khan_topic_tree --- adapted to use caching API results.
    """
    print('Building topic tree for lang=', lang)
    topic_tree = get_khan_api_json(lang)
    # Flatten node_data
    flattened_tree = [node for node_list in topic_tree.values() for node in node_list]
    # convert to dict with ids as keys
    tree_dict = {node["id"]: node for node in flattened_tree}
    return _recurse_create(tree_dict["x00000000"], tree_dict, lang=lang)


def print_subtree(subtree, level=0, SLUG_BLACKLIST=[], all_en_topic_slugs=[]):
    if subtree.slug in SLUG_BLACKLIST:
        return
    if level == 4:
        return
    extra = ''
    if subtree.curriculum:
        extra = 'CURRICULUM='+ subtree.curriculum
        if level > 2:
            raise ValueError('Unexpected curriculum annotation found at level = ' + str(level))
    isbold = '**' if subtree.slug not in all_en_topic_slugs else ''
    print(' '*2*level + '   -', isbold+subtree.title.strip(), '(' + subtree.id + ')'+isbold, extra)
    for child in subtree.children:
        if isinstance(child, KhanTopic):
            print_subtree(child, level=level+1, SLUG_BLACKLIST=SLUG_BLACKLIST, all_en_topic_slugs=all_en_topic_slugs)


def export_khantree(lang, khantree, report, variant=None, all_en_topic_slugs=[]):
    SLUG_BLACKLIST = get_slug_blacklist(lang=lang)
    basedir = os.path.join(KA_CHEF_DIR, "reports", "khantrees")
    path_md = os.path.join(basedir, 'khan_academy_{}_tree.md'.format(lang))
    path_html = os.path.join(basedir, 'khan_academy_{}_tree.html'.format(lang))
    
    with io.StringIO() as buf, redirect_stdout(buf):

        print('# Khan Academy Content for language code', lang)

        print('## Stats')
        for key, value in report.items():
            print('  - ', key, ':', value)

        print('## Tree')
        print('\nEntries shown in **bold** represent topics that are not present in the KA English tree.')
        print_subtree(khantree, SLUG_BLACKLIST=SLUG_BLACKLIST, all_en_topic_slugs=all_en_topic_slugs)
        output_md = buf.getvalue()

        with open(path_md, 'w') as mdfile:
            mdfile.write(output_md)

    subprocess.call(['pandoc', '--from', 'gfm', path_md, '-o', path_html])
    print('Saved', path_html)
    os.remove(path_md)


def get_ka_learn_menu_topics(lang, curriculum=None):
    post_data = {
        "operationName": "learnMenuTopicsQuery",
        "variables": {},
        "query":"query learnMenuTopicsQuery($curriculum: String) {\n  learnMenuTopics(curriculum: $curriculum) {\n    slug\n    translatedTitle\n    href\n    children {\n      slug\n      translatedTitle\n      href\n      loggedOutHref\n      nonContentLink\n      __typename\n    }\n    __typename\n  }\n}\n"
    }
    if curriculum:
        post_data["variables"]["curriculum"] = curriculum

    url = 'https://www.khanacademy.org/api/internal/graphql/learnMenuTopicsQuery'
    url += '?lang=' + lang
    response = requests.post(url, json=post_data)
    response_data = response.json()
    menu_topics = response_data['data']['learnMenuTopics']
    for top_menu in menu_topics:
        del top_menu['__typename']
        top_menu['slug'] = top_menu['href'].split('/')[-1]
        for menu in top_menu['children']:
            del menu['loggedOutHref']
            del menu['nonContentLink']
            del menu['__typename']
            menu['slug'] = menu['href'].split('/')[-1]
    return menu_topics


if __name__ == '__main__':
    ka_info_path = os.path.join(KA_CHEF_DIR, "reports", "ka_channels_info.json")
    khan_channels_info = json.load(open(ka_info_path))

    # first get en tree so we can diff against it to know the LTT slugs
    endata = get_khan_api_json('en', update=False)
    all_en_topic_slugs = get_topic_slug_set(endata)

    for khan_channel in khan_channels_info:
        lang = khan_channel['language']
        data = get_khan_api_json(lang, update=False)
        report = report_from_raw_data(lang, data, all_en_topic_slugs=all_en_topic_slugs)
        khantree = get_khan_topic_tree(lang)
        export_khantree(lang, khantree, report, variant=None, all_en_topic_slugs=all_en_topic_slugs)
