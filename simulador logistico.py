import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página web
st.set_page_config(page_title="Simulador Logístico CEDIS", layout="wide")

# --- 1. BASE DE DATOS DE USUARIOS ---
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

# Inicialización segura de galpones
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
        # Usamos inputs independientes fuera de un 'form' complejo para evitar bloqueos de hilos en la nube
        correo_form = st.text_input("Correo electrónico Corporativo:", key="u_email")
        pass_form = st.text_input("Contraseña:", type="password", key="u_pass")
        
        if st.button("🚀 Ingresar al Sistema", use_container_width=True, key="btn_entrar"):
            db = st.session_state["usuarios_db"]
            if correo_form in db and db[correo_form]["password"] == pass_form:
                st.session_state["usuario_autenticado"] = correo_form
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas.")
else:
    # --- 4. PANEL PRINCIPAL (USUARIO LOGUEADO) ---
    user_info = st.session_state["usuarios_db"][st.session_state["usuario_autenticado"]]

    # Cabecera de usuario
    c_tit, c_user = st.columns([4, 1])
    with c_user:
        st.markdown(f"👤 **{user_info['nombre']}**<br><small>{user_info['rol']}</small>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", use_container_width=True, key="btn_logout"):
            st.session_state["usuario_autenticado"] = None
            st.rerun()

    st.title("🚢 Sistema de Simulación de Importaciones y CEDIS")
    
    # --- INTERFAZ DEL PANEL LATERAL ---
    st.sidebar.header("📥 Entrada de Importaciones")
    if not user_info["permiso_modificar"]:
        st.sidebar.warning("⚠️ Tu usuario es de solo LECTURA.")
    else:
        cat_seleccionada = st.sidebar.selectbox("1. Tipo de producto:", ["Línea Blanca", "Televisores y Audio", "Pequeños Electrodomésticos", "Tecnología y Gadgets"])
        nombres_g = [f"Galpón {g.id_galpon} ({g.categoria})" for g in galpones]
        g_seleccionado_txt = st.sidebar.selectbox("2. Destino de Almacenamiento:", nombres_g)
        idx_g = int(g_seleccionado_txt.split(" ")[1]) - 1
        g_target = galpones[idx_g]
        
        cant_ingreso = st.sidebar.number_input("3. Cantidad de unidades:", min_value=1, max_value=2000, value=150)
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

        if st.sidebar.button("Simular Almacenaje", use_container_width=True):
            if g_target.categoria != cat_seleccionada:
                st.sidebar.error("❌ Error de Zonificación.")
            else:
                if modo_ub == "Automática (Sugerida WMS)":
                    slots = max(1, int(cant_ingreso / (g_target.capacidad_max / (g_target.filas * g_target.columnas))))
                    exito, m = g_target.almacenamiento_automatico(cat_seleccionada, slots)
                else:
                    exito, m = g_target.almacenar_en_posicion(f_idx, c_idx, cat_seleccionada)
                if exito: st.rerun()
                else: st.sidebar.error(m)

    # --- INDICADORES VISUALES SUPERIORES ---
    st.subheader("📊 Estado Actual de los Galpones")
    columnas_g = st.columns(4)
    for idx, g in enumerate(galpones):
        with columnas_g[idx]:
            st.markdown(f"### Galpón {g.id_galpon}")
            st.caption(f"**Uso:** {g.categoria}")
            pct = g.ocupacion_actual / (g.filas * g.columnas)
            unds_calc = int(pct * g.capacidad_max)
            st.metric("Ocupación", f"{unds_calc} / {g.capacidad_max} unds")
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
        c1.metric("Almacenado", f"{u_aud} unds")
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
        df = pd.DataFrame({"Galpón": [f"Galpón {g.id_galpon}" for g in galpones], "Categoría": [g.categoria for g in galpones], "Capacidad": [g.capacidad_max for g in galpones], "Ocupación": uds_tot})
        st.dataframe(df, use_container_width=True)

    if t5 is not None:
        with t5:
            st.subheader("🔑 Gestión de Usuarios (Master)")
            user_sel = st.selectbox("Seleccionar usuario a editar:", list(st.session_state["usuarios_db"].keys()))
            u_data = st.session_state["usuarios_db"][user_sel]
            
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                n_name = st.text_input("Nombre:", value=u_data["nombre"])
                n_role = st.selectbox("Rol:", ["Operador", "Master"], index=0 if u_data["rol"] == "Operador" else 1)
            with col_u2:
                n_pass = st.text_input("Contraseña:", value=u_data["password"])
                n_perm = st.checkbox("Permiso de Escritura", value=u_data["permiso_modificar"])
                
            if st.button("Actualizar Credenciales"):
                st.session_state["usuarios_db"][user_sel] = {"nombre": n_name, "password": n_pass, "rol": n_role, "permiso_modificar": n_perm if n_role == "Operador" else True}
                st.success("Usuario actualizado.")
                st.rerun()