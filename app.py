# ============================================================
# ATC PLANNER - VERSION STREAMLIT CLOUD (CORRIGÉE)
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
import json
import os
import base64
import hashlib
import secrets
import warnings
warnings.filterwarnings("ignore")

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================

st.set_page_config(
    page_title="ATC Planner - ICNA AIAC",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CONSTANTES ET CONFIGURATION
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

def generate_temp_password():
    return secrets.token_urlsafe(6)

def esc(x):
    if x is None:
        return ""
    return str(x)

# ============================================
# CSS
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
    .main-header h1 { color: #7affb0; font-size: 1.8em; margin: 0; }
    .main-header p { color: rgba(180,200,220,0.3); font-size: 0.8em; margin: 0; }
    .section-title {
        font-size: 1.2em; font-weight: 700; color: #7affb0;
        margin-bottom: 15px; text-transform: uppercase;
    }
    .stat-card {
        background: linear-gradient(145deg, #0d1a2b 0%, #162a3f 100%);
        border-radius: 12px; padding: 20px; text-align: center;
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
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060a12 0%, #0d1a2b 100%);
        border-right: 1px solid rgba(0,255,100,0.04);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# BASE DE DONNÉES
# ============================================

class Database:
    def __init__(self, db_path="data/planning.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT, prenom TEXT, email TEXT,
                groupe_id INTEGER,
                password_hash TEXT, password_salt TEXT
            );
            CREATE TABLE IF NOT EXISTS instructeurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT, prenom TEXT, actif BOOLEAN DEFAULT 1,
                password_hash TEXT, password_salt TEXT
            );
            CREATE TABLE IF NOT EXISTS groupes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT, instructeur_id INTEGER, simulateur_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT, duree INTEGER DEFAULT 65, est_test BOOLEAN DEFAULT 0, ordre INTEGER
            );
            CREATE TABLE IF NOT EXISTS seances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE, heure_debut TEXT, duree INTEGER,
                type TEXT, simulation_id INTEGER, groupe_id INTEGER,
                instructeur_id INTEGER, controle_eleve_id INTEGER,
                pseudo_eleve_id INTEGER, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_debut DATE, date_fin_souhaitee DATE,
                nb_eleves INTEGER, nb_instructeurs INTEGER, nb_simulateurs INTEGER,
                duree_briefing INTEGER DEFAULT 20, duree_debriefing INTEGER DEFAULT 30,
                heure_debut_matin TEXT DEFAULT "09:00", heure_fin_matin TEXT DEFAULT "12:15",
                heure_debut_apres_midi TEXT DEFAULT "14:15", heure_fin_apres_midi TEXT DEFAULT "17:30"
            );
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER, instructeur_id INTEGER,
                simulation_id INTEGER, date_note DATE,
                note DECIMAL(5,2), appreciation TEXT, commentaires TEXT
            );
        """)
        
        # Données de démonstration
        cursor.execute("SELECT COUNT(*) FROM simulations")
        if cursor.fetchone()[0] == 0:
            sims = [
                ("Synthese Dynamique", 65, 0, 1),
                ("Simulation 1", 65, 0, 2),
                ("Simulation 2", 65, 0, 3),
                ("Simulation 3", 65, 0, 4),
                ("Simulation Test", 65, 1, 5)
            ]
            cursor.executemany("INSERT INTO simulations (nom, duree, est_test, ordre) VALUES (?, ?, ?, ?)", sims)
        
        # Ajouter les données de démonstration
        pwd_hash, salt = hash_password(DEFAULT_PASSWORD)
        
        cursor.execute("SELECT COUNT(*) FROM instructeurs")
        if cursor.fetchone()[0] == 0:
            instr = [('RIFAI', 'Mr', 1), ('TAHERI', 'Mr', 1)]
            for nom, prenom, actif in instr:
                cursor.execute(
                    "INSERT INTO instructeurs (nom, prenom, actif, password_hash, password_salt) VALUES (?, ?, ?, ?, ?)",
                    (nom, prenom, actif, pwd_hash, salt)
                )
        
        cursor.execute("SELECT COUNT(*) FROM eleves")
        if cursor.fetchone()[0] == 0:
            eleves = [
                ('KOUBAA', 'AYOUB'),
                ('BAMIDA', 'AYMANE'),
                ('CHADDANI', 'MOHAMED')
            ]
            for nom, prenom in eleves:
                cursor.execute(
                    "INSERT INTO eleves (nom, prenom, password_hash, password_salt) VALUES (?, ?, ?, ?)",
                    (nom, prenom, pwd_hash, salt)
                )
        
        cursor.execute("SELECT COUNT(*) FROM config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO config (date_debut, date_fin_souhaitee, nb_eleves, nb_instructeurs, nb_simulateurs)
                VALUES (?, ?, ?, ?, ?)
            """, ('2026-09-01', '2026-09-30', 3, 2, 2))
        
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

    def set_password_eleve(self, eleve_id, new_password):
        pwd_hash, salt = hash_password(new_password)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE eleves SET password_hash = ?, password_salt = ? WHERE id = ?", (pwd_hash, salt, eleve_id))
        conn.commit()
        conn.close()

    def get_eleves(self):
        return pd.read_sql_query("SELECT * FROM eleves ORDER BY nom, prenom", self.get_connection())

    def get_eleve_by_id(self, eleve_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prenom, email, groupe_id FROM eleves WHERE id = ?", (eleve_id,))
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

    def get_seances(self):
        return pd.read_sql_query("""
            SELECT s.*, sim.nom as simulation_nom
            FROM seances s
            LEFT JOIN simulations sim ON s.simulation_id = sim.id
            ORDER BY s.date, s.heure_debut
        """, self.get_connection())

    def get_seances_eleve(self, eleve_id):
        return pd.read_sql_query("""
            SELECT s.*, sim.nom as simulation_nom
            FROM seances s
            LEFT JOIN simulations sim ON s.simulation_id = sim.id
            WHERE s.type = 'simulation' AND (s.controle_eleve_id = ? OR s.pseudo_eleve_id = ?)
            ORDER BY s.date, s.heure_debut
        """, self.get_connection(), params=(eleve_id, eleve_id))

    def get_notes_eleve(self, eleve_id):
        return pd.read_sql_query("""
            SELECT n.*, sim.nom as simulation_nom,
                   i.nom || ' ' || i.prenom as instructeur_nom
            FROM notes n
            LEFT JOIN simulations sim ON n.simulation_id = sim.id
            LEFT JOIN instructeurs i ON n.instructeur_id = i.id
            WHERE n.eleve_id = ?
            ORDER BY n.date_note DESC
        """, self.get_connection(), params=(eleve_id,))

    def add_note(self, note):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notes (eleve_id, instructeur_id, simulation_id, date_note, note, appreciation, commentaires)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (note["eleve_id"], note["instructeur_id"], note["simulation_id"],
              note["date_note"], note["note"], note["appreciation"], note.get("commentaires", "")))
        conn.commit()
        conn.close()

