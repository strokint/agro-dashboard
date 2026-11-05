import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="Сельхозтехника Иркутской области", layout="wide")
st.title("🚜 Мониторинг сельскохозяйственной техники Иркутской области")
st.markdown("**Дата актуализации данных: 05.11.2026")

# --- ДАННЫЕ (Здесь вы можете обновлять цифры) ---
# 1. Общая оснащенность
metrics_data = {
    "Тракторы": 3286,
    "Зерноуборочные комбайны": 1094,
    "Кормоуборочные комбайны": 140,
    "Другая техника": 7000 # Более 7 тысяч
}

# 2. Техническая оснащенность (%)
readiness_data = pd.DataFrame({
    "Техника": ["Тракторы", "Зерноуборочные комбайны", "Кормоуборочные комбайны", "Другая техника"],
    "Готовность, %": [52, 30, 59, 55]
})

# 3. Нагрузка на единицу техники (га)
load_data = pd.DataFrame({
    "Техника": ["Тракторы", "Зерноуборочные комбайны", "Кормоуборочные комбайны"],
    "Факт": [233, 390, 472],
    "Норматив": [120, 117, 280]
})

# 4. Динамика обновления и выбытия (2020-2026)
years = [str(y) for y in range(2020, 2027)]
years[-1] = "2026 (на тек. дату)"

tractors_dyn = pd.DataFrame({
    "Год": years,
    "Обновление, %": [3.6, 3.6, 2.2, 3.3, 2.4, 2.4, 1.16],
    "Выбытие, %": [7.3, 5.3, 4.6, 4.8, 5.3, 5.3, 4.16]
})

grain_dyn = pd.DataFrame({
    "Год": years,
    "Обновление, %": [6.1, 4.7, 4.9, 3.7, 3.6, 1.8, 1.74],
    "Выбытие, %": [5.5, 4.7, 4.8, 3.9, 1.1, 0.7, 5.62]
})

forage_dyn = pd.DataFrame({
    "Год": years,
    "Обновление, %": [8.9, 5.4, 4.7, 2.8, 1.4, 2.0, 2.14],
    "Выбытие, %": [14.6, 8.1, 6.8, 6.8, 7.7, 7.0, 0.0]
})

# 5. Приобретение техники (План vs Факт)
# Внимание: текст на стр. 3 и графики на стр. 4 немного расходятся. 
# Здесь использованы данные с графиков (стр. 4).
purchase_2025 = pd.DataFrame({
    "Техника": ["Тракторы", "Зерноуборочные", "Кормоуборочные", "Прочая техника"],
    "План": [120, 50, 10, 500],
    "Факт": [82, 20, 4, 415]
})

purchase_2026 = pd.DataFrame({
    "Техника": ["Тракторы", "Зерноуборочные", "Кормоуборочные", "Прочая техника"],
    "План": [100, 30, 5, 450],
    "Факт": [38, 19, 3, 220]
})

# --- ОТОБРАЖЕНИЕ ДАННЫХ ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Обзор", "📈 Динамика (2020-2026)", "🚜 Приобретение", "📋 Лизинг и заявки"])

with tab1:
    st.subheader("Наличие техники")
    cols = st.columns(4)
    for i, (name, value) in enumerate(metrics_data.items()):
        cols[i].metric(name, f"{value:,} ед.")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Техническая обеспеченность, %")
        fig_ready = px.bar(readiness_data, x="Техника", y="Готовность, %", text="Готовность, %", color_discrete_sequence=['#4472C4'])
        fig_ready.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_ready.update_layout(yaxis_range=[0, 70])
        st.plotly_chart(fig_ready, use_container_width=True)

    with col2:
        st.subheader("Нагрузка на единицу техники, га")
        fig_load = go.Figure()
        fig_load.add_trace(go.Bar(x=load_data["Техника"], y=load_data["Факт"], name="Факт", marker_color='#C0504D', text=load_data["Факт"], textposition='auto'))
        fig_load.add_trace(go.Bar(x=load_data["Техника"], y=load_data["Норматив"], name="Норматив", marker_color='#4472C4', text=load_data["Норматив"], textposition='auto'))
        fig_load.update_layout(barmode='group', yaxis_range=[0, 500])
        st.plotly_chart(fig_load, use_container_width=True)

