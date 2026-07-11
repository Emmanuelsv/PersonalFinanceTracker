from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session

from finanzas.application.use_cases.generar_reporte_semanal import (
    GenerarReporteSemanal,
)
from finanzas.config.settings import settings
from finanzas.infrastructure.db.engine import engine
from finanzas.infrastructure.email.enviador_email_smtp import (
    EnviadorEmailSMTP,
)
from finanzas.infrastructure.repositories.repositorio_categorias_sqlmodel import (
    RepositorioCategoriasSQLModel,
)
from finanzas.infrastructure.repositories.repositorio_movimientos_sqlmodel import (
    RepositorioMovimientosSQLModel,
)


def enviar_reporte_semanal() -> None:
    if not settings.email_to:
        return
    session = Session(engine)
    try:
        repo_mov = RepositorioMovimientosSQLModel(session)
        repo_cat = RepositorioCategoriasSQLModel(session)
        email = EnviadorEmailSMTP()
        use_case = GenerarReporteSemanal(
            repo_movimientos=repo_mov,
            repo_categorias=repo_cat,
            enviador_email=email,
        )
        use_case.ejecutar(email_to=settings.email_to)
    finally:
        session.close()


def iniciar_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        enviar_reporte_semanal,
        trigger="cron",
        day_of_week="sun",
        hour=10,
        minute=0,
    )
    scheduler.start()
    return scheduler
