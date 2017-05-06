from google.cloud import language
import argparse
from oauth2client.client import GoogleCredentials

credentials = GoogleCredentials.get_application_default()


class SentimentDetect:

    def __init__(self, filename=""):
        self.filename = filename
        self.sentiment_score = 0.0
        self.sentiment_magnitude = 0.0

    def run_sentiment_text(self):
        """Detects sentiment in the text."""
        language_client = language.Client()

        document = language_client.document_from_text(self.text)
        try :
            sentiment = document.analyze_sentiment().sentiment
            self.score = format(sentiment.score)
            self.magnitude = format(sentiment.magnitude)
        except :
            print("error occured")


        print('Score: {}'.format(self.score))
        print('Magnitude: {}'.format(self.magnitude))

    def set_file_name(self, file_name):
        self.filename = file_name

    def get_score(self):
        return self.score

    def get_magnitude(self):
        return self.magnitude

    def print_result(self, annotations):
        self.score = annotations.sentiment.score
        self.magnitude = annotations.sentiment.magnitude

        for index, sentence in enumerate(annotations.sentences):
            sentence_sentiment = sentence.sentiment.score
            print('Sentence {} has a sentiment score of {}'.format(
                index, sentence_sentiment))

        print('Overall Sentiment: score of {} with magnitude of {}'.format(
            self.score, self.magnitude))
        return 0

    def analyze(self, article_filename):
        """Run a sentiment analysis request on text within a passed filename."""
        language_client = language.Client()

        with open(article_filename, 'r') as review_file:
            # Instantiates a plain text document.
            document = language_client.document_from_html(review_file.read())

            # Detects sentiment in the document.
            annotations = document.annotate_text(include_sentiment=True,
                                                 include_syntax=False,
                                                 include_entities=False)

            # Print the results
            self.print_result(annotations)

    def run_analystics(self):
        self.analyze(self.filename)
