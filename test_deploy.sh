cd $(dirname "$0")
python build.py
python -m http.server --bind localhost --directory food
