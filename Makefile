.DEFAULT_GOAL := help

ifeq ($(OS),Windows_NT)
PYTHON ?= py
ENV_PYTHON := .venv/Scripts/python.exe
else
PYTHON ?= python3
ENV_PYTHON := .venv/bin/python
endif

.PHONY: help create-env install setup run test

help:
	@echo make setup       - Create the environment and install dependencies
	@echo make create-env  - Create the .venv environment
	@echo make install     - Install dependencies into .venv
	@echo make run         - Launch DrawingBoard
	@echo make test        - Discover and run unittest tests

create-env:
	$(PYTHON) -m venv .venv

install:
	"$(ENV_PYTHON)" -m pip install -r requirements.txt

setup: create-env
	$(MAKE) install

run:
	"$(ENV_PYTHON)" main.py

test:
	"$(ENV_PYTHON)" -m unittest discover -v
