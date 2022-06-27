#!/usr/bin/env python
"""
Helpers for downloding Kolibri databases and printing topic trees:

    ./kolibridb.py --channel_id=95a52b386f2c485cb97dd60901674a98

or to get the same result as HTML (assuming you have `pandoc` installed):

    ./kolibridb.py --channel_id=95a52b386f2c485cb97dd60901674a98 --htmlexport

"""
import argparse
from collections import defaultdict
from contextlib import redirect_stdout
from itertools import groupby
from operator import itemgetter
import os
import io
import json
import requests
import sqlite3
import subprocess
import uuid



# DATABASE
################################################################################

DATABASES_DIR = 'chefdata/databases'

STUDIO_SERVER_LOOKUP = {
    'production': 'https://studio.learningequality.org',
    'develop': 'https://develop.studio.learningequality.org',
    'local': 'http://localhost:8080',
}

def download_db_file(channel_id, server='production', update=False):
    """
    Download DB file for Kolibri channel `channel_id` from a Studio server.
    """
    os.makedirs(DATABASES_DIR, exist_ok=True)
    db_file_path = os.path.join(DATABASES_DIR, channel_id + '.sqlite3')
    if os.path.exists(db_file_path) and not update:
        return db_file_path
    if server in STUDIO_SERVER_LOOKUP.keys():
        base_url = STUDIO_SERVER_LOOKUP[server]
    elif 'http' in server:
        base_url = server.rstrip('/')
    else:
        raise ValueError('Unrecognized arg', server)
    db_file_url = base_url + '/content/databases/' + channel_id + '.sqlite3'
    response = requests.get(db_file_url)
    if response.ok:
        with open(db_file_path, 'wb') as db_file:
            for chunk in response:
                db_file.write(chunk)
        return db_file_path
    else:
        print(response.status_code, response.content)
        raise ConnectionError('Failed to download DB file from', db_file_url)


def dbconnect(db_file_path):
    conn = sqlite3.connect(db_file_path)
    return conn


def dbex(conn, query):
    """
    Execure a DB query and return results as a list of dicts.
    """
    cursor = conn.cursor()
    print('Running DB query', query)
    cursor.execute(query)
    results = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    return results



# BASIC ORM
################################################################################

def dbfilter(rows, **kwargs):
    """
    Return all the `rows` that match the `key=value` conditions, where keys are DB column
    names and value is a row's value.
    """
    selected = []
    for row in rows:
        accept = True
        for key, value in kwargs.items():
            if key not in row or row[key] != value:
                accept = False
        if accept:
            selected.append(row)
    return selected


def filter_key_in_values(rows, key, values):
    """
    Return all the `rows` whose value for `key` is in the list `values`.
    """
    if isinstance(values, str):
        values = [values]
    return list(filter(lambda r: r[key] in values, rows))


def dbget(rows, **kwargs):
    """
    Return all the `rows` that match the `key=value` conditions, where keys are DB column
    names and value is a row's value.
    """
    selected = dbfilter(rows, **kwargs)
    assert len(selected) < 2, 'mulitple results found'
    if selected:
        return selected[0]
    else:
        return None


def dbvalues_list(rows, *args, flat=False):
    results = []
    for row in rows:
        result = []
        for arg in args:
            result.append(row[arg])
        results.append(result)
    if flat:
        return [result[0] for result in results]
    else:
        return results



# UTILS 
################################################################################

def sane_group_by(items, key):
    """
    Wrapper for itertools.groupby to make it easier to use.
    Returns a dict with keys = possible values of key in items
    and corresponding values being lists of items that have that key.
    """
    sorted_items = sorted(items, key=itemgetter(key))
    return dict((k, list(g)) for k, g in groupby(sorted_items, key=itemgetter(key)))


def count_values_for_attr(rows, *attrs):
    counts = {}
    for attr in attrs:
        counts[attr] = defaultdict(int)
        for row in rows:
            val = row[attr]
            counts[attr][val] += 1
    return counts



# KOLIBRI CHANNEL
################################################################################

def get_channel(channel_id):
    db_file_path = download_db_file(channel_id)
    conn = sqlite3.connect(db_file_path)
    return dbex(conn, "SELECT * FROM content_channelmetadata;")[0]


