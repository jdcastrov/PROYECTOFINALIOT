import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Nodo Agrícola - EAFIT",
    page_icon="🌱",
    layout="wide"
)

st.title('🌱 Análisis de Nodo Agrícola - Universidad EAFIT')
st.markdown("Análisis de datos de nivel de silo, flujo de agua y peso de cosecha recolectados por sensores ESP32.")

eafit_location = pd.DataFrame({
    'lat': [6.2006],
    'lon': [-75.5783],
    'location': ['Universidad EAFIT']
})

st.subheader("📍 Ubicación de los Sensores - Universidad EAFIT")
st.map(eafit_location, zoom=15)

uploaded_file = st.file_uploader('Seleccione archivo CSV', type=['csv'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, skiprows=3)

        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time'])
            df = df.set_index('Time')

        variables = {
            'nivel_silo_pct': '📦 Nivel del Silo (%)',
            'flujo_agua_lpm': '💧 Flujo de Agua (L/min)',
            'peso_cosecha_kg': '⚖️ Peso Cosecha (kg)'
        }

        variable_disponible = [v for v in variables.keys() if v in df.columns]

        if not variable_disponible:
            st.error("No se encontraron las columnas esperadas en el CSV.")
        else:
            variable_sel = st.selectbox(
                "Seleccione variable a analizar",
                options=variable_disponible,
                format_func=lambda x: variables[x]
            )

            tab1, tab2, tab3, tab4 = st.tabs(["📈 Visualización", "📊 Estadísticas", "🔍 Filtros", "🗺️ Sitio"])

            with tab1:
                st.subheader(f'Visualización - {variables[variable_sel]}')
                chart_type = st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barra"])
                if chart_type == "Línea":
                    st.line_chart(df[variable_sel])
                elif chart_type == "Área":
                    st.area_chart(df[variable_sel])
                else:
                    st.bar_chart(df[variable_sel])
                if st.checkbox('Mostrar datos crudos'):
                    st.write(df)

            with tab2:
                st.subheader('Análisis Estadístico')
                stats = df[variable_sel].describe()
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(stats)
                with col2:
                    st.metric("Promedio", f"{stats['mean']:.2f}")
                    st.metric("Máximo", f"{stats['max']:.2f}")
                    st.metric("Mínimo", f"{stats['min']:.2f}")
                    st.metric("Desviación Estándar", f"{stats['std']:.2f}")

            with tab3:
                st.subheader('Filtros de Datos')
                min_v = float(df[variable_sel].min())
                max_v = float(df[variable_sel].max())
                mean_v = float(df[variable_sel].mean())
                if min_v == max_v:
                    st.warning(f"Todos los valores son iguales: {min_v:.2f}")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        min_val = st.slider('Valor mínimo', min_v, max_v, mean_v, key="min_val")
                        st.write(f"Registros superiores a {min_val:.2f}:")
                        st.dataframe(df[df[variable_sel] > min_val])
                    with col2:
                        max_val = st.slider('Valor máximo', min_v, max_v, mean_v, key="max_val")
                        st.write(f"Registros inferiores a {max_val:.2f}:")
                        st.dataframe(df[df[variable_sel] < max_val])

            with tab4:
                st.subheader("Información del Sitio")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### Ubicación del Sensor")
                    st.write("**Universidad EAFIT**")
                    st.write("- Latitud: 6.2006")
                    st.write("- Longitud: -75.5783")
                    st.write("- Altitud: ~1,495 msnm")
                with col2:
                    st.write("### Detalles del Sensor")
                    st.write("- Tipo: ESP32")
                    st.write("- Variables: Nivel silo, Flujo agua, Peso cosecha")
                    st.write("- Frecuencia: 5 segundos")
                    st.write("- Ubicación: Campus universitario")

    except Exception as e:
        st.error(f'Error al procesar el archivo: {str(e)}')
else:
    st.warning('Por favor, cargue un archivo CSV para comenzar el análisis.')

st.markdown("""
    ---
    Desarrollado para el análisis de datos de sensores agrícolas.
    Ubicación: Universidad EAFIT, Medellín, Colombia
""")
