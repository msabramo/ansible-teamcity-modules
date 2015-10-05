#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Marc Abramowitz <marca@surveymonkey.com>

DOCUMENTATION = '''
---
module: teamcity_project
short_description: Manage TeamCity projects
description:
     - Manage TeamCity projects
options:
  name:
    description:
      - The name of the TeamCity project
    required: true
    default: null
  state:
    description:
      - The desired state of project
    required: false
    default: present
    choices: [ "present", "absent" ]
  server_url:
    description:
      - URL on which supervisord server is listening
    required: false
    default: null
  username:
    description:
      - username to use for authentication
    required: false
    default: null
  password:
    description:
      - password to use for authentication
    required: false
    default: null
'''

EXAMPLES = '''
- teamcity_project: name="marca_test_project"
- teamcity_project: name="branches" parent_project_id="MarcaTestProject"
'''

import os
import json
import urllib2


class TeamCity(object):
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password

    def _request(self, method, path, data=None, headers=None):
        url = '%s/httpAuth/app/rest/%s' % (self.base_url, path)
        if headers is None:
            headers = {'Content-Type': 'application/json',
                       'Accept': 'application/json'}
        return open_url(
            url, data=data, headers=headers, method=method,
            url_username=self.username, url_password=self.password)

    def create_project(self, name, project_id=None,
                       parent_project_id=None, source_project_id=None):
        data = {'name': name}
        if project_id:
            data['id'] = project_id
        if parent_project_id:
            data['parentProject'] = {'id': parent_project_id}
        if source_project_id:
            data['sourceProject'] = {'id': source_project_id}

        return self._request('POST', 'projects', data)

    def get_project_by_id(self, id):
        return self._request('GET', 'projects/id:%s' % id)

    def set_project_parameters(self, project_id, parameters):
        changed = False

        for name, value in parameters.items():
            path = 'projects/id:%s/parameters/%s' % (project_id, name)
            get_response = self._request('GET', path)
            previous_value = json.loads(get_response.read())['value']
            if value != previous_value:
                self._request('PUT', path, json.dumps({'value': value}))

        return changed

    def delete_project(self, project_id):
        return self._request('DELETE', 'projects/id:%s' % project_id)


def main():
    arg_spec = dict(
        name=dict(required=False),
        project_id=dict(required=False),
        state=dict(choices=['present', 'absent'], default='present'),
        server_url=dict(required=False),
        username=dict(required=False),
        password=dict(required=False),
        parent_project_id=dict(required=False),
        source_project_id=dict(required=False),
        parameters=dict(required=False),
    )

    module = AnsibleModule(argument_spec=arg_spec)

    name = module.params['name']
    project_id = module.params['project_id']
    state = module.params['state']
    server_url = module.params.get('server_url') or os.getenv('TEAMCITY_URL')
    username = module.params.get('username') or os.getenv('TEAMCITY_USER')
    password = module.params.get('password') or os.getenv('TEAMCITY_PASSWORD')
    parent_project_id = module.params.get('parent_project_id')
    source_project_id = module.params.get('source_project_id')
    parameters = module.params.get('parameters')

    result = dict(
        name=name,
        project_id=project_id,
        state=state,
        changed=False,
    )
    if parameters:
        result['parameters'] = parameters
    if parent_project_id:
        result['parent_project_id'] = parent_project_id
    if source_project_id:
        result['source_project_id'] = source_project_id

    teamcity = TeamCity(server_url, username, password)

    if state == 'present':
        resp = teamcity.get_project_by_id(project_id)
        if resp:
            project = json.loads(resp.read())
            # result['project'] = project
        else:
            try:
                resp = teamcity.create_project(
                    name,
                    parent_project_id=parent_project_id,
                    source_project_id=source_project_id)
                if resp:
                    project = json.loads(resp.read())
                    result['changed'] = True
                    result['project_id'] = project_id
                    result['_detail'] = data
            except urllib2.HTTPError as e:
                module.fail_json(name=name, state=state, msg=str(e), url=e.url)

        if parameters:
            changed = teamcity.set_project_parameters(
                project['id'], parameters)
    elif state == 'absent':
        resp = teamcity.delete_project(project_id=project_id)
        result['changed'] = (resp is not None)
    else:
        result['msg'] = 'Illegal state: %s' % state
        module.fail_json(**result)

    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
