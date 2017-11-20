#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'Lineate DevOps team'
}

DOCUMENTATION = '''
---
module: couchbase

short_description: Couchbase configuration library.

version_added: "2.3.2"

description:
    - "This is a module to configure Couchbase cluster using its REST API"

options:
    target:
        description:
            - Couchbase entity to be configured (node, cluster or bucket are supported now)
        required: true
    name:
        description:
            - Name (or string identifier) of Couchbase entity
        required: true
    options:
        description:
            - Configuration settings for Couchbase entity
        required: false

extends_documentation_fragment:
    - 

author:
    - Anton Talevnin (@yourhandle)
'''

EXAMPLES = '''
# Setup Couchbase node
- name: init node
  couchbase:
    target: node
    name: 127.0.0.1
    options:
      services: kv,index,n1ql
      path: "/opt/couchbase/var/lib/couchbase/data"
      index_path: "/opt/couchbase/var/lib/couchbase/index"
    url: "http://127.0.0.1:8091"
    username: "couchbase"
    password: "c0uchbase"

- name: setup cluster
  couchbase:
    target: cluster
    name: default # it's not used
    options:
      nodes: "{{ groups['couchbase-server'] | map('extract', hostvars, ['ansible_default_ipv4', 'address']) | list }}"
      memory: 8192
      imemory: 1024
    url: "http://127.0.0.1:8091"
    username: "couchbase"
    password: "c0uchbase"
  run_once: true
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

import requests
from collections import namedtuple

class CbError(Exception):

    def __init__(self, message, status):
        super(Exception, self).__init__("%s - %s" % (status, message))


# Couchbase client settings to interact via REST
class CbCluster(object):

    __slots__ = ('name', 'session', 'password', 'url', 'version', 'nodes')

    def __init__(self, name='default', url='http://127.0.0.1:8091', **kwargs):
       self.name = name
       self.url = url
       self.session = requests.Session()
       self.session.auth = (kwargs.get('username'), kwargs.get('password'))
       self.version = self.get().get('implementationVersion', 'unknown')
       self.nodes = self.get(path='/pools/nodes').get('nodes',[])

    def add(self, node):
        r = self.post('/controller/addNode', {'hostname': node, 'user': self.session.auth[0], 'password': self.session.auth[1]})
        return r #{u'otpNode': u'ns_1@172.18.0.5'}

    def rebalance(self):
        known = map(lambda x: x['otpNode'], self.nodes)
        nodes = self.get('/pools/default').get('nodes', [])
        if any(filter(lambda x: x['clusterMembership'] != 'active', nodes)):
            r = self.post('/controller/rebalance', {'ejectedNodes': '', 'knownNodes': ','.join(known)})
            return True
        return False

    def setup(self, quotas):
        r = self.post('/pools/default', {'memoryQuota': quotas.memory, 'indexMemoryQuota': quotas.imemory})

    def get(self, path='/pools'):
        r = self.session.get(self.url + path)
        if r.status_code == 404:
            return {}
        return r.json()

    def post(self, path='/pools', data={}):
        r = self.session.post(self.url + path, data=data)
        if not r.ok:
            raise CbError(r.text, r.status_code)
        if int(r.headers['content-length']) > 0:
            return r.json()
        return {}


ClusterOptions = namedtuple('ClusterOptions', ['name', 'memory', 'imemory', 'nodes', 'username', 'password', 'port'])
ClusterOptions.__new__.__defaults__ = ('',1024, 256, [], '', '', 8091)


def cluster(cbc, options):

    def exists():
        pools = cbc.get().get('pools',[])
        return len(pools) > 0

    changed = not exists()

    # Setup quotas for entire cluster
    if changed:
        cbc.setup(options)

    # Add new nodes in a cluster
    nodes = map(lambda x: x['hostname'], cbc.nodes)
    for node in options.nodes:
       if not any(filter(lambda x: x.startswith(node), nodes)):
           cbc.add(node)
           changed = True

    # Rebalance cluster if new nodes were added
    changed = cbc.rebalance() or changed

    return changed


NodeOptions = namedtuple('NodeOptions', ['name', 'username', 'password', 'services', 'path', 'index_path'])
NodeOptions.__new__.__defaults__ = ('127.0.0.1', None, None, 'index,kv,n1ql', '', '')


def node(cbc, options):

    def state(node):
        r = cbc.get('/nodes/self')
        actual = {'name': r['hostname'], 'services': r['services']}

        storage = sum(map(lambda x: x, r['storage'].values()), [])
        if any(filter(lambda x: node.path == x.get('path',''), storage)):
            actual['path'] = node.path

        if any(filter(lambda x: node.index_path == x.get('index_path',''), storage)):
            actual['index_path'] = node.index_path

        return NodeOptions(**actual)

    def services(args):
        r = cbc.post('/node/controller/setupServices', {'services': args.services})
        return True

    def settings(args):
        r = cbc.post('/nodes/self/controller/settings', {'path': args.path, 'index_path': args.index_path})
        return True

    def auth():
        r = cbc.post('/settings/web', {'password': cbc.session.auth[1], 'username': cbc.session.auth[0], 'port': 'SAME'})
        return True

    def rename(args):
        r = cbc.post('/node/controller/rename', {'hostname': args.name})
        return True

    changed = False
    node = state(options)
    if node.path != options.path or node.index_path != options.index_path:
        changed = settings(options)

    if set(node.services) != set(options.services.split(',')):
        changed = services(options)
    auth()
    return changed


BucketOptions = namedtuple('BucketOptions', ['name', 'authType', 'bucketType', 'evictionPolicy', 'flushEnabled',
                                             'ramQuotaMB', 'replicaIndex', 'replicaNumber', 'threadsNumber'])
BucketOptions.__new__.__defaults__ = ('', 'sasl', 'couchbase', None, 0, 0, 0, 1, 2)

def bucket(client, options):

    def state(options):
        r = client.get('/pools/default/buckets')
        return r

    def add(options):
        r = client.post('/pools/default/buckets', options._asdict())

#{'name': options.name, 
#'bucketType': options.type, 'ramQuotaMB': options.ramsize, 'evictionPolicy': options.eviction, 'replicaNumber': options.replica, 'authType': 'sasl' })
        #flushEnabled=1&threadsNumber=3&replicaIndex=0
        return r

    buckets = state(client)
    #print buckets
    if not any(filter(lambda x: x.name == options.name, buckets)):
        add(options)
    return False


TargetHandler = namedtuple('TargetHandler', ['handler', 'settings'])


HANDLERS = {
    'node': TargetHandler(node, NodeOptions),
    'cluster': TargetHandler(cluster, ClusterOptions),
    'bucket': TargetHandler(bucket, BucketOptions),
}

import os
import sys
sys.path.remove(os.path.dirname(os.path.abspath(__file__)))

from ansible.module_utils.basic import AnsibleModule


def run_module():

    module_args = dict(
        id=dict(type='str', required=True, aliases=['name']),
        target=dict(type='str', required=True, choices=HANDLERS.keys()),
        options=dict(type='dict', required=False, default=dict()),
        url=dict(type='str', default='http://127.0.0.1:8091'),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        message='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    try:
        cbc = CbCluster(url=module.params['url'],
                        username=module.params['username'],
                        password=module.params['password'])

        target = HANDLERS[module.params['target']]
        result['version'] = cbc.version
        result['changed'] = target.handler(cbc, target.settings(name=module.params['id'], **module.params['options']))
    except CbError as err:
        module.fail_json(msg=err.message, **result)

    if module.check_mode:
        return result

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()

