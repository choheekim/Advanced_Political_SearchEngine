import os

from whoosh.analysis import StemmingAnalyzer
from whoosh import index
from whoosh.fields import *
from whoosh.qparser.default import MultifieldParser
from whoosh.query import Every

from GooglePrediction.GooglePrediction import TrainedModel, PROJECT_ID

schema = Schema(title=TEXT(stored=True),
                content=TEXT(analyzer=StemmingAnalyzer(), stored=True),
                id=ID(stored=True))


class WhooshSearch:

    def __init__(self, db):
        self.db = db
        self.cursor = self.db.cursor()
        self.trainModel = TrainedModel(PROJECT_ID, "political_bias")
        if not os.path.exists("../indexdir"):
            os.mkdir("../indexdir")
            self.idx = index.create_in("../indexdir", schema)
        else:
            self.idx = index.open_dir("../indexdir")

    '''
    Get all urls that are stored in articlecontent table
    '''
    def get_all_article_tables(self):
        self.cursor.execute("SELECT * FROM ArticleContent")
        return self.cursor.fetchall()

    # Check if the file exists
    def data_file_exist(self, id):
        path = "../dataset/" + id + ".txt"
        return os.path.exists(path)

    def write_index(self):
        count = 1
        articles = self.get_all_article_tables()

        for (title, story, articleKey) in articles:

            if not self.data_file_exist(articleKey):
                continue

            article_id = articleKey
            article_title = title

            with open("../dataset/" + article_id + ".txt", 'r') as file:
                article_content = file.read()
            print(str(count) + ". Writing doc" + article_id)

            writer = self.idx.writer()
            writer.add_document(title=article_title,
                                content=article_content,
                                id=article_id)
            writer.commit()
            count += 1

        print('indexing done')


    def search(self, query):
        qp = MultifieldParser(['title', 'content'], schema=self.idx.schema)
        q = qp.parse(query)

        query_result = self.trainModel.predict(query)
        query_label = query_result['outputLabel']
        query_output_list = query_result['outputMulti']
        query_score = float()

        for output in query_output_list:
            if output['label'] == query_label:
                query_score = float(output['score'])

        #print("Query result : " + query_label + "\nQuery score : " + str(query_score))

        with self.idx.searcher() as searcher:
            search_results = searcher.search(q, limit=None)
            article_ids = self.find_matching_political_bias\
                            (search_results, query_label, query_score)

        for article_id in article_ids:
            #print(article_id)
            print(self.get_article_url(article_id))
            print(self.get_article_title(article_id))
            print(self.get_article_snippet(article_id))
            print(self.get_article_date(article_id))


    def find_matching_political_bias(self, search_results, query_label, query_score):
        article_ids = set()
        for result in search_results:
            article_id = result['id']
            article_political_score = self.get_article_political_bias_score(article_id, query_label)
            if article_political_score > (query_score - 0.1) and article_political_score < (query_score + 0.1):
                article_ids.add(result['id'])
        return article_ids


    def get_article_political_bias_score(self, id, query_label):
        if query_label == 'liberal':
            self.cursor.execute("""SELECT liberal_score  FROM ArticlePoliticalCompass WHERE articleKey = %s""", (id,))
            result = self.cursor.fetchall()
            return result[0][0]
        else:
            self.cursor.execute("""SELECT conservative_score  FROM ArticlePoliticalCompass WHERE articleKey = %s""", (id,))
            result = self.cursor.fetchall()
            return result[0][0]

    def get_article_title(self, id):
        self.cursor.execute("""SELECT title  FROM ArticleContent WHERE articleKey = %s""", (id,))
        result = self.cursor.fetchall()
        return result[0][0]

    def get_article(self, id):
        self.cursor.execute("""SELECT *  FROM Article WHERE id = %s""", (id,))
        result = self.cursor.fetchall()
        return result

    def get_article_url(self, id):
        result = self.get_article(id)
        return result[0][4]

    def get_article_date(self, id):
        result = self.get_article(id)
        return result[0][3]

    def get_article_snippet(self, id):
        result = self.get_article(id)
        return result[0][2]








