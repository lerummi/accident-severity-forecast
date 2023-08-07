.MAKEFLAGS += --warn-undifined-variables --no-print-directory
.SHELLFALGS := -ue -o pipfail -c

all: help
.PHONY: all

# Use bash for inline if-statements
SHELL:=bash
APP_NAME=$(shell basename "`pwd`")
OWNER?=martin.krause
DOCKER_REPOSITORY=local
SOURCE_IMAGE=$(DOCKER_REPOSITORY)/$(OWNER)/$(APP_NAME)

# Enable BuildKit for Docker build
export DOCKER_BUILDKIT:=1

##@ Helpers
help: ## display this help
	@echo "$(APP_NAME)"
	@echo "============================="
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m\033[0m"} /^[a-zA-Z0-9_%\/-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@printf "\n"

##@ Install pre-commit
pre-commit-install: ## set up the git hooks script and install pylint
	@pip install pre-commit
	@pre-commit --version
	@pip install pylint


##@ Run all pre-commit hooks
pre-commit: ## run pre-commit hook script manuelly. This is just for testing cases, pre-commit automatically runs when 'git commit'
	pre-commit run --all-files || (printf "\n\n\n" && git --no-pager diff --color=always)


##@ Apply unit test
unit-tests: ## run unit-tests for all directory containing code
	for directory in workflow-orchestration model-training model-deployment model-monitoring ; do \
	    cd $$directory && poetry run pytest ./tests --cov=workflows && cd .. ; \
	done

##@ Build stack
build-compose: CARGS?=--profile all
build-compose: DARGS?=--no-cache
build-compose: ## Run composition locally
	docker-compose $(CARGS) build $(DARGS)

##@ Build and run stack
run-compose: CARGS?=--profile all
run-compose: ## Run composition locally
	docker-compose $(CARGS) up --build

##@ Run simulation mode
simulation: SECONDS_PER_DAY?=10
simulation: MODEL_VERSION=
simulation: ## Run time simulation starting at SIMULATION_START_DATE and continuously ingest data, make model inference, evaluate model and train model based on monitoring metrics drop. Parameter int SECONDS_PER_DAY describe, how many (real!) seconds are forming a day.
	export MODEL_VERSION=$(MODEL_VERSION)
	export SECONDS_PER_DAY=$(SECONDS_PER_DAY)
	docker-compose --profile simulation up --build && docker-compose rm -fsv
