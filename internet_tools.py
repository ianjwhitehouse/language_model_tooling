from typing import List
import urllib3

from bs4 import BeautifulSoup
from bs4.element import Tag

from base_classes import Tool, ToolUseStatus, Model


def get_summary(model, page: Tag, sub_header="h2"):
    tags = page.find_all([sub_header, "p"])

    processed_summary = []
    prompts = []
    cur_section = ""

    # Add prompts or headers to summary to be processed
    for tag in tags:
        if tag.name == sub_header:
            if len(cur_section) > 0:
                processed_summary.append(None)
                prompts.append([
                    {
                        "role": "system",
                        "content": "You are a summarization model that summarizes parts of webpages that a user has asked about.  My next message will be the page snippet.  Please summarize it so that the user can better understand it, while keeping essential information including dates, names, and other information.  Do not preface your summary or mention that you are summarizing."
                    },
                    {
                        "role": "system",
                        "content": "The snippet says %s" % cur_section
                    },
                ])
            processed_summary.append(tag.get_text())
            cur_section = ""
        else:
            cur_section += tag.get_text() + "\n"

    if len(cur_section) > 0:
        processed_summary.append(None)
        prompts.append([
            {
                "role": "system",
                "content": "You are a summarization model that summarizes parts of webpages that a user has asked about.  My next message will be the page snippet.  Please summarize it so that the user can better understand it, while keeping essential information including dates, names, and other information.  Do not preface your summary or mention that you are summarizing."
            },
            {
                "role": "system",
                "content": "The snippet says %s" % cur_section
            },
        ])

    # Run the prompts
    summarized = model.prompt(prompts)

    # Add prompts back to summary
    i = 0
    for j, txt in enumerate(processed_summary):
        if not txt:
            processed_summary[j] = summarized[i]
            print(summarized[i])
            i += 1

    print(processed_summary)

    return "\n".join(processed_summary)


class WikipediaTool(Tool):
    def __init__(self, summary_model:Model=None):
        self.summarizer = summary_model

    def get_name(self,):
        return "WIKI"

    def get_short_description(self,):
        return "Read an article from Wikipedia on millions of topics.  Good for getting factual information on widely-known topics"

    def get_commands(self,):
        return [
            ("GET", "Download and read a wikipedia article", self.get, ("Article topic",)),
        ] + super().get_commands()

    def get(self, args: List[str]):
        try:
            # Download page
            query = "_".join(args)
            req = urllib3.request(
                "GET",
                "https://en.wikipedia.org/wiki/%s" % query,
                headers={"User-Agent": "Chrome", "Accept-Encoding": "UTF-8"}
            ).data.decode("utf-8", errors="ignore")

            if self.summarizer:
                page = get_summary(
                    self.summarizer,
                    BeautifulSoup(req).find_all("div", {"class": "mw-page-container-inner"})[0]
                )
            else:
                page = BeautifulSoup(req).find_all("div", {"class": "mw-page-container-inner"})[0].get_text()
            
            return ToolUseStatus.SUCCEEDED, "The wikipedia page for %s says '%s'" % (query, page)
        except Exception as e:
            return ToolUseStatus.FAILED_REPROMPT, "The Wikipedia page was not returned because of %s" % e
    
    def get_two_examples(self,):
        ex1 = "user: When did the Roman Empire collapse?\nassistant: %WIKI GET Fall of the Western Roman Empire\nsystem: The wikipedia page for Fall_of_the_Western_Roman_Empire says [WIKIPEDIA PAGE]\nnassistant: The Roman Empire fell in 476 AD"

        ex2 = "user: What is Tom Cruise's birthday?\nassistant: %WIKI GET Tom Cruise\nsystem: The wikipedia page for Tom_Cruise says [WIKIPEDIA PAGE]\nnassistant: Tom Cruise's birthday is July 3rd"

        return ex1, ex2


