#!/usr/bin/env python
"""
Helpers for getting, parsing, printing, and archiving Khan Academy topic trees.

    ./katrees.py --lang fr   # see ./chefdata/khanapitrees/khan_api_tree_fr.json

or
    ./katrees.py --lang fr  --print         # prints tree in terminal
    ./katrees.py --lang fr  --htmlexport    # expots tree as an HTML file

"""
import argparse
from contextlib import redirect_stdout
import copy
import io
import json
import os
import subprocess

from khan import get_khan_api_json, report_from_raw_data
from khan import get_khan_topic_tree, get_kind, print_subtree

KHAN_JSON_TREE_DIR = os.path.join('chefdata', 'khanapitrees')



# JSON EXPORTS
################################################################################

def subtree_to_dict(subtree, SLUG_BLACKLIST=[]):
    """
    Convert the tree of `KhanNode` objects to a tree of JSON-serializbale dicts.
    """
    node_data = subtree.__dict__
    node_data['kind'] = get_kind(subtree)
    if 'children' in node_data:
        children = node_data.pop('children')
        node_data['children'] = []
        for child in children:
            child_data = subtree_to_dict(child, SLUG_BLACKLIST=SLUG_BLACKLIST)
            node_data['children'].append(child_data)
    return node_data


def save_parsed_khan_topic_tree(ka_root_topic, lang):
    """
    Export the parsed topic tree of `KhanNode`s as JSON for archival and diffs.
    """
    KHAN_JSON_TREE_DIR = os.path.join('chefdata', 'khanapitrees')
    filename = "khan_api_tree_{lang}.json".format(lang=lang)
    ka_root_topic = copy.deepcopy(ka_root_topic)
    khan_topic_tree = subtree_to_dict(ka_root_topic)
    if not os.path.exists(KHAN_JSON_TREE_DIR):
        os.makedirs(KHAN_JSON_TREE_DIR, exist_ok=True)
    jsonpath = os.path.join(KHAN_JSON_TREE_DIR, filename)
    with open(jsonpath, 'w') as jsonf:
        json.dump(khan_topic_tree, jsonf, indent=2, ensure_ascii=False)
    print('Saved topic tree JSON to', jsonpath)



# HTML EXPORTS
################################################################################

def export_khantree_as_html(lang, khantree, report, maxlevel=7, SLUG_BLACKLIST=[]):
    """
    Export `khantree` as HTML for manual debugging and inspection of contents.
    """
    basedir = os.path.join("exports", "khanhtmltrees")
    if not os.path.exists(basedir):
        os.makedirs(basedir, exist_ok=True)
    path_md = os.path.join(basedir, 'khan_academy_{}_tree.md'.format(lang))
    path_html = os.path.join(basedir, 'khan_academy_{}_tree.html'.format(lang))

    with io.StringIO() as buf, redirect_stdout(buf):
        print('# Khan Academy Content for language code', lang)
        print('## Summary')
        for key, value in report.items():
            print('  - ', key, ':', value)

        print('## Topic tree')
        print_subtree(khantree, maxlevel=maxlevel, SLUG_BLACKLIST=SLUG_BLACKLIST)
        output_md = buf.getvalue()

        with open(path_md, 'w') as mdfile:
            mdfile.write(output_md)

    subprocess.call(['pandoc', '--from', 'gfm', path_md, '-o', path_html])
    print('Saved', path_html)
    os.remove(path_md)


# CLI
################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KA topic tree archiver')
    parser.add_argument('--lang', required=True, help="language code")
    parser.add_argument('--htmlexport', action='store_true', help='save topic tree as html')
    parser.add_argument('--htmlmaxlevel', type=int, default=7, help='html tree depth')
    parser.add_argument('--print', action='store_true', help='print topic tree')
    parser.add_argument('--printmaxlevel', type=int, default=2, help='print tree depth')
    args = parser.parse_args()

    print('Getting KA topic tree from API v2 for lang', args.lang)
    ka_root_topic, _ = get_khan_topic_tree(lang=args.lang, update=False)

    # json export of parsed tree of `KhanNode`s
    save_parsed_khan_topic_tree(ka_root_topic, args.lang)

    if args.htmlexport:
        ka_data = get_khan_api_json(args.lang)
        report = report_from_raw_data(args.lang, ka_data)
        export_khantree_as_html(args.lang, ka_root_topic, report, maxlevel=args.htmlmaxlevel)

    if args.print:
        print_subtree(ka_root_topic, maxlevel=args.printmaxlevel)

