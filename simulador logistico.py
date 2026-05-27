import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página web
st.set_page_config(page_title="Simulador Logístico CEDIS", layout="wide")

# FACTOR DE CONVERSIÓN: Unidades por Contenedor estándar (TEU)
UNIDADES_POR_CONTENEDOR = 200

# --- 1. BASE DE DATOS GLOBAL COMPARTIDA ---
@st.cache_resource
def inicializar_base_datos_global():
    return {
        "admin@cedis.com": {"nombre": "Administrador Master", "password": "admin", "rol": "Master", "permiso_modificar": True},
        "operador1@cedis.com": {"nombre": "Juan Pérez", "password": "123", "rol": "Operador", "permiso_modificar": True},
        "operador2@cedis.com": {"nombre": "María López", "password": "456", "rol": "Operador", "permiso_modificar": False}
    }

usuarios_db_global = inicializar_base_datos_global()

if "usuario_autenticado" not in st.session_state:
    st.session_state["usuario_autenticado"] = None

# --- 2. LÓGICA DEL SIMULADOR LOGÍSTICO (POO) ---
class Galpon:
    def __init__(self, id_galpon, categoria_defecto, capacidad_defecto, filas=10, columnas=10):
        self.id_galpon = id_galpon
        self.filas = filas
        self.columnas = columnas
        
        if f"cat_{id_galpon}" not in st.session_state:
            st.session_state[f"cat_{id_galpon}"] = categoria_defecto
        if f"cap_{id_galpon}" not in st.session_state:
            st.session_state[f"cap_{id_galpon}"] = capacidad_defecto
        if f"mapa_{id_galpon}" not in st.session_state:
            st.session_state[f"mapa_{id_galpon}"] = np.full((filas, columnas), "Disponible", dtype=object)

    @property
    def categoria(self):
        return st.session_state[f"cat_{self.id_galpon}"]
    @categoria.setter
    def categoria(self, nueva_cat):
        st.session_state[f"cat_{self.id_galpon}"] = nueva_cat

    @property
    def capacidad_max(self):
        return st.session_state[f"cap_{self.id_galpon}"]
    @capacidad_max.setter
    def capacidad_max(self, valor):
        st.session_state[f"cap_{self.id_galpon}"] = valor

    @property
    def mapa_racks(self):
        return st.session_state[f"mapa_{self.id_galpon}"]

    @property
    def ocupacion_actual(self):
        return int(np.sum(self.mapa_racks != "Disponible"))

    def espacio_disponible(self):
        return (self.filas * self.columnas) - self.ocupacion_actual

    def almacenar_en_posicion(self, fila, columna, producto):
        if self.mapa_racks[fila, columna] != "Disponible":
            return False, "La posición física seleccionada ya está ocupada."
        self.mapa_racks[fila, columna] = producto
        return True, "Ubicación asignada con éxito."

    # --- SOLUCIÓN AL BUG DEL TRACEBACK (Línea 77) ---
    def almacenamiento_automatico(self, producto, cantidad_slots):
        disponibles = self.espacio_disponible()
        if cantidad_slots > disponibles:
            return False, f"Capacidad insuficiente en racks. Solo quedan {disponibles} slots libres."
        
        slots_ocupados = 0
        for f in range(self.filas):
            for c in range(self.columnas):
                if slots_ocupados < cantidad_slots and self.mapa_racks[f, c] == "Disponible":
                    self.mapa_racks[f, c] = producto
                    slots_ocupados += 1
        return True, f"Se asignaron {slots_ocupados} slots automáticamente en la matriz."

if "galpones_lista" not in st.session_state:
    st.session_state["galpones_lista"] = [
        Galpon(1, "Línea Blanca", 500, filas=10, columnas=10),
        Galpon(2, "Televisores y Audio", 800, filas=10, columnas=10),
        Galpon(3, "Pequeños Electrodomésticos", 1200, filas=10, columnas=10),
        Galpon(4, "Tecnología y Gadgets", 1000, filas=10, columnas=10)
    ]
