import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date, time as dtime
import json
import numpy as np
import random
import io
import os
import base64
import zipfile
from io import BytesIO
import html as html_lib
import hashlib
import secrets
import sqlite3
import warnings
warnings.filterwarnings("ignore")

# ============================================
# CONFIGURATION SQLITE
# ============================================
DB_PATH = "data/planning.db"
os.makedirs("data", exist_ok=True)

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================

st.set_page_config(
    page_title="ATC Planner - ICNA AIAC",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def esc(x):
    """Échappe le texte libre avant de l'insérer dans un bloc HTML brut."""
    if x is None:
        return ""
    return html_lib.escape(str(x))

# ============================================
# AUTHENTIFICATION - HACHAGE DES MOTS DE PASSE
# ============================================

PASSWORD_ITERATIONS = 100_000
DEFAULT_PASSWORD = "ATC2026"

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

def generate_temp_password() -> str:
    return secrets.token_urlsafe(6)

# ============================================
# STYLE CSS
# ============================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@300;400;600;700&display=swap');
    * { font-family: 'Inter', 'JetBrains Mono', sans-serif; }
    .stApp { background: #0a0e17; }
    .radar-container {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: radial-gradient(ellipse at center, #0d1a2b 0%, #060a12 100%);
        overflow: hidden;
    }
    .radar-screen {
        position: relative;
        width: 480px;
        height: 480px;
        border-radius: 50%;
        background: radial-gradient(circle at center, #0a1a0a 0%, #061206 40%, #030803 100%);
        border: 3px solid #1a4a2a;
        box-shadow: 0 0 60px rgba(0, 255, 100, 0.08), inset 0 0 80px rgba(0, 255, 100, 0.05);
    }
    .radar-ring {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        border: 1px solid rgba(0, 255, 100, 0.12);
    }
    .radar-ring:nth-child(1) { width: 25%; height: 25%; }
    .radar-ring:nth-child(2) { width: 45%; height: 45%; }
    .radar-ring:nth-child(3) { width: 65%; height: 65%; }
    .radar-ring:nth-child(4) { width: 85%; height: 85%; }
    .radar-crosshair::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: rgba(0, 255, 100, 0.08);
    }
    .radar-crosshair::after {
        content: '';
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 1px;
        background: rgba(0, 255, 100, 0.08);
    }
    .radar-sweep {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 50%;
        height: 2px;
        background: linear-gradient(90deg, rgba(0, 255, 100, 0.7), rgba(0, 255, 100, 0));
        transform-origin: 0% 50%;
        animation: sweep 4s linear infinite;
        border-radius: 0 2px 2px 0;
        filter: drop-shadow(0 0 12px rgba(0, 255, 100, 0.2));
    }
    @keyframes sweep {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .radar-blip {
        position: absolute;
        width: 6px;
        height: 6px;
        background: rgba(0, 255, 100, 0.8);
        border-radius: 50%;
        box-shadow: 0 0 12px rgba(0, 255, 100, 0.4);
        animation: blip-pulse 1.5s ease-in-out infinite;
    }
    .radar-blip:nth-child(1) { top: 28%; left: 35%; animation-delay: 0s; }
    .radar-blip:nth-child(2) { top: 55%; left: 68%; animation-delay: 0.5s; }
    .radar-blip:nth-child(3) { top: 72%; left: 42%; animation-delay: 1s; }
    .radar-blip:nth-child(4) { top: 40%; left: 72%; animation-delay: 1.5s; }
    .radar-blip:nth-child(5) { top: 65%; left: 25%; animation-delay: 2s; }
    @keyframes blip-pulse {
        0%, 100% { opacity: 0.3; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.2); }
    }
    .radar-center {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 12px;
        height: 12px;
        background: rgba(0, 255, 100, 0.9);
        border-radius: 50%;
        box-shadow: 0 0 30px rgba(0, 255, 100, 0.4);
        z-index: 10;
    }
    .radar-title {
        position: absolute;
        top: -50px;
        left: 50%;
        transform: translateX(-50%);
        color: rgba(0, 255, 100, 0.6);
        font-family: 'JetBrains Mono', monospace;
        font-size: 1em;
        font-weight: 700;
        letter-spacing: 4px;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .radar-title span { color: rgba(255, 200, 50, 0.5); font-weight: 300; }
    .radar-label {
        position: absolute;
        bottom: -50px;
        left: 50%;
        transform: translateX(-50%);
        color: rgba(0, 255, 100, 0.3);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65em;
        letter-spacing: 3px;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .login-card {
        position: absolute;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(10, 20, 30, 0.85);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(0, 255, 100, 0.1);
        border-radius: 16px;
        padding: 24px 32px;
        min-width: 300px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
        text-align: center;
    }
    .login-card h2 {
        color: rgba(0, 255, 100, 0.8);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9em;
        font-weight: 600;
        letter-spacing: 2px;
        margin-bottom: 16px;
        text-transform: uppercase;
    }
    .flight-strip {
        background: linear-gradient(135deg, #0d1a2b 0%, #162a3f 100%);
        border-left: 4px solid #2a7a4a;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin: 4px 0;
        font-family: 'JetBrains Mono', monospace;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .flight-strip:hover {
        transform: translateX(4px);
        border-left-color: #4aff8a;
        box-shadow: 0 4px 16px rgba(0, 255, 100, 0.08);
    }
    .flight-strip .strip-callsign { color: #7affb0; font-weight: 700; font-size: 1em; letter-spacing: 0.5px; }
    .flight-strip .strip-info { color: rgba(180, 200, 220, 0.5); font-size: 0.75em; letter-spacing: 0.3px; }
    .flight-strip .strip-time { color: #ffcc44; font-weight: 600; font-size: 0.85em; }
    .strip-role-controller { background: rgba(0, 255, 100, 0.12); color: #7affb0; border: 1px solid rgba(0, 255, 100, 0.1); }
    .strip-role-pseudo { background: rgba(255, 200, 50, 0.1); color: #ffcc44; border: 1px solid rgba(255, 200, 50, 0.08); }
    .strip-role-observer { background: rgba(100, 150, 200, 0.06); color: #88bbdd; border: 1px solid rgba(100, 150, 200, 0.06); }
    .stat-card {
        background: linear-gradient(145deg, #0d1a2b 0%, #162a3f 100%);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        border: 1px solid rgba(0, 255, 100, 0.04);
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
    }
    .stat-number { font-size: 2.2em; font-weight: 800; color: #7affb0; font-family: 'JetBrains Mono', monospace; }
    .stat-label { font-size: 0.7em; color: rgba(180, 200, 220, 0.4); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-family: 'JetBrains Mono', monospace; }
    .stat-icon { font-size: 1.5em; display: block; margin-bottom: 4px; }
    .badge-success { background: rgba(0, 255, 100, 0.1); color: #7affb0; padding: 2px 10px; border-radius: 10px; font-size: 0.65em; font-weight: 600; border: 1px solid rgba(0, 255, 100, 0.06); }
    .badge-warning { background: rgba(255, 200, 50, 0.08); color: #ffcc44; padding: 2px 10px; border-radius: 10px; font-size: 0.65em; font-weight: 600; border: 1px solid rgba(255, 200, 50, 0.06); }
    .badge-info { background: rgba(50, 200, 255, 0.06); color: #66ddff; padding: 2px 10px; border-radius: 10px; font-size: 0.65em; font-weight: 600; border: 1px solid rgba(50, 200, 255, 0.04); }
    .badge-danger { background: rgba(255, 80, 80, 0.06); color: #ff7777; padding: 2px 10px; border-radius: 10px; font-size: 0.65em; font-weight: 600; border: 1px solid rgba(255, 80, 80, 0.04); }
    .badge-td { background: rgba(255, 150, 50, 0.08); color: #ff9944; padding: 2px 10px; border-radius: 10px; font-size: 0.65em; font-weight: 600; border: 1px solid rgba(255, 150, 50, 0.06); }
    .scenario-card {
        background: linear-gradient(145deg, #0d1a2b 0%, #162a3f 100%);
        border-radius: 10px;
        padding: 14px 18px;
        margin: 6px 0;
        border-left: 3px solid #4444cc;
    }
    .scenario-title { font-weight: 600; color: #8888ff; font-family: 'JetBrains Mono', monospace; font-size: 0.95em; }
    .scenario-meta { font-size: 0.75em; color: rgba(180, 200, 220, 0.4); font-family: 'JetBrains Mono', monospace; }
    .groupe-card {
        background: linear-gradient(145deg, #0d1a2b 0%, #162a3f 100%);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 10px 0;
        border: 1px solid rgba(0, 255, 100, 0.06);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .groupe-card h4 { color: #7affb0; font-weight: 700; margin: 0 0 8px 0; font-family: 'JetBrains Mono', monospace; }
    .groupe-card .eleve-chip {
        display: inline-block;
        background: rgba(0, 255, 100, 0.06);
        border: 1px solid rgba(0, 255, 100, 0.08);
        border-radius: 16px;
        padding: 4px 12px;
        margin: 3px 4px 3px 0;
        font-size: 0.8em;
        color: #b0c8e0;
        font-family: 'JetBrains Mono', monospace;
    }
    .groupe-card .instructeur-badge {
        display: inline-block;
        background: rgba(255, 200, 50, 0.06);
        border: 1px solid rgba(255, 200, 50, 0.08);
        border-radius: 16px;
        padding: 4px 12px;
        font-size: 0.8em;
        color: #ffcc44;
        font-family: 'JetBrains Mono', monospace;
    }
    .doc-viewer {
        background: rgba(10, 20, 30, 0.6);
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        border: 1px solid rgba(0, 255, 100, 0.04);
    }
    .doc-btn {
        text-decoration: none;
        border-radius: 8px;
        padding: 6px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85em;
        display: inline-block;
    }
    .doc-btn-open {
        background: rgba(50, 200, 255, 0.05);
        border: 1px solid rgba(50, 200, 255, 0.1);
        color: #66ddff;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060a12 0%, #0d1a2b 100%);
        border-right: 1px solid rgba(0, 255, 100, 0.04);
    }
    [data-testid="stSidebar"] * { color: rgba(200, 220, 240, 0.7); }
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: 1px solid rgba(0, 255, 100, 0.1) !important;
        background: rgba(0, 255, 100, 0.03) !important;
        color: #7affb0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: 0.5px !important;
        padding: 0.5rem 1.2rem !important;
    }
    .stButton > button:hover {
        background: rgba(0, 255, 100, 0.06) !important;
        border-color: rgba(0, 255, 100, 0.2) !important;
    }
    .section-title {
        font-size: 1.2em;
        font-weight: 700;
        color: #7affb0;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 10px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stNumberInput input {
        background: rgba(10, 20, 30, 0.6) !important;
        border: 1px solid rgba(0, 255, 100, 0.06) !important;
        border-radius: 8px !important;
        color: #b0c8e0 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stFileUploader > div {
        background: rgba(10, 20, 30, 0.6) !important;
        border: 1px solid rgba(0, 255, 100, 0.06) !important;
        border-radius: 8px !important;
    }
    hr { border-color: rgba(0, 255, 100, 0.04) !important; margin: 16px 0 !important; }
    ::-webkit-scrollbar { width: 4px; background: rgba(10, 20, 30, 0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(0, 255, 100, 0.1); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATABASE SQLITE
# ============================================

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_schema()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.isolation_level = None
        return conn

    def _query(self, sql, params=None):
        conn = self.get_connection()
        try:
            if params:
                df = pd.read_sql_query(sql, conn, params=params)
            else:
                df = pd.read_sql_query(sql, conn)
        finally:
            conn.close()
        return df

    def _exec(self, sql, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
        except Exception as e:
            raise e
        finally:
            conn.close()

    def _exec_many(self, sql, list_of_params):
        if not list_of_params:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, list_of_params)
        except Exception as e:
            raise e
        finally:
            conn.close()

    def _exec_returning_id(self, sql, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            new_id = cursor.lastrowid
        except Exception as e:
            raise e
        finally:
            conn.close()
        return new_id

    def _ensure_schema(self):
        ddl_statements = [
            """CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_debut DATE NOT NULL,
                date_fin_souhaitee DATE NOT NULL,
                nb_eleves INTEGER NOT NULL,
                nb_instructeurs INTEGER NOT NULL,
                nb_simulateurs INTEGER NOT NULL,
                duree_briefing INTEGER DEFAULT 20,
                duree_debriefing INTEGER DEFAULT 30,
                heure_debut_matin TEXT DEFAULT '09:00',
                heure_fin_matin TEXT DEFAULT '12:15',
                heure_debut_apres_midi TEXT DEFAULT '14:15',
                heure_fin_apres_midi TEXT DEFAULT '17:30',
                pause_matin_debut TEXT DEFAULT '10:30',
                pause_matin_fin TEXT DEFAULT '10:45',
                pause_am_debut TEXT DEFAULT '15:45',
                pause_am_fin TEXT DEFAULT '16:00'
            )""",
            """CREATE TABLE IF NOT EXISTS eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, prenom TEXT NOT NULL, email TEXT, groupe_id INTEGER,
                password_hash TEXT, password_salt TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS instructeurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, prenom TEXT NOT NULL, actif BOOLEAN DEFAULT 1,
                password_hash TEXT, password_salt TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS groupes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, instructeur_id INTEGER, simulateur_id INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS groupe_eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                groupe_id INTEGER, eleve_id INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, duree INTEGER DEFAULT 65, est_test BOOLEAN DEFAULT 0, ordre INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS seances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL, heure_debut TEXT NOT NULL, duree INTEGER NOT NULL,
                type TEXT CHECK(type IN ('briefing', 'simulation', 'debriefing')),
                simulation_id INTEGER, groupe_id INTEGER, instructeur_id INTEGER,
                instructeur_evaluateur_id INTEGER, simulateur_id INTEGER,
                controle_eleve_id INTEGER, pseudo_eleve_id INTEGER,
                observateurs TEXT, statut TEXT DEFAULT 'planifiee', notes TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS cours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL, description TEXT,
                type TEXT CHECK(type IN ('pdf', 'video', 'document', 'lien')),
                contenu TEXT, date_upload DATE, instructeur_id INTEGER,
                groupe_cible_id INTEGER, tags TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL, description TEXT, objectifs TEXT, duree_estimee INTEGER,
                niveau TEXT CHECK(niveau IN ('debutant', 'intermediaire', 'avance')),
                simulateur_requis BOOLEAN DEFAULT 0, instructions TEXT, contenu TEXT,
                type TEXT CHECK(type IN ('pdf', 'video', 'document', 'lien')),
                date_creation DATE, instructeur_id INTEGER, groupe_cible_id INTEGER, tags TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS td (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL, description TEXT,
                type TEXT CHECK(type IN ('exercice', 'corrige', 'serie', 'devoir')),
                contenu TEXT, date_upload DATE, instructeur_id INTEGER,
                groupe_cible_id INTEGER, tags TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS grilles_evaluation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, description TEXT, criteres TEXT, bareme TEXT,
                instructeur_id INTEGER, date_creation DATE
            )""",
            """CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER, instructeur_id INTEGER, grille_id INTEGER,
                simulation_id INTEGER, seance_id INTEGER, date_note DATE, note DECIMAL(5,2),
                appreciation TEXT, scores_criteres TEXT, commentaires TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS admin_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                code_hash TEXT, code_salt TEXT
            )""",
        ]
        for ddl in ddl_statements:
            self._exec(ddl)

        try:
            nb_sims = self._query("SELECT COUNT(*) AS n FROM simulations").iloc[0]["n"]
        except:
            nb_sims = 0
            
        if nb_sims == 0:
            sims = [
                {"nom": "Synthese Dynamique", "duree": 65, "est_test": 0, "ordre": 1},
                {"nom": "Simulation 1", "duree": 65, "est_test": 0, "ordre": 2},
                {"nom": "Simulation 2", "duree": 65, "est_test": 0, "ordre": 3},
                {"nom": "Simulation 3", "duree": 65, "est_test": 0, "ordre": 4},
                {"nom": "Simulation 4", "duree": 65, "est_test": 0, "ordre": 5},
                {"nom": "Simulation 5", "duree": 65, "est_test": 0, "ordre": 6},
                {"nom": "Simulation 6", "duree": 65, "est_test": 0, "ordre": 7},
                {"nom": "Simulation Test", "duree": 65, "est_test": 1, "ordre": 8},
            ]
            self._exec_many(
                "INSERT INTO simulations (nom, duree, est_test, ordre) VALUES (:nom, :duree, :est_test, :ordre)",
                sims
            )

        try:
            nb_grilles = self._query("SELECT COUNT(*) AS n FROM grilles_evaluation").iloc[0]["n"]
        except:
            nb_grilles = 0
            
        if nb_grilles == 0:
            self._exec(
                "INSERT INTO grilles_evaluation (nom, description, criteres, bareme, date_creation) "
                "VALUES (:nom, :description, :criteres, :bareme, :date_creation)",
                {
                    "nom": "Grille ATC Standard",
                    "description": "Grille d'évaluation standard",
                    "criteres": json.dumps(["Phraséologie", "Anticipation", "Gestion du trafic", "Communication", "Réactivité"]),
                    "bareme": json.dumps([4, 4, 4, 4, 4]),
                    "date_creation": date.today().strftime("%Y-%m-%d"),
                }
            )

        try:
            nb_instr = self._query("SELECT COUNT(*) AS n FROM instructeurs").iloc[0]["n"]
            nb_eleves = self._query("SELECT COUNT(*) AS n FROM eleves").iloc[0]["n"]
        except:
            nb_instr = 0
            nb_eleves = 0
            
        if nb_instr == 0 and nb_eleves == 0:
            for nom, prenom in [("RIFAI", "Mr"), ("TAHERI", "Mr"), ("JBARA", "Mr")]:
                self.add_instructeur(nom, prenom, password=DEFAULT_PASSWORD)
            for nom, prenom in [
                ("KOUBAA", "AYOUB"), ("BAMIDA", "AYMANE"), ("CHADDANI", "MOHAMED"),
                ("KHOULANE", "ILYAS"), ("AKNOUZE", "RACHID"), ("MIFDAL", "IMANE"),
                ("KOUMI", "KHADIJA"), ("GUENNOUN", "CHAIMAE"), ("ICHOU", "ABDELLATIF"),
            ]:
                self.add_eleve(nom, prenom, password=DEFAULT_PASSWORD)

        for table in ("eleves", "instructeurs"):
            try:
                sans_mdp = self._query(f"SELECT id FROM {table} WHERE password_hash IS NULL OR password_salt IS NULL")
                for row_id in sans_mdp["id"].tolist():
                    pwd_hash, salt = hash_password(DEFAULT_PASSWORD)
                    self._exec(
                        f"UPDATE {table} SET password_hash = :h, password_salt = :s WHERE id = :id",
                        {"h": pwd_hash, "s": salt, "id": int(row_id)}
                    )
            except:
                pass

    def verify_password_eleve(self, eleve_id, password):
        df = self._query("SELECT password_hash, password_salt FROM eleves WHERE id = :id", {"id": eleve_id})
        if df.empty:
            return False
        return verify_password(password, df.iloc[0]["password_salt"], df.iloc[0]["password_hash"])

    def verify_password_instructeur(self, instr_id, password):
        df = self._query("SELECT password_hash, password_salt FROM instructeurs WHERE id = :id", {"id": instr_id})
        if df.empty:
            return False
        return verify_password(password, df.iloc[0]["password_salt"], df.iloc[0]["password_hash"])

    def admin_code_configured(self):
        df = self._query("SELECT code_hash, code_salt FROM admin_config WHERE id = 1")
        if df.empty:
            return False
        return bool(df.iloc[0]["code_hash"] and df.iloc[0]["code_salt"])

    def verify_admin_code(self, code):
        df = self._query("SELECT code_hash, code_salt FROM admin_config WHERE id = 1")
        if df.empty:
            return False
        return verify_password(code, df.iloc[0]["code_salt"], df.iloc[0]["code_hash"])

    def set_password_eleve(self, eleve_id, new_password):
        pwd_hash, salt = hash_password(new_password)
        self._exec("UPDATE eleves SET password_hash = :h, password_salt = :s WHERE id = :id",
                    {"h": pwd_hash, "s": salt, "id": eleve_id})

    def set_password_instructeur(self, instr_id, new_password):
        pwd_hash, salt = hash_password(new_password)
        self._exec("UPDATE instructeurs SET password_hash = :h, password_salt = :s WHERE id = :id",
                    {"h": pwd_hash, "s": salt, "id": instr_id})

    def get_eleves(self, groupe_id=None):
        if groupe_id:
            return self._query("SELECT * FROM eleves WHERE groupe_id = :gid ORDER BY nom, prenom", {"gid": groupe_id})
        return self._query("SELECT * FROM eleves ORDER BY nom, prenom")

    def get_eleve_by_id(self, eleve_id):
        df = self._query("SELECT id, nom, prenom, email, groupe_id FROM eleves WHERE id = :id", {"id": eleve_id})
        if df.empty:
            return None
        row = df.iloc[0]
        return (int(row["id"]), row["nom"], row["prenom"], row["email"], row["groupe_id"])

    def add_eleve(self, nom, prenom, email=None, password=None):
        temp_password = None
        if not password:
            temp_password = generate_temp_password()
            password = temp_password
        pwd_hash, salt = hash_password(password)
        new_id = self._exec_returning_id(
            "INSERT INTO eleves (nom, prenom, email, password_hash, password_salt) "
            "VALUES (:nom, :prenom, :email, :h, :s) RETURNING id",
            {"nom": nom, "prenom": prenom, "email": email, "h": pwd_hash, "s": salt}
        )
        return new_id, temp_password

    def delete_eleve(self, eleve_id):
        self._exec("DELETE FROM groupe_eleves WHERE eleve_id = :id", {"id": eleve_id})
        self._exec("DELETE FROM notes WHERE eleve_id = :id", {"id": eleve_id})
        self._exec("DELETE FROM eleves WHERE id = :id", {"id": eleve_id})

    def get_instructeurs(self):
        return self._query("SELECT * FROM instructeurs WHERE actif = 1 ORDER BY nom, prenom")

    def get_instructeur_by_id(self, instr_id):
        df = self._query("SELECT id, nom, prenom, actif FROM instructeurs WHERE id = :id", {"id": instr_id})
        if df.empty:
            return None
        row = df.iloc[0]
        return (int(row["id"]), row["nom"], row["prenom"], row["actif"])

    def add_instructeur(self, nom, prenom, password=None):
        temp_password = None
        if not password:
            temp_password = generate_temp_password()
            password = temp_password
        pwd_hash, salt = hash_password(password)
        new_id = self._exec_returning_id(
            "INSERT INTO instructeurs (nom, prenom, actif, password_hash, password_salt) "
            "VALUES (:nom, :prenom, 1, :h, :s) RETURNING id",
            {"nom": nom, "prenom": prenom, "h": pwd_hash, "s": salt}
        )
        return new_id, temp_password

    def delete_instructeur(self, instr_id):
        self._exec("DELETE FROM instructeurs WHERE id = :id", {"id": instr_id})

    def get_groupes(self):
        return self._query("""
            SELECT g.*, i.nom || ' ' || i.prenom as instructeur_nom
            FROM groupes g LEFT JOIN instructeurs i ON g.instructeur_id = i.id            ORDER BY g.id
        """)

    def get_groupe_eleves(self, groupe_id):
        return self._query("""
            SELECT e.* FROM groupe_eleves ge JOIN eleves e ON ge.eleve_id = e.id
            WHERE ge.groupe_id = :gid ORDER BY e.nom, e.prenom
        """, {"gid": groupe_id})

    def get_groupe_de_eleve(self, eleve_id):
        df = self._query("""
            SELECT g.*, i.nom || ' ' || i.prenom as instructeur_nom
            FROM eleves e
            JOIN groupes g ON e.groupe_id = g.id
            LEFT JOIN instructeurs i ON g.instructeur_id = i.id
            WHERE e.id = :id
        """, {"id": eleve_id})
        return df.iloc[0].to_dict() if not df.empty else None

    def save_groupes(self, groupes):
        id_map = {}
        for g in groupes:
            new_id = self._exec_returning_id(
                "INSERT INTO groupes (nom, instructeur_id, simulateur_id) "
                "VALUES (:nom, :instr, :sim) RETURNING id",
                {"nom": g["nom"], "instr": g["instructeur_id"], "sim": g["simulateur_id"]}
            )
            id_map[g["id"]] = new_id
            for eid in g["eleves"]:
                self._exec("INSERT INTO groupe_eleves (groupe_id, eleve_id) VALUES (:gid, :eid)",
                          {"gid": new_id, "eid": eid})
                self._exec("UPDATE eleves SET groupe_id = :gid WHERE id = :eid",
                          {"gid": new_id, "eid": eid})
        return id_map

    def get_seances(self):
        return self._query("""
            SELECT s.*, sim.nom as simulation_nom, g.nom as groupe_nom,
                   i.nom || ' ' || i.prenom as instructeur_nom,
                   e1.nom || ' ' || e1.prenom as controle_eleve_nom,
                   e2.nom || ' ' || e2.prenom as pseudo_eleve_nom
            FROM seances s
            LEFT JOIN simulations sim ON s.simulation_id = sim.id
            LEFT JOIN groupes g ON s.groupe_id = g.id
            LEFT JOIN instructeurs i ON s.instructeur_id = i.id
            LEFT JOIN eleves e1 ON s.controle_eleve_id = e1.id
            LEFT JOIN eleves e2 ON s.pseudo_eleve_id = e2.id
            ORDER BY s.date, s.heure_debut
        """)

    def get_seances_eleve(self, eleve_id):
        return self._query("""
            SELECT s.*, sim.nom as simulation_nom, g.nom as groupe_nom,
                   i.nom || ' ' || i.prenom as instructeur_nom,
                   e1.nom || ' ' || e1.prenom as controle_eleve_nom,
                   e2.nom || ' ' || e2.prenom as pseudo_eleve_nom
            FROM seances s
            LEFT JOIN simulations sim ON s.simulation_id = sim.id
            LEFT JOIN groupes g ON s.groupe_id = g.id
            LEFT JOIN instructeurs i ON s.instructeur_id = i.id
            LEFT JOIN eleves e1 ON s.controle_eleve_id = e1.id
            LEFT JOIN eleves e2 ON s.pseudo_eleve_id = e2.id
            WHERE s.type = 'simulation' AND (s.controle_eleve_id = :eid OR s.pseudo_eleve_id = :eid)
            ORDER BY s.date, s.heure_debut
        """, {"eid": eleve_id})

    def save_seances(self, seances):
        rows = [{
            "date": s["date"], "heure": s["heure_debut"], "duree": s["duree"], "type": s["type"],
            "sim_id": s.get("simulation_id"), "groupe_id": s.get("groupe_id"),
            "instr_id": s.get("instructeur_id"), "instr_eval_id": s.get("instructeur_evaluateur_id"),
            "sim_engin": s.get("simulateur_id"), "controle_id": s.get("controle_eleve_id"),
            "pseudo_id": s.get("pseudo_eleve_id"), "observateurs": json.dumps(s.get("observateurs", [])),
            "notes": s.get("notes", ""),
        } for s in seances]
        self._exec_many("""
            INSERT INTO seances (
                date, heure_debut, duree, type, simulation_id, groupe_id,
                instructeur_id, instructeur_evaluateur_id, simulateur_id,
                controle_eleve_id, pseudo_eleve_id, observateurs, notes
            ) VALUES (
                :date, :heure, :duree, :type, :sim_id, :groupe_id,
                :instr_id, :instr_eval_id, :sim_engin,
                :controle_id, :pseudo_id, :observateurs, :notes
            )
        """, rows)

    def reset_planning(self):
        for table in ("seances", "groupe_eleves", "groupes"):
            self._exec(f"DELETE FROM {table}")
        self._exec("UPDATE eleves SET groupe_id = NULL")

    def _filtered_by_group(self, table, eleve_id, groupe_id, order_col):
        if eleve_id is not None:
            df_g = self._query("SELECT groupe_id FROM eleves WHERE id = :id", {"id": eleve_id})
            if not df_g.empty and pd.notna(df_g.iloc[0]["groupe_id"]):
                groupe_id = int(df_g.iloc[0]["groupe_id"])
            else:
                groupe_id = None
        if eleve_id is not None or groupe_id is not None:
            return self._query(
                f"SELECT * FROM {table} WHERE groupe_cible_id IS NULL OR groupe_cible_id = :gid "
                f"ORDER BY {order_col} DESC",
                {"gid": groupe_id}
            )
        return self._query(f"SELECT * FROM {table} ORDER BY {order_col} DESC")

    def add_cours(self, cours):
        self._exec("""
            INSERT INTO cours (titre, description, type, contenu, date_upload, instructeur_id, groupe_cible_id, tags)
            VALUES (:titre, :description, :type, :contenu, :date_upload, :instructeur_id, :groupe_cible_id, :tags)
        """, {
            "titre": cours["titre"], "description": cours["description"], "type": cours["type"],
            "contenu": cours["contenu"], "date_upload": cours["date_upload"],
            "instructeur_id": cours.get("instructeur_id"), "groupe_cible_id": cours.get("groupe_cible_id"),
            "tags": cours.get("tags", ""),
        })

    def get_cours(self, eleve_id=None, groupe_id=None):
        return self._filtered_by_group("cours", eleve_id, groupe_id, "date_upload")

    def delete_cours(self, cours_id):
        self._exec("DELETE FROM cours WHERE id = :id", {"id": cours_id})

    def add_scenario(self, scenario):
        self._exec("""
            INSERT INTO scenarios (titre, description, objectifs, duree_estimee, niveau, simulateur_requis,
                                    instructions, contenu, type, date_creation, instructeur_id, groupe_cible_id, tags)
            VALUES (:titre, :description, :objectifs, :duree_estimee, :niveau, :simulateur_requis,
                    :instructions, :contenu, :type, :date_creation, :instructeur_id, :groupe_cible_id, :tags)
        """, {
            "titre": scenario["titre"], "description": scenario["description"], "objectifs": scenario["objectifs"],
            "duree_estimee": scenario["duree_estimee"], "niveau": scenario["niveau"],
            "simulateur_requis": int(bool(scenario["simulateur_requis"])),
            "instructions": scenario["instructions"],
            "contenu": scenario.get("contenu", ""), "type": scenario.get("type", "document"),
            "date_creation": scenario["date_creation"], "instructeur_id": scenario.get("instructeur_id"),
            "groupe_cible_id": scenario.get("groupe_cible_id"), "tags": scenario.get("tags", ""),
        })

    def get_scenarios(self, eleve_id=None, groupe_id=None):
        return self._filtered_by_group("scenarios", eleve_id, groupe_id, "date_creation")

    def delete_scenario(self, scenario_id):
        self._exec("DELETE FROM scenarios WHERE id = :id", {"id": scenario_id})

    def add_td(self, td):
        self._exec("""
            INSERT INTO td (titre, description, type, contenu, date_upload, instructeur_id, groupe_cible_id, tags)
            VALUES (:titre, :description, :type, :contenu, :date_upload, :instructeur_id, :groupe_cible_id, :tags)
        """, {
            "titre": td["titre"], "description": td["description"], "type": td["type"],
            "contenu": td["contenu"], "date_upload": td["date_upload"],
            "instructeur_id": td.get("instructeur_id"), "groupe_cible_id": td.get("groupe_cible_id"),
            "tags": td.get("tags", ""),
        })

    def get_td(self, eleve_id=None, groupe_id=None):
        return self._filtered_by_group("td", eleve_id, groupe_id, "date_upload")

    def delete_td(self, td_id):
        self._exec("DELETE FROM td WHERE id = :id", {"id": td_id})

    def add_grille(self, grille):
        self._exec("""
            INSERT INTO grilles_evaluation (nom, description, criteres, bareme, instructeur_id, date_creation)
            VALUES (:nom, :description, :criteres, :bareme, :instructeur_id, :date_creation)
        """, {
            "nom": grille["nom"], "description": grille["description"],
            "criteres": grille["criteres"], "bareme": grille["bareme"],
            "instructeur_id": grille.get("instructeur_id"),
            "date_creation": grille["date_creation"],
        })

    def get_grilles(self):
        return self._query("SELECT * FROM grilles_evaluation ORDER BY date_creation DESC")

    def add_note(self, note):
        self._exec("""
            INSERT INTO notes (eleve_id, instructeur_id, grille_id, simulation_id, seance_id, date_note, note,
                                appreciation, scores_criteres, commentaires)
            VALUES (:eleve_id, :instructeur_id, :grille_id, :simulation_id, :seance_id, :date_note, :note,
                    :appreciation, :scores_criteres, :commentaires)
        """, {
            "eleve_id": note["eleve_id"], "instructeur_id": note["instructeur_id"],
            "grille_id": note.get("grille_id"), "simulation_id": note.get("simulation_id"),
            "seance_id": note.get("seance_id"), "date_note": note["date_note"], "note": note["note"],
            "appreciation": note.get("appreciation", ""), "scores_criteres": note.get("scores_criteres", "[]"),
            "commentaires": note.get("commentaires", ""),
        })

    def get_notes_eleve(self, eleve_id):
        return self._query("""
            SELECT n.*, sim.nom as simulation_nom,
                   i.nom || ' ' || i.prenom as instructeur_nom, g.nom as grille_nom
            FROM notes n
            LEFT JOIN simulations sim ON n.simulation_id = sim.id
            LEFT JOIN instructeurs i ON n.instructeur_id = i.id
            LEFT JOIN grilles_evaluation g ON n.grille_id = g.id
            WHERE n.eleve_id = :id
            ORDER BY n.date_note DESC
        """, {"id": eleve_id})

    def delete_note(self, note_id):
        self._exec("DELETE FROM notes WHERE id = :id", {"id": note_id})

    def delete_notes_eleve(self, eleve_id):
        self._exec("DELETE FROM notes WHERE eleve_id = :id", {"id": eleve_id})

    def save_config(self, config):
        self._exec("DELETE FROM config")
        self._exec("""
            INSERT INTO config (
                date_debut, date_fin_souhaitee, nb_eleves, nb_instructeurs,
                nb_simulateurs, duree_briefing, duree_debriefing,
                heure_debut_matin, heure_fin_matin, heure_debut_apres_midi, heure_fin_apres_midi,
                pause_matin_debut, pause_matin_fin, pause_am_debut, pause_am_fin
            ) VALUES (
                :date_debut, :date_fin_souhaitee, :nb_eleves, :nb_instructeurs,
                :nb_simulateurs, :duree_briefing, :duree_debriefing,
                :heure_debut_matin, :heure_fin_matin, :heure_debut_apres_midi, :heure_fin_apres_midi,
                :pause_matin_debut, :pause_matin_fin, :pause_am_debut, :pause_am_fin
            )
        """, config)

    def get_config(self):
        df = self._query("SELECT * FROM config ORDER BY id DESC LIMIT 1")
        return df.iloc[0].to_dict() if not df.empty else None

    def get_simulations(self):
        return self._query("SELECT * FROM simulations ORDER BY ordre")

    def update_simulation_duree(self, sim_id, duree):
        self._exec("UPDATE simulations SET duree = :duree WHERE id = :id", {"duree": duree, "id": sim_id})

    def delete_all_data(self):
        for table in ("seances", "groupe_eleves", "groupes", "eleves", "instructeurs",
                      "cours", "scenarios", "td", "notes", "grilles_evaluation"):
            self._exec(f"DELETE FROM {table}")

# ============================================
# FONCTION DE VISUALISATION DE DOCUMENTS - VERSION STREAMLIT CLOUD
# ============================================

def detect_file_type(decoded):
    """Renvoie (extension, icone, label, mime_type) à partir des octets."""
    if decoded[:4] == b'%PDF':
        return "pdf", "📄", "Document PDF", "application/pdf"
    if len(decoded) > 4 and decoded[:4] == b'PK\x03\x04':
        try:
            with zipfile.ZipFile(BytesIO(decoded)) as zf:
                names = zf.namelist()
                if 'word/document.xml' in names:
                    return "docx", "📝", "Document Word (DOCX)", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                if 'xl/workbook.xml' in names:
                    return "xlsx", "📊", "Tableur Excel (XLSX)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                if 'ppt/presentation.xml' in names:
                    return "pptx", "📽️", "Présentation PowerPoint (PPTX)", "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        except Exception:
            pass
        return "zip", "📦", "Archive ZIP", "application/zip"
    if decoded[:8] == b'\x89PNG\r\n\x1a\n':
        return "png", "🖼️", "Image PNG", "image/png"
    if decoded[:3] == b'\xff\xd8\xff':
        return "jpg", "🖼️", "Image JPEG", "image/jpeg"
    if decoded[:6] in (b'GIF87a', b'GIF89a'):
        return "gif", "🖼️", "Image GIF", "image/gif"
    try:
        decoded.decode('utf-8')
        return "txt", "📝", "Document texte", "text/plain"
    except Exception:
        return "bin", "📎", "Fichier", "application/octet-stream"

from streamlit_pdf_viewer import pdf_viewer

def render_document_view(contenu, type_doc, titre, doc_index=None):
    """Affiche un document - Version avec streamlit-pdf-viewer"""
    
    if not contenu:
        st.info("Aucun contenu disponible pour ce document.")
        return

    titre_safe = esc(titre)

    if doc_index is None:
        doc_index = random.randint(1000, 9999)

    # --- Gestion des liens externes ---
    if contenu.startswith(("http://", "https://")):
        st.markdown(f"""
        <div class="doc-viewer">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap;">
                <span style="font-size:1.2em;">🔗</span>
                <div>
                    <div style="color:#7affb0;font-weight:600;">{titre_safe}</div>
                    <div style="color:rgba(180,200,220,0.4);font-size:0.8em;">Lien externe</div>
                </div>
                <div style="margin-left:auto;">
                    <a href="{contenu}" target="_blank" class="doc-btn doc-btn-open">🔗 Ouvrir</a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # --- DÉCODAGE BASE64 ROBUSTE ---
    decoded = None
    
    # Tentative 1: Décodage base64 standard avec padding
    try:
        padding = len(contenu) % 4
        if padding:
            contenu_padded = contenu + '=' * (4 - padding)
        else:
            contenu_padded = contenu
        decoded = base64.b64decode(contenu_padded)
    except Exception:
        pass
    
    # Tentative 2: Décodage base64 sans padding
    if decoded is None:
        try:
            decoded = base64.b64decode(contenu + '==')
        except Exception:
            pass
    
    # Tentative 3: Si le contenu est du texte brut
    if decoded is None:
        try:
            if contenu.startswith('%PDF'):
                decoded = contenu.encode('utf-8')
        except Exception:
            pass
    
    if decoded is None:
        st.error("❌ Impossible de décoder le document")
        st.code(contenu[:200])
        return

    # --- DÉTECTION DU TYPE ---
    file_ext, icon, label, mime_type = detect_file_type(decoded)
    taille_kb = len(decoded) // 1024
    taille_mo = len(decoded) / (1024 * 1024)

    # --- AFFICHAGE DES INFOS ---
    st.markdown(f"""
    <div class="doc-viewer">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <span style="font-size:1.2em;">{icon}</span>
            <div>
                <div style="color:#7affb0;font-weight:600;">{titre_safe}</div>
                <div style="color:rgba(180,200,220,0.4);font-size:0.8em;">{esc(label)}</div>
                <div style="color:rgba(180,200,220,0.3);font-size:0.7em;">📦 {taille_kb} KB ({taille_mo:.2f} Mo)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- AFFICHAGE DU PDF AVEC STREAMLIT-PDF-VIEWER ---
    if mime_type == "application/pdf":
        st.markdown("### 📄 Aperçu du document")
        
        # Utiliser le composant streamlit-pdf-viewer
        # Il passe par le mécanisme officiel des composants Streamlit
        try:
            pdf_viewer(input=decoded, width=1100, height=700)
        except Exception as e:
            st.error(f"❌ Erreur d'affichage du PDF : {str(e)}")
            
            # Fallback : lien de téléchargement
            pdf_b64 = base64.b64encode(decoded).decode("utf-8")
            data_url = f"data:application/pdf;base64,{pdf_b64}"
            st.markdown(f"""
            <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
                <a href="{data_url}" target="_blank" 
                   style="display:inline-block;padding:10px 20px;background:rgba(0,255,100,0.05);
                          border:1px solid rgba(0,255,100,0.1);border-radius:8px;color:#66ddff;
                          text-decoration:none;font-family:'JetBrains Mono',monospace;text-align:center;">
                    🔗 Ouvrir dans un nouvel onglet
                </a>
            </div>
            """, unsafe_allow_html=True)

    elif mime_type.startswith("image/"):
        st.image(decoded, caption=titre, use_container_width=True)

    elif mime_type == "text/plain":
        try:
            text_content = decoded.decode("utf-8")
            with st.expander("📄 Voir le contenu texte", expanded=True):
                st.text(text_content[:5000] + ("..." if len(text_content) > 5000 else ""))
        except Exception:
            pass

    else:
        st.info(f"📎 Type de document: {label}")
    
    # --- BOUTON DE TÉLÉCHARGEMENT ---
    st.download_button(
        label=f"📥 Télécharger {titre}.{file_ext}",
        data=decoded,
        file_name=f"{titre}.{file_ext}",
        mime=mime_type,
        use_container_width=True,
        key=f"download_doc_{doc_index}_{file_ext}"
    )

# ============================================
# FONCTIONS DE GÉNÉRATION DU PLANNING
# ============================================

def parse_hm(s):
    h, m = s.split(":")
    return dtime(int(h), int(m))

def build_windows(config):
    matin_start = parse_hm(config["heure_debut_matin"])
    matin_end = parse_hm(config["heure_fin_matin"])
    am_start = parse_hm(config["heure_debut_apres_midi"])
    am_end = parse_hm(config["heure_fin_apres_midi"])
    pause_matin = None
    if config.get("pause_matin_debut") and config.get("pause_matin_fin"):
        pause_matin = (parse_hm(config["pause_matin_debut"]), parse_hm(config["pause_matin_fin"]))
    pause_am = None
    if config.get("pause_am_debut") and config.get("pause_am_fin"):
        pause_am = (parse_hm(config["pause_am_debut"]), parse_hm(config["pause_am_fin"]))

    def split(start, end, pause):
        if pause and pause[0] < end and start < pause[1]:
            segs = []
            if start < pause[0]:
                segs.append((start, pause[0]))
            if pause[1] < end:
                segs.append((pause[1], end))
            return segs if segs else [(start, end)]
        return [(start, end)]

    windows = []
    windows.extend(split(matin_start, matin_end, pause_matin))
    windows.extend(split(am_start, am_end, pause_am))
    return windows

class DayScheduler:
    def __init__(self, start_date, windows):
        self.date = start_date
        self.windows = windows
        self._skip_weekend()
        self.window_idx = 0
        self.cur_time = self.windows[0][0]

    def _skip_weekend(self):
        while self.date.weekday() >= 5:
            self.date += timedelta(days=1)

    def get_slot(self, duration_minutes):
        guard = 0
        while True:
            guard += 1
            if guard > 1000:
                raise RuntimeError("Boucle infinie détectée")
            w_start, w_end = self.windows[self.window_idx]
            if self.cur_time < w_start:
                self.cur_time = w_start
            cur_dt = datetime.combine(self.date, self.cur_time)
            end_dt = cur_dt + timedelta(minutes=duration_minutes)
            w_end_dt = datetime.combine(self.date, w_end)
            if end_dt <= w_end_dt:
                slot_date = self.date
                slot_start = self.cur_time
                self.cur_time = end_dt.time()
                return slot_date.strftime("%Y-%m-%d"), slot_start.strftime("%H:%M"), duration_minutes
            else:
                self.window_idx += 1
                if self.window_idx >= len(self.windows):
                    self.window_idx = 0
                    self.date += timedelta(days=1)
                    self._skip_weekend()
                self.cur_time = self.windows[self.window_idx][0]

    def state(self):
        return (self.date, self.window_idx, self.cur_time)

def generer_groupes(eleves_df, instructeurs_df):
    nb_instr = len(instructeurs_df)
    if nb_instr == 0 or eleves_df.empty:
        return []
    nb_eleves = len(eleves_df)
    par_groupe = nb_eleves // nb_instr
    reste = nb_eleves % nb_instr
    eleves_list = eleves_df["id"].tolist()
    random.shuffle(eleves_list)
    groupes = []
    idx = 0
    for i, instr_row in enumerate(instructeurs_df.itertuples()):
        nb = par_groupe + (1 if i < reste else 0)
        membres = eleves_list[idx:idx+nb]
        idx += nb
        groupes.append({
            "id": i + 1,
            "nom": f"Groupe de {instr_row.prenom} {instr_row.nom}",
            "instructeur_id": instr_row.id,
            "simulateur_id": i + 1,
            "eleves": membres
        })
    return groupes

def generer_runs_groupe_pour_sim(groupe, ds, tous_instructeurs_ids, sim, suivi, rotation_counter):
    seances = []
    eleves = groupe["eleves"]
    instr_id = groupe["instructeur_id"]
    sim_engin = groupe["simulateur_id"]
    autres_instructeurs = [i for i in tous_instructeurs_ids if i != instr_id]
    est_test = sim["est_test"] == 1

    if est_test:
        runs = []
        eleves_ordre = sorted(eleves, key=lambda e: suivi[e]["controleur"])
        for k, eleve in enumerate(eleves_ordre):
            instr_sub = autres_instructeurs[k % len(autres_instructeurs)] if autres_instructeurs else instr_id
            runs.append({"controleur": eleve, "pseudo": None, "instructeur_id": instr_sub, "instructeur_evaluateur_id": instr_id})
    else:
        n = len(eleves)
        runs = []
        if n >= 2:
            offset = rotation_counter % n
            ordre = eleves[offset:] + eleves[:offset]
            for i in range(n):
                runs.append({"controleur": ordre[i], "pseudo": ordre[(i + 1) % n], "instructeur_id": instr_id, "instructeur_evaluateur_id": None})
            rotation_counter += 1

    for run in runs:
        d, t, dur = ds.get_slot(sim["duree"])
        actifs = {run["controleur"]}
        if run["pseudo"] is not None:
            actifs.add(run["pseudo"])
        observateurs = [e for e in eleves if e not in actifs]
        seances.append({
            "date": d, "heure_debut": t, "duree": dur, "type": "simulation",
            "simulation_id": sim["id"], "groupe_id": groupe["local_id"],
            "instructeur_id": run["instructeur_id"], "instructeur_evaluateur_id": run["instructeur_evaluateur_id"],
            "simulateur_id": sim_engin, "controle_eleve_id": run["controleur"], "pseudo_eleve_id": run["pseudo"],
            "observateurs": observateurs, "notes": "Simulation Test" if est_test else ""
        })
        suivi[run["controleur"]]["controleur"] += 1
        if run["pseudo"] is not None:
            suivi[run["pseudo"]]["pseudo"] += 1

    return seances, rotation_counter

def generer_planning_complet(groupes, instructeurs_df, simulations_df, config):
    windows = build_windows(config)
    tous_instr_ids = instructeurs_df["id"].tolist()
    master_ds = DayScheduler(config["_date_debut_obj"], windows)
    toutes_seances = []
    suivis = {g["local_id"]: {e: {"controleur": 0, "pseudo": 0} for e in g["eleves"]} for g in groupes}
    rotation_counters = {g["local_id"]: 0 for g in groupes}

    for _, sim in simulations_df.iterrows():
        d, t, dur = master_ds.get_slot(config["duree_briefing"])
        toutes_seances.append({
            "date": d, "heure_debut": t, "duree": dur, "type": "briefing",
            "simulation_id": sim["id"], "groupe_id": None,
            "instructeur_id": None, "instructeur_evaluateur_id": None, "simulateur_id": None,
            "controle_eleve_id": None, "pseudo_eleve_id": None, "observateurs": [],
            "notes": f"Briefing collectif - {sim['nom']}"
        })
        finish_states = []
        for groupe in groupes:
            group_ds = DayScheduler(master_ds.date, windows)
            group_ds.window_idx = master_ds.window_idx
            group_ds.cur_time = master_ds.cur_time
            seances_g, rotation_counters[groupe["local_id"]] = generer_runs_groupe_pour_sim(
                groupe, group_ds, tous_instr_ids, sim,
                suivis[groupe["local_id"]], rotation_counters[groupe["local_id"]]
            )
            toutes_seances.extend(seances_g)
            finish_states.append(group_ds.state())
        if finish_states:
            master_ds.date, master_ds.window_idx, master_ds.cur_time = max(finish_states)
        d, t, dur = master_ds.get_slot(config["duree_debriefing"])
        toutes_seances.append({
            "date": d, "heure_debut": t, "duree": dur, "type": "debriefing",
            "simulation_id": sim["id"], "groupe_id": None,
            "instructeur_id": None, "instructeur_evaluateur_id": None, "simulateur_id": None,
            "controle_eleve_id": None, "pseudo_eleve_id": None, "observateurs": [],
            "notes": f"Debriefing collectif - {sim['nom']}"
        })

    date_fin = master_ds.date
    sim_dates = [datetime.strptime(s["date"], "%Y-%m-%d").date() for s in toutes_seances if s["type"] == "simulation"]
    if sim_dates:
        date_fin = max(date_fin, max(sim_dates))
    return toutes_seances, date_fin

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def get_avatar(nom, prenom):
    initials = (prenom[0] + nom[0]).upper() if prenom and nom else "E"
    return f"""
    <div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#0d1a2b,#2a5298);
                display:flex;align-items:center;justify-content:center;color:#7affb0;font-size:1.1em;
                font-weight:700;font-family:'JetBrains Mono',monospace;border:1px solid rgba(0,255,100,0.1);">
        {esc(initials)}
    </div>
    """

def render_flight_strip(seance, eleve_id):
    role_text = "Observateur"
    role_class = "strip-role-observer"
    if seance.get("controle_eleve_id") == eleve_id:
        role_text = "Contrôleur"
        role_class = "strip-role-controller"
    elif seance.get("pseudo_eleve_id") == eleve_id:
        role_text = "Pseudopilote"
        role_class = "strip-role-pseudo"

    return f"""
    <div class="flight-strip">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
            <div>
                <span class="strip-callsign">📡 {esc(seance.get('simulation_nom', 'Simulation'))}</span>
                <span style="margin-left:10px;">
                    <span class="{role_class}" style="padding:2px 10px;border-radius:10px;font-size:0.7em;font-weight:600;">{role_text}</span>
                </span>
            </div>
            <div>
                <span class="strip-time">🕐 {esc(seance.get('heure_debut', ''))}</span>
                <span style="margin-left:10px;color:rgba(180,200,220,0.3);font-size:0.75em;">⏱️ {seance.get('duree', 0)}min</span>
            </div>
        </div>
        <div class="strip-info">
            🏷️ {esc(seance.get('groupe_nom', ''))}
            {f" | 👤 {esc(seance.get('instructeur_nom',''))}" if seance.get("instructeur_nom") else ''}
        </div>
    </div>
    """

def _type_label(t):
    return {"briefing": "Briefing", "simulation": "Simulation", "debriefing": "Débriefing"}.get(t, t)

def build_export_dataframe(seances_df, eleves_df=None):
    colonnes = ["Date", "Heure", "Durée (min)", "Type", "Simulation", "Groupe",
                "Instructeur", "Contrôleur", "Pseudo-pilote", "Observateurs", "Notes"]
    if seances_df is None or seances_df.empty:
        return pd.DataFrame(columns=colonnes)

    eleves_map = {}
    if eleves_df is not None and not eleves_df.empty:
        eleves_map = {row["id"]: f"{row['prenom']} {row['nom']}" for _, row in eleves_df.iterrows()}

    def observateurs_label(val):
        try:
            ids = json.loads(val) if val else []
        except Exception:
            ids = []
        if eleves_map:
            return ", ".join(eleves_map.get(i, f"#{i}") for i in ids)
        return ", ".join(str(i) for i in ids)

    export_df = pd.DataFrame({
        "Date": seances_df["date"],
        "Heure": seances_df["heure_debut"],
        "Durée (min)": seances_df["duree"],
        "Type": seances_df["type"].apply(_type_label),
        "Simulation": seances_df["simulation_nom"] if "simulation_nom" in seances_df.columns else "",
        "Groupe": seances_df["groupe_nom"] if "groupe_nom" in seances_df.columns else "",
        "Instructeur": seances_df["instructeur_nom"] if "instructeur_nom" in seances_df.columns else "",
        "Contrôleur": seances_df["controle_eleve_nom"] if "controle_eleve_nom" in seances_df.columns else "",
        "Pseudo-pilote": seances_df["pseudo_eleve_nom"] if "pseudo_eleve_nom" in seances_df.columns else "",
        "Observateurs": seances_df["observateurs"].apply(observateurs_label) if "observateurs" in seances_df.columns else "",
        "Notes": seances_df["notes"] if "notes" in seances_df.columns else "",
    })
    return export_df.sort_values(["Date", "Heure"], na_position="last").reset_index(drop=True)

def to_excel_bytes(df, sheet_name="Planning"):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns):
            max_len = max([len(col)] + [len(str(v)) for v in df[col].tolist()]) + 2 if not df.empty else len(col) + 2
            worksheet.column_dimensions[worksheet.cell(row=1, column=i + 1).column_letter].width = min(max_len, 40)
    return buffer.getvalue()

def render_export_buttons(export_df, filename_prefix, key_prefix):
    st.markdown('<div class="section-title" style="font-size:1em;">📤 Exporter</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    horodatage = date.today().strftime("%Y-%m-%d")
    unique_id = random.randint(1000, 9999)
    
    with col1:
        st.download_button(
            "📥 Exporter en Excel (.xlsx)",
            data=to_excel_bytes(export_df, "Planning"),
            file_name=f"{filename_prefix}_{horodatage}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"export_xlsx_{key_prefix}_{unique_id}"
        )
    with col2:
        st.download_button(
            "📥 Exporter en CSV",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{filename_prefix}_{horodatage}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"export_csv_{key_prefix}_{unique_id}"
        )

# ============================================
# CHANGEMENT DE MOT DE PASSE
# ============================================

def section_mon_mot_de_passe(db, role, user_id):
    st.markdown('<div class="section-title">🔑 Mon Mot de Passe</div>', unsafe_allow_html=True)
    st.caption("Vous pouvez modifier votre mot de passe à tout moment. Il n'est jamais stocké en clair.")

    with st.form("change_password_form"):
        ancien = st.text_input("Mot de passe actuel", type="password")
        nouveau = st.text_input("Nouveau mot de passe", type="password")
        confirmation = st.text_input("Confirmer le nouveau mot de passe", type="password")
        submitted = st.form_submit_button("🔒 Mettre à jour le mot de passe")

        if submitted:
            if role == "eleve":
                mdp_valide = db.verify_password_eleve(user_id, ancien)
            else:
                mdp_valide = db.verify_password_instructeur(user_id, ancien)

            if not mdp_valide:
                st.error("❌ Le mot de passe actuel est incorrect.")
            elif len(nouveau) < 4:
                st.error("❌ Le nouveau mot de passe doit contenir au moins 4 caractères.")
            elif nouveau != confirmation:
                st.error("❌ Les deux mots de passe ne correspondent pas.")
            elif nouveau == ancien:
                st.warning("⚠️ Le nouveau mot de passe doit être différent de l'ancien.")
            else:
                if role == "eleve":
                    db.set_password_eleve(user_id, nouveau)
                else:
                    db.set_password_instructeur(user_id, nouveau)
                st.success("✅ Mot de passe mis à jour avec succès.")

# ============================================
# ÉCRAN DE CONNEXION
# ============================================

def radar_login():
    st.markdown("""
    <div class="radar-container">
        <div class="radar-screen">
            <div style="position:absolute;top:0;left:0;width:100%;height:100%;">
                <div class="radar-ring"></div><div class="radar-ring"></div>
                <div class="radar-ring"></div><div class="radar-ring"></div>
            </div>
            <div class="radar-crosshair" style="position:absolute;top:0;left:0;width:100%;height:100%;"></div>
            <div class="radar-sweep"></div>
            <div class="radar-blips">
                <div class="radar-blip"></div><div class="radar-blip"></div>
                <div class="radar-blip"></div><div class="radar-blip"></div><div class="radar-blip"></div>
            </div>
            <div class="radar-center"></div>
            <div class="radar-title">ATC <span>PLANNER</span></div>
            <div class="radar-label">ICNA · AIAC · PHASE PRATIQUE</div>
        </div>
        <div class="login-card">
            <h2>⬡ SÉLECTIONNEZ VOTRE PROFIL</h2>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    db = Database()

    with col1:
        if st.button("👨‍🎓 ÉLÈVE", use_container_width=True):
            st.session_state["login_role"] = "eleve"
            st.rerun()
    with col2:
        if st.button("👨‍🏫 INSTRUCTEUR", use_container_width=True):
            st.session_state["login_role"] = "instructeur"
            st.rerun()

    role = st.session_state.get("login_role")

    if role == "eleve":
        eleves = db.get_eleves()
        if eleves.empty:
            st.warning("Aucun élève disponible.")
            return
        eleve_options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in eleves.iterrows()}
        selected = st.selectbox("Choisissez votre nom", list(eleve_options.keys()))
        password_input = st.text_input("Mot de passe", type="password", key="login_pwd_eleve")
        if st.button("🎯 Entrer", type="primary", use_container_width=True):
            eleve_id = eleve_options[selected]
            if db.verify_password_eleve(eleve_id, password_input):
                eleve = db.get_eleve_by_id(eleve_id)
                st.session_state["user"] = dict(zip(["id", "nom", "prenom", "email", "groupe_id"], eleve))
                st.session_state["role"] = "eleve"
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect.")

        with st.expander("🔒 Mot de passe oublié ?"):
            st.caption(f"Réinitialiser directement le mot de passe de **{esc(selected)}**")
            if st.button("🔄 Réinitialiser mon mot de passe", key="reset_btn_eleve"):
                new_temp = generate_temp_password()
                db.set_password_eleve(eleve_options[selected], new_temp)
                st.success(f"✅ Nouveau mot de passe temporaire : **{new_temp}**")

    elif role == "instructeur":
        instructeurs = db.get_instructeurs()
        if instructeurs.empty:
            st.warning("Aucun instructeur disponible.")
            return
        instr_options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in instructeurs.iterrows()}
        selected = st.selectbox("Choisissez votre nom", list(instr_options.keys()))
        password_input = st.text_input("Mot de passe", type="password", key="login_pwd_instr")
        if st.button("🎯 Entrer", type="primary", use_container_width=True):
            instr_id = instr_options[selected]
            if db.verify_password_instructeur(instr_id, password_input):
                instr = db.get_instructeur_by_id(instr_id)
                st.session_state["user"] = dict(zip(["id", "nom", "prenom", "email", "actif"], instr))
                st.session_state["role"] = "instructeur"
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect.")

        with st.expander("🔒 Mot de passe oublié ?"):
            autres_instructeurs = {k: v for k, v in instr_options.items() if k != selected}
            if autres_instructeurs:
                st.caption(f"Un **autre** instructeur peut autoriser la réinitialisation")
                autor_selected = st.selectbox("Instructeur autorisant", list(autres_instructeurs.keys()), key="reset_instr_select_instr")
                autor_password = st.text_input("Son mot de passe", type="password", key="reset_instr_pwd_instr")
                if st.button("🔄 Réinitialiser (autorisation instructeur)", key="reset_btn_instr"):
                    if db.verify_password_instructeur(autres_instructeurs[autor_selected], autor_password):
                        new_temp = generate_temp_password()
                        db.set_password_instructeur(instr_options[selected], new_temp)
                        st.success(f"✅ Nouveau mot de passe temporaire : **{new_temp}**")
                    else:
                        st.error("❌ Mot de passe incorrect")

            if db.admin_code_configured():
                st.markdown("---")
                st.caption("🛡️ Code administrateur :")
                admin_code_input = st.text_input("Code administrateur", type="password", key="admin_code_instr")
                if st.button("🔄 Réinitialiser (code admin)", key="reset_admin_btn_instr"):
                    if db.verify_admin_code(admin_code_input):
                        new_temp = generate_temp_password()
                        db.set_password_instructeur(instr_options[selected], new_temp)
                        st.success(f"✅ Nouveau mot de passe temporaire : **{new_temp}**")
                    else:
                        st.error("❌ Code administrateur incorrect.")

    st.markdown('</div></div>', unsafe_allow_html=True)

# ============================================
# EN-TÊTES
# ============================================

def header_eleve(user):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#060a12 0%,#0d1a2b 50%,#162a3f 100%);
                padding:16px 20px;border-radius:12px;margin-bottom:20px;
                border:1px solid rgba(0,255,100,0.04);">
        <div style="display:flex;align-items:center;gap:14px;">
            <div>{get_avatar(user.get('nom',''), user.get('prenom',''))}</div>
            <div>
                <h1 style="font-size:1.3em;font-weight:700;color:#7affb0;font-family:'JetBrains Mono',monospace;
                           margin:0;letter-spacing:0.5px;">
                    📡 {esc(user.get('prenom','Élève'))} {esc(user.get('nom',''))}
                </h1>
                <p style="color:rgba(180,200,220,0.3);font-family:'JetBrains Mono',monospace;font-size:0.75em;
                          margin:0;letter-spacing:0.3px;">
                    Espace Élève · Phase Pratique Aérodrome
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def header_instructeur(user):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#060a12 0%,#0d1a2b 50%,#162a3f 100%);
                padding:16px 20px;border-radius:12px;margin-bottom:20px;
                border:1px solid rgba(255,200,50,0.04);">
        <div style="display:flex;align-items:center;gap:14px;">
            <div>{get_avatar(user.get('nom',''), user.get('prenom',''))}</div>
            <div>
                <h1 style="font-size:1.3em;font-weight:700;color:#ffcc44;font-family:'JetBrains Mono',monospace;
                           margin:0;letter-spacing:0.5px;">
                    📡 {esc(user.get('prenom','Instructeur'))} {esc(user.get('nom',''))}
                </h1>
                <p style="color:rgba(180,200,220,0.3);font-family:'JetBrains Mono',monospace;font-size:0.75em;
                          margin:0;letter-spacing:0.3px;">
                    Espace Instructeur · Phase Pratique Aérodrome
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# SECTIONS ÉLÈVE
# ============================================

def section_cours_eleve(cours):
    st.markdown('<div class="section-title">📚 Cours disponibles</div>', unsafe_allow_html=True)
    if cours.empty:
        st.info("Aucun cours disponible.")
        return
    
    for idx, (_, c) in enumerate(cours.iterrows()):
        with st.expander(f"📄 {c['titre']}", expanded=False):
            st.markdown(f"""
            <div style="color:rgba(180,200,220,0.4);font-size:0.8em;">
                📅 {esc(c['date_upload'])} · <span class="badge-info">{esc(c['type']).upper()}</span>
                {f' · 🏷️ {esc(c["tags"])}' if c.get("tags") else ''}
            </div>
            """, unsafe_allow_html=True)
            if c.get("description"):
                st.write(c["description"])
            render_document_view(c['contenu'], c['type'], c['titre'], doc_index=idx)

def section_scenarios_eleve(scenarios):
    st.markdown('<div class="section-title">🎯 Scénarios de simulation</div>', unsafe_allow_html=True)
    if scenarios.empty:
        st.info("Aucun scénario disponible.")
        return
    
    niveau_badge = {"debutant": "badge-success", "intermediaire": "badge-warning", "avance": "badge-danger"}
    for idx, (_, s) in enumerate(scenarios.iterrows()):
        with st.expander(f"🎯 {s['titre']}", expanded=False):
            st.markdown(f"""
            <div class="scenario-meta">
                <span class="{niveau_badge.get(s['niveau'], 'badge-info')}">{esc(s['niveau']).upper()}</span>
                <span style="margin-left:8px;">⏱️ {s['duree_estimee']} min</span>
                {' <span style="margin-left:8px;">💻 Simulateur requis</span>' if s['simulateur_requis'] else ''}
            </div>
            """, unsafe_allow_html=True)
            if s.get("description"):
                st.write(s["description"])
            if s.get("objectifs"):
                st.write("**Objectifs :**", s["objectifs"])
            if s.get("instructions"):
                st.write("**Instructions :**", s["instructions"])
            if s.get("contenu"):
                render_document_view(s['contenu'], s['type'], s['titre'], doc_index=idx)

def section_td_eleve(tds):
    st.markdown('<div class="section-title">📝 Travaux Dirigés</div>', unsafe_allow_html=True)
    if tds.empty:
        st.info("Aucun TD disponible.")
        return
    
    for idx, (_, td) in enumerate(tds.iterrows()):
        with st.expander(f"📝 {td['titre']}", expanded=False):
            st.markdown(f"""
            <div style="color:rgba(180,200,220,0.4);font-size:0.8em;">
                📅 {esc(td['date_upload'])} · <span class="badge-td">{esc(td['type']).upper()}</span>
                {f' · 🏷️ {esc(td["tags"])}' if td.get("tags") else ''}
            </div>
            """, unsafe_allow_html=True)
            if td.get("description"):
                st.write(td["description"])
            render_document_view(td['contenu'], td['type'], td['titre'], doc_index=idx)

def section_planning_eleve(db, seances, eleve_id, eleve_nom=""):
    st.markdown('<div class="section-title">📅 Mon Planning</div>', unsafe_allow_html=True)
    if seances.empty:
        st.info("Aucune simulation planifiée.")
        return
    for date_val in sorted(seances["date"].unique()):
        st.markdown(f"""
        <div style="color:#7affb0;font-family:'JetBrains Mono',monospace;font-size:0.8em;
                    margin:12px 0 6px 0;border-bottom:1px solid rgba(0,255,100,0.04);padding-bottom:4px;">
            📅 {esc(date_val)}
        </div>
        """, unsafe_allow_html=True)
        jour = seances[seances["date"] == date_val].sort_values("heure_debut")
        for _, s in jour.iterrows():
            st.markdown(render_flight_strip(s, eleve_id), unsafe_allow_html=True)

    st.markdown("---")
    export_df = build_export_dataframe(seances, db.get_eleves())
    prefix = f"mon_planning_{eleve_nom}".strip().replace(" ", "_") or "mon_planning"
    render_export_buttons(export_df, prefix, "planning_eleve")

def section_groupe_eleve(db, eleve_id):
    st.markdown('<div class="section-title">👥 Mon Groupe</div>', unsafe_allow_html=True)
    groupe = db.get_groupe_de_eleve(eleve_id)
    if not groupe:
        st.info("Vous n'êtes pas encore affecté(e) à un groupe.")
        return

    membres = db.get_groupe_eleves(groupe["id"])
    chips = "".join([
        f'<span class="eleve-chip">📌 {esc(m["prenom"])} {esc(m["nom"])}{" · vous" if m["id"] == eleve_id else ""}</span>'
        for _, m in membres.iterrows()
    ])
    instr_nom = groupe.get("instructeur_nom") or "Non assigné"
    sim_id = groupe.get("simulateur_id")
    sim_label = f"Simulateur {sim_id}" if sim_id is not None else "Simulateur non assigné"

    st.markdown(f"""
    <div class="groupe-card">
        <h4>🏷️ {esc(groupe['nom'])}</h4>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
            <span class="instructeur-badge">👤 Instructeur : {esc(instr_nom)}</span>
            <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                        border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                💻 {esc(sim_label)}
            </span>
            <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                        border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                👨‍🎓 {len(membres)} élève(s)
            </span>
        </div>
        <div>{chips if chips else '<span style="color:rgba(180,200,220,0.3);font-size:0.85em;">Aucun élève</span>'}</div>
    </div>
    """, unsafe_allow_html=True)

def section_notes_eleve(notes):
    st.markdown('<div class="section-title">📊 Mes Notes</div>', unsafe_allow_html=True)
    if notes.empty:
        st.info("Aucune note disponible.")
        return
    moyenne = notes["note"].mean()
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:16px;">
        <span style="font-size:2em;font-weight:700;color:#7affb0;">{moyenne:.1f}/20</span>
        <span style="display:block;color:rgba(180,200,220,0.3);font-size:0.75em;">
            Moyenne sur {len(notes)} évaluation(s)
        </span>
    </div>
    """, unsafe_allow_html=True)

    for _, n in notes.iterrows():
        st.markdown(f"""
        <div class="flight-strip" style="border-left-color:#ffcc44;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                <div>
                    <span class="strip-callsign" style="color:#ffcc44;">📊 {esc(n['simulation_nom'])}</span>
                    <span style="margin-left:10px;color:rgba(180,200,220,0.4);font-size:0.75em;">{esc(n['date_note'])}</span>
                </div>
                <div>
                    <span style="font-size:1.1em;font-weight:700;color:#7affb0;">
                        {n['note']:.1f}/20
                    </span>
                    <span style="margin-left:10px;font-size:0.75em;color:rgba(180,200,220,0.3);">{esc(n['appreciation'])}</span>
                </div>
            </div>
            <div class="strip-info">👤 {esc(n['instructeur_nom'])} · 🏷️ {esc(n['grille_nom'])}</div>
        </div>
        """, unsafe_allow_html=True)
        if n.get("commentaires"):
            st.caption(f"💬 {n['commentaires']}")

    if len(notes) > 1:
        fig = px.line(notes.sort_values("date_note"), x="date_note", y="note",
                      title="Évolution des notes", labels={"date_note": "Date", "note": "Note /20"},
                      color_discrete_sequence=["#7affb0"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,20,30,0.3)",
                          font=dict(color="rgba(180,200,220,0.5)", family="JetBrains Mono"),
                          title_font=dict(color="#7affb0", size=14))
        fig.update_xaxes(gridcolor="rgba(0,255,100,0.04)", zeroline=False)
        fig.update_yaxes(gridcolor="rgba(0,255,100,0.04)", zeroline=False)
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# SECTIONS INSTRUCTEUR
# ============================================

def _groupe_name_to_id(db):
    groupes_list = db.get_groupes()
    return {g["nom"]: g["id"] for _, g in groupes_list.iterrows()}

def section_cours_instr(db, instr_id):
    st.markdown('<div class="section-title">📚 Gestion des Cours</div>', unsafe_allow_html=True)

    with st.expander("➕ Ajouter un cours", expanded=False):
        with st.form("add_cours_form"):
            titre = st.text_input("Titre du cours")
            description = st.text_area("Description")
            uploaded_file = st.file_uploader("📎 Importer un fichier", type=["pdf", "docx", "txt", "md", "pptx", "xlsx"])
            col1, col2 = st.columns(2)
            with col1:
                type_cours = st.selectbox("Type", ["document", "pdf", "video", "lien"])
            with col2:
                if uploaded_file:
                    st.success(f"✅ {uploaded_file.name} ({uploaded_file.size // 1024} KB)")
                    contenu = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                else:
                    contenu = st.text_input("URL ou contenu (si pas de fichier)")
            tags = st.text_input("Tags (séparés par des virgules)")
            g_map = _groupe_name_to_id(db)
            groupe_cible = st.selectbox("Groupe cible", ["Tous"] + list(g_map.keys()))
            if st.form_submit_button("➕ Ajouter"):
                if titre and (contenu or uploaded_file):
                    db.add_cours({
                        "titre": titre, "description": description, "type": type_cours, "contenu": contenu,
                        "date_upload": date.today().strftime("%Y-%m-%d"), "instructeur_id": instr_id,
                        "groupe_cible_id": None if groupe_cible == "Tous" else g_map[groupe_cible],
                        "tags": tags
                    })
                    st.success("✅ Cours ajouté")
                    st.rerun()
                else:
                    st.error("Titre et contenu requis.")

    cours_df = db.get_cours()
    for idx, (_, c) in enumerate(cours_df.iterrows()):
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.expander(f"📄 {c['titre']}", expanded=False):
                st.markdown(f"""
                <div style="color:rgba(180,200,220,0.4);font-size:0.8em;">
                    📅 {esc(c['date_upload'])} · <span class="badge-info">{esc(c['type']).upper()}</span>
                    {f' · 🏷️ {esc(c["tags"])}' if c.get("tags") else ''}
                </div>
                """, unsafe_allow_html=True)
                if c.get("description"):
                    st.write(c["description"])
                render_document_view(c['contenu'], c['type'], c['titre'], doc_index=idx)
        with col2:
            if st.button("🗑️ Supprimer", key=f"del_cours_{c['id']}", use_container_width=True):
                db.delete_cours(c["id"])
                st.rerun()

def section_scenarios_instr(db, instr_id):
    st.markdown('<div class="section-title">🎯 Gestion des Scénarios</div>', unsafe_allow_html=True)

    with st.expander("➕ Ajouter un scénario", expanded=False):
        with st.form("add_scenario_form"):
            titre = st.text_input("Titre du scénario")
            description = st.text_area("Description")
            objectifs = st.text_area("Objectifs pédagogiques")
            duree = st.number_input("Durée estimée (minutes)", min_value=5, value=45)
            niveau = st.selectbox("Niveau", ["debutant", "intermediaire", "avance"])
            sim_requis = st.checkbox("Simulateur requis")
            instructions = st.text_area("Instructions")
            uploaded_file = st.file_uploader("📎 Fichier joint", type=["pdf", "docx", "txt", "md", "pptx", "xlsx"], key="upload_scenario")
            col1, col2 = st.columns(2)
            with col1:
                type_scenario = st.selectbox("Type de fichier", ["document", "pdf", "video", "lien"])
            with col2:
                if uploaded_file:
                    contenu = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                else:
                    contenu = st.text_input("URL ou contenu")
            tags = st.text_input("Tags")
            g_map = _groupe_name_to_id(db)
            groupe_cible = st.selectbox("Groupe cible", ["Tous"] + list(g_map.keys()))
            if st.form_submit_button("➕ Ajouter"):
                if titre:
                    db.add_scenario({
                        "titre": titre, "description": description, "objectifs": objectifs,
                        "duree_estimee": duree, "niveau": niveau, "simulateur_requis": sim_requis,
                        "instructions": instructions, "contenu": contenu, "type": type_scenario,
                        "date_creation": date.today().strftime("%Y-%m-%d"), "instructeur_id": instr_id,
                        "groupe_cible_id": None if groupe_cible == "Tous" else g_map[groupe_cible],
                        "tags": tags
                    })
                    st.success("✅ Scénario ajouté")
                    st.rerun()
                else:
                    st.error("Le titre est requis.")

    scenarios_df = db.get_scenarios()
    niveau_badge = {"debutant": "badge-success", "intermediaire": "badge-warning", "avance": "badge-danger"}
    for idx, (_, s) in enumerate(scenarios_df.iterrows()):
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.expander(f"🎯 {s['titre']}", expanded=False):
                st.markdown(f"""
                <div class="scenario-meta">
                    <span class="{niveau_badge.get(s['niveau'],'badge-info')}">{esc(s['niveau']).upper()}</span>
                    <span style="margin-left:8px;">⏱️ {s['duree_estimee']} min</span>
                </div>
                """, unsafe_allow_html=True)
                if s.get("description"):
                    st.write(s["description"])
                if s.get("instructions"):
                    st.write("**Instructions :**", s["instructions"])
                if s.get("contenu"):
                    render_document_view(s['contenu'], s['type'], s['titre'], doc_index=idx)
        with col2:
            if st.button("🗑️ Supprimer", key=f"del_scenario_{s['id']}", use_container_width=True):
                db.delete_scenario(s["id"])
                st.rerun()

def section_td_instr(db, instr_id):
    st.markdown('<div class="section-title">📝 Gestion des TD</div>', unsafe_allow_html=True)

    with st.expander("➕ Ajouter un TD", expanded=False):
        with st.form("add_td_form"):
            titre = st.text_input("Titre du TD")
            description = st.text_area("Description")
            uploaded_file = st.file_uploader("📎 Importer un fichier", type=["pdf", "docx", "txt", "md", "pptx", "xlsx"], key="upload_td")
            col1, col2 = st.columns(2)
            with col1:
                type_td = st.selectbox("Type", ["exercice", "corrige", "serie", "devoir"])
            with col2:
                if uploaded_file:
                    contenu = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                else:
                    contenu = st.text_input("URL ou contenu")
            tags = st.text_input("Tags")
            g_map = _groupe_name_to_id(db)
            groupe_cible = st.selectbox("Groupe cible", ["Tous"] + list(g_map.keys()))
            if st.form_submit_button("➕ Ajouter"):
                if titre and (contenu or uploaded_file):
                    db.add_td({
                        "titre": titre, "description": description, "type": type_td, "contenu": contenu,
                        "date_upload": date.today().strftime("%Y-%m-%d"), "instructeur_id": instr_id,
                        "groupe_cible_id": None if groupe_cible == "Tous" else g_map[groupe_cible],
                        "tags": tags
                    })
                    st.success("✅ TD ajouté")
                    st.rerun()
                else:
                    st.error("Titre et contenu requis.")

    tds_df = db.get_td()
    for idx, (_, td) in enumerate(tds_df.iterrows()):
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.expander(f"📝 {td['titre']}", expanded=False):
                st.markdown(f"""
                <div style="color:rgba(180,200,220,0.4);font-size:0.8em;">
                    📅 {esc(td['date_upload'])} · <span class="badge-td">{esc(td['type']).upper()}</span>
                    {f' · 🏷️ {esc(td["tags"])}' if td.get("tags") else ''}
                </div>
                """, unsafe_allow_html=True)
                if td.get("description"):
                    st.write(td["description"])
                render_document_view(td['contenu'], td['type'], td['titre'], doc_index=idx)
        with col2:
            if st.button("🗑️ Supprimer", key=f"del_td_{td['id']}", use_container_width=True):
                db.delete_td(td["id"])
                st.rerun()

def section_evals_instr(db, instr_id):
    st.markdown('<div class="section-title">📊 Évaluations</div>', unsafe_allow_html=True)

    with st.expander("📋 Gérer les grilles d'évaluation", expanded=False):
        with st.form("add_grille_form"):
            nom = st.text_input("Nom de la grille")
            description = st.text_area("Description")
            criteres = st.text_area("Critères (un par ligne)", "Phraséologie\nAnticipation\nGestion du trafic\nCommunication\nRéactivité")
            bareme = st.text_area("Barème (un par ligne)", "4\n4\n4\n4\n4")
            if st.form_submit_button("➕ Créer"):
                criteres_list = [c.strip() for c in criteres.split("\n") if c.strip()]
                bareme_list_raw = [b.strip() for b in bareme.split("\n") if b.strip()]
                try:
                    bareme_list = [float(b) for b in bareme_list_raw]
                except ValueError:
                    st.error("❌ Le barème doit contenir uniquement des nombres.")
                    bareme_list = None
                if bareme_list is not None:
                    if len(criteres_list) == len(bareme_list) and nom:
                        db.add_grille({
                            "nom": nom, "description": description,
                            "criteres": json.dumps(criteres_list), "bareme": json.dumps(bareme_list),
                            "instructeur_id": instr_id, "date_creation": date.today().strftime("%Y-%m-%d")
                        })
                        st.success("✅ Grille créée")
                        st.rerun()
                    else:
                        st.error("❌ Le nombre de critères doit correspondre au nombre de barèmes")

    st.markdown('<div style="margin-top:12px;color:#7affb0;font-size:0.9em;">✏️ Noter un élève</div>', unsafe_allow_html=True)
    eleves_df = db.get_eleves()
    if eleves_df.empty:
        st.info("Aucun élève inscrit.")
        return

    eleve_labels = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in eleves_df.iterrows()}
    eleve_selected = st.selectbox("Choisir un élève", list(eleve_labels.keys()))
    eleve_id = eleve_labels[eleve_selected]

    grilles_df = db.get_grilles()
    if grilles_df.empty:
        st.warning("Créez d'abord une grille d'évaluation.")
    else:
        grille_selected = st.selectbox("Grille d'évaluation", grilles_df["nom"].tolist())
        grille_row = grilles_df[grilles_df["nom"] == grille_selected].iloc[0]
        grille_id = grille_row["id"]
        criteres = json.loads(grille_row["criteres"])
        bareme = json.loads(grille_row["bareme"])

        simulations_df = db.get_simulations()
        sim_name_to_id = {row["nom"]: row["id"] for _, row in simulations_df.iterrows()}

        with st.form("note_form"):
            simulation = st.selectbox("Simulation", list(sim_name_to_id.keys()))
            st.markdown("**Critères d'évaluation**")
            scores = []
            for c, b in zip(criteres, bareme):
                score = st.slider(f"{c} (max {b})", 0.0, float(b), float(b) / 2, 0.5)
                scores.append(score)
            appreciation = st.selectbox("Appréciation", ["Excellent", "Très bien", "Bien", "Passable", "Insuffisant"])
            commentaires = st.text_area("Commentaires")
            if st.form_submit_button("📊 Enregistrer l'évaluation"):
                note_total = sum(scores)
                db.add_note({
                    "eleve_id": eleve_id, "instructeur_id": instr_id, "grille_id": grille_id,
                    "simulation_id": sim_name_to_id[simulation],
                    "seance_id": None, "date_note": date.today().strftime("%Y-%m-%d"),
                    "note": note_total, "appreciation": appreciation,
                    "scores_criteres": json.dumps(scores), "commentaires": commentaires
                })
                st.success(f"✅ Note enregistrée : {note_total:.1f}/20")
                st.rerun()

    notes = db.get_notes_eleve(eleve_id)
    if not notes.empty:
        st.markdown(f"📋 **Historique des notes — {eleve_selected}**")
        for _, n in notes.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"📅 {n['date_note']} - {n['simulation_nom']}")
            with col2:
                st.write(f"Note: {n['note']:.1f}/20 - {n['appreciation']}")
            with col3:
                if st.button("🗑️", key=f"del_note_{n['id']}"):
                    db.delete_note(n['id'])
                    st.rerun()
        if st.button("🗑️ Supprimer toutes les notes", key=f"del_all_notes_{eleve_id}", use_container_width=True):
            db.delete_notes_eleve(eleve_id)
            st.rerun()

def section_planning_instr(db):
    st.markdown('<div class="section-title">📅 Planning Général</div>', unsafe_allow_html=True)
    seances = db.get_seances()
    if seances.empty:
        st.info("Aucun planning généré.")
        return

    groupes_df = db.get_groupes()
    groupe_options = ["Tous les groupes"] + (groupes_df["nom"].tolist() if not groupes_df.empty else [])
    type_options = {"Tous les types": None, "Briefing": "briefing", "Simulation": "simulation", "Débriefing": "debriefing"}

    col1, col2 = st.columns(2)
    with col1:
        groupe_choisi = st.selectbox("Filtrer par groupe", groupe_options)
    with col2:
        type_label_choisi = st.selectbox("Filtrer par type", list(type_options.keys()))

    filtered = seances.copy()
    if groupe_choisi != "Tous les groupes":
        filtered = filtered[filtered["groupe_nom"] == groupe_choisi]
    if type_options[type_label_choisi] is not None:
        filtered = filtered[filtered["type"] == type_options[type_label_choisi]]

    st.caption(f"{len(filtered)} séance(s) affichée(s) sur {len(seances)} au total.")

    eleves_df = db.get_eleves()
    export_df = build_export_dataframe(filtered, eleves_df)
    st.dataframe(export_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    render_export_buttons(export_df, "planning_general_atc", "planning_instr")

def section_groupes_instr(db):
    st.markdown('<div class="section-title">🏷️ Groupes</div>', unsafe_allow_html=True)
    groupes = db.get_groupes()
    if groupes.empty:
        st.info("Aucun groupe généré.")
        return
    for _, g in groupes.iterrows():
        membres = db.get_groupe_eleves(g["id"])
        chips = "".join([f'<span class="eleve-chip">📌 {esc(m["prenom"])} {esc(m["nom"])}</span>' for _, m in membres.iterrows()])
        st.markdown(f"""
        <div class="groupe-card">
            <h4>🏷️ {esc(g['nom'])}</h4>
            <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
                <span class="instructeur-badge">👤 Instructeur : {esc(g['instructeur_nom'])}</span>
                <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                            border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                    💻 Simulateur {g['simulateur_id']}
                </span>
                <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                            border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                    👨‍🎓 {len(membres)} élève(s)
                </span>
            </div>
            <div>{chips if chips else '<span style="color:rgba(180,200,220,0.3);">Aucun élève</span>'}</div>
        </div>
        """, unsafe_allow_html=True)

def page_generateur():
    st.markdown('<div class="section-title">🚀 Générateur de Planning</div>', unsafe_allow_html=True)
    db = Database()
    config = db.get_config()
    eleves = db.get_eleves()
    instructeurs = db.get_instructeurs()

    if not config:
        st.warning("⚠️ Configurez d'abord l'application")
        return
    if eleves.empty:
        st.warning("⚠️ Ajoutez des élèves")
        return
    if instructeurs.empty:
        st.warning("⚠️ Ajoutez des instructeurs")
        return
    if len(instructeurs) < 2:
        st.warning("⚠️ Il faut au moins 2 instructeurs")
        return

    date_debut = config['date_debut']
    date_fin_souhaitee = config['date_fin_souhaitee']
    
    st.info(f"👨‍🎓 {len(eleves)} élèves | 👨‍🏫 {len(instructeurs)} instructeurs | 📅 {date_debut} → {date_fin_souhaitee}")

    if st.button("🚀 Générer le planning", type="primary"):
        with st.spinner("🔄 Génération..."):
            try:
                db.reset_planning()
                groupes_raw = generer_groupes(eleves, instructeurs)
                for i, g in enumerate(groupes_raw):
                    g["local_id"] = i + 1
                simulations = db.get_simulations()
                config_run = dict(config)
                config_run["_date_debut_obj"] = datetime.strptime(config["date_debut"], "%Y-%m-%d").date()
                seances, date_fin_reelle = generer_planning_complet(groupes_raw, instructeurs, simulations, config_run)
                groupes_to_save = [{"id": g["local_id"], "nom": g["nom"], "instructeur_id": g["instructeur_id"],
                                     "simulateur_id": g["simulateur_id"], "eleves": g["eleves"]} for g in groupes_raw]
                id_map = db.save_groupes(groupes_to_save)
                for s in seances:
                    if s["groupe_id"] is not None:
                        s["groupe_id"] = id_map.get(s["groupe_id"], s["groupe_id"])
                db.save_seances(seances)
                
                date_fin_souhaitee_obj = datetime.strptime(config["date_fin_souhaitee"], "%Y-%m-%d").date()
                nb_sim = len([s for s in seances if s["type"] == "simulation"])
                
                if date_fin_reelle <= date_fin_souhaitee_obj:
                    st.success(f"✅ Planning généré ! Fin: {date_fin_reelle.strftime('%d/%m/%Y')}")
                    st.success(f"✅ {nb_sim} simulations planifiées")
                    st.balloons()
                else:
                    jours_depassement = (date_fin_reelle - date_fin_souhaitee_obj).days
                    st.warning(f"⚠️ Dépassement de {jours_depassement} jour(s) !")
                    st.warning(f"📅 Fin réelle : {date_fin_reelle.strftime('%d/%m/%Y')} (vs {date_fin_souhaitee_obj.strftime('%d/%m/%Y')})")
                    st.success(f"✅ {nb_sim} simulations planifiées")
                    
                    st.markdown("### 💡 Solutions possibles :")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**🕐 Option 1 : Ajuster les horaires**")
                        st.markdown("- Réduire la durée des briefings")
                        st.markdown("- Réduire la durée des débriefings")
                        st.markdown("- Réduire la durée des simulations")
                        if st.button("⚙️ Aller à la configuration", key="go_config"):
                            st.session_state["page"] = "Config"
                            st.rerun()
                    with col2:
                        st.markdown("**📅 Option 2 : Étendre la date de fin**")
                        nouvelle_date = date_fin_souhaitee_obj + timedelta(days=jours_depassement + 1)
                        st.markdown(f"- Proposer : **{nouvelle_date.strftime('%d/%m/%Y')}**")
                        if st.button("📅 Proposer cette date", key="extend_date"):
                            config_update = config.copy()
                            config_update["date_fin_souhaitee"] = nouvelle_date.strftime("%Y-%m-%d")
                            db.save_config(config_update)
                            st.success(f"✅ Date de fin étendue au {nouvelle_date.strftime('%d/%m/%Y')}")
                            st.rerun()
                    st.balloons()
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")

# ============================================
# MAIN
# ============================================

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["login_role"] = None

    if not st.session_state["logged_in"]:
        radar_login()
        return

    role = st.session_state.get("role")
    user = st.session_state.get("user", {})
    db = Database()

    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:10px 0;border-bottom:1px solid rgba(0,255,100,0.04);margin-bottom:16px;">
            <div style="font-size:1.6em;font-weight:700;color:#7affb0;letter-spacing:2px;">📡 ATC</div>
            <div style="font-size:0.6em;color:rgba(180,200,220,0.2);letter-spacing:2px;">ICNA · AIAC</div>
        </div>
        """, unsafe_allow_html=True)

        if role == "eleve":
            pages = {"👥 Mon Groupe": "Groupe", "📚 Cours": "Cours", "🎯 Scénarios": "Scenarios", "📝 TD": "TD",
                    "📅 Mon Planning": "Planning", "📊 Mes Notes": "Notes", "🔑 Mon Mot de Passe": "MotDePasse"}
        else:
            pages = {"👥 Personnes": "Personnes", "⚙️ Configuration": "Config", "🚀 Générateur": "Generateur",
                    "📅 Planning": "Planning_Instr",
                    "📚 Cours": "Cours_Instr", "🎯 Scénarios": "Scenarios_Instr", "📝 TD": "TD_Instr",
                    "📊 Évaluations": "Evals", "🏷️ Groupes": "Groupes_Instr", "🔑 Mon Mot de Passe": "MotDePasse_Instr"}
        selection = st.radio("Navigation", list(pages.keys()))
        page = pages[selection]

        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user"] = {}
            st.rerun()

    if role == "eleve":
        eleve_id = user.get("id")
        header_eleve(user)
        if page == "Groupe":
            section_groupe_eleve(db, eleve_id)
        elif page == "Cours":
            section_cours_eleve(db.get_cours(eleve_id))
        elif page == "Scenarios":
            section_scenarios_eleve(db.get_scenarios(eleve_id))
        elif page == "TD":
            section_td_eleve(db.get_td(eleve_id))
        elif page == "Planning":
            section_planning_eleve(db, db.get_seances_eleve(eleve_id), eleve_id, f"{user.get('prenom','')} {user.get('nom','')}")
        elif page == "Notes":
            section_notes_eleve(db.get_notes_eleve(eleve_id))
        elif page == "MotDePasse":
            section_mon_mot_de_passe(db, "eleve", eleve_id)
        return

    # ---- Instructeur ----
    instr_id = user.get("id")

    if page == "Personnes":
        header_instructeur(user)
        st.markdown('<div class="section-title">👥 Gestion des Personnes</div>', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["👨‍🎓 Élèves", "👨‍🏫 Instructeurs"])
        with tab1:
            if st.session_state.get("temp_pwd_eleve"):
                st.info(f"🔑 Compte créé. Mot de passe temporaire : **{st.session_state['temp_pwd_eleve']}**")
                del st.session_state["temp_pwd_eleve"]
            if st.session_state.get("reset_pwd_eleve"):
                st.info(f"🔄 Mot de passe réinitialisé : **{st.session_state['reset_pwd_eleve']}**")
                del st.session_state["reset_pwd_eleve"]
            with st.form("add_eleve_form"):
                col1, col2 = st.columns(2)
                with col1:
                    nom = st.text_input("Nom")
                with col2:
                    prenom = st.text_input("Prénom")
                mot_de_passe_initial = st.text_input(
                    "Mot de passe initial (laisser vide pour génération automatique)",
                    type="password", key="pwd_new_eleve"
                )
                if st.form_submit_button("➕ Ajouter"):
                    if nom and prenom:
                        new_id, temp_pwd = db.add_eleve(nom, prenom, password=mot_de_passe_initial or None)
                        if temp_pwd:
                            st.session_state["temp_pwd_eleve"] = temp_pwd
                        st.success("✅ Élève ajouté")
                        st.rerun()
            eleves = db.get_eleves()
            if not eleves.empty:
                st.dataframe(eleves[["nom", "prenom"]], use_container_width=True, hide_index=True)
                for _, row in eleves.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"👤 {row['prenom']} {row['nom']}")
                    with col2:
                        if st.button("🔄", key=f"reset_eleve_{row['id']}"):
                            new_temp = generate_temp_password()
                            db.set_password_eleve(row['id'], new_temp)
                            st.session_state["reset_pwd_eleve"] = new_temp
                            st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"del_eleve_{row['id']}"):
                            db.delete_eleve(row['id'])
                            st.rerun()
        with tab2:
            if st.session_state.get("temp_pwd_instr"):
                st.info(f"🔑 Compte créé. Mot de passe temporaire : **{st.session_state['temp_pwd_instr']}**")
                del st.session_state["temp_pwd_instr"]
            if st.session_state.get("reset_pwd_instr"):
                st.info(f"🔄 Mot de passe réinitialisé : **{st.session_state['reset_pwd_instr']}**")
                del st.session_state["reset_pwd_instr"]
            with st.form("add_instructeur_form"):
                col1, col2 = st.columns(2)
                with col1:
                    nom = st.text_input("Nom")
                with col2:
                    prenom = st.text_input("Prénom")
                mot_de_passe_initial = st.text_input(
                    "Mot de passe initial (laisser vide pour génération automatique)",
                    type="password", key="pwd_new_instr"
                )
                if st.form_submit_button("➕ Ajouter"):
                    if nom and prenom:
                        new_id, temp_pwd = db.add_instructeur(nom, prenom, password=mot_de_passe_initial or None)
                        if temp_pwd:
                            st.session_state["temp_pwd_instr"] = temp_pwd
                        st.success("✅ Instructeur ajouté")
                        st.rerun()
            instrs = db.get_instructeurs()
            if not instrs.empty:
                st.dataframe(instrs[["nom", "prenom"]], use_container_width=True, hide_index=True)
                for _, row in instrs.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"👤 {row['prenom']} {row['nom']}")
                    with col2:
                        if st.button("🔄", key=f"reset_instr_{row['id']}"):
                            new_temp = generate_temp_password()
                            db.set_password_instructeur(row['id'], new_temp)
                            st.session_state["reset_pwd_instr"] = new_temp
                            st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"del_instr_{row['id']}"):
                            db.delete_instructeur(row['id'])
                            st.rerun()
        st.markdown("---")
        with st.expander("⚠️ Zone dangereuse"):
            confirm = st.checkbox("Je comprends que cette action est irréversible")
            if st.button("🗑️ Tout réinitialiser", disabled=not confirm):
                db.delete_all_data()
                st.success("✅ Toutes les données ont été supprimées")
                st.rerun()

    elif page == "Config":
        header_instructeur(user)
        st.markdown('<div class="section-title">⚙️ Configuration</div>', unsafe_allow_html=True)
        with st.form("config_form"):
            col1, col2 = st.columns(2)
            with col1:
                date_debut = st.date_input("Date de début", value=date.today())
            with col2:
                date_fin = st.date_input("Date de fin souhaitée", value=date.today() + timedelta(days=30))
            st.markdown("**Horaires**")
            col1, col2 = st.columns(2)
            with col1:
                hd_matin = st.text_input("Début matin", value="09:00")
                hf_matin = st.text_input("Fin matin", value="12:15")
            with col2:
                hd_am = st.text_input("Début après-midi", value="14:15")
                hf_am = st.text_input("Fin après-midi", value="17:30")
            st.markdown("**Pauses**")
            col1, col2 = st.columns(2)
            with col1:
                pm_debut = st.text_input("Pause matin début", value="10:30")
                pm_fin = st.text_input("Pause matin fin", value="10:45")
            with col2:
                pam_debut = st.text_input("Pause après-midi début", value="15:45")
                pam_fin = st.text_input("Pause après-midi fin", value="16:00")
            col1, col2 = st.columns(2)
            with col1:
                duree_brief = st.number_input("Briefing collectif (min)", min_value=0, value=20)
            with col2:
                duree_debrief = st.number_input("Debriefing collectif (min)", min_value=0, value=30)
            st.markdown("**Durée des simulations**")
            simulations = db.get_simulations()
            durees_input = {}
            cols = st.columns(4)
            for i, (_, sim) in enumerate(simulations.iterrows()):
                with cols[i % 4]:
                    durees_input[sim["id"]] = st.number_input(sim["nom"], min_value=0, value=int(sim["duree"]), key=f"sim_{sim['id']}")
            if st.form_submit_button("💾 Sauvegarder"):
                eleves_count = len(db.get_eleves())
                instr_count = len(db.get_instructeurs())
                config_data = {
                    "date_debut": date_debut.strftime("%Y-%m-%d"), "date_fin_souhaitee": date_fin.strftime("%Y-%m-%d"),
                    "nb_eleves": eleves_count, "nb_instructeurs": instr_count, "nb_simulateurs": instr_count,
                    "duree_briefing": duree_brief, "duree_debriefing": duree_debrief,
                    "heure_debut_matin": hd_matin, "heure_fin_matin": hf_matin,
                    "heure_debut_apres_midi": hd_am, "heure_fin_apres_midi": hf_am,
                    "pause_matin_debut": pm_debut, "pause_matin_fin": pm_fin,
                    "pause_am_debut": pam_debut, "pause_am_fin": pam_fin
                }
                db.save_config(config_data)
                for sim_id, duree in durees_input.items():
                    db.update_simulation_duree(sim_id, duree)
                st.success("✅ Configuration sauvegardée")

    elif page == "Generateur":
        header_instructeur(user)
        page_generateur()
    elif page == "Planning_Instr":
        header_instructeur(user)
        section_planning_instr(db)
    elif page == "Cours_Instr":
        header_instructeur(user)
        section_cours_instr(db, instr_id)
    elif page == "Scenarios_Instr":
        header_instructeur(user)
        section_scenarios_instr(db, instr_id)
    elif page == "TD_Instr":
        header_instructeur(user)
        section_td_instr(db, instr_id)
    elif page == "Evals":
        header_instructeur(user)
        section_evals_instr(db, instr_id)
    elif page == "Groupes_Instr":
        header_instructeur(user)
        section_groupes_instr(db)
    elif page == "MotDePasse_Instr":
        header_instructeur(user)
        section_mon_mot_de_passe(db, "instructeur", instr_id)

if __name__ == "__main__":
    main()
