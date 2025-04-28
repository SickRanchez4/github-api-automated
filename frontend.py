import streamlit as st
import plotly.express as px
import pandas as pd
from backend import generar_informe_actividad, seguimiento_metricas, establecer_configuraciones, analizar_contribuciones, analizar_issues, analizar_pull_requests_por_mes

st.set_page_config(layout="wide")
st.title("🎯 Interfaz Interactiva - Git")

st.sidebar.title("Menú")

seccion = st.sidebar.radio(
    "Selecciona una sección",
    [":house: Principal", ":bar_chart: Reportes", ":clipboard: Tareas"]
)

if seccion == ":house: Principal":
# --------- SECCIÓN PRINCIPAL ---------

    with st.container():
        st.subheader("🔹 Sección Principal")

        col1, col2 = st.columns(2)
        with col1:
            input1 = st.text_input("Dueño del Repositorio")
        with col2:
            input2 = st.text_input("Nombre del Repositorio")

        access_level = st.radio("Personal Access Token", ["No", "Si"], horizontal=True)

        if access_level == "Si":
            extra_input = st.file_uploader("Seleccione el archivo de texto que contiene el Personal Acces Token:", type=["txt"])

        if st.button("Guardar"):
            establecer_configuraciones(input1, input2, extra_input)
            st.write("¡Configuraciones establecidas!")
    st.markdown("---")
    
elif seccion == ":bar_chart: Reportes":
    # --------- SECCIÓN REPORTES ---------
    st.subheader("⚙️ Reports")

    col_opt1, col_opt2, col_opt3, col_opt4 = st.columns(4)

    action = None

    with col_opt1:
        if st.button("📊 Ver Gráfico de Barras"):
            action = "bar"
    with col_opt2:
        if st.button("🧩 Ver Pie Chart"):
            action = "pie"
    with col_opt3:
        if st.button("💡 Ver 4 Tarjetas"):
            action = "cards"
    with col_opt4:
        if st.button("📈 Ver Gráfico de Líneas"):
            action = "line"

    st.markdown("---")

    # --------- SECCIÓN RESULTADOS ---------
    st.subheader("📌 Resultados")

    # Datos de ejemplo
    data = pd.DataFrame({
        "Usuario": ["NirDiamant", "tevfikcagridural", "lzytitan494", "Nick"],
        "Commits": [213, 21, 16, 15]
    })

    if action == "bar":
        data = analizar_issues()
        data_reset = data.reset_index().rename(columns={"index": "Mes"})
        data_reset["Mes"] = data_reset["Mes"].astype(str) # Convertir Period a String
        fig = px.bar(
            data_reset, 
            x="Mes", 
            y=["Abiertos", "Cerrados"], 
            title="Issues Abiertos y Cerrados por Mes", 
            labels={"value": "Cantidad de Issues", "Mes": "Mes"}, 
            barmode="stack")
        
        st.plotly_chart(fig, use_container_width=True)

    elif action == "pie":
        data = analizar_contribuciones()
        fig = px.pie(data, names="Usuario", values="Commits", title="Distribución de Commits")
        st.plotly_chart(fig, use_container_width=True)

    elif action == "cards":
        issues_creados, pull_requests_mergeados = generar_informe_actividad()
        promedio_respuesta_issues, promedio_merge_prs = seguimiento_metricas()
        card1, card2, card3, card4 = st.columns(4)
        with card1:
            st.metric("Issues Creadas", issues_creados)
        with card2:
            st.metric("PRs Mergeados", pull_requests_mergeados)
        with card3:
            st.metric("Resp. Promedio Issues", promedio_respuesta_issues)
        with card4:
            st.metric("Tiempo Merge PR", promedio_merge_prs)

    elif action == "line":
        st.title("Pull Requests por Mes")
        data = analizar_pull_requests_por_mes()
        fig = px.line(data, x="Mes", y="Pull Requests", markers=True, title="Evolución de Pull Requests")
        st.plotly_chart(fig, use_container_width=True)

elif seccion == ":clipboard: Tareas":
    st.title("Gestión de Tareas")
    st.write("Aquí Gestionamos las acciones de GitHub...")


