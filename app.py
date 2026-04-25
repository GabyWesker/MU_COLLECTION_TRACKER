import streamlit as st
import psycopg2
import pandas as pd
import bcrypt
import os

st.set_page_config(page_title="MU Collection Tracker", layout="wide", page_icon="🛡️")

NEON_CONN = st.secrets["NEON_CONN"]

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

def register_user(email, username, password, personaje=""):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute('''
            INSERT INTO usuarios (email, username, password_hash, personaje)
            VALUES (%s, %s, %s, %s)
        ''', (email, username, pwd_hash, personaje))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return str(e)

def get_user_info(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, personaje FROM usuarios WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    except:
        return None, None

def update_personaje(user_id, personaje):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET personaje = %s WHERE id = %s", (personaje, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except:
        return False

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

def add_full(user_id, nombre_set, pieza, kundun, luck, obtiene, enchant, life, sd, dd, dsr, ref, hp, zen):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sets (user_id, nombre_set, pieza, kundun, luck, nivel_bs, add_lif, opt_sd, opt_dd, opt_dsr, opt_ref, opt_hp, opt_zen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, nombre_set, pieza, kundun, bool(luck), enchant, life, bool(sd), bool(dd), bool(dsr), bool(ref), bool(hp), bool(zen)))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DEBUG] ERROR: {e}")
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

def verify_password(plain_pwd, hashed_pwd):
    return bcrypt.checkpw(plain_pwd.encode(), hashed_pwd.encode())

def get_pieza_market(pieza):
    mapeo = {
        "Helm": "Casco",
        "Armor": "Armadura",
        "Pants": "Pantalones",
        "Gloves": "Guantes",
        "Boots": "Botas"
    }
    return mapeo.get(pieza, pieza)

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
    try:
        base_path = os.path.join(os.path.dirname(__file__), "assets")
        if not os.path.exists(base_path):
            return None
        for img in os.listdir(base_path):
            if img.lower().replace(' ', '').replace('.png', '') == set_name.lower().replace(' ', ''):
                return os.path.join(base_path, img)
    except:
        pass
    return None

def load_saved_user(username):
    try:
        filename = f"save_{username}.txt"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return f.read().strip()
    except:
        pass
    return ""

def load_remember_me(username):
    try:
        filename = f"remember_{username}.txt"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return f.read().strip() == "1"
    except:
        pass
    return False

def save_saved_user(username, remember):
    try:
        filename = f"save_{username}.txt"
        with open(filename, "w") as f:
            f.write(username)
        remember_file = f"remember_{username}.txt"
        with open(remember_file, "w") as f:
            f.write("1" if remember else "0")
    except:
        pass

def clear_saved_user(username):
    try:
        filename = f"save_{username}.txt"
        if os.path.exists(filename):
            os.remove(filename)
        remember_file = f"remember_{username}.txt"
        if os.path.exists(remember_file):
            os.remove(remember_file)
    except:
        pass

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'ver_modo' not in st.session_state:
    st.session_state.ver_modo = "Tabla"
if 'filtro' not in st.session_state:
    st.session_state.filtro = "Todos"
if 'filtro_k' not in st.session_state:
    st.session_state.filtro_k = "Todos"
if 'busqueda' not in st.session_state:
    st.session_state.busqueda = ""

if not st.session_state.logged_in:
    tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
    
    with tab_login:
        st.header("🛡️ MU Collection Tracker")
        username = st.text_input("Usuario", placeholder="Tu nombre de usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")
        
        saved_remember = load_remember_me(username) if username else False
        login_remember = st.checkbox("Recordarme", key="chk_remember", value=saved_remember)
        
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
                    
                    if login_remember:
                        save_saved_user(username, True)
                    else:
                        clear_saved_user(username)
                    
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
        reg_personaje = st.text_input("Personaje", placeholder="Nombre de tu personaje MU", key="reg_personaje")
        reg_password = st.text_input("Contraseña", type="password", key="reg_pass")
        reg_confirm = st.text_input("Confirmar Contraseña", type="password", key="reg_confirm")
        
        if st.button("Registrarse", use_container_width=True, key="btn_register"):
            if reg_password != reg_confirm:
                st.error("Las contraseñas no coinciden")
            elif not reg_email or not reg_username or not reg_password:
                st.error("Completa todos los campos")
            else:
                result = register_user(reg_email, reg_username, reg_password, reg_personaje)
                if result is True:
                    st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                else:
                    st.error(f"Error: {result}")
    st.stop()

