library(httr)
library(jsonlite)
library(rvest)

source("fun.R")
source("credentials.R")

papers <- get_nep("nep-mig")
all_papers_to_slack(papers$content)