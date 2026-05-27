import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página web
st.set_page_config(page_title="Simulador Logístico CEDIS", layout="wide")

# --- LÓGICA DEL SIMULADOR (POO) ---
class Galpon:
    def __init__(self, id_galpon, categoria_defecto, capacidad_defecto, filas_layout=5, columnas_layout=10):
        self.id_galpon = id_galpon
        self.filas = filas_layout
        self.columnas = columnas_layout
        
        # Guardar categoría en el estado de la sesión si no existe
        if f"cat_{id_galpon}" not in st.session_state:
            st.session_state[f"cat_{id_galpon}"] = categoria_defecto
            
        # Guardar capacidad máxima en el estado de la sesión si no existe
        if f"cap_{id_galpon}" not in st.session_state:
            st.session_state[f"cap_{id_galpon}"] = capacidad_defecto

        # Guardar ocupación actual en el estado de la sesión si no existe
        if f"galpon_{id_galpon}" not in st.session_state:
            st.session_state[f"galpon_{id_galpon}"] = 0

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
    def ocupacion_actual(self):
        return st.session_state[f"galpon_{self.id_galpon}"]

    @ocupacion_actual.setter
    def ocupacion_actual(self, valor):
        st.session_state[f"galpon_{self.id_galpon}"] = min(max(0, valor), self.capacidad_max)

    def espacio_disponible(self):
        return max(0, self.capacidad_max - self.ocupacion_actual)

    def almacenar(self, cantidad):
        if cantidad <= self.espacio_disponible():
            self.ocupacion_actual += cantidad
            return True
        return False

# Inicialización dinámica de los galpones
galpones = [
    Galpon(1, "Línea Blanca", 500, filas_layout=5, columnas_layout=10),      # 50 posiciones de rack
    Galpon(2, "Televisores y Audio", 800, filas_layout=8, columnas_layout=10), # 80 posiciones de rack
    Galpon(3, "Pequeños Electrodomésticos", 1200, filas_layout=10, columnas_layout=12), # 120 posiciones
    Galpon(4, "Tecnología y Gadgets", 1000, filas_layout=10, columnas_layout=10) # 100 posiciones
]

# --- INTERFAZ GRÁFICA (STREAMLIT) ---
st.title("🚢 Sistema de Simulación de Importaciones y CEDIS")
st.markdown("Gestione el ingreso de mercancía, configure la infraestructura y monitoree los galpones en tiempo real.")

# Panel Lateral: Entrada de Mercancía (REDISEÑADO)
st.sidebar.header("📥 Entrada de Importaciones")

# 1. Selección libre del Producto/Categoría
categorias_existentes = ["Línea Blanca", "Televisores y Audio", "Pequeños Electrodomésticos", "Tecnología y Gadgets", "Otros / Mercancía General"]
producto_ingreso = st.sidebar.selectbox("1. Tipo de producto que ingresa:", categorias_existentes)

# 2. Selección libre del Galpón de Destino (Independiente del producto)
lista_galpones_nombres = [f"Galpón {g.id_galpon} ({g.categoria})" for g in galpones]
galpon_seleccionado_nombre = st.sidebar.selectbox("2. Destino de Almacenamiento:", lista_galpones_nombres)
id_galpon_destino = int(galpon_seleccionado_nombre.split(" ")[1])

cantidad_ingreso = st.sidebar.number_input("3. Cantidad de unidades:", min_value=1, max_value=2000, value=150)

if st.sidebar.button("Simular Desembarco y Almacenaje"):
    galpon_destino = galpones[id_galpon_destino - 1]
    
    # Alerta si se guarda un producto en un galpón asignado a otra categoría
    if galpon_destino.categoria != producto_ingreso:
        st.sidebar.warning(f"⚠️ Alerta de Mezcla: Guardando '{producto_ingreso}' en un galpón destinado a '{galpon_destino.categoria}'.")

    if galpon_destino.almacenar(cantidad_ingreso):
        st.sidebar.success(f"✅ Éxito: Se alojaron {cantidad_ingreso} unds de '{producto_ingreso}' en el Galpón {galpon_destino.id_galpon}.")
    else:
        st.sidebar.error(f"⚠️ Capacidad insuficiente en Galpón {galpon_destino.id_galpon}. Disponible: {galpon_destino.espacio_disponible()} unds.")

if st.sidebar.button("🔄 Reiniciar Ocupación (Vaciar CEDIS)"):
    for g in galpones:
        g.ocupacion_actual = 0
    st.rerun()

# Bloque Principal 1: Monitor General Visual
st.subheader("📊 Estado Actual de los Galpones")
col1, col2, col3, col4 = st.columns(4)
columnas = [col1, col2, col3, col4]

for i, g in enumerate(galpones):
    with columnas[i]:
        st.markdown(f"### Galpón {g.id_galpon}")
        st.caption(f"**Uso Principal:** {g.categoria}")
        porcentaje = (g.ocupacion_actual / g.capacidad_max) if g.capacidad_max > 0 else 0.0
        porcentaje = min(1.0, porcentaje) 
        st.metric(label="Ocupación", value=f"{g.ocupacion_actual} / {g.capacidad_max} unds")
        st.progress(porcentaje)

