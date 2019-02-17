VENV = venv
PYTEST = $(PWD)/$(VENV)/bin/py.test

# These targets are not files
.PHONY: build_sandbox clean compile_translations coverage css docs extract_translations help install install-python \
 install-test install-js lint release retest sandbox_clean sandbox_image sandbox test todo venv

help: ## Display this help message
	@echo "Please use \`make <target>\` where <target> is one of"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; \
	{printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

##################
# Install commands
##################
install: install-python ## Install requirements for local development and production

install-python: ## Install python requirements
	conda config --add channels conda-forge
	conda install uwsgi
	pip install -r requirements.txt
	pip install -r requirements_migrations.txt


create_env: ##creates a conda env
	conda create -n vivify_backend

activate_env: ## activates the conda env
	conda activate vivify_backend

#############################
# Sandbox management commands
#############################
sandbox:  install build_sandbox ## Install requirements and create a sandbox

build_sandbox: sandbox_clean sandbox_load_user sandbox_load_data ## Creates a sandbox from scratch

sandbox_clean: ## Clean sandbox images,cache,static and database
	# Remove media
	-rm -rf sandbox/public/media/images
	-rm -rf sandbox/public/media/cache
	-rm -rf sandbox/public/static
	-rm -f sandbox/db.sqlite
	# Create database
	sandbox/manage.py migrate

sandbox_load_user: ## Load user data into sandbox
	sandbox/manage.py loaddata sandbox/fixtures/auth.json

sandbox_load_data: ## Import fixtures and collect static
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	sandbox/manage.py loaddata sandbox/fixtures/child_products.json
	sandbox/manage.py oscar_import_catalogue sandbox/fixtures/*.csv
	sandbox/manage.py oscar_import_catalogue_images sandbox/fixtures/images.tar.gz
	sandbox/manage.py oscar_populate_countries --initial-only
	sandbox/manage.py loaddata sandbox/fixtures/pages.json sandbox/fixtures/ranges.json sandbox/fixtures/offers.json
	sandbox/manage.py loaddata sandbox/fixtures/orders.json sandbox/fixtures/promotions.json
	sandbox/manage.py clear_index --noinput
	sandbox/manage.py update_index catalogue
	sandbox/manage.py thumbnail cleanup
	sandbox/manage.py collectstatic --noinput

sandbox_image: ## Build latest docker image of django-oscar-sandbox
	docker build -t django-oscar-sandbox:latest .


	pip install twine wheel
	rm -rf dist/*
	python setup.py sdist bdist_wheel
	twine upload -s dist/*
