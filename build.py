import os
import re
import shutil
import sys
import json
import hashlib

BASE_DIRS = ["page_src/recipes"]
BUILD_DIR = "dist/food"
DIST_SHIFT_DIRS = ["page_src"]
INDEX_BLACKLIST_DIRS = ["assets"]
BUILD_ASSETS_DIR = "build_assets"
PAGE_ASSETS_DIR = "page_assets"
PAGE_ASSETS_BUILD_DIR = os.path.join(BUILD_DIR, "assets")

def walk_dirs(start_dirs):
    files = []
    dirs = start_dirs
    while len(dirs) > 0:
        for item in os.scandir(dirs.pop()):
            if item.is_dir():
                dirs.append(item.path)
            elif item.is_file():
                files.append(item.path)
    return files

def shift_dirs(directory_path):
    for shift_dir in DIST_SHIFT_DIRS:
        directory_path = re.sub("/+", "/", directory_path.replace(shift_dir, "/"))
    return directory_path

def get_html_head(output_html_path):
    replacements = [
        {"target": r"{page_title}", "replacement": output_html_path.split("/")[-2].replace("_", " ").title()},
        {"target": r"{./styles.css}", "replacement": os.path.relpath(os.path.join(PAGE_ASSETS_BUILD_DIR, "styles.css"), os.path.dirname(output_html_path))},
    ]
    head_html = open("./" + BUILD_ASSETS_DIR + "/head.html").read()
    for replacement in replacements:
        head_html = head_html.replace(replacement["target"], replacement["replacement"])
    return head_html

def markdown_to_html(markdown_string):
    markdown_string = re.sub("(\n|\r){2,}", "\n\n", markdown_string) # remove excessive blank lines
    markdown_string_hash = hashlib.sha256(markdown_string.encode("utf-8")).hexdigest()
    markdown_lines = list(map(str.rstrip, markdown_string.split("\n"))) # strip excess whitespace only on right, left side whitespace is sytactically important

    # a -> b replacements
    basic_replacements = [
        {"target": "^###### ", "prefix": "", "replacement": "<h6>", "suffix": "</h6>"}, # h6
        {"target": "^##### ", "prefix": "", "replacement": "<h5>", "suffix": "</h5>"}, # h5
        {"target": "^#### ", "prefix": "", "replacement": "<h4>", "suffix": "</h4>"}, # h4
        {"target": "^### ", "prefix": "", "replacement": "<h3>", "suffix": "</h3>"}, # h3
        {"target": "^## ", "prefix": "", "replacement": "<h2>", "suffix": "</h2>"}, # h2
        {"target": "^# ", "prefix": "", "replacement": "<h1>", "suffix": "</h1>"}, # h1
        {"target": "^-# ", "prefix": "", "replacement": "<sub>", "suffix": "</sub>"}, # subtext
        {"target": r"\[(.+?)\]\((.+?)\)", "prefix": "", "replacement": r'<a href="\2">\1</a>', "suffix": ""}, # link
        {"target": r"\*\*(.*)\*\*", "prefix": "", "replacement": r'<b>\1</b>', "suffix": ""}, # bold
        {"target": "__(.*)__", "prefix": "", "replacement": r'<u>\1</u>', "suffix": ""}, # underline
        {"target": r"(?:\*|_)(.*)(?:\*|_)", "prefix": "", "replacement": r'<i>\1</i>', "suffix": ""}, # italic
    ]
    for basic_replacement in basic_replacements:
        i = 0
        markdown_lines_len = len(markdown_lines)
        while i < markdown_lines_len:
            if re.search(basic_replacement["target"], markdown_lines[i]):
                markdown_lines[i] = basic_replacement["prefix"] + re.sub(basic_replacement["target"], basic_replacement["replacement"], markdown_lines[i]) + basic_replacement["suffix"]
            i += 1

    # replacements that need special handling at the start and end as well as allowing alternate matches to hold the state
    stateful_replacements = [
        {"target": r"^(-|\*) ", "prefix": "", "replacement": "<li>", "suffix": "</li>", "starting_prefix": "<ul>\n", "ending_suffix": "</ul>\n",
         "alternate_target": r"(^\s{2,}|^$)", "alternate_prefix": "", "alternate_replacement": r"\1", "alternate_suffix": "<br>"}, # ul and li children
        {"target": "^[0-9]+. ", "prefix": "", "replacement": "<li>", "suffix": "</li>", "starting_prefix": "<ol>\n", "ending_suffix": "</ol>\n",
         "alternate_target": r"(^\s{2,}|^$)", "alternate_prefix": "", "alternate_replacement": r"\1", "alternate_suffix": "<br>"}, # ol and li children
    ]

    for stateful_replacement in stateful_replacements:
        state_active = False
        i = 0
        markdown_lines_len = len(markdown_lines)
        while i < markdown_lines_len:
            found_target = re.search(stateful_replacement["target"], markdown_lines[i])
            found_alternative_target = re.search(stateful_replacement["alternate_target"], markdown_lines[i])
            if found_target and state_active:
                markdown_lines[i] = re.sub(stateful_replacement["target"], stateful_replacement["replacement"], markdown_lines[i]) + stateful_replacement["suffix"]
            elif found_target:
                markdown_lines[i] = stateful_replacement["starting_prefix"] + re.sub(stateful_replacement["target"], stateful_replacement["replacement"], markdown_lines[i]) + stateful_replacement["suffix"]
                state_active = True
            elif found_alternative_target and state_active:
                markdown_lines[i] = re.sub(stateful_replacement["alternate_target"], stateful_replacement["alternate_replacement"], markdown_lines[i])
            elif not found_target and state_active:
                markdown_lines[i] = stateful_replacement["ending_suffix"] + "\n" + markdown_lines[i]
                state_active = False
            i += 1

        if state_active:
            markdown_lines[markdown_lines_len - 1] += stateful_replacement["ending_suffix"]

    result_html = "\n".join(markdown_lines)

    # a -> b replacements spanning multiple lines
    basic_multiline_replacements = [
        {"target": "```((.|\n)*?)```", "replacement": r'<pre>\1</pre>'}, # multiline code block
        {"target": "`(.*)`", "replacement": r'<code>\1</code>'}, # inline code block
        {"target": "\n> (.*)", "replacement": r'\n<blockquote>\1</blockquote>'}, # single line quote
        {"target": "\n>>> ((.|\n)*?(\n(?=\n)|$))", "replacement": r'\n<blockquote>\1</blockquote>'}, # multiline quote
        {"target": "\n", "replacement": r'<br>\n', "alternate_search": "(<blockquote>.*(?<!</blockquote>)\n(?:.|\n)*?(?:</blockquote>))"}, # set `\n` to `<br>` inside multiline block quote
        {"target": "<!--.*?-->", "replacement": ""}, # remove html comments

        {"target": r"(</(li|ol|ul|h\d|br|div|p|pre|blockquote)>)\n+", "replacement": r"\1\n"}, # compress newlines behind line breaking elements to allow correct br insertion between non line breaking elements
        {"target": "\n\n", "replacement": "<br>\n"}, # insert brs for double newlines
    ]
    for basic_multiline_replacement in basic_multiline_replacements:

        if "alternate_search" in basic_multiline_replacement:
            for regex_match in re.findall(basic_multiline_replacement["alternate_search"], result_html):
                result_html = re.sub(re.escape(regex_match), re.sub(basic_multiline_replacement["target"], basic_multiline_replacement["replacement"], regex_match), result_html)
        else:
            result_html = re.sub(basic_multiline_replacement["target"], basic_multiline_replacement["replacement"], result_html)

    result_html = "<span id=\"markdown-hash\" title=\"" + markdown_string_hash + "\">" + markdown_string_hash[:7] + "</span>\n" + result_html
    result_html = "<a id=\"back-button\" href=\"../\"><-</a>" + result_html

    return result_html

