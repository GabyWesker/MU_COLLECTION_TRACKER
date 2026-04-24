import streamlit as st
import psycopg2
import pandas as pd
import bcrypt
import os

st.set_page_config(page_title="MU Collection Tracker", layout="wide", page_icon="🛡️")

NEON_CONN = "postgresql://neondb_owner:npg_D3z2uqPSwdtj@ep-delicate-band-acgfpuaz.sa-east-1.aws.neon.tech/neondb?sslmode=require"

def get_connection():
    return psycopg2.connect(NEON_CONN)

def get_users_for_auth():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, username, password_hash FROM usuarios")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = {}
    for email, username, pwd_hash in users:
        result[username] = {
            'name': username,
            'email': email,
            'password': pwd_hash
        }
    return result

def register_user(email, username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute('''
            INSERT INTO usuarios (email, username, password_hash)
            VALUES (%s, %s, %s)
        ''', (email, username, pwd_hash))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return str(e)

def load_data(user_id):
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM sets WHERE user_id = %s", conn, params=(user_id,))
        df_premios = pd.read_sql("SELECT * FROM premios_sets", conn)
        conn.close()
        return df, df_premios
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

def save_data(edited_df, user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for _, row in edited_df.iterrows():
            cursor.execute("""
                UPDATE sets SET kundun=%s, obtenido=%s, luck=%s, nivel_bs=%s, add_lif=%s, 
                opt_sd=%s, opt_dd=%s, opt_dsr=%s, opt_ref=%s, opt_hp=%s, opt_zen=%s
                WHERE id=%s AND user_id=%s
            """, (row['kundun'], row['obtenido'], row['luck'], row['nivel_bs'], row['add_lif'], 
                  row['opt_sd'], row['opt_dd'], row['opt_dsr'], row['opt_ref'], 
                  row['opt_hp'], row['opt_zen'], row['id'], user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def delete_item(item_id, user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sets WHERE id=%s AND user_id=%s", (item_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False

def export_data(user_id):
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM sets WHERE user_id = %s", conn, params=(user_id,))
        conn.close()
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(f"Error al exportar: {e}")
        return None

def add_item(user_id, f_set, f_pieza, f_kundun, f_enchant, f_luck, f_life, f_sd, f_dd, f_dsr, f_ref, f_hp, f_zen):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sets (user_id, nombre_set, pieza, kundun, obtenido, luck, nivel_bs, add_lif, opt_sd, opt_dd, opt_dsr, opt_ref, opt_hp, opt_zen)
            VALUES (%s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f_set, f_pieza, f_kundun, 1 if f_luck else 0, f_enchant, f_life, 1 if f_sd else 0, 1 if f_dd else 0, 1 if f_dsr else 0, 1 if f_ref else 0, 1 if f_hp else 0, 1 if f_zen else 0))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def create_set_complete(user_id, nombre_set, kundun):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        piezas = ["Helm", "Armor", "Pants", "Gloves", "Boots"]
        for p in piezas:
            cursor.execute("""
                INSERT INTO sets (user_id, nombre_set, pieza, kundun, obtenido)
                VALUES (%s, %s, %s, %s, FALSE)
            """, (user_id, nombre_set, p, kundun))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def find_image(set_name):
    if not os.path.exists('assets'):
        return None
    for img in os.listdir('assets'):
        if img.lower().replace(' ', '').replace('.png', '') == set_name.lower().replace(' ', ''):
            return os.path.join('assets', img)
    return None

def verify_password(plain_pwd, hashed_pwd):
    return bcrypt.checkpw(plain_pwd.encode(), hashed_pwd.encode())

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
    
    with tab_login:
        st.header("🛡️ MU Collection Tracker")
        username = st.text_input("Usuario", placeholder="Tu nombre de usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")
        
        if st.button("Entrar", use_container_width=True, key="btn_login"):
            users = get_users_for_auth()
            if username in users:
                if verify_password(password, users[username]['password']):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
                    user_id = cursor.fetchone()[0]
                    cursor.close()
                    conn.close()
                    
                    st.session_state.user_id = user_id
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
            else:
                st.error("Usuario no encontrado")
    
    with tab_register:
        st.header("Crear Cuenta")
        reg_email = st.text_input("Email", placeholder="tu@email.com", key="reg_email")
        reg_username = st.text_input("Usuario", placeholder="Nombre de usuario", key="reg_user")
        reg_password = st.text_input("Contraseña", type="password", key="reg_pass")
        reg_confirm = st.text_input("Confirmar Contraseña", type="password", key="reg_confirm")
        
        if st.button("Registrarse", use_container_width=True, key="btn_register"):
            if reg_password != reg_confirm:
                st.error("Las contraseñas no coinciden")
            elif not reg_email or not reg_username or not reg_password:
                st.error("Completa todos los campos")
            else:
                result = register_user(reg_email, reg_username, reg_password)
                if result is True:
                    st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                else:
                    st.error(f"Error: {result}")
    st.stop()

user_id = st.session_state.user_id
st.title(f"🛡️ Mi Colección - {st.session_state.username}")

if st.button("Cerrar Sesión"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.rerun()

df, df_premios = load_data(user_id)

if df.empty:
    st.warning("Tu colección está vacía. ¡Añade tu primera pieza!")
else:
    total_items = len(df)
    obtenidos = df['obtenido'].sum()
    porcentaje = int((obtenidos / total_items) * 100) if total_items > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Piezas", total_items)
    m2.metric("Obtenidas ✅", obtenidos)
    m3.metric("Completado", f"{porcentaje}%")
    st.progress(porcentaje / 100)

    sets_completos = []
    for s in df['nombre_set'].unique():
        temp_df = df[df['nombre_set'] == s]
        if len(temp_df) > 0 and temp_df['obtenido'].all():
            sets_completos.append(s)

    if sets_completos:
        with st.expander("🎁 BONUS ACTIVOS", expanded=True):
            cols = st.columns(2)
            for i, s in enumerate(sets_completos):
                desc = df_premios[df_premios['nombre_set'] == s]['bonus_desc'].values
                txt = desc[0] if len(desc) > 0 else "Bonus Activado"
                cols[i % 2].success(f"**{s}:** {txt}")

    st.divider()

    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        busqueda = st.text_input("🔍 Buscar set o pieza...", "").lower()
    with f2:
        filtro = st.selectbox("Estado:", ["Todos", "Pendientes ❌", "Completados ✅"])
    with f3:
        ver_modo = st.selectbox("Ver:", ["Tabla", "Galería"])

    df_display = df.copy()
    if busqueda:
        mask = df_display.apply(lambda r: busqueda in str(r['nombre_set']).lower() or busqueda in str(r['pieza']).lower(), axis=1)
        df_display = df_display[mask]
    if filtro == "Pendientes ❌":
        df_display = df_display[df_display['obtenido'] == False]
    elif filtro == "Completados ✅":
        df_display = df_display[df_display['obtenido'] == True]

    if ver_modo == "Tabla":
        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "obtenido": st.column_config.CheckboxColumn("✅"),
            "nombre_set": "Set",
            "pieza": "Parte",
            "kundun": st.column_config.NumberColumn("K", min_value=1, max_value=5),
            "luck": st.column_config.CheckboxColumn("L"),
            "nivel_bs": st.column_config.NumberColumn("B/S", min_value=0, max_value=15),
            "add_lif": st.column_config.NumberColumn("LIF", min_value=0, max_value=28, step=4),
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
            column_order=["obtenido", "nombre_set", "pieza", "kundun", "luck", "nivel_bs", "add_lif", "opt_sd", "opt_dd", "opt_dsr", "opt_ref", "opt_hp", "opt_zen"],
            disabled=["nombre_set", "pieza", "id"],
            hide_index=True,
            use_container_width=True,
            key="editor"
        )

        if st.button("💾 Guardar Progreso", use_container_width=True):
            if save_data(edited_df, user_id):
                st.toast("¡Datos guardados!")
                st.rerun()

        with st.expander("🗑️ Eliminar items"):
            if not df_display.empty:
                item_to_delete = st.selectbox("Selecciona ID a eliminar", df_display['id'].tolist())
                if st.button("Eliminar", type="primary"):
                    if delete_item(item_to_delete, user_id):
                        st.toast("Item eliminado")
                        st.rerun()
    else:
        sets_nombres = df_display['nombre_set'].unique()
        for s in sets_nombres:
            with st.container(border=True):
                col_img, col_info = st.columns([1, 2])
                
                with col_img:
                    img_path = find_image(s)
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/200?text=Sin+Imagen", use_container_width=True)
                
                with col_info:
                    bonus_row = df_premios[df_premios['nombre_set'] == s]
                    bonus_txt = f"🎁 Bonus: {bonus_row['bonus_desc'].values[0]}" if not bonus_row.empty else "🎁 Bonus: No definido"
                    
                    st.markdown(f"### {s}")
                    st.caption(bonus_txt)
                    
                    piezas_del_set = df_display[df_display['nombre_set'] == s]
                    for _, p in piezas_del_set.iterrows():
                        icono = "✅" if p['obtenido'] else "❌"
                        k_val = f" | K{int(p['kundun'])}" if p['kundun'] else ""
                        st.write(f"{icono} **{p['pieza']}**{k_val}")

    st.divider()
    st.subheader("🖼️ Galería de Sets")

    sets_nombres = df_display['nombre_set'].unique()
    for s in sets_nombres:
        with st.container(border=True):
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                img_path = find_image(s)
                if img_path and os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/200?text=Sin+Imagen", use_container_width=True)
            
            with col_info:
                bonus_row = df_premios[df_premios['nombre_set'] == s]
                bonus_txt = f"🎁 Bonus: {bonus_row['bonus_desc'].values[0]}" if not bonus_row.empty else "🎁 Bonus: No definido"
                
                st.markdown(f"### {s}")
                st.caption(bonus_txt)
                
                piezas_del_set = df_display[df_display['nombre_set'] == s]
                for _, p in piezas_del_set.iterrows():
                    icono = "✅" if p['obtenido'] else "❌"
                    k_val = f" | K{int(p['kundun'])}" if p['kundun'] else ""
                    st.write(f"{icono} **{p['pieza']}**{k_val}")

    st.divider()

    with st.expander("📤 Exportar Datos"):
        if st.button("Descargar CSV"):
            csv_data = export_data(user_id)
            if csv_data:
                st.download_button(
                    label="Descargar mi colección (CSV)",
                    data=csv_data,
                    file_name="mi_coleccion_mu.csv",
                    mime="text/csv"
                )

with st.sidebar:
    st.divider()
    
    with st.expander("➕ Crear Set Completo"):
        with st.form("nuevo_set_form"):
            st.write("Añadir 5 piezas de un set")
            nombre_nuevo = st.text_input("Nombre del Set", key="input_set_nombre")
            k_nuevo = st.number_input("Nivel de Kundun", min_value=1, max_value=5, value=1, key="input_kundun")
            
            if st.form_submit_button("Crear Set"):
                if nombre_nuevo:
                    if create_set_complete(user_id, nombre_nuevo, k_nuevo):
                        st.success(f"Set {nombre_nuevo} creado!")
                        st.rerun()
                else:
                    st.error("Poné un nombre para el set.")
    
    st.divider()
    st.header("➕ Gestión de Inventario")
    
    with st.form("nuevo_item_form"):
        st.write("Registrar nueva pieza")
        
        f_set = st.text_input("Nombre del Set", key="input_item_set")
        f_pieza = st.selectbox("Pieza", ["Helm", "Armor", "Pants", "Gloves", "Boots"], key="input_item_pieza")
        f_kundun = st.number_input("Nivel de Kundun", min_value=1, max_value=5, value=1, key="input_item_kundun")
        
        col_a, col_b = st.columns(2)
        with col_a:
            f_enchant = st.number_input("Enchant (+0 a +15)", min_value=0, max_value=15, value=0, key="input_enchant")
            f_luck = st.checkbox("Luck (L)", key="input_luck")
        with col_b:
            f_life = st.number_input("Life (+4 a +28)", min_value=0, max_value=28, step=4, value=0, key="input_life")

        st.write("--- Opciones Excellent ---")
        c1, c2, c3 = st.columns(3)
        f_sd = c1.checkbox("SD", key="opt_sd")
        f_dd = c2.checkbox("DD", key="opt_dd")
        f_dsr = c3.checkbox("DSR", key="opt_dsr")
        
        c4, c5, c6 = st.columns(3)
        f_ref = c4.checkbox("REF", key="opt_ref")
        f_hp = c5.checkbox("HP", key="opt_hp")
        f_zen = c6.checkbox("ZEN", key="opt_zen")
        
        if st.form_submit_button("Añadir al Inventario"):
            if f_set and f_pieza:
                if add_item(user_id, f_set, f_pieza, f_kundun, f_enchant, f_luck, f_life, f_sd, f_dd, f_dsr, f_ref, f_hp, f_zen):
                    st.success(f"¡{f_pieza} {f_set} guardado!")
                    st.rerun()
            else:
                st.error("Faltan datos obligatorios (Set y Pieza).")