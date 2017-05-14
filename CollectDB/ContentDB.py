import json

from whoosh import index

from CollectDB.HTMLParser import HTMLParser
from GooglePrediction.GooglePrediction import TrainedModel, PROJECT_ID
from SentimentalSearch.Sentimental_detect import SentimentDetect
import time
import os

from WhooshIndex.Indexer import schema



'''
Content DB creates two table - article content and article sentiment.
Given unique article urls that are stored in Article table, it parse the url and store the title and content as a text file.
The text file is stored under dataset with the name of the unique url.
As parsing the url, it analyzes sentiment level of content and stores in database
'''


class ContentDB:

    def __init__(self, db):
        self.db = db
        self.cursor = self.db.cursor()
        self.html_parser = HTMLParser()
        self.sentiment_detect = SentimentDetect()
        self.create_article_content_table()
        self.create_article_sentiment_table()
        self.create_article_political_compass_table()
        self.trainedModel = TrainedModel(PROJECT_ID, "political_bias")
        if not os.path.exists("../indexdir"):
            os.mkdir("../indexdir")
            self.idx = index.create_in("../indexdir", schema)
        else:
            self.idx = index.open_dir("../indexdir")


    '''
    Create article content table if not exists
    '''
    def create_article_content_table(self):
        self.cursor.execute("""
                           CREATE TABLE IF NOT EXISTS ArticleContent (
                                                       title TEXT,
                                                       articleKey VARCHAR(255) UNIQUE ,
                                                       FOREIGN KEY(articleKey) REFERENCES ARTICLE (id))""")
        self.db.commit()

    '''
    Create articleSentiment table if not exists
    '''
    def create_article_sentiment_table(self):
        self.cursor.execute("""
                           CREATE TABLE IF NOT EXISTS ArticleSentiment (
                                                       sentimentScore FLOAT,
                                                       sentimentMagnitude FLOAT,
                                                       articleKey VARCHAR(255) UNIQUE ,
                                                       FOREIGN KEY(articleKey) REFERENCES ARTICLE (id))""")
        self.db.commit()

    '''
    Get all urls that are stored in article table
    '''
    def get_all_article_tables(self):
        self.cursor.execute("SELECT * FROM ARTICLE")
        return self.cursor.fetchall()

    '''
    Insert data into article content. The article content table has attributes, title and articleKey
    '''
    def insert_data_into_article_content(self, title, article_key):
        self.cursor.execute("""INSERT IGNORE INTO ArticleContent(title, articleKey) VALUES(%s, %s)""",
                            (title, article_key))
        self.db.commit()

    '''
    Insert data into article sentiment table. the table has attributes, sentimentScore, sentimentMagnitude, articleKey
    '''
    def insert_data_into_article_sentiment(self, article_key):

        #assign the path where the content is stored.
        self.sentiment_detect.set_file_name("../dataset/" + article_key + ".txt")

        try:
            #Analyzes sentiment level
            self.sentiment_detect.run_analystics()
            sentiment_score = self.sentiment_detect.get_score()
            sentiment_magnitude = self.sentiment_detect.get_magnitude()
        except Exception as ex:
            print(ex)
            sentiment_score = 0
            sentiment_magnitude = 0

        self.cursor.execute("""INSERT IGNORE INTO ArticleSentiment(sentimentScore, sentimentMagnitude, articleKey)
                                VALUES(%s, %s, %s)""",
                            (sentiment_score, sentiment_magnitude, article_key))
        self.db.commit()

    '''
    Update both tables, articleContent and articleSentiment
    '''
    def update_database(self):
        #Get all unique article keys
        data = self.get_all_article_tables()

        count = 1

        for (id, category, snippet, pub_date, url) in data:

            if not self.key_exist_in_article_content(id):
            #if not self.data_file_exist(id):

                self.html_parser.set_url(url)
                self.html_parser.set_category(category)
                title = self.html_parser.get_title()
                story = self.html_parser.get_story()

                print(id, category, url)
                print(title)
                print(story)

                print(str(count) + ". Writing " + id)

                #writer = self.idx.writer()
                #writer.add_document(title=title,
                 #                   content=story,
                 #                   id=id)
                #writer.commit()
                self.insert_data_into_article_content(title, id)

                if not self.key_exist_in_article_political_compass(id):
                    result = self.trainedModel.predict(story)
                    label = result['outputLabel']
                    print("label : " + result['outputLabel'])

                    outputMulti = result['outputMulti']
                    for output in outputMulti:
                        if output['label'] == 'conservative':
                            conservative_score = output['score']
                        else:
                            liberal_score = output['score']
                    self.insert_article_political_compass(id, label, liberal_score, conservative_score)

                self.wrtie_content_text_file(id, story)
            else:
                print(id + " key already existed")
            if not self.key_exist_in_article_sentiment(id):
                self.insert_data_into_article_sentiment(id)
            count += 1


    def create_article_political_compass_table(self):
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ArticlePoliticalCompass (
                                            liberal_score DOUBLE,
                                            conservative_score DOUBLE,
                                            label VARCHAR(50),
                                            articleKey VARCHAR(255),
                                            FOREIGN KEY(articleKey) REFERENCES ARTICLE (id))""")
        self.db.commit()

    def insert_article_political_compass(self, article_key, label, liberal_score, conservative_score):
        self.cursor.execute("""INSERT IGNORE INTO ArticlePoliticalCompass
                            (liberal_score, conservative_score, label, articleKey)
                            VALUES(%s, %s, %s, %s)""", (liberal_score, conservative_score, label, article_key))
        self.db.commit()

    def key_exist_in_article_political_compass(self, id):
        self.cursor.execute("""SELECT count(*) FROM ArticlePoliticalCompass WHERE articleKey = %s""", (id,))
        result = self.cursor.fetchall()
        return result[0][0] == 1

    #Check if the file exists
    def data_file_exist(self, id):
        path = "../dataset/" + id + ".txt"
        return os.path.exists(path)

    def key_exist_in_article_content(self, id):
        self.cursor.execute("""SELECT count(*) FROM ArticleContent WHERE articleKey = %s""", (id, ))
        result = self.cursor.fetchall()
        return result[0][0] == 1

    def key_exist_in_article_sentiment(self, id):
        self.cursor.execute("""SELECT count(*) FROM ArticleSentiment WHERE articleKey = %s""", (id,))
        result = self.cursor.fetchall()
        return result[0][0] == 1

    def wrtie_content_text_file(self, id, story):
        file = open("../dataset/" + id + ".txt", 'w+')
        print(story)
        file.write(story)
        print("fine has been created")

