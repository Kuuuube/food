function truncate_string(input_string) {
    return input_string.toLowerCase().replaceAll(/[-_]/g, " ").trim().replaceAll(/[^a-zA-Z0-9\s]/g, "");
}

function update_search() {
    const search_text_truncated = truncate_string(document.querySelector("#index-page-search").value);
    const search_text_regex_ready = RegExp.escape(truncate_string(document.querySelector("#index-page-search").value)).replaceAll("\\x20", " ");
    let possible_results = [];
    for (const search_item of SEARCH_INDEX) {
        if (search_text_truncated.length === 0) { break; }
        const index_name_truncated = truncate_string(search_item.name);

        let score = 0;

        const partial_any_position_any_word = new RegExp(`(${search_text_regex_ready.replaceAll(/\s/g, "|")})`, "g");
        const partial_any_position_any_word_match = index_name_truncated.match(partial_any_position_any_word);
        if (partial_any_position_any_word_match) {
            score += 1 * Math.min(partial_any_position_any_word_match.length, 9); // partial any position any word match
        }
        const partial_any_word_start = new RegExp(`(?:^| )(${search_text_regex_ready.replaceAll(/\s/g, "|")})`, "g");
        const partial_any_word_start_match = index_name_truncated.match(partial_any_word_start);
        if (partial_any_word_start_match) {
            score += 10 * Math.min(partial_any_word_start_match.length, 9); // partial any word start match
        }
        const partial_start = new RegExp(`^${search_text_regex_ready.split(" ")[0]}`, "g");
        const partial_start_match = index_name_truncated.match(partial_start);
        if (partial_start_match) {
            score += 100; // partial start match
        }
        const full_any_word = new RegExp(`(^| )(${search_text_regex_ready.replaceAll(/\s/g, "|")})( |$)`, "g");
        const full_any_word_match = index_name_truncated.match(full_any_word);
        if (full_any_word_match) {
            score += 1000 * Math.min(full_any_word_match.length, 9); // full any word match
        }
        const full_start_word = new RegExp(`^${search_text_regex_ready.split(" ")[0]}( |$)`, "g")
        const full_start_word_match = index_name_truncated.match(full_start_word);
        if (full_start_word_match) {
            score += 10000; // full word start match
        }
        if (index_name_truncated === search_text_truncated) {
            score += 100000; // entire search exact match
        }

        if (score > 0) {
            possible_results.push({item: search_item, score: score});
        }
    }

    possible_results.sort((a, b) => {return b.score - a.score});

    const search_results = document.querySelectorAll(".search-result");
    for (const search_result of search_results) {
        const result = possible_results.shift();
        search_result.classList.remove("inactive-result");
        search_result.textContent = "";
        search_result.href = "";
        if (!result) {
            search_result.classList.add("inactive-result");
            continue;
        }
        search_result.textContent = result.item.name;
        search_result.href = result.item.path;
    }
}

document.querySelector("#index-page-search").addEventListener("input", update_search);
update_search();
