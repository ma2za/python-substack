import os

from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

if __name__ == "__main__":
    api = Api(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD"),
        publication_url=os.getenv("PUBLICATION_URL"),
    )

    subscriberCount: int = api.get_publication_subscriber_count()
    print(f"Subscriber count: {subscriberCount}")
