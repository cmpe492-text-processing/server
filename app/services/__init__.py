import tagme
import os
from dotenv import load_dotenv

env_path = ".env"
load_dotenv(dotenv_path=env_path)


api_key = os.getenv("TAGME_API_KEY")
tagme.GCUBE_TOKEN = api_key
