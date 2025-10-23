cd $(dirname "$0")
./test.sh
./build.sh
python -m http.server --bind localhost --directory ./dist/food
