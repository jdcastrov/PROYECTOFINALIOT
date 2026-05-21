import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Nodo Agrícola - EAFIT",
    page_icon="🌱",
    layout="wide"
)

st.title('🌱 Análisis de Nodo Agrícola - Universidad EAFIT')
st.markdown("Monitoreo en tiempo real de nivel de silo, flujo de agua y peso de cosecha.")

uploaded_file = st.file_uploader('Seleccione archivo CSV', type=['csv'])

if uploaded_file is not None:
    try:
        # Lectura de datos omitiendo metadatos si es necesario
        df = pd.read_csv(uploaded_file, skiprows=3)

        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time'])
            df = df.sort_values('Time')
            df = df.set_index('Time')

        variables = {
            'nivel_silo_pct': '📦 Nivel del Silo (%)',
            'flujo_agua_lpm': '💧 Flujo de Agua (L/min)',
            'peso_cosecha_kg': '⚖️ Peso Cosecha (kg)'
        }

        # Filtrar solo columnas existentes en el archivo
        v_disponibles = [v for v in variables.keys() if v in df.columns]

        if not v_disponibles:
            st.error("No se encontraron las columnas esperadas en el CSV.")
        else:
            # --- SECCIÓN 1: MÉTRICAS EN TIEMPO REAL Y ALERTAS ---
            st.subheader("📊 Estado Actual del Nodo")
            
            # Obtener el último registro disponible
            ultimo_registro = df.iloc[-1]
            
            col_m1, col_m2, col_m3 = st.columns(3)
            
            with col_m1:
                val_silo = ultimo_registro.get('nivel_silo_pct', 0)
                st.metric(label=variables['nivel_silo_pct'], value=f"{val_silo:.1f} %")
                if val_silo < 20:
                    st.error("🚨 ALERTA: Nivel de silo críticamente bajo (< 20%)")
                    
            with col_m2:
                val_flujo = ultimo_registro.get('flujo_agua_lpm', 0)
                st.metric(label=variables['flujo_agua_lpm'], value=f"{val_flujo:.2f} L/min")
                if val_flujo > 15:
                    st.warning("⚠️ ADVERTENCIA: Flujo de agua inusualmente alto (> 15 L/min)")
                    
            with col_m3:
                val_peso = ultimo_registro.get('peso_cosecha_kg', 0)
                st.metric(label=variables['peso_cosecha_kg'], value=f"{val_peso:.1f} kg")

            st.markdown("---")

            # --- SECCIÓN 2: MEDIDORES (GAUGES) ---
            st.subheader("⏱️ Indicadores de Nivel y Flujo")
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
                fig_silo.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
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
                fig_flujo.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_flujo, use_container_width=True)

            with col_g3:
                # Gauge adaptativo basado en el máximo histórico del dataset actual
                max_historico_peso = max(float(df['peso_cosecha_kg'].max()), 100.0)
                fig_peso = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=val_peso,
                    title={'text': "Peso Cosecha"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, max_historico_peso]},
                        'bar': {'color': "darkgreen"}
                    }
                ))
                fig_peso.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_peso, use_container_width=True)

            st.markdown("---")

            # --- SECCIÓN 3: PESTAÑAS DE ANÁLISIS ---
            tab1, tab2, tab3 = st.tabs(["📈 Histórico", "🔍 Correlación", "📋 Datos Crudos"])

            with tab1:
                variable_sel = st.selectbox(
                    "Seleccione variable para el gráfico histórico",
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
                st.subheader("Análisis de Relación entre Variables")
                if len(v_disponibles) >= 2:
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        var_x = st.selectbox("Variable Eje X", options=v_disponibles, format_func=lambda x: variables[x], index=0)
                    with col_c2:
                        var_y = st.selectbox("Variable Eje Y", options=v_disponibles, format_func=lambda x: variables[x], index=1 if len(v_disponibles) > 1 else 0)
                    
                    fig_scatter = px.scatter(
                        df, 
                        x=var_x, 
                        y=var_y, 
                        labels={var_x: variables[var_x], var_y: variables[var_y]},
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.warning("Se requieren al menos 2 variables numéricas en el archivo para trazar correlaciones.")

            with tab3:
                st.subheader("Exploración e Exportación de Datos")
                st.dataframe(df, use_container_width=True)
                
                # Conversión de DataFrame a CSV para descarga
                csv_data = df.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Descargar datos en CSV",
                    data=csv_data,
                    file_name=f"datos_nodo_{df.index.max().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f'Error al procesar el archivo: {str(e)}')
else:
    st.warning('Por favor, cargue un archivo CSV para comenzar el análisis.')

st.markdown("""
    ---
    Desarrollado para el análisis de datos de sensores agrícolas.
    Ubicación: Universidad EAFIT, Medellín, Colombia
""")
