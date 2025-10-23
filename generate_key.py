from cryptography.fernet import Fernet

def generate_encryption_key():
    """Generate a secure encryption key"""
    key = Fernet.generate_key()
    print("🔐 Your encryption key (copy this to .env):")
    print(key.decode())
    print("\n⚠️  Keep this key secure! Don't share it or commit to version control.")

if __name__ == "__main__":
    generate_encryption_key()