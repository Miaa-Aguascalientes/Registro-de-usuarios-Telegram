import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import time as t
from zoneinfo import ZoneInfo

# Configuración de página
st.set_page_config(layout="wide", page_title="Registro de usuarios", page_icon="https://www.miaa.mx/favicon.ico")

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
        padding-top: 1.5rem !important; 
        padding-bottom: 2rem !important;
        background-color: #0B132B;
        color: #FFFFFF;
    }
    body, [data-testid="stAppViewContainer"] {
        background-color: #0B132B;
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
    .card-container {
        background-color: #1C2541;
        border: 1px solid #3A506B;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
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
        border-color: #3A506B !important;
        border-radius: 8px !important;
    }
    .footer-miaa {
        text-align: center;
        color: #8D99AE;
        font-size: 0.85rem;
        margin-top: 3rem;
        border-top: 1px solid #1C2541;
        padding-top: 1rem;
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA ---
col_h1, col_h2, col_h3 = st.columns([1, 2.5, 1]) 
with col_h2:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 10px;">
            <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" 
                 style="width: 260px; height: auto; display: inline-block;">
        </div>
        <h1 class="custom-title">Registro de usuarios</h1>
        <p class="subtitle-miaa">Administra y registra nuevos usuarios del sistema</p>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border: 1px solid #1C2541; margin-bottom: 2rem;'>", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
try:
    df_destinatarios = obtener_datos("SELECT id, nombre, chart_id, activo, departamento FROM Diccionario_telegram")
except:
    df_destinatarios = pd.DataFrame()

# --- FORMULARIO PARA AÑADIR DESTINATARIO ---
with st.container():
    st.markdown("""
        <div class="card-container">
            <h3 style="color: #00E5FF; margin-top: 0; font-size: 1.3rem;">➕ Añadir nuevo destinatario</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Expandible estilizado integrado
    with st.expander("Desplegar formulario de registro", expanded=False):
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

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("👥 Catálogo de Usuarios Registrados")

# --- LISTADO DE USUARIOS EN TARJETAS ---
if not df_destinatarios.empty:
    for idx, row_user in df_destinatarios.iterrows():
        with st.container():
            st.markdown(f"""
                <div class="card-container" style="padding: 15px 20px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.1rem; font-weight: bold; color: #FFFFFF;">👤 {row_user['nombre']}</span><br>
                            <span style="color: #8D99AE; font-size: 0.9rem;">💬 ID: {row_user['chart_id']} &nbsp;|&nbsp; 🏢 {row_user['departamento']}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            cols_u = st.columns([6, 2, 2])
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
else:
    st.info("No se encontraron registros en Diccionario_telegram.")

# --- MODAL / SECCIÓN DE CONFIRMACIÓN DE ELIMINACIÓN ---
if st.session_state.user_to_delete is not None:
    uid_Target = st.session_state.user_to_delete
    st.markdown(f"""
        <div style="background-color: #3A1C1C; border: 1px solid #E63946; padding: 15px; border-radius: 8px; margin-top: 20px;">
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

# --- PIE DE PÁGINA ---
st.markdown("""
    <div class="footer-miaa">
        🔒 Política de privacidad &nbsp;&bull;&nbsp; © 2026 MIAA. Todos los derechos reservados.
    </div>
""", unsafe_allow_html=True)
