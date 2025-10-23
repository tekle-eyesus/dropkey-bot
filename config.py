import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    
    # Validate critical environment variables
    @classmethod
    def validate(cls):
        missing = []
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not cls.ENCRYPTION_KEY:
            missing.append("ENCRYPTION_KEY")
        
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    
    # Bot settings
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    DROP_ID_LENGTH = 8

config = Config()