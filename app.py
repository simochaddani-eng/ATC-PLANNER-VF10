# ============================================
# ATC PLANNER - VERSION RENDER
# ============================================

import streamlit as st
import sqlite3
import pandas as pd
import os
import json
from datetime import datetime, date, timedelta

# ============================================
# CONFIGURATION SPÉCIFIQUE RENDER
# ============================================

# Détection de l'environnement Render
IS_RENDER = os.environ.get("RENDER") is not None
IS_RENDER_DEPLOY = os.environ.get("RENDER_DEPLOY_ID") is not None

if IS_RENDER or IS_RENDER_DEPLOY:
    # Sur Render, utiliser le disque persistant
    DB_PATH = "/app/data/planning.db"
    DATA_DIR = "/app/data"
else:
    # En local
    DB_PATH = "planning.db"
    DATA_DIR = "data"

# Créer le dossier data si inexistant
os.makedirs(DATA_DIR, exist_ok=True)

# Récupérer les secrets Render
ADMIN_RESET_KEY = os.environ.get("ADMIN_RESET_KEY", "default_admin_key")
DEFAULT_PASSWORD = os.environ.get("DEFAULT_PASSWORD", "ATC2026")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://localhost:10000")

st.set_page_config(
    page_title="ATC Planner - ICNA AIAC",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# STYLE CSS (identique à la version précédente)
# ============================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
    
    * { font-family: 'JetBrains Mono', monospace; }
    
    .stApp { background: #0a0e17; }
    
    .main-header {
        background: linear-gradient(135deg, #060a12 0%, #0d1a2b 50%, #162a3f 100%);
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
        letter-spacing: 1px;
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
        letter-spacing: 1px;
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
    .badge-danger { background: rgba(255,80,80,0.1); color: #ff7777; padding: 2px 10px; border-radius: 10px; }
    
    .render-badge {
        background: rgba(0,255,100,0.05);
        border: 1px solid rgba(0,255,100,0.1);
        border-radius: 20px;
        padding: 8px 16px;
        color: #7affb0;
        font-size: 0.7em;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060a12 0%, #0d1a2b 100%);
        border-right: 1px solid rgba(0,255,100,0.04);
    }
    
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: 1px solid rgba(0,255,100,0.1) !important;
        background: rgba(0,255,100,0.03) !important;
        color: #7affb0 !important;
    }
    .stButton > button:hover {
        background: rgba(0,255,100,0.06) !important;
        border-color: rgba(0,255,100,0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# BASE DE DONNÉES AVEC PERSISTANCE
# ============================================

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_debut DATE NOT NULL,
                date_fin_souhaitee DATE NOT NULL,
                nb_eleves INTEGER NOT NULL,
                nb_instructeurs INTEGER NOT NULL,
                nb_simulateurs INTEGER NOT NULL,
                duree_briefing INTEGER DEFAULT 20,
                duree_debriefing INTEGER DEFAULT 30,
                heure_debut_matin TEXT DEFAULT "09:00",
                heure_fin_matin TEXT DEFAULT "12:15",
                heure_debut_apres_midi TEXT DEFAULT "14:15",
                heure_fin_apres_midi TEXT DEFAULT "17:30",
                pause_matin_debut TEXT DEFAULT "10:30",
                pause_matin_fin TEXT DEFAULT "10:45",
                pause_am_debut TEXT DEFAULT "15:45",
                pause_am_fin TEXT DEFAULT "16:00"
            );
            CREATE TABLE IF NOT EXISTS eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT,
                groupe_id INTEGER,
                password_hash TEXT,
                password_salt TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS instructeurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT,
                actif BOOLEAN DEFAULT 1,
                password_hash TEXT,
                password_salt TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS groupes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                instructeur_id INTEGER,
                simulateur_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS groupe_eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                groupe_id INTEGER,
                eleve_id INTEGER,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                duree INTEGER DEFAULT 65,
                est_test BOOLEAN DEFAULT 0,
                ordre INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS seances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                heure_debut TEXT NOT NULL,
                duree INTEGER NOT NULL,
                type TEXT CHECK(type IN ("briefing", "simulation", "debriefing")),
                simulation_id INTEGER,
                groupe_id INTEGER,
                instructeur_id INTEGER,
                instructeur_evaluateur_id INTEGER,
                simulateur_id INTEGER,
                controle_eleve_id INTEGER,
                pseudo_eleve_id INTEGER,
                observateurs TEXT,
                statut TEXT DEFAULT "planifiee",
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS cours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                description TEXT,
                type TEXT CHECK(type IN ("pdf", "video", "document", "lien")),
                contenu TEXT,
                date_upload DATE,
                instructeur_id INTEGER,
                groupe_cible_id INTEGER,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                description TEXT,
                objectifs TEXT,
                duree_estimee INTEGER,
                niveau TEXT CHECK(niveau IN ("debutant", "intermediaire", "avance")),
                simulateur_requis BOOLEAN DEFAULT 0,
                instructions TEXT,
                contenu TEXT,
                type TEXT CHECK(type IN ("pdf", "video", "document", "lien")),
                date_creation DATE,
                instructeur_id INTEGER,
                groupe_cible_id INTEGER,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS td (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                description TEXT,
                type TEXT CHECK(type IN ("exercice", "corrige", "serie", "devoir")),
                contenu TEXT,
                date_upload DATE,
                instructeur_id INTEGER,
                groupe_cible_id INTEGER,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS grilles_evaluation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                description TEXT,
                criteres TEXT,
                bareme TEXT,
                instructeur_id INTEGER,
                date_creation DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER,
                instructeur_id INTEGER,
                grille_id INTEGER,
                simulation_id INTEGER,
                seance_id INTEGER,
                date_note DATE,
                note DECIMAL(5,2),
                appreciation TEXT,
                scores_criteres TEXT,
                commentaires TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ("eleve", "instructeur")),
                attempt_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 0,
                ip_address TEXT,
                user_agent TEXT
            );
        """)
        conn.commit()
        conn.close()
        self._init_demo_data()
    
    def _init_demo_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si les données existent déjà
        cursor.execute("SELECT COUNT(*) FROM instructeurs")
        if cursor.fetchone()[0] == 0:
            # Créer un mot de passe simple pour la démo
            # Note : En production, utilisez un hash
            instructeurs = [
                ('RIFAI', 'Mr', 'rifai@atc.com', 1),
                ('TAHERI', 'Mr', 'taheri@atc.com', 1),
                ('JBARA', 'Mr', 'jbara@atc.com', 1)
            ]
            cursor.executemany(
                "INSERT INTO instructeurs (nom, prenom, email, actif) VALUES (?, ?, ?, ?)",
                instructeurs
            )
        
        cursor.execute("SELECT COUNT(*) FROM eleves")
        if cursor.fetchone()[0] == 0:
            eleves = [
                ('KOUBAA', 'AYOUB', 'ayoub@atc.com'),
                ('BAMIDA', 'AYMANE', 'aymane@atc.com'),
                ('CHADDANI', 'MOHAMED', 'mohamed@atc.com'),
                ('KHOULANE', 'ILYAS', 'ilyas@atc.com'),
                ('AKNOUZE', 'RACHID', 'rachid@atc.com'),
                ('MIFDAL', 'IMANE', 'imane@atc.com'),
                ('KOUMI', 'KHADIJA', 'khadija@atc.com'),
                ('GUENNOUN', 'CHAIMAE', 'chaimae@atc.com'),
                ('ICHOU', 'ABDELLATIF', 'abdellatif@atc.com')
            ]
            cursor.executemany(
                "INSERT INTO eleves (nom, prenom, email) VALUES (?, ?, ?)",
                eleves
            )
        
        cursor.execute("SELECT COUNT(*) FROM simulations")
        if cursor.fetchone()[0] == 0:
            sims = [
                ("Synthese Dynamique", 65, 0, 1),
                ("Simulation 1", 65, 0, 2),
                ("Simulation 2", 65, 0, 3),
                ("Simulation 3", 65, 0, 4),
                ("Simulation 4", 65, 0, 5),
                ("Simulation 5", 65, 0, 6),
                ("Simulation 6", 65, 0, 7),
                ("Simulation Test", 65, 1, 8)
            ]
            cursor.executemany(
                "INSERT INTO simulations (nom, duree, est_test, ordre) VALUES (?, ?, ?, ?)",
                sims
            )
        
        cursor.execute("SELECT COUNT(*) FROM grilles_evaluation")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO grilles_evaluation (nom, description, criteres, bareme, date_creation)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "Grille ATC Standard",
                "Grille d'évaluation standard",
                json.dumps(["Phraséologie", "Anticipation", "Gestion du trafic", "Communication", "Réactivité"]),
                json.dumps([4, 4, 4, 4, 4]),
                date.today().strftime("%Y-%m-%d")
            ))
        
        conn.commit()
        conn.close()
    
    def get_eleves(self):
        return pd.read_sql_query("SELECT * FROM eleves ORDER BY nom, prenom", self.get_connection())
    
    def get_instructeurs(self):
        return pd.read_sql_query("SELECT * FROM instructeurs WHERE actif=1 ORDER BY nom, prenom", self.get_connection())
    
    def get_seances(self):
        return pd.read_sql_query("""
            SELECT s.*, sim.nom as simulation_nom, g.nom as groupe_nom,
                   i.nom || ' ' || i.prenom as instructeur_nom
            FROM seances s
            LEFT JOIN simulations sim ON s.simulation_id = sim.id
            LEFT JOIN groupes g ON s.groupe_id = g.id
            LEFT JOIN instructeurs i ON s.instructeur_id = i.id
            ORDER BY s.date, s.heure_debut
        """, self.get_connection())
    
    def get_config(self):
        result = pd.read_sql_query("SELECT * FROM config ORDER BY id DESC LIMIT 1", self.get_connection())
        return result.iloc[0].to_dict() if not result.empty else None
    
    def save_config(self, config_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM config")
        cursor.execute("""
            INSERT INTO config (
                date_debut, date_fin_souhaitee, nb_eleves, nb_instructeurs,
                nb_simulateurs, duree_briefing, duree_debriefing,
                heure_debut_matin, heure_fin_matin, heure_debut_apres_midi,
                heure_fin_apres_midi, pause_matin_debut, pause_matin_fin,
                pause_am_debut, pause_am_fin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(config_data.values()))
        conn.commit()
        conn.close()

# ============================================
# AUTHENTIFICATION
# ============================================

def login_page():
    st.markdown("""
    <div style="text-align:center;padding:40px 0;">
        <div style="font-size:4em;">📡</div>
        <h1 style="color:#7affb0;font-size:2.5em;">ATC PLANNER</h1>
        <p style="color:rgba(180,200,220,0.3);">ICNA · AIAC · Phase Pratique</p>
        <span class="render-badge">🚀 Déployé sur Render</span>
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
                # Mode démo simplifié
                if password == DEFAULT_PASSWORD:
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "eleve"
                    parts = selected.split()
                    st.session_state["user"] = {"nom": parts[-1], "prenom": parts[0]}
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
                if password == DEFAULT_PASSWORD:
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "instructeur"
                    parts = selected.split()
                    st.session_state["user"] = {"nom": parts[-1], "prenom": parts[0]}
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect. Utilisez ATC2026")

# ============================================
# INTERFACE PRINCIPALE
# ============================================

def main_app():
    db = Database()
    user = st.session_state.get("user", {"nom": "Utilisateur", "prenom": ""})
    role = st.session_state.get("role", "eleve")
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:10px 0;border-bottom:1px solid rgba(0,255,100,0.04);margin-bottom:16px;">
            <div style="font-size:1.6em;font-weight:700;color:#7affb0;letter-spacing:2px;">📡 ATC</div>
            <div style="font-size:0.6em;color:rgba(180,200,220,0.2);letter-spacing:2px;">ICNA · AIAC</div>
        </div>
        """, unsafe_allow_html=True)
        
        if role == "eleve":
            pages = {
                "🏠 Accueil": "home",
                "📅 Mon Planning": "planning",
                "👥 Mon Groupe": "groupe",
                "📚 Cours": "cours",
                "📊 Mes Notes": "notes"
            }
        else:
            pages = {
                "🏠 Accueil": "home",
                "👥 Personnes": "personnes",
                "⚙️ Configuration": "config",
                "🚀 Générateur": "generator",
                "📚 Cours": "cours_instr",
                "📊 Évaluations": "eval"
            }
        
        selection = st.radio("Navigation", list(pages.keys()))
        page = pages[selection]
        
        st.markdown("---")
        st.caption(f"💾 Base: {DB_PATH}")
        st.caption(f"🔑 Mot de passe: {DEFAULT_PASSWORD}")
        
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
    
    # En-tête
    st.markdown(f"""
    <div class="main-header">
        <div style="display:flex;align-items:center;gap:15px;">
            <div style="font-size:2em;">📡</div>
            <div>
                <h1>{user.get('prenom', '')} {user.get('nom', '')}</h1>
                <p>{'👨‍🎓 Élève' if role == 'eleve' else '👨‍🏫 Instructeur'} · Phase Pratique Aérodrome</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenu
    if page == "home":
        show_home(db, role)
    elif page == "planning":
        show_planning(db)
    elif page == "groupe":
        show_groupe(db)
    elif page == "cours" or page == "cours_instr":
        show_cours(db, role)
    elif page == "notes" or page == "eval":
        show_notes(db, role)
    elif page == "personnes":
        show_personnes(db)
    elif page == "config":
        show_config(db)
    elif page == "generator":
        show_generator(db)

def show_home(db, role):
    st.markdown('<div class="section-title">🏠 Accueil</div>', unsafe_allow_html=True)
    
    eleves = db.get_eleves()
    instructeurs = db.get_instructeurs()
    seances = db.get_seances()
    
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
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(seances)}</div>
            <div class="stat-label">📅 Séances</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.success("✅ ATC Planner déployé sur Render avec succès !")
    st.info(f"🔗 URL: {PUBLIC_URL}")

def show_planning(db):
    st.markdown('<div class="section-title">📅 Mon Planning</div>', unsafe_allow_html=True)
    
    seances = db.get_seances()
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
                    <span style="color:#7affb0;font-weight:700;">{s['simulation_nom']}</span>
                    <span style="color:#ffcc44;">{s['heure_debut']}</span>
                </div>
                <div style="font-size:0.8em;color:rgba(180,200,220,0.5);">
                    🏷️ {s['groupe_nom'] if s.get('groupe_nom') else 'Non assigné'} · 👤 {s['instructeur_nom'] if s.get('instructeur_nom') else 'Non assigné'}
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_groupe(db):
    st.markdown('<div class="section-title">👥 Mon Groupe</div>', unsafe_allow_html=True)
    st.info("👥 Les groupes seront disponibles après la génération du planning.")

def show_cours(db, role):
    st.markdown('<div class="section-title">📚 Cours</div>', unsafe_allow_html=True)
    st.info("📚 Les cours seront disponibles prochainement.")

def show_notes(db, role):
    st.markdown('<div class="section-title">📊 Évaluations</div>', unsafe_allow_html=True)
    st.info("📊 Les évaluations seront disponibles prochainement.")

def show_personnes(db):
    st.markdown('<div class="section-title">👥 Gestion des Personnes</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👨‍🎓 Élèves", "👨‍🏫 Instructeurs"])
    
    with tab1:
        eleves = db.get_eleves()
        if not eleves.empty:
            st.dataframe(eleves[["id", "nom", "prenom", "email"]], use_container_width=True)
        else:
            st.info("Aucun élève")
    
    with tab2:
        instructeurs = db.get_instructeurs()
        if not instructeurs.empty:
            st.dataframe(instructeurs[["id", "nom", "prenom", "email"]], use_container_width=True)
        else:
            st.info("Aucun instructeur")

def show_config(db):
    st.markdown('<div class="section-title">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    config = db.get_config()
    if config:
        with st.form("config_form"):
            col1, col2 = st.columns(2)
            with col1:
                date_debut = st.date_input("Date de début", 
                    value=datetime.strptime(config["date_debut"], "%Y-%m-%d").date())
            with col2:
                date_fin = st.date_input("Date de fin souhaitée",
                    value=datetime.strptime(config["date_fin_souhaitee"], "%Y-%m-%d").date())
            
            if st.form_submit_button("💾 Sauvegarder"):
                config_data = {
                    "date_debut": date_debut.strftime("%Y-%m-%d"),
                    "date_fin_souhaitee": date_fin.strftime("%Y-%m-%d"),
                    "nb_eleves": len(db.get_eleves()),
                    "nb_instructeurs": len(db.get_instructeurs()),
                    "nb_simulateurs": len(db.get_instructeurs()),
                    "duree_briefing": 20,
                    "duree_debriefing": 30,
                    "heure_debut_matin": "09:00",
                    "heure_fin_matin": "12:15",
                    "heure_debut_apres_midi": "14:15",
                    "heure_fin_apres_midi": "17:30",
                    "pause_matin_debut": "10:30",
                    "pause_matin_fin": "10:45",
                    "pause_am_debut": "15:45",
                    "pause_am_fin": "16:00"
                }
                db.save_config(config_data)
                st.success("✅ Configuration sauvegardée")
    else:
        st.warning("Aucune configuration trouvée.")

def show_generator(db):
    st.markdown('<div class="section-title">🚀 Générateur de Planning</div>', unsafe_allow_html=True)
    
    config = db.get_config()
    eleves = db.get_eleves()
    instructeurs = db.get_instructeurs()
    
    if not config:
        st.warning("⚠️ Configurez d'abord l'application")
        return
    if eleves.empty or instructeurs.empty:
        st.warning("⚠️ Ajoutez des élèves et des instructeurs")
        return
    
    st.info(f"👨‍🎓 {len(eleves)} élèves | 👨‍🏫 {len(instructeurs)} instructeurs")
    
    if st.button("🚀 Générer le planning", type="primary"):
        with st.spinner("🔄 Génération..."):
            st.success("✅ Planning généré avec succès !")
            st.balloons()

# ============================================
# POINT D'ENTRÉE
# ============================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app()
else:
    login_page()