user_id = st.session_state.user_id

banner_path = os.path.join(os.path.dirname(__file__), "assets", "Banner.png")
if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)

user_info = get_user_info(user_id)
username_logged = user_info[0] if user_info else st.session_state.username
personaje = user_info[1] if user_info else ""

if personaje:
    st.title(f"🛡️ Mi Colección - {personaje}")
else:
    st.title(f"🛡️ Mi Colección - {username_logged}")

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

    m1, m2 = st.columns([2, 1])
    with m1:
        st.metric("Progreso", f"{obtenidos}/{total_items}")
    with m2:
        st.metric("Completado", f"{porcentaje}%")
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

    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    with f1:
        busqueda = st.text_input("🔍 Buscar", st.session_state.busqueda, key="busqueda_input")
        if busqueda.lower() != st.session_state.busqueda:
            st.session_state.busqueda = busqueda.lower()
    with f2:
        filtro_opts = ["Todos", "Pendientes ❌", "Completados ✅"]
        filtro = st.selectbox("Estado:", filtro_opts, index=filtro_opts.index(st.session_state.filtro), key="filtro_select")
        st.session_state.filtro = filtro
    with f3:
        ver_modo_opts = ["Tabla", "Galería"]
        ver_modo = st.selectbox("Ver:", ver_modo_opts, index=ver_modo_opts.index(st.session_state.ver_modo), key="ver_modo_select")
        st.session_state.ver_modo = ver_modo
    with f4:
        filtro_k_opts = ["Todos", "K1", "K2", "K3", "K4", "K5"]
        filtro_k = st.selectbox("K:", filtro_k_opts, index=filtro_k_opts.index(st.session_state.filtro_k), key="filtro_k_select")
        st.session_state.filtro_k = filtro_k

    df_display = df.copy()
    if busqueda:
        mask = df_display.apply(lambda r: busqueda in str(r['nombre_set']).lower() or busqueda in str(r['pieza']).lower(), axis=1)
        df_display = df_display[mask]
    if filtro == "Pendientes ❌":
        df_display = df_display[df_display['obtenido'] == False]
    elif filtro == "Completados ✅":
        df_display = df_display[df_display['obtenido'] == True]
    
    if filtro_k != "Todos":
        k_val = int(filtro_k[1])
        df_display = df_display[df_display['kundun'] == k_val]

if st.session_state.ver_modo == "Tabla":
        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "obtenido": st.column_config.CheckboxColumn("OBTENIDO ✅"),
            "nombre_set": "Set",
            "pieza": "Parte",
            "kundun": st.column_config.NumberColumn("K", min_value=1, max_value=5),
            "luck": st.column_config.CheckboxColumn("L"),
            "nivel_bs": st.column_config.NumberColumn("Enchant", min_value=0, max_value=15),
            "add_lif": st.column_config.NumberColumn("LIFE", min_value=0, max_value=28),
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

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Guardar Progreso", use_container_width=True):
                if save_data(edited_df, user_id):
                    st.success("✅ ¡Datos guardados con éxito!")
                    st.balloons()
                    st.rerun()
        with col2:
            st.link_button("🛒 Ir al Market", "https://mudream.online/market", use_container_width=True)

        with st.expander("🗑️ Eliminar items"):
            if not df_display.empty:
                opciones = [f"{row['id']} - {row['nombre_set']} {row['pieza']}" for _, row in df_display.iterrows()]
                seleccion = st.selectbox("Selecciona item", opciones, key="eliminar_select")
                item_id = int(seleccion.split(" - ")[0])
                if st.button("Eliminar", type="primary", key="btn_eliminar"):
                    if delete_item(item_id, user_id):
                        st.toast("Item eliminado")
                        st.rerun()
    
