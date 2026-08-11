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
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# ============================================
# CONFIGURATION DES PHASES PRATIQUES ICNA
# ============================================

PHASES_ICNA = {
    "AERODROME": {
        "id": "AER",
        "nom": "Aérodrome",
        "nom_en": "Aerodrome",
        "nom_ar": "المطار",
        "semestre": "S1/S2",
        "simulations": 8,
        "duree_simulation": 65,
        "couleur": "#2a7a4a",
        "niveau": "1ère année",
        "promotion": "P1"
    },
    "APPROCHE_NON_RADAR": {
        "id": "ANR",
        "nom": "Approche Non Radar",
        "nom_en": "Non-Radar Approach",
        "nom_ar": "المقاربة غير الرادارية",
        "semestre": "S3",
        "simulations": 8,
        "duree_simulation": 70,
        "couleur": "#4444cc",
        "niveau": "2ème année",
        "promotion": "P2"
    },
    "APPROCHE_RADAR": {
        "id": "ARD",
        "nom": "Approche Radar",
        "nom_en": "Radar Approach",
        "nom_ar": "المقاربة الرادارية",
        "semestre": "S4",
        "simulations": 8,
        "duree_simulation": 75,
        "couleur": "#cc8844",
        "niveau": "2ème année",
        "promotion": "P2"
    },
    "ENROUTE_NON_RADAR": {
        "id": "ENR",
        "nom": "En-route Non Radar",
        "nom_en": "Non-Radar En-route",
        "nom_ar": "الطريق غير الراداري",
        "semestre": "S4/S5",
        "simulations": 8,
        "duree_simulation": 80,
        "couleur": "#cc4444",
        "niveau": "2ème/3ème année",
        "promotion": "P2/P3"
    },
    "ENROUTE_RADAR": {
        "id": "ERR",
        "nom": "En-route Radar",
        "nom_en": "Radar En-route",
        "nom_ar": "الطريق الراداري",
        "semestre": "S5/S6",
        "simulations": 8,
        "duree_simulation": 85,
        "couleur": "#8844cc",
        "niveau": "3ème année",
        "promotion": "P3"
    }
}

# ============================================
# CONFIGURATION DES PROMOTIONS ET ÉLÈVES
# ============================================

PROMOTIONS = {
    "P1": {
        "nom": "1ère Année",
        "nom_en": "1st Year",
        "nom_ar": "السنة الأولى",
        "phases": ["AERODROME"],
        "eleves": [
            ("KOUBAA", "AYOUB"), ("BAMIDA", "AYMANE"), ("CHADDANI", "MOHAMED")
        ]
    },
    "P2": {
        "nom": "2ème Année",
        "nom_en": "2nd Year",
        "nom_ar": "السنة الثانية",
        "phases": ["APPROCHE_NON_RADAR", "APPROCHE_RADAR", "ENROUTE_NON_RADAR"],
        "eleves": [
            ("KHOULANE", "ILYAS"), ("AKNOUZE", "RACHID"), ("MIFDAL", "IMANE")
        ]
    },
    "P3": {
        "nom": "3ème Année",
        "nom_en": "3rd Year",
        "nom_ar": "السنة الثالثة",
        "phases": ["ENROUTE_NON_RADAR", "ENROUTE_RADAR"],
        "eleves": [
            ("KOUMI", "KHADIJA"), ("GUENNOUN", "CHAIMAE"), ("ICHOU", "ABDELLATIF")
        ]
    }
}

# ============================================
# INSTRUCTEURS PAR PHASE
# ============================================

INSTRUCTEURS_PAR_PHASE = {
    "AERODROME": {
        "instructeurs": [
            {"nom": "RIFAI", "prenom": "Mr"},
            {"nom": "TAHERI", "prenom": "Mr"}
        ]
    },
    "APPROCHE_NON_RADAR": {
        "instructeurs": [
            {"nom": "JBARA", "prenom": "Mr"},
            {"nom": "ELALAOUI", "prenom": "Mr"}
        ]
    },
    "APPROCHE_RADAR": {
        "instructeurs": [
            {"nom": "BENNANI", "prenom": "Mr"},
            {"nom": "FASSI", "prenom": "Mr"}
        ]
    },
    "ENROUTE_NON_RADAR": {
        "instructeurs": [
            {"nom": "CHERKAOUI", "prenom": "Mr"},
            {"nom": "OULAD", "prenom": "Mr"}
        ]
    },
    "ENROUTE_RADAR": {
        "instructeurs": [
            {"nom": "NAJI", "prenom": "Mr"},
            {"nom": "SEKKAL", "prenom": "Mr"}
        ]
    }
}

# ============================================
# SIMULATEURS - 7 POSTES
# ============================================

SIMULATEURS_ICNA = {
    1: {"nom": "Simulateur AER-1", "type": "AERODROME", "dedie": True, 
        "phases_autorisees": ["AERODROME"]},
    2: {"nom": "Simulateur AER-2", "type": "AERODROME", "dedie": True, 
        "phases_autorisees": ["AERODROME"]},
    3: {"nom": "Simulateur ANR-1", "type": "APPROCHE_NON_RADAR", "dedie": True, 
        "phases_autorisees": ["APPROCHE_NON_RADAR"]},
    4: {"nom": "Simulateur ANR-2", "type": "APPROCHE_NON_RADAR", "dedie": True, 
        "phases_autorisees": ["APPROCHE_NON_RADAR"]},
    5: {"nom": "Simulateur MIXTE-1", "type": "MIXTE", "dedie": False, 
        "phases_autorisees": ["APPROCHE_NON_RADAR", "APPROCHE_RADAR", "ENROUTE_NON_RADAR", "ENROUTE_RADAR"]},
    6: {"nom": "Simulateur MIXTE-2", "type": "MIXTE", "dedie": False,
        "phases_autorisees": ["APPROCHE_NON_RADAR", "APPROCHE_RADAR", "ENROUTE_NON_RADAR", "ENROUTE_RADAR"]},
    7: {"nom": "Simulateur MIXTE-3", "type": "MIXTE", "dedie": False,
        "phases_autorisees": ["ENROUTE_NON_RADAR", "ENROUTE_RADAR"]}
}

# ============================================
# FONCTIONS DE DÉTECTION DES SIMULATEURS
# ============================================

def get_type_simulateur(simulateur_id):
    """Retourne le type d'un simulateur : DEDIE ou PARTAGE."""
    sim_info = SIMULATEURS_ICNA.get(simulateur_id)
    if not sim_info:
        return "INCONNU"
    
    if sim_info.get("dedie", False):
        return "DEDIE"
    else:
        return "PARTAGE"

def get_phases_simulateur(simulateur_id):
    """Retourne la liste des phases autorisées pour un simulateur."""
    sim_info = SIMULATEURS_ICNA.get(simulateur_id, {})
    return sim_info.get("phases_autorisees", [])

def generer_matrice_sharing_automatique():
    """Génère automatiquement la matrice de partage en fonction de la configuration."""
    matrice = {}
    
    for phase_id in PHASES_ICNA:
        sim_dedies = []
        sim_partages = []
        
        for sim_id, sim_info in SIMULATEURS_ICNA.items():
            if phase_id in sim_info.get("phases_autorisees", []):
                if sim_info.get("dedie", False):
                    sim_dedies.append(sim_id)
                else:
                    sim_partages.append(sim_id)
        
        phases_partagees = []
        for sim_id in sim_partages:
            sim_info = SIMULATEURS_ICNA.get(sim_id, {})
            for phase in sim_info.get("phases_autorisees", []):
                if phase != phase_id and phase not in phases_partagees:
                    phases_partagees.append(phase)
        
        matrice[phase_id] = {
            "simulateurs_dedies": sim_dedies,
            "simulateurs_partages": sim_partages,
            "phases_partagees": phases_partagees,
            "tous_simulateurs": sim_dedies + sim_partages
        }
    
    return matrice

MATRICE_SHARING = generer_matrice_sharing_automatique()

# ============================================
# GESTION DES LANGUES
# ============================================

