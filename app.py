# ============================================================
# ATC PLANNER - VERSION MINIMALE POUR STREAMLIT CLOUD
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import os
import hashlib
import secrets
from datetime import datetime, date
import warnings
warnings.filterwarnings("ignore")

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================

st.set_page_config(
    page_title="ATC Planner",
    page_icon="📡",
    layout="wide"
)

# ============================================
# STYLE CSS
# ============================================

st.markdown("""
<style>
    .stApp { background: #0a0e17; }
    .header {
        background: linear-gradient(135deg, #060a12 0%, #0d1a2b 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid rgba(0,255,100,0.04);
    }
    .header h1 { color: #7affb0; font-size: 1.8em; margin: 0; }
    .header p { color: rgba(180,200,220,0.3); margin: 0; }
    .stat-card {
        background: linear-gradient(145deg, #0d1a2b 0%, #162a3f 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(0,255,100,0.04);
    }
    .stat-number { font-size: 2.5em; font-weight: 800; color: #7affb0; }
    .stat-label { color: rgba(180,200,220,0.4); font-size: 0.7em; text-transform: uppercase; }
    .flight-strip {
        background: linear-gradient(135deg, #0d1a2b 0%, #162a3f 100%);
        border-left: 4px solid #2a7a4a;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin: 4px 0;
    }
    .section-title {
        font-size: 1.2em;
        font-weight: 700;
        color: #7affb0;
        margin-bottom: 15px;
        text-transform: uppercase;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060a12 0%, #0d1a2b 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONSTANTES
# ============================================

DEFAULT_PASSWORD = "ATC2026"
PASSWORD_ITERATIONS = 100_000

def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PASSWORD_ITERATIONS
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    if not salt or not stored_hash or not password:
        return False
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(test_hash, stored_hash)

# ============================================
# BASE DE DONNÉES
# ============================================

class Database:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.db_path = "data/planning.db"
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
                password_hash TEXT, password_salt TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instructeurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT, prenom TEXT, actif BOOLEAN,
                password_hash TEXT, password_salt TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, heure_debut TEXT, duree INTEGER,
                type TEXT, simulation_nom TEXT
            )
        """)
        
        # Données de démonstration
        pwd_hash, salt = hash_password(DEFAULT_PASSWORD)
        
        cursor.execute("SELECT COUNT(*) FROM eleves")
        if cursor.fetchone()[0] == 0:
            eleves = [('KOUBAA', 'AYOUB'), ('BAMIDA', 'AYMANE'), ('CHADDANI', 'MOHAMED')]
            for nom, prenom in eleves:
                cursor.execute(
                    "INSERT INTO eleves (nom, prenom, password_hash, password_salt) VALUES (?, ?, ?, ?)",
                    (nom, prenom, pwd_hash, salt)
                )
        
        cursor.execute("SELECT COUNT(*) FROM instructeurs")
        if cursor.fetchone()[0] == 0:
            instr = [('RIFAI', 'Mr'), ('TAHERI', 'Mr')]
            for nom, prenom in instr:
                cursor.execute(
                    "INSERT INTO instructeurs (nom, prenom, actif, password_hash, password_salt) VALUES (?, ?, 1, ?, ?)",
                    (nom, prenom, pwd_hash, salt)
                )
        
        conn.commit()
        conn.close()
    
    def verify_password_eleve(self, eleve_id, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, password_salt FROM eleves WHERE id = ?", (eleve_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False
        return verify_password(password, row[1], row[0])
    
    def verify_password_instructeur(self, instr_id, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, password_salt FROM instructeurs WHERE id = ?", (instr_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False
        return verify_password(password, row[1], row[0])
    
    def get_eleves(self):
        return pd.read_sql_query("SELECT * FROM eleves ORDER BY nom, prenom", self.get_connection())
    
    def get_eleve_by_id(self, eleve_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prenom, email FROM eleves WHERE id = ?", (eleve_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_instructeurs(self):
        return pd.read_sql_query("SELECT * FROM instructeurs WHERE actif=1 ORDER BY nom, prenom", self.get_connection())
    
    def get_instructeur_by_id(self, instr_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prenom, actif FROM instructeurs WHERE id = ?", (instr_id,))
        result = cursor.fetchone()
        conn.close()
        return result

# ============================================
# LOGIN
# ============================================

def login_page():
    st.markdown("""
    <div style="text-align:center;padding:40px 0;">
        <div style="font-size:4em;">📡</div>
        <h1 style="color:#7affb0;font-size:2.5em;">ATC PLANNER</h1>
        <p style="color:rgba(180,200,220,0.3);">ICNA · AIAC · Phase Pratique</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = Database()
    
    tab1, tab2 = st.tabs(["👨‍🎓 Élève", "👨‍🏫 Instructeur"])
    
    with tab1:
        eleves = db.get_eleves()
        if eleves.empty:
            st.warning("Aucun élève")
            return
        
        options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in eleves.iterrows()}
        selected = st.selectbox("Choisissez votre nom", list(options.keys()))
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter", type="primary", use_container_width=True):
            eleve_id = options[selected]
            if db.verify_password_eleve(eleve_id, password):
                st.session_state["user"] = {"nom": selected.split()[1], "prenom": selected.split()[0]}
                st.session_state["role"] = "eleve"
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect. Utilisez ATC2026")
    
    with tab2:
        instrs = db.get_instructeurs()
        if instrs.empty:
            st.warning("Aucun instructeur")
            return
        
        options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in instrs.iterrows()}
        selected = st.selectbox("Choisissez votre nom", list(options.keys()))
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter", type="primary", use_container_width=True):
            instr_id = options[selected]
            if db.verify_password_instructeur(instr_id, password):
                st.session_state["user"] = {"nom": selected.split()[1], "prenom": selected.split()[0]}
                st.session_state["role"] = "instructeur"
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect. Utilisez ATC2026")

# ============================================
# MAIN
# ============================================

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    
    if not st.session_state["logged_in"]:
        login_page()
        return
    
    user = st.session_state.get("user", {})
    role = st.session_state.get("role", "eleve")
    db = Database()
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:10px 0;border-bottom:1px solid rgba(0,255,100,0.04);">
            <div style="font-size:1.6em;font-weight:700;color:#7affb0;">📡 ATC</div>
        </div>
        """, unsafe_allow_html=True)
        
        if role == "eleve":
            pages = ["🏠 Accueil", "📅 Planning", "📊 Notes"]
        else:
            pages = ["🏠 Accueil", "👥 Personnes", "📊 Évaluations"]
        
        selection = st.radio("Navigation", pages)
        
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
    
    st.markdown(f"""
    <div class="header">
        <h1>📡 {user.get('prenom', '')} {user.get('nom', '')}</h1>
        <p>{'👨‍🎓 Élève' if role == 'eleve' else '👨‍🏫 Instructeur'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if selection == "🏠 Accueil":
        st.markdown('<div class="section-title">🏠 Accueil</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(db.get_eleves())}</div>
                <div class="stat-label">👨‍🎓 Élèves</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(db.get_instructeurs())}</div>
                <div class="stat-label">👨‍🏫 Instructeurs</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.success("✅ Application en ligne !")
        st.info("🔑 Mot de passe : ATC2026")
    
    elif selection == "📅 Planning":
        st.markdown('<div class="section-title">📅 Planning</div>', unsafe_allow_html=True)
        st.info("📅 Planning à venir")
    
    elif selection == "📊 Notes" or selection == "📊 Évaluations":
        st.markdown('<div class="section-title">📊 Évaluations</div>', unsafe_allow_html=True)
        st.info("📊 Évaluations à venir")
    
    elif selection == "👥 Personnes":
        st.markdown('<div class="section-title">👥 Personnes</div>', unsafe_allow_html=True)
        eleves = db.get_eleves()
        if not eleves.empty:
            st.dataframe(eleves[["nom", "prenom"]], use_container_width=True)

if __name__ == "__main__":
    main()
