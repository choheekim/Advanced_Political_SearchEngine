import urllib.request
from http.cookiejar import CookieJar
from bs4 import BeautifulSoup

class HTMLParser:

    def __init__(self, url="", category=""):
        self.url = url
        self.category = category
        self.soup = None

    def set_url(self, url):
        self.url = url

    def set_category(self, category):
        self.category = category

    def get_html(self):
        html_doc = ""
        try:
            cj = CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)).open(self.url)
            html_doc = opener.read()
        except urllib.request.HTTPError as inst:
            output = format(inst)
            print(output)
        return html_doc

    def get_soup(self):
        return BeautifulSoup(self.get_html(), 'html.parser')

    def get_title(self):
        title = ""
        if self.category == 'article':
            title = self.get_title_article()
        else:
            title = self.get_title_deadbook_politics()
        return title

    def get_story(self):
        story = ""
        if self.category == 'article':
            story = self.get_story_article()
        else:
            story = self.get_story_deadbook_politics()
        return story.encode('ascii', 'ignore').decode('ascii')

    def get_title_article(self):
        title = None
        for h1 in self.get_soup().find_all('h1'):
            if h1.get('id') is not None and h1['id'] == 'headline':
                title = h1.get_text()
        if title is None:
            for h2 in self.get_soup().find_all('h2'):
                if h2.get('id') is not None and h2['id'] == 'headline':
                    title = h2.get_text()
        return title

    def get_story_article(self):
        content = ""
        for p in self.get_soup().find_all('p'):
                if p.get('class') is not None and 'story-content' in p['class']:
                    content += (p.get_text()+"\n")
        return content

    def get_title_deadbook_politics(self):
        for h1 in self.get_soup().find_all('h1'):
            if h1.get('itemprop') is not None and h1['itemprop'] == 'headline':
                return h1.get_text()

    def get_story_deadbook_politics(self):
        content = ""
        for p in self.get_soup().find_all('p'):
                if p.get('class') is not None and 'story-body-text' in p['class']:
                    content += p.get_text()
        return content




