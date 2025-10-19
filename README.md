<h1 align=center>
    Missing Cursor Problem
</h1>

## 1. Prerequisites

- conda (highly recommended)
- pip

## 2. Setup

```shell
# repo
git clone https://github.com/kjh2159/missing-cursor.git
cd missing-cursor

# venv and packages
conda create --name cursor python=3.13
conda activate cursor
pip install PyQt6
```
> For the web version, you don't need to prepare venv and packages.

## 3. Execution

### A. Python

```shell
python py/cursor.py
```

### B. Web
```shell
# Windows
start "" chrome ".\web\cursor.html"

# or
# OSX
open web/cursor.html
```
