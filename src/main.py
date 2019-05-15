import requests
from dotenv import load_dotenv
import os
import luigi
import pickle
from google_drive_utils import get_token, upload_media
from instagram_utils import User

# ENV VARIABLE
load_dotenv()
INSTAGRAM_USER_PICKLE = 'instagram_user.pickle'
GOOGLE_TOKEN_PICKLE = 'google_token_pickle'


class LoginInstagram(luigi.ExternalTask):
    """Login to Instagram"""

    def run(self):
        if not os.path.exists(INSTAGRAM_USER_PICKLE):
            self.user = User()
            self.user.save_myself(INSTAGRAM_USER_PICKLE)

    def output(self):
        return luigi.LocalTarget(INSTAGRAM_USER_PICKLE)


class ScrapeInstagram(luigi.ExternalTask):
    """Start scraping - download posts and stories"""
    user = None

    def requires(self):
        return LoginInstagram()

    def run(self):
        with open(self.input().path, 'rb') as p:
            user: User = pickle.load(p)
        user.scrape()

    def output(self):
        return luigi.LocalTarget('fearythanyarat')


class LoginGoogleDrive(luigi.ExternalTask):
    """Login to Google Drive"""

    def requires(self):
        pass

    def run(self):
        pass

    def output(self):
        pass


class UploadToDrive(luigi.ExternalTask):
    """Upload to google drive"""

    def requires(self):
        return (ScrapeInstagram(), LoginGoogleDrive())

    def run(self):
        pass


if __name__ == "__main__":
    luigi.run()