# ============================================
# INTERFACE DE CONNEXION
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
        tab1, tab2 = st.tabs(["👨‍🎓 Élève", "👨‍🏫 Instructeur"])
        
        with tab1:
            db = Database()
            eleves = db.get_eleves()
            if eleves.empty:
                st.warning("Aucun élève disponible.")
                return
            
            options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in eleves.iterrows()}
            selected = st.selectbox("Choisissez votre nom", list(options.keys()))
            password = st.text_input("Mot de passe", type="password")
            
            if st.button("🎯 Se connecter", type="primary", use_container_width=True):
                eleve_id = options[selected]
                if db.verify_password_eleve(eleve_id, password):
                    eleve = db.get_eleve_by_id(eleve_id)
                    st.session_state["user"] = dict(zip(["id", "nom", "prenom", "email", "groupe_id"], eleve))
                    st.session_state["role"] = "eleve"
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect. Utilisez ATC2026")
        
        with tab2:
            db = Database()
            instructeurs = db.get_instructeurs()
            if instructeurs.empty:
                st.warning("Aucun instructeur disponible.")
                return
            
            options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in instructeurs.iterrows()}
            selected = st.selectbox("Choisissez votre nom", list(options.keys()))
            password = st.text_input("Mot de passe", type="password")
            
            if st.button("🎯 Se connecter", type="primary", use_container_width=True):
                instr_id = options[selected]
                if db.verify_password_instructeur(instr_id, password):
                    instr = db.get_instructeur_by_id(instr_id)
                    st.session_state["user"] = dict(zip(["id", "nom", "prenom", "actif"], instr))
                    st.session_state["role"] = "instructeur"
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect. Utilisez ATC2026")

# ============================================
# INTERFACE PRINCIPALE
# ============================================

def main_app():
    db = Database()
    user = st.session_state.get("user", {})
    role = st.session_state.get("role", "eleve")
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:10px 0;border-bottom:1px solid rgba(0,255,100,0.04);margin-bottom:16px;">
            <div style="font-size:1.6em;font-weight:700;color:#7affb0;letter-spacing:2px;">📡 ATC</div>
            <div style="font-size:0.6em;color:rgba(180,200,220,0.2);letter-spacing:2px;">ICNA · AIAC</div>
        </div>
        """, unsafe_allow_html=True)
        
        if role == "eleve":
            pages = ["🏠 Accueil", "📅 Mon Planning", "📊 Mes Notes"]
        else:
            pages = ["🏠 Accueil", "👥 Personnes", "📊 Évaluations"]
        
        selection = st.radio("Navigation", pages)
        
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
    
    # En-tête
    st.markdown(f"""
    <div class="main-header">
        <h1>{user.get('prenom', '')} {user.get('nom', '')}</h1>
        <p>{'👨‍🎓 Élève' if role == 'eleve' else '👨‍🏫 Instructeur'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if selection == "🏠 Accueil":
        show_home(db, role)
    elif selection == "📅 Mon Planning":
        show_planning(db)
    elif selection == "📊 Mes Notes" and role == "eleve":
        show_notes(db)
    elif selection == "📊 Évaluations" and role == "instructeur":
        show_evaluations(db)
    elif selection == "👥 Personnes":
        show_personnes(db)

def show_home(db, role):
    st.markdown('<div class="section-title">🏠 Accueil</div>', unsafe_allow_html=True)
    
    eleves = db.get_eleves()
    instructeurs = db.get_instructeurs()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(eleves)}</div>
            <div class="stat-label">👨‍🎓 Élèves</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(instructeurs)}</div>
            <div class="stat-label">👨‍🏫 Instructeurs</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.success("✅ ATC Planner en ligne !")
    st.info("🔑 Mot de passe par défaut : ATC2026")

