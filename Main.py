from CollectDB.NYTDB import NYTDatabase
from CollectDB.ContentDB import ContentDB
import mysql.connector

from WhooshIndex.Indexer import WhooshSearch

db = mysql.connector.connect(user='root', password='ly9739ql', database='sentiment_search')

collectUrl = NYTDatabase(db)

#Collecting articles dataset
#collectUrl.crawl_data()


#Creating file and insert data into articlecontent table
nytdb = ContentDB(db)
#nytdb.update_database()
#db.disconnect()

##Creating training data set
#TrainingSet().create_train_data_set()


#Indexing files
test = WhooshSearch(db)
test.write_index()
#test.search("Politics")


#cursor = db.cursor()

