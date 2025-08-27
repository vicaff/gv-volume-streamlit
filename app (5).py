import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, datetime

st.set_page_config(page_title="G&V - Volumes (Toras, Cavaco & Lenha)", layout="wide")

# ----------------------------- Helpers -----------------------------
MESES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
UNITS_BY_TIPO = {"Toras": ["ST"], "Cavaco": ["TN", "m3"], "Lenha": ["ST", "m3", "TN"]}

def to_date(s):
    if isinstance(s, (date, datetime)):
        return pd.to_datetime(s).date()
    try:
        return pd.to_datetime(str(s)).date()
    except Exception:
        return None

def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

# ----------------------------- Seed -----------------------------
SEED_ROWS = [
    # Data, Tipo, Cliente, Unidade, Quantidade, Status
    ["2025-07-25","Toras","Eucamad","ST",3531.49,"ok"],
    ["2025-07-25","Toras","GVP","ST",6118.91,"ok"],
    ["2025-07-25","Toras","Cezan","ST",2547.84,"ok"],
    ["2025-07-25","Toras","Italac","ST",1776.22,"ok"],
    ["2025-07-25","Toras","Cal Oeste","ST",2639.89,"ok"],
    ["2025-07-25","Toras","Plumatex","ST",1212.31,"ok"],
    ["2025-07-25","Toras","Machado","ST",1662.96,"ok"],
    ["2025-07-25","Toras","Miguel e Miguel","ST",140.99,"ok"],
    ["2025-07-25","Toras","Ripack","ST",292.33,"ok"],
    ["2025-07-25","Cavaco","Cereal","TN",5768.16,"ok"],
    ["2025-07-25","Cavaco","Cargill","TN",759.13,"verificando"],
    ["2025-07-25","Cavaco","Bunge Rondonópolis","TN",1377.55,"verificando"],
    ["2025-07-25","Cavaco","Agra","m3",897.23,"ok"],
    ["2025-07-25","Cavaco","McCain","TN",445.14,"ok"],
    ["2025-07-25","Cavaco","Bunge L.","TN",764.57,"ok"],
    ["2025-07-25","Cavaco","Itambé","TN",98.16,"ok"],
    ["2025-07-25","Cavaco","Ebba","TN",276.12,"ok"],
    ["2025-07-25","Cavaco","Goiás Rendereng","TN",34.12,"ok"],
    ["2025-07-25","Lenha","Cliente Lenha (exemplo)","ST",500,"ok"],
]
COLS = ["Data","Tipo","Cliente","Unidade","Quantidade","Status"]

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(SEED_ROWS, columns=COLS)
    st.session_state.df["Data"] = pd.to_datetime(st.session_state.df["Data"]).dt.date

df = st.session_state.df

# ----------------------------- Sidebar -----------------------------
st.sidebar.title("⚙️ Controles")
tipo_sel = st.sidebar.selectbox("Tipo", ["Todos", "Toras", "Cavaco", "Lenha"], index=0)
ano_sel = st.sidebar.number_input("Ano", min_value=2024, max_value=2100, value=2025, step=1)
mes_idx = st.sidebar.selectbox("Mês", list(range(1,13)), index=6, format_func=lambda i: f"{MESES[i-1]} ({i:02d})")

clientes_all = sorted(df["Cliente"].unique().tolist())
cliente_sel = st.sidebar.selectbox("Cliente", ["Todos"] + clientes_all, index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("CSV")
st.sidebar.download_button(
    "⬇️ Exportar CSV (filtrado)",
    data=csv_bytes(df),  # substituído mais abaixo após filtragem real
    file_name="gv_volumes_filtrado.csv",
    mime="text/csv",
    key="dl_placeholder",
    disabled=True,
    help="O botão real de exportação aparece abaixo da tabela principal."
)

# ----------------------------- Título -----------------------------
st.title("📊 Cavaco, Toras & Lenha — Volume Diário (G&V)")

# ----------------------------- Filtros no DataFrame -----------------------------
df_use = df.copy()
df_use["Data"] = pd.to_datetime(df_use["Data"]).dt.date
df_use = df_use[(pd.to_datetime(df_use["Data"]).dt.year == ano_sel) &
                (pd.to_datetime(df_use["Data"]).dt.month == mes_idx)]
if tipo_sel != "Todos":
    df_use = df_use[df_use["Tipo"] == tipo_sel]
if cliente_sel != "Todos":
    df_use = df_use[df_use["Cliente"] == cliente_sel]

# ----------------------------- Gráficos -----------------------------
if df_use.empty:
    st.info("Nenhum registro encontrado com os filtros selecionados.")
else:
    left, right = st.columns(2)

    with left:
        st.subheader("📈 Acumulado do período (mês selecionado)")
        df_sorted = df_use.sort_values("Data").copy()
        df_sorted["Acumulado"] = df_sorted["Quantidade"].cumsum()
        line = alt.Chart(df_sorted).mark_line(point=True).encode(
            x=alt.X("Data:T", title="Data"),
            y=alt.Y("Acumulado:Q", title="Quantidade acumulada"),
            tooltip=COLS + ["Acumulado"]
        )
        st.altair_chart(line, use_container_width=True)

    with right:
        st.subheader("🏆 Ranking por Cliente (mês selecionado)")
        bar = alt.Chart(df_use.groupby("Cliente", as_index=False)["Quantidade"].sum()).mark_bar().encode(
            x=alt.X("Cliente:N", sort="-y"),
            y=alt.Y("Quantidade:Q"),
            tooltip=["Cliente","Quantidade"]
        )
        st.altair_chart(bar, use_container_width=True)

# ----------------------------- CRUD: Lançamentos -----------------------------
st.subheader("📋 Lançamentos do período filtrado")

colA, colB = st.columns([3,1])
with colA:
    st.caption("Edite os valores diretamente na tabela abaixo. As mudanças são salvas em sessão.")
with colB:
    csv_data = csv_bytes(df_use[COLS])
    st.download_button("⬇️ Exportar CSV (filtrado)", data=csv_data, file_name=f"gv_volumes_{ano_sel}-{mes_idx:02d}.csv", mime="text/csv")

edited_df = st.data_editor(
    df_use[COLS],
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Data": st.column_config.DateColumn("Data", format="YYYY-MM-DD"),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Toras","Cavaco","Lenha"]),
        "Unidade": st.column_config.SelectboxColumn("Unidade", options=["ST","TN","m3"]),
        "Status": st.column_config.SelectboxColumn("Status", options=["ok","verificando"]),
        "Quantidade": st.column_config.NumberColumn("Quantidade", step=0.01, min_value=0.0),
    },
    key="editor_filtered",
)

