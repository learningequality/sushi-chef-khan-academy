import sqlite3
from collections import defaultdict
import os
import requests
from itertools import groupby
from operator import itemgetter



# DATABASE
################################################################################

DATABSES_DIR = 'reports/databases'

STUDIO_SERVER_LOOKUP = {
    'production': 'https://studio.learningequality.org',
    'develop': 'https://develop.studio.learningequality.org',
    'local': 'http://localhost:8080',
}

def download_db_file(channel_id, server='production', update=False):
    """
    Download DB file for Kolibri channel `channel_id` from a Studio server.
    """
    db_file_path = os.path.join(DATABSES_DIR, channel_id + '.sqlite3')
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


def dbex(conn, query):
    """
    Execure a DB query and return results as a list of dicts.
    """
    cursor = conn.cursor()
    print('Running DB query', query)
    cursor.execute(query)
    results = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
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
    db_path = download_db_file(channel_id)
    conn = sqlite3.connect(db_path)
    return dbex(conn, "SELECT * FROM content_channelmetadata;")[0]


def get_nodes_by_id(channel_id, attach_files=True):
    db_path = download_db_file(channel_id)
    conn = sqlite3.connect(db_path)
    nodes = dbex(conn, "SELECT * FROM content_contentnode;")
    # TODO: load content_assessmentmetadata
    # TODO: load tags from content_contentnode_tags and content_contenttag
    # TODO: load prerequisites from content_contentnode_has_prerequisite,
    #                           and content_contentnode_related
    nodes_by_id = {}
    for node in nodes:
        nodes_by_id[node['id']] = node
    if attach_files:
        # attach all the files associated with each node under the key "files"
        files = get_files(channel_id)
        for file in files:
            node_id = file['contentnode_id']
            node = nodes_by_id[node_id]
            if 'files' in node:
                node['files'].append(file)
            else:
                node['files'] = [file]
    return nodes_by_id


def get_files(channel_id, kind=None):
    db_path = download_db_file(channel_id)
    conn = sqlite3.connect(db_path)
    files = dbex(conn, "SELECT * FROM content_file;")
    return files


def get_tree(channel_id):
    nodes_by_id = get_nodes_by_id(channel_id)
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


def print_subtree(subtree, level=0, extrakeys=None):
    extra = ''
    if extrakeys:
        for key in extrakeys:
            extra = extra + ' ' + key + '=' + subtree[key]
    print(' '*2*level + '   -', subtree['title'] + ' (' + subtree['id'][0:7] + ')', extra)
    if 'children' in subtree:
        for child in subtree['children']:
            print_subtree(child, level=level+1, extrakeys=extrakeys)

