import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import base64
import requests
from datetime import datetime

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="Сельхозтехника Иркутской области", layout="wide", page_icon="🌾")

# --- ДИЗАЙН ---
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: linear-gradient(rgba(250, 250, 245, 0.88), rgba(250, 250, 245, 0.88)), 
    url("https://images.unsplash.com/photo-1500382017468-9049fed747ef?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
    background-size: cover; background-position: center; background-attachment: fixed;
}
[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
[data-testid="stMetricValue"] { color: #3A5A40; font-weight: bold; }
h1, h2, h3 { color: #3A5A40 !important; font-family: 'Georgia', serif; }
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

COLOR_GREEN = '#5A7D5A'
COLOR_TERRACOTTA = '#B8624F'
COLOR_DARK = '#333333'
DATA_FILE = "data.json"

# --- ДАННЫЕ ПО УМОЛЧАНИЮ ---
def get_default_data():
    years = [str(y) for y in range(2020, 2027)]
    years[-1] = "2026 (тек. дата)"
    return {
        "date": "05.11.2026",
        "metrics": {"Тракторы": 3286, "Зерноуборочные комбайны": 1094, "Кормоуборочные комбайны": 140, "Другая техника": 7000},
        "readiness": [
            {"Техника": "Тракторы", "Оснащенность, %": 52},
            {"Техника": "Зерноуборочные", "Оснащенность, %": 30},
            {"Техника": "Кормоуборочные", "Оснащенность, %": 59},
            {"Техника": "Другая техника", "Оснащенность, %": 55}
        ],
        "load": [
            {"Техника": "Тракторы", "Факт": 233, "Норматив": 120},
            {"Техника": "Зерноуборочные", "Факт": 390, "Норматив": 117},
            {"Техника": "Кормоуборочные", "Факт": 472, "Норматив": 280}
        ],
        "tractors_dyn": {"Год": years, "Обновление, %": [3.6, 3.6, 2.2, 3.3, 2.4, 2.4, 1.16], "Выбытие, %": [7.3, 5.3, 4.6, 4.8, 5.3, 5.3, 4.16]},
        "grain_dyn": {"Год": years, "Обновление, %": [6.1, 4.7, 4.9, 3.7, 3.6, 1.8, 1.74], "Выбытие, %": [5.5, 4.7, 4.8, 3.9, 1.1, 0.7, 5.62]},
        "forage_dyn": {"Год": years, "Обновление, %": [8.9, 5.4, 4.7, 2.8, 1.4, 2.0, 2.14], "Выбытие, %": [14.6, 8.1, 6.8, 6.8, 7.7, 7.0, 0.0]},
        "purchase_2025": [
            {"Техника": "Тракторы", "План": 120, "Факт": 82},
            {"Техника": "Зерноуборочные", "План": 50, "Факт": 20},
            {"Техника": "Кормоуборочные", "План": 10, "Факт": 4},
            {"Техника": "Прочая техника", "План": 500, "Факт": 415}
        ],
        "purchase_2026": [
            {"Техника": "Тракторы", "План": 100, "Факт": 38},
            {"Техника": "Зерноуборочные", "План": 30, "Факт": 19},
            {"Техника": "Кормоуборочные", "План": 5, "Факт": 3},
            {"Техника": "Прочая техника", "План": 450, "Факт": 220}
        ],
        "leasing": {
            "total_text": "С начала 2026 года подано **77 заявок** на **90 единиц** техники.",
            "metrics": [
                {"Статус": "Одобрено", "Детали": "45 заявок / 79 ед.", "Сумма": "350,9 млн руб."},
                {"Статус": "Поставлено", "Детали": "37 заявок / 41 ед.", "Сумма": "308,2 млн руб."},
                {"Статус": "В процессе поставки", "Детали": "12 заявок / 21 ед.", "Сумма": "35,2 млн руб."}
            ],
            "rejections": [
                "❌ Отказано по 28 заявкам на 28 единиц техники.",
                "🔄 Отозвано аграриями: 14 заявок на 14 единиц.",
                "🏢 Отказано АО «РОСАГРОЛИЗИНГ»: по 14 заявкам на 14 единиц."
            ]
        }
    }

def load_data():
    if "data" in st.session_state:
        return st.session_state["data"]
    
    default_data = get_default_data()
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Миграция старых данных (добавление лизинга и смена названия колонки)
            if "leasing" not in data:
                data["leasing"] = default_data["leasing"]
                
            if "readiness" in data and data["readiness"] and "Готовность, %" in data["readiness"][0]:
                for row in data["readiness"]:
                    row["Оснащенность, %"] = row.pop("Готовность, %")
                    
        except Exception:
            data = default_data
    else:
        data = default_data
        
    st.session_state["data"] = data
    return data

def save_to_github(content_str, commit_message):
    try:
        token = st.secrets["github_token"]
        repo = st.secrets["github_repo"]
    except (KeyError, FileNotFoundError):
        return False, "⚠️ GitHub-токен не настроен. Изменения сохранены только в текущей сессии (пропадут при перезапуске)."

    url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {
        "message": commit_message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload)
    if r.status_code in (200, 201):
        return True, "✅ Данные сохранены! Приложение обновится через 30–60 секунд."
    return False, f"❌ Ошибка {r.status_code}: {r.text[:200]}"

# --- АВТОРИЗАЦИЯ (СКРЫТАЯ) ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

is_admin = st.session_state["password_correct"]

# Если это не админ — полностью скрываем боковую панель
if not is_admin:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.sidebar.success("✅ Вы вошли как администратор")
    if st.sidebar.button("🚪 Выйти", use_container_width=True):
        st.session_state["password_correct"] = False
        st.session_state.pop("data", None)
        st.rerun()

data = load_data()

# --- ЗАГОЛОВОК ---
st.title("🌾 Мониторинг сельскохозяйственной техники Иркутской области")
st.markdown(f"**Дата актуализации данных: {data['date']}**")

# --- ВКЛАДКИ ---
tab_titles = ["📊 Обзор", "📈 Динамика (2020-2026)", "🚜 Приобретение", "📋 Лизинг и заявки"]
if is_admin:
    tab_titles.append("✏️ Редактирование")
tabs = st.tabs(tab_titles)

# --- ВКЛАДКА 1 ---
with tabs[0]:
    st.subheader("Наличие техники")
    cols = st.columns(4)
    for i, (name, value) in enumerate(data["metrics"].items()):
        cols[i].metric(name, f"{value:,} ед.")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Техническая оснащенность, %")
        df = pd.DataFrame(data["readiness"])
        fig = px.bar(df, x="Техника", y="Оснащенность, %", text="Оснащенность, %", color_discrete_sequence=[COLOR_GREEN])
        fig.update_traces(texttemplate='%{text}%', textposition='outside', textfont=dict(color=COLOR_DARK))
        fig.update_layout(yaxis_range=[0, 70], plot_bgcolor='rgba(255,255,255,0.7)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color=COLOR_DARK))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Нагрузка на единицу техники, га")
        df = pd.DataFrame(data["load"])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["Техника"], y=df["Факт"], name="Факт", marker_color=COLOR_TERRACOTTA, text=df["Факт"], textposition='auto', textfont=dict(color='white')))
        fig.add_trace(go.Bar(x=df["Техника"], y=df["Норматив"], name="Норматив", marker_color=COLOR_GREEN, text=df["Норматив"], textposition='auto', textfont=dict(color='white')))
        fig.update_layout(barmode='group', yaxis_range=[0, 500], plot_bgcolor='rgba(255,255,255,0.7)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color=COLOR_DARK))
        st.plotly_chart(fig, use_container_width=True)

# --- ВКЛАДКА 2 ---
with tabs[1]:
    st.subheader("Обновление и выбытие техники по годам")
    def create_dyn_chart(df, title):
        fig = go.Figure()
        text_update = [str(v) for v in df["Обновление, %"]]
        text_disposal = [str(v) for v in df["Выбытие, %"]]
        max_val = max(df["Обновление, %"].max(), df["Выбытие, %"].max())
        fig.add_trace(go.Scatter(x=df["Год"], y=df["Обновление, %"], mode='lines+markers+text', name='Обновление, %', text=text_update, textposition="top center", textfont=dict(size=12, color=COLOR_GREEN), line=dict(color=COLOR_GREEN, width=3), cliponaxis=False))
        fig.add_trace(go.Scatter(x=df["Год"], y=df["Выбытие, %"], mode='lines+markers+text', name='Выбытие, %', text=text_disposal, textposition="bottom center", textfont=dict(size=12, color=COLOR_TERRACOTTA), line=dict(color=COLOR_TERRACOTTA, width=3), cliponaxis=False))
        fig.update_layout(title=title, yaxis_title="Проценты", xaxis_title="Год", height=450, yaxis=dict(range=[-2, max_val + 3], gridcolor='rgba(200,200,200,0.3)'), plot_bgcolor='rgba(255,255,255,0.7)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=50, b=100), font=dict(color=COLOR_DARK))
        fig.update_xaxes(type='category', tickangle=-45, tickmode='array', tickvals=df["Год"], ticktext=df["Год"], gridcolor='rgba(200,200,200,0.3)')
        return fig
    st.plotly_chart(create_dyn_chart(pd.DataFrame(data["tractors_dyn"]), "Тракторы"), use_container_width=True)
    st.plotly_chart(create_dyn_chart(pd.DataFrame(data["grain_dyn"]), "Зерноуборочные комбайны"), use_container_width=True)
    st.plotly_chart(create_dyn_chart(pd.DataFrame(data["forage_dyn"]), "Кормоуборочные комбайны"), use_container_width=True)

# --- ВКЛАДКА 3 ---
with tabs[2]:
    st.subheader("Приобретение техники: План vs Факт")
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(pd.DataFrame(data["purchase_2025"]), x="Техника", y=["План", "Факт"], barmode="group", title="2025 год", text_auto=True, color_discrete_sequence=[COLOR_GREEN, COLOR_TERRACOTTA])
        fig.update_layout(plot_bgcolor='rgba(255,255,255,0.7)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color=COLOR_DARK))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(pd.DataFrame(data["purchase_2026"]), x="Техника", y=["План", "Факт"], barmode="group", title="2026 год (на текущую дату)", text_auto=True, color_discrete_sequence=[COLOR_GREEN, COLOR_TERRACOTTA])
        fig.update_layout(plot_bgcolor='rgba(255,255,255,0.7)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color=COLOR_DARK))
        st.plotly_chart(fig, use_container_width=True)

# --- ВКЛАДКА 4 ---
with tabs[3]:
    st.subheader("Заявки на приобретение техники в АО Росагролизинг (2026 год)")
    st.markdown(data["leasing"]["total_text"])
    
    col1, col2, col3 = st.columns(3)
    metrics = data["leasing"]["metrics"]
    cols = [col1, col2, col3]
    for i, m in enumerate(metrics[:3]):
        cols[i].metric(m["Статус"], m["Детали"], m["Сумма"])
        
    st.divider()
    st.markdown("**Отказы и отзывы:**")
    for rej in data["leasing"]["rejections"]:
        st.write(f"- {rej}")

# --- ВКЛАДКА 5: РЕДАКТИРОВАНИЕ ---
if is_admin:
    with tabs[4]:
        st.subheader("✏️ Редактирование данных")
        st.info("После редактирования нажмите кнопку «Сохранить». Изменения уйдут в репозиторий GitHub, и приложение перезагрузится в течение минуты.")

        edit_data = json.loads(json.dumps(data))

        edit_data["date"] = st.text_input("📅 Дата актуализации", value=edit_data["date"])

        st.divider()
        st.markdown("### 1. Наличие техники (ед.)")
        metrics_df = pd.DataFrame([{"Техника": k, "Количество": v} for k, v in edit_data["metrics"].items()])
        edited = st.data_editor(metrics_df, num_rows="dynamic", use_container_width=True, key="metrics_edit")
        edit_data["metrics"] = dict(zip(edited["Техника"], edited["Количество"]))

        st.divider()
        st.markdown("### 2. Техническая оснащенность (%)")
        edited = st.data_editor(pd.DataFrame(edit_data["readiness"]), num_rows="dynamic", use_container_width=True, key="readiness_edit")
        edit_data["readiness"] = edited.to_dict(orient="records")

        st.divider()
        st.markdown("### 3. Нагрузка на технику (га)")
        edited = st.data_editor(pd.DataFrame(edit_data["load"]), num_rows="dynamic", use_container_width=True, key="load_edit")
        edit_data["load"] = edited.to_dict(orient="records")

        st.divider()
        st.markdown("### 4. Динамика обновления/выбытия (%, 2020–2026)")
        for key, label in [("tractors_dyn", "Тракторы"), ("grain_dyn", "Зерноуборочные комбайны"), ("forage_dyn", "Кормоуборочные комбайны")]:
            st.markdown(f"**{label}**")
            edited = st.data_editor(pd.DataFrame(edit_data[key]), num_rows="fixed", use_container_width=True, key=f"{key}_edit")
            edit_data[key] = edited.to_dict(orient="list")

        st.divider()
        st.markdown("### 5. Приобретение техники")
        st.markdown("**2025 год**")
        edited = st.data_editor(pd.DataFrame(edit_data["purchase_2025"]), num_rows="dynamic", use_container_width=True, key="p25_edit")
        edit_data["purchase_2025"] = edited.to_dict(orient="records")

        st.markdown("**2026 год**")
        edited = st.data_editor(pd.DataFrame(edit_data["purchase_2026"]), num_rows="dynamic", use_container_width=True, key="p26_edit")
        edit_data["purchase_2026"] = edited.to_dict(orient="records")

        st.divider()
        st.markdown("### 6. Лизинг и заявки")
        edit_data["leasing"]["total_text"] = st.text_area("Текст-описание", value=edit_data["leasing"]["total_text"], height=100)
        
        st.markdown("**Основные показатели:**")
        edited = st.data_editor(pd.DataFrame(edit_data["leasing"]["metrics"]), num_rows="dynamic", use_container_width=True, key="leasing_metrics_edit")
        edit_data["leasing"]["metrics"] = edited.to_dict(orient="records")

        st.markdown("**Список отказов/отзывов (каждая строка — новый пункт):**")
        rej_df = pd.DataFrame({"Текст": edit_data["leasing"]["rejections"]})
        edited = st.data_editor(rej_df, num_rows="dynamic", use_container_width=True, key="leasing_rej_edit")
        edit_data["leasing"]["rejections"] = edited["Текст"].dropna().tolist()

        st.divider()
        if st.button("💾 Сохранить и опубликовать", type="primary", use_container_width=True):
            st.session_state["data"] = edit_data
            content = json.dumps(edit_data, ensure_ascii=False, indent=2)
            commit_msg = f"Обновление данных дашборда: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ok, msg = save_to_github(content, commit_msg)
            if ok:
                st.success(msg)
                st.balloons()
            else:
                st.warning(msg)

# --- ВХОД ДЛЯ АДМИНИСТРАТОРА (В САМОМ НИЗУ СТРАНИЦЫ) ---
if not is_admin:
    st.divider()
    with st.expander("🔒 Вход для администратора", expanded=False):
        pwd = st.text_input("Пароль", type="password", key="admin_pwd_field")
        if st.button("Войти", key="admin_login_btn"):
            if pwd == st.secrets.get("password", "admin"):
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Неверный пароль")
