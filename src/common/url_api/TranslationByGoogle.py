import urllib.request
import urllib.parse
import string


class TranslationByGoogle:
    def __init__(self):
        pass

    def __del__(self):
        pass

    def translate_on_site_cn(self, content_str, lang_from="en", lang_to="zh-CN"):
        # about languages
        lang_from = lang_from.strip()
        lang_to = lang_to.strip()
        support_lang_from = ["auto", "zh-CN", "en"]
        support_lang_to = support_lang_from.copy()
        support_lang_to.remove("auto")
        if lang_from not in ", ".join(support_lang_from):
            print("Error! Language from supports [{0}]".format(",".join(support_lang_from)))
            return
        if lang_to not in ", ".join(support_lang_to):
            print("Error! Language to supports [{0}]".format(",".join(support_lang_to)))
            return

        url_header = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"}
        trans_url = "https://translate.google.cn/m?hl=%s&sl=%s&q=%s" % (lang_to, lang_from, content_str.replace(" ", "%20"))
        trans_url_safe = urllib.parse.quote(trans_url, safe=string.printable)   # if not do this, it will raise error "UnicodeEncodeError: ‘ascii’ codec can’t encode characters in position 10-12: ordinal not in range(128)"

        request = urllib.request.Request(trans_url_safe, headers=url_header)
        page = str(urllib.request.urlopen(request).read().decode("utf-8"))
        flag = 'class="t0">'
        target = page[page.find(flag) + len(flag):]
        target = target.split("<")[0]
        return target
