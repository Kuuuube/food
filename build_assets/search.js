const SEARCH_INDEX = {search_index};

function update_search() {
    const search_text_lowered = document.querySelector("#index-page-search").value.toLowerCase();
    let possible_results = [];
    for (const search_item of SEARCH_INDEX) {
        if (search_text_lowered.length === 0) { break; }
        const index_name_lowered = search_item.name.toLowerCase();
        if (index_name_lowered === search_text_lowered) {
            possible_results.splice(0, 0, search_item);
        } else if (index_name_lowered.includes(search_text_lowered)) {
            possible_results.push(search_item);
        }
    }

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
        search_result.textContent = result.name;
        search_result.href = result.path;
    }
}

document.querySelector("#index-page-search").addEventListener("input", update_search);
update_search();