st.markdown("---")

# Pestañas de Trabajo Organizadas (Añadida Pestaña de Ubicaciones)
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Consulta Individual", "📍 Ubicaciones Físicas y Teóricas", "⚙️ Configurar Capacidad", "📈 Tabla General"])

with tab1:
    st.subheader("🔍 Inspección Detallada por Galpón")
    id_elegido = st.selectbox("Seleccione el Galpón que desea auditar:", [1, 2, 3, 4], key="inspeccion")
    g_seleccionado = galpones[id_elegido - 1]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Unidades Almacenadas", f"{g_seleccionado.ocupacion_actual} unds")
    c2.metric("Capacidad Total Asignada", f"{g_seleccionado.capacidad_max} unds")
    c3.metric("Espacio Disponible Inmediato", f"{g_seleccionado.espacio_disponible()} unds")

with tab2:
    st.subheader("📍 Layout de Ubicaciones en Racks (Físico vs Teórico)")
    st.markdown("Visualización volumétrica del espacio disponible. Cada celda representa una **posición física (Pallet/Rack)**.")
    
    id_layout = st.selectbox("Seleccione el Galpón para ver el mapa de calor:", [1, 2, 3, 4], key="layout_select")
    g_layout = galpones[id_layout - 1]
    
    # Cálculo Teórico
    total_posiciones = g_layout.filas * g_layout.columnas
    factor_conversion = g_layout.capacidad_max / total_posiciones
    posiciones_ocupadas_teoricas = int(g_layout.ocupacion_actual / factor_conversion) if factor_conversion > 0 else 0
    
    # Métricas de la pestaña
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Total de Posiciones Físicas", f"{total_posiciones} Racks")
    mc2.metric("Posiciones Ocupadas (Teorico)", f"{posiciones_ocupadas_teoricas} Racks")
    mc3.metric("Posiciones Libres", f"{total_posiciones - posiciones_ocupadas_teoricas} Racks")
    
    st.markdown("#### 🗺️ Mapa de Distribución en Planta")
    
    # Crear la matriz visual
    mapa = np.zeros(total_posiciones)
    mapa[:posiciones_ocupadas_teoricas] = 1  # 1 = Ocupado
    # Desordenar un poco para simular almacenamiento físico real no perfecto
    np.random.seed(id_layout) 
    np.random.shuffle(mapa)
    mapa_2d = mapa.reshape(g_layout.filas, g_layout.columnas)
    
    # Dibujar el Layout con HTML/CSS nativo de Streamlit para máxima velocidad
    html_grid = "<div style='display: grid; grid-template-columns: repeat("+str(g_layout.columnas)+", 1fr); gap: 5px;'>"
    for f in range(g_layout.filas):
        for c in range(g_layout.columnas):
            estado = mapa_2d[f, c]
            color = "#EF4444" if estado == 1 else "#10B981" # Rojo ocupado, Verde libre
            codigo_ubicacion = f"R{f+1}-C{c+1}"
            html_grid += f"<div style='background-color: {color}; color: white; padding: 10px 2px; text-align: center; border-radius: 4px; font-size: 11px; font-weight: bold;' title='Ubicación: {codigo_ubicacion}'>{codigo_ubicacion}</div>"
    html_grid += "</div>"
    
    st.markdown(html_grid, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: 10px;'><span style='color: #10B981;'>■</span> Disponible &nbsp;&nbsp;&nbsp;&nbsp; <span style='color: #EF4444;'>■</span> Ocupado (Slot Asignado)</p>", unsafe_allow_html=True)

with tab3:
    st.subheader("⚙️ Optimización de Infraestructura")
    id_modificar = st.selectbox("Seleccione el Galpón a actualizar:", [1, 2, 3, 4], key="config")
    g_a_modificar = galpones[id_modificar - 1]
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        nueva_categoria = st.text_input("Editar Categoría / Tipo de Producto:", value=g_a_modificar.categoria)
    with col_input2:
        nueva_capacidad = st.number_input("Establecer Nueva Capacidad Máxima (Unidades):", min_value=100, max_value=5000, value=g_a_modificar.capacidad_max, step=50)
        
    if st.button("💾 Aplicar y Actualizar Galpón"):
        g_a_modificar.categoria = nueva_categoria
        g_a_modificar.capacidad_max = nueva_capacidad
        st.success(f"⚙️ ¡Galpón {id_modificar} actualizado con éxito!")
        st.rerun()

with tab4:
    st.subheader("📊 Cuadro de Mando Consolidado")
    data = {
        "Galpón": [f"Galpón {g.id_galpon}" for g in galpones],
        "Categoría asignada": [g.categoria for g in galpones],
        "Capacidad Máxima": [g.capacidad_max for g in galpones],
        "Ocupación Actual": [g.ocupacion_actual for g in galpones],
        "Disponibilidad Real": [g.espacio_disponible() for g in galpones]
    }
    st.dataframe(pd.DataFrame(data), use_container_width=True)