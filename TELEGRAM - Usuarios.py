import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import time as t
from zoneinfo import ZoneInfo

# Configuración de página
st.set_page_config(layout="wide", page_title="Gestión de Destinatarios - Telegram", page_icon="https://www.miaa.mx/favicon.ico")

# --- ESTADO DE SESIÓN ---
if 'user_to_delete' not in st.session_state: st.session_state.user_to_delete = None
if 'active_tab' not in st.session_state: st.session_state.active_tab = "👥 Usuarios Registrados"

zona_mx = ZoneInfo("America/Mexico_City")

# --- CONEXIÓN A BASE DE DATOS ---
@st.cache_resource
def get_engine(): 
    engine_dic = create_engine(
        st.secrets["databases"]["url_dic"],
        pool_pre_ping=True, 
        pool_recycle=1800, 
        pool_timeout=10,
        connect_args={'connect_timeout': 10}
    )
    return engine_dic

ENGINE_DIC = get_engine()

def obtener_datos(query, max_retries=2):
    """Ejecuta consultas con manejo de errores robusto para redes móviles."""
    global ENGINE_DIC
    for intento in range(max_retries):
        try:
            with ENGINE_DIC.connect() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            if intento < max_retries - 1:
                try:
                    ENGINE_DIC.dispose()
                except:
                    pass
                ENGINE_DIC = get_engine()
                t.sleep(1)
            else:
                st.warning("⚠️ No se pudo establecer conexión con el servidor de base de datos de MIAA. Comprueba tu red o VPN.")
                return pd.DataFrame()

def ejecutar_sql(query, params=None, max_retries=2):
    """Ejecuta sentencias SQL con control de errores."""
    global ENGINE_DIC
    for intento in range(max_retries):
        try:
            with ENGINE_DIC.connect() as conn:
                with conn.begin():
                    conn.execute(text(query) if isinstance(query, str) else query, params or {})
            return True
        except Exception as e:
            if intento < max_retries - 1:
                try:
                    ENGINE_DIC.dispose()
                except:
                    pass
                ENGINE_DIC = get_engine()
                t.sleep(1)
            else:
                raise e

