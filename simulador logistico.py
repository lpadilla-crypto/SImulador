import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página web
st.set_page_config(page_title="Simulador Logístico CEDIS", layout="wide")

# --- LÓGICA DEL SIMULADOR (POO) ---
class Galpon:
    def __init__(self, id_galpon, categoria_defecto, capacidad_defecto, filas=10, columnas=10):
        self.id_galpon = id_galpon
        self.filas = filas
        self.columnas = columnas
        
        # Estado de sesión para categoría y capacidad máxima
        if f"cat_{id_galpon}" not in st.session_state:
            st.session_state[f"cat_{id_galpon}"] = categoria_defecto
        if f"cap_{id_galpon}" not in st.session_state:
            st.session_state[f"cap_{id_galpon}"] = capacidad_defecto

        # Inicializar el mapa físico del galpón (Matriz para registrar qué producto ocupa cada slot)
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
        # Cuenta las celdas que están ocupadas por algún producto
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

# Inicialización fija de dimensiones de galpones para el mapa (ej: 10x10 = 100 slots base por galpón, escalable por backend)
galpones = [
    Galpon(1, "Línea Blanca", 500, filas=10, columnas=10),
    Galpon(2, "Televisores y Audio", 800, filas=10, columnas=10),
    Galpon(3, "Pequeños Electrodomésticos", 1200, filas=10, columnas=10),
    Galpon(4, "Tecnología y Gadgets", 1000, filas=10, columnas=10)
]

# --- INTERFAZ GRÁFICA (STREAMLIT) ---
st.title("🚢 Sistema de Simulación de Importaciones y CEDIS")
st.markdown("Gestione el ingreso de mercancía, configure la infraestructura y monitoree los galpones en tiempo real.")

# Panel Lateral: Entrada de Mercancía (MODIFICADO CON SELECCIÓN DE UBICACIÓN)
st.sidebar.header("📥 Entrada de Importaciones")

categorias_existentes = ["Línea Blanca", "Televisores y Audio", "Pequeños Electrodomésticos", "Tecnología y Gadgets"]
producto_ingreso = st.sidebar.selectbox("1. Tipo de producto que ingresa:", categorias_existentes)

lista_galpones_nombres = [f"Galpón {g.id_galpon} ({g.categoria})" for g in galpones]
galpon_seleccionado_nombre = st.sidebar.selectbox("2. Destino de Almacenamiento:", lista_galpones_nombres)
id_galpon_destino = int(galpon_seleccionado_nombre.split(" ")[1])
g_destino = galpones[id_galpon_destino - 1]

cantidad_ingreso = st.sidebar.number_input("3. Cantidad de unidades:", min_value=1, max_value=2000, value=150)

# NUEVO: Selector de Modo de Ubicación en el Menú Lateral
modo_ubicacion = st.sidebar.radio("4. Modo de asignación de ubicación:", ["Automática (Sugerida WMS)", "Manual (Seleccionar Coordenadas)"])

f_idx, c_idx = 0, 0
if modo_ubicacion == "Manual (Seleccionar Coordenadas)":
    col_lateral1, col_lateral2 = st.sidebar.columns(2)
    with col_lateral1:
        fila_elegida = st.selectbox("Rack (Fila):", [f"R{i+1}" for i in range(g_destino.filas)])
        f_idx = int(fila_elegida[1:]) - 1
    with col_lateral2:
        col_elegida = st.selectbox("Slot (Col):", [f"C{i+1}" for i in range(g_destino.columnas)])
        c_idx = int(col_elegida[1:]) - 1

# Botón Principal de Ejecución
if st.sidebar.button("Simular Desembarco y Almacenaje"):
    # Regla de Validación: No mezclar categorías en galpones erróneos
    if g_destino.categoria != producto_ingreso:
        st.sidebar.error(f"❌ Error de Zonificación: No puedes ingresar {producto_ingreso} en el {galpon_seleccionado_nombre}.")
    else:
        if modo_ubicacion == "Automática (Sugerida WMS)":
            # Para mantener la escala original, calculamos cuántas "posiciones de volumen masivo" ocupa la cantidad
            # Si el usuario ingresa 150 unidades, simularemos que ocupa proporcionalmente los slots del mapa
            slots_a_ocupar = max(1, int(cantidad_ingreso / (g_destino.capacidad_max / (g_destino.filas * g_destino.columnas))))
            exito, msg = g_destino.almacenamiento_automatico(producto_ingreso, slots_a_ocupar)
            if exito:
                st.sidebar.success(f"✅ Éxito: Se almacenaron {cantidad_ingreso} unidades en el Galpón {g_destino.id_galpon}.")
                st.rerun()
            else:
                st.sidebar.error(f"⚠️ {msg}")
        else:
            # Asignación manual en una celda específica
            exito, msg = g_destino.almacenar_en_posicion(f_idx, c_idx, producto_ingreso)
            if exito:
                st.sidebar.success(f"✅ Slot {fila_elegida}-{col_elegida} asignado en Galpón {g_destino.id_galpon}.")
                st.rerun()
            else:
                st.sidebar.error(f"⚠️ {msg}")

