CONFIG := $(XDG_CONFIG_HOME)/pypirc

publish-test:
	flit publish --repository testpypi