galpones = st.session_state["galpones_lista"]

# --- 3. PROCESAMIENTO DE AUTENTICACIÓN ---
if st.session_state["usuario_autenticado"] is None:
    st.markdown("<h2 style='text-align: center; margin-top: 30px;'>🔐 Acceso al Sistema WMS - CEDIS</h2>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        correo_form = st.text_input("Correo electrónico Corporativo:", key="u_email")
        pass_form = st.text_input("Contraseña:", type="password", key="u_pass")
        
        if st.button("🚀 Ingresar al Sistema", use_container_width=True, key="btn_entrar"):
            if correo_form in usuarios_db_global and usuarios_db_global[correo_form]["password"] == pass_form:
                st.session_state["usuario_autenticado"] = correo_form
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas.")
else:
    # --- 4. PANEL PRINCIPAL (USUARIO LOGUEADO) ---
    user_info = usuarios_db_global[st.session_state["usuario_autenticado"]]

    # Cabecera de usuario
    c_tit, c_user = st.columns([4, 1])
    with c_user:
        st.markdown(f"👤 **{user_info['nombre']}**<br><small>{user_info['rol']}</small>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", use_container_width=True, key="btn_logout"):
            st.session_state["usuario_autenticado"] = None
            st.rerun()

    st.title("🚢 Sistema de Simulación de Importaciones y CEDIS")
    
    # --- INTERFAZ DEL PANEL LATERAL: SECCIÓN DE INGRESOS ---
    st.sidebar.header("📥 Entrada de Importaciones")
    if not user_info["permiso_modificar"]:
        st.sidebar.warning("⚠️ Tu usuario es de solo LECTURA.")
    else:
        cat_seleccionada = st.sidebar.selectbox("1. Tipo de producto que ingresa:", ["Línea Blanca", "Televisores y Audio", "Pequeños Electrodomésticos", "Tecnología y Gadgets"])
        
        nombres_g = [f"Galpón {g.id_galpon} ({g.categoria})" for g in galpones]
        g_seleccionado_txt = st.sidebar.selectbox("2. Destino de Almacenamiento:", nombres_g)
        idx_g = int(g_seleccionado_txt.split(" ")[1]) - 1
        g_target = galpones[idx_g]
        
        # Entrada dual: El usuario puede definir la carga por unidades o calcular por contenedores
        modo_metrica = st.sidebar.radio("Definir volumen de importación por:", ["Cantidad de Unidades", "Cantidad de Contenedores (TEU)"])
        
        if modo_metrica == "Cantidad de Unidades":
            cant_unidades = st.sidebar.number_input("3. Unidades a ingresar:", min_value=1, max_value=5000, value=200, step=50)
            # Cálculo de contenedores equivalentes (informativo)
            calc_contenedores = round(cant_unidades / UNIDADES_POR_CONTENEDOR, 2)
            st.sidebar.info(f"📦 Equivalente teórico: **{calc_contenedores} Contenedores**")
        else:
            cant_contenedores = st.sidebar.number_input("3. Contenedores a desembarcar:", min_value=0.5, max_value=25.0, value=1.0, step=0.5)
            # Cálculo de unidades equivalentes
            cant_unidades = int(cant_contenedores * UNIDADES_POR_CONTENEDOR)
            st.sidebar.info(f"🔢 Equivalente teórico: **{cant_unidades} Unidades**")

        modo_ub = st.sidebar.radio("4. Asignación de ubicación:", ["Automática (Sugerida WMS)", "Manual (Coordenadas)"])
        
        f_idx, c_idx = 0, 0
        if modo_ub == "Manual (Coordenadas)":
            col_l1, col_l2 = st.sidebar.columns(2)
            with col_l1:
                f_txt = st.selectbox("Rack (Fila):", [f"R{i+1}" for i in range(g_target.filas)])
                f_idx = int(f_txt[1:]) - 1
            with col_l2:
                c_txt = st.selectbox("Slot (Col):", [f"C{i+1}" for i in range(g_target.columnas)])
                c_idx = int(c_txt[1:]) - 1

        st.sidebar.markdown("---")
        # BOTÓN DE ACCIÓN PRINCIPAL VISIBLE Y EMITIDO AL FINAL
        if st.sidebar.button("🚢 EJECUTAR INGRESO AL CEDIS", use_container_width=True, type="primary", key="btn_ejecutar_simulacion"):
            if g_target.categoria != cat_seleccionada:
                st.sidebar.error(f"❌ Error de Zonificación: No puedes meter {cat_seleccionada} en el {g_seleccionado_txt}.")
            else:
                if modo_ub == "Automática (Sugerida WMS)":
                    # Proporción de espacios físicos a ocupar basados en las unidades ingresadas
                    slots_a_ocupar = max(1, int(cant_unidades / (g_target.capacidad_max / (g_target.filas * g_target.columnas))))
                    exito, m = g_target.almacenamiento_automatico(cat_seleccionada, slots_a_ocupar)
                else:
                    exito, m = g_target.almacenar_en_posicion(f_idx, c_idx, cat_seleccionada)
                
                if exito: 
                    st.toast(f"¡Ingreso completado! Carga registrada.", icon="✅")
                    st.rerun()
                else: 
                    st.sidebar.error(m)

    # --- INDICADORES VISUALES SUPERIORES ---
    st.subheader("📊 Estado Actual de los Galpones")
    columnas_g = st.columns(4)
    for idx, g in enumerate(galpones):
        with columnas_g[idx]:
            st.markdown(f"### Galpón {g.id_galpon}")
            st.caption(f"**Uso:** {g.categoria}")
            pct = g.ocupacion_actual / (g.filas * g.columnas)
            unds_calc = int(pct * g.capacidad_max)
            cont_calc = round(unds_calc / UNIDADES_POR_CONTENEDOR, 1)
            
            st.metric("Ocupación", f"{unds_calc} / {g.capacidad_max} unds", f"{cont_calc} TEU")
            st.progress(min(1.0, pct))

    st.markdown("---")

    # --- SECCIÓN DE PESTAÑAS (TABS) ---
    if user_info["rol"] == "Master":
        t1, t2, t3, t4, t5 = st.tabs(["🔍 Consulta", "📍 Ubicaciones", "⚙️ Capacidad", "📈 Tabla General", "🔑 Control de Usuarios"])
    else:
        t1, t2, t3, t4 = st.tabs(["🔍 Consulta", "📍 Ubicaciones", "⚙️ Capacidad", "📈 Tabla General"])
        t5 = None

    with t1:
        id_auditar = st.selectbox("Auditar Galpón:", [1,2,3,4], key="audit")
        g_aud = galpones[id_auditar-1]
        u_aud = int((g_aud.ocupacion_actual / (g_aud.filas * g_aud.columnas)) * g_aud.capacidad_max)
        c1, c2, c3 = st.columns(3)
        c1.metric("Almacenado", f"{u_aud} unds", f"{round(u_aud/UNIDADES_POR_CONTENEDOR, 1)} Contenedores")
        c2.metric("Capacidad Max", f"{g_aud.capacidad_max} unds")
        c3.metric("Disponible", f"{g_aud.capacidad_max - u_aud} unds")

    with t2:
        id_lay = st.selectbox("Ver mapa de Racks:", [1,2,3,4], key="lay")
        g_lay = galpones[id_lay-1]
        grid_html = "<div style='display: grid; grid-template-columns: repeat("+str(g_lay.columnas)+", 1fr); gap: 4px;'> "
        for f in range(g_lay.filas):
            for c in range(g_lay.columnas):
                color = "#EF4444" if g_lay.mapa_racks[f,c] != "Disponible" else "#10B981"
                grid_html += f"<div style='background-color: {color}; color: white; text-align: center; font-size: 10px; padding: 8px 0; border-radius: 3px;'>R{f+1}</div>"
        grid_html += "</div>"
        st.markdown(grid_html, unsafe_allow_html=True)

    with t3:
        if not user_info["permiso_modificar"]: st.error("No tienes permisos.")
        else:
            id_mod = st.selectbox("Configurar Galpón:", [1,2,3,4], key="mod_inf")
            g_mod = galpones[id_mod-1]
            n_cat = st.text_input("Nueva Categoría:", value=g_mod.categoria)
            n_cap = st.number_input("Nueva Capacidad:", value=g_mod.capacidad_max)
            if st.button("Guardar Cambios"):
                g_mod.categoria = n_cat
                g_mod.capacidad_max = n_cap
                st.success("Guardado.")
                st.rerun()

    with t4:
        uds_tot = [int((g.ocupacion_actual / (g.filas * g.columnas)) * g.capacidad_max) for g in galpones]
        con_tot = [round(u / UNIDADES_POR_CONTENEDOR, 1) for u in uds_tot]
        df = pd.DataFrame({
            "Galpón": [f"Galpón {g.id_galpon}" for g in galpones], 
            "Categoría": [g.categoria for g in galpones], 
            "Capacidad Max (Unds)": [g.capacidad_max for g in galpones], 
            "Ocupación (Unidades)": uds_tot,
            "Ocupación (Contenedores)": con_tot
        })
        st.dataframe(df, use_container_width=True)

    if t5 is not None:
        with t5:
            st.subheader("🔑 Gestión de Usuarios (Master)")
            usuarios_lista = []
            for correo, info in usuarios_db_global.items():
                usuarios_lista.append({
                    "Usuario (Correo)": correo,
                    "Nombre Completo": info["nombre"],
                    "Contraseña Activa": info["password"],
                    "Rol": info["rol"],
                    "Acceso Escritura": "✅ SI" if info["permiso_modificar"] else "❌ NO"
                })
            st.dataframe(pd.DataFrame(usuarios_lista), use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 🛠️ Modificar Credenciales de un Usuario")
            
            user_sel = st.selectbox("Seleccionar usuario a editar:", list(usuarios_db_global.keys()), key="selector_master_usuarios")
            u_data = usuarios_db_global[user_sel]
            
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                n_name = st.text_input("Nombre Completo:", value=u_data["nombre"], key=f"name_{user_sel}")
                n_role = st.selectbox("Rol del Sistema:", ["Operador", "Master"], index=0 if u_data["rol"] == "Operador" else 1, key=f"role_{user_sel}")
            with col_u2:
                n_pass = st.text_input("Contraseña de Acceso:", value=u_data["password"], key=f"pass_{user_sel}")
                n_perm = st.checkbox("Habilitar Permiso de Escritura", value=u_data["permiso_modificar"], key=f"perm_{user_sel}")
            
            @st.dialog("⚠️ Confirmar Actualización de Credenciales")
            def confirmar_cambio_modal(usuario, nombre, clave, rol, permiso):
                st.warning(f"¿Desea aplicar estos cambios globales para **{usuario}**?")
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✅ Sí, Guardar", use_container_width=True, key=f"btn_confirmar_{usuario}"):
                        usuarios_db_global[usuario] = {"nombre": str(nombre), "password": str(clave), "rol": str(rol), "permiso_modificar": bool(permiso) if rol == "Operador" else True}
                        st.rerun()
                with c_btn2:
                    if st.button("❌ Cancelar", use_container_width=True, key=f"btn_cancelar_{usuario}"): st.rerun()

            if st.button("🔄 Actualizar Credenciales", use_container_width=True, type="primary", key=f"btn_trigger_{user_sel}"):
                confirmar_cambio_modal(user_sel, n_name, n_pass, n_role, n_perm)