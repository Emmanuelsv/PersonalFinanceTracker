from datetime import date
from decimal import Decimal
from uuid import UUID

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlmodel import Session, select

from finanzas.application.services.calculadora_financiera import (
    CalculadoraFinanciera,
)
from finanzas.domain.entities.categoria import Categoria
from finanzas.domain.entities.movimiento import (
    Movimiento,
    TipoMovimiento,
)
from finanzas.domain.value_objects.periodo import Periodo
from finanzas.infrastructure.db.engine import engine

st.set_page_config(page_title="Personal Finance Dashboard", layout="wide")
st.title("Personal Finance Dashboard")

calculadora = CalculadoraFinanciera()


def cargar_movimientos(
    year: int, month: int | None = None
) -> list[Movimiento]:
    session = Session(engine)
    try:
        stmt = select(Movimiento)
        if month:
            periodo = Periodo.for_month(year, month)
            stmt = (
                stmt.where(Movimiento.fecha >= periodo.fecha_inicio)
                .where(Movimiento.fecha <= periodo.fecha_fin)
            )
        else:
            stmt = stmt.where(
                Movimiento.fecha >= date(year, 1, 1)
            ).where(Movimiento.fecha <= date(year, 12, 31))
        stmt = stmt.order_by(Movimiento.fecha)
        return list(session.exec(stmt).all())
    finally:
        session.close()


def cargar_categorias() -> dict[UUID, str]:
    session = Session(engine)
    try:
        return {c.id: c.nombre for c in session.exec(select(Categoria)).all()}
    finally:
        session.close()


def cargar_todos_movimientos() -> list[Movimiento]:
    session = Session(engine)
    try:
        stmt = select(Movimiento).order_by(Movimiento.fecha)
        return list(session.exec(stmt).all())
    finally:
        session.close()


st.sidebar.header("Filters")
today = date.today()
year = st.sidebar.selectbox("Year", range(today.year - 3, today.year + 2), index=3)
month = st.sidebar.selectbox("Month", range(1, 13), index=today.month - 1)

movimientos_mes = cargar_movimientos(year, month)
movimientos_anio = cargar_movimientos(year)
movimientos_todos = cargar_todos_movimientos()
categorias_map = cargar_categorias()

periodo = Periodo.for_month(year, month)
balance = calculadora.calcular_balance_mensual(movimientos_mes, periodo)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Income", f"{balance.total_ingresos}")
col2.metric("Expenses", f"{balance.total_gastos}")
col3.metric("Net Balance", f"{balance.balance_neto}")
tasa_str = f"{balance.tasa_ahorro:.1f}%" if balance.tasa_ahorro is not None else "N/A"
col4.metric("Savings Rate", tasa_str)

st.subheader("Income vs Expenses by Month")
mov_por_mes: dict[tuple[int, int], dict[str, Decimal]] = {}
for m in movimientos_todos:
    key = (m.fecha.year, m.fecha.month)
    if key not in mov_por_mes:
        mov_por_mes[key] = {"income": Decimal("0"), "expenses": Decimal("0")}
    if m.tipo == TipoMovimiento.INGRESO:
        mov_por_mes[key]["income"] += m.valor
    else:
        mov_por_mes[key]["expenses"] += m.valor

