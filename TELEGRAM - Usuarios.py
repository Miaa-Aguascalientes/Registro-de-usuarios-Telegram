import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import time as t
from zoneinfo import ZoneInfo

# Configuración de página
st.set_page_config(layout="wide", page_title="Gestión de usuarios", page_icon="https://www.miaa.mx/favicon.ico")

# --- ESTADO DE SESIÓN ---
if 'user_to_delete' not in st.session_state: st.session_state.user_to_delete = None

zona_mx = ZoneInfo("America/Mexico_City")

# --- CONEXIÓN A BASE DE DATOS ---
@st.cache_resource
def get_engine(): 
    engine_dic = create_engine(
        st.secrets["databases"]["url_dic"],
        pool_pre_ping=True, pool_recycle=1800, pool_timeout=30
    )
    return engine_dic

ENGINE_DIC = get_engine()

def obtener_datos(query, max_retries=3):
    """Ejecuta consultas con reintento automático ante desconexiones."""
    global ENGINE_DIC
    for intento in range(max_retries):
        try:
            return pd.read_sql(query, ENGINE_DIC)
        except Exception as e:
            if intento < max_retries - 1:
                try:
                    ENGINE_DIC.dispose()
                except:
                    pass
                ENGINE_DIC = get_engine()
                t.sleep(2)
            else:
                st.error(f"Error de conexión a la base de datos tras varios intentos: {e}")
                return pd.DataFrame()

def ejecutar_sql(query, params=None, max_retries=3):
    """Ejecuta sentencias SQL (INSERT/UPDATE/DELETE) con reconexión automática."""
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
                t.sleep(2)
            else:
                raise e

