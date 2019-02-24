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
# Vivify management commands
#############################
vivify:  install build_vivify ## Install requirements and create vivify

build_vivify: vivify_clean vivify_load_user vivify_load_data ## Creates vivify from scratch

vivify_clean: ## Clean vivify images,cache,static and database
	# Remove media
	-rm -rf vivify/public/media/images
	-rm -rf vivify/public/media/cache
	-rm -rf vivify/public/static
	-rm -f vivify/db.sqlite
	# Create database
	vivify/manage.py migrate

vivify_load_user: ## Load user data into vivify
	vivify/manage.py loaddata vivify/fixtures/auth.json

vivify_load_data: ## Import fixtures and collect static
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	vivify/manage.py loaddata vivify/fixtures/child_products.json
	vivify/manage.py oscar_import_catalogue vivify/fixtures/*.csv
	vivify/manage.py oscar_import_catalogue_images vivify/fixtures/images.tar.gz
	vivify/manage.py oscar_populate_countries --initial-only
	vivify/manage.py loaddata vivify/fixtures/pages.json vivify/fixtures/ranges.json vivify/fixtures/offers.json
	vivify/manage.py loaddata vivify/fixtures/orders.json vivify/fixtures/promotions.json
	vivify/manage.py clear_index --noinput
	vivify/manage.py update_index catalogue
	vivify/manage.py thumbnail cleanup
	vivify/manage.py collectstatic --noinput
