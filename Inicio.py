import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Nodo Agrícola Avanzado - EAFIT",
    page_icon="🌱",
    layout="wide"
)

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("⚙️ Panel de Control")
uploaded_file = st.sidebar.file_uploader('1. Cargue el archivo CSV del ESP32', type=['csv'])

# Inicializar variables de control en el sidebar
rango_datos = 100
mostrar_tendencia = False

# Título principal en la zona central
st.title('🌱 Análisis de Nodo Agrícola - Universidad EAFIT')
st.markdown("Monitoreo inteligente y análisis predictivo de nivel de silo, flujo de agua y peso de cosecha.")

if uploaded_file is not None:
    try:
        # Lectura de datos omitiendo las primeras 3 líneas de metadatos del sensor
        df_completo = pd.read_csv(uploaded_file, skiprows=3)

        # Detectar columna de tiempo sin importar mayúsculas/minúsculas
        columna_tiempo = [col for col in df_completo.columns if col.lower() == 'time']
        
        if columna_tiempo:
            df_completo[columna_tiempo[0]] = pd.to_datetime(df_completo[columna_tiempo[0]])
            df_completo = df_completo.sort_values(columna_tiempo[0])
            df_completo = df_completo.set_index(columna_tiempo[0])

        # Mapeo de variables esperadas
        variables = {
            'nivel_silo_pct': '📦 Nivel del Silo (%)',
            'flujo_agua_lpm': '💧 Flujo de Agua (L/min)',
            'peso_cosecha_kg': '⚖️ Peso Cosecha (kg)'
        }

        # Filtrar solo columnas existentes en el archivo cargado
        v_disponibles = [v for v in variables.keys() if v in df_completo.columns]

        if not v_disponibles:
            st.error("No se encontraron las columnas esperadas en el CSV. Verifica los encabezados.")
        else:
            # Controles adicionales en el Sidebar que dependen de los datos cargados
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 Filtros de Visualización")
            
            # Control para limitar la cantidad de datos visibles
            max_filas = len(df_completo)
            rango_datos = st.sidebar.slider(
                "Cantidad de registros a visualizar", 
                min_value=min(5, max_filas), 
                max_value=max_filas, 
                value=max_filas
            )
            
            # Filtrar el dataframe según el slider
            df = df_completo.tail(rango_datos)

            # Opción para activar línea de tendencia en Scatter Plot
            st.sidebar.markdown("---")
            st.sidebar.subheader("📈 Configuración de Gráficos")
            mostrar_tendencia = st.sidebar.checkbox("Mostrar Línea de Tendencia (Regresión)", value=True)

            # --- SECCIÓN 1: MÉTRICAS EN TIEMPO REAL CON DELTAS Y ALERTAS ---
            st.subheader("📊 Estado Actual del Nodo (Último Registro)")
            
            # Extraer la última y penúltima fila de datos para calcular Deltas
            ultimo_registro = df_completo.iloc[-1]
            tiene_anterior = len(df_completo) > 1
            penultimo_registro = df_completo.iloc[-2] if tiene_anterior else ultimo_registro
            
            col_m1, col_m2, col_m3 = st.columns(3)
            
            with col_m1:
                val_silo = float(ultimo_registro.get('nivel_silo_pct', 0))
                val_silo_ant = float(penultimo_registro.get('nivel_silo_pct', 0))
                delta_silo = val_silo - val_silo_ant if tiene_anterior else 0.0
                
                st.metric(
                    label=variables['nivel_silo_pct'], 
                    value=f"{val_silo:.1f} %", 
                    delta=f"{delta_silo:+.1f} % respecto al anterior"
                )
                if val_silo < 20:
                    st.error("🚨 ALERTA: Nivel de silo críticamente bajo (< 20%)")
                    
            with col_m2:
                val_flujo = float(ultimo_registro.get('flujo_agua_lpm', 0))
                val_flujo_ant = float(penultimo_registro.get('flujo_agua_lpm', 0))
                delta_flujo = val_flujo - val_flujo_ant if tiene_anterior else 0.0
                
                st.metric(
                    label=variables['flujo_agua_lpm'], 
                    value=f"{val_flujo:.2f} L/min", 
                    delta=f"{delta_flujo:+.2f} L/min respecto al anterior",
                    delta_color="inverse"  # Cambia a rojo si sube el flujo (alertas de gasto de agua)
                )
                if val_flujo > 15:
                    st.warning("⚠️ ADVERTENCIA: Flujo de agua inusualmente alto (> 15 L/min)")
                    
            with col_m3:
                val_peso = float(ultimo_registro.get('peso_cosecha_kg', 0))
                val_peso_ant = float(penultimo_registro.get('peso_cosecha_kg', 0))
                delta_peso = val_peso - val_peso_ant if tiene_anterior else 0.0
                
                st.metric(
                    label=variables['peso_cosecha_kg'], 
                    value=f"{val_peso:.1f} kg", 
                    delta=f"{delta_peso:+.1f} kg recolectados"
                )

            st.markdown("---")

            # --- SECCIÓN 2: MEDIDORES (GAUGES) ---
            st.subheader("⏱️ Indicadores Análogos en Tiempo Real")
            col_g1, col_g2, col_g3 = st.columns(3)

            with col_g1:
                fig_silo = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=val_silo,
                    title={'text': "Nivel del Silo"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 20], 'color': "rgba(255, 0, 0, 0.3)"},
                            {'range': [20, 100], 'color': "rgba(0, 255, 0, 0.1)"}
                        ]
                    }
                ))
                fig_silo.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_silo, use_container_width=True)

            with col_g2:
                fig_flujo = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=val_flujo,
                    title={'text': "Flujo de Agua"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 30]},
                        'bar': {'color': "teal"},
                        'steps': [
                            {'range': [0, 15], 'color': "rgba(0, 255, 0, 0.1)"},
                            {'range': [15, 30], 'color': "rgba(255, 165, 0, 0.3)"}
                        ]
                    }
                ))
                fig_flujo.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_flujo, use_container_width=True)

            with col_g3:
                max_historico_peso = max(float(df_completo['peso_cosecha_kg'].max()), 100.0)
                fig_peso = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=val_peso,
                    title={'text': "Peso Cosecha Total"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, max_historico_peso]},
                        'bar': {'color': "darkgreen"}
                    }
                ))
                fig_peso.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_peso, use_container_width=True)

            st.markdown("---")

            # --- SECCIÓN 3: PESTAÑAS DE ANÁLISIS ---
            tab1, tab2, tab3 = st.tabs(["📈 Histórico Temporal", "🔍 Gráfica de Correlación", "📋 Tabla de Datos"])

            with tab1:
                variable_sel = st.selectbox(
                    "Seleccione variable para analizar el rango temporal filtrado:",
                    options=v_disponibles,
                    format_func=lambda x: variables[x]
                )
                chart_type = st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barra"])
                
                if chart_type == "Línea":
                    st.line_chart(df[variable_sel])
                elif chart_type == "Área":
                    st.area_chart(df[variable_sel])
                else:
                    st.bar_chart(df[variable_sel])

            with tab2:
                st.subheader("Análisis Estadístico de Relación (Scatter Plot)")
                if len(v_disponibles) >= 2:
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        var_x = st.selectbox("Variable Eje X", options=v_disponibles, format_func=lambda x: variables[x], index=0)
                    with col_c2:
                        var_y = st.selectbox("Variable Eje Y", options=v_disponibles, format_func=lambda x: variables[x], index=1 if len(v_disponibles) > 1 else 0)
                    
                    # Generar gráfica con o sin línea de tendencia según el sidebar
                    trend_mode = "ols" if mostrar_tendencia else None
                    
                    fig_scatter = px.scatter(
                        df, 
                        x=var_x, 
                        y=var_y, 
                        labels={var_x: variables[var_x], var_y: variables[var_y]},
                        template="plotly_white",
                        color_discrete_sequence=['#2ca02c'],
                        trendline=trend_mode
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.warning("Se requieren al menos 2 variables numéricas en el archivo para trazar correlaciones.")

            with tab3:
                st.subheader("Exploración y Exportación de Datos Filtrados")
                st.write(f"Mostrando los últimos {rango_datos} registros de acuerdo al filtro de la barra lateral.")
                st.dataframe(df, use_container_width=True)
                
                # Conversión segura a CSV del set de datos filtrado
                csv_data = df.to_csv().encode('utf-8')
                
                try:
                    fecha_nombre = df.index.max().strftime('%Y%m%d_%H%M')
                except AttributeError:
                    fecha_nombre = datetime.now().strftime('%Y%m%d_%H%M')

                st.download_button(
                    label="📥 Descargar segmento filtrado en CSV",
                    data=csv_data,
                    file_name=f"nodo_filtrado_{fecha_nombre}.csv",
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f'Error al procesar el archivo: {str(e)}')
else:
    st.info('👋 Bienvenido. Por favor, cargue un archivo CSV desde el panel izquierdo para inicializar los medidores y gráficos.')

st.markdown("""
    ---
    Desarrollado para el análisis de datos de sensores agrícolas.
    Ubicación: Universidad EAFIT, Medellín, Colombia
""")
