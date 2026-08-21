import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import time, datetime, timedelta
import time as t
from zoneinfo import ZoneInfo

# Configuración de página
st.set_page_config(layout="wide", page_title="Gestión de Usuarios - Telegram", page_icon="https://www.miaa.mx/favicon.ico")

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

# --- CSS ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {padding-top: 1rem !important; padding-bottom: 0rem !important;} 
    .custom-title {color: #00E5FF !important; font-size: 2rem; font-weight: bold; margin-bottom: 0px; text-align: center; margin-top: 0px;} 
    .logo-container img {
        width: 300px !important; 
        height: auto !important;
        display: block;
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA ---
col_h1, col_h2 = st.columns([2, 9]) 
with col_h1:
    st.markdown("""
        <div style="width: 250px;">
            <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" 
                 style="width: 100%; height: auto; display: block;">
        </div>
    """, unsafe_allow_html=True)

with col_h2: 
    st.markdown('<h1 class="custom-title">Gestión de Destinatarios (Telegram)</h1>', unsafe_allow_html=True)
st.divider()

# --- CARGA DE DATOS ---
try:
    df_destinatarios = obtener_datos("SELECT id, nombre, chart_id, activo, departamento FROM Diccionario_telegram")
except:
    df_destinatarios = pd.DataFrame()

# --- GESTIÓN DE DESTINATARIOS ---
st.subheader("👥 Catálogo de Usuarios")

with st.expander("➕ Añadir nuevo destinatario"):
    with st.form("form_nuevo_usuario_dinamico_unico"):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            nuevo_nombre = st.text_input("Nombre completo", key="input_nuevo_nombre")
        with f_col2:
            nuevo_chart = st.text_input("Chart ID (Telegram)", key="input_nuevo_chart")
        with f_col3:
            nuevo_depto = st.text_input("Departamento", value="Planeacion Tecnica", key="input_nuevo_depto")
        
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

if not df_destinatarios.empty:
    for idx, row_user in df_destinatarios.iterrows():
        cols_u = st.columns([2, 2, 2, 1, 1])
        with cols_u[0]:
            st.text(f"👤 {row_user['nombre']}")
        with cols_u[1]:
            st.text(f"💬 ID: {row_user['chart_id']}")
        with cols_u[2]:
            st.text(f"🏢 {row_user['departamento']}")
        with cols_u[3]:
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
        with cols_u[4]:
            if st.button("🗑️ Eliminar", key=f"del_user_{row_user['id']}_{idx}"):
                st.session_state.user_to_delete = row_user['id']
                st.rerun()
else:
    st.info("No se encontraron registros en Diccionario_telegram.")

if st.session_state.user_to_delete is not None:
    uid_Target = st.session_state.user_to_delete
    st.warning(f"⚠️ Estás a punto de eliminar al usuario con ID: {uid_Target}. Esta acción no se puede deshacer.")
    
    confirm_text = st.text_input("Para confirmar, escribe la palabra requerida en el siguiente campo:", key="input_confirm_delete")
    
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
