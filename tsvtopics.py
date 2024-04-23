#!/usr/bin/env python
"""
This script can be used to extract the main menu info from the KA website.
Usage:

    ./tsvtopics.py  --lang=bg
    ./tsvtopics.py  --lang=es --curriculum=mx-eb

"""

import argparse

from tsvkhan import get_khan_tsv
from tsvkhan import TOPIC_LIKE_KINDS
from tsvkhan import DOMAINS_SORT_ORDER


def _recurse_children(node, data, curriculum):
    if "translated_title" not in node:
        node["translated_title"] = node["original_title"]
    if node["kind"] in TOPIC_LIKE_KINDS:
        children = []
        for child in node["children_ids"]:
            if child["id"] in data:
                child = data[child["id"]]
                if child.get("fully_translated", True) and (not curriculum or not child["curriculum_key"] or child["curriculum_key"] == curriculum):
                    if curriculum and child.get("kind") == "Course" and child["curriculum_key"] != curriculum:
                        continue
                    _recurse_children(child, data, curriculum)
                    children.append(child)
        node["children"] = children


def get_ka_learn_menu_topics(lang, curriculum=None):
    """
    Obtain the custom menu from the Khan Academy website for language `lang` and
    `curriculum`, see for example https://es.khanacademy.org/?curriculum=pe-pe .
    """
    data = get_khan_tsv(lang, update=True)

    menu_topics = []
    domains = [row for row in data.values() if row['kind'] == 'Domain']
    domains_by_slug = dict((domain['slug'], domain) for domain in domains)
    for domain_slug in DOMAINS_SORT_ORDER:
        if domain_slug in domains_by_slug:
            domain = domains_by_slug[domain_slug]
            if not curriculum or not domain["curriculum_key"] or domain["curriculum_key"] == curriculum:
                _recurse_children(domain, data, curriculum)
                if domain["children"]:
                    menu_topics.append(domain)

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
            line += '"translatedTitle": "' + top_menu['translated_title'] + '", '
            line += '"children": ['
            print(line)
            for menu in top_menu['children']:
                subline = '        {'
                subline += '"slug": "' + menu['slug'] + '", '
                subline += '"translatedTitle": "' + menu['translated_title'] + '"},'
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
            print(' -', top_menu['translated_title'], 'slug='+top_menu['slug'], 'href='+top_menu['href'])
            for menu in top_menu['children']:
                print('    -', menu['translated_title'], 'slug='+menu['slug'], 'href='+menu['href'])
                if 'children' in menu:
                    print(menu['children'])

    slugs = [tm['slug'] for tm in menu_topics]
    print_curation_topic_tree(menu_topics, slugs=slugs)
    print("\nCopy-paste (the relevant subset) of ^ ^ to TOPIC_TREE_REPLACMENTS_PER_LANG in curation.py")
    print("Topics that are not 'curated' in TOPIC_TREE_REPLACMENTS_PER_LANG")
    print("will maintain their structure and order as obtained the KA API.")
    print("In other words, the topic tree replacements are only needed for exceptional cases,")
    print("usually `math` and `science` when by-grade trees are vailable.")