def get_nodes_by_id(conn, attach_files=True, attach_assessments=True):
    nodes = dbex(conn, "SELECT * FROM content_contentnode;")
    # TODO: load tags from content_contentnode_tags and content_contenttag
    # TODO: load content_contentnode_has_prerequisite, content_contentnode_related
    nodes_by_id = {}
    for node in nodes:
        nodes_by_id[node['id']] = node
    if attach_files:
        # attach all the files associated with each node under the key "files"
        files = get_files(conn)
        local_files = get_local_files(conn)
        local_file_lookup = {}
        for local_file in local_files:
            local_file_lookup[local_file["id"]] = local_file
        for file in files:
            node_id = file['contentnode_id']
            node = nodes_by_id[node_id]
            local_file = local_file_lookup[file["local_file_id"]]
            file["extension"] = local_file["extension"]
            file["checksum"] = local_file["id"]
            if 'files' in node:
                node['files'].append(file)
            else:
                node['files'] = [file]
    if attach_assessments:
        assessmentmetadata = get_assessmentmetadata(conn)
        for aim in assessmentmetadata:
            node = nodes_by_id[aim['contentnode_id']]
            # attach assesment_ids direclty to node to imitate ricecooker/studio
            node['assessment_item_ids'] = json.loads(aim['assessment_item_ids'])
            node['assessmentmetadata'] = {
                'number_of_assessments': aim['number_of_assessments'],
                'mastery_model': aim['mastery_model'],
                'randomize': aim['randomize'],
                'is_manipulable': aim['is_manipulable'],
            }
    return nodes_by_id


def get_nodes_for_remote_files(channel_id):
    db_file_path = download_db_file(channel_id)
    conn = sqlite3.connect(db_file_path)
    return get_nodes_by_id(conn, attach_files=True, attach_assessments=False)


def get_files(conn):
    files = dbex(conn, "SELECT * FROM content_file;")
    return files


def get_local_files(conn):
    localfiles = dbex(conn, "SELECT * FROM content_localfile;")
    return localfiles


def get_assessmentmetadata(conn):
    assessmentmetadata = dbex(conn, "SELECT * FROM content_assessmentmetadata;")
    return assessmentmetadata


def get_tree(conn):
    """
    Return a complete JSON tree of the entire channel.
    """
    nodes_by_id = get_nodes_by_id(conn)
    nodes = nodes_by_id.values()
    sorted_nodes = sorted(nodes, key=lambda n: (n['parent_id'] or '0'*32, n['sort_order']))
    root = sorted_nodes[0]
    for node in sorted_nodes[1:]:
        parent = nodes_by_id[node['parent_id']]
        if 'children' in parent:
            parent['children'].append(node)
        else:
            parent['children'] = [node]
    return root



# NODE_ID UTILS
################################################################################

def node_id_from_source_ids(source_domain, channel_source_id, source_ids):
    """
    Compute the node_id (str) for the node whose path is  `source_ids` (list)
    in a channel identified by `source_domain` and `channel_source_id`.
    """
    domain_namespace = uuid.uuid5(uuid.NAMESPACE_DNS, source_domain)
    content_ids = [uuid.uuid5(domain_namespace, source_id).hex for source_id in source_ids]
    print('computed content_ids =', content_ids)
    channel_id = uuid.uuid5(domain_namespace, channel_source_id)
    print('Computed channel_id =', channel_id.hex)
    node_id = channel_id
    for content_id in content_ids:
        node_id = uuid.uuid5(node_id, content_id)
    return node_id.hex



# TREE PRINTING
################################################################################

CONTENT_KINDS = ['topic', 'video', 'audio', 'exercise', 'document', 'slideshow', 'h5p', 'html5']

def get_stats(subtree):
    """
    Recusively compute kind-counts and total file_size (non-deduplicated).
    """
    if 'children' in subtree and subtree['children']:
        stats = dict((kind, 0) for kind in CONTENT_KINDS)
        stats['topic'] = 1  # count self
        stats['size'] = 0
        for child in subtree['children']:
            child_stats = get_stats(child)
            for k, v in child_stats.items():
                stats[k] += v
        return stats
    else:
        size = sum([f['file_size'] for f in subtree['files']])
        return {subtree['kind']: 1, 'size': size}