class GoogleTool(Tool):
    def __init__(self, summary_model:Model=None):
        self.links = []
        self.summarizer = summary_model

    def get_name(self,):
        return "GOOGLE"

    def get_short_description(self,):
        return "Search Google and Google Scholar for up-to-date, real time information"

    def get_commands(self,):
        return [
            ("SEARCH", "Search Google to have access to anything on the internet", self.search, ("Topic",)),
            ("SCHOLAR", "Search Google Scholar to see a list of articles about a topic", self.scholar, ("Topic",)),
            ("CLICK", "Click a link from your previous search [ONLY AVALIABLE AFTER SEARCHING]", self.click, ("Link Number",)),
        ] + super().get_commands()

    def search(self, args: List[str]):
        try:
            # Download page
            query = "_".join(args)
            req = urllib3.request(
                "GET",
                "https://google.com/search?q=%s" % query,
                headers={"User-Agent": "Chrome", "Accept-Encoding": "UTF-8"}
            ).data.decode("utf-8", errors="ignore")

            self.links = []
            page = ""
            
            links = BeautifulSoup(req).find_all("a")
            for link in links:
                try:
                    url = "".join(link.attrs["href"].split("=")[1:]).split("&")[0]
                    print(url)
                    url_only_site = url.split("/")[2]
    
                    self.links.append(url)
                    page += "LINK %d: %s (from %s)\n" % (len(self.links), link.get_text(), url_only_site)
                except IndexError:
                    pass
            
            return ToolUseStatus.SUCCEEDED, "The Google Search page for %s says '%s'.  You can call %%GOOGLE CLICK [LINK #] to click on a page" % (query, page)
        except Exception as e:
            return ToolUseStatus.FAILED_REPROMPT, "The Google Search page was not returned because of %s" % e
    
    def scholar(self, args: List[str]):
        try:
            # Download page
            query = "_".join(args)
            req = urllib3.request(
                "GET",
                "https://scholar.google.com/scholar?q=%s" % query,
                headers={"User-Agent": "Chrome", "Accept-Encoding": "UTF-8"}
            ).data.decode("utf-8", errors="ignore")

            self.links = []
            page = ""
            
            papers = BeautifulSoup(req).find_all("div", {"class": "gs_or"})

            for paper in papers:
                title = paper.find_all("h3")[0]
                desc = paper.find_all("div", {"class": "gs_rs"})[0].get_text()
                self.links.append(title.find_all("a")[0].attrs["href"])
                
                page += "LINK #%d: %s\n%s\n\n" % (len(self.links), title.get_text(), desc)
            
            return ToolUseStatus.SUCCEEDED, "The Google Scholar page for %s says '%s'.  You can call %%GOOGLE CLICK [LINK #] to click on a page" % (query, page)
        except Exception as e:
            return ToolUseStatus.FAILED_REPROMPT, "The Google Scholar page was not returned because of %s" % e

    def click(self, args: List[str]):
        try:
            # Download page
            req = urllib3.request(
                "GET",
                self.links[int(args[0]) - 1],
                headers={"User-Agent": "Chrome", "Accept-Encoding": "UTF-8"}
            ).data.decode("utf-8", errors="ignore")

            if self.summarizer:
                page = get_summary(
                    self.summarizer,
                    BeautifulSoup(req).find_all("body")[0],
                    sub_header="asdasdfasdf" # Garbage that isn't a real HTML tag
                )
            else:
                page = BeautifulSoup(req).find_all("body")[0].get_text()

            return ToolUseStatus.SUCCEEDED, "The page at %s says '%s'." % (self.links[int(args[0]) - 1], page)
        except IndexError:
            return ToolUseStatus.FAILED_REPROMPT, "The page was not returned because that was not a valid link"
        except Exception as e:
            return ToolUseStatus.FAILED_REPROMPT, "The page was not returned because of %s" % e
    
    def get_two_examples(self,):
        ex1 = "user: What has Yann LeCun published?\nassistant: %GOOGLE SCHOLAR Yann Lecun\nsystem: The Google Scholar page for Machine says [GS PAGE]\nnassistant: Yann Lecun has published numerous articles, including ones on CNNs and Deep Learning\nuser: Click on one article and summarize it\nassistant: %GOOGLE CLICK 2\nsystem: The link you clicked says [PAGE CONTENTS]\nassistant: This article is about the creation of deep learning"

        ex2 = "user: What is Tom Cruise's birthday?\nassistant: %WIKI GET Tom Cruise\nsystem: The wikipedia page for Tom_Cruise says [WIKIPEDIA PAGE]\nnassistant: Tom Cruise's birthday is July 3rd"

        return ex1, ex2