import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
from huggingface_hub import HfApi, hf_hub_download

# ---------------------------------------------------------
# Page Configuration & Soft Pink Theme Customization
# ---------------------------------------------------------
st.set_page_config(
    page_title="Master Plan 2027",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp { background-color: #fff9fa; }
    h1 { color: #d65a75; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    div.stButton > button {
        border-radius: 12px;
        border: 2px solid #fdb0c0;
        background-color: #ffffff;
        color: #4a4a4a;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #fdb0c0;
        color: white;
        border-color: #e593a4;
    }
    .card-box {
        background-color: #ffffff;
        border: 1px solid #f8d7da;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0px 4px 10px rgba(253, 176, 192, 0.15);
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "master_plan_data.json"
HF_TOKEN = os.getenv("HF_TOKEN")
REPO_ID = "jan0611/master-plan-db"

# ---------------------------------------------------------
# Data Persistence with Hugging Face Dataset Sync
# ---------------------------------------------------------
def get_default_data():
    return {
        "paper_tasks": [
            {"label": "Abstract", "checked": False},
            {"label": "Literature Review", "checked": False},
            {"label": "Methodology", "checked": False}
        ],
        "ielts_scores": {
            day: {"Writing": 6.0, "Speaking": 6.0, "Reading": 6.0, "Listening": 6.0}
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        },
        "campuses": {
            "Default University": {
                "info": "Target intake: 2027",
                "requirements": [{"label": "Requirement 1", "checked": False}]
            }
        }
    }

def load_data():
    if HF_TOKEN:
        try:
            filepath = hf_hub_download(
                repo_id=REPO_ID,
                filename=DATA_FILE,
                repo_type="dataset",
                token=HF_TOKEN
            )
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return get_default_data()
    return get_default_data()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
    if HF_TOKEN:
        try:
            api = HfApi()
            api.upload_file(
                path_or_fileobj=DATA_FILE,
                path_in_repo=DATA_FILE,
                repo_id=REPO_ID,
                repo_type="dataset",
                token=HF_TOKEN
            )
        except Exception as e:
            st.error(f"Cloud sync error: {e}")

if "db" not in st.session_state:
    st.session_state.db = load_data()

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Master Paper Progress"

# ---------------------------------------------------------
# Header & Custom Tab Navigation
# ---------------------------------------------------------
st.title("🏆 Master Plan 2027")

col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    if st.button("📄 Master Paper Progress", use_container_width=True):
        st.session_state.active_tab = "Master Paper Progress"

with col_t2:
    if st.button("⏱️ Habit Tracker", use_container_width=True):
        st.session_state.active_tab = "Habit Tracker"

with col_t3:
    if st.button("🎓 Campus Info and Requirements", use_container_width=True):
        st.session_state.active_tab = "Campus Info and Requirements"

st.divider()

# ---------------------------------------------------------
# TAB 1: Master Paper Progress
# ---------------------------------------------------------
if st.session_state.active_tab == "Master Paper Progress":
    st.subheader("📄 Paper Writing Milestones")
    
    col_left, col_right = st.columns([1.3, 1])
    tasks = st.session_state.db["paper_tasks"]
    updated = False
    
    with col_left:
        st.markdown("**Checklist**")
        checked_count = 0
        to_delete = None
        
        for idx, task in enumerate(tasks):
            c_check, c_input, c_del = st.columns([0.1, 0.8, 0.1])
            
            with c_check:
                is_checked = st.checkbox("Task", value=task["checked"], key=f"paper_chk_{idx}", label_visibility="collapsed")
                if is_checked != task["checked"]:
                    task["checked"] = is_checked
                    updated = True
            
            with c_input:
                new_label = st.text_input("Label", value=task["label"], key=f"paper_lbl_{idx}", label_visibility="collapsed")
                if new_label != task["label"]:
                    task["label"] = new_label
                    updated = True
            
            with c_del:
                if st.button("🗑️", key=f"paper_del_{idx}"):
                    to_delete = idx
                    
            if task["checked"]:
                checked_count += 1

        if to_delete is not None:
            tasks.pop(to_delete)
            save_data(st.session_state.db)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add New Task", key="add_paper_task"):
            tasks.append({"label": f"New Task {len(tasks) + 1}", "checked": False})
            save_data(st.session_state.db)
            st.rerun()

        if updated:
            save_data(st.session_state.db)
            st.rerun()

    with col_right:
        st.markdown("<h3 style='text-align: center; color: #d65a75;'>Completion Progress</h3>", unsafe_allow_html=True)
        total_tasks = len(tasks)
        percentage = round((checked_count / total_tasks) * 100, 1) if total_tasks > 0 else 0
        
        fig = go.Figure(data=[go.Pie(
            labels=['Completed', 'Remaining'],
            values=[checked_count, max(0, total_tasks - checked_count)],
            hole=0.68,
            marker_colors=['#fdb0c0', '#fce4e8'],
            textinfo='none',
            hoverinfo='label+value'
        )])
        
        fig.update_layout(
            showlegend=False,
            annotations=[{
                'text': f"<b>{percentage:.0f}%</b><br><span style='font-size:14px;color:gray;'>{checked_count}/{total_tasks} Done</span>",
                'x': 0.5, 'y': 0.5,
                'font_size': 26,
                'showarrow': False
            }],
            margin=dict(t=20, b=20, l=20, r=20),
            height=320
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: Habit Tracker (IELTS Preparation)
# ---------------------------------------------------------
elif st.session_state.active_tab == "Habit Tracker":
    st.subheader("⏱️ Daily Progress in IELTS")
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    skills = ["Writing", "Speaking", "Reading", "Listening"]
    
    cols = st.columns(5)
    daily_averages = []
    scores_db = st.session_state.db["ielts_scores"]
    data_changed = False
    
    for idx, day in enumerate(days):
        with cols[idx]:
            st.markdown(f"<div class='card-box'><h4 style='text-align:center; color:#d65a75;'>{day}</h4>", unsafe_allow_html=True)
            
            day_scores = scores_db.get(day, {"Writing": 6.0, "Speaking": 6.0, "Reading": 6.0, "Listening": 6.0})
            day_sum = 0.0
            
            for skill in skills:
                val = st.number_input(
                    label=skill,
                    min_value=0.0,
                    max_value=9.0,
                    step=0.5,
                    value=float(day_scores.get(skill, 6.0)),
                    key=f"{day}_{skill}"
                )
                if val != day_scores.get(skill):
                    day_scores[skill] = val
                    data_changed = True
                day_sum += val
            
            avg = round(day_sum / 4.0, 2)
            daily_averages.append(avg)
            
            st.markdown(f"<p style='text-align:center; font-weight:bold; margin-top:10px;'>Score Average: <span style='color:#d65a75;'>{avg}</span></p></div>", unsafe_allow_html=True)
            
    if data_changed:
        st.session_state.db["ielts_scores"] = scores_db
        save_data(st.session_state.db)
        st.rerun()

    st.divider()
    st.subheader("📈 Weekly Progress")
    
    df_chart = pd.DataFrame({"Day": days, "Average Score": daily_averages})
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=df_chart["Day"],
        y=df_chart["Average Score"],
        mode='lines+markers+text',
        text=[f"{v:.2f}" for v in daily_averages],
        textposition="top center",
        line=dict(color='#fdb0c0', width=4),
        marker=dict(size=10, color='#d65a75')
    ))
    
    fig_line.update_layout(
        yaxis=dict(range=[0, 9.5], title="IELTS Score"),
        xaxis=dict(title="Day of Week"),
        height=350,
        margin=dict(t=30, b=30, l=30, r=30)
    )
    
    st.plotly_chart(fig_line, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: Campus Info and Requirements
# ---------------------------------------------------------
elif st.session_state.active_tab == "Campus Info and Requirements":
    st.subheader("🎓 Campus Info & Requirements")
    
    campuses_db = st.session_state.db.setdefault("campuses", {})
    if not campuses_db:
        campuses_db["Default University"] = {
            "info": "Target intake: 2027",
            "requirements": [{"label": "Requirement 1", "checked": False}]
        }
        
    c_select, c_add, c_del = st.columns([0.5, 0.35, 0.15])
    
    with c_select:
        selected_campus = st.selectbox("Select Target Campus:", list(campuses_db.keys()))
        
    with c_add:
        new_campus_name = st.text_input("Add New Campus Name:", key="new_campus_input")
        if st.button("➕ Add Campus"):
            if new_campus_name and new_campus_name not in campuses_db:
                campuses_db[new_campus_name] = {
                    "info": "",
                    "requirements": [{"label": "Requirement 1", "checked": False}]
                }
                save_data(st.session_state.db)
                st.rerun()

    with c_del:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Delete Campus"):
            if len(campuses_db) > 1:
                del campuses_db[selected_campus]
                save_data(st.session_state.db)
                st.success(f"Deleted {selected_campus}!")
                st.rerun()
            else:
                st.warning("Cannot delete the last remaining campus!")

    campus_data = campuses_db[selected_campus]
    
    st.markdown(f"### Details for **{selected_campus}**")
    
    updated_info = st.text_area(
        "Campus Information & Notes:",
        value=campus_data.get("info", ""),
        height=130,
        key=f"info_area_{selected_campus}"
    )
    
    if updated_info != campus_data.get("info", ""):
        campus_data["info"] = updated_info
        save_data(st.session_state.db)

    st.markdown("#### Requirements Checklist")
    reqs = campus_data.get("requirements", [])
    updated_reqs = False
    req_to_delete = None
    
    for idx, req in enumerate(reqs):
        cr_check, cr_input, cr_del = st.columns([0.08, 0.82, 0.10])
        
        with cr_check:
            c_val = st.checkbox("Req", value=req["checked"], key=f"req_chk_{selected_campus}_{idx}", label_visibility="collapsed")
            if c_val != req["checked"]:
                req["checked"] = c_val
                updated_reqs = True
                
        with cr_input:
            r_lbl = st.text_input("ReqLabel", value=req["label"], key=f"req_lbl_{selected_campus}_{idx}", label_visibility="collapsed")
            if r_lbl != req["label"]:
                req["label"] = r_lbl
                updated_reqs = True
                
        with cr_del:
            if st.button("🗑️", key=f"req_del_{selected_campus}_{idx}"):
                req_to_delete = idx

    if req_to_delete is not None:
        reqs.pop(req_to_delete)
        save_data(st.session_state.db)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Add New Requirement", key=f"add_req_{selected_campus}"):
        reqs.append({"label": f"Requirement {len(reqs) + 1}", "checked": False})
        save_data(st.session_state.db)
        st.rerun()

    if updated_reqs:
        save_data(st.session_state.db)
        st.rerun()
