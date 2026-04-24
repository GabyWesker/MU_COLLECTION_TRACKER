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
# --- VISTA VISUAL DE COLECCIONES (CARDS) ---
st.divider()
st.subheader("🖼️ Galería de Trofeos - Sets")

# Obtenemos los nombres únicos de los sets que tenés en la DB
sets_nombres = df['nombre_set'].unique()

# Creamos una cuadrícula de 2 columnas para aprovechar el espacio
for s in sets_nombres:
    with st.container(border=True):
        col_img, col_info = st.columns([1, 2])
        
        with col_img:
            # Buscamos la imagen en la carpeta assets que creaste
            img_path = f"assets/{s}.png"
            try:
                st.image(img_path, use_container_width=True)
            except:
                # Si la imagen no coincide exactamente con el nombre o no existe
                st.image("https://via.placeholder.com/200?text=Sin+Imagen", use_container_width=True)
        
        with col_info:
            # Buscamos el bonus del set en la tabla de premios
            bonus_row = df_premios[df_premios['nombre_set'] == s]
            bonus_txt = f"🎁 Bonus: {bonus_row['bonus_desc'].values[0]}" if not bonus_row.empty else "🎁 Bonus: No definido"
            
            st.markdown(f"### {s}")
            st.caption(bonus_txt)
            
            # Listamos las 5 piezas del set y su estado actual
            piezas_del_set = df[df['nombre_set'] == s]
            for _, p in piezas_del_set.iterrows():
                icono = "✅" if p['obtenido'] else "❌"
                # Agregamos el número de Kundun si ya lo tenés en la base
                k_val = f" | K{int(p['kundun'])}" if 'kundun' in p and p['kundun'] else ""
                st.write(f"{icono} **{p['pieza']}**{k_val}")

# --- BARRA LATERAL: AGREGAR NUEVO SET ---
# --- BARRA LATERAL: AGREGAR PIEZA DETALLADA ---
with st.sidebar:
    st.divider()
    st.header("➕ Gestión de Inventario")
    
    with st.form("nuevo_item_form"):
        st.write("Registrar nueva pieza")
        
        # Datos Básicos
        f_set = st.text_input("Nombre del Set (ej: Bronze)")
        f_pieza = st.selectbox("Pieza", ["Helm", "Armor", "Pants", "Gloves", "Boots", "Weapon", "Shield", "Pendant", "Ring"])
        f_kundun = st.number_input("Nivel de Kundun", min_value=1, max_value=5, value=1)
        
        # Atributos de la Pieza
        col_a, col_b = st.columns(2)
        with col_a:
            f_enchant = st.number_input("Enchant (+0 a +15)", min_value=0, max_value=15, value=0)
            f_luck = st.checkbox("Luck (L)")
        with col_b:
            f_life = st.number_input("Life (+4 a +28)", min_value=0, max_value=28, step=4, value=0)

        # Opciones Excellent
        st.write("--- Opciones Excellent ---")
        c1, c2, c3 = st.columns(3)
        f_sd = c1.checkbox("SD")
        f_dd = c2.checkbox("DD")
        f_dsr = c3.checkbox("DSR")
        
        c4, c5, c6 = st.columns(3)
        f_ref = c4.checkbox("REF")
        f_hp = c5.checkbox("HP")
        f_zen = c6.checkbox("ZEN")
        
        if st.form_submit_button("Añadir al Inventario"):
            if f_set and f_pieza:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sets (
                        nombre_set, pieza, kundun, obtenido, luck, 
                        nivel_bs, add_lif, opt_sd, opt_dd, 
                        opt_dsr, opt_ref, opt_hp, opt_zen
                    ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (f_set, f_pieza, f_kundun, 1 if f_luck else 0, 
                      f_enchant, f_life, 1 if f_sd else 0, 1 if f_dd else 0, 
                      1 if f_dsr else 0, 1 if f_ref else 0, 1 if f_hp else 0, 1 if f_zen else 0))
                conn.commit()
                conn.close()
                st.success(f"¡{f_pieza} {f_set} guardado con éxito!")
                st.rerun()
            else:
                st.error("Faltan datos obligatorios (Set y Pieza).")