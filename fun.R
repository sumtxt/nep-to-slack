strip_whitespace <- function(str) {
    if (is.null(str)) {
        return(NA)
    } else {
        str <- gsub("\\s+", " ", str)
        return(trimws(str))
    }
}

# NEP Crawler
get_nep <- function(name) {
    endpoint <- paste0("https://nep.repec.org/", name, "/latest")
    res <- read_html(endpoint)
    update <- html_node(res, "title") |> html_text()
    update <- gsub("nep-mig | papers", "", update)
    tmp <- html_nodes(res, ".coblo_li")
    tmp <- lapply(tmp, parse_nep_item)
    out <- do.call(rbind, tmp)
    out <- list(update = update, content = out)
    return(out)
}

parse_nep_item <- function(li) {
    head <- li |>
        html_nodes("div") |>
        html_node("a")
    title <- head |> html_text()
    url <- head |> html_attr("href")
    data <- li |>
        html_nodes("tr") %>%
        html_text()

    slc_abstract <- lapply(data, function(item) grepl("^Abstract:", item))
    slc_author <- lapply(data, function(item) grepl("^By:", item))
    slc_date <- lapply(data, function(item) grepl("^Date:", item))

    abstract <- strip_whitespace(data[unlist(slc_abstract)])
    if (length(abstract) == 0) {
        abstract <- ""
    } else {
        abstract <- gsub("^Abstract: ", "", abstract)
    }

    author <- strip_whitespace(data[unlist(slc_author)])
    if (length(author) == 0) {
        author <- ""
    } else {
        author <- gsub("^By: ", "", author)
    }

    date <- strip_whitespace(data[unlist(slc_date)])
    if (length(date) == 0) {
        date <- ""
    } else {
        date <- gsub("^Date: ", "", date)
    }

    out <- data.frame(
        title = title,
        authors = author,
        created = date,
        abstract = abstract,
        url = url
    )

    return(out)
}

# Slack Poster
paper_to_slack <- function(paper) {
    response <- POST(
        url = .slack_workflow_trigger_url,
        body = toJSON(paper, auto_unbox = TRUE),
        add_headers(`Content-Type` = "application/json")
    )

    return(response)
}

all_papers_to_slack <- function(papers, wait_in_seconds = 2, rate_limit_per_minute = 10) {
    start_time <- Sys.time()

    N <- nrow(papers)

    for (i in 1:N) {
        cat(".")
        paper <- as.vector(papers[i, ])
        response <- content(paper_to_slack(paper))

        if (response$ok != TRUE) stop("Error in posting to Slack: ", response)

        if (i %% rate_limit_per_minute == 0) {
            elapsed_time <- as.numeric(difftime(Sys.time(), start_time, units = "secs"))
            remaining_time <- max(0, 60 - elapsed_time)
            Sys.sleep(remaining_time)
            start_time <- Sys.time()
        } else {
            Sys.sleep(wait_in_seconds)
        }
    }
}
