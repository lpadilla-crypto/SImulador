import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página web
st.set_page_config(page_title="Simulador Logístico CEDIS con Privilegios", layout="wide")

# --- 1. BASE DE DATOS DE USUARIOS (SESSION STATE) ---
if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {
        "admin@cedis.com": {"nombre": "Administrador Master", "password": "admin", "rol": "Master", "permiso_modificar": True},
        "operador1@cedis.com": {"nombre": "Juan Pérez", "password": "123", "rol": "Operador", "permiso_modificar": True},
        "operador2@cedis.com": {"nombre": "María López", "password": "456", "rol": "Operador", "permiso_modificar": False}
    }

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

    def almacenamiento_automatico(self, producto, cantidad):
        disponibles = self.espacio_disponible()
        if cantidad > disponibles:
            return False, f"Capacidad insuficiente. Solo quedan {disponibles} racks libres."
        
        colocados = 0
        for f in range(self.filas):
            for c in range(self.columnas):
                if colocado < cantidad and self.mapa_racks[f, c] == "Disponible":
                    self.mapa_racks[f, c] = producto
                    colocado += 1
        return True, f"Se almacenaron {colocados} unidades automáticamente."

# Inicialización persistente de galpones
if "galpones_init" not in st.session_state:
    st.session_state["galpones_init"] = [
        Galpon(1, "Línea Blanca", 500, filas=10, columnas=10),
        Galpon(2, "Televisores y Audio", 800, filas=10, columnas=10),
        Galpon(3, "Pequeños Electrodomésticos", 1200, filas=10, columnas=10),
        Galpon(4, "Tecnología y Gadgets", 1000, filas=10, columnas=10)
    ]
galpones = st.session_state["galpones_init"]

