#!/usr/bin/env python
"""
This file needs to be place in the root of the git repo for the Khan Academy chef:
https://github.com/learningequality/sushi-chef-khan-academy


Install treediff lib:

    pip install treediffer

Run these commands to generate KhanNode json trees:

    ./katrees.py  --oldapi --lang fr            # generate tree from old v2 API
    ./katrees.py  --lang fr                     # generate tree from new TSV exports

then run 

    ./tsvdiffs.py  --lang fr

to generate the detailed tree diff to the file `khan_academy_tree_diff_fr.json`
and print the diff including nodes deleted, added, moved, and modified.
"""

import argparse
from contextlib import redirect_stdout
import copy
import io
import json
import os
import subprocess
from treediffer import treediff
from treediffer.diffutils import print_diff
import pprint


OLD_TREES_DIR = os.path.join("chefdata", "oldkhanapitrees")
NEW_TREES_DIR = os.path.join("chefdata", "khanapitrees")
TREE_FILENAME_TPL = 'khan_api_tree_{lang}.json'


def get_trees(lang):
    pathA = os.path.join(OLD_TREES_DIR, TREE_FILENAME_TPL.format(lang=lang))
    treeA = json.load(open(pathA))
    pathB = os.path.join(NEW_TREES_DIR, TREE_FILENAME_TPL.format(lang=lang))
    treeB = json.load(open(pathB))
    return treeA, treeB


def listify_assessment_items(subtree):
    if 'assessment_items' in subtree:
        new_assessment_items = []
        for ai in subtree['assessment_items']:
            new_assessment_items.append(ai["id"])
        subtree['assessment_items'] = new_assessment_items
    if 'children' in subtree:
        for child in subtree['children']:
            listify_assessment_items(child)

def de_ariclefy(subtree):
    if 'children' in subtree:
        new_children = []
        for child in subtree['children']:
            if child['kind'] == 'article':
                pass
            else:
                new_children.append(child)
                if 'children' in child:
                    de_ariclefy(child)
        subtree['children'] = new_children


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KA topic tree differ')
    parser.add_argument('--lang', required=True, help="language code")
    args = parser.parse_args()

    treeA, treeB = get_trees(args.lang)
    print('loaded old tree with ', len(treeA), 'level 1 topics (KA domains)')
    print('loaded new tree with ', len(treeB), 'level 1 topics (KA domains)')


    listify_assessment_items(treeA)
    de_ariclefy(treeA)
    de_ariclefy(treeB)

    khan_api_json_exclude_attrs = [
        'download_urls',
        'listed',
        'license',  # or map manually ...
        'source_url',
        'thumbnail',
        # 'youtube_id',
    ]

    khan_api_json_map = {
        "root.node_id": "id",
        "root.content_id": "slug",
        "node_id": "id",
        "content_id": "slug",
    }

    diff = treediff(treeA, treeB,
            format="restructured",
            sort_order_changes=False,
            attrs=None,
            exclude_attrs=khan_api_json_exclude_attrs,
            mapA=khan_api_json_map.copy(),
            mapB=khan_api_json_map.copy(),
            assessment_items_key=None,
            setlike_attrs=['tags', 'assessment_items'],
    )

    diff_filename = 'khan_academy_tree_diff_' + args.lang + '.json'
    with open(diff_filename, 'w') as jsonf:
        json.dump(diff, jsonf, indent=2, ensure_ascii=False)


    nodes_deleted = diff['nodes_deleted']
    nodes_added = diff['nodes_added']
    nodes_moved = diff['nodes_moved']
    nodes_modified = diff['nodes_modified']

    print('\n\nnodesdeleted:', len(nodes_deleted))
    # pprint.pprint(nodes_deleted[0])

    print('\n\nnodes_added:', len(nodes_added))
    # # pprint.pprint(nodes_added[0])

    print('\n\nnodes_moved:', len(nodes_moved))
    # pprint.pprint(nodes_moved[0])

    print('\n\nnodes_modified:', len(nodes_modified))
    # pprint.pprint(nodes_modified[100:120], width=200)


    print_diff(diff,
        attrs=['title', 'kind'],
        ids=['node_id', 'parent_id']
    )
