#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Marc Abramowitz <marca@surveymonkey.com>

DOCUMENTATION = '''
---
module: teamcity_build_config
short_description: Manage TeamCity build configurations
description:
     - Manage TeamCity build configurations
options:
  project_id:
    description:
      - The id of the parent TeamCity project
    required: true
    default: null
  state:
    description:
      - The desired state of build configuration
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
- teamcity_build_config:
    name: docs
    build_config_id: MarcaTestProject_Branches_Docs
    project_id: MarcaTestProject_Branches
    template_id: RunPipelineScript
    parameters:
      sm.pipeline.script.name: test.sh
      sm.pipeline.script.args: '"py27" "devmonkeys/anonweb" "%teamcity.build.branch%"'
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

    def create_build_config(self, project_id, name):
        path = 'projects/id:%s/buildTypes' % project_id
        headers = {'Content-Type': 'text/plain',
                   'Accept': 'application/json'}
        return self._request('POST', path, name, headers=headers)

    def get_build_config_by_id(self, id):
        return self._request('GET', 'buildTypes/id:%s' % id)

    def set_build_config_parameters(self, build_config_id, parameters):
        changed = False

        for name, value in parameters.items():
            path = 'buildTypes/id:%s/parameters/%s' % (build_config_id, name)
            get_response = self._request('GET', path)
            previous_value = json.loads(get_response.read())['value']
            if value != previous_value:
                self._request('PUT', path, json.dumps({'value': value}))
                changed = True

        return changed

    def attach_build_config_to_template(self, build_config_id, template_id):
        path = 'buildTypes/id:%s/template' % build_config_id
        headers = {'Content-Type': 'text/plain',
                   'Accept': 'application/json'}
        return self._request('PUT', path, template_id, headers=headers)


def main():
    arg_spec = dict(
        build_config_id=dict(required=False),
        project_id=dict(required=False),
        template_id=dict(required=False),
        name=dict(required=False),
        state=dict(choices=['present', 'absent'], default='present'),
        server_url=dict(required=False),
        username=dict(required=False),
        password=dict(required=False),
        parameters=dict(required=False),
    )

    module = AnsibleModule(argument_spec=arg_spec)

    build_config_id = module.params['build_config_id']
    project_id = module.params['project_id']
    template_id = module.params['template_id']
    name = module.params.get('name')
    state = module.params['state']
    server_url = module.params.get('server_url') or os.getenv('TEAMCITY_URL')
    username = module.params.get('username') or os.getenv('TEAMCITY_USER')
    password = module.params.get('password') or os.getenv('TEAMCITY_PASSWORD')
    parameters = module.params.get('parameters')

    result = dict(
        name=name,
        build_config_id=build_config_id,
        state=state,
        changed=False,
    )
    if parameters:
        result['parameters'] = parameters
    if project_id:
        result['project_id'] = project_id
    if template_id:
        result['template_id'] = template_id

    teamcity = TeamCity(server_url, username, password)

    if state == 'present':
        resp = teamcity.get_build_config_by_id(build_config_id)
        if resp:
            build_config = json.loads(resp.read())
        else:
            try:
                resp = teamcity.create_build_config(project_id, name)
            except urllib2.HTTPError as e:
                module.fail_json(
                    project_id=project_id, state=state, msg=str(e), url=e.url,
                    _details=e.read())

        if template_id:
            teamcity.attach_build_config_to_template(
                build_config['id'], template_id)

        if parameters:
            changed = teamcity.set_build_config_parameters(
                build_config['id'], parameters)
            if changed:
                result['changed'] = True
    elif state == 'absent':
        resp = teamcity.delete_build_config(build_config_id=build_config_id)
        result['changed'] = (resp is not None)
    else:
        result['msg'] = 'Illegal state: %s' % state
        module.fail_json(**result)

    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
