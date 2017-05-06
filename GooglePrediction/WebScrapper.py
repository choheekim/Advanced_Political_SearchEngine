import os
import urllib
import mysql.connector

from http.cookiejar import CookieJar
from bs4 import BeautifulSoup

CNN_ROOT = "http://www.cnn.com/politics"
CNN_BASE = "http://www.cnn.com"

FOX_ROOT = "http://www.foxnews.com/politics"
FOX_BASE = "http://www.foxnews.com"

FILE_NAME = "../trainingSet/political_training_data.txt"


db = mysql.connector.connect(user='root', password='ly9739ql', database='sentiment_search')
cursor = db.cursor()

cursor.execute("""
                   CREATE TABLE IF NOT EXISTS WebParseUrl (
                                              label VARCHAR(25),
                                              url TEXT)""")


def key_exist_in_web_parse_url(url):
    cursor.execute("""SELECT count(*) FROM WebParseUrl WHERE url = %s""", (url, ))
    result = cursor.fetchall()
    return result[0][0] == 1

def get_count_in_web_parse_url(label):
    cursor.execute("""SELECT count(*) FROM WebParseUrl WHERE label = %s""", (label,))
    result = cursor.fetchall()
    return result[0][0]

def insert_web_parse_url(label, url):
    cursor.execute("""INSERT IGNORE INTO WebParseUrl(label, url)
                        VALUES(%s, %s)""", (label, url))
    db.commit()

def write_to_the_training_set(line):
    if os.path.exists(FILE_NAME):
        print("File already exist")
        with open(FILE_NAME, "+a") as file:
            file.write(line)
            file.write("\n")
    else:
        print("creating file")
        with open(FILE_NAME, "w") as file:
            file.write(line)
            file.write("\n")

class CNNScraper:

    def __init__(self, num_article):
        self.url = set()
        self.num_article = num_article
        self.scanned_url = set()
        self.cur_url = None


    def get_html(self, url):
        html_doc = ""
        try:
            cj = CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)).open(url)
            html_doc = opener.read()
        except urllib.request.HTTPError as inst:
            output = format(inst)
            print(output)
        return html_doc

    def get_soup(self):
        return BeautifulSoup(self.get_html(self.cur_url), 'html.parser')

    def get_href(self):
        print("Current link : " + self.cur_url)
        result = ""

        self.scanned_url.add(self.cur_url)
        html_doc_soup = self.get_soup()
        title = self.get_head_line(html_doc_soup)

        if title is not None and self.is_political_url(self.cur_url):
            content = self.get_content(html_doc_soup)
            result = "\"liberal\"," + "\"" + title + " " + content + "\""

        for link in html_doc_soup.find_all('a'):
            if link.has_attr('href'):
                cur_link = link['href']
                if self.is_valid_url(cur_link):
                    cur_link = CNN_BASE + cur_link
                    if cur_link not in self.scanned_url:
                        self.url.add(cur_link)
        return result

    def is_political_url(self, cur_link):
        return "politics" in cur_link

    def get_head_line(self, html_doc_soup):
        title = html_doc_soup.find('h1', {'class': 'pg-headline'})
        if title is not None:
            title = title.get_text()
        return title

    def get_content(self, html_doc_soup):
        content = ""
        p_paragraphs = html_doc_soup.findAll('p', attrs={'class': 'zn-body__paragraph'})
        for paragraph in p_paragraphs:
            content += paragraph.get_text()
        div_paragraphs = html_doc_soup.findAll('div', attrs={'class': 'zn-body__paragraph'})
        for paragraph in div_paragraphs:
            content += paragraph.get_text()
        content = content.encode('ascii', 'ignore').decode('utf-8')
        content = content.replace("\"", "\"\"")
        return content

    def is_valid_url(self, link):
        if link.startswith('/specials') or (link.startswith('/') and 'politics' in link):
            return True
        else:
            return False

    def scrapping(self):
        while True:
            num_cnn_label = get_count_in_web_parse_url("cnn")
            if num_cnn_label == self.num_article:
                break
            if self.cur_url is None:
                self.cur_url = CNN_ROOT
            else:
                self.cur_url = self.url.pop()
            result = self.get_href()
            if result != "" and not key_exist_in_web_parse_url(self.cur_url):
                insert_web_parse_url("cnn", self.cur_url)
                write_to_the_training_set(result)

class FOXScapper():

    def __init__(self, num_article):
        self.url = set()
        self.num_article = num_article
        self.scanned_url = set()
        self.cur_url = None

    def get_fox_articles(self):
        self.scrapping()
        return self.fox_article

    def get_html(self, url):
        html_doc = ""
        try:
            cj = CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)).open(url)
            html_doc = opener.read()
        except urllib.request.HTTPError as inst:
            output = format(inst)
            print(output)
        return html_doc

    def get_soup(self):
        return BeautifulSoup(self.get_html(self.cur_url), 'html.parser')

    def get_href(self):
        print("Current link : " + self.cur_url)
        html_doc_soup = self.get_soup()
        result = self.get_content(html_doc_soup)

        if result is not None and result != "" and not key_exist_in_web_parse_url(self.cur_url):
            if result != "":
                result = "\"conservative\",\"" + result + "\""
                print(result)
                insert_web_parse_url("fox", self.cur_url)
                write_to_the_training_set(result)

        self.scanned_url.add(self.cur_url)
        for link in html_doc_soup.find_all():
            if link.has_attr('href'):
                if link['href'].startswith("/politics"):
                    cur_link = FOX_BASE + link['href']
                elif link['href'].startswith("http://www.foxnews.com"):
                    cur_link = link['href']
                    if cur_link not in self.scanned_url:
                        print(cur_link)
                        self.url.add(cur_link)

    def get_content(self, html_doc_soup):
        content = ""
        paragraphs = html_doc_soup.find('div', {'class': 'article-text'})
        if paragraphs is not None:
            for paragraph in paragraphs.find_all('p'):
                content += paragraph.get_text()
        content = content.encode('ascii', 'ignore').decode('ascii')
        content = content.replace("\n", " ")
        content = content.replace("\"", "\"\"")
        return content

    def is_valid_url(self, link):
        if link.startswith('/politics') and not link.endswith('print.html'):
            return True
        else:
            return False

    def scrapping(self):
        while True:
            num_fox_label = get_count_in_web_parse_url("fox")
            if num_fox_label == self.num_article:
                break
            if self.cur_url is None:
                self.cur_url = FOX_ROOT
            else:
                self.cur_url = self.url.pop()
            self.get_href()


cnn_data = CNNScraper(700).scrapping()
fox_data = FOXScapper(700).scrapping()



