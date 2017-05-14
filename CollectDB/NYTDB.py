import requests
from datetime import datetime

FILE_FORMAT = 'json'
PARAMETERS = {"api-key": "5dc531c6bc3849b1ab53e3bf90948810"}


class NYTDatabase:

    def __init__(self, db):
        self.db = db
        self.cursor = self.db.cursor()
        self.create_article_table()
        self.create_article_content_table()
        self.category = {"article": "article", "politics": "politics", "dealbook": "dealbook"}

    def create_article_table(self):
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ARTICLE (
                                            id VARCHAR(255) PRIMARY KEY,
                                            category VARCHAR(255),
                                            snippet TEXT,
                                            pub_date DATE,
                                            url VARCHAR(255) UNIQUE)""")
        self.db.commit()

    def create_article_content_table(self):
        self.cursor.execute("""
                        CREATE TABLE IF NOT EXISTS ArticleContent (
                                                    title TEXT,
                                                    story TEXT,
                                                    articleKey VARCHAR(255),
                                                    FOREIGN KEY(articleKey) REFERENCES ARTICLE (id))""")
        self.db.commit()

    def format_url(self, year, month):
        url = "https://api.nytimes.com/svc/archive/v1/" \
              + str(year) + "/" + str(month) + "." + FILE_FORMAT
        return url

    def archive_parse_json(self, json_file):

        for i in json_file['response']['docs']:
            web_url = str(i['web_url'])
            article_key = str(i['_id'])
            article_snippet = str(i['snippet'])
            article_category = self.find_category(web_url)
            article_section = str(i['section_name'])
            article_date = str(i['pub_date'])[:-1]
            article_subsection = str(i['subsection_name'])

            print(article_date)

            if self.key_exist_in_article(article_key):
                print("Key exist")
                continue

            print(article_date.split("+")[0])

            formatted_date = datetime.strptime(str(article_date.split("+")[0]), "%Y-%m-%dT%H:%M:%S")
            print("\n\nurl : " + web_url)
            print("article section : " + article_section)
            print("article subsection : " + article_subsection)

            if article_category is not None and self.is_valid_url(web_url) \
                    and (article_subsection == 'Politics' or article_section == 'Politics'):
                print("\nSnippet :", article_snippet, "\nurl : ", web_url)
                self.insert_into_article(article_key, article_category, article_snippet, formatted_date, web_url)
            elif "nytimes.com/20" in web_url and "/politics/" in web_url:
                print("\nSnippet :", article_snippet, "\nurl : ", web_url)
                self.insert_into_article(article_key, "politics", article_snippet, formatted_date, web_url)

    def insert_into_article(self, article_key, article_category,  snippet, pub_date, web_url):
        print(web_url)
        self.cursor.execute("""INSERT IGNORE INTO ARTICLE(id, category,  snippet, pub_date,  url)
                                VALUES(%s, %s, %s, %s, %s)""",
                            (article_key,  article_category, snippet, pub_date, web_url))
        self.db.commit()

    def key_exist_in_article(self, id):
        self.cursor.execute("""SELECT count(*) FROM Article WHERE id = %s""", (id,))
        result = self.cursor.fetchall()
        return result[0][0] == 1

    def is_valid_url(self, web_url):
        if not ("nytimes.com/interactive" in web_url or "nytimes.com/slideshow" in web_url
                or "nytimes.com/video"in web_url or "blogs.nytimes.com"in web_url):
            return True
        return False

    def find_category(self, web_url):
        if "nytimes.com/politics" in web_url:
            return self.category["politics"]
        elif "dealbook.nytimes.com" in web_url:
            return self.category["dealbook"]
        elif "nytimes.com/201" in web_url:
            return self.category["article"]
        return None

    def crawl_data(self):
        for year in range(2017, 2018):
            for month in range(4, 5):
                url =self.format_url(year, month)
                response = requests.get(url, params=PARAMETERS)
                self.archive_parse_json(response.json())




