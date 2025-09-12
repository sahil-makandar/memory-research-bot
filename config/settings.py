import os

class Config:
    SHORT_TERM_TOKEN_LIMIT = int(os.getenv("SHORT_TERM_TOKEN_LIMIT", "40000"))
    LONG_TERM_FACT_LIMIT = int(os.getenv("LONG_TERM_FACT_LIMIT", "1000"))
    MAX_SUB_QUERIES = int(os.getenv("MAX_SUB_QUERIES", "5"))
    QUERY_TIMEOUT = float(os.getenv("QUERY_TIMEOUT", "30.0"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    BASE_RETRY_DELAY = float(os.getenv("BASE_RETRY_DELAY", "1.0"))
    MAX_RETRY_DELAY = float(os.getenv("MAX_RETRY_DELAY", "60.0"))
    CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    CIRCUIT_BREAKER_TIMEOUT = float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60.0"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/memory.db")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_WORKERS = int(os.getenv("API_WORKERS", "4"))

class DevConfig(Config):
    LOG_LEVEL = "DEBUG"
    MAX_RETRIES = 1
    API_WORKERS = 1

class TestConfig(Config):
    SHORT_TERM_TOKEN_LIMIT = 1000
    LONG_TERM_FACT_LIMIT = 100
    MAX_RETRIES = 1
    QUERY_TIMEOUT = 5.0
    DATABASE_URL = "sqlite:///:memory:"

def get_config(env: str = None):
    env = env or os.getenv("ENVIRONMENT", "production")
    
    if env == "development":
        return DevConfig()
    elif env == "testing":
        return TestConfig()
    else:
        return Config()