# --- 3. CONTROL DE PANTALLAS PRINCIPALES ---
if st.session_state["usuario_autenticado"] is None:
    # Formulario estricto de login para evitar el "Efecto Tenue" en Streamlit Cloud
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔐 Acceso al Sistema WMS - CEDIS</h2>", unsafe_allow_html=True)
    
    col_login_1, col_login_2, col_login_3 = st.columns([1, 1.5, 1])
    with col_login_2:
        with st.form(key="login_form_cloud"):
            correo_input = st.text_input("Correo electrónico Corporativo:", key="input_email_clean")
            password_input = st.text_input("Contraseña:", type="password", key="input_pass_clean")
            submit_login = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
            
            if submit_login:
                db = st.session_state["usuarios_db"]
                if correo_input in db and db[correo_input]["password"] == password_input:
                    st.session_state["usuario_autenticado"] = correo_input
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique e intente nuevamente.")
else:
    # --- 4. INTERFAZ DE LA APP PRINCIPAL (LOGUEADO) ---
    user_actual_info = st.session_state["usuarios_db"][st.session_state["usuario_autenticado"]]

    # Barra Superior de Información y Cierre de Sesión
    col_sup1, col_sup2 = st.columns([4, 1])
    with col_sup2:
        st.markdown(f"👤 **{user_actual_info['nombre']}** <br><small>Rol: {user_actual_info['rol']}</small>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", use_container_width=True, key="btn_logout"):
            st.session_state["usuario_autenticado"] = None
            st.rerun()

    st.title("🚢 Sistema de Simulación de Importaciones y CEDIS")
    st.markdown("Gestione el ingreso de mercancía, configure la infraestructura y monitoree los galpones en tiempo real.")

    # --- PANEL LATERAL CON RESTRICCIONES ---
    st.sidebar.header("📥 Entrada de Importaciones")

    if not user_actual_info["permiso_modificar"]:
        st.sidebar.warning("⚠️ Tu usuario solo tiene permisos de **LECTURA**. No puedes alterar el inventario.")
    else:
        categorias_existentes = ["Línea Blanca", "Televisores y Audio", "Pequeños Electrodomésticos", "Tecnología y Gadgets"]
        producto_ingreso = st.sidebar.selectbox("1. Tipo de producto que ingresa:", categorias_existentes, key="sb_prod")

        lista_galpones_nombres = [f"Galpón {g.id_galpon} ({g.categoria})" for g in galpones]
        galpon_seleccionado_nombre = st.sidebar.selectbox("2. Destino de Almacenamiento:", lista_galpones_nombres, key="sb_galp")
        id_galpon_destino = int(galpon_seleccionado_nombre.split(" ")[1])
        g_destino = galpones[id_galpon_destino - 1]

        cantidad_ingreso = st.sidebar.number_input("3. Cantidad de unidades:", min_value=1, max_value=2000, value=150, key="num_cant")
        modo_ubicacion = st.sidebar.radio("4. Modo de asignación de ubicación:", ["Automática (Sugerida WMS)", "Manual (Seleccionar Coordenadas)"], key="rd_modo")

        f_idx, c_idx = 0, 0
        if modo_ubicacion == "Manual (Seleccionar Coordenadas)":
            col_lateral1, col_lateral2 = st.sidebar.columns(2)
            with col_lateral1:
                fila_elegida = st.selectbox("Rack (Fila):", [f"R{i+1}" for i in range(g_destino.filas)], key="sb_fila")
                f_idx = int(fila_elegida[1:]) - 1
            with col_lateral2:
                col_elegida = st.selectbox("Slot (Col):", [f"C{i+1}" for i in range(g_destino.columnas)], key="sb_col")
                c_idx = int(col_elegida[1:]) - 1

        if st.sidebar.button("Simular Desembarco y Almacenaje", key="btn_simular"):
            if g_destino.categoria != producto_ingreso:
                st.sidebar.error(f"❌ Error de Zonificación: No puedes ingresar {producto_ingreso} en el {galpon_seleccionado_nombre}.")
            else:
                if modo_ubicacion == "Automática (Sugerida WMS)":
                    slots_a_ocupar = max(1, int(cantidad_ingreso / (g_destino.capacidad_max / (g_destino.filas * g_destino.columnas))))
                    exito, msg = g_destino.almacenamiento_automatico(producto_ingreso, slots_a_ocupar)
                    if exito:
                        st.sidebar.success(f"✅ Éxito: Almacenadas {cantidad_ingreso} unds en Galpón {g_destino.id_galpon}.")
                        st.rerun()
                    else: st.sidebar.error(f"⚠️ {msg}")
                else:
                    exito, msg = g_destino.almacenar_en_posicion(f_idx, c_idx, producto_ingreso)
                    if exito:
                        st.sidebar.success(f"✅ Slot {fila_elegida}-{col_elegida} asignado.")
                        st.rerun()
                    else: st.sidebar.error(f"⚠️ {msg}")

    if user_actual_info["rol"] == "Master":
        if st.sidebar.button("🔄 Reiniciar Ocupación (Vaciar CEDIS)", key="btn_reset_all"):
            for g in galpones:
                st.session_state[f"mapa_{g.id_galpon}"] = np.full((g.filas, g.columnas), "Disponible", dtype=object)
            st.rerun()

    # --- MONITOR SUPERIOR (VISUALIZACIÓN GENERAL) ---
    st.subheader("📊 Estado Actual de los Galpones")
    col1, col2, col3, col4 = st.columns(4)
    columnas = [col1, col2, col3, col4]

    for i, g in enumerate(galpones):
        with columnas[i]:
            st.markdown(f"### Galpón {g.id_galpon}")
            st.caption(f"**Uso Principal:** {g.categoria}")
            total_slots = g.filas * g.columnas
            porcentaje_ocupacion = g.ocupacion_actual / total_slots
            unidades_calculadas = int(porcentaje_ocupacion * g.capacidad_max)
            st.metric(label="Ocupación", value=f"{unidades_calculadas} / {g.capacidad_max} unds")
            st.progress(min(1.0, porcentaje_ocupacion))

    st.markdown("---")

    # --- PESTAÑAS DE TRABAJO ---
    if user_actual_info["rol"] == "Master":
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Consulta Individual", "📍 Ubicaciones Físicas y Teóricas", "⚙️ Configurar Capacidad", "📈 Tabla General", "🔑 Control de Usuarios (Master)"])
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Consulta Individual", "📍 Ubicaciones Físicas y Teóricas", "⚙️ Configurar Capacidad", "📈 Tabla General"])
        tab5 = None

    with tab1:
        st.subheader("🔍 Inspección Detallada por Galpón")
        id_elegido = st.selectbox("Seleccione el Galpón que desea auditar:", [1, 2, 3, 4], key="inspeccion")
        g_seleccionado = galpones[id_elegido - 1]
        u_sel = int((g_seleccionado.ocupacion_actual / (g_seleccionado.filas * g_seleccionado.columnas)) * g_seleccionado.capacidad_max)
        c1, c2, c3 = st.columns(3)
        c1.metric("Unidades Almacenadas", f"{u_sel} unds")
        c2.metric("Capacidad Total Asignada", f"{g_seleccionado.capacidad_max} unds")
        c3.metric("Espacio Disponible Inmediato", f"{g_seleccionado.capacidad_max - u_sel} unds")

    with tab2:
        st.subheader("📍 Layout de Ubicaciones en Planta")
        id_layout = st.selectbox("Seleccione el Galpón para ver el mapa:", [1, 2, 3, 4], key="layout_select")
        g_layout = galpones[id_layout - 1]
        
        html_grid = "<div style='display: grid; grid-template-columns: repeat("+str(g_layout.columnas)+", 1fr); gap: 5px;'>"
        for f in range(g_layout.filas):
            for c in range(g_layout.columnas):
                contenido = g_layout.mapa_racks[f, c]
                color = "#EF4444" if contenido != "Disponible" else "#10B981"
                html_grid += f"<div style='background-color: {color}; color: white; padding: 10px 2px; text-align: center; border-radius: 4px; font-size: 11px; font-weight: bold;'>R{f+1}-C{c+1}</div>"
        html_grid += "</div>"
        st.markdown(html_grid, unsafe_allow_html=True)

    with tab3:
        st.subheader("⚙️ Optimización de Infraestructura")
        if not user_actual_info["permiso_modificar"]:
            st.error("🚫 No tienes privilegios para reconfigurar el CEDIS.")
        else:
            id_modificar = st.selectbox("Seleccione el Galpón a actualizar:", [1, 2, 3, 4], key="config")
            g_a_modificar = galpones[id_modificar - 1]
            col_in1, col_in2 = st.columns(2)
            with col_in1: nueva_categoria = st.text_input("Editar Categoría:", value=g_a_modificar.categoria, key="txt_edit_cat")
            with col_in2: nueva_capacidad = st.number_input("Nueva Capacidad Máxima:", min_value=100, max_value=5000, value=g_a_modificar.capacidad_max, key="num_edit_cap")
                
            if st.button("💾 Aplicar y Actualizar Galpón", key="btn_save_infra"):
                g_a_modificar.categoria = nueva_categoria
                g_a_modificar.capacidad_max = nueva_capacidad
                st.success("⚙️ Configuración de infraestructura guardada.")
                st.rerun()

    with tab4:
        st.subheader("📊 Cuadro de Mando Consolidado")
        unidades_totales = [int((g.ocupacion_actual / (g.filas * g.columnas)) * g.capacidad_max) for g in galpones]
        data = {"Galpón": [f"Galpón {g.id_galpon}" for g in galpones], "Categoría": [g.categoria for g in galpones], "Capacidad Máxima": [g.capacidad_max for g in galpones], "Ocupación": unidades_totales}
        st.dataframe(pd.DataFrame(data), use_container_width=True)

    if tab5 is not None:
        with tab5:
            st.subheader("🔑 Consola de Administración de Credenciales y Permisos")
            
            usuarios_lista = []
            for correo, info in st.session_state["usuarios_db"].items():
                usuarios_lista.append({
                    "Correo / Usuario": correo,
                    "Nombre Completo": info["nombre"],
                    "Contraseña": info["password"],
                    "Rol de Sistema": info["rol"],
                    "Permiso de Escritura": "✅ SI" if info["permiso_modificar"] else "❌ NO"
                })
            st.dataframe(pd.DataFrame(usuarios_lista), use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 🛠️ Modificar un Usuario Existente")
            
            user_a_editar = st.selectbox("Seleccione el usuario a gestionar:", list(st.session_state["usuarios_db"].keys()), key="sb_user_manage")
            info_user = st.session_state["usuarios_db"][user_a_editar]
            
            c_mod1, c_mod2, c_mod3 = st.columns(3)
            with c_mod1: nuevo_nombre = st.text_input("Editar Nombre:", value=info_user["nombre"], key="txt_edit_unombre")
            with c_mod2: nueva_pass = st.text_input("Modificar Contraseña:", value=info_user["password"], key="txt_edit_upass")
            with c_mod3: nuevo_rol = st.selectbox("Cambiar Rol:", ["Operador", "Master"], index=0 if info_user["rol"] == "Operador" else 1, key="sb_edit_urol")
                
            permiso_check = st.checkbox("Habilitar Permiso de Modificación", value=info_user["permiso_modificar"], key="chk_edit_uperm")
            
            if st.button("💾 Guardar Cambios de Credenciales", key="btn_save_user"):
                st.session_state["usuarios_db"][user_a_editar] = {
                    "nombre": nuevo_nombre,
                    "password": nueva_pass,
                    "rol": nuevo_rol,
                    "permiso_modificar": permiso_check if nuevo_rol == "Operador" else True
                }
                st.success(f"¡Usuario {user_a_editar} actualizado!")
                st.rerun()