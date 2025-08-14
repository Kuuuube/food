cd $(dirname "$0")
./test.sh
source .env/bin/activate
python build.py
python -m http.server --bind localhost --directory ./dist/food