LANGUAGES = {
    "🇫🇷 Français": {
        "code": "fr",
        "title": "Planificateur ATC",
        "subtitle": "ICNA · AIAC · Phase Pratique",
        "login_title": "⬡ SÉLECTIONNEZ VOTRE PROFIL",
        "student": "👨‍🎓 ÉLÈVE",
        "instructor": "👨‍🏫 INSTRUCTEUR",
        "select_name": "Choisissez votre nom",
        "password": "Mot de passe",
        "enter": "🎯 Entrer",
        "forgot_password": "🔒 Mot de passe oublié ?",
        "reset_password": "🔄 Réinitialiser mon mot de passe",
        "logout": "🚪 Se déconnecter",
        "my_group": "👥 Mon Groupe",
        "courses": "📚 Cours",
        "scenarios": "🎯 Scénarios",
        "td": "📝 TD",
        "my_planning": "📅 Mon Planning",
        "my_notes": "📊 Mes Notes",
        "my_password": "🔑 Mon Mot de Passe",
        "people": "👥 Personnes",
        "config": "⚙️ Configuration",
        "generator": "🚀 Générateur",
        "multi_phases": "✈️ Multi-Phases",
        "gantt": "📊 Gantt Simulateurs",
        "simulateurs": "💻 Simulateurs",
        "config_simulateurs": "⚙️ Config Simulateurs",
        "planning": "📅 Planning",
        "evaluations": "📊 Évaluations",
        "groups": "🏷️ Groupes",
        "change_password": "🔒 Mettre à jour le mot de passe",
        "current_password": "Mot de passe actuel",
        "new_password": "Nouveau mot de passe",
        "confirm_password": "Confirmer le nouveau mot de passe",
        "no_students": "Aucun élève disponible.",
        "no_instructors": "Aucun instructeur disponible.",
        "no_courses": "Aucun cours disponible pour le moment.",
        "no_scenarios": "Aucun scénario disponible pour le moment.",
        "no_td": "Aucun TD disponible pour le moment.",
        "no_planning": "Aucune simulation planifiée pour le moment.",
        "no_notes": "Aucune note disponible pour le moment.",
        "password_updated": "✅ Mot de passe mis à jour avec succès.",
        "password_incorrect": "❌ Le mot de passe actuel est incorrect.",
        "password_too_short": "❌ Le nouveau mot de passe doit contenir au moins 4 caractères.",
        "password_mismatch": "❌ Les deux mots de passe ne correspondent pas.",
        "password_same": "⚠️ Le nouveau mot de passe doit être différent de l'ancien.",
        "add_course": "➕ Ajouter un cours",
        "add_scenario": "➕ Ajouter un scénario",
        "add_td": "➕ Ajouter un TD",
        "course_title": "Titre du cours",
        "description": "Description",
        "upload_file": "📎 Importer un fichier",
        "type": "Type",
        "tags": "Tags (séparés par des virgules)",
        "target_group": "Groupe cible",
        "all_groups": "Tous",
        "add": "➕ Ajouter",
        "delete": "🗑️ Supprimer",
        "download": "📥 Télécharger",
        "preview": "📄 Aperçu du document",
        "no_content": "Aucun contenu disponible pour ce document.",
        "external_link": "Lien externe",
        "open_link": "🔗 Ouvrir",
        "no_group": "Vous n'êtes pas encore affecté(e) à un groupe.",
        "instructor_label": "Instructeur",
        "simulator_label": "Simulateur",
        "students_count": "élève(s)",
        "average": "Moyenne sur",
        "evaluations": "évaluation(s)",
        "export": "📤 Exporter",
        "export_excel": "📥 Exporter en Excel (.xlsx)",
        "export_csv": "📥 Exporter en CSV",
        "mobile_mode": "📱 Mode Mobile",
        "mobile_mode_active": "📱 Mode mobile activé",
        "back": "⬅ Retour",
        "language": "🌐 Langue",
        "delete_all": "🗑️ Tout réinitialiser",
        "danger_zone": "⚠️ Zone dangereuse",
        "confirm_delete": "Je comprends que cette action est irréversible",
        "simulation": "Simulation",
        "briefing": "Briefing",
        "debriefing": "Débriefing",
        "controller": "Contrôleur",
        "pseudopilot": "Pseudopilote",
        "observer": "Observateur",
        "date": "Date",
        "time": "Heure",
        "duration": "Durée (min)",
        "group": "Groupe",
        "observers": "Observateurs",
        "notes": "Notes",
        "generate_planning": "🚀 Générer le planning",
        "config_saved": "✅ Configuration sauvegardée",
        "planning_generated": "✅ Planning généré !",
        "planning_error": "❌ Erreur : {error}",
        "title_required": "Le titre est requis.",
        "content_required": "Titre et contenu requis.",
        "students": "👨‍🎓 Élèves",
        "instructors": "👨‍🏫 Instructeurs",
        "no_students_in_group": "Aucun élève dans ce groupe",
        "your_group": "Mon Groupe",
        "your_planning": "Mon Planning",
        "your_notes": "Mes Notes",
        "extension_scenarios": "💡 Scénarios d'extension horaire",
        "extension_desc": "Voici des propositions pour faire tenir le planning dans la période souhaitée.",
        "no_extension": "❌ Aucun scénario d'extension ne permet de faire tenir le planning.",
        "comparative_calendar": "📅 Calendrier comparatif",
        "scenario_detail": "🔍 Détail des scénarios",
        "apply_scenario": "✅ Appliquer ce scénario",
        "best_scenario": "💡 Le meilleur scénario est",
        "apply_best": "🚀 Appliquer le meilleur scénario",
        "new_schedule": "📋 Nouveaux horaires",
        "new_end_date": "📅 Nouvelle date de fin",
        "time_gain": "⏱️ Gain total",
        "days_gain": "📊 Gain en jours",
        "planning_preview": "📈 Aperçu du planning",
        "manual_solutions": "💡 Solutions manuelles",
        "option_adjust_hours": "🕐 Option 1 : Ajuster les horaires",
        "option_extend_date": "📅 Option 2 : Étendre la date de fin",
        "propose_date": "Proposer cette date",
    },
    "🇬🇧 English": {
        "code": "en",
        "title": "ATC Planner",
        "subtitle": "ICNA · AIAC · Practical Phase",
        "login_title": "⬡ SELECT YOUR PROFILE",
        "student": "👨‍🎓 STUDENT",
        "instructor": "👨‍🏫 INSTRUCTOR",
        "select_name": "Choose your name",
        "password": "Password",
        "enter": "🎯 Enter",
        "forgot_password": "🔒 Forgot password?",
        "reset_password": "🔄 Reset my password",
        "logout": "🚪 Logout",
        "my_group": "👥 My Group",
        "courses": "📚 Courses",
        "scenarios": "🎯 Scenarios",
        "td": "📝 TD",
        "my_planning": "📅 My Planning",
        "my_notes": "📊 My Notes",
        "my_password": "🔑 My Password",
        "people": "👥 People",
        "config": "⚙️ Configuration",
        "generator": "🚀 Generator",
        "multi_phases": "✈️ Multi-Phases",
        "gantt": "📊 Simulator Gantt",
        "simulateurs": "💻 Simulators",
        "config_simulateurs": "⚙️ Simulator Config",
        "planning": "📅 Planning",
        "evaluations": "📊 Evaluations",
        "groups": "🏷️ Groups",
        "change_password": "🔒 Update password",
        "current_password": "Current password",
        "new_password": "New password",
        "confirm_password": "Confirm new password",
        "no_students": "No students available.",
        "no_instructors": "No instructors available.",
        "no_courses": "No courses available at the moment.",
        "no_scenarios": "No scenarios available at the moment.",
        "no_td": "No TD available at the moment.",
        "no_planning": "No simulation scheduled at the moment.",
        "no_notes": "No notes available at the moment.",
        "password_updated": "✅ Password updated successfully.",
        "password_incorrect": "❌ Current password is incorrect.",
        "password_too_short": "❌ New password must be at least 4 characters.",
        "password_mismatch": "❌ Passwords do not match.",
        "password_same": "⚠️ New password must be different from current.",
        "add_course": "➕ Add a course",
        "add_scenario": "➕ Add a scenario",
        "add_td": "➕ Add a TD",
        "course_title": "Course title",
        "description": "Description",
        "upload_file": "📎 Upload a file",
        "type": "Type",
        "tags": "Tags (comma separated)",
        "target_group": "Target group",
        "all_groups": "All",
        "add": "➕ Add",
        "delete": "🗑️ Delete",
        "download": "📥 Download",
        "preview": "📄 Document preview",
        "no_content": "No content available for this document.",
        "external_link": "External link",
        "open_link": "🔗 Open",
        "no_group": "You are not assigned to a group yet.",
        "instructor_label": "Instructor",
        "simulator_label": "Simulator",
        "students_count": "student(s)",
        "average": "Average over",
        "evaluations": "evaluation(s)",
        "export": "📤 Export",
        "export_excel": "📥 Export to Excel (.xlsx)",
        "export_csv": "📥 Export to CSV",
        "mobile_mode": "📱 Mobile Mode",
        "mobile_mode_active": "📱 Mobile mode activated",
        "back": "⬅ Back",
        "language": "🌐 Language",
        "delete_all": "🗑️ Reset all",
        "danger_zone": "⚠️ Danger Zone",
        "confirm_delete": "I understand this action is irreversible",
        "simulation": "Simulation",
        "briefing": "Briefing",
        "debriefing": "Debriefing",
        "controller": "Controller",
        "pseudopilot": "Pseudo-pilot",
        "observer": "Observer",
        "date": "Date",
        "time": "Time",
        "duration": "Duration (min)",
        "group": "Group",
        "observers": "Observers",
        "notes": "Notes",
        "generate_planning": "🚀 Generate planning",
        "config_saved": "✅ Configuration saved",
        "planning_generated": "✅ Planning generated!",
        "planning_error": "❌ Error: {error}",
        "title_required": "Title is required.",
        "content_required": "Title and content are required.",
        "students": "👨‍🎓 Students",
        "instructors": "👨‍🏫 Instructors",
        "no_students_in_group": "No students in this group",
        "your_group": "My Group",
        "your_planning": "My Planning",
        "your_notes": "My Notes",
        "extension_scenarios": "💡 Extension scenarios",
        "extension_desc": "Here are proposals to fit the planning within the desired period.",
        "no_extension": "❌ No extension scenario allows the planning to fit.",
        "comparative_calendar": "📅 Comparative calendar",
        "scenario_detail": "🔍 Scenario details",
        "apply_scenario": "✅ Apply this scenario",
        "best_scenario": "💡 The best scenario is",
        "apply_best": "🚀 Apply the best scenario",
        "new_schedule": "📋 New schedule",
        "new_end_date": "📅 New end date",
        "time_gain": "⏱️ Total gain",
        "days_gain": "📊 Days gained",
        "planning_preview": "📈 Planning preview",
        "manual_solutions": "💡 Manual solutions",
        "option_adjust_hours": "🕐 Option 1: Adjust hours",
        "option_extend_date": "📅 Option 2: Extend end date",
        "propose_date": "Propose this date",
    },
    "🇸🇦 العربية": {
        "code": "ar",
        "title": "مخطط ATC",
        "subtitle": "ICNA · AIAC · المرحلة العملية",
        "login_title": "⬡ اختر ملفك الشخصي",
        "student": "👨‍🎓 طالب",
        "instructor": "👨‍🏫 مدرب",
        "select_name": "اختر اسمك",
        "password": "كلمة المرور",
        "enter": "🎯 دخول",
        "forgot_password": "🔒 نسيت كلمة المرور؟",
        "reset_password": "🔄 إعادة تعيين كلمة المرور",
        "logout": "🚪 تسجيل الخروج",
        "my_group": "👥 مجموعتي",
        "courses": "📚 الدورات",
        "scenarios": "🎯 السيناريوهات",
        "td": "📝 الأعمال الموجهة",
        "my_planning": "📅 جدولي",
        "my_notes": "📊 درجاتي",
        "my_password": "🔑 كلمة المرور",
        "people": "👥 الأشخاص",
        "config": "⚙️ الإعدادات",
        "generator": "🚀 المولد",
        "multi_phases": "✈️ المراحل المتعددة",
        "gantt": "📊 مخطط غانت",
        "simulateurs": "💻 المحاكيات",
        "config_simulateurs": "⚙️ إعداد المحاكيات",
        "planning": "📅 الجدول",
        "evaluations": "📊 التقييمات",
        "groups": "🏷️ المجموعات",
        "change_password": "🔒 تحديث كلمة المرور",
        "current_password": "كلمة المرور الحالية",
        "new_password": "كلمة المرور الجديدة",
        "confirm_password": "تأكيد كلمة المرور الجديدة",
        "no_students": "لا يوجد طلاب متاحون.",
        "no_instructors": "لا يوجد مدربون متاحون.",
        "no_courses": "لا توجد دورات متاحة حالياً.",
        "no_scenarios": "لا توجد سيناريوهات متاحة حالياً.",
        "no_td": "لا توجد أعمال موجهة متاحة حالياً.",
        "no_planning": "لا توجد محاكاة مجدولة حالياً.",
        "no_notes": "لا توجد درجات متاحة حالياً.",
        "password_updated": "✅ تم تحديث كلمة المرور بنجاح.",
        "password_incorrect": "❌ كلمة المرور الحالية غير صحيحة.",
        "password_too_short": "❌ يجب أن تحتوي كلمة المرور الجديدة على 4 أحرف على الأقل.",
        "password_mismatch": "❌ كلمات المرور غير متطابقة.",
        "password_same": "⚠️ يجب أن تكون كلمة المرور الجديدة مختلفة عن الحالية.",
        "add_course": "➕ إضافة دورة",
        "add_scenario": "➕ إضافة سيناريو",
        "add_td": "➕ إضافة عمل موجه",
        "course_title": "عنوان الدورة",
        "description": "الوصف",
        "upload_file": "📎 رفع ملف",
        "type": "النوع",
        "tags": "الوسوم (مفصولة بفواصل)",
        "target_group": "المجموعة المستهدفة",
        "all_groups": "الكل",
        "add": "➕ إضافة",
        "delete": "🗑️ حذف",
        "download": "📥 تحميل",
        "preview": "📄 معاينة المستند",
        "no_content": "لا يوجد محتوى متاح لهذا المستند.",
        "external_link": "رابط خارجي",
        "open_link": "🔗 فتح",
        "no_group": "لم يتم تعيينك لمجموعة بعد.",
        "instructor_label": "المدرب",
        "simulator_label": "المحاكي",
        "students_count": "طالب(ـة)",
        "average": "المتوسط على",
        "evaluations": "تقييم(ـات)",
        "export": "📤 تصدير",
        "export_excel": "📥 تصدير إلى Excel (.xlsx)",
        "export_csv": "📥 تصدير إلى CSV",
        "mobile_mode": "📱 الوضع المحمول",
        "mobile_mode_active": "📱 تم تفعيل الوضع المحمول",
        "back": "⬅ رجوع",
        "language": "🌐 اللغة",
        "delete_all": "🗑️ إعادة تعيين الكل",
        "danger_zone": "⚠️ منطقة خطرة",
        "confirm_delete": "أفهم أن هذا الإجراء لا رجعة فيه",
        "simulation": "محاكاة",
        "briefing": "إحاطة",
        "debriefing": "تقييم",
        "controller": "مراقب",
        "pseudopilot": "طيار وهمي",
        "observer": "مراقب",
        "date": "التاريخ",
        "time": "الوقت",
        "duration": "المدة (دقيقة)",
        "group": "المجموعة",
        "observers": "المراقبون",
        "notes": "ملاحظات",
        "generate_planning": "🚀 إنشاء الجدول",
        "config_saved": "✅ تم حفظ الإعدادات",
        "planning_generated": "✅ تم إنشاء الجدول!",
        "planning_error": "❌ خطأ: {error}",
        "title_required": "العنوان مطلوب.",
        "content_required": "العنوان والمحتوى مطلوبان.",
        "students": "👨‍🎓 الطلاب",
        "instructors": "👨‍🏫 المدربون",
        "no_students_in_group": "لا يوجد طلاب في هذه المجموعة",
        "your_group": "مجموعتي",
        "your_planning": "جدولي",
        "your_notes": "درجاتي",
        "extension_scenarios": "💡 سيناريوهات التمديد",
        "extension_desc": "هذه اقتراحات لتتناسب الجدولة مع الفترة المطلوبة.",
        "no_extension": "❌ لا يوجد سيناريو تمديد يسمح بتناسب الجدولة.",
        "comparative_calendar": "📅 تقويم مقارن",
        "scenario_detail": "🔍 تفاصيل السيناريو",
        "apply_scenario": "✅ تطبيق هذا السيناريو",
        "best_scenario": "💡 أفضل سيناريو هو",
        "apply_best": "🚀 تطبيق أفضل سيناريو",
        "new_schedule": "📋 الجدول الجديد",
        "new_end_date": "📅 تاريخ الانتهاء الجديد",
        "time_gain": "⏱️ الربح الإجمالي",
        "days_gain": "📊 الأيام المربحة",
        "planning_preview": "📈 معاينة الجدول",
        "manual_solutions": "💡 حلول يدوية",
        "option_adjust_hours": "🕐 الخيار 1: تعديل الساعات",
        "option_extend_date": "📅 الخيار 2: تمديد تاريخ الانتهاء",
        "propose_date": "اقتراح هذا التاريخ",
    }
}

