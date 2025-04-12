.PHONY: docs

test:
	uv run pytest --junitxml=report.xml tests/

# publish:
# 	pip3 install 'twine>=1.5.0'
# 	python3 setup.py sdist bdist_wheel
# 	twine upload dist/*
# 	rm -fr build dist .egg gnmi-py.egg-info

docs:
	cd docs && make html
	@echo "\033[95m\n\nBuild successful! View the docs homepage at docs/_build/html/index.html.\n\033[0m"