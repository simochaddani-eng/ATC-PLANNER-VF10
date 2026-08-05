# ============================================
# ATC PLANNER - APPLICATION PRINCIPALE
# ============================================

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
import json
import os

# ============================================
# CONFIGURATION
# ============================================

st.set_page_config(
    page_title="ATC Planner - ICNA AIAC",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# STYLE CSS
# ============================================

st.markdown("""
<style>
    .stApp { background: #0a0e17; }
    .main-header {
        background: linear-gradient(135deg, #060a12 0%, #0d1a2b 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(0,255,100,0.04);
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #7affb0;
        font-size: 1.8em;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: rgba(180,200,220,0.3);
        font-size: 0.8em;
        margin: 0;
    }
    .section-title {
        font-size: 1.2em;
        font-weight: 700;
        color: #7affb0;
        margin-bottom: 15px;
        text-transform: uppercase;
    }
    .stat-card {
        background: linear-gradient(145deg, #0d1a2b 0%, #162a3f 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(0,255,100,0.04);
    }
    .stat-number {
        font-size: 2.5em;
        font-weight: 800;
        color: #7affb0;
    }
    .stat-label {
        color: rgba(180,200,220,0.4);
        font-size: 0.7em;
        text-transform: uppercase;
    }
    .flight-strip {
        background: linear-gradient(135deg, #0d1a2b 0%, #162a3f 100%);
        border-left: 4px solid #2a7a4a;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin: 4px 0;
    }
    .badge-success { background: rgba(0,255,100,0.1); color: #7affb0; padding: 2px 10px; border-radius: 10px; }
    .badge-warning { background: rgba(255,200,50,0.1); color: #ffcc44; padding: 2px 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# BASE DE DONNÉES
# ============================================

class Database:
    def __init__(self):
        # Adapté pour HF Spaces
        if os.environ.get("SPACE_ID"):
            self.db_path = "/app/data/planning.db"
        else:
            self.db_path = "planning.db"
        self.init_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT, prenom TEXT, email TEXT,
                groupe_id INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instructeurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT, prenom TEXT, actif BOOLEAN
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT, duree INTEGER
            )
        """)
        # ... autres tables
        conn.commit()
        conn.close()
        self._init_demo_data()
    
    def _init_demo_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM eleves")
        if cursor.fetchone()[0] == 0:
            eleves = [
                ('KOUBAA', 'AYOUB'),
                ('BAMIDA', 'AYMANE'),
                ('CHADDANI', 'MOHAMED')
            ]
            cursor.executemany("INSERT INTO eleves (nom, prenom) VALUES (?, ?)", eleves)
        conn.commit()
        conn.close()
    
    def get_eleves(self):
        return pd.read_sql_query("SELECT * FROM eleves", self.get_connection())

# ============================================
# AUTHENTIFICATION
# ============================================

def login_page():
    st.markdown("""
    <div style="text-align:center;padding:40px 0;">
        <div style="font-size:4em;">📡</div>
        <h1 style="color:#7affb0;font-size:2.5em;">ATC PLANNER</h1>
        <p style="color:rgba(180,200,220,0.3);">ICNA · AIAC · Phase Pratique</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("👨‍🎓 Élève", use_container_width=True):
            st.session_state["role"] = "eleve"
            st.session_state["logged_in"] = True
            st.rerun()
        
        if st.button("👨‍🏫 Instructeur", use_container_width=True):
            st.session_state["role"] = "instructeur"
            st.session_state["logged_in"] = True
            st.rerun()

# ============================================
# INTERFACE PRINCIPALE
# ============================================

def main_app():
    db = Database()
    eleves = db.get_eleves()
    
    st.markdown("""
    <div class="main-header">
        <h1>📡 ATC Planner</h1>
        <p>ICNA · AIAC · Phase Pratique Aérodrome</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(eleves)}</div>
            <div class="stat-label">👨‍🎓 Élèves</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.dataframe(eleves, use_container_width=True)

# ============================================
# POINT D'ENTRÉE
# ============================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app()
else:
    login_page()