from sqlmodel import Session, select

from finanzas.domain.entities.categoria import Categoria, TipoAsociado
from finanzas.infrastructure.db import models  # noqa: F401
from finanzas.infrastructure.db.engine import crear_tablas, engine

CATEGORIAS: list[dict] = [
    {"nombre": "Transporte", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Comida", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Clases particulares", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Apartamento Niquía", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Booking", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Airbnb", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Servicion de programación", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Ventas", "tipo_asociado": TipoAsociado.INGRESO},

    {"nombre": "Otros ingresos", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Otras salidas", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Acciones", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Indrive", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Didi", "tipo_asociado": TipoAsociado.INGRESO},
    {"nombre": "Uber", "tipo_asociado": TipoAsociado.INGRESO},

    {"nombre": "Ropa", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Regalos", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Plan celular", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Vacaciones", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Préstamos", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Entretenimiento", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Aseo personal", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Carro", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Casa", "tipo_asociado": TipoAsociado.SALIDA},
    {"nombre": "Seguridad social", "tipo_asociado": TipoAsociado.SALIDA},
]


def seed_categorias(session: Session) -> list[Categoria]:
    creadas: list[Categoria] = []
    for data in CATEGORIAS:
        existente = session.exec(
            select(Categoria).where(Categoria.nombre == data["nombre"])
        ).first()
        if not existente:
            cat = Categoria(**data)
            session.add(cat)
            creadas.append(cat)
    session.commit()
    for cat in creadas:
        session.refresh(cat)
    return creadas


if __name__ == "__main__":
    from finanzas.infrastructure.db.engine import crear_tablas, engine

    crear_tablas()
    with Session(engine) as session:
        result = seed_categorias(session)
        print(f"Seeded {len(result)} categories.")
        for cat in result:
            print(f"  - {cat.nombre} ({cat.tipo_asociado.value})")