def render_html_page(output_html_path, markdown_data):
    output_html = ""
    output_html += get_html_head(output_html_path)
    output_html += "<body>\n"
    output_html += markdown_to_html(markdown_data)
    output_html += "</body>\n"
    return output_html

def get_search_js(html_content_file_paths, output_html_path):
    relative_html_content_paths = []
    for html_content_file_path in html_content_file_paths:
        name = html_content_file_path.replace("/index.html", "").split("/")[-1].replace("_", " ").title()
        rel_path = os.path.relpath(os.path.dirname(html_content_file_path), os.path.dirname(output_html_path))
        relative_html_content_paths.append({"name": name, "path": rel_path})
    search_index = json.dumps(relative_html_content_paths)
    search_js_index_injected = open(os.path.join(BUILD_ASSETS_DIR, "search.js")).read().replace(r"{search_index}", search_index)
    return search_js_index_injected.strip()

def get_noindex_dirs(start_dirs):
    dirs = start_dirs
    noindex_dirs = []
    while len(dirs) > 0:
        index_found = False
        current_dir = dirs.pop()
        for item in os.scandir(current_dir):
            if item.is_dir() and item.name not in INDEX_BLACKLIST_DIRS:
                dirs.append(item.path)
            elif item.is_file() and item.name == "index.html":
                index_found = True
        if not index_found:
            noindex_dirs.append(current_dir)
    return noindex_dirs

if __name__ == "__main__":
    if "build.py" not in os.listdir():
        print("Aborting build, build.py not found in cwd. Navigate to build.py's parent directory and try again.")
        sys.exit()
    shutil.rmtree(BUILD_DIR, ignore_errors = True)
    os.makedirs(BUILD_DIR, exist_ok = True)
    shutil.copytree(PAGE_ASSETS_DIR, PAGE_ASSETS_BUILD_DIR, dirs_exist_ok = True)

    html_content_file_paths = []

    for file_path in walk_dirs(BASE_DIRS):
        if file_path.split(".")[-1] == "md":
            markdown_data = open(file_path).read()
            output_html_path = shift_dirs(os.path.join(BUILD_DIR, file_path.split(".")[0] + ".html"))
            html_content_file_paths.append(output_html_path)
            os.makedirs("/".join(output_html_path.split("/")[:-1]), exist_ok = True)
            with open(output_html_path, "w") as output_html:
                output_html.write(render_html_page(output_html_path, markdown_data))

    for noindex_dir in get_noindex_dirs([BUILD_DIR]):
        noindex_dir_list = sorted(os.scandir(noindex_dir), key = lambda x: x.name)
        output_html_path = os.path.join(noindex_dir, "index.html")
        with open(output_html_path, "w") as index_file:
            index_file.write(get_html_head(output_html_path))
            index_items = []
            for item in noindex_dir_list:
                if item.name in INDEX_BLACKLIST_DIRS or item.name == "index.html":
                    continue
                index_items.append("<a href=\"" + "./" + item.name + "\"><h1>" + item.name.replace("_", " ").title() + "</h1></a>")
            placeholder_index_template = open(os.path.join(BUILD_ASSETS_DIR, "placeholder_index.html")).read()
            placeholder_index_template = placeholder_index_template.replace(r"{index_items}", "\n<hr>\n".join(index_items))
            placeholder_index_template = placeholder_index_template.replace(r"{search_js}", get_search_js(html_content_file_paths, output_html_path))
            index_file.write(placeholder_index_template)
