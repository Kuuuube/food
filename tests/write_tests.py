import sys

# add src folder to path to allow accessing build.py there
sys.path.append(sys.path[0] + "/../.")

def write_test_page_html():
    import build

    test_page_markdown = open("./tests/test_page.md").read()
    with open("./tests/test_page.html", "w") as test_page_html:
        test_page_html.write(build.render_html_page("./tests/test_page.html", test_page_markdown))

write_test_page_html()
