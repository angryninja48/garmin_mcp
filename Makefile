.PHONY: help build up down logs test clean restart

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the Docker image
	docker-compose build

up: ## Start the container
	docker-compose up -d
	@echo "✅ Container started. View logs with: make logs"

down: ## Stop the container
	docker-compose down

logs: ## Follow container logs
	docker-compose logs -f

test: ## Run automated Docker test
	./test-docker.sh

restart: ## Restart the container
	docker-compose restart
	@echo "✅ Container restarted"

clean: ## Stop container and remove volumes
	docker-compose down -v
	@echo "✅ Container and volumes removed"

rebuild: ## Rebuild and restart (for code changes)
	docker-compose up --build -d
	@echo "✅ Container rebuilt and restarted. View logs with: make logs"

status: ## Show container status
	docker-compose ps

shell: ## Open shell in running container
	docker-compose exec garmin-mcp /bin/bash

# Kubernetes targets
k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f k8s/deployment.yaml

k8s-logs: ## View Kubernetes logs
	kubectl logs -f deployment/garmin-mcp -n garmin-mcp

k8s-status: ## Check Kubernetes deployment status
	kubectl get all -n garmin-mcp

k8s-delete: ## Delete Kubernetes deployment
	kubectl delete namespace garmin-mcp