if st.sidebar.button("🔄 Reiniciar Ocupación (Vaciar CEDIS)"):
    for g in galpones:
        st.session_state[f"mapa_{g.id_galpon}"] = np.full((g.filas, g.columnas), "Disponible", dtype=object)
    st.rerun()

# Bloque Principal 1: Monitor General Visual (IDÉNTICO A TU CAPTURA)
st.subheader("📊 Estado Actual de los Galpones")
col1, col2, col3, col4 = st.columns(4)
columnas = [col1, col2, col3, col4]

# Para la barra de progreso general reflejamos el volumen proporcional en unidades
for i, g in enumerate(galpones):
    with columnas[i]:
        st.markdown(f"### Galpón {g.id_galpon}")
        st.caption(f"**Uso Principal:** {g.categoria}")
        
        # Calcular unidades proporcionales en base a los slots ocupados del mapa
        total_slots = g.filas * g.columnas
        porcentaje_ocupacion = g.ocupacion_actual / total_slots
        unidades_calculadas = int(porcentaje_ocupacion * g.capacidad_max)
        
        st.metric(label="Ocupación", value=f"{unidades_calculadas} / {g.capacidad_max} unds")
        st.progress(min(1.0, porcentaje_ocupacion))

st.markdown("---")

# Pestañas de Trabajo Inferiores
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Consulta Individual", "📍 Ubicaciones Físicas y Teóricas", "⚙️ Configurar Capacidad", "📈 Tabla General"])

with tab1:
    st.subheader("🔍 Inspección Detallada por Galpón")
    id_elegido = st.selectbox("Seleccione el Galpón que desea auditar:", [1, 2, 3, 4], key="inspeccion")
    g_seleccionado = galpones[id_elegido - 1]
    
    total_slots_sel = g_seleccionado.filas * g_seleccionado.columnas
    porcentaje_sel = g_seleccionado.ocupacion_actual / total_slots_sel
    unidades_sel = int(porcentaje_sel * g_seleccionado.capacidad_max)
    disponible_sel = g_seleccionado.capacidad_max - unidades_sel
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Unidades Almacenadas", f"{unidades_sel} unds")
    c2.metric("Capacidad Total Asignada", f"{g_seleccionado.capacidad_max} unds")
    c3.metric("Espacio Disponible Inmediato", f"{disponible_sel} unds")

with tab2:
    st.subheader("📍 Layout de Ubicaciones en Planta (Matriz de Racks)")
    st.markdown("Visualización en tiempo real de los pasillos de almacenamiento.")
    
    id_layout = st.selectbox("Seleccione el Galpón para ver el mapa de calor:", [1, 2, 3, 4], key="layout_select")
    g_layout = galpones[id_layout - 1]
    
    # Grid HTML/CSS para dibujar el mapa de calor de forma elegante
    html_grid = "<div style='display: grid; grid-template-columns: repeat("+str(g_layout.columnas)+", 1fr); gap: 5px;'>"
    for f in range(g_layout.filas):
        for c in range(g_layout.columnas):
            contenido = g_layout.mapa_racks[f, c]
            codigo = f"R{f+1}-C{c+1}"
            color = "#EF4444" if contenido != "Disponible" else "#10B981"
            tooltip = "Vacío" if contenido == "Disponible" else f"Producto: {contenido}"
            
            html_grid += f"<div style='background-color: {color}; color: white; padding: 10px 2px; text-align: center; border-radius: 4px; font-size: 11px; font-weight: bold;' title='{tooltip}'>{codigo}</div>"
    html_grid += "</div>"
    
    st.markdown(html_grid, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: 10px;'><span style='color: #10B981;'>■</span> Posición Disponible &nbsp;&nbsp;&nbsp;&nbsp; <span style='color: #EF4444;'>■</span> Posición Asignada</p>", unsafe_allow_html=True)

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
    
    unidades_totales = [int((g.ocupacion_actual / (g.filas * g.columnas)) * g.capacidad_max) for g in galpones]
    
    data = {
        "Galpón": [f"Galpón {g.id_galpon}" for g in galpones],
        "Categoría asignada": [g.categoria for g in galpones],
        "Capacidad Máxima": [g.capacidad_max for g in galpones],
        "Ocupación Actual (Unidades)": unidades_totales,
        "Disponibilidad Real (Unidades)": [g.capacidad_max - unidades_totales[i] for i, g in enumerate(galpones)]
    }
    st.dataframe(pd.DataFrame(data), use_container_width=True)