def stats_to_str(stats):
    stats_str = '  '
    for key in CONTENT_KINDS:
        if key in stats and stats[key]:
            if stats[key] > 1:
                stats_str += str(stats[key]) + ' ' + key + 's, '
            else:
                stats_str += str(stats[key]) + ' ' + key + ', '
    size_mb_str = "%.2f" % (float(stats['size'])/1024/1024) + 'MB'
    stats_str += size_mb_str
    return stats_str


def print_subtree(subtree, level=0, extrakeys=None, maxlevel=2, printstats=True):
    extra = ''
    if level > maxlevel:
        return
    if extrakeys:
        for key in extrakeys:
            extra = extra + ' ' + key + '=' + subtree[key]
    if printstats:
        stats = get_stats(subtree)
        extra += stats_to_str(stats)
    title = subtree['title'].replace('\n', ' ')
    print(' '*2*level + '   -',  title + ' (' + subtree['id'] + ')', extra)
    if 'children' in subtree:
        for child in subtree['children']:
            print_subtree(child, level=level+1, extrakeys=extrakeys, maxlevel=maxlevel, printstats=printstats)



# TREE EXPORT
################################################################################

def export_kolibri_json_tree(channel_id=None, db_file_path=None, suffix='', server='production', update=False):
    """
    Convert a channel from Kolibri database file to a JSON tree.
    """
    if channel_id is None and db_file_path is None:
        raise ValueError("Need to specify either channel_id or db_file_path")

    if db_file_path:
        conn = dbconnect(db_file_path)
    else:
        db_file_path = download_db_file(channel_id, server=server, update=update)
        conn = dbconnect(db_file_path)

    kolibri_tree = get_tree(conn)
    conn.close()

    if db_file_path:
        pre_filename = db_file_path.split(os.pathsep)[-1].replace('.sqlite3', '')
        json_filename = pre_filename + suffix + '.json'
    else:
        json_filename = channel_id + suffix + '.json'

    with open(json_filename, 'w') as jsonf:
        json.dump(kolibri_tree, jsonf, indent=2, ensure_ascii=False, sort_keys=True)
    print('Channel exported as Kolibri JSON Tree in ' + json_filename)



# HTML EXPORTS
################################################################################

KOLIBRI_TREE_HTMLEXPORT_DIR = 'reports/kolibrihtmltrees'

def export_kolibritree_as_html(kolibritree, maxlevel=7):
    """
    Export `kolibritree` as HTML for inspection of contents.
    """
    basedir = KOLIBRI_TREE_HTMLEXPORT_DIR
    if not os.path.exists(basedir):
        os.makedirs(basedir, exist_ok=True)
    channel_id = kolibritree['id']
    path_md = os.path.join(basedir, 'channel_{}_tree.md'.format(channel_id))
    path_html = os.path.join(basedir, 'channel_{}_tree.html'.format(channel_id))

    with io.StringIO() as buf, redirect_stdout(buf):
        print('# Kolibri Topic Tree for channel', channel_id)
        print('')
        print_subtree(kolibritree, maxlevel=maxlevel)
        output_md = buf.getvalue()
        with open(path_md, 'w') as mdfile:
            mdfile.write(output_md)

    subprocess.call(['pandoc', '--from', 'gfm', path_md, '-o', path_html])
    print('Saved', path_html)
    os.remove(path_md)



# CLI
################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Kolibri channel topic tree viewer')
    parser.add_argument('--channel_id', required=True, help="Channel ID")
    parser.add_argument('--printmaxlevel', type=int, default=2, help='print tree depth')
    parser.add_argument('--htmlexport', action='store_true', help='save topic tree as html')
    parser.add_argument('--htmlmaxlevel', type=int, default=7, help='html tree depth')
    parser.add_argument('--update', action='store_true', help='Force re-download of DB file')

    args = parser.parse_args()


    db_file_path = download_db_file(args.channel_id, update=args.update)
    conn = dbconnect(db_file_path)
    kolibritree = get_tree(conn)

    # PRINT IN TERMINAL
    print_subtree(kolibritree, maxlevel=args.printmaxlevel)

    # HTML TREE EXPORT
    if args.htmlexport:
        export_kolibritree_as_html(kolibritree, maxlevel=args.htmlmaxlevel)
