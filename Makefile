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
build-compose: DARGS?=--no-cache
build-compose: ## Run composition locally
	docker-compose build $(DARGS)

##@ Build and run stack
run-compose: ## Run composition locally
	docker-compose up --build

