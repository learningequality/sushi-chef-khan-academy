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



KHAN_JSON_TREE_DIR = None
KHAN_HTMLEXPORT_TREE_DIR = None





# JSON TREE EXPORTS
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
    basedir = KHAN_HTMLEXPORT_TREE_DIR
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



# TREE PRINTING
################################################################################

def get_stats(subtree):
    """
    Recusively compute kind-counts and total file_size (non-deduplicated).
    """
    kind = get_kind(subtree)
    if kind == 'topic':
        stats = {'topic': 1, 'video':0, 'exercise':0, 'article':0}
        for child in subtree.children:
            child_stats = get_stats(child)
            for k, v in child_stats.items():
                stats[k] += v
        return stats
    else:
        return {kind: 1}

def stats_to_str(stats):
    stats_items = []
    for key in ['topic', 'video', 'exercise']:  # TODO: add 'article' when impl.
        if key in stats and stats[key]:
            stats_items.append(str(stats[key]) + ' ' + key + 's')
    stats_str = ' ' + ', '.join(stats_items)
    return stats_str


def print_subtree(subtree, level=0, maxlevel=2, SLUG_BLACKLIST=[], printstats=True):
    if hasattr(subtree, 'slug') and subtree.slug in SLUG_BLACKLIST:
        return
    if level >= maxlevel:
        return
    extras = []
    if hasattr(subtree, 'curriculum') and subtree.curriculum:
        extras.append('CURRICULUM=' + subtree.curriculum)
        if level > 2:
            raise ValueError('Unexpected curriculum annotation found at level = ' + str(level))
    if hasattr(subtree, 'listed') and not subtree.listed:
        extras.append('listed=' + str(subtree.listed))
    if printstats:
        stats = get_stats(subtree)
        extras.append(stats_to_str(stats))
    extra = ' ' + ', '.join(extras)
    print(' '*2*level + '   -', subtree.title.strip(),
        '[' + get_kind(subtree) + ']',
        '(' + subtree.id + ')', extra)
    if hasattr(subtree, 'children'):
        for child in subtree.children:
            print_subtree(child, level=level+1, maxlevel=maxlevel, SLUG_BLACKLIST=SLUG_BLACKLIST, printstats=printstats)



# CLI
################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KA topic tree archiver')
    parser.add_argument('--lang', required=True, help="language code")
    parser.add_argument('--htmlexport', action='store_true', help='save topic tree as html')
    parser.add_argument('--htmlmaxlevel', type=int, default=7, help='html tree depth')
    parser.add_argument('--print', action='store_true', help='print topic tree')
    parser.add_argument('--printmaxlevel', type=int, default=2, help='print tree depth')
    parser.add_argument('--oldapi', action='store_true', help='use the old API v2')
    parser.add_argument('--showunlisted', action='store_true', help='show unlisted nodes')
    args = parser.parse_args()

    # Normally build tree using only `listed=True` nodes, which corresponds to
    # setting onlylisted=True. If want to see unlisted, we set onlylisted=False.
    onlylisted = not args.showunlisted

    if args.oldapi:
        # OLD JSON API v2
        from khan import get_khan_api_json, report_from_raw_data
        from khan import get_khan_topic_tree, get_kind
        KHAN_JSON_TREE_DIR = os.path.join('chefdata', 'oldkhanapitrees')
        KHAN_HTMLEXPORT_TREE_DIR = os.path.join("exports", "oldkhanhtmltrees")
        print('Getting KA topic tree for lang', args.lang)
        ka_root_topic, _ = get_khan_topic_tree(lang=args.lang, update=False)
        # json export of parsed tree of `KhanNode`s
        save_parsed_khan_topic_tree(ka_root_topic, args.lang)
        ka_data = get_khan_api_json(args.lang)

    else:
        # NEW TSV API
        from tsvkhan import get_khan_tsv
        from tsvkhan import report_from_raw_data
        from tsvkhan import get_khan_topic_tree, get_kind
        KHAN_JSON_TREE_DIR = os.path.join('chefdata', 'khanapitrees')
        KHAN_HTMLEXPORT_TREE_DIR = os.path.join("exports", "khanhtmltrees")
        print('Getting KA topic tree for lang', args.lang)
        ka_root_topic, _ = get_khan_topic_tree(lang=args.lang, update=False, onlylisted=onlylisted)
        # json export of parsed tree of `KhanNode`s
        save_parsed_khan_topic_tree(ka_root_topic, args.lang)
        ka_data = get_khan_tsv(args.lang)

    # HTML TREE EXPORT
    if args.htmlexport:
        report = report_from_raw_data(args.lang, ka_data)
        export_khantree_as_html(args.lang, ka_root_topic, report, maxlevel=args.htmlmaxlevel)

    # PRINT IN TERMINCAL
    if args.print:
        print_subtree(ka_root_topic, maxlevel=args.printmaxlevel)
