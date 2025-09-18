#!/bin/bash
echo "Setting up modular structure..."
cp streamlit_app.py streamlit_app_backup.py
mkdir -p config data providers services ui/pages utils tests
touch config/__init__.py data/__init__.py providers/__init__.py services/__init__.py ui/__init__.py ui/pages/__init__.py utils/__init__.py tests/__init__.py
echo "Directory structure created!"