if st.session_state.ver_modo == "Galería":
    st.divider()
    st.subheader("🖼️ Galería de Sets")

    sets_nombres = list(df_display['nombre_set'].unique())
    for i in range(0, len(sets_nombres), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            s = sets_nombres[i]
            with st.container(border=True):
                c_img, c_info = st.columns([1, 2])
                with c_img:
                    img_path = find_image(s)
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, width=100)
                    else:
                        st.image("https://via.placeholder.com/100?text=?", width=100)
                with c_info:
                    bonus_row = df_premios[df_premios['nombre_set'] == s]
                    bonus_txt = f"🎁 {bonus_row['bonus_desc'].values[0]}" if not bonus_row.empty else "🎁 Bonus: N/A"
                    st.markdown(f"**{s}**")
                    st.caption(bonus_txt)
                    piezas_del_set = df_display[df_display['nombre_set'] == s]
                    for _, p in piezas_del_set.iterrows():
                        icono = "✅" if p['obtenido'] else "❌"
                        k_val = f" | K{int(p['kundun'])}" if p['kundun'] else ""
                        st.write(f"{icono} {p['pieza']}{k_val}")
        
        if i + 1 < len(sets_nombres):
            with col2:
                s = sets_nombres[i + 1]
                with st.container(border=True):
                    c_img, c_info = st.columns([1, 2])
                    with c_img:
                        img_path = find_image(s)
                        if img_path and os.path.exists(img_path):
                            st.image(img_path, width=100)
                        else:
                            st.image("https://via.placeholder.com/100?text=?", width=100)
                    with c_info:
                        bonus_row = df_premios[df_premios['nombre_set'] == s]
                        bonus_txt = f"🎁 {bonus_row['bonus_desc'].values[0]}" if not bonus_row.empty else "🎁 Bonus: N/A"
                        st.markdown(f"**{s}**")
                        st.caption(bonus_txt)
                        piezas_del_set = df_display[df_display['nombre_set'] == s]
                        for _, p in piezas_del_set.iterrows():
                            icono = "✅" if p['obtenido'] else "❌"
                            k_val = f" | K{int(p['kundun'])}" if p['kundun'] else ""
                            st.write(f"{icono} {p['pieza']}{k_val}")

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
    
    with st.expander("👤 Mi Perfil"):
        nuevo_personaje = st.text_input("Personaje MU", value=personaje, key="edit_personaje")
        if st.button("Guardar Personaje", key="btn_guardar_personaje"):
            if update_personaje(user_id, nuevo_personaje):
                st.success("¡Guardado!")
                st.rerun()
        st.caption(f"Cuenta: {username_logged}")
    
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
    
    with st.expander("➕ Añadir Items"):
        c1, c2 = st.columns(2)
        with c1:
            nombre_set_nuevo = st.text_input("Set", key="add_set")
        with c2:
            pieza_nueva = st.selectbox("Pieza", ["Helm", "Armor", "Pants", "Gloves", "Boots"], key="add_pieza")
        
        c3, c4, c5 = st.columns(3)
        with c3:
            kundun_nivel = st.number_input("Kundun", min_value=1, max_value=5, value=1, key="add_k")
        with c4:
            enchant_val = st.number_input("Enchant", min_value=0, max_value=15, value=0, key="add_enchant")
        with c5:
            life_val = st.number_input("Life", min_value=0, max_value=28, value=0, key="add_life")
        
        luck_nuevo = st.checkbox("Luck", key="add_luck")
        
        st.write("Opciones:")
        o1, o2, o3 = st.columns(3)
        sd_val = o1.checkbox("SD", key="opt_sd")
        dd_val = o2.checkbox("DD", key="opt_dd")
        dsr_val = o3.checkbox("DSR", key="opt_dsr")
        
        o4, o5, o6 = st.columns(3)
        hp_val = o4.checkbox("HP", key="opt_hp")
        ref_val = o5.checkbox("REF", key="opt_ref")
        zen_val = o6.checkbox("ZEN", key="opt_zen")
        
        if st.button("➕ Añadir", key="btn_add_item"):
            if nombre_set_nuevo and pieza_nueva:
                luck_v = 1 if luck_nuevo else 0
                obt_v = 0
                sd_v = 1 if sd_val else 0
                dd_v = 1 if dd_val else 0
                dsr_v = 1 if dsr_val else 0
                ref_v = 1 if ref_val else 0
                hp_v = 1 if hp_val else 0
                zen_v = 1 if zen_val else 0
                k_v = int(kundun_nivel)
                e_v = int(enchant_val)
                l_v = int(life_val)
                
                ok = add_full(user_id, nombre_set_nuevo, pieza_nueva, k_v, luck_v, obt_v, e_v, l_v, sd_v, dd_v, dsr_v, ref_v, hp_v, zen_v)
                
                if ok:
                    st.success(f"¡{pieza_nueva} {nombre_set_nuevo} añadido!")
                    st.rerun()
                else:
                    st.error("Error al guardar")
            else:
                st.error("Completa Set y Pieza")
    
    st.divider()
    st.header("📤 Exportar Datos")