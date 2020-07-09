#!/usr/bin/env python
"""
This script can be used to extract the main menu info from the KA website.
Usage:

    ./graphql.py  --lang=bg
    ./graphql.py  --lang=es --curriculum=mx-eb

"""

import argparse
import requests


# KA WEBSITE GRAPHQL HACKS
################################################################################

def get_ka_learn_menu_topics(lang, curriculum=None):
    """
    Obtain the custom menu from the Khan Academy website for language `lang` and
    `curriculum`, see for example https://es.khanacademy.org/?curriculum=pe-pe .
    """
    post_data = {
        "operationName": "learnMenuTopicsQuery",
        "variables": {},
        "query":"query learnMenuTopicsQuery($curriculum: String) {\n  learnMenuTopics(curriculum: $curriculum) {\n    slug\n    translatedTitle\n    href\n    children {\n      slug\n      translatedTitle\n      href\n      loggedOutHref\n      nonContentLink\n      __typename\n    }\n    __typename\n  }\n}\n"
    }
    if curriculum:
        post_data["variables"]["curriculum"] = curriculum

    url = 'https://www.khanacademy.org/api/internal/graphql/learnMenuTopicsQuery'
    url += '?lang=' + lang
    print('Sending POST', url)
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


def print_curation_topic_tree(menu_topics, slugs=[]):
    """
    Print the `menu_topics` obtained from `get_ka_learn_menu_topics` in the form
    of a dict tree structure suitable for inclusion in `curaiton.py`.
    The output of the function can be added to `TOPIC_TREE_REPLACMENTS_PER_LANG`
    in `curation.py` to obtain restructuring operations of the KA API results to
    make the Kolibri channel topic tree look like the KA website.
    """
    print('[')
    for top_menu in menu_topics:
        if top_menu['slug'] in slugs:
            line = '    {'
            line += '"slug": "' + top_menu['slug'] + '", '
            line += '"translatedTitle": "' + top_menu['translatedTitle'] + '", '
            line += '"children": ['
            print(line)
            for menu in top_menu['children']:
                subline = '        {'
                subline += '"slug": "' + menu['slug'] + '", '
                subline += '"translatedTitle": "' + menu['translatedTitle'] + '"},'
                print(subline)
            print('    ]},')
    print(']')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KA GraphQL main manu export.')
    parser.add_argument('--lang', required=True, help="language code")
    parser.add_argument('--curriculum', default=None, help="curriculum key")
    parser.add_argument('--printmd', action='store_true', help='print menu tree as md')
    args = parser.parse_args()

    menu_topics = get_ka_learn_menu_topics(args.lang, curriculum=args.curriculum)

    print("Menu for lang", args.lang, 'and curriculum', args.curriculum, 'is:')
    if args.printmd:
        for top_menu in menu_topics:
            print(' -', top_menu['translatedTitle'], 'slug='+top_menu['slug'], 'href='+top_menu['href'])
            for menu in top_menu['children']:
                print('    -', menu['translatedTitle'], 'slug='+menu['slug'], 'href='+menu['href'])
                if 'children' in menu:
                    print(menu['children'])

    slugs = [tm['slug'] for tm in menu_topics]
    print_curation_topic_tree(menu_topics, slugs=slugs)
    print("\nCopy-paste (the relevant subset) of ^ ^ to TOPIC_TREE_REPLACMENTS_PER_LANG in curation.py")
    print("Topics that are not 'curated' in TOPIC_TREE_REPLACMENTS_PER_LANG")
    print("will maintain their structure and order as obtained the KA API.")
    print("In other words, the topic tree replacements are only needed for exceptional cases,")
    print("usually `math` and `science` when by-grade trees are vailable.")
