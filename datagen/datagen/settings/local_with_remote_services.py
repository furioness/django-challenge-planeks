from dotenv import load_dotenv

load_dotenv()


from .heroku import *
from .base import DEBUG, ALLOWED_HOSTS

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

