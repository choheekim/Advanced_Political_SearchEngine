from CollectDB.NYTDB import NYTDatabase
from CollectDB.ContentDB import ContentDB
import mysql.connector


db = mysql.connector.connect(user='root', password='ly9739ql', database='sentiment_search')

collectUrl = NYTDatabase(db)

#Collecting articles dataset
#collectUrl.crawl_data()


#Creating file and insert data into articlecontent table
nytdb = ContentDB(db)
nytdb.update_database()
#db.disconnect()

##Creating training data set
#TrainingSet().create_train_data_set()

cursor = db.cursor()