# --- ESTILOS CSS PROFESIONALES (BOTONES MÁS JUNTOS Y COMPACTOS) ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important;
        background: radial-gradient(circle at top center, #0F2042 0%, #070D1B 70%);
        color: #FFFFFF;
        max-width: 1200px;
    }
    body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top center, #0F2042 0%, #070D1B 70%);
        color: #FFFFFF;
    }
    
    /* FORZAR 3 COLUMNAS JUNTAS Y COMPACTAS EN MÓVIL Y PC */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important; /* Espacio reducido entre columnas */
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        width: 33.333% !important;
        flex: 1 1 33.333% !important;
        min-width: 0 !important;
        padding-left: 2px !important;
        padding-right: 2px !important;
    }

    .user-card {
        background: linear-gradient(90deg, #1A2A56 0%, #162247 100%);
        border: 1px solid rgba(0, 229, 255, 0.15);
        border-left: 4px solid #00E5FF;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .user-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 229, 255, 0.15);
        border-color: rgba(0, 229, 255, 0.4);
    }
    .stButton>button {
        background: linear-gradient(135deg, #0077B6, #00E5FF);
        color: #070D1B;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.4rem 0.1rem;
        font-size: 0.8rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3);
        width: 100%;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00E5FF, #90E0EF);
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.6);
        color: #070D1B;
    }
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] {
        background-color: #070D1B !important;
        color: #FFFFFF !important;
        border-color: rgba(0, 229, 255, 0.3) !important;
        border-radius: 8px !important;
    }
    .footer-miaa {
        text-align: center;
        color: #8D99AE;
        font-size: 0.85rem;
        margin-top: 3rem;
        border-top: 1px solid rgba(0, 229, 255, 0.1);
        padding-top: 1.5rem;
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA: LOGOTIPO MIAA + TÍTULO ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 4px;">
        <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" 
             style="width: 150px; height: auto; display: inline-block; filter: drop-shadow(0 0 8px rgba(0,229,255,0.3));">
    </div>
""", unsafe_allow_html=True)

col_title_1, col_title_2, col_title_3 = st.columns([1, 6, 1])
with col_title_2:
    st.markdown("""
        <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 1.5rem;">
            <h2 style="color: #00E5FF; margin: 0; font-size: 1.6rem; font-weight: 800; letter-spacing: 0.5px; text-shadow: 0 0 10px rgba(0,229,255,0.3);">Gestión de Usuarios</h2>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32" fill="#00E5FF" style="filter: drop-shadow(0 0 8px rgba(0,229,255,0.4);">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.03-1.99 1.27-5.62 3.72-.53.36-1.01.54-1.44.53-.47-.01-1.38-.27-2.06-.49-.83-.27-1.49-.42-1.43-.88.03-.24.37-.49 1.02-.75 3.98-1.73 6.64-2.87 7.98-3.43 3.8-1.6 4.58-1.88 5.09-1.89.11 0 .37.03.54.17.14.12.18.28.2.4-.02.07-.02.2-.04.33z"/>
            </svg>
        </div>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
df_destinatarios = obtener_datos("SELECT id, nombre, chart_id, activo, departamento FROM Diccionario_telegram")

# --- 3 BOTONES EN 3 COLUMNAS JUNTAS Y COMPACTAS ---
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    if st.button("👥 U. Registrados", key="nav_btn_1"):
        st.session_state.active_tab = "👥 Usuarios Registrados"
        st.rerun()

with col_b2:
    if st.button("➕ Añadir", key="nav_btn_2"):
        st.session_state.active_tab = "➕ Añadir Nuevo"
        st.rerun()

with col_b3:
    if st.button("⚙️ Editar/Elim.", key="nav_btn_3"):
        st.session_state.active_tab = "⚙️ Editar y Eliminar"
        st.rerun()

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ==========================================
# CONTENIDO DE LA PESTAÑA 1: USUARIOS REGISTRADOS
# ==========================================
if st.session_state.active_tab == "👥 Usuarios Registrados":
    st.markdown('<h3 style="color: #00E5FF; margin-top: 10px; font-size: 1.4rem;">📊 Listado General de Destinatarios</h3>', unsafe_allow_html=True)
    
    if not df_destinatarios.empty:
        for _, row_user in df_destinatarios.iterrows():
            estado_badge = '<span style="color: #00FF66; font-weight: 700; text-shadow: 0 0 8px rgba(0,255,102,0.4);">● Activo</span>' if str(row_user['activo']).strip().lower() == 'si' else '<span style="color: #FF3366; font-weight: 700;">● Inactivo</span>'
            st.markdown(f"""
                <div class="user-card">
                    <div>
                        <span style="font-size: 1.15rem; font-weight: bold; color: #FFFFFF;">👤 {row_user['nombre']}</span><br>
                        <span style="color: #00E5FF; font-size: 0.85rem; font-family: monospace;">ID Telegram: {row_user['chart_id']}</span> &nbsp;|&nbsp; 
                        <span style="color: #8D99AE; font-size: 0.9rem;">🏢 {row_user['departamento']}</span>
                    </div>
                    <div>
                        {estado_badge}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No se pudieron cargar los registros de la base de datos.")

# ==========================================
# CONTENIDO DE LA PESTAÑA 2: AÑADIR NUEVO
# ==========================================
elif st.session_state.active_tab == "➕ Añadir Nuevo":
    st.markdown('<h3 style="color: #00E5FF; margin-top: 10px; font-size: 1.4rem;">✨ Registrar Nuevo Destinatario</h3>', unsafe_allow_html=True)
    
    with st.form("form_nuevo_usuario_dinamico_unico"):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            nuevo_nombre = st.text_input("Nombre completo", key="input_nuevo_nombre")
        with f_col2:
            nuevo_chart = st.text_input("Chart ID (Telegram)", key="input_nuevo_chart")
        with f_col3:
            nuevo_depto = st.text_input("Departamento", value="Planeacion Tecnica", key="input_nuevo_depto")
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_crear = st.form_submit_button("🚀 Guardar Nuevo Usuario")
        if btn_crear:
            if nuevo_nombre and nuevo_chart:
                try:
                    df_max_id = obtener_datos("SELECT MAX(CAST(id AS UNSIGNED)) as max_id FROM Diccionario_telegram")
                    siguiente_id = 1
                    if not df_max_id.empty and pd.notnull(df_max_id.iloc[0]['max_id']):
                        siguiente_id = int(df_max_id.iloc[0]['max_id']) + 1
                    
                    nuevo_id_str = f"{siguiente_id:03d}"

                    ejecutar_sql(
                        "INSERT INTO Diccionario_telegram (id, nombre, chart_id, activo, departamento) VALUES (:id, :nombre, :chart_id, 'Si', :depto)",
                        {"id": nuevo_id_str, "nombre": nuevo_nombre, "chart_id": nuevo_chart, "depto": nuevo_depto}
                    )
                    st.success(f"¡Usuario {nuevo_nombre} añadido correctamente con ID {nuevo_id_str}!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al insertar el usuario: {ex}")
            else:
                st.warning("Por favor completa los campos obligatorios (Nombre y Chart ID).")

# ==========================================
# CONTENIDO DE LA PESTAÑA 3: EDITAR Y ELIMINAR
# ==========================================
elif st.session_state.active_tab == "⚙️ Editar y Eliminar":
    st.markdown('<h3 style="color: #00E5FF; margin-top: 10px; font-size: 1.4rem;">🛠️ Gestión, Estados y Eliminación</h3>', unsafe_allow_html=True)
    
    if not df_destinatarios.empty:
        for idx, row_user in df_destinatarios.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style="background: linear-gradient(90deg, #162247 0%, #0F1A36 100%); border: 1px solid rgba(0,229,255,0.15); border-radius: 10px; padding: 12px 18px; margin-bottom: 8px;">
                        <span style="font-weight: bold; color: #FFFFFF; font-size: 1.05rem;">{row_user['nombre']}</span> 
                        <span style="color: #00E5FF; font-size: 0.85rem; font-family: monospace;">(ID: {row_user['chart_id']})</span>
                    </div>
                """, unsafe_allow_html=True)
                
                cols_u = st.columns([4, 2, 2])
                with cols_u[0]:
                    st.markdown(f"<span style='color: #8D99AE; font-size: 0.9rem;'>Depto: <b>{row_user['departamento']}</b></span>", unsafe_allow_html=True)
                with cols_u[1]:
                    actual_val = True if str(row_user['activo']).strip().lower() == 'si' else False
                    nuevo_estado = st.toggle("Activo", value=actual_val, key=f"toggle_user_{row_user['id']}_{idx}")
                    nuevo_str = "Si" if nuevo_estado else "No"
                    if nuevo_str != str(row_user['activo']):
                        try:
                            ejecutar_sql("UPDATE Diccionario_telegram SET activo = :val WHERE id = :uid", {"val": nuevo_str, "uid": row_user['id']})
                            st.toast(f"Actualizado: {row_user['nombre']} -> {nuevo_str}")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error al actualizar: {ex}")
                with cols_u[2]:
                    if st.button("🗑️ Eliminar", key=f"del_user_{row_user['id']}_{idx}"):
                        st.session_state.user_to_delete = row_user['id']
                        st.rerun()
                st.markdown("<hr style='border: 0.5px solid rgba(0,229,255,0.1); margin: 12px 0;'>", unsafe_allow_html=True)
    else:
        st.info("No hay usuarios disponibles para editar o la conexión está inactiva.")

    # Manejo de confirmación de eliminación
    if st.session_state.user_to_delete is not None:
        uid_Target = st.session_state.user_to_delete
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #3A1C1C 0%, #2A0E0E 100%); border: 1px solid #FF3366; padding: 18px; border-radius: 12px; margin-top: 20px; box-shadow: 0 4px 20px rgba(255,51,102,0.3);">
                <h4 style="color: #FF4D6D; margin-top: 0;">⚠️ Advertencia de Eliminación Permanente</h4>
                <p style="color: #FFFFFF;">Estás a punto de eliminar al usuario con ID: <b>{uid_Target}</b>. Esta acción no se puede deshacer.</p>
            </div>
        """, unsafe_allow_html=True)
        
        confirm_text = st.text_input("Para confirmar, escribe la palabra requerida ('delete') en el siguiente campo:", key="input_confirm_delete")
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("Sí, confirmar eliminación", type="primary", key="btn_ejecutar_eliminar_def"):
                if confirm_text.strip().lower() == "delete":
                    try:
                        ejecutar_sql("DELETE FROM Diccionario_telegram WHERE id = :uid", {"uid": uid_Target})
                        st.success("Registro eliminado correctamente de la base de datos.")
                        st.session_state.user_to_delete = None
                        t.sleep(0.5)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al eliminar de la base de datos: {ex}")
                else:
                    st.error("La palabra ingresada no coincide. Escribe 'delete' para confirmar.")
        with c_btn2:
            if st.button("Cancelar", key="btn_cancelar_eliminar_def"):
                st.session_state.user_to_delete = None
                st.rerun()

# --- PIE DE PÁGINA ---
st.markdown("""
    <div class="footer-miaa">
        🔒 Política de privacidad &nbsp;&bull;&nbsp; © 2026 MIAA. Todos los derechos reservados.
    </div>
""", unsafe_allow_html=True)
