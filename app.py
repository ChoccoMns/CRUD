import os
from datetime import date
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

SERVICE_TYPES = [
    "TRANSPORTE",
    "HOSPEDAGEM",
    "PASSAGEM AEREA",
    "SEGURO",
]

AIRLINES = [
    "AIR FRANCE",
    "AMERICAN AIRLINES",
    "AZUL",
    "DELTA",
    "GOL",
    "LATAM AIRLINES",
    "UNITED AIRLINES",
]

COST_CENTERS = [
    "N/A",
    "ADM-RATEIO",
    "FINANCEIRO",
    "G. GERAL",
    "VENDAS",
    "RH",
    "OPS-RATEIO",
]

STATUSES = [
    "CANCELADA",
    "ATENDIDA",
    "EM ABERTO",
]

SUPPLIERS = [
    "LOCARIO",
    "RICKER",
    "MAX MOBILIDADE",
    "RIOMAR",
    "HOTEL ROYAL REGENCY",
    "IBIS BOTAFOGO",
    "COPASTUR",
    "ROYAL ATLANTICA MACAÉ",
    "FOUR POINTS",
    "MONREALE",
]

MONTH_CHOICES: List[Tuple[int, str]] = [
    (1, "01 - Janeiro"),
    (2, "02 - Fevereiro"),
    (3, "03 - Março"),
    (4, "04 - Abril"),
    (5, "05 - Maio"),
    (6, "06 - Junho"),
    (7, "07 - Julho"),
    (8, "08 - Agosto"),
    (9, "09 - Setembro"),
    (10, "10 - Outubro"),
    (11, "11 - Novembro"),
    (12, "12 - Dezembro"),
]


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        st.error("Variável de ambiente DATABASE_URL não configurada.")
        st.stop()
    return create_engine(database_url, pool_pre_ping=True)


