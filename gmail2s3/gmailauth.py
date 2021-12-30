from simplegmail import Gmail

from gmail2s3.config import GCONFIG


class GmailClient:
    """
    It's assumed that client_secret and gmail_token will be added in the container via secret/configmap
    """

    def __init__(
        self,
        client_secret=GCONFIG.gmail["client_secret"],
        gmail_token=GCONFIG.gmail["gmail_token"],
    ):
        self.client_secret = client_secret
        self.gmail_token = gmail_token
        self._client = None

    def fetch_token(self):
        """Get the token from an object storage"""
        raise NotImplementedError

    def gen_token(self):
        return self.auth()

    def store_token(self):
        """Upload the gmail_token to an object storage"""
        raise NotImplementedError

    def auth(self):
        return Gmail(client_secret_file=self.client_secret, creds_file=self.gmail_token)

    @property
    def client(self):
        """
        Initialize the Gmail client if needed.
        In case the creds_file is None, it will prompt the user to consent access
        """
        if self._client is None:
            self._client = self.auth()
        return self._client
