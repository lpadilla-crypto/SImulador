import streamlit as st
import pandas as pd

# Configuración de la página web
st.set_page_config(page_title="Simulador Logístico CEDIS", layout="wide")

# --- LÓGICA DEL SIMULADOR (POO) ---
class Galpon:
    def __init__(self, id_galpon, categoria_defecto, capacidad_defecto):
        self.id_galpon = id_galpon
        
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
        # Asegurar que la ocupación no supere una nueva capacidad reducida
        st.session_state[f"galpon_{self.id_galpon}"] = min(valor, self.capacidad_max)

    def espacio_disponible(self):
        return max(0, self.capacidad_max - self.ocupacion_actual)

    def almacenar(self, cantidad):
        if cantidad <= self.espacio_disponible():
            self.ocupacion_actual += cantidad
            return True
        return False

# Inicialización dinámica de los galpones en memoria/estado de sesión
galpones = [
    Galpon(1, "Línea Blanca", 500),
    Galpon(2, "Televisores y Audio", 800),
    Galpon(3, "Pequeños Electrodomésticos", 1200),
    Galpon(4, "Tecnología y Gadgets", 1000)
]

# --- INTERFAZ GRÁFICA (STREAMLIT) ---
st.title("🚢 Sistema de Simulación de Importaciones y CEDIS")
st.markdown("Gestione el ingreso de mercancía, configure la infraestructura y monitoree los galpones en tiempo real.")

# Panel Lateral: Entrada de Mercancía
st.sidebar.header("📥 Entrada de Importaciones")
# Elige dinámicamente según las categorías vigentes de los galpones
categorias_vivas = [g.categoria for g in galpones]
categoria_seleccionada = st.sidebar.selectbox(
    "Seleccione el tipo de producto que ingresa:",
    categorias_vivas
)
cantidad_ingreso = st.sidebar.number_input("Cantidad de unidades:", min_value=1, max_value=2000, value=150)

if st.sidebar.button("Simular Desembarco y Almacenaje"):
    galpon_destino = next((g for g in galpones if g.categoria == categoria_seleccionada), None)
    if galpon_destino:
        if galpon_destino.almacenar(cantidad_ingreso):
            st.sidebar.success(f"✅ Éxito: Se almacenaron {cantidad_ingreso} unidades en el Galpón {galpon_destino.id_galpon}.")
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
        st.caption(f"**Categoría:** {g.categoria}")
        porcentaje = (g.ocupacion_actual / g.capacidad_max) if g.capacidad_max > 0 else 0.0
        # Asegurar tope visual del 100%
        porcentaje = min(1.0, porcentaje) 
        st.metric(label="Ocupación", value=f"{g.ocupacion_actual} / {g.capacidad_max} unds")
        st.progress(porcentaje)

st.markdown("---")

# Nuevas Solicitudes organizadas en Pestañas (Tabs)
tab1, tab2, tab3 = st.tabs(["🔍 Consulta Individual", "⚙️ Configurar Capacidad de Galpones", "📈 Tabla General"])

with tab1:
    st.subheader("🔍 Inspección Detallada por Galpón")
    id_elegido = st.selectbox("Seleccione el Galpón que desea auditar:", [1, 2, 3, 4], key="inspeccion")
    g_seleccionado = galpones[id_elegido - 1]
    
    # KPIs grandes e individuales
    c1, c2, c3 = st.columns(3)
    c1.metric("Unidades Almacenadas", f"{g_seleccionado.ocupacion_actual} unds")
    c2.metric("Capacidad Total Asignada", f"{g_seleccionado.capacidad_max} unds")
    c3.metric("Espacio Disponible Inmediato", f"{g_seleccionado.espacio_disponible()} unds", delta=f"{g_seleccionado.espacio_disponible()} libres", delta_color="inverse")

with tab2:
    st.subheader("⚙️ Optimización de Infraestructura")
    st.markdown("Modifique los techos límites de almacenamiento o reasigne categorías si la estrategia de distribución cambia.")
    
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
        st.success(f"⚙️ ¡Galpón {id_modificar} actualizado con éxito! Los cambios ya se reflejan en el monitor superior.")
        st.rerun()

with tab3:
    st.subheader("📊 Cuadro de Mando Consolidado")
    data = {
        "Galpón": [f"Galpón {g.id_galpon}" for g in galpones],
        "Categoría asignada": [g.categoria for g in galpones],
        "Capacidad Máxima": [g.capacidad_max for g in galpones],
        "Ocupación Actual": [g.ocupacion_actual for g in galpones],
        "Disponibilidad Real": [g.espacio_disponible() for g in galpones]
    }
    st.dataframe(pd.DataFrame(data), use_container_width=True)