def ensure_table(engine: Engine) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS travel_services (
        id SERIAL PRIMARY KEY,
        service_type VARCHAR(32) NOT NULL,
        control VARCHAR(64) NOT NULL,
        issue_date DATE NOT NULL,
        issuer VARCHAR(64) NOT NULL,
        airline VARCHAR(64),
        departure_date DATE,
        month_number SMALLINT NOT NULL,
        origin VARCHAR(64),
        destination VARCHAR(64),
        user_name VARCHAR(64),
        reason TEXT,
        cost_center VARCHAR(32),
        service_cost NUMERIC(12,2) DEFAULT 0,
        fee NUMERIC(12,2) DEFAULT 0,
        total_cost NUMERIC(12,2) GENERATED ALWAYS AS (COALESCE(service_cost,0)+COALESCE(fee,0)) STORED,
        status VARCHAR(32),
        supplier VARCHAR(64),
        nf_issue_date DATE,
        nf_number VARCHAR(64),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def fetch_dataframe(engine: Engine) -> pd.DataFrame:
    query = """
    SELECT
        id, service_type, control, issue_date, issuer, airline,
        departure_date, month_number, origin, destination,
        user_name, reason, cost_center, service_cost, fee,
        total_cost, status, supplier, nf_issue_date, nf_number,
        created_at
    FROM travel_services
    ORDER BY issue_date DESC, id DESC;
    """
    with engine.begin() as conn:
        return pd.read_sql(text(query), conn)


def insert_record(engine: Engine, payload: Dict) -> None:
    stmt = text(
        """
        INSERT INTO travel_services (
            service_type, control, issue_date, issuer, airline,
            departure_date, month_number, origin, destination,
            user_name, reason, cost_center, service_cost, fee,
            status, supplier, nf_issue_date, nf_number
        ) VALUES (
            :service_type, :control, :issue_date, :issuer, :airline,
            :departure_date, :month_number, :origin, :destination,
            :user_name, :reason, :cost_center, :service_cost, :fee,
            :status, :supplier, :nf_issue_date, :nf_number
        );
        """
    )
    with engine.begin() as conn:
        conn.execute(stmt, payload)


def update_record(engine: Engine, record_id: int, payload: Dict) -> None:
    payload["id"] = record_id
    stmt = text(
        """
        UPDATE travel_services SET
            service_type=:service_type,
            control=:control,
            issue_date=:issue_date,
            issuer=:issuer,
            airline=:airline,
            departure_date=:departure_date,
            month_number=:month_number,
            origin=:origin,
            destination=:destination,
            user_name=:user_name,
            reason=:reason,
            cost_center=:cost_center,
            service_cost=:service_cost,
            fee=:fee,
            status=:status,
            supplier=:supplier,
            nf_issue_date=:nf_issue_date,
            nf_number=:nf_number
        WHERE id=:id;
        """
    )
    with engine.begin() as conn:
        conn.execute(stmt, payload)


def delete_records(engine: Engine, ids: List[int]) -> None:
    stmt = text("DELETE FROM travel_services WHERE id = ANY(:ids);")
    with engine.begin() as conn:
        conn.execute(stmt, {"ids": ids})


def pt_month_label(month_number: int) -> str:
    mapping = dict(MONTH_CHOICES)
    return mapping.get(month_number, "")


def month_selectbox(label: str, default_value: int) -> int:
    labels = [choice[1] for choice in MONTH_CHOICES]
    numbers = [choice[0] for choice in MONTH_CHOICES]
    default_index = numbers.index(default_value) if default_value in numbers else 0
    selection = st.selectbox(label, labels, index=default_index)
    return numbers[labels.index(selection)]


def optional_date_input(label: str, value: Optional[date]) -> Optional[date]:
    picker = st.date_input(label, value=value, format="DD/MM/YYYY")
    return picker


def build_payload(
    service_type: str,
    control: str,
    issue_date: date,
    issuer: str,
    airline: str,
    departure_date: Optional[date],
    month_number: int,
    origin: str,
    destination: str,
    user_name: str,
    reason: str,
    cost_center: str,
    service_cost: float,
    fee: float,
    status: str,
    supplier: str,
    nf_issue_date: Optional[date],
    nf_number: str,
) -> Dict:
    return {
        "service_type": service_type,
        "control": control.strip(),
        "issue_date": issue_date,
        "issuer": issuer.strip(),
        "airline": airline or None,
        "departure_date": departure_date,
        "month_number": month_number,
        "origin": origin.strip() or None,
        "destination": destination.strip() or None,
        "user_name": user_name.strip() or None,
        "reason": reason.strip() or None,
        "cost_center": cost_center or None,
        "service_cost": round(service_cost or 0, 2),
        "fee": round(fee or 0, 2),
        "status": status or None,
        "supplier": supplier or None,
        "nf_issue_date": nf_issue_date,
        "nf_number": nf_number.strip() or None,
    }


def show_create_tab(engine: Engine) -> None:
    st.subheader("Cadastrar serviço")
    with st.form("create_form"):
        col1, col2 = st.columns(2)
        with col1:
            service_type = st.selectbox("Tipo de serviço", SERVICE_TYPES)
            control = st.text_input("Controle")
            issue_date = st.date_input(
                "Emissão", value=date.today(), format="DD/MM/YYYY"
            )
            issuer = st.text_input("Emissor")
            airline = st.selectbox("Companhia aérea", [""] + AIRLINES)
            month_number = month_selectbox("Mês (número ↔ nome)", issue_date.month)
            status = st.selectbox("Status", STATUSES)
        with col2:
            departure_date = optional_date_input("Partida / Check-in", None)
            origin = st.text_input("Origem")
            destination = st.text_input("Destino")
            user_name = st.text_input("Usuário")
            reason = st.text_area("Motivo")
            cost_center = st.selectbox("Centro de custo", COST_CENTERS)
            supplier = st.selectbox("Fornecedor", SUPPLIERS)

        service_cost = st.number_input(
            "Custo do serviço (R$)", min_value=0.0, format="%.2f"
        )
        fee = st.number_input("Taxa (R$)", min_value=0.0, format="%.2f")

        col_nf1, col_nf2 = st.columns(2)
        with col_nf1:
            nf_issue_date = optional_date_input("Emissão NF", None)
        with col_nf2:
            nf_number = st.text_input("Nº NF")

        submitted = st.form_submit_button("Salvar registro")
        if submitted:
            if not control.strip():
                st.error("O campo Controle é obrigatório.")
                return
            payload = build_payload(
                service_type,
                control,
                issue_date,
                issuer,
                airline,
                departure_date,
                month_number,
                origin,
                destination,
                user_name,
                reason,
                cost_center,
                service_cost,
                fee,
                status,
                supplier,
                nf_issue_date,
                nf_number,
            )
            try:
                insert_record(engine, payload)
                st.success("Registro salvo com sucesso.")
                st.info(
                    f"Custo total calculado: R$ {payload['service_cost'] + payload['fee']:.2f}"
                )
                st.rerun()
            except SQLAlchemyError as exc:
                st.error(f"Erro ao salvar: {exc.orig if hasattr(exc, 'orig') else exc}")


def show_table_tab(engine: Engine) -> None:
    st.subheader("Consultar serviços")
    data = fetch_dataframe(engine)
    if data.empty:
        st.info("Nenhum registro cadastrado.")
        return

    with st.expander("Filtros opcionais"):
        selected_status = st.multiselect("Status", STATUSES)
        selected_months = st.multiselect(
            "Mês", [choice[1] for choice in MONTH_CHOICES]
        )
        use_issue_filter = st.checkbox("Filtrar por intervalo de emissão", value=False)
        issue_range: Optional[Tuple[date, date]] = None
        if use_issue_filter:
            issue_range = st.date_input(
                "Selecione o intervalo",
                value=(date.today(), date.today()),
                format="DD/MM/YYYY",
                key="filter_issue_range",
            )

    filtered = data.copy()
    if selected_status:
        filtered = filtered[filtered["status"].isin(selected_status)]
    if selected_months:
        month_numbers = [
            choice[0] for choice in MONTH_CHOICES if choice[1] in selected_months
        ]
        filtered = filtered[filtered["month_number"].isin(month_numbers)]
    if issue_range:
        start, end = issue_range
        filtered = filtered[
            (filtered["issue_date"] >= pd.to_datetime(start))
            & (filtered["issue_date"] <= pd.to_datetime(end))
        ]

    if filtered.empty:
        st.warning("Nenhum registro encontrado com os filtros informados.")
        return

    display_df = filtered.copy()
    display_df["issue_date"] = display_df["issue_date"].dt.strftime("%d/%m/%Y")
    display_df["departure_date"] = display_df["departure_date"].dt.strftime(
        "%d/%m/%Y"
    )
    display_df["nf_issue_date"] = display_df["nf_issue_date"].dt.strftime("%d/%m/%Y")
    display_df["month"] = display_df["month_number"].apply(pt_month_label)
    display_df = display_df.drop(columns=["month_number"])
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def show_update_tab(engine: Engine) -> None:
    st.subheader("Atualizar registro")
    data = fetch_dataframe(engine)
    if data.empty:
        st.info("Nenhum registro disponível para edição.")
        return

    record_options = data.apply(
        lambda row: (int(row["id"]), f"{int(row['id'])} · {row['control']}"), axis=1
    ).tolist()
    option_labels = {item[0]: item[1] for item in record_options}

    selected_id = st.selectbox(
        "Selecione o registro",
        options=list(option_labels.keys()),
        format_func=lambda value: option_labels[value],
    )
    row = data[data["id"] == selected_id].iloc[0]

    with st.form("update_form"):
        col1, col2 = st.columns(2)
        with col1:
            service_type = st.selectbox(
                "Tipo de serviço", SERVICE_TYPES, index=SERVICE_TYPES.index(row["service_type"])
            )
            control = st.text_input("Controle", value=row["control"])
            issue_date = st.date_input(
                "Emissão",
                value=row["issue_date"].date(),
                format="DD/MM/YYYY",
            )
            issuer = st.text_input("Emissor", value=row["issuer"])
            airline = st.selectbox(
                "Companhia aérea",
                [""] + AIRLINES,
                index=([""] + AIRLINES).index(row["airline"] or ""),
            )
            month_number = month_selectbox("Mês (número ↔ nome)", int(row["month_number"]))
            status = st.selectbox(
                "Status",
                STATUSES,
                index=STATUSES.index(row["status"]) if row["status"] else 0,
            )
        with col2:
            departure_date = optional_date_input(
                "Partida / Check-in",
                row["departure_date"].date() if pd.notna(row["departure_date"]) else None,
            )
            origin = st.text_input("Origem", value=row["origin"] or "")
            destination = st.text_input("Destino", value=row["destination"] or "")
            user_name = st.text_input("Usuário", value=row["user_name"] or "")
            reason = st.text_area("Motivo", value=row["reason"] or "")
            cost_center = st.selectbox(
                "Centro de custo",
                COST_CENTERS,
                index=COST_CENTERS.index(row["cost_center"]) if row["cost_center"] in COST_CENTERS else 0,
            )
            supplier = st.selectbox(
                "Fornecedor",
                SUPPLIERS,
                index=SUPPLIERS.index(row["supplier"]) if row["supplier"] in SUPPLIERS else 0,
            )

        service_cost = st.number_input(
            "Custo do serviço (R$)",
            min_value=0.0,
            value=float(row["service_cost"] or 0),
            format="%.2f",
        )
        fee = st.number_input(
            "Taxa (R$)",
            min_value=0.0,
            value=float(row["fee"] or 0),
            format="%.2f",
        )

        col_nf1, col_nf2 = st.columns(2)
        with col_nf1:
            nf_issue_date = optional_date_input(
                "Emissão NF",
                row["nf_issue_date"].date() if pd.notna(row["nf_issue_date"]) else None,
            )
        with col_nf2:
            nf_number = st.text_input("Nº NF", value=row["nf_number"] or "")

        submitted = st.form_submit_button("Atualizar registro")
        if submitted:
            payload = build_payload(
                service_type,
                control,
                issue_date,
                issuer,
                airline,
                departure_date,
                month_number,
                origin,
                destination,
                user_name,
                reason,
                cost_center,
                service_cost,
                fee,
                status,
                supplier,
                nf_issue_date,
                nf_number,
            )
            try:
                update_record(engine, selected_id, payload)
                st.success("Registro atualizado.")
                st.info(
                    f"Novo custo total: R$ {payload['service_cost'] + payload['fee']:.2f}"
                )
                st.rerun()
            except SQLAlchemyError as exc:
                st.error(f"Erro ao atualizar: {exc.orig if hasattr(exc, 'orig') else exc}")


def show_delete_tab(engine: Engine) -> None:
    st.subheader("Excluir registros")
    data = fetch_dataframe(engine)
    if data.empty:
        st.info("Nenhum registro disponível para exclusão.")
        return

    ids = data["id"].tolist()
    labels = data.apply(
        lambda row: f"{int(row['id'])} · {row['control']} · {row['service_type']}",
        axis=1,
    ).tolist()
    selection = st.multiselect(
        "Selecione os registros para excluir",
        options=ids,
        format_func=lambda value: labels[ids.index(value)],
    )

    if selection and st.button("Excluir registros selecionados", type="primary"):
        try:
            delete_records(engine, selection)
            st.success(f"{len(selection)} registro(s) excluído(s).")
            st.rerun()
        except SQLAlchemyError as exc:
            st.error(f"Erro ao excluir: {exc.orig if hasattr(exc, 'orig') else exc}")


def main() -> None:
    st.set_page_config(page_title="CRUD Serviços de Viagem", layout="wide")
    st.title("CRUD de Serviços de Viagem")
    st.caption(
        "Gerencie serviços (transporte, hospedagem, passagens e seguros) com integração PostgreSQL."
    )

    engine = get_engine()
    ensure_table(engine)

    tabs = st.tabs(["Cadastrar", "Consultar", "Atualizar", "Excluir"])
    with tabs[0]:
        show_create_tab(engine)
    with tabs[1]:
        show_table_tab(engine)
    with tabs[2]:
        show_update_tab(engine)
    with tabs[3]:
        show_delete_tab(engine)


if __name__ == "__main__":
    main()