df_mensual = pd.DataFrame(
    [
        {
            "Month": f"{k[0]}-{k[1]:02d}",
            "Income": float(v["income"]),
            "Expenses": float(v["expenses"]),
        }
        for k, v in sorted(mov_por_mes.items())
    ]
)
if not df_mensual.empty:
    fig = px.bar(
        df_mensual,
        x="Month",
        y=["Income", "Expenses"],
        title="Monthly Income vs Expenses",
        barmode="group",
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Expenses by Category")
gasto_por_cat = calculadora.gasto_por_categoria(movimientos_mes)
if gasto_por_cat:
    df_cat = pd.DataFrame(
        [
            {
                "Category": categorias_map.get(cat_id, "Unknown"),
                "Amount": float(valor),
            }
            for cat_id, valor in gasto_por_cat.items()
        ]
    )
    fig = px.treemap(
        df_cat,
        path=["Category"],
        values="Amount",
        title="Expense Distribution (Treemap)",
    )
    st.plotly_chart(fig, use_container_width=True)

    df_cat_sorted = df_cat.sort_values("Amount", ascending=True)
    fig2 = px.bar(
        df_cat_sorted,
        y="Category",
        x="Amount",
        title="Expenses by Category",
        orientation="h",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Net Worth Evolution")
mov_por_mes_balance: dict[str, Decimal] = {}
acumulado = Decimal("0")
for m in movimientos_todos:
    key = f"{m.fecha.year}-{m.fecha.month:02d}"
    if key not in mov_por_mes_balance:
        mov_por_mes_balance[key] = Decimal("0")
    if m.tipo == TipoMovimiento.INGRESO:
        mov_por_mes_balance[key] += m.valor
    else:
        mov_por_mes_balance[key] -= m.valor

patrimonio_data: list[dict] = []
for k, v in sorted(mov_por_mes_balance.items()):
    acumulado += v
    patrimonio_data.append({"Month": k, "Net Worth": float(acumulado)})
df_patrimonio = pd.DataFrame(patrimonio_data)
if not df_patrimonio.empty:
    fig = px.line(
        df_patrimonio,
        x="Month",
        y="Net Worth",
        title="Net Worth Evolution",
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Cash Flow")
df_flujo = pd.DataFrame(
    [
        {
            "Date": m.fecha,
            "Amount": float(m.valor) if m.tipo == TipoMovimiento.INGRESO else -float(m.valor),
            "Type": m.tipo.value,
        }
        for m in movimientos_mes
    ]
)
if not df_flujo.empty:
    fig = px.bar(
        df_flujo,
        x="Date",
        y="Amount",
        color="Type",
        title="Daily Cash Flow",
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Category Distribution (%)")
if gasto_por_cat:
    total_gasto = sum(gasto_por_cat.values(), Decimal("0"))
    if total_gasto > 0:
        df_pct = pd.DataFrame(
            [
                {
                    "Category": categorias_map.get(cat_id, "Unknown"),
                    "Percentage": float(valor / total_gasto * 100),
                }
                for cat_id, valor in gasto_por_cat.items()
            ]
        )
        fig = px.bar(
            df_pct,
            x="Category",
            y="Percentage",
            title="Category Distribution (%)",
        )
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Advanced Metrics")
num_categorias = len(gasto_por_cat)
total_prestamos = Decimal("0")
for m in movimientos_mes:
    cat_name = categorias_map.get(m.categoria_id, "")
    if cat_name == "Préstamos" and m.tipo == TipoMovimiento.SALIDA:
        total_prestamos += m.valor
score = calculadora.indice_salud_financiera(balance, num_categorias, total_prestamos)
gasto_fijo_variable = calculadora.gasto_fijo_vs_variable(
    movimientos_mes, set()
)
suscripciones = calculadora.costo_suscripciones(movimientos_todos)

col_a, col_b, col_c = st.columns(3)
col_a.metric("Financial Health Score", f"{score:.0f}/100")
col_b.metric("Subscriptions (monthly avg)", f"{suscripciones:.2f} COP")
col_c.metric("Active Categories", str(num_categorias))

st.subheader("Anomaly Detection")
anomalias = calculadora.detectar_anomalias(
    movimientos_anio, movimientos_mes
)
if anomalias:
    for a in anomalias:
        cat_name = categorias_map.get(a["categoria_id"], "Unknown")
        st.warning(
            f"**{cat_name}**: {a['cambio_pct']:+.1f}% vs average "
            f"({a['actual']:.2f} vs {a['historico']:.2f} COP)"
        )
else:
    st.info("No anomalies detected this month.")

st.subheader("Pending Review — Uncategorized Movements")
sess = Session(engine)
try:
    stmt_pend = (
        select(Movimiento)
        .where(Movimiento.categoria_id.is_(None))
        .order_by(Movimiento.fecha)
    )
    movs_pendientes = list(sess.exec(stmt_pend).all())
except Exception:
    movs_pendientes = []
finally:
    sess.close()

if movs_pendientes:
    for m in movs_pendientes[:10]:
        cols = st.columns([2, 1, 2, 1])
        cols[0].write(f"{m.fecha}")
        cols[1].write(f"{m.tipo.value}")
        cols[2].write(f"{m.valor:.2f}")
        cols[3].write(f"{m.descripcion or ''}")
        with st.expander(f"Assign category to {m.id}"):
            s = Session(engine)
            cat_options = {
                c.nombre: c.id for c in s.exec(select(Categoria)).all()
            }
            s.close()
            selected = st.selectbox(
                "Category", list(cat_options.keys()),
                key=f"cat_{m.id}"
            )
            if st.button("Assign", key=f"btn_{m.id}"):
                s2 = Session(engine)
                try:
                    mov = s2.get(Movimiento, m.id)
                    if mov:
                        mov.categoria_id = cat_options[selected]
                        s2.add(mov)
                        s2.commit()
                        st.success(f"Assigned '{selected}' to movement!")
                        st.rerun()
                finally:
                    s2.close()
    if len(movs_pendientes) > 10:
        st.info(f"... and {len(movs_pendientes) - 10} more uncategorized movements")
else:
    st.success("All movements are categorized!")

st.subheader("Recent Movements")
df_recent = pd.DataFrame(
    [
        {
            "Date": m.fecha,
            "Type": m.tipo.value,
            "Category": categorias_map.get(m.categoria_id, ""),
            "Amount": float(m.valor),
            "Description": m.descripcion or "",
        }
        for m in movimientos_mes[-20:]
    ]
)
if not df_recent.empty:
    st.dataframe(df_recent, use_container_width=True)
