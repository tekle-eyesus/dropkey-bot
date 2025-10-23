import os
from supabase import create_client, Client
from config import config
import logging

logger = logging.getLogger(__name__)

class SupabaseDatabase:
    def __init__(self):
        self.client: Client = None
        self.is_connected = False
    
    async def connect(self):
        """Connect to Supabase"""
        try:
            if not config.SUPABASE_URL or not config.SUPABASE_KEY:
                logger.warning("Supabase credentials not configured")
                return
            
            self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            
            # Test connection with a simple query
            test_response = self.client.table('users').select('count', count='exact').limit(1).execute()
            logger.info("✅ Connected to Supabase successfully")
            self.is_connected = True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            raise
    
    async def disconnect(self):
        """Supabase client doesn't need explicit disconnection"""
        self.client = None
        self.is_connected = False
    
    def table(self, table_name: str):
        """Access a Supabase table"""
        if not self.is_connected:
            raise ConnectionError("Not connected to Supabase")
        return self.client.table(table_name)

# Global database instance
db = SupabaseDatabase()