# --- ESTILOS CSS PROFESIONALES (TEMA OSCURO MIAA) ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important;
        background-color: #070D1B;
        color: #FFFFFF;
        max-width: 1200px;
    }
    body, [data-testid="stAppViewContainer"] {
        background-color: #070D1B;
        color: #FFFFFF;
    }
    .custom-title {
        color: #00E5FF !important; 
        font-size: 2.2rem; 
        font-weight: 800; 
        margin-bottom: 0px; 
        text-align: center; 
        letter-spacing: 0.5px;
    }
    .subtitle-miaa {
        color: #8D99AE;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .section-box {
        background-color: #0F1A36;
        border: 1px solid #1E293B;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    .user-card {
        background-color: #162247;
        border: 1px solid #283861;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0077B6, #00B4D8);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00B4D8, #90E0EF);
        box-shadow: 0 0 12px rgba(0, 180, 216, 0.5);
    }
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] {
        background-color: #0B132B !important;
        color: #FFFFFF !important;
        border-color: #283861 !important;
        border-radius: 8px !important;
    }
    /* Estilo de pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0F1A36;
        padding: 10px;
        border-radius: 12px;
        border: 1px solid #1E293B;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #162247;
        border-radius: 8px;
        color: #8D99AE;
        font-weight: 600;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0077B6, #00B4D8) !important;
        color: #FFFFFF !important;
    }
    .footer-miaa {
        text-align: center;
        color: #8D99AE;
        font-size: 0.85rem;
        margin-top: 3rem;
        border-top: 1px solid #162247;
        padding-top: 1.5rem;
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA ---
col_h1, col_h2, col_h3 = st.columns([1, 3, 1]) 
with col_h2:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 12px;">
            <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" 
                 style="width: 260px; height: auto; display: inline-block;">
        </div>
        <h1 class="custom-title">Gestión de Usuarios</h1>
        <p class="subtitle-miaa">Administra, registra y edita los destinatarios del sistema de alertas</p>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
try:
    df_destinatarios = obtener_datos("SELECT id, nombre, chart_id, activo, departamento FROM Diccionario_telegram")
except:
    df_destinatarios = pd.DataFrame()

# --- PESTAÑAS PRINCIPALES ---
tab_lista, tab_nuevo, tab_editar = st.tabs([
    "👥 Usuarios Registrados", 
    "➕ Añadir Nuevo", 
    "⚙️ Editar y Eliminar"
])

# ==========================================
# PESTAÑA 1: USUARIOS REGISTRADOS
# ==========================================
with tab_lista:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("👥 Listado de Destinatarios Activos")
    
    if not df_destinatarios.empty:
        for _, row_user in df_destinatarios.iterrows():
            estado_badge = '<span style="color: #00FF00; font-weight: 600;">● Activo</span>' if str(row_user['activo']).strip().lower() == 'si' else '<span style="color: #FF4D4D; font-weight: 600;">● Inactivo</span>'
            st.markdown(f"""
                <div class="user-card">
                    <div>
                        <span style="font-size: 1.1rem; font-weight: bold; color: #FFFFFF;">👤 {row_user['nombre']}</span><br>
                        <span style="color: #8D99AE; font-size: 0.9rem;">💬 ID: {row_user['chart_id']} &nbsp;|&nbsp; 🏢 {row_user['departamento']}</span>
                    </div>
                    <div>
                        {estado_badge}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No se encontraron registros en Diccionario_telegram.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PESTAÑA 2: AÑADIR NUEVO DESTINATARIO
# ==========================================
with tab_nuevo:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("➕ Registro de Nuevo Destinatario")
    
    with st.form("form_nuevo_usuario_dinamico_unico"):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            nuevo_nombre = st.text_input("Nombre completo", key="input_nuevo_nombre")
        with f_col2:
            nuevo_chart = st.text_input("Chart ID (Telegram)", key="input_nuevo_chart")
        with f_col3:
            nuevo_depto = st.text_input("Departamento", value="Planeacion Tecnica", key="input_nuevo_depto")
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_crear = st.form_submit_button("Guardar Usuario")
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
                    st.success(f"Usuario {nuevo_nombre} añadido correctamente con ID {nuevo_id_str}.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al insertar el usuario: {ex}")
            else:
                st.warning("Por favor completa los campos obligatorios (Nombre y Chart ID).")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PESTAÑA 3: EDITAR Y ELIMINAR USUARIOS
# ==========================================
with tab_editar:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("⚙️ Control de Edición y Eliminación")
    
    if not df_destinatarios.empty:
        for idx, row_user in df_destinatarios.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style="background-color: #162247; border: 1px solid #283861; border-radius: 10px; padding: 12px 18px; margin-bottom: 10px;">
                        <span style="font-weight: bold; color: #FFFFFF;">{row_user['nombre']}</span> <span style="color: #8D99AE; font-size: 0.85rem;">(ID: {row_user['chart_id']})</span>
                    </div>
                """, unsafe_allow_html=True)
                
                cols_u = st.columns([4, 2, 2])
                with cols_u[0]:
                    st.markdown(f"<span style='color: #8D99AE; font-size: 0.9rem;'>Depto: {row_user['departamento']}</span>", unsafe_allow_html=True)
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
                st.markdown("<hr style='border: 0.5px solid #283861; margin: 10px 0;'>", unsafe_allow_html=True)
    else:
        st.info("No hay usuarios para editar.")

    # Manejo de confirmación de eliminación
    if st.session_state.user_to_delete is not None:
        uid_Target = st.session_state.user_to_delete
        st.markdown(f"""
            <div style="background-color: #3A1C1C; border: 1px solid #E63946; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <h4 style="color: #FF6B6B; margin-top: 0;">⚠️ Confirmación de Eliminación</h4>
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
                        st.success("Registro eliminado correctamente.")
                        st.session_state.user_to_delete = None
                        t.sleep(0.5)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al eliminar de la base de datos: {ex}")
                else:
                    st.error("La palabra ingresada no coincide. Inténtalo de nuevo.")
        with c_btn2:
            if st.button("Cancelar", key="btn_cancelar_eliminar_def"):
                st.session_state.user_to_delete = None
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- PIE DE PÁGINA ---
st.markdown("""
    <div class="footer-miaa">
        🔒 Política de privacidad &nbsp;&bull;&nbsp; © 2026 MIAA. Todos los derechos reservados.
    </div>
""", unsafe_allow_html=True)