# Sincroniza edições do editor filtrado de volta ao df global por (Data, Tipo, Cliente, Unidade, Quantidade, Status)
# Estratégia: removemos do df global as linhas que pertencem ao filtro atual e substituímos pelas editadas.
def apply_back_to_global(original_global: pd.DataFrame, filtered_original: pd.DataFrame, filtered_edited: pd.DataFrame) -> pd.DataFrame:
    # Normaliza datas
    filtered_original = filtered_original.copy()
    filtered_edited = filtered_edited.copy()
    filtered_original["Data"] = pd.to_datetime(filtered_original["Data"]).dt.date
    filtered_edited["Data"] = pd.to_datetime(filtered_edited["Data"]).dt.date

    # Conjunto que define o período filtrado no global para remoção
    mask_period = (
        (pd.to_datetime(original_global["Data"]).dt.year == ano_sel) &
        (pd.to_datetime(original_global["Data"]).dt.month == mes_idx)
    )
    if tipo_sel != "Todos":
        mask_period &= (original_global["Tipo"] == tipo_sel)
    if cliente_sel != "Todos":
        mask_period &= (original_global["Cliente"] == cliente_sel)

    # Remove período do global
    remaining = original_global.loc[~mask_period].copy()
    # Adiciona editadas
    merged = pd.concat([remaining, filtered_edited[COLS]], ignore_index=True)
    return merged

if st.button("💾 Salvar alterações do período filtrado"):
    st.session_state.df = apply_back_to_global(st.session_state.df, df_use[COLS], edited_df[COLS])
    st.success("Alterações salvas no app (sessão atual).")
    st.rerun()

# ----------------------------- Adicionar novo lançamento -----------------------------
with st.expander("➕ Adicionar novo lançamento"):
    c1, c2, c3 = st.columns(3)
    with c1:
        nova_data = st.date_input("Data", value=date.today())
        novo_tipo = st.selectbox("Tipo do produto", ["Toras","Cavaco","Lenha"], index=0)
    with c2:
        # unidade condicionada ao tipo
        unidades = UNITS_BY_TIPO[novo_tipo]
        nova_unidade = st.selectbox("Unidade", unidades, index=0)
        nova_qtd = st.number_input("Quantidade", min_value=0.0, step=0.01)
    with c3:
        novo_cliente = st.text_input("Cliente")
        novo_status = st.selectbox("Status", ["ok","verificando"], index=0)

    if st.button("Salvar novo lançamento"):
        if novo_cliente.strip() == "":
            st.warning("Informe o nome do cliente.")
        else:
            new_row = {
                "Data": nova_data.strftime("%Y-%m-%d"),
                "Tipo": novo_tipo,
                "Cliente": novo_cliente.strip(),
                "Unidade": nova_unidade,
                "Quantidade": float(nova_qtd),
                "Status": novo_status
            }
            st.session_state.df.loc[len(st.session_state.df)] = new_row
            st.success("Registro adicionado!")
            st.rerun()

# ----------------------------- Importar CSV -----------------------------
st.subheader("📥 Importar CSV")
st.caption("Formato esperado: Data,Tipo,Cliente,Unidade,Quantidade,Status")
file = st.file_uploader("Selecione um arquivo CSV", type=["csv"])
if file is not None:
    try:
        new = pd.read_csv(file)
        # saneamento básico
        new = new[[c for c in COLS if c in new.columns]].copy()
        for c in COLS:
            if c not in new.columns:
                if c == "Quantidade":
                    new[c] = 0.0
                elif c == "Data":
                    new[c] = date.today().strftime("%Y-%m-%d")
                elif c == "Status":
                    new[c] = "ok"
                else:
                    new[c] = ""
        new["Data"] = pd.to_datetime(new["Data"]).dt.date
        new["Quantidade"] = pd.to_numeric(new["Quantidade"], errors="coerce").fillna(0.0)
        new["Status"] = new["Status"].str.lower().where(new["Status"].str.lower().isin(["ok","verificando"]), "ok")

        st.session_state.df = pd.concat([st.session_state.df, new[COLS]], ignore_index=True)
        st.success(f"Importado {len(new)} linha(s)!")
        st.rerun()
    except Exception as e:
        st.error(f"Falha ao importar: {e}")

# ----------------------------- Rodapé -----------------------------
st.markdown("---")
st.caption("POC • G&V • Dados em sessão do Streamlit (não persistem após reiniciar o app). Para persistência real, posso plugar Google Sheets/Firestore.")

