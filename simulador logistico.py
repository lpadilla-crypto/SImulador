import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página web
st.set_page_config(page_title="Simulador Logístico CEDIS con WMS", layout="wide")

# --- LÓGICA DEL SIMULADOR (POO) ---
class Galpon:
    def __init__(self, id_galpon, categoria_defecto, capacidad_defecto, filas=6, columnas=10):
        self.id_galpon = id_galpon
        self.filas = filas
        self.columnas = columnas
        
        # Estado de sesión para categoría y capacidad máxima
        if f"cat_{id_galpon}" not in st.session_state:
            st.session_state[f"cat_{id_galpon}"] = categoria_defecto
        if f"cap_{id_galpon}" not in st.session_state:
            st.session_state[f"cap_{id_galpon}"] = capacidad_defecto

        # Inicializar el mapa físico del galpón vacío (Matriz de strings para guardar qué producto hay en cada slot)
        # Si la celda está vacía tendrá el valor "Disponible"
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
        # La ocupación real es el conteo de celdas que NO están "Disponible"
        return np.sum(self.mapa_racks != "Disponible")

    def espacio_disponible(self):
        return (self.filas * self.columnas) - self.ocupacion_actual

    def almacenar_en_posicion(self, fila, columna, producto):
        # Validar si el slot está libre
        if self.mapa_racks[fila, columna] != "Disponible":
            return False, "La posición física seleccionada ya se encuentra OCUPADA."
        
        # Registrar producto en la posición física exacta
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
        return True, f"Se asignaron automáticamente {colocados} posiciones de rack de forma ordenada."

# Inicialización de los galpones
galpones = [
    Galpon(1, "Línea Blanca", 60, filas=6, columnas=10),      # 60 posiciones de rack
    Galpon(2, "Televisores y Audio", 60, filas=6, columnas=10), # 60 posiciones de rack
    Galpon(3, "Pequeños Electrodomésticos", 80, filas=8, columnas=10), # 80 posiciones
    Galpon(4, "Tecnología y Gadgets", 50, filas=5, columnas=10) # 50 posiciones
]

# --- INTERFAZ GRÁFICA (STREAMLIT) ---
st.title("🚢 Sistema de Simulación de Importaciones y CEDIS con Reglas WMS")
st.markdown("Gestione el ingreso ordenado de mercancía mediante **Zonificación Estratégica de Ubicaciones**.")

# Panel Lateral: Entrada Dirigida de Mercancía
st.sidebar.header("📥 Recepción de Mercancía")

categorias_existentes = ["Línea Blanca", "Televisores y Audio", "Pequeños Electrodomésticos", "Tecnología y Gadgets", "Otros"]
producto_ingreso = st.sidebar.selectbox("1. Tipo de producto que ingresa:", categorias_existentes)

lista_galpones_nombres = [f"Galpón {g.id_galpon} (Zona: {g.categoria})" for g in galpones]
galpon_seleccionado_nombre = st.sidebar.selectbox("2. Seleccione Galpón de Destino:", lista_galpones_nombres)
id_galpon_destino = int(galpon_seleccionado_nombre.split(" ")[1])
g_destino = galpones[id_galpon_destino - 1]

# Modo de Asignación de Ubicación
modo_asignacion = st.sidebar.radio("3. Estrategia de Ubicación:", ["Sugerida por Sistema (Auto)", "Manual por Operario (Seleccionar Rack)"])

if modo_asignacion == "Sugerida por Sistema (Auto)":
    cantidad_ingreso = st.sidebar.number_input("Cantidad de Racks a ocupar:", min_value=1, max_value=50, value=5)
    
    if st.sidebar.button("Procesar Ingreso Automático"):
        # Alerta de Regla de Negocio si la zona no coincide
        if g_destino.categoria != producto_ingreso:
            st.sidebar.error(f"❌ Rechazado por WMS: No puedes mezclar '{producto_ingreso}' en la Zona Reservada para '{g_destino.categoria}'.")
        else:
            exito, msg = g_destino.almacenamiento_automatico(producto_ingreso, cantidad_ingreso)
            if exito:
                st.sidebar.success(f"✅ WMS: {msg}")
                st.rerun()
            else:
                st.sidebar.error(f"⚠️ {msg}")

else:  # Asignación de Posición Manual Física
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Coordenadas del Almacén:**")
    fila_elegida = st.sidebar.selectbox("Seleccione Fila (Rack):", [f"Fila {i+1}" for i in range(g_destino.filas)])
    col_elegida = st.sidebar.selectbox("Seleccione Columna (Slot):", [f"Columna {i+1}" for i in range(g_destino.columnas)])
    
    f_idx = int(fila_elegida.split(" ")[1]) - 1
    c_idx = int(col_elegida.split(" ")[1]) - 1

    if st.sidebar.button("Asignar Posición Manual"):
        if g_destino.categoria != producto_ingreso:
            st.sidebar.error(f"❌ Alerta de Calidad: La posición física pertenece a la zona de '{g_destino.categoria}' y no coincide con el producto '{producto_ingreso}'.")
        else:
            exito, msg = g_destino.almacenar_en_posicion(f_idx, c_idx, producto_ingreso)
            if exito:
                st.sidebar.success(f"✅ Posición [{fila_elegida}, {col_elegida}] bloqueada.")
                st.rerun()
            else:
                st.sidebar.error(f"⚠️ {msg}")

