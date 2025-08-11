import os
import re
import shutil
import sys

BASE_DIRS = ["recipes"]
BUILD_DIR = "food"
INDEX_BLACKLIST_DIRS = ["page_assets"]
BUILD_ASSETS_DIR = "build_assets"
PAGE_ASSETS_DIR = "page_assets"

if "build.py" not in os.listdir():
    print("Aborting build, build.py not found in cwd. Navigate to build.py's parent directory and try again.")
    sys.exit()
shutil.rmtree(BUILD_DIR, ignore_errors = True)
os.makedirs(BUILD_DIR, exist_ok = True)
shutil.copytree(PAGE_ASSETS_DIR, BUILD_DIR + "/" + PAGE_ASSETS_DIR, dirs_exist_ok = True)

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

def get_html_head(output_html_path):
    assets_folder_relative = "../" * (output_html_path.count("/") - 1) + PAGE_ASSETS_DIR + "/"
    replacements = [
        {"target": r"{page_title}", "replacement": output_html_path.split("/")[-2].replace("_", " ").title()},
        {"target": r"{./styles.css}", "replacement": assets_folder_relative + "styles.css"},
    ]
    head_html = open("./" + BUILD_ASSETS_DIR + "/head.html").read()
    for replacement in replacements:
        head_html = head_html.replace(replacement["target"], replacement["replacement"])
    return head_html

def markdown_to_html(markdown_string):
    markdown_string = re.sub("(\n|\r){2,}", "\n\n", markdown_string) # remove excessive blank lines
    markdown_lines = list(map(str.rstrip, markdown_string.split("\n"))) # strip excess whitespace only on right, left side whitespace is sytactically important

    # a -> b replacements
    basic_replacements = [
        {"target": "^###### ", "prefix": "", "replacement": "<h6>", "suffix": "</h6>"},
        {"target": "^##### ", "prefix": "", "replacement": "<h5>", "suffix": "</h5>"},
        {"target": "^#### ", "prefix": "", "replacement": "<h4>", "suffix": "</h4>"},
        {"target": "^### ", "prefix": "", "replacement": "<h3>", "suffix": "</h3>"},
        {"target": "^## ", "prefix": "", "replacement": "<h2>", "suffix": "</h2>"},
        {"target": "^# ", "prefix": "", "replacement": "<h1>", "suffix": "</h1>"},
        {"target": "^-# ", "prefix": "", "replacement": "<sub>", "suffix": "</sub>"},
        {"target": r"\[(.+?)\]\((.+?)\)", "prefix": "", "replacement": r'<a href="\2">\1</a>', "suffix": ""},
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
         "alternate_target": r"(^\s{2,}|^$)", "alternate_prefix": "", "alternate_replacement": r"\1", "alternate_suffix": "<br>"},
        {"target": "^[0-9]. ", "prefix": "", "replacement": "<li>", "suffix": "</li>", "starting_prefix": "<ol>\n", "ending_suffix": "</ol>\n",
         "alternate_target": r"(^\s{2,}|^$)", "alternate_prefix": "", "alternate_replacement": r"\1", "alternate_suffix": "<br>"},
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

    # replacements that switch state after each replace
    on_off_stateful_replacements = [
        {"target": r"\*\*", "replacement_on": "<b>", "replacement_off": "</b>"},
        {"target": r"\*", "replacement_on": "<i>", "replacement_off": "</i>"},
        {"target": "__", "replacement_on": "<u>", "replacement_off": "</u>"},
    ]
    for on_off_stateful_replacement in on_off_stateful_replacements:
        state_active = True
        i = 0
        markdown_lines_len = len(markdown_lines)
        while i < markdown_lines_len:
            while re.search(on_off_stateful_replacement["target"], markdown_lines[i]):
                replacement_text = on_off_stateful_replacement["replacement_on"] if state_active else on_off_stateful_replacement["replacement_off"]
                markdown_lines[i] = re.subn(on_off_stateful_replacement["target"], replacement_text, markdown_lines[i], count = 1)[0]
                state_active = not state_active

            i += 1

    result_html = "\n".join(markdown_lines)

    # a -> b replacements spanning multiple lines
    basic_multiline_replacements = [
        {"target": "```((.|\n)*?)```", "replacement": r'<pre>\1</pre>'},
        {"target": "`(.*)`", "replacement": r'<code>\1</code>'},
        {"target": "\n> (.*)", "replacement": r'\n<blockquote>\1</blockquote>'},
        {"target": "\n>>> ((.|\n)*?(\n(?=\n)|$))", "replacement": r'\n<blockquote>\1</blockquote>'},
        {"target": "\n", "replacement": r'<br>', "alternate_search": "(<blockquote>.*(?<!</blockquote>)\n(?:.|\n)*</blockquote>)"}, # Set `\n` to `<br>` inside multiline block quote

        {"target": r"(</(li|ol|ul|h\d|br|div|p|pre|blockquote)>)\n+", "replacement": r"\1\n"},
        {"target": "\n\n", "replacement": "<br>\n"},
    ]
    for basic_multiline_replacement in basic_multiline_replacements:

        if "alternate_search" in basic_multiline_replacement:
            for regex_match in re.findall(basic_multiline_replacement["alternate_search"], result_html):
                result_html = re.sub(regex_match, re.sub(basic_multiline_replacement["target"], basic_multiline_replacement["replacement"], regex_match), result_html)
        else:
            result_html = re.sub(basic_multiline_replacement["target"], basic_multiline_replacement["replacement"], result_html)

    return result_html

for file_path in walk_dirs(BASE_DIRS):
    if file_path.split(".")[-1] == "md":
        markdown_data = open(file_path).read()
        output_html_path = BUILD_DIR + "/" + file_path.split(".")[0] + ".html"
        os.makedirs("/".join(output_html_path.split("/")[:-1]), exist_ok = True)
        with open(BUILD_DIR + "/" + file_path.split(".")[0] + ".html", "w") as output_html:
            output_html.write(get_html_head(output_html_path))
            output_html.write("<body>\n")
            output_html.write(markdown_to_html(markdown_data))
            output_html.write("</body>\n")

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

for noindex_dir in get_noindex_dirs([BUILD_DIR]):
    noindex_dir_list = os.scandir(noindex_dir)
    output_html_path = noindex_dir + "/index.html"
    with open(output_html_path, "w") as index_file:
        index_file.write(get_html_head(output_html_path))
        index_file.write("<body id=\"placeholder-index-page\"><div class=\"border-container\">\n")
        index_items = []
        for item in noindex_dir_list:
            if item.name in INDEX_BLACKLIST_DIRS or item.name == "index.html":
                continue
            index_items.append("<h1><a href=\"" + "./" + item.name + "\">" + item.name.replace("_", " ").title() + "</a></h1>\n")
        index_file.write("<hr>\n".join(index_items))
        index_file.write("</div></body>\n")