def show_planning(db):
    st.markdown('<div class="section-title">📅 Mon Planning</div>', unsafe_allow_html=True)
    
    eleve_id = st.session_state["user"]["id"]
    seances = db.get_seances_eleve(eleve_id)
    
    if seances.empty:
        st.info("Aucune séance planifiée.")
        return
    
    for date_val in sorted(seances["date"].unique()):
        st.markdown(f"### 📅 {date_val}")
        jour = seances[seances["date"] == date_val].sort_values("heure_debut")
        for _, s in jour.iterrows():
            st.markdown(f"""
            <div class="flight-strip">
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:#7affb0;">{s['simulation_nom']}</span>
                    <span style="color:#ffcc44;">{s['heure_debut']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_notes(db):
    st.markdown('<div class="section-title">📊 Mes Notes</div>', unsafe_allow_html=True)
    
    eleve_id = st.session_state["user"]["id"]
    notes = db.get_notes_eleve(eleve_id)
    
    if notes.empty:
        st.info("Aucune évaluation disponible.")
        return
    
    moyenne = notes["note"].mean()
    st.markdown(f"""
    <div style="text-align:center;margin:20px 0;">
        <span style="font-size:3em;color:#7affb0;">{moyenne:.1f}/20</span>
        <div style="color:rgba(180,200,220,0.3);">Moyenne sur {len(notes)} évaluation(s)</div>
    </div>
    """, unsafe_allow_html=True)
    
    for _, n in notes.iterrows():
        st.markdown(f"""
        <div class="flight-strip">
            <div style="display:flex;justify-content:space-between;">
                <span>{n['simulation_nom']}</span>
                <span style="color:#7affb0;">{n['note']:.1f}/20</span>
            </div>
            <div style="font-size:0.8em;color:rgba(180,200,220,0.5);">
                {n['instructeur_nom']} · {n['appreciation']}
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_evaluations(db):
    st.markdown('<div class="section-title">📊 Évaluations</div>', unsafe_allow_html=True)
    
    eleves = db.get_eleves()
    if eleves.empty:
        st.info("Aucun élève.")
        return
    
    eleve_options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in eleves.iterrows()}
    selected = st.selectbox("Choisir un élève", list(eleve_options.keys()))
    eleve_id = eleve_options[selected]
    
    notes = db.get_notes_eleve(eleve_id)
    if not notes.empty:
        st.dataframe(notes[["date_note", "simulation_nom", "note", "appreciation"]], use_container_width=True)
    
    st.markdown("---")
    with st.form("add_note"):
        simulation = st.selectbox("Simulation", ["Simulation 1", "Simulation 2", "Simulation Test"])
        note = st.slider("Note", 0.0, 20.0, 10.0, 0.5)
        appreciation = st.selectbox("Appréciation", ["Excellent", "Très bien", "Bien", "Passable", "Insuffisant"])
        commentaires = st.text_area("Commentaires")
        
        if st.form_submit_button("📊 Enregistrer"):
            db.add_note({
                "eleve_id": eleve_id,
                "instructeur_id": st.session_state["user"]["id"],
                "simulation_id": 1,
                "date_note": date.today().strftime("%Y-%m-%d"),
                "note": note,
                "appreciation": appreciation,
                "commentaires": commentaires
            })
            st.success("✅ Note enregistrée")
            st.rerun()

def show_personnes(db):
    st.markdown('<div class="section-title">👥 Personnes</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Élèves", "Instructeurs"])
    
    with tab1:
        eleves = db.get_eleves()
        if not eleves.empty:
            st.dataframe(eleves[["id", "nom", "prenom", "email"]], use_container_width=True)
    
    with tab2:
        instructeurs = db.get_instructeurs()
        if not instructeurs.empty:
            st.dataframe(instructeurs[["id", "nom", "prenom", "email"]], use_container_width=True)

# ============================================
# POINT D'ENTRÉE
# ============================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app()
else:
    login_page()
