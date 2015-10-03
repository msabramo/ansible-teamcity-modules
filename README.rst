TeamCity modules for Ansible
============================

.. image:: https://travis-ci.org/msabramo/ansible-teamcity-modules.svg?branch=master
    :target: https://travis-ci.org/msabramo/ansible-teamcity-modules

This implements some `Ansible <http://www.ansible.com/>`_ modules for managing
`TeamCity <https://www.jetbrains.com/teamcity/>`_ projects and build configs.

Basically you can do stuff like this:

.. code-block:: yaml

    ---
    - hosts: localhost
      gather_facts: no
      tasks:
        - teamcity_project:
            name: marca_test_project  # ==> MarcaTestProject
        - teamcity_project:
            name: branches
            parent_project_id: MarcaTestProject  # ==> MarcaTestProject_Branches
        - teamcity_build_config:
            project_id: MarcaTestProject_Branches
            name: "{{ item }}"
            template_id: RunPipelineScript  # ==> MarcaTestProject_Branches_Docs, etc.
          with_items:
            - docs
            - flake8
            - package
            - py27

See the ``playbooks`` directory.


Tests
=====

To run some simple (but not very thorough) tests, do ``make test``.

To really test this, you need to have a TeamCity server. You will need to set some environment variables for your TeamCity server:

- ``TEAMCITY_URL``
- ``TEAMCITY_USER``
- ``TEAMCITY_PASSWORD``

Then you can do:

.. code-block:: bash

    $ ansible-playbook playbooks/create_projects.yaml
    $ ansible-playbook playbooks/delete_projects.yaml


Travis CI
=========

https://travis-ci.org/msabramo/ansible-teamcity-modules
