from urllib import request
from urllib import parse
import json


class TranslationByYoudao:
    def __init__(self):
        pass

    def __del__(self):
        pass

    def translate_on_fanyi_page(self, str_content: str):
        url = "http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule"

        data = {}
        data["i"] = str_content.strip()
        data["to"] = "AUTO"
        data["smartresult"] = "dict"
        data["client"] = "fanyideskweb"
        data["salt"] = "1517200217152"
        data["sign"] = "fc8a26607798294e102f7b4e60cc2686"
        data["doctype"] = "json"
        data["version"] = "2.1"
        data["keyfrom"] = "fanyi.web"
        data["action"] = "FY_BY_CLICKBUTTION"
        data["typoResult"] = "true"
        data = parse.urlencode(data).encode("utf-8")

        req = request.Request(url, data)
        req.add_header("User-Agent",
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36")
        response = request.urlopen(req)
        html = response.read().decode("utf-8")

        target = json.loads(html)
        return target["translateResult"][0][0]["tgt"]

    def translate_on_homepage(self, str_content: str):
        url = "https://www.youdao.com/w/"
        url_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3239.132 Safari/537.36"}

        str_content = str_content.strip().replace("/", "\\").replace(" ", "%20") #  %2F 为URL中符号“/”的转义符，其中 2F 为ASC2 编码
        trans_url = "{0}/{1}".format(url, str_content)
        url_request = request.Request(trans_url, headers=url_header)
        page = str(request.urlopen(url_request).read().decode("utf-8"))

        target = ""
        if page.find('<div id="phrsListTab" class="trans-wrapper clearfix">') != -1:
            target = page[page.find('<div id="phrsListTab" class="trans-wrapper clearfix">'):]
            target = target[target.find('<div class="trans-container">'):]
            if target.find("<!--def end-->") != -1:
                target = target[: target.find("<!--def end-->")]
                target = target[: target.rfind("</span>")]
                target = target[target.rfind("<span"):]
                target = target[target.find(">") + 1:].strip()
            else:
                target = target[:target.find("</div>")]
                target = target[:target.rfind("</li>")]
                target = target[target.find("<li>") + 4:].strip()
        elif page.find('<div id="results-contents" class="results-content">') != -1:
            target = page[page.find('<div id="results-contents" class="results-content">'):]
            if target.find('<div id="fanyiToggle">') != -1:
                target = target[target.find('<div class="trans-container">'):]
                target = target[target.find("<p>") + 3:]
                target = target[target.find("<p>") + 3:]
                target = target[: target.find("</p>")].strip()
            elif target.find('<div class="wt-container">') != -1:
                target = target[target.find('<div class="wt-container">'):]
                target = target[:target.find("</span>")]
                target = target[target.rfind("<span"):]
                target = target[target.find(">") + 1:].strip()
            elif target.find('<div id="webPhrase" class="pr-container more-collapse">') != -1:
                target = target[target.find('<div id="webPhrase" class="pr-container more-collapse">'):]
                target = target[target.find("</span>") + len("</span>"): target.find("</p>")].strip()
            elif target.find('<ul id="tPETrans-all-trans" class="all-trans">') != -1:
                target = target[target.find('<ul id="tPETrans-all-trans" class="all-trans">'):]
                target = target[target.find("<span"): target.find("</span>")]
                target = target[target.find(">") + 1:].strip()

        return target.replace("\n","；").replace("<li>", "").replace("</li>", "").replace(" ", "")
