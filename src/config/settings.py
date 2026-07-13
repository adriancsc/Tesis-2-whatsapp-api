"""
Configuración centralizada del sistema MAS-CIS
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None  # Inyectado por Railway
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DB_SERVER: str = "localhost"
    DB_PORT: int = 1433
    DB_NAME: str = "MAS_CIS_DB"
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_TRUSTED_CONNECTION: bool = True  # Default to True for Windows Auth
    
    # WhatsApp Business Cloud API
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_API_VERSION: str = "v21.0"
    WHATSAPP_API_URL: str = "https://graph.facebook.com"
    
    # Application Settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    PORT: Optional[int] = None  # Railway injects this
    DEBUG_MODE: bool = True
    LOG_LEVEL: str = "INFO"
    ADMIN_PHONE: str = ""  # Número al que se enviarán alertas proactivas (ej: +51...)
    
    # Agent Configuration
    AGENT_STORE_TIMEOUT: int = 300  # 5 minutos
    AGENT_COORDINATOR_RETRY: int = 3
    NLU_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Optional: Redis Configuration
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = 6379
    REDIS_DB: Optional[int] = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Google AI Studio (Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a la base de datos"""
        if self.DATABASE_URL:
            # Railway inyecta 'postgresql://', SQLAlchemy necesita 'postgresql+psycopg2://'
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
            return self.DATABASE_URL
            
        if self.DB_DRIVER.lower() == 'sqlite':
            return "sqlite:///./mas_cis.db"
            
        # SQL Server Logic
        if self.DB_TRUSTED_CONNECTION:
            # Windows Authentication (Trusted Connection) using odbc_connect
            import urllib.parse
            connection_string = (
                f"DRIVER={{{self.DB_DRIVER}}};"
                f"SERVER={self.DB_SERVER},{self.DB_PORT};"
                f"DATABASE={self.DB_NAME};"
                f"Trusted_Connection=yes;"
            )
            params = urllib.parse.quote_plus(connection_string)
            return f"mssql+pyodbc:///?odbc_connect={params}"
        else:
            driver = self.DB_DRIVER.replace(' ', '+')
            return (
                f"mssql+pyodbc://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
                f"?driver={driver}"
            )
    
    @property
    def whatsapp_graph_api_url(self) -> str:
        """URL base para WhatsApp Graph API"""
        return f"{self.WHATSAPP_API_URL}/{self.WHATSAPP_API_VERSION}"
    
    @property
    def use_redis(self) -> bool:
        """Verifica si Redis está configurado"""
        return self.REDIS_HOST is not None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
