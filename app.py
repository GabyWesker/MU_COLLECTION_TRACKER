import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="MU Collection Tracker", layout="wide", page_icon="🛡️")

def get_connection():
    return sqlite3.connect('mu_online.db')

def load_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM sets", conn)
    df_premios = pd.read_sql("SELECT * FROM premios_sets", conn)
    conn.close()
    return df, df_premios

# --- HEADER & MÉTRICAS ---
st.title("🛡️ Mi Colección de MU Online")

df, df_premios = load_data()

total_items = len(df)
obtenidos = df['obtenido'].sum()
porcentaje = int((obtenidos / total_items) * 100) if total_items > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total Piezas", total_items)
m2.metric("Obtenidas ✅", obtenidos)
m3.metric("Completado", f"{porcentaje}%")
st.progress(porcentaje / 100)

# --- LÓGICA DE BONUS ACTIVOS ---
sets_completos = []
for s in df['nombre_set'].unique():
    temp_df = df[df['nombre_set'] == s]
    if len(temp_df) > 0 and temp_df['obtenido'].all():
        sets_completos.append(s)

if sets_completos:
    with st.expander("🎁 BONUS ACTIVOS", expanded=True):
        cols = st.columns(2) # Dividimos en 2 columnas para que no sea una lista tan larga
        for i, s in enumerate(sets_completos):
            desc = df_premios[df_premios['nombre_set'] == s]['bonus_desc'].values
            txt = desc[0] if len(desc) > 0 else "Bonus Activado"
            cols[i % 2].success(f"**{s}:** {txt}")

st.divider()

# --- BUSCADOR Y FILTROS ---
f1, f2 = st.columns([2, 1])
with f1:
    busqueda = st.text_input("🔍 Buscar set o pieza...", "").lower()
with f2:
    filtro = st.selectbox("Estado:", ["Todos", "Pendientes ❌", "Completados ✅"])

# Filtrado
df_display = df.copy()
if busqueda:
    mask = df_display.apply(lambda r: busqueda in r['nombre_set'].lower() or busqueda in r['pieza'].lower(), axis=1)
    df_display = df_display[mask]
if filtro == "Pendientes ❌":
    df_display = df_display[df_display['obtenido'] == 0]
elif filtro == "Completados ✅":
    df_display = df_display[df_display['obtenido'] == 1]

# --- TABLA INTERACTIVA ---
column_config = {
    "obtenido": st.column_config.CheckboxColumn("✅"),
    "nombre_set": "Set",
    "pieza": "Parte",
    "luck": st.column_config.CheckboxColumn("L"),
    "nivel_bs": st.column_config.NumberColumn("B/S", min_value=0, max_value=15),
    "add_lif": st.column_config.NumberColumn("LIF", min_value=0, max_value=7),
    "opt_sd": st.column_config.CheckboxColumn("SD"),
    "opt_dd": st.column_config.CheckboxColumn("DD"),
    "opt_dsr": st.column_config.CheckboxColumn("DSR"),
    "opt_ref": st.column_config.CheckboxColumn("REF"),
    "opt_hp": st.column_config.CheckboxColumn("HP"),
    "opt_zen": st.column_config.CheckboxColumn("ZEN"),
}

edited_df = st.data_editor(
    df_display,
    column_config=column_config,
    column_order=["obtenido", "nombre_set", "pieza", "luck", "nivel_bs", "add_lif", "opt_sd", "opt_dd", "opt_dsr", "opt_ref", "opt_hp", "opt_zen"],
    disabled=["nombre_set", "pieza"],
    hide_index=True,
    use_container_width=True,
    key="editor"
)

# --- BOTÓN DE GUARDADO ---
if st.button("💾 Guardar Progreso Actual", use_container_width=True):
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in edited_df.iterrows():
        cursor.execute("""
            UPDATE sets SET obtenido=?, luck=?, nivel_bs=?, add_lif=?, 
            opt_sd=?, opt_dd=?, opt_dsr=?, opt_ref=?, opt_hp=?, opt_zen=?
            WHERE id=?
        """, (row['obtenido'], row['luck'], row['nivel_bs'], row['add_lif'], 
              row['opt_sd'], row['opt_dd'], row['opt_dsr'], row['opt_ref'], 
              row['opt_hp'], row['opt_zen'], row['id']))
    conn.commit()
    conn.close()
    st.toast("¡Datos guardados!")
    st.rerun()