# Makefile for ELK project

# Default environment (production or development)
ELK_ENV ?= production

# Main target: run the project
run: 
	@echo "Running in $(ELK_ENV) environment..."
	@ELK_ENV=$(ELK_ENV) uv run src/main.py

# Optional: create virtual environment using uv if needed
venv:
	@echo "Ensuring virtual environment exists..."
	@uv venv

# Clean virtual environment (optional)
clean:
	@echo "Removing virtual environment..."
	@rm -rf venv
