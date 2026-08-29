.PHONY: help build run test dev clean seed

help:
	@echo "SENTRY - Calibrated ML Email Threat Detection & Forensic Intelligence Platform"
	@echo "Available commands:"
	@echo "  make dev      - Run local backend and frontend concurrently"
	@echo "  make test     - Run full automated pytest test suite"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all microservices via Docker Compose"
	@echo "  make down     - Stop all Docker Compose services"
	@echo "  make seed     - Ingest demo email scenarios into local database"

test:
	.venv/Scripts/pytest -v backend/tests

dev-backend:
	.venv/Scripts/uvicorn app.main:app --app-dir backend --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

up:
	docker compose up -d

down:
	docker compose down

clean:
	rm -rf backend/__pycache__ frontend/dist evidence_vault/*
