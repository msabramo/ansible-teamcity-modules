#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Marc Abramowitz <marca@surveymonkey.com>

import os
import json
import urllib2


class MethodRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else:
            self._method = None
        return urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        if self._method is not None:
            return self._method
        return urllib2.Request.get_method(self, *args, **kwargs)


class TeamCity(object):
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.opener = self._get_opener()

    def _get_opener(self):
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(
            None, self.base_url, self.username, self.password)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        return urllib2.build_opener(handler)

    def create_project(self, name, parent_project_id=None,
                       source_project_id=None):
        data = {'name': name}
        if parent_project_id:
            data['parentProject'] = {'id': parent_project_id}
        if source_project_id:
            data['sourceProject'] = {'id': source_project_id}

        try:
            return self._request('POST', 'projects', data)
        except urllib2.HTTPError as e:
            if e.code == 400:
                return None
            raise

    def create_build_config(self, project_id, name):
        path = 'projects/id:%s/buildTypes' % project_id
        headers = {
            'Content-Type': 'text/plain',
            'Accept': 'application/json',
        }
        try:
            return self._request('POST', path, name, headers=headers)
        except urllib2.HTTPError as e:
            if e.code == 400:
                return None
            raise

    def attach_build_config_to_template(self, build_config_id, template_id):
        path = 'buildTypes/id:%s/template' % build_config_id
        headers = {
            'Content-Type': 'text/plain',
            'Accept': 'application/json',
        }
        # try:
        return self._request('PUT', path, template_id, headers=headers)
        # except urllib2.HTTPError as e:
        #     if e.code == 400:
        #         return None
        #     raise

    def create_build_config_from_data(self, project_id, data):
        # I can't get this to work
        # try:
        return self._request('POST', 'buildTypes', data)
        # except urllib2.HTTPError as e:
        #     if e.code == 400:
        #         return None
        #     raise

    def create_project_from_data(self, name, data):
        try:
            return self._request('POST', 'projects', data)
        except urllib2.HTTPError as e:
            if e.code == 400:
                return None
            raise

    def delete_project(self, id):
        try:
            return self._request('DELETE', 'projects/id:%s' % id)
        except urllib2.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def _request(self, method, path, data=None, headers=None):
        url = self._get_url(path)
        if headers is None:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        request = MethodRequest(url, method=method, headers=headers)
        if data:
            resp = self.opener.open(request, data=data)
        else:
            resp = self.opener.open(request)
        return resp

    def _get_url(self, path):
        middle = 'httpAuth/app/rest'
        return '%s/%s/%s' % (self.base_url, middle, path)


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
- teamcity_project: name="marca_test_project"
- teamcity_project: name="branches" parent_project_id="MarcaTestProject"
'''


def main():
    arg_spec = dict(
        project_id=dict(required=False),
        template_id=dict(required=False),
        name=dict(required=False),
        state=dict(choices=['present', 'absent'], default='present'),
        server_url=dict(required=False),
        username=dict(required=False),
        password=dict(required=False),
        parent_project_id=dict(required=False),
        source_project_id=dict(required=False),
        from_json=dict(required=False),
    )

    module = AnsibleModule(argument_spec=arg_spec)

    project_id = module.params['project_id']
    template_id = module.params['template_id']
    name = module.params.get('name')
    state = module.params['state']
    server_url = module.params.get('server_url') or os.getenv('TEAMCITY_URL')
    username = module.params.get('username') or os.getenv('TEAMCITY_USER')
    password = module.params.get('password') or os.getenv('TEAMCITY_PASSWORD')
    # from_json = module.params.get('from_json')

    teamcity = TeamCity(server_url, username, password)

    if state == 'present':
        try:
            # Can't get this working
            # if from_json:
            #     resp = teamcity.create_build_config_from_data(
            #         project_id, from_json)
            #     # data = json.loads(resp.read())
            #     func = 'create_build_config_from_data'
            #     module.exit_json(
            #         changed=True, project_id=project_id,  # _details=data,
            #         state=state, _func=func)
            func = 'create_build_config'
            resp = teamcity.create_build_config(project_id, name)
        except urllib2.HTTPError as e:
            module.fail_json(
                project_id=project_id, state=state, msg=str(e), url=e.url,
                _details=e.read(), _func=func)
        if resp:
            data = json.loads(resp.read())

            if template_id:
                func = 'create_build_config'
                build_config_id = data['id']
                resp = teamcity.attach_build_config_to_template(
                    build_config_id, template_id)

            module.exit_json(
                changed=True, name=name, state=state, _details=data)
        else:
            module.exit_json(changed=False, name=name, state=state)
    elif state == 'absent':
        resp = teamcity.delete_project(id=id)
        changed = (resp is not None)
        module.exit_json(changed=changed, id=id, state=state)
    else:
        data['error'] = 'Illegal state: %s' % state


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
