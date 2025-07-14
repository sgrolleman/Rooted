# Rooted

Rooted is a small task planning application written in Python. The GUI is built with [PySide6](https://wiki.qt.io/Qt_for_Python) and all data is stored in a local SQLite database. The project provides a basic planner, a "focus mode" window and a template builder for creating project flows.

## Features
- Visual template builder for creating tasks and connections
- Simple project and task management using SQLite
- Focus mode dialog to work through the next task
- Planner that prioritises tasks based on deadlines and other scores

## Setup
1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python Rooted/main.py
   ```
   On first run the file `Rooted/rooted.db` (or `data/rooted.db`) will be created if it does not already exist.

Running the GUI requires a working Qt environment. On systems without a graphical desktop the application will fail to start.

## Repository layout
- `Rooted/` – application source code
- `Rooted/data/` – SQLite schema and example database
- `Rooted/templatebuilder/` – widgets for building templates visually
- `Rooted/views/` – user interface components

This repository does not include automated tests. Running `python -m py_compile $(git ls-files '*.py')` ensures the sources are syntactically correct.