def t(key, lang=None):
    """Traduit une clé dans la langue sélectionnée."""
    if lang is None:
        lang = st.session_state.get("language", "🇫🇷 Français")
    return LANGUAGES[lang].get(key, key)

def is_mobile_device():
    """Détecte si l'utilisateur est sur un appareil mobile."""
    try:
        user_agent = st.context.headers.get("User-Agent", "")
        mobile_keywords = ["Mobile", "Android", "iPhone", "iPad", "webOS"]
        return any(keyword in user_agent for keyword in mobile_keywords)
    except:
        return False

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
                promotion TEXT DEFAULT 'P1',
                password_hash TEXT, password_salt TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS instructeurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, prenom TEXT NOT NULL, actif BOOLEAN DEFAULT 1,
                phase TEXT,
                password_hash TEXT, password_salt TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS groupes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, instructeur_id INTEGER, simulateur_id INTEGER,
                phase TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS groupe_eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                groupe_id INTEGER, eleve_id INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, duree INTEGER DEFAULT 65, est_test BOOLEAN DEFAULT 0, ordre INTEGER,
                phase TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS seances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL, heure_debut TEXT NOT NULL, duree INTEGER NOT NULL,
                type TEXT CHECK(type IN ('briefing', 'simulation', 'debriefing')),
                simulation_id INTEGER, groupe_id INTEGER, instructeur_id INTEGER,
                instructeur_evaluateur_id INTEGER, simulateur_id INTEGER,
                controle_eleve_id INTEGER, pseudo_eleve_id INTEGER,
                observateurs TEXT, statut TEXT DEFAULT 'planifiee', notes TEXT,
                phase TEXT, promotion TEXT
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
            """CREATE TABLE IF NOT EXISTS simulateurs (
                id INTEGER PRIMARY KEY,
                nom TEXT NOT NULL,
                type TEXT NOT NULL,
                disponible BOOLEAN DEFAULT 1,
                phase_actuelle TEXT,
                promotion_actuelle TEXT,
                date_occupation DATE,
                heure_debut_occupation TEXT,
                heure_fin_occupation TEXT,
                est_dedie BOOLEAN DEFAULT 0,
                phases_autorisees TEXT
            )"""
        ]
        for ddl in ddl_statements:
            self._exec(ddl)

        # Initialiser les simulateurs
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM simulateurs")
        if cursor.fetchone()[0] == 0:
            for sim_id, sim_info in SIMULATEURS_ICNA.items():
                cursor.execute("""
                    INSERT INTO simulateurs (id, nom, type, est_dedie, phases_autorisees)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    sim_id,
                    sim_info["nom"],
                    sim_info["type"],
                    1 if sim_info["dedie"] else 0,
                    json.dumps(sim_info.get("phases_autorisees", []))
                ))
        cursor.connection.commit()
        cursor.connection.close()

        # Seed des données de démonstration
        try:
            nb_instr = self._query("SELECT COUNT(*) AS n FROM instructeurs").iloc[0]["n"]
            nb_eleves = self._query("SELECT COUNT(*) AS n FROM eleves").iloc[0]["n"]
        except:
            nb_instr = 0
            nb_eleves = 0
            
        if nb_instr == 0 and nb_eleves == 0:
            # Ajouter les instructeurs par phase
            for phase_id, phase_instr in INSTRUCTEURS_PAR_PHASE.items():
                for instr in phase_instr["instructeurs"]:
                    self.add_instructeur_phase(
                        instr["nom"], 
                        instr["prenom"], 
                        phase_id,
                        password=DEFAULT_PASSWORD
                    )
            
            # Ajouter les élèves par promotion
            for promo_id, promo_info in PROMOTIONS.items():
                for nom, prenom in promo_info["eleves"]:
                    self.add_eleve(
                        nom, 
                        prenom, 
                        password=DEFAULT_PASSWORD, 
                        promotion=promo_id
                    )

        # Backfill des mots de passe
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

    def add_eleve(self, nom, prenom, email=None, password=None, promotion="P1"):
        temp_password = None
        if not password:
            temp_password = generate_temp_password()
            password = temp_password
        pwd_hash, salt = hash_password(password)
        new_id = self._exec_returning_id(
            "INSERT INTO eleves (nom, prenom, email, promotion, password_hash, password_salt) "
            "VALUES (:nom, :prenom, :email, :promotion, :h, :s) RETURNING id",
            {"nom": nom, "prenom": prenom, "email": email, "promotion": promotion, "h": pwd_hash, "s": salt}
        )
        return new_id, temp_password

    def add_instructeur_phase(self, nom, prenom, phase_id, password=None):
        temp_password = None
        if not password:
            temp_password = generate_temp_password()
            password = temp_password
        pwd_hash, salt = hash_password(password)
        new_id = self._exec_returning_id(
            "INSERT INTO instructeurs (nom, prenom, actif, phase, password_hash, password_salt) "
            "VALUES (:nom, :prenom, 1, :phase, :h, :s) RETURNING id",
            {"nom": nom, "prenom": prenom, "phase": phase_id, "h": pwd_hash, "s": salt}
        )
        return new_id, temp_password

    def get_instructeurs_par_phase(self, phase_id):
        return self._query(
            "SELECT * FROM instructeurs WHERE phase = :phase AND actif = 1 ORDER BY nom, prenom",
            {"phase": phase_id}
        )

    def get_eleves(self, groupe_id=None):
        if groupe_id:
            return self._query("SELECT * FROM eleves WHERE groupe_id = :gid ORDER BY nom, prenom", {"gid": groupe_id})
        return self._query("SELECT * FROM eleves ORDER BY nom, prenom")

    def get_eleve_by_id(self, eleve_id):
        df = self._query("SELECT id, nom, prenom, email, groupe_id, promotion FROM eleves WHERE id = :id", {"id": eleve_id})
        if df.empty:
            return None
        row = df.iloc[0]
        return (int(row["id"]), row["nom"], row["prenom"], row["email"], row["groupe_id"], row["promotion"])

    def delete_eleve(self, eleve_id):
        self._exec("DELETE FROM groupe_eleves WHERE eleve_id = :id", {"id": eleve_id})
        self._exec("DELETE FROM notes WHERE eleve_id = :id", {"id": eleve_id})
        self._exec("DELETE FROM eleves WHERE id = :id", {"id": eleve_id})

    def get_instructeurs(self):
        return self._query("SELECT * FROM instructeurs WHERE actif = 1 ORDER BY nom, prenom")

    def get_instructeur_by_id(self, instr_id):
        df = self._query("SELECT id, nom, prenom, actif, phase FROM instructeurs WHERE id = :id", {"id": instr_id})
        if df.empty:
            return None
        row = df.iloc[0]
        return (int(row["id"]), row["nom"], row["prenom"], row["actif"], row["phase"])

    def delete_instructeur(self, instr_id):
        self._exec("DELETE FROM instructeurs WHERE id = :id", {"id": instr_id})

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

    def set_password_eleve(self, eleve_id, new_password):
        pwd_hash, salt = hash_password(new_password)
        self._exec("UPDATE eleves SET password_hash = :h, password_salt = :s WHERE id = :id",
                    {"h": pwd_hash, "s": salt, "id": eleve_id})

    def set_password_instructeur(self, instr_id, new_password):
        pwd_hash, salt = hash_password(new_password)
        self._exec("UPDATE instructeurs SET password_hash = :h, password_salt = :s WHERE id = :id",
                    {"h": pwd_hash, "s": salt, "id": instr_id})

    def get_groupes(self):
        return self._query("""
            SELECT g.*, i.nom || ' ' || i.prenom as instructeur_nom
            FROM groupes g LEFT JOIN instructeurs i ON g.instructeur_id = i.id
            ORDER BY g.id
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
                "INSERT INTO groupes (nom, instructeur_id, simulateur_id, phase) "
                "VALUES (:nom, :instr, :sim, :phase) RETURNING id",
                {"nom": g["nom"], "instr": g["instructeur_id"], "sim": g["simulateur_id"], "phase": g.get("phase", "AERODROME")}
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
            "notes": s.get("notes", ""), "phase": s.get("phase"), "promotion": s.get("promotion")
        } for s in seances]
        self._exec_many("""
            INSERT INTO seances (
                date, heure_debut, duree, type, simulation_id, groupe_id,
                instructeur_id, instructeur_evaluateur_id, simulateur_id,
                controle_eleve_id, pseudo_eleve_id, observateurs, notes,
                phase, promotion
            ) VALUES (
                :date, :heure, :duree, :type, :sim_id, :groupe_id,
                :instr_id, :instr_eval_id, :sim_engin,
                :controle_id, :pseudo_id, :observateurs, :notes,
                :phase, :promotion
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
                      "cours", "scenarios", "td", "notes", "grilles_evaluation", "simulateurs"):
            self._exec(f"DELETE FROM {table}")

# ============================================
# GESTIONNAIRE DE SIMULATEURS
# ============================================

class GestionnaireSimulateursICNA:
    def __init__(self, db):
        self.db = db
    
    def get_simulateurs_disponibles(self, phase_id, date=None, heure_debut=None, heure_fin=None):
        """Retourne les simulateurs disponibles pour une phase donnée."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        sim_autorises = []
        for sim_id, sim_info in SIMULATEURS_ICNA.items():
            if phase_id in sim_info.get("phases_autorisees", []):
                sim_autorises.append(sim_id)
        
        if not sim_autorises:
            conn.close()
            return []
        
        query = """
            SELECT s.* FROM simulateurs s
            WHERE s.id IN ({})
            AND s.disponible = 1
        """.format(','.join('?' * len(sim_autorises)))
        params = sim_autorises.copy()
        
        if date and heure_debut and heure_fin:
            query += """
                AND NOT EXISTS (
                    SELECT 1 FROM seances se
                    WHERE se.simulateur_id = s.id
                    AND se.date = ?
                    AND (
                        (se.heure_debut < ? AND datetime(se.date || ' ' || se.heure_debut, '+' || se.duree || ' minutes') > datetime(?))
                        OR (se.heure_debut >= ? AND se.heure_debut < ?)
                    )
                )
            """
            params.extend([date, heure_fin, heure_debut, heure_debut, heure_fin])
        
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.close()
        
        return [dict(zip([col[0] for col in cursor.description], row)) for row in result]
    
    def get_occupation_simulateurs(self, date=None):
        """Retourne l'occupation de tous les simulateurs."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT s.id, s.nom, s.type, s.disponible, s.phase_actuelle, 
                   s.promotion_actuelle, s.date_occupation, 
                   s.heure_debut_occupation, s.heure_fin_occupation,
                   s.est_dedie, s.phases_autorisees
            FROM simulateurs s
        """
        
        if date:
            query += " WHERE s.date_occupation = ? OR s.disponible = 1"
            cursor.execute(query, (date,))
        else:
            cursor.execute(query)
        
        result = cursor.fetchall()
        conn.close()
        
        return [dict(zip([col[0] for col in cursor.description], row)) for row in result]
    
    def get_stats_occupation(self):
        """Retourne les statistiques d'occupation des simulateurs."""
        simulateurs = self.get_occupation_simulateurs()
        
        stats = {
            "total": len(simulateurs),
            "disponibles": sum(1 for s in simulateurs if s['disponible']),
            "occupes": sum(1 for s in simulateurs if not s['disponible']),
            "par_phase": {},
            "par_type": {"DEDIE": 0, "PARTAGE": 0}
        }
        
        for sim in simulateurs:
            if sim['est_dedie']:
                stats["par_type"]["DEDIE"] += 1
            else:
                stats["par_type"]["PARTAGE"] += 1
            
            if not sim['disponible'] and sim['phase_actuelle']:
                phase = sim['phase_actuelle']
                if phase not in stats["par_phase"]:
                    stats["par_phase"][phase] = {"occupes": 0, "total": 0}
                stats["par_phase"][phase]["occupes"] += 1
            
            phases_autorisees = json.loads(sim['phases_autorisees']) if sim['phases_autorisees'] else []
            for phase in phases_autorisees:
                if phase not in stats["par_phase"]:
                    stats["par_phase"][phase] = {"occupes": 0, "total": 0}
                stats["par_phase"][phase]["total"] += 1
        
        return stats

# ============================================
# FONCTIONS DE VISUALISATION DE DOCUMENTS
# ============================================

def detect_file_type(decoded):
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

def render_document_view(contenu, type_doc, titre, doc_index=None):
    if not contenu:
        st.info(t("no_content"))
        return

    titre_safe = esc(titre)

    if doc_index is None:
        doc_index = random.randint(1000, 9999)

    if contenu.startswith(("http://", "https://")):
        st.markdown(f"""
        <div class="doc-viewer">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap;">
                <span style="font-size:1.2em;">🔗</span>
                <div>
                    <div style="color:#7affb0;font-weight:600;">{titre_safe}</div>
                    <div style="color:rgba(180,200,220,0.4);font-size:0.8em;">{t("external_link")}</div>
                </div>
                <div style="margin-left:auto;">
                    <a href="{contenu}" target="_blank" class="doc-btn doc-btn-open">{t("open_link")}</a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    decoded = None
    
    try:
        padding = len(contenu) % 4
        if padding:
            contenu_padded = contenu + '=' * (4 - padding)
        else:
            contenu_padded = contenu
        decoded = base64.b64decode(contenu_padded)
    except Exception:
        pass
    
    if decoded is None:
        try:
            decoded = base64.b64decode(contenu + '==')
        except Exception:
            pass
    
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

    file_ext, icon, label, mime_type = detect_file_type(decoded)
    taille_kb = len(decoded) // 1024
    taille_mo = len(decoded) / (1024 * 1024)

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

    if mime_type == "application/pdf":
        st.markdown(f"### {t('preview')}")
        
        is_mobile = st.session_state.get("is_mobile", False)
        
        if is_mobile:
            viewer_width = "100%"
            viewer_height = 500
        else:
            viewer_width = 1200
            viewer_height = 800
        
        try:
            from streamlit_pdf_viewer import pdf_viewer
            pdf_viewer(
                input=decoded,
                width=viewer_width,
                height=viewer_height
            )
        except ImportError:
            st.error("❌ La bibliothèque streamlit-pdf-viewer n'est pas installée.")
            st.info("💡 Installez-la avec : pip install streamlit-pdf-viewer")
            
            pdf_b64 = base64.b64encode(decoded).decode("utf-8")
            data_url = f"data:application/pdf;base64,{pdf_b64}"
            st.markdown(f"""
            <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
                <a href="{data_url}" target="_blank" 
                   style="display:inline-block;padding:10px 20px;background:rgba(0,255,100,0.05);
                          border:1px solid rgba(0,255,100,0.1);border-radius:8px;color:#66ddff;
                          text-decoration:none;font-family:'JetBrains Mono',monospace;text-align:center;">
                    🔗 {t('open_link')}
                </a>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Erreur d'affichage du PDF : {str(e)}")
            
            pdf_b64 = base64.b64encode(decoded).decode("utf-8")
            data_url = f"data:application/pdf;base64,{pdf_b64}"
            st.markdown(f"""
            <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
                <a href="{data_url}" target="_blank" 
                   style="display:inline-block;padding:10px 20px;background:rgba(0,255,100,0.05);
                          border:1px solid rgba(0,255,100,0.1);border-radius:8px;color:#66ddff;
                          text-decoration:none;font-family:'JetBrains Mono',monospace;text-align:center;">
                    🔗 {t('open_link')}
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
    
    st.download_button(
        label=f"{t('download')} {titre}.{file_ext}",
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

def generer_groupes_phase(eleves_df, instructeurs_df, phase_id):
    """Génère des groupes pour une phase spécifique."""
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
            "nom": f"Groupe {phase_id} - {instr_row.prenom} {instr_row.nom}",
            "instructeur_id": instr_row.id,
            "simulateur_id": i + 1,
            "eleves": membres,
            "phase": phase_id
        })
    return groupes

def generer_runs_pour_groupe(groupe, instructeurs_ids, sim):
    """Génère les runs pour un groupe."""
    eleves = groupe["eleves"]
    instr_id = groupe["instructeur_id"]
    autres_instructeurs = [i for i in instructeurs_ids if i != instr_id]
    est_test = sim.get('est_test', False)
    
    runs = []
    if est_test:
        for k, eleve in enumerate(eleves):
            instr_sub = autres_instructeurs[k % len(autres_instructeurs)] if autres_instructeurs else instr_id
            runs.append({
                "controleur": eleve,
                "pseudo": None,
                "instructeur_id": instr_sub,
                "instructeur_evaluateur_id": instr_id,
                "observateurs": [e for e in eleves if e != eleve]
            })
    else:
        if len(eleves) >= 2:
            offset = random.randint(0, len(eleves) - 1)
            ordre = eleves[offset:] + eleves[:offset]
            for i in range(len(eleves)):
                runs.append({
                    "controleur": ordre[i],
                    "pseudo": ordre[(i + 1) % len(eleves)],
                    "instructeur_id": instr_id,
                    "instructeur_evaluateur_id": None,
                    "observateurs": [e for e in eleves if e not in [ordre[i], ordre[(i + 1) % len(eleves)]]]
                })
    
    return runs

def generer_planning_multiphases(config, eleves_df, instructeurs_df):
    """Génère le planning pour toutes les phases."""
    toutes_seances = []
    gestionnaire_sim = GestionnaireSimulateursICNA(Database())
    
    for promo_id, promo_info in PROMOTIONS.items():
        eleves_promo = eleves_df[eleves_df['promotion'] == promo_id]
        if eleves_promo.empty:
            continue
        
        for phase_id in promo_info['phases']:
            phase_info = PHASES_ICNA.get(phase_id)
            if not phase_info:
                continue
            
            instructeurs_phase = instructeurs_df[instructeurs_df['phase'] == phase_id]
            if instructeurs_phase.empty:
                continue
            
            groupes = generer_groupes_phase(eleves_promo, instructeurs_phase, phase_id)
            
            windows = build_windows(config)
            config_phase = config.copy()
            config_phase['_date_debut_obj'] = datetime.strptime(config['date_debut'], "%Y-%m-%d").date()
            
            jours_decalage = list(PHASES_ICNA.keys()).index(phase_id) * 3
            date_debut_phase = config_phase['_date_debut_obj'] + timedelta(days=jours_decalage)
            config_phase['_date_debut_obj'] = date_debut_phase
            
            ds_phase = DayScheduler(date_debut_phase, windows)
            
            sims_phase = []
            for i in range(phase_info['simulations']):
                sims_phase.append({
                    "id": i + 1,
                    "nom": f"{phase_info['nom']} - Sim {i+1}",
                    "duree": phase_info['duree_simulation'],
                    "est_test": 0,
                    "phase": phase_id
                })
            sims_phase.append({
                "id": len(sims_phase) + 1,
                "nom": f"{phase_info['nom']} - Test",
                "duree": phase_info['duree_simulation'] + 15,
                "est_test": 1,
                "phase": phase_id
            })
            
            for sim in sims_phase:
                d, t, dur = ds_phase.get_slot(config['duree_briefing'])
                toutes_seances.append({
                    "date": d, "heure_debut": t, "duree": dur, "type": "briefing",
                    "simulation_id": sim['id'], "phase": phase_id,
                    "promotion": promo_id,
                    "groupe_id": None, "instructeur_id": None,
                    "simulateur_id": None,
                    "controle_eleve_id": None, "pseudo_eleve_id": None,
                    "observateurs": [],
                    "notes": f"Briefing - {sim['nom']} ({promo_info['nom']})"
                })
                
                for groupe in groupes:
                    instructeurs_phase_list = instructeurs_phase['id'].tolist()
                    runs = generer_runs_pour_groupe(groupe, instructeurs_phase_list, sim)
                    
                    for run in runs:
                        d_run, t_run, dur_run = ds_phase.get_slot(sim['duree'])
                        
                        sim_dispo = gestionnaire_sim.get_simulateurs_disponibles(
                            phase_id, d_run, t_run,
                            (datetime.strptime(t_run, "%H:%M") + timedelta(minutes=dur_run)).strftime("%H:%M")
                        )
                        sim_utilise = sim_dispo[0]['id'] if sim_dispo else None
                        
                        seance = {
                            "date": d_run, "heure_debut": t_run, "duree": dur_run, "type": "simulation",
                            "simulation_id": sim['id'], "phase": phase_id,
                            "promotion": promo_id,
                            "groupe_id": groupe['id'],
                            "instructeur_id": run.get('instructeur_id'),
                            "instructeur_evaluateur_id": run.get('instructeur_evaluateur_id'),
                            "simulateur_id": sim_utilise,
                            "controle_eleve_id": run['controleur'],
                            "pseudo_eleve_id": run.get('pseudo'),
                            "observateurs": run.get('observateurs', []),
                            "notes": f"{phase_info['nom']} - {sim['nom']} ({promo_info['nom']})" + (" (Test)" if sim['est_test'] else "")
                        }
                        toutes_seances.append(seance)
                
                d, t, dur = ds_phase.get_slot(config['duree_debriefing'])
                toutes_seances.append({
                    "date": d, "heure_debut": t, "duree": dur, "type": "debriefing",
                    "simulation_id": sim['id'], "phase": phase_id,
                    "promotion": promo_id,
                    "groupe_id": None, "instructeur_id": None,
                    "simulateur_id": None,
                    "controle_eleve_id": None, "pseudo_eleve_id": None,
                    "observateurs": [],
                    "notes": f"Debriefing - {sim['nom']} ({promo_info['nom']})"
                })
    
    return toutes_seances

# ============================================
# FONCTIONS D'EXPORT
# ============================================

def _type_label(type_value):
    type_map = {
        "briefing": t("briefing"),
        "simulation": t("simulation"),
        "debriefing": t("debriefing")
    }
    return type_map.get(type_value, type_value)

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
    st.markdown(f'<div class="section-title" style="font-size:1em;">{t("export")}</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    horodatage = date.today().strftime("%Y-%m-%d")
    unique_id = random.randint(1000, 9999)
    
    with col1:
        st.download_button(
            t("export_excel"),
            data=to_excel_bytes(export_df, "Planning"),
            file_name=f"{filename_prefix}_{horodatage}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"export_xlsx_{key_prefix}_{unique_id}"
        )
    with col2:
        st.download_button(
            t("export_csv"),
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{filename_prefix}_{horodatage}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"export_csv_{key_prefix}_{unique_id}"
        )

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
    role_text = t("observer")
    role_class = "strip-role-observer"
    if seance.get("controle_eleve_id") == eleve_id:
        role_text = t("controller")
        role_class = "strip-role-controller"
    elif seance.get("pseudo_eleve_id") == eleve_id:
        role_text = t("pseudopilot")
        role_class = "strip-role-pseudo"

    return f"""
    <div class="flight-strip">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
            <div>
                <span class="strip-callsign">📡 {esc(seance.get('simulation_nom', t('simulation')))}</span>
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

# ============================================
# CHANGEMENT DE MOT DE PASSE
# ============================================

def section_mon_mot_de_passe(db, role, user_id):
    st.markdown(f'<div class="section-title">{t("my_password")}</div>', unsafe_allow_html=True)
    st.caption("Vous pouvez modifier votre mot de passe à tout moment. Il n'est jamais stocké en clair.")

    with st.form("change_password_form"):
        ancien = st.text_input(t("current_password"), type="password")
        nouveau = st.text_input(t("new_password"), type="password")
        confirmation = st.text_input(t("confirm_password"), type="password")
        submitted = st.form_submit_button(t("change_password"))

        if submitted:
            if role == "eleve":
                mdp_valide = db.verify_password_eleve(user_id, ancien)
            else:
                mdp_valide = db.verify_password_instructeur(user_id, ancien)

            if not mdp_valide:
                st.error(t("password_incorrect"))
            elif len(nouveau) < 4:
                st.error(t("password_too_short"))
            elif nouveau != confirmation:
                st.error(t("password_mismatch"))
            elif nouveau == ancien:
                st.warning(t("password_same"))
            else:
                if role == "eleve":
                    db.set_password_eleve(user_id, nouveau)
                else:
                    db.set_password_instructeur(user_id, nouveau)
                st.success(t("password_updated"))

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
        if st.button(t("student"), use_container_width=True):
            st.session_state["login_role"] = "eleve"
            st.rerun()
    with col2:
        if st.button(t("instructor"), use_container_width=True):
            st.session_state["login_role"] = "instructeur"
            st.rerun()

    role = st.session_state.get("login_role")

    if role == "eleve":
        eleves = db.get_eleves()
        if eleves.empty:
            st.warning(t("no_students"))
            return
        eleve_options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in eleves.iterrows()}
        selected = st.selectbox(t("select_name"), list(eleve_options.keys()))
        password_input = st.text_input(t("password"), type="password", key="login_pwd_eleve")
        if st.button(t("enter"), type="primary", use_container_width=True):
            eleve_id = eleve_options[selected]
            if db.verify_password_eleve(eleve_id, password_input):
                eleve = db.get_eleve_by_id(eleve_id)
                st.session_state["user"] = dict(zip(["id", "nom", "prenom", "email", "groupe_id", "promotion"], eleve))
                st.session_state["role"] = "eleve"
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect.")

        with st.expander(t("forgot_password")):
            st.caption(f"Réinitialiser directement le mot de passe de **{esc(selected)}**")
            if st.button(t("reset_password"), key="reset_btn_eleve"):
                new_temp = generate_temp_password()
                db.set_password_eleve(eleve_options[selected], new_temp)
                st.success(f"✅ Nouveau mot de passe temporaire : **{new_temp}**")

    elif role == "instructeur":
        instructeurs = db.get_instructeurs()
        if instructeurs.empty:
            st.warning(t("no_instructors"))
            return
        instr_options = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in instructeurs.iterrows()}
        selected = st.selectbox(t("select_name"), list(instr_options.keys()))
        password_input = st.text_input(t("password"), type="password", key="login_pwd_instr")
        if st.button(t("enter"), type="primary", use_container_width=True):
            instr_id = instr_options[selected]
            if db.verify_password_instructeur(instr_id, password_input):
                instr = db.get_instructeur_by_id(instr_id)
                st.session_state["user"] = dict(zip(["id", "nom", "prenom", "email", "actif", "phase"], instr))
                st.session_state["role"] = "instructeur"
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect.")

        with st.expander(t("forgot_password")):
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
    promo = user.get('promotion', 'P1')
    promo_nom = PROMOTIONS.get(promo, {}).get('nom', promo)
    
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
                    {t("title")} · {t("subtitle")} · {promo_nom}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def header_instructeur(user):
    phase = user.get('phase', '')
    phase_nom = PHASES_ICNA.get(phase, {}).get('nom', phase)
    
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
                    {t("title")} · {t("subtitle")} · {phase_nom}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# SECTIONS ÉLÈVE
# ============================================

def section_cours_eleve(cours):
    st.markdown(f'<div class="section-title">{t("courses")}</div>', unsafe_allow_html=True)
    if cours.empty:
        st.info(t("no_courses"))
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
    st.markdown(f'<div class="section-title">{t("scenarios")}</div>', unsafe_allow_html=True)
    if scenarios.empty:
        st.info(t("no_scenarios"))
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
    st.markdown(f'<div class="section-title">{t("td")}</div>', unsafe_allow_html=True)
    if tds.empty:
        st.info(t("no_td"))
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
    st.markdown(f'<div class="section-title">{t("my_planning")}</div>', unsafe_allow_html=True)
    if seances.empty:
        st.info(t("no_planning"))
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
    st.markdown(f'<div class="section-title">{t("my_group")}</div>', unsafe_allow_html=True)
    groupe = db.get_groupe_de_eleve(eleve_id)
    if not groupe:
        st.info(t("no_group"))
        return

    membres = db.get_groupe_eleves(groupe["id"])
    chips = "".join([
        f'<span class="eleve-chip">📌 {esc(m["prenom"])} {esc(m["nom"])}{" · vous" if m["id"] == eleve_id else ""}</span>'
        for _, m in membres.iterrows()
    ])
    instr_nom = groupe.get("instructeur_nom") or "Non assigné"
    sim_id = groupe.get("simulateur_id")
    sim_label = f"{t('simulator_label')} {sim_id}" if sim_id is not None else "Simulateur non assigné"
    phase = groupe.get("phase", "")
    phase_nom = PHASES_ICNA.get(phase, {}).get('nom', phase)

    st.markdown(f"""
    <div class="groupe-card">
        <h4>🏷️ {esc(groupe['nom'])}</h4>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
            <span class="instructeur-badge">👤 {t('instructor_label')} : {esc(instr_nom)}</span>
            <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                        border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                💻 {esc(sim_label)}
            </span>
            <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                        border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                🛫 {phase_nom}
            </span>
            <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                        border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                👨‍🎓 {len(membres)} {t('students_count')}
            </span>
        </div>
        <div>{chips if chips else f'<span style="color:rgba(180,200,220,0.3);font-size:0.85em;">{t("no_students_in_group")}</span>'}</div>
    </div>
    """, unsafe_allow_html=True)

def section_notes_eleve(notes):
    st.markdown(f'<div class="section-title">{t("my_notes")}</div>', unsafe_allow_html=True)
    if notes.empty:
        st.info(t("no_notes"))
        return
    moyenne = notes["note"].mean()
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:16px;">
        <span style="font-size:2em;font-weight:700;color:#7affb0;">{moyenne:.1f}/20</span>
        <span style="display:block;color:rgba(180,200,220,0.3);font-size:0.75em;">
            {t('average')} {len(notes)} {t('evaluations')}
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
# SECTIONS INSTRUCTEUR - NOUVELLES PAGES
# ============================================

def section_visualisation_phases(db):
    """Affiche le planning de toutes les phases avec instructeurs."""
    st.markdown(f"## ✈️ {t('multi_phases')}")
    st.caption("Visualisation des 5 phases pratiques avec leurs instructeurs et simulateurs")
    
    col1, col2 = st.columns(2)
    with col1:
        date_debut = st.date_input("Date de début", value=date.today())
    with col2:
        nb_jours = st.slider("Nombre de jours à afficher", 7, 30, 14)
    
    seances = db.get_seances()
    if seances.empty:
        st.info("Aucune séance planifiée.")
        return
    
    date_fin = date_debut + timedelta(days=nb_jours)
    seances['date'] = pd.to_datetime(seances['date'])
    seances = seances[(seances['date'] >= pd.Timestamp(date_debut)) & 
                       (seances['date'] <= pd.Timestamp(date_fin))]
    
    if seances.empty:
        st.info("Aucune séance dans cette période.")
        return
    
    for phase_id, phase_info in PHASES_ICNA.items():
        seances_phase = seances[seances['phase'] == phase_id]
        if seances_phase.empty:
            continue
        
        instructeurs_phase = db.get_instructeurs_par_phase(phase_id)
        
        with st.expander(f"🛫 {phase_info['nom']} ({phase_info['niveau']})", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Promotion", PROMOTIONS.get(phase_info['promotion'], {}).get('nom', 'N/A'))
            with col2:
                st.metric("Instructeurs", len(instructeurs_phase))
            with col3:
                sim_count = len(seances_phase['simulateur_id'].dropna().unique())
                st.metric("Simulateurs", sim_count)
            with col4:
                st.metric("Simulations", len(seances_phase[seances_phase['type'] == 'simulation']))
            
            if not instructeurs_phase.empty:
                st.markdown("**👨‍🏫 Instructeurs de la phase:**")
                instr_names = ", ".join([f"{row['prenom']} {row['nom']}" for _, row in instructeurs_phase.iterrows()])
                st.caption(instr_names)
            
            st.markdown("**📅 Séances:**")
            for _, seance in seances_phase.sort_values(['date', 'heure_debut']).iterrows():
                type_emoji = "📋" if seance['type'] == 'briefing' else "🛫" if seance['type'] == 'simulation' else "📝"
                statut = "✅" if seance['simulateur_id'] else "⏳"
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span>{type_emoji}</span>
                    <span style="font-size:0.85em;color:#7affb0;">{seance['date'].strftime('%d/%m')}</span>
                    <span style="font-size:0.85em;color:#ffcc44;">{seance['heure_debut']}</span>
                    <span style="font-size:0.85em;color:rgba(180,200,220,0.5);">{seance.get('notes', '')[:40]}</span>
                    <span style="margin-left:auto;font-size:0.75em;color:rgba(180,200,220,0.3);">{statut}</span>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Matrice de Partage des Simulateurs")
    
    data = []
    for phase_id, phase_info in PHASES_ICNA.items():
        sim_ids = MATRICE_SHARING.get(phase_id, {}).get("tous_simulateurs", [])
        sim_dedies = MATRICE_SHARING.get(phase_id, {}).get("simulateurs_dedies", [])
        sim_partages = MATRICE_SHARING.get(phase_id, {}).get("simulateurs_partages", [])
        partage = MATRICE_SHARING.get(phase_id, {}).get("phases_partagees", [])
        instr_count = len(db.get_instructeurs_par_phase(phase_id))
        
        data.append({
            "Phase": phase_info['nom'],
            "Promotion": PROMOTIONS.get(phase_info['promotion'], {}).get('nom', 'N/A'),
            "Instructeurs": instr_count,
            "Simulateurs": len(sim_ids),
            "Dédiés": ", ".join([f"S{id}" for id in sim_dedies]) or "-",
            "Partagés": ", ".join([f"S{id}" for id in sim_partages]) or "-",
            "Partage avec": ", ".join([PHASES_ICNA.get(p, {}).get('nom', p) for p in partage]) or "Aucun"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def afficher_gantt_simulateurs(db):
    """Affiche un diagramme de Gantt pour les simulateurs."""
    st.markdown(f"### 📊 {t('gantt')}")
    
    col1, col2 = st.columns(2)
    with col1:
        date_debut = st.date_input("Date de début Gantt", value=date.today())
    with col2:
        nb_jours = st.slider("Nombre de jours Gantt", 3, 21, 7)
    
    seances = db.get_seances()
    if seances.empty:
        st.info("Aucune séance planifiée.")
        return
    
    date_fin = date_debut + timedelta(days=nb_jours)
    seances['date'] = pd.to_datetime(seances['date'])
    seances = seances[(seances['date'] >= pd.Timestamp(date_debut)) & 
                       (seances['date'] <= pd.Timestamp(date_fin))]
    
    if seances.empty:
        st.info("Aucune séance dans cette période.")
        return
    
    data = []
    simulateurs_ids = seances['simulateur_id'].dropna().unique()
    
    for sim_id in simulateurs_ids:
        seances_sim = seances[seances['simulateur_id'] == sim_id]
        for _, seance in seances_sim.iterrows():
            if seance['type'] == 'simulation':
                phase_info = PHASES_ICNA.get(seance.get('phase', ''), {})
                data.append({
                    "Simulateur": f"S{int(sim_id)} - {SIMULATEURS_ICNA.get(sim_id, {}).get('nom', '')}",
                    "Phase": phase_info.get('nom', 'Inconnue'),
                    "Promotion": seance.get('promotion', ''),
                    "Début": f"{seance['date'].strftime('%Y-%m-%d')} {seance['heure_debut']}",
                    "Fin": (seance['date'] + pd.Timedelta(minutes=seance['duree'])).strftime("%Y-%m-%d %H:%M"),
                    "Durée": seance['duree']
                })
    
    if not data:
        st.info("Aucune simulation avec simulateur assigné.")
        return
    
    df_gantt = pd.DataFrame(data)
    
    fig = px.timeline(df_gantt, x_start="Début", x_end="Fin", y="Simulateur", 
                      color="Phase", title="Occupation des Simulateurs",
                      labels={"Simulateur": "Simulateur", "Phase": "Phase"})
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,20,30,0.3)",
        font=dict(color="rgba(180,200,220,0.5)", family="JetBrains Mono"),
        title_font=dict(color="#7affb0", size=14),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def section_statut_simulateurs(db):
    """Affiche le statut des simulateurs."""
    st.markdown(f"### 💻 {t('simulateurs')}")
    
    gestionnaire = GestionnaireSimulateursICNA(db)
    stats = gestionnaire.get_stats_occupation()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", stats['total'])
    with col2:
        st.metric("🟢 Disponibles", stats['disponibles'])
    with col3:
        st.metric("🔴 Occupés", stats['occupes'])
    with col4:
        st.metric("📊 Occupation", f"{stats['occupes']/stats['total']*100:.0f}%" if stats['total'] > 0 else "0%")
    
    simulateurs = gestionnaire.get_occupation_simulateurs()
    
    cols = st.columns(2)
    
    for idx, sim in enumerate(simulateurs):
        with cols[idx % 2]:
            sim_type = get_type_simulateur(sim['id'])
            phases = get_phases_simulateur(sim['id'])
            
            type_color = "#2a7a4a" if sim_type == "DEDIE" else "#cc8844"
            type_emoji = "🔒" if sim_type == "DEDIE" else "🔄"
            
            if sim['disponible']:
                status_emoji = "🟢"
                status_text = "Libre"
                bg_color = "rgba(42,122,74,0.1)"
            else:
                status_emoji = "🔴"
                status_text = "Occupé"
                bg_color = "rgba(204,68,68,0.1)"
                phase_info = PHASES_ICNA.get(sim['phase_actuelle'], {})
                phase_nom = phase_info.get('nom', sim['phase_actuelle'])
            
            st.markdown(f"""
            <div style="background:{bg_color};border-radius:8px;padding:12px;margin:6px 0;
                        border-left:3px solid {type_color};">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:700;color:#7affb0;">{sim['nom']}</span>
                        <span style="font-size:0.75em;color:{type_color};margin-left:8px;">
                            {type_emoji} {sim_type}
                        </span>
                    </div>
                    <span>{status_emoji} {status_text}</span>
                </div>
                <div style="font-size:0.8em;color:rgba(180,200,220,0.5);margin-top:4px;">
                    Type: {sim['type']} | Phases: {', '.join([PHASES_ICNA.get(p, {}).get('nom', p) for p in phases])}
                </div>
                {f'<div style="font-size:0.75em;color:#ffcc44;margin-top:2px;">📅 {sim["date_occupation"]} {sim["heure_debut_occupation"]} - {sim["heure_fin_occupation"]}</div>' if not sim['disponible'] else ''}
                {f'<div style="font-size:0.75em;color:rgba(180,200,220,0.4);">👤 {phase_nom} | {sim["promotion_actuelle"]}</div>' if not sim['disponible'] and sim.get('phase_actuelle') else ''}
            </div>
            """, unsafe_allow_html=True)

def section_configuration_simulateurs(db):
    """Interface de configuration des simulateurs par phase."""
    st.markdown("### ⚙️ Configuration des Simulateurs par Phase")
    
    phase_selected = st.selectbox(
        "Choisir une phase",
        list(PHASES_ICNA.keys()),
        format_func=lambda x: PHASES_ICNA[x]['nom']
    )
    
    if phase_selected:
        phase_info = PHASES_ICNA[phase_selected]
        matrice = MATRICE_SHARING.get(phase_selected, {})
        
        st.markdown(f"#### {phase_info['nom']} ({phase_info['niveau']})")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔒 Simulateurs DÉDIÉS :**")
            if matrice.get("simulateurs_dedies"):
                for sim_id in matrice.get("simulateurs_dedies", []):
                    sim_info = SIMULATEURS_ICNA.get(sim_id, {})
                    st.markdown(f"- {sim_info.get('nom', f'Simulateur {sim_id}')}")
            else:
                st.caption("Aucun simulateur dédié")
        
        with col2:
            st.markdown("**🔄 Simulateurs PARTAGÉS :**")
            if matrice.get("simulateurs_partages"):
                for sim_id in matrice.get("simulateurs_partages", []):
                    sim_info = SIMULATEURS_ICNA.get(sim_id, {})
                    phases_partagees = get_phases_simulateur(sim_id)
                    phases_noms = [PHASES_ICNA.get(p, {}).get('nom', p) for p in phases_partagees if p != phase_selected]
                    st.markdown(f"- {sim_info.get('nom', f'Simulateur {sim_id}')} (partagé avec: {', '.join(phases_noms)})")
            else:
                st.caption("Aucun simulateur partagé")
        
        st.markdown("**📊 Résumé :**")
        tous_sim = matrice.get("tous_simulateurs", [])
        st.markdown(f"Total simulateurs pour cette phase: **{len(tous_sim)}**")
        st.markdown(f"- Dédiés: **{len(matrice.get('simulateurs_dedies', []))}**")
        st.markdown(f"- Partagés: **{len(matrice.get('simulateurs_partages', []))}**")
        
        st.markdown("**📋 Matrice de partage :**")
        data = []
        for phase_id in PHASES_ICNA:
            if phase_id == phase_selected:
                continue
            m = MATRICE_SHARING.get(phase_id, {})
            sims = m.get("tous_simulateurs", [])
            sims_noms = [SIMULATEURS_ICNA.get(s, {}).get('nom', f'S{s}') for s in sims]
            
            sims_communs = set(matrice.get("tous_simulateurs", [])) & set(sims)
            if sims_communs:
                communs = [SIMULATEURS_ICNA.get(s, {}).get('nom', f'S{s}') for s in sims_communs]
                partage = "✅ Oui - " + ", ".join(communs)
            else:
                partage = "❌ Non"
            
            data.append({
                "Phase": PHASES_ICNA[phase_id]['nom'],
                "Simulateurs": len(sims),
                "Partage avec": partage
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================
# SECTIONS INSTRUCTEUR - EXISTANTES
# ============================================

def _groupe_name_to_id(db):
    groupes_list = db.get_groupes()
    return {g["nom"]: g["id"] for _, g in groupes_list.iterrows()}

def section_cours_instr(db, instr_id):
    st.markdown(f'<div class="section-title">{t("courses")}</div>', unsafe_allow_html=True)

    with st.expander(t("add_course"), expanded=False):
        with st.form("add_cours_form"):
            titre = st.text_input(t("course_title"))
            description = st.text_area(t("description"))
            uploaded_file = st.file_uploader(t("upload_file"), type=["pdf", "docx", "txt", "md", "pptx", "xlsx"])
            col1, col2 = st.columns(2)
            with col1:
                type_cours = st.selectbox(t("type"), ["document", "pdf", "video", "lien"])
            with col2:
                if uploaded_file:
                    st.success(f"✅ {uploaded_file.name} ({uploaded_file.size // 1024} KB)")
                    contenu = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                else:
                    contenu = st.text_input("URL ou contenu (si pas de fichier)")
            tags = st.text_input(t("tags"))
            g_map = _groupe_name_to_id(db)
            groupe_cible = st.selectbox(t("target_group"), [t("all_groups")] + list(g_map.keys()))
            if st.form_submit_button(t("add")):
                if titre and (contenu or uploaded_file):
                    db.add_cours({
                        "titre": titre, "description": description, "type": type_cours, "contenu": contenu,
                        "date_upload": date.today().strftime("%Y-%m-%d"), "instructeur_id": instr_id,
                        "groupe_cible_id": None if groupe_cible == t("all_groups") else g_map[groupe_cible],
                        "tags": tags
                    })
                    st.success("✅ Cours ajouté")
                    st.rerun()
                else:
                    st.error(t("content_required"))

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
            if st.button(t("delete"), key=f"del_cours_{c['id']}", use_container_width=True):
                db.delete_cours(c["id"])
                st.rerun()

def section_scenarios_instr(db, instr_id):
    st.markdown(f'<div class="section-title">{t("scenarios")}</div>', unsafe_allow_html=True)

    with st.expander(t("add_scenario"), expanded=False):
        with st.form("add_scenario_form"):
            titre = st.text_input("Titre du scénario")
            description = st.text_area(t("description"))
            objectifs = st.text_area("Objectifs pédagogiques")
            duree = st.number_input("Durée estimée (minutes)", min_value=5, value=45)
            niveau = st.selectbox("Niveau", ["debutant", "intermediaire", "avance"])
            sim_requis = st.checkbox("Simulateur requis")
            instructions = st.text_area("Instructions")
            uploaded_file = st.file_uploader(t("upload_file"), type=["pdf", "docx", "txt", "md", "pptx", "xlsx"], key="upload_scenario")
            col1, col2 = st.columns(2)
            with col1:
                type_scenario = st.selectbox(t("type"), ["document", "pdf", "video", "lien"])
            with col2:
                if uploaded_file:
                    contenu = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                else:
                    contenu = st.text_input("URL ou contenu")
            tags = st.text_input(t("tags"))
            g_map = _groupe_name_to_id(db)
            groupe_cible = st.selectbox(t("target_group"), [t("all_groups")] + list(g_map.keys()))
            if st.form_submit_button(t("add")):
                if titre:
                    db.add_scenario({
                        "titre": titre, "description": description, "objectifs": objectifs,
                        "duree_estimee": duree, "niveau": niveau, "simulateur_requis": sim_requis,
                        "instructions": instructions, "contenu": contenu, "type": type_scenario,
                        "date_creation": date.today().strftime("%Y-%m-%d"), "instructeur_id": instr_id,
                        "groupe_cible_id": None if groupe_cible == t("all_groups") else g_map[groupe_cible],
                        "tags": tags
                    })
                    st.success("✅ Scénario ajouté")
                    st.rerun()
                else:
                    st.error(t("title_required"))

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
            if st.button(t("delete"), key=f"del_scenario_{s['id']}", use_container_width=True):
                db.delete_scenario(s["id"])
                st.rerun()

def section_td_instr(db, instr_id):
    st.markdown(f'<div class="section-title">{t("td")}</div>', unsafe_allow_html=True)

    with st.expander(t("add_td"), expanded=False):
        with st.form("add_td_form"):
            titre = st.text_input("Titre du TD")
            description = st.text_area(t("description"))
            uploaded_file = st.file_uploader(t("upload_file"), type=["pdf", "docx", "txt", "md", "pptx", "xlsx"], key="upload_td")
            col1, col2 = st.columns(2)
            with col1:
                type_td = st.selectbox(t("type"), ["exercice", "corrige", "serie", "devoir"])
            with col2:
                if uploaded_file:
                    contenu = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                else:
                    contenu = st.text_input("URL ou contenu")
            tags = st.text_input(t("tags"))
            g_map = _groupe_name_to_id(db)
            groupe_cible = st.selectbox(t("target_group"), [t("all_groups")] + list(g_map.keys()))
            if st.form_submit_button(t("add")):
                if titre and (contenu or uploaded_file):
                    db.add_td({
                        "titre": titre, "description": description, "type": type_td, "contenu": contenu,
                        "date_upload": date.today().strftime("%Y-%m-%d"), "instructeur_id": instr_id,
                        "groupe_cible_id": None if groupe_cible == t("all_groups") else g_map[groupe_cible],
                        "tags": tags
                    })
                    st.success("✅ TD ajouté")
                    st.rerun()
                else:
                    st.error(t("content_required"))

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
            if st.button(t("delete"), key=f"del_td_{td['id']}", use_container_width=True):
                db.delete_td(td["id"])
                st.rerun()

def section_evals_instr(db, instr_id):
    st.markdown(f'<div class="section-title">{t("evaluations")}</div>', unsafe_allow_html=True)

    with st.expander("📋 Gérer les grilles d'évaluation", expanded=False):
        with st.form("add_grille_form"):
            nom = st.text_input("Nom de la grille")
            description = st.text_area(t("description"))
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
        st.info(t("no_students"))
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
            simulation = st.selectbox(t("simulation"), list(sim_name_to_id.keys()))
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
                if st.button(t("delete"), key=f"del_note_{n['id']}"):
                    db.delete_note(n['id'])
                    st.rerun()
        if st.button(f"{t('delete')} {t('all_groups')}", key=f"del_all_notes_{eleve_id}", use_container_width=True):
            db.delete_notes_eleve(eleve_id)
            st.rerun()

def section_planning_instr(db):
    st.markdown(f'<div class="section-title">{t("planning")}</div>', unsafe_allow_html=True)
    seances = db.get_seances()
    if seances.empty:
        st.info("Aucun planning généré.")
        return

    groupes_df = db.get_groupes()
    groupe_options = [t("all_groups")] + (groupes_df["nom"].tolist() if not groupes_df.empty else [])
    type_options = {t("all_groups"): None, t("briefing"): "briefing", t("simulation"): "simulation", t("debriefing"): "debriefing"}

    col1, col2 = st.columns(2)
    with col1:
        groupe_choisi = st.selectbox(t("group"), groupe_options)
    with col2:
        type_label_choisi = st.selectbox(t("type"), list(type_options.keys()))

    filtered = seances.copy()
    if groupe_choisi != t("all_groups"):
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
    st.markdown(f'<div class="section-title">{t("groups")}</div>', unsafe_allow_html=True)
    groupes = db.get_groupes()
    if groupes.empty:
        st.info("Aucun groupe généré.")
        return
    for _, g in groupes.iterrows():
        membres = db.get_groupe_eleves(g["id"])
        chips = "".join([f'<span class="eleve-chip">📌 {esc(m["prenom"])} {esc(m["nom"])}</span>' for _, m in membres.iterrows()])
        phase = g.get("phase", "")
        phase_nom = PHASES_ICNA.get(phase, {}).get('nom', phase)
        
        st.markdown(f"""
        <div class="groupe-card">
            <h4>🏷️ {esc(g['nom'])}</h4>
            <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
                <span class="instructeur-badge">👤 {t('instructor_label')} : {esc(g['instructeur_nom'])}</span>
                <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                            border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                    💻 {t('simulator_label')} {g['simulateur_id']}
                </span>
                <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                            border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                    🛫 {phase_nom}
                </span>
                <span style="display:inline-block;background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.04);
                            border-radius:16px;padding:4px 12px;font-size:0.8em;color:rgba(180,200,220,0.4);">
                    👨‍🎓 {len(membres)} {t('students_count')}
                </span>
            </div>
            <div>{chips if chips else f'<span style="color:rgba(180,200,220,0.3);">{t("no_students_in_group")}</span>'}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# PAGE GÉNÉRATEUR AVEC MULTI-PHASES
# ============================================

def page_generateur():
    st.markdown(f'<div class="section-title">{t("generator")}</div>', unsafe_allow_html=True)
    db = Database()
    config = db.get_config()
    eleves = db.get_eleves()
    instructeurs = db.get_instructeurs()

    if not config:
        st.warning("⚠️ Configurez d'abord l'application")
        return
    if eleves.empty:
        st.warning(t("no_students"))
        return
    if instructeurs.empty:
        st.warning(t("no_instructors"))
        return
    if len(instructeurs) < 2:
        st.warning("⚠️ Il faut au moins 2 instructeurs")
        return

    date_debut = config['date_debut']
    date_fin_souhaitee = config['date_fin_souhaitee']
    
    # Afficher les promotions
    promo_counts = eleves.groupby('promotion').size().to_dict()
    promo_text = " | ".join([f"{PROMOTIONS.get(p, {}).get('nom', p)}: {c}" for p, c in promo_counts.items()])
    
    st.info(f"👨‍🎓 {len(eleves)} {t('students')} ({promo_text}) | 👨‍🏫 {len(instructeurs)} {t('instructors')} | 📅 {date_debut} → {date_fin_souhaitee}")
    
    col1, col2 = st.columns(2)
    with col1:
        generer_multiphases = st.checkbox("📊 Générer planning multi-phases (5 phases)", value=True)
    
    if st.button(t("generate_planning"), type="primary"):
        with st.spinner("🔄 Génération du planning multi-phases..."):
            try:
                db.reset_planning()
                
                if generer_multiphases:
                    seances = generer_planning_multiphases(config, eleves, instructeurs)
                else:
                    from datetime import datetime as dt
                    import random as rd
                    # Génération simple (fallback)
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
                
                nb_sim = len([s for s in seances if s["type"] == "simulation"])
                st.success(f"✅ {t('planning_generated')} - {nb_sim} simulations planifiées")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")

# ============================================
# PAGE PERSONNES - VERSION AVEC PROMOTIONS ET PHASES
# ============================================

def section_personnes_instr(db):
    st.markdown(f'<div class="section-title">{t("people")}</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs([t("students"), t("instructors")])
    
    with tab1:
        st.markdown("### 👨‍🎓 Gestion des Élèves")
        
        if st.session_state.get("temp_pwd_eleve"):
            st.info(f"🔑 Compte créé. Mot de passe temporaire : **{st.session_state['temp_pwd_eleve']}**")
            del st.session_state["temp_pwd_eleve"]
        if st.session_state.get("reset_pwd_eleve"):
            st.info(f"🔄 Mot de passe réinitialisé : **{st.session_state['reset_pwd_eleve']}**")
            del st.session_state["reset_pwd_eleve"]
        
        with st.form("add_eleve_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                nom = st.text_input("Nom")
            with col2:
                prenom = st.text_input("Prénom")
            with col3:
                promotion = st.selectbox("Promotion", list(PROMOTIONS.keys()), format_func=lambda x: PROMOTIONS[x]['nom'])
            mot_de_passe_initial = st.text_input(
                "Mot de passe initial (laisser vide pour génération automatique)",
                type="password", key="pwd_new_eleve"
            )
            if st.form_submit_button("➕ Ajouter"):
                if nom and prenom:
                    new_id, temp_pwd = db.add_eleve(nom, prenom, password=mot_de_passe_initial or None, promotion=promotion)
                    if temp_pwd:
                        st.session_state["temp_pwd_eleve"] = temp_pwd
                    st.success("✅ Élève ajouté")
                    st.rerun()
        
        eleves = db.get_eleves()
        if not eleves.empty:
            # Afficher par promotion
            for promo_id in PROMOTIONS:
                eleves_promo = eleves[eleves['promotion'] == promo_id]
                if not eleves_promo.empty:
                    st.markdown(f"**{PROMOTIONS[promo_id]['nom']}**")
                    for _, row in eleves_promo.iterrows():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        with col1:
                            st.write(f"👤 {row['prenom']} {row['nom']}")
                        with col2:
                            st.caption(f"Phase: {', '.join(PROMOTIONS[promo_id]['phases'])}")
                        with col3:
                            if st.button("🔄", key=f"reset_eleve_{row['id']}"):
                                new_temp = generate_temp_password()
                                db.set_password_eleve(row['id'], new_temp)
                                st.session_state["reset_pwd_eleve"] = new_temp
                                st.rerun()
                        with col4:
                            if st.button("🗑️", key=f"del_eleve_{row['id']}"):
                                db.delete_eleve(row['id'])
                                st.rerun()
    
    with tab2:
        st.markdown("### 👨‍🏫 Gestion des Instructeurs")
        
        if st.session_state.get("temp_pwd_instr"):
            st.info(f"🔑 Compte créé. Mot de passe temporaire : **{st.session_state['temp_pwd_instr']}**")
            del st.session_state["temp_pwd_instr"]
        if st.session_state.get("reset_pwd_instr"):
            st.info(f"🔄 Mot de passe réinitialisé : **{st.session_state['reset_pwd_instr']}**")
            del st.session_state["reset_pwd_instr"]
        
        with st.form("add_instructeur_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                nom = st.text_input("Nom")
            with col2:
                prenom = st.text_input("Prénom")
            with col3:
                phase = st.selectbox("Phase", list(PHASES_ICNA.keys()), format_func=lambda x: PHASES_ICNA[x]['nom'])
            mot_de_passe_initial = st.text_input(
                "Mot de passe initial (laisser vide pour génération automatique)",
                type="password", key="pwd_new_instr"
            )
            if st.form_submit_button("➕ Ajouter"):
                if nom and prenom:
                    new_id, temp_pwd = db.add_instructeur_phase(nom, prenom, phase, password=mot_de_passe_initial or None)
                    if temp_pwd:
                        st.session_state["temp_pwd_instr"] = temp_pwd
                    st.success("✅ Instructeur ajouté")
                    st.rerun()
        
        instrs = db.get_instructeurs()
        if not instrs.empty:
            # Afficher par phase
            for phase_id in PHASES_ICNA:
                instrs_phase = instrs[instrs['phase'] == phase_id]
                if not instrs_phase.empty:
                    st.markdown(f"**{PHASES_ICNA[phase_id]['nom']}**")
                    for _, row in instrs_phase.iterrows():
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
    with st.expander(t("danger_zone")):
        confirm = st.checkbox(t("confirm_delete"))
        if st.button(t("delete_all"), disabled=not confirm):
            db.delete_all_data()
            st.success("✅ Toutes les données ont été supprimées")
            st.rerun()

# ============================================
# MAIN
# ============================================

def main():
    # Initialisation des variables de session
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["login_role"] = None
        st.session_state["language"] = "🇫🇷 Français"
        st.session_state["mobile_mode"] = False
        st.session_state["is_mobile"] = is_mobile_device()

    # Sélecteur de langue dans la sidebar
    with st.sidebar:
        st.markdown(f"### {t('language')}")
        lang = st.selectbox(
            "",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.get("language", "🇫🇷 Français"))
        )
        if lang != st.session_state.get("language"):
            st.session_state["language"] = lang
            st.rerun()

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
            pages = {
                t("my_group"): "Groupe",
                t("courses"): "Cours",
                t("scenarios"): "Scenarios",
                t("td"): "TD",
                t("my_planning"): "Planning",
                t("my_notes"): "Notes",
                t("my_password"): "MotDePasse"
            }
        else:
            pages = {
                t("people"): "Personnes",
                t("config"): "Config",
                t("generator"): "Generateur",
                t("multi_phases"): "MultiPhases",
                t("gantt"): "Gantt",
                t("simulateurs"): "Simulateurs",
                t("config_simulateurs"): "ConfigSimulateurs",
                t("planning"): "Planning_Instr",
                t("courses"): "Cours_Instr",
                t("scenarios"): "Scenarios_Instr",
                t("td"): "TD_Instr",
                t("evaluations"): "Evals",
                t("groups"): "Groupes_Instr",
                t("my_password"): "MotDePasse_Instr"
            }

        selection = st.radio("Navigation", list(pages.keys()))
        page = pages[selection]

        st.markdown("---")
        
        if st.button(t("mobile_mode"), use_container_width=True):
            st.session_state["mobile_mode"] = not st.session_state.get("mobile_mode", False)
            st.rerun()
        
        if st.session_state.get("mobile_mode", False):
            st.info(t("mobile_mode_active"))
        
        st.markdown("---")
        if st.button(t("logout"), use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user"] = {}
            st.rerun()

    if role == "eleve":
        eleve_id = user.get("id")
        header_eleve(user)
        
        if st.session_state.get("mobile_mode", False):
            tabs = st.tabs(list(pages.keys()))
            tab_pages = list(pages.values())
            for tab, page_name in zip(tabs, tab_pages):
                with tab:
                    if page_name == "Groupe":
                        section_groupe_eleve(db, eleve_id)
                    elif page_name == "Cours":
                        section_cours_eleve(db.get_cours(eleve_id))
                    elif page_name == "Scenarios":
                        section_scenarios_eleve(db.get_scenarios(eleve_id))
                    elif page_name == "TD":
                        section_td_eleve(db.get_td(eleve_id))
                    elif page_name == "Planning":
                        section_planning_eleve(db, db.get_seances_eleve(eleve_id), eleve_id, f"{user.get('prenom','')} {user.get('nom','')}")
                    elif page_name == "Notes":
                        section_notes_eleve(db.get_notes_eleve(eleve_id))
                    elif page_name == "MotDePasse":
                        section_mon_mot_de_passe(db, "eleve", eleve_id)
        else:
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

    if st.session_state.get("mobile_mode", False):
        tabs = st.tabs(list(pages.keys()))
        tab_pages = list(pages.values())
        for tab, page_name in zip(tabs, tab_pages):
            with tab:
                if page_name == "Personnes":
                    section_personnes_instr(db)
                elif page_name == "Config":
                    # Configuration simplifiée pour mobile
                    st.markdown(f'<div class="section-title">{t("config")}</div>', unsafe_allow_html=True)
                    st.info("📱 Version mobile - Configuration")
                elif page_name == "Generateur":
                    page_generateur()
                elif page_name == "MultiPhases":
                    section_visualisation_phases(db)
                elif page_name == "Gantt":
                    afficher_gantt_simulateurs(db)
                elif page_name == "Simulateurs":
                    section_statut_simulateurs(db)
                elif page_name == "ConfigSimulateurs":
                    section_configuration_simulateurs(db)
                elif page_name == "Planning_Instr":
                    section_planning_instr(db)
                elif page_name == "Cours_Instr":
                    section_cours_instr(db, instr_id)
                elif page_name == "Scenarios_Instr":
                    section_scenarios_instr(db, instr_id)
                elif page_name == "TD_Instr":
                    section_td_instr(db, instr_id)
                elif page_name == "Evals":
                    section_evals_instr(db, instr_id)
                elif page_name == "Groupes_Instr":
                    section_groupes_instr(db)
                elif page_name == "MotDePasse_Instr":
                    section_mon_mot_de_passe(db, "instructeur", instr_id)
        return

    # Mode desktop normal - Instructeur
    if page == "Personnes":
        header_instructeur(user)
        section_personnes_instr(db)

    elif page == "Config":
        header_instructeur(user)
        st.markdown(f'<div class="section-title">{t("config")}</div>', unsafe_allow_html=True)
        with st.form("config_form"):
            col1, col2 = st.columns(2)
            with col1:
                date_debut = st.date_input(t("date"), value=date.today())
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
                st.success(t("config_saved"))

    elif page == "Generateur":
        header_instructeur(user)
        page_generateur()
    
    elif page == "MultiPhases":
        header_instructeur(user)
        section_visualisation_phases(db)
    
    elif page == "Gantt":
        header_instructeur(user)
        afficher_gantt_simulateurs(db)
    
    elif page == "Simulateurs":
        header_instructeur(user)
        section_statut_simulateurs(db)
    
    elif page == "ConfigSimulateurs":
        header_instructeur(user)
        section_configuration_simulateurs(db)
    
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
