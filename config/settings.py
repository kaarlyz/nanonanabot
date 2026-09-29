import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "6526833205")
BASE_URL = os.getenv("ROUTER_BASE_URL", "http://127.0.0.1:20128")
DB_PATH = os.getenv("ROUTER_DB_PATH", os.path.expanduser("~/.9router/db/data.sqlite"))
JWT_SECRET_PATH = os.getenv("ROUTER_JWT_PATH", os.path.expanduser("~/.9router/jwt-secret"))
OPENCODE_CONFIG_PATH = os.getenv("OPENCODE_CONFIG_PATH", os.path.expanduser("~/.config/opencode/opencode.json"))
BANNER_IMAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "banner.jpg")
