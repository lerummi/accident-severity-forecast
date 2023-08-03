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
simulation: SECONDS_PER_DAY?=5
simulation: EVAL_SCHEDULER_INCREMENT?=1
simulation: MODEL_VERSION=
simulation: ## Run time simulation starting at SIMULATION_START_DATE and continuously ingest data, make model inference, evaluate model and train model based on monitoring metrics drop. Parameter int SECONDS_PER_DAY describe, how many (real!) seconds are forming a day.
	export MODEL_VERSION=$(MODEL_VERSION)
	docker-compose --profile simulation up --build
