"""
Configuración de conexión a base de datos SQL Server
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator

from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# Crear engine de SQLAlchemy
try:
    print(f"DEBUG: Connecting to {settings.database_url}")
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,  # SQL Server maneja su propio pool
        echo=settings.DEBUG_MODE,
        future=True
    )
    logger.info(f"✅ Conexión a SQL Server configurada: {settings.DB_SERVER}/{settings.DB_NAME}")
except Exception as e:
    logger.error(f"❌ Error al configurar conexión a SQL Server: {e}")
    raise


# Configurar eventos de conexión
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Evento al conectar a la base de datos"""
    logger.debug("Nueva conexión establecida a SQL Server")


@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Evento al cerrar conexión"""
    logger.debug("Conexión cerrada a SQL Server")


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager para obtener sesión de base de datos
    
    Uso:
        with get_db() as db:
            products = db.query(Product).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error en transacción de base de datos: {e}")
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Dependency para FastAPI
    
    Uso en FastAPI:
        @app.get("/products")
        def get_products(db: Session = Depends(get_db_session)):
            return db.query(Product).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
