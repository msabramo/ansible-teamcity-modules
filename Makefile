.DEFAULT_GOAL := test

clean:
	git clean -Xdf
	rm -rf build/ dist/

test: test-playbook-syntax test-python-syntax

test-playbook-syntax:
	ansible-playbook playbooks/*.yaml --syntax-check

test-python-syntax:
	python -c 'import teamcity_build_config, teamcity_project; print(teamcity_build_config, teamcity_project)'
