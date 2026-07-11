from sqlmodel import Session, SQLModel, create_engine

from finanzas.config.settings import settings

_connect_args: dict = {}
if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    connect_args=_connect_args,
    pool_pre_ping=True,
)


def crear_tablas() -> None:
    SQLModel.metadata.create_all(engine)


def obtener_sesion() -> Session:
    return Session(engine)
