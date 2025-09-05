import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "").split(",")
PDF_FOLDER = "pdfs"
DATA_FOLDER = "data"