with tab2:
    st.subheader("Обновление и выбытие техники по годам")
    
    def create_dyn_chart(df, title):
        fig = go.Figure()
        
        # Явно переводим цифры в строки для надежного отображения
        text_update = [str(val) for val in df["Обновление, %"]]
        text_disposal = [str(val) for val in df["Выбытие, %"]]
        
        # Находим максимальное значение, чтобы задать отступ сверху
        max_val = max(df["Обновление, %"].max(), df["Выбытие, %"].max())
        
        # График Обновления
        fig.add_trace(go.Scatter(
            x=df["Год"], 
            y=df["Обновление, %"], 
            mode='lines+markers+text', 
            name='Обновление, %', 
            text=text_update, 
            textposition="top center", 
            textfont=dict(size=12, color='#4472C4'), # Делаем текст синим под цвет линии
            line=dict(color='#4472C4', width=3),
            cliponaxis=False
        ))
        
        # График Выбытия
        fig.add_trace(go.Scatter(
            x=df["Год"], 
            y=df["Выбытие, %"], 
            mode='lines+markers+text', 
            name='Выбытие, %', 
            text=text_disposal, 
            textposition="bottom center", 
            textfont=dict(size=12, color='#C0504D'), # Делаем текст красным под цвет линии
            line=dict(color='#C0504D', width=3),
            cliponaxis=False
        ))
        
        fig.update_layout(
            title=title, 
            yaxis_title="Проценты", 
            xaxis_title="Год", 
            height=450, # Чуть увеличили высоту
            # Задаем жесткие границы оси Y: от -2 (для подписей снизу) до max+3 (для подписей сверху)
            yaxis=dict(range=[-2, max_val + 3]),
            margin=dict(l=40, r=40, t=50, b=100) # Добавили места снизу
        )
        
        # Принудительно задаем все годы, чтобы ни один не пропал
        fig.update_xaxes(
            type='category', 
            tickangle=-45,
            tickmode='array',
            tickvals=df["Год"],
            ticktext=df["Год"]
        )
        
        return fig

    st.plotly_chart(create_dyn_chart(tractors_dyn, "Тракторы"), use_container_width=True)
    st.plotly_chart(create_dyn_chart(grain_dyn, "Зерноуборочные комбайны"), use_container_width=True)
    st.plotly_chart(create_dyn_chart(forage_dyn, "Кормоуборочные комбайны"), use_container_width=True)

with tab3:
    st.subheader("Приобретение техники: План vs Факт")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_25 = px.bar(purchase_2025, x="Техника", y=["План", "Факт"], barmode="group", title="2025 год", text_auto=True, color_discrete_sequence=['#4472C4', '#C0504D'])
        st.plotly_chart(fig_25, use_container_width=True)
        

    with col2:
        fig_26 = px.bar(purchase_2026, x="Техника", y=["План", "Факт"], barmode="group", title="2026 год (на текущую дату)", text_auto=True, color_discrete_sequence=['#4472C4', '#C0504D'])
        st.plotly_chart(fig_26, use_container_width=True)

with tab4:
    st.subheader("Заявки на приобретение техники в АО Росагролизинг (2026 год)")
    st.markdown("С начала 2026 года подано **77 заявок** на **90 единиц** техники.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Одобрено", "45 заявок / 79 ед.", "350,9 млн руб.")
    col2.metric("Поставлено", "37 заявок / 41 ед.", "308,2 млн руб.")
    col3.metric("В процессе поставки", "12 заявок / 21 ед.", "35,2 млн руб.")
    
    st.divider()
    st.markdown("**Отказы и отзывы:**")
    st.write("- ❌ Отказано по 28 заявкам на 28 единиц техники.")
    st.write("- 🔄 Отозвано аграриями: 14 заявок на 14 единиц.")
    st.write("- 🏢 Отказано АО «РОСАГРОЛИЗИНГ»: по 14 заявкам на 14 единиц.")


