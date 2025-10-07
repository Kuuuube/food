import sys

# add src folder to path to allow accessing build.py there
sys.path.insert(0, sys.path[0] + "/../.")

def test_html_render():
    import build

    test_page_markdown = open("./tests/test_page.md").read()
    test_page_html = open("./tests/test_page.html").read()

    assert(build.render_html_page("./tests/test_page.html", test_page_markdown) == test_page_html)
