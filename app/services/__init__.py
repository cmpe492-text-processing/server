import tagme
from os import getenv

api_key = getenv('TAGME_API_KEY')
tagme.GCUBE_TOKEN = api_key
