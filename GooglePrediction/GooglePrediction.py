import json

import httplib2
import mysql.connector

from googleapiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow, GoogleCredentials
from oauth2client import tools

credentials = GoogleCredentials.get_application_default()

with open("../client_secret.json") as json_file:
    data = json.load(json_file)

CLIENT_ID = data["installed"]["client_id"]
CLIENT_SECRET = data["installed"]["client_secret"]
PROJECT_ID = data["installed"]["project_id"]

print(CLIENT_ID + "\n" + CLIENT_SECRET + "\n" + PROJECT_ID)

scope = {'https://www.googleapis.com/auth/devstorage.read_only', 'https://www.googleapis.com/auth/prediction'}

flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, scope)

storage = Storage("credentials.dat")
credentials = storage.get()

if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage)

http = httplib2.Http()
http = credentials.authorize(http)

service = build('prediction', 'v1.6', http=http)
training_set_path = "training_set/political_training_data.txt"


class TrainedModel(object):

    def __init__(self, project_id, model_name):
        self.p = project_id
        self.m = model_name

    def insert(self, storage_data_location=None, output_value=None, features=None):
        body = {
            "storageDataLocation": storage_data_location,
            "id": self.m,
        }
        return service.trainedmodels().insert(body=body, project=self.p).execute()

    # Train a Prediction API model using a dataset
    def insert_dataset(self, training_data):
        body = {
            "id": self.m,
            "trainingInstances": training_data
        }
        return service.trainedmodels().insert(body=body, project=self.p).execute()

    # Check training status of your model
    def get(self):
        return service.trainedmodels().get(project=self.p, id=self.m).execute()

    # Submit model id and request a prediction
    def predict(self, features):
        body = {
            "input": {
                "csvInstance": [features]
            }
        }
        return service.trainedmodels().predict(body=body, id=self.m, project=self.p).execute()

    # List available models
    def list(self):
        return service.trainedmodels().list(project=self.p).execute()

    # Delete a trained model
    def delete(self):
        return service.trainedmodels().delete(project=self.p, id=self.m).execute()

    # Get analysis of the model and the data the model was trained on
    def analyze(self):
        return service.trainedmodels().analyze(project=self.p, id=self.m).execute()

    # Add new data to a trained model
    def update(self, output, features):
        body = {
            "output": output,
            "csvInstance": [
                features
            ]
        }
        return service.trainedmodels().update(project=self.p, id=self.m, body=body).execute()



#trainedModel = TrainedModel(PROJECT_ID, "political_bias")


##Creating model and check if it has been done.
#trainedModel.insert(training_set_path)
'''
while True:
    status = trainedModel.get()
    print(status)
    state = status['trainingStatus']
    print('Training state: ' + state)
    if state == 'DONE':
        break
    elif state == 'RUNNING':
        continue
    else:
        raise Exception('Training Error: ' + state)


'''