if st.sidebar.button("🔄 Vaciar Almacén (Reiniciar Todo)"):
    for g in galpones:
        st.session_state[f"mapa_{g.id_galpon}"] = np.full((g.filas, g.columnas), "Disponible", dtype=object)
    st.rerun()


# Bloque Principal: Monitor de Capacidad en Tiempo Real
st.subheader("📊 Ocupación General por Zonas de Capacidad")
col1, col2, col3, col4 = st.columns(4)
columnas = [col1, col2, col3, col4]

for i, g in enumerate(galpones):
    with columnas[i]:
        st.markdown(f"### Galpón {g.id_galpon}")
        st.caption(f"**Categoría Designada:** {g.categoria}")
        porcentaje = (g.ocupacion_actual / g.capacidad_max) if g.capacidad_max > 0 else 0.0
        st.metric(label="Racks Ocupados", value=f"{g.ocupacion_actual} / {g.capacidad_max} Slots")
        st.progress(porcentaje)

st.markdown("---")

# Pestañas de Gestión Analítica
tab1, tab2, tab3 = st.tabs(["🗺️ Layout Físico en Planta", "⚙️ Re-Zonificación de Infraestructura", "📈 Resumen General de Inventario"])

with tab1:
    st.subheader("🗺️ Mapa Logístico de Racks y Bahías de Almacenamiento")
    st.markdown("Auditoría visual del piso. Pase el cursor sobre los recuadros para identificar el contenido exacto de la ubicación.")
    
    id_layout = st.selectbox("Seleccione el Galpón a auditar:", [1, 2, 3, 4], key="layout_select")
    g_layout = galpones[id_layout - 1]
    
    # KPIs dinámicos de la posición
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Capacidad Estructural", f"{g_layout.capacidad_max} Posiciones")
    mc2.metric("Posiciones Asignadas (Físicas)", f"{g_layout.ocupacion_actual} Racks")
    mc3.metric("Posiciones Libres Operativas", f"{g_layout.espacio_disponible()} Racks")
    
    # Renderizado CSS Inteligente de la Matriz Organizada
    html_grid = "<div style='display: grid; grid-template-columns: repeat("+str(g_layout.columnas)+", 1fr); gap: 6px;'>"
    for f in range(g_layout.filas):
        for c in range(g_layout.columnas):
            contenido = g_layout.mapa_racks[f, c]
            codigo_ubicacion = f"R{f+1}-C{c+1}"
            
            # Cambiar colores según las categorías reales del WMS
            if contenido == "Disponible":
                color_bg = "#10B981"  # Verde disponible
                texto_tooltip = "Espacio Vacío"
            else:
                color_bg = "#EF4444"  # Rojo Ocupado
                texto_tooltip = f"Contenido: {contenido}"
                
            html_grid += f"""
            <div style='background-color: {color_bg}; color: white; padding: 12px 2px; text-align: center; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: help;' 
                 title='Ubicación: {codigo_ubicacion} | {texto_tooltip}'>
                 {codigo_ubicacion}
            </div>
            """
    html_grid += "</div>"
    st.markdown(html_grid, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: 10px;'><span style='color: #10B981;'>■</span> Posición Disponible &nbsp;&nbsp;&nbsp;&nbsp; <span style='color: #EF4444;'>■</span> Posición Asignada / Bloqueada</p>", unsafe_allow_html=True)

with tab2:
    st.subheader("⚙️ Modificación de Layout y Re-Zonificación")
    st.markdown("Si cambia el modelo de negocio, puede re-asignar qué categoría tiene derecho a usar el galpón de forma prioritaria.")
    
    id_modificar = st.selectbox("Seleccione el Galpón a actualizar:", [1, 2, 3, 4], key="config")
    g_a_modificar = galpones[id_modificar - 1]
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        nueva_categoria = st.text_input("Cambiar Categoría Autorizada:", value=g_a_modificar.categoria)
    with col_input2:
        st.markdown(f"**Capacidad Física Estructural:** {g_a_modificar.capacidad_max} Racks (Fijo por dimensiones de {g_a_modificar.filas}x{g_a_modificar.columnas}).")
        
    if st.button("💾 Guardar Nueva Configuración de Zona"):
        g_a_modificar.categoria = nueva_categoria
        st.success(f"⚙️ ¡Zonificación del Galpón {id_modificar} actualizada con éxito!")
        st.rerun()

with tab3:
    st.subheader("📊 Cuadro de Mando Consolidado")
    data = {
        "Galpón / Zona": [f"Galpón {g.id_galpon}" for g in galpones],
        "Zonificación de Categoría": [g.categoria for g in galpones],
        "Total Posiciones Físicas": [g.capacidad_max for g in galpones],
        "Posiciones Utilizadas": [g.ocupacion_actual for g in galpones],
        "Slots Vacíos": [g.espacio_disponible() for g in galpones]
    }
    st.dataframe(pd.DataFrame(data), use_container_width=True)