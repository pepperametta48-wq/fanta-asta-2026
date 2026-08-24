import streamlit as st
import pandas as pd
import numpy as np
import json
import io
import os
import requests
import feedparser
from datetime import datetime

# ==============================================================================
# 1. SETUP GENERALE & THEME STYLING
# ==============================================================================
st.set_page_config(
    page_title="FantaAsta 2026/27 Pro Master Suite",
    layout="wide",
    page_icon="⚽",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 15% 15%, #0f172a 0%, #0b0f19 55%, #050811 100%);
        color: #f8fafc;
    }
    
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(148, 163, 184, 0.15);
        padding: 16px 20px;
        border-radius: 14px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(12px);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #f8fafc !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.65);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.12);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 18px;
        font-weight: 600;
        color: #94a3b8;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
    }

    .pitch-container {
        background: linear-gradient(to bottom, #15803d 0%, #166534 50%, #15803d 100%);
        background-size: 100% 40px;
        border: 3px solid #f8fafc;
        border-radius: 18px;
        padding: 24px 16px;
        position: relative;
        box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.5), 0 10px 30px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }
    .pitch-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin: 18px 0;
    }
    .player-disc {
        background: rgba(15, 23, 42, 0.85);
        border: 2px solid #60a5fa;
        color: #ffffff;
        border-radius: 14px;
        padding: 8px 14px;
        text-align: center;
        min-width: 120px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        backdrop-filter: blur(6px);
    }
    .player-disc-empty {
        background: rgba(30, 41, 59, 0.5);
        border: 2px dashed #94a3b8;
        color: #cbd5e1;
        border-radius: 14px;
        padding: 8px 14px;
        text-align: center;
        min-width: 120px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. COSTANTI DI GIOCO & BENCHMARK FANTALAB (10 SQUADRE / 500 CR)
# ==============================================================================
SAVE_FILE = "fanta_auction_save.json"
TOTAL_BUDGET = 500
SLOTS = {'P': 3, 'D': 8, 'C': 8, 'A': 6}
TOTAL_SLOTS = sum(SLOTS.values())
BASE_DEPT_BUDGET = {'P': 35, 'D': 95, 'C': 155, 'A': 215}

BASELINE_DEPT_CURVES = {
    'P': [20, 3, 1],
    'D': [38, 16, 12, 10, 8, 8, 2, 1],
    'C': [55, 48, 20, 11, 8, 7, 4, 2],
    'A': [90, 75, 38, 15, 6, 2]
}

PENALTY_TAKERS = {
    "Inter": ["Calhanoglu (1° - 89%)", "Zielinski (2°)", "Martinez L. (3°)"],
    "Genoa": ["Colombo (1°)", "Vitinha (2°)", "Ostigard (3°)"],
    "Como": ["Da Cunha (1°)", "Douvikas (2°)", "Paz N. (3°)"],
    "Napoli": ["De Bruyne (1°)", "Hojlund (2°)", "McTominay (3°)"],
    "Milan": ["Nkunku (1°)", "Pulisic (2°)", "Gonçalo Ramos (3°)"],
    "Juventus": ["Kolo Muani (1°)", "Yildiz (2°)", "Locatelli (3°)"],
    "Bologna": ["Orsolini (1°)", "Bernardeschi (2°)", "Dovbyk (3°)"],
    "Fiorentina": ["Gudmundsson (1°)", "Pellegrino (2°)", "Kean (3°)"],
    "Lazio": ["Zaccagni (1°)", "Taylor K. (2°)", "Cataldi (3°)"],
    "Roma": ["Malen (1°)", "Dybala (2°)", "Castro (3°)"],
    "Sassuolo": ["Berardi (1°)", "Pinamonti (2°)", "Lauriente' (3°)"],
    "Torino": ["Vlasic (1°)", "Simeone (2°)", "Casadei (3°)"],
    "Udinese": ["Davis (1°)", "Solet (2°)", "Zaniolo (3°)"],
    "Cagliari": ["Mina (1°)", "Carlos K. (2°)", "Maldini D. (3°)"],
    "Monza": ["Pessina (1°)", "Cutrone (2°)", "Petagna (3°)"],
    "Parma": ["Bernabè (1°)", "Tourè E. (2°)", "Valeri (3°)"],
    "Lecce": ["Stulic (1°)", "Geubbels (2°)", "Berisha (3°)"],
    "Frosinone": ["Calò (1°)", "Schmid (2°)"],
    "Venezia": ["Adams A. (1°)", "Rrahmani A. (2°)", "Yeboah (3°)"],
    "Atalanta": ["Scamacca (1°)", "Samardzic (2°)", "De Ketelaere (3°)"]
}

SERIE_A_LOGOS = {
    "Inter": "505", "Milan": "489", "Juventus": "496", "Roma": "497",
    "Napoli": "492", "Atalanta": "499", "Lazio": "487", "Fiorentina": "502",
    "Bologna": "500", "Torino": "503", "Sassuolo": "488", "Genoa": "495",
    "Udinese": "494", "Lecce": "867", "Cagliari": "490", "Monza": "1579",
    "Frosinone": "501", "Como": "882", "Parma": "523", "Venezia": "517"
}

def get_team_logo_url(team_name):
    team_id = SERIE_A_LOGOS.get(team_name, "505")
    return f"https://media.api-sports.io/football/teams/{team_id}.png"

GOALKEEPER_PAIRINGS = {
    'Inter': [
        {"club": "Monza", "starter": "Thiam", "target": 5, "max": 7, "diff": "🟢🟢 Alternanza 100% (Low-Cost)", "reason": "Derby lombardo alternato, spesa minima (5 cr), garantisce sempre 1 partita in casa."},
        {"club": "Bologna", "starter": "Skorupski", "target": 17, "max": 21, "diff": "🟢🟢 Ottimo Incrocio + Modificatore", "reason": "Tedesco 4-3-3 compatto, Skorupski affidabile con ottima alternanza contro le big."},
        {"club": "Lecce", "starter": "Falcone", "target": 12, "max": 15, "diff": "🟢 Specialista Modificatore", "reason": "Falcone para moltissimo e prende 6.5/7 anche sotto pressione, perfetto nei big match."},
        {"club": "Genoa", "starter": "Bijlow", "target": 9, "max": 12, "diff": "🟢 Alternanza Favorevole", "reason": "De Rossi organizza bene la difesa, ottima copertura per i turni fuori casa dell'Inter."},
        {"club": "Como", "starter": "Butez", "target": 31, "max": 36, "diff": "🟢🟢 Coppia Top Clean Sheet", "reason": "Record 19 clean sheet Como + Inter blindata. Se il budget lo permette, imbattibilità totale."}
    ],
    'Milan': [
        {"club": "Monza", "starter": "Thiam", "target": 5, "max": 7, "diff": "🟢🟢 Alternanza Perfetta", "reason": "Vicinanza e incrocio calendario favorevole a costi minimi."},
        {"club": "Bologna", "starter": "Skorupski", "target": 17, "max": 21, "diff": "🟢 Ottima Copertura", "reason": "Incroci favorevoli nei big match di Amorim."}
    ],
    'Juventus': [
        {"club": "Torino", "starter": "Perri", "target": 5, "max": 7, "diff": "🟢🟢 Alternanza 100% (Cittadina)", "reason": "Stesso stadio/città, alternanza casa-trasferta al 100% a costo budget minimo."},
        {"club": "Genoa", "starter": "Bijlow", "target": 9, "max": 12, "diff": "🟢 Ottimo Incrocio", "reason": "Incrocio calendario ideale con la Juventus di Spalletti."}
    ],
    'Roma': [
        {"club": "Lazio", "starter": "Mandas", "target": 15, "max": 19, "diff": "🟢🟢 Alternanza 100% (Olimpico)", "reason": "Stesso stadio (Olimpico), alternanza perfetta casa-fuori a 38/38 giornate."},
        {"club": "Fiorentina", "starter": "De Gea", "target": 21, "max": 25, "diff": "🟢 Ottima Qualità", "reason": "Doppio portiere di livello europeo per modificatore di difesa."}
    ],
    'Napoli': [
        {"club": "Cagliari", "starter": "Caprile", "target": 10, "max": 13, "diff": "🟢🟢 Ottimo Incrocio Storico", "reason": "Incroci calendario ideali con il Napoli di Allegri, Caprile garanzia voti."}
    ],
    'Atalanta': [
        {"club": "Como", "starter": "Butez", "target": 31, "max": 36, "diff": "🟢🟢 Incrocio Lombardo", "reason": "Vicinanza e solidità eccellente."}
    ]
}

GOALIE_HIERARCHY = {
    'Inter': [('Martinez Jo.', 34, 39), ('Provedel', 8, 10), ('Di Gennaro', 1, 1)],
    'Roma': [('Svilar', 49, 56), ('Gollini', 1, 2), ('De Marzi', 1, 1)],
    'Como': [('Butez', 31, 36), ('Tornqvist', 1, 2), ('Vigorito', 1, 1)],
    'Juventus': [('Vicario', 39, 45), ('Perin', 5, 7), ('Pinsoglio', 1, 1)],
    'Atalanta': [('Carnesecchi', 34, 40), ('Sportiello', 1, 2), ('Vismara', 1, 1)],
    'Milan': [('Maignan', 42, 48), ('Terracciano', 1, 2), ('Torriani', 1, 1)],
    'Fiorentina': [('De Gea', 21, 25), ('Christensen O.', 1, 2), ('Lezzerini', 1, 1)],
    'Napoli': [('Meret', 28, 33), ('Milinkovic-Savic V.', 11, 14), ('Contini', 1, 1)],
    'Bologna': [('Skorupski', 17, 21), ('Pessina Mas.', 1, 2), ('Happonen', 1, 1)],
    'Lazio': [('Mandas', 15, 19), ('Motta', 1, 2), ('Renzetti', 1, 1)],
    'Udinese': [('Okoye', 14, 17), ('Padelli', 1, 2), ('Piana', 1, 1)],
    'Cagliari': [('Caprile', 10, 13), ('Sherri', 1, 2), ('Radunovic', 1, 1)],
    'Lecce': [('Falcone', 12, 15), ('Bleve', 1, 2), ('Penev', 1, 1)],
    'Genoa': [('Bijlow', 9, 12), ('Stolz', 1, 2), ('Sommariva', 1, 1)],
    'Sassuolo': [('Muric', 5, 7), ('Turati', 1, 2), ('Russo A.', 1, 1)],
    'Torino': [('Perri', 5, 7), ('Paleari', 5, 7), ('Siviero', 1, 1)],
    'Monza': [('Thiam', 4, 6), ('Pizzignacco', 1, 1), ('Strajnar', 1, 1)],
    'Parma': [('Corvi', 4, 6), ('Daffara', 4, 6), ('Rinaldi', 1, 1)],
    'Frosinone': [('Palmisani', 3, 5), ('Desplanches', 2, 3), ('Lolic', 1, 1)],
    'Venezia': [('Stankovic F.', 4, 6), ('Grandi', 1, 1), ('Pozzi', 1, 1)]
}

DOC_TARGETS = {
    "Svilar Mile": 48.5, "Svilar": 48.5, "Maignan Mike": 42.0, "Maignan": 42.0, "Vicario Guglielmo": 39.0, "Vicario": 39.0,
    "Martinez Josep": 34.0, "Martinez Jo.": 34.0, "Carnesecchi Marco": 33.5, "Carnesecchi": 33.5, "Butez Jean": 31.0, "Butez": 31.0,
    "Meret Alex": 27.5, "Meret": 27.5, "De Gea David": 21.0, "De Gea": 21.0, "Skorupski Lukasz": 17.0, "Skorupski": 17.0,
    "Mandas Christos": 15.0, "Mandas": 15.0, "Okoye Maduka": 13.5, "Okoye": 13.5, "Falcone Wladimiro": 11.5, "Falcone": 11.5,
    "Caprile Elia": 9.5, "Caprile": 9.5, "Bijlow Justin": 8.5, "Bijlow": 8.5, "Milinkovic-Savic Vanja": 10.5, "Milinkovic-Savic V.": 10.5,
    "Provedel Ivan": 7.5, "Provedel": 7.5, "Muric Arijanet": 5.0, "Muric": 5.0, "Corvi Edoardo": 4.0, "Corvi": 4.0,
    "Perri Lucas": 4.5, "Perri": 4.5, "Thiam Demba": 3.5, "Thiam": 3.5, "Stankovic Filip": 3.5, "Stankovic F.": 3.5,
    "Dimarco Federico": 52.0, "Dimarco": 52.0, "Bremer Gleison": 38.0, "Bremer": 38.0, "Mancini Gianluca": 32.0, "Mancini": 32.0,
    "Wesley França": 30.0, "Wesley": 30.0, "Bastoni Alessandro": 26.0, "Bastoni": 26.0, "Pavlovic Strahinja": 26.0, "Pavlovic": 26.0,
    "Solet Oumar": 25.0, "Solet": 25.0, "Akanji Manuel": 24.0, "Akanji": 24.0, "Cambiaso Andrea": 23.0, "Cambiaso": 23.0,
    "Bisseck Yann": 23.0, "Bisseck": 23.0, "Di Lorenzo Giovanni": 22.0, "Di Lorenzo": 22.0, "Rrahmani Amir": 21.0, "Rrahmani": 21.0,
    "Scalvini Giorgio": 20.0, "Scalvini": 20.0, "Kempf Marc Oliver": 18.5, "Kempf": 18.5, "Ostigard Leo": 18.0, "Ostigard": 18.0,
    "Kalulu Pierre": 16.0, "Kalulu": 16.0, "Ndicka Evan": 15.5, "Ndicka": 15.5, "Gila Mario": 14.5, "Gila": 14.5,
    "Yan Couto": 16.0, "Molina Nahuel": 16.0, "Molina N.": 16.0, "Dragusin Radu": 15.0, "Dragusin": 15.0,
    "Spinazzola Leonardo": 14.0, "Spinazzola": 14.0, "Chalobah Trevoh": 13.5, "Chalobah": 13.5, "Miranda Juan": 12.5, "Miranda": 12.5,
    "Dodò": 12.0, "Dodo": 12.0, "Mina Yerry": 11.0, "Mina": 11.0, "Doekhi Danilho": 10.5, "Doekhi": 10.5,
    "Vojvoda Mergim": 10.0, "Vojvoda": 10.0, "Kaiki Bruno": 8.0, "Kaiki": 8.0, "Rensch Devyne": 8.0, "Rensch": 8.0,
    "Heggem Torbjorn": 7.0, "Heggem": 7.0, "Ahanor Honest": 7.0, "Ahanor": 7.0, "Ziolkowski Jan": 1.0, "Ziolkowski": 1.0,
    "Paz Nico": 87.75, "Nico Paz": 87.75, "McTominay Scott": 68.94, "McTominay": 68.94, "Orsolini Riccardo": 58.0, "Orsolini": 58.0,
    "Calhanoglu Hakan": 68.81, "Calhanoglu": 68.81, "De Bruyne Kevin": 46.0, "De Bruyne": 46.0, "Rabiot Adrien": 44.0, "Rabiot": 44.0,
    "Da Cunha Lucas": 32.0, "Da Cunha": 32.0, "Barella Nicolo'": 33.0, "Barella": 33.0, "Atta Arthur": 30.0, "Atta": 30.0,
    "Baturina Martin": 29.0, "Baturina": 29.0, "Politano Matteo": 28.0, "Politano": 28.0, "Zielinski Piotr": 26.0, "Zielinski": 26.0,
    "Ederson Dos Santos": 26.0, "Ederson": 26.0, "McKennie Weston": 25.0, "McKennie": 25.0, "Mastantuono Franco": 24.0, "Mastantuono": 24.0,
    "Vlasic Nikola": 24.0, "Vlasic": 24.0, "Moreira Diego": 22.0, "Diego Moreira": 22.0, "Gaetano Gianluca": 21.0, "Gaetano": 21.0,
    "Saelemaekers Alexis": 20.0, "Saelemaekers": 20.0, "Rowe Jonathan": 20.0, "Rowe": 20.0, "Sucic Petar": 19.0, "Sucic": 19.0,
    "Thorstvedt Kristian": 19.0, "Thorstvedt": 19.0, "Casadei Cesare": 18.0, "Casadei": 18.0, "Zaniolo Nicolo'": 19.0, "Zaniolo": 19.0,
    "Perrone Maximo": 14.0, "Perrone": 14.0, "Manu Koné": 15.0, "Koné M.": 15.0, "Frattesi Davide": 17.0, "Frattesi": 17.0,
    "Locatelli Manuel": 12.0, "Locatelli": 12.0, "Lobotka Stanislav": 10.0, "Lobotka": 10.0, "Diouf Andy": 11.0, "Diouf": 11.0,
    "Adzic Vasilije": 8.0, "Adzic": 8.0, "Busio Gianluca": 8.0, "Busio": 8.0, "El Azzouzi Anouar": 2.0, "El Azzouzi A.": 2.0, "Lahdo Adrian": 2.0,
    "Martinez Lautaro": 129.36, "Lautaro Martinez": 129.36, "Martinez L.": 129.36, "Malen Donyell": 113.9, "Malen": 113.9,
    "Thuram Marcus": 116.02, "Thuram": 116.02, "Ramos Gonçalo": 102.37, "Ramos G.": 102.37, "Gonçalo Ramos": 102.37,
    "Hojlund Rasmus": 83.25, "Hojlund": 83.25, "Kolo Muani Randal": 109.48, "Kolo Muani": 109.48, "Kean Moise": 84.44, "Kean": 84.44,
    "Yildiz Kenan": 82.0, "Yildiz": 82.0, "Pulisic Christian": 62.45, "Pulisic": 62.45, "Douvikas Anastasios": 72.0, "Douvikas": 72.0,
    "Scamacca Gianluca": 66.0, "Scamacca": 66.0, "Dybala Paulo": 62.0, "Dybala": 62.0, "Leão Rafael": 70.0, "Leao": 70.0,
    "Krstovic Nikola": 48.0, "Krstovic": 48.0, "Dovbyk Artem": 52.0, "Dovbyk": 52.0, "Nkunku Christopher": 55.85, "Nkunku": 55.85,
    "Simeone Giovanni": 39.0, "Simeone": 39.0, "Davis Keinan": 34.0, "Davis K.": 34.0, "Berardi Domenico": 45.0, "Berardi": 45.0,
    "Gudmundsson Albert": 40.0, "Gudmundsson": 40.0, "Castro Santiago": 34.0, "Castro": 34.0, "Piccoli Roberto": 25.0, "Piccoli": 25.0,
    "Noslin Tijjani": 25.0, "Noslin": 25.0, "Raspadori Giacomo": 24.0, "Raspadori": 24.0, "Pellegrino Mateo": 22.0, "Pellegrino": 22.0,
    "Touré El Bilal": 18.0, "Tourè E.": 18.0, "Cutrone Patrick": 21.0, "Cutrone": 21.0, "Akor Adams": 20.0, "Adams A.": 20.0,
    "Esposito Francesco Pio": 14.0, "Esposito F.P.": 14.0, "Bonny Ange-Yoan": 12.0, "Bonny": 12.0, "Kevin Carlos": 11.0, "Carlos K.": 11.0
}

ROLE_TIERED_POOLS = {
    'P': [
        {"tier_label": "Top Clean Sheet", "min_p": 25, "max_p": 50, "candidates": [
            {"name": "Svilar", "team": "Roma", "base_target": 49, "max": 56, "role": "Top Clean Sheet (18 CS)"},
            {"name": "Maignan", "team": "Milan", "base_target": 42, "max": 48, "role": "Top Portiere Amorim"},
            {"name": "Vicario", "team": "Juventus", "base_target": 39, "max": 45, "role": "Portiere Spalletti"},
            {"name": "Martinez Jo.", "team": "Inter", "base_target": 34, "max": 39, "role": "Titolare Inter Chivu"},
            {"name": "Carnesecchi", "team": "Atalanta", "base_target": 34, "max": 40, "role": "Top Modificatore Sarri"},
            {"name": "Butez", "team": "Como", "base_target": 31, "max": 36, "role": "Record 19 Clean Sheet"}
        ]},
        {"tier_label": "Portiere Rendimento / Semi-Top", "min_p": 15, "max_p": 28, "candidates": [
            {"name": "Meret", "team": "Napoli", "base_target": 28, "max": 33, "role": "Titolare Allegri"},
            {"name": "De Gea", "team": "Fiorentina", "base_target": 21, "max": 25, "role": "Esperienza Internazionale"},
            {"name": "Skorupski", "team": "Bologna", "base_target": 17, "max": 21, "role": "Affidabile Tedesco"},
            {"name": "Mandas", "team": "Lazio", "base_target": 15, "max": 19, "role": "Titolare Gattuso"},
            {"name": "Okoye", "team": "Udinese", "base_target": 14, "max": 17, "role": "Fisicità e Rendimento"}
        ]},
        {"tier_label": "Portiere Low-Cost / Alternanza", "min_p": 1, "max_p": 14, "candidates": [
            {"name": "Falcone", "team": "Lecce", "base_target": 12, "max": 15, "role": "Re del Modificatore"},
            {"name": "Milinkovic-Savic V.", "team": "Napoli", "base_target": 11, "max": 14, "role": "Co-titolare Napoli"},
            {"name": "Caprile", "team": "Cagliari", "base_target": 10, "max": 13, "role": "Titolare Pisacane"},
            {"name": "Bijlow", "team": "Genoa", "base_target": 9, "max": 12, "role": "Titolare De Rossi"},
            {"name": "Provedel", "team": "Inter", "base_target": 8, "max": 10, "role": "Copertura Porta Inter"},
            {"name": "Perri", "team": "Torino", "base_target": 5, "max": 7, "role": "Titolare Abate"},
            {"name": "Thiam", "team": "Monza", "base_target": 4, "max": 6, "role": "Titolare Low-Cost Jurić"}
        ]}
    ],
    'D': [
        {"tier_label": "Top Modificatore / Assist", "min_p": 20, "max_p": 55, "candidates": [
            {"name": "Dimarco", "team": "Inter", "base_target": 52, "max": 60, "role": "Top Assist / Piazzati (FM 7.64)"},
            {"name": "Bremer", "team": "Juventus", "base_target": 38, "max": 44, "role": "Top Difensore Modificatore (FM 6.81)"},
            {"name": "Mancini", "team": "Roma", "base_target": 32, "max": 38, "role": "Centrale Goleador / Saltatore (FM 6.51)"},
            {"name": "Wesley", "team": "Roma", "base_target": 30, "max": 35, "role": "Terzino di Spinta Modificatore (5 gol)"},
            {"name": "Bastoni", "team": "Inter", "base_target": 26, "max": 31, "role": "Garanzia 6.5 Modificatore (FM 6.34)"},
            {"name": "Pavlovic", "team": "Milan", "base_target": 26, "max": 31, "role": "Centrale Goleador da Piazzato (5 gol)"}
        ]},
        {"tier_label": "Centrale da Bonus / Saltatore", "min_p": 15, "max_p": 25, "candidates": [
            {"name": "Solet", "team": "Udinese", "base_target": 25, "max": 30, "role": "Centrale Regista Aggiunto (FM 6.40)"},
            {"name": "Akanji", "team": "Inter", "base_target": 24, "max": 28, "role": "Centrale Titolare Senza Malus (FM 6.41)"},
            {"name": "Cambiaso", "team": "Juventus", "base_target": 23, "max": 28, "role": "Laterale Titolare Spalletti (3G+4A)"},
            {"name": "Bisseck", "team": "Inter", "base_target": 23, "max": 27, "role": "Centrale in Ascesa da Bonus (FM 6.65)"},
            {"name": "Di Lorenzo", "team": "Napoli", "base_target": 22, "max": 26, "role": "Intoccabile a Destra (FM 6.33)"},
            {"name": "Rrahmani", "team": "Napoli", "base_target": 21, "max": 25, "role": "Centrale Titolarissimo Allegri (FM 6.45)"},
            {"name": "Scalvini", "team": "Atalanta", "base_target": 20, "max": 24, "role": "Perno Difensivo Sarri (3 gol)"},
            {"name": "Kempf", "team": "Como", "base_target": 19, "max": 22, "role": "Pilastro Difesa Fabregas (FM 6.52)"},
            {"name": "Ostigard", "team": "Genoa", "base_target": 18, "max": 22, "role": "Specialista Aereo da Corner (5 gol)"}
        ]},
        {"tier_label": "Titolare Modificatore / Spinta", "min_p": 10, "max_p": 16, "candidates": [
            {"name": "Kalulu", "team": "Juventus", "base_target": 16, "max": 19, "role": "Titolare Fisso Senza Sbavature (FM 6.35)"},
            {"name": "Yan Couto", "team": "Como", "base_target": 16, "max": 19, "role": "Esterno Spinta Fabregas"},
            {"name": "Molina N.", "team": "Roma", "base_target": 16, "max": 19, "role": "Esterno Offensivo da Bonus"},
            {"name": "Ndicka", "team": "Roma", "base_target": 16, "max": 18, "role": "Centrale Solido (FM 6.32)"},
            {"name": "Dragusin", "team": "Fiorentina", "base_target": 15, "max": 18, "role": "Titolare Fisso Modificatore Grosso"},
            {"name": "Gila", "team": "Milan", "base_target": 15, "max": 17, "role": "Affidabilità Pura Difesa a 3 Amorim"},
            {"name": "Spinazzola", "team": "Napoli", "base_target": 14, "max": 17, "role": "Jolly Bonus Allegri (FM 6.53)"},
            {"name": "Mina", "team": "Cagliari", "base_target": 11, "max": 14, "role": "1° Rigorista / Minutaggio 85%"},
            {"name": "Doekhi", "team": "Lazio", "base_target": 11, "max": 13, "role": "Centrale Goleador da Piazzato"},
            {"name": "Vojvoda", "team": "Udinese", "base_target": 10, "max": 13, "role": "Titolare Frequente nelle Rose"}
        ]},
        {"tier_label": "Titolare Low Cost / Scommessa", "min_p": 1, "max_p": 8, "candidates": [
            {"name": "Kaiki", "team": "Como", "base_target": 8, "max": 10, "role": "Terzino Sinistro Fabregas"},
            {"name": "Rensch", "team": "Roma", "base_target": 8, "max": 10, "role": "Scommessa Assist (FM 6.48)"},
            {"name": "Heggem", "team": "Bologna", "base_target": 7, "max": 9, "role": "Centrale Mancino Tedesco"},
            {"name": "Ahanor", "team": "Atalanta", "base_target": 7, "max": 9, "role": "Giovane Talento Sarri"},
            {"name": "Ziolkowski", "team": "Roma", "base_target": 1, "max": 2, "role": "Under Low Cost a 1 Credito"}
        ]}
    ],
    'C': [
        {"tier_label": "Supertop / Rigorista Primario", "min_p": 45, "max_p": 90, "candidates": [
            {"name": "Paz N.", "team": "Como", "base_target": 88, "max": 98, "role": "Supertop Assoluto (12G, FM 7.30)"},
            {"name": "McTominay", "team": "Napoli", "base_target": 69, "max": 78, "role": "Dominante Inserimenti (FM 7.26)"},
            {"name": "Calhanoglu", "team": "Inter", "base_target": 69, "max": 78, "role": "Top 1° Rigorista (89% realizzo, 9G)"},
            {"name": "Orsolini", "team": "Bologna", "base_target": 58, "max": 66, "role": "Ala d'Attacco / 1° Rigorista (10G)"},
            {"name": "De Bruyne", "team": "Napoli", "base_target": 46, "max": 54, "role": "1° Rigorista Napoli (FM 7.24)"},
            {"name": "Rabiot", "team": "Milan", "base_target": 44, "max": 52, "role": "Perno Mediana Amorim (6G+4A)"}
        ]},
        {"tier_label": "Top / Mezzala da Bonus", "min_p": 25, "max_p": 40, "candidates": [
            {"name": "Barella", "team": "Inter", "base_target": 33, "max": 38, "role": "Mezzala Totale Titolarità 100% (FM 6.71)"},
            {"name": "Da Cunha", "team": "Como", "base_target": 32, "max": 38, "role": "1° Rigorista Como (6G, FM 6.91)"},
            {"name": "Atta", "team": "Fiorentina", "base_target": 30, "max": 36, "role": "Mezzala Inserimento Rivelazione (FM 6.88)"},
            {"name": "Baturina", "team": "Como", "base_target": 29, "max": 35, "role": "Trequartista Puro (FM 7.12)"},
            {"name": "Politano", "team": "Napoli", "base_target": 28, "max": 34, "role": "Esterno d'Attacco Tridente Allegri"},
            {"name": "Zielinski", "team": "Inter", "base_target": 26, "max": 31, "role": "2° Rigorista Inter Rigenerato"},
            {"name": "Ederson", "team": "Atalanta", "base_target": 26, "max": 31, "role": "Perno Intoccabile Sarri (FM 6.43)"},
            {"name": "McKennie", "team": "Juventus", "base_target": 25, "max": 30, "role": "Incursore Spalletti (5G+6A)"}
        ]},
        {"tier_label": "Incursore / Asimmetria Tattica", "min_p": 15, "max_p": 24, "candidates": [
            {"name": "Mastantuono", "team": "Fiorentina", "base_target": 24, "max": 28, "role": "Talento Trequartista Viola"},
            {"name": "Vlasic", "team": "Torino", "base_target": 24, "max": 28, "role": "100% Rigori 7/7 (FM 6.66)"},
            {"name": "Moreira Diego", "team": "Milan", "base_target": 22, "max": 26, "role": "Asimmetria Tattica (Attaccante listato C)"},
            {"name": "Gaetano", "team": "Atalanta", "base_target": 21, "max": 25, "role": "Regista da Bonus Sarri (FM 6.31)"},
            {"name": "Saelemaekers", "team": "Milan", "base_target": 20, "max": 24, "role": "Esterno Offensivo Amorim (FM 6.41)"},
            {"name": "Rowe", "team": "Bologna", "base_target": 20, "max": 24, "role": "Ala Offensiva Tedesco (FM 6.62)"},
            {"name": "Zaniolo", "team": "Udinese", "base_target": 19, "max": 23, "role": "Attaccante Aggiunto (FM 6.77)"},
            {"name": "Frattesi", "team": "Lazio", "base_target": 17, "max": 21, "role": "Mezzala Offensiva con Licenza di Tiro"},
            {"name": "Koné M.", "team": "Roma", "base_target": 15, "max": 18, "role": "Media Voto Pura 6.26 Senza Insufficienze"}
        ]},
        {"tier_label": "Regista Low Cost / Scommesse", "min_p": 1, "max_p": 14, "candidates": [
            {"name": "Perrone", "team": "Como", "base_target": 14, "max": 17, "role": "Regista da Voto Fabregas (FM 6.47)"},
            {"name": "Locatelli", "team": "Juventus", "base_target": 12, "max": 15, "role": "Garanzia Voto e 3° Rigorista Juve"},
            {"name": "Diouf", "team": "Inter", "base_target": 11, "max": 14, "role": "Jolly Incursore Rotazioni Chivu"},
            {"name": "Lobotka", "team": "Napoli", "base_target": 10, "max": 12, "role": "Regista Intoccabile Allegri"},
            {"name": "Adzic", "team": "Sassuolo", "base_target": 8, "max": 10, "role": "Scommessa Talento Trequarti"},
            {"name": "Busio", "team": "Venezia", "base_target": 8, "max": 10, "role": "Leader Tecnico e Piazzati Venezia"},
            {"name": "El Azzouzi A.", "team": "Frosinone", "base_target": 2, "max": 3, "role": "Titolare Low Cost 1-2 Crediti"}
        ]}
    ],
    'A': [
        {"tier_label": "Supertop Bomber", "min_p": 80, "max_p": 140, "candidates": [
            {"name": "Martinez L.", "team": "Inter", "base_target": 129, "max": 139, "role": "Top 1 Assoluto Spesa (FM 8.25)"},
            {"name": "Thuram", "team": "Inter", "base_target": 116, "max": 126, "role": "Partner d'Attacco Lautaro (FM 7.95)"},
            {"name": "Malen", "team": "Roma", "base_target": 114, "max": 124, "role": "Record FM 8.84 e 1° Rigorista Roma"},
            {"name": "Kolo Muani", "team": "Juventus", "base_target": 109, "max": 119, "role": "1° Rigorista Juventus Spalletti"},
            {"name": "Ramos G.", "team": "Milan", "base_target": 102, "max": 112, "role": "Centravanti 3-4-2-1 Amorim"},
            {"name": "Kean", "team": "Fiorentina", "base_target": 84, "max": 94, "role": "Terminale Centrale Grosso"},
            {"name": "Hojlund", "team": "Napoli", "base_target": 83, "max": 93, "role": "Prima Punta 4-3-3 Allegri (FM 7.56)"},
            {"name": "Yildiz", "team": "Juventus", "base_target": 82, "max": 92, "role": "Talento Puro e 2° Rigorista (FM 7.30)"}
        ]},
        {"tier_label": "Secondo Slot / Bomber Affidabili", "min_p": 45, "max_p": 75, "candidates": [
            {"name": "Douvikas", "team": "Como", "base_target": 72, "max": 80, "role": "14 Gol Como Fabregas (FM 7.38)"},
            {"name": "Leao", "team": "Milan", "base_target": 70, "max": 78, "role": "Esterno Offensivo Amorim (FM 6.86)"},
            {"name": "Scamacca", "team": "Atalanta", "base_target": 66, "max": 74, "role": "1° Rigorista Sarri (FM 7.55)"},
            {"name": "Pulisic", "team": "Milan", "base_target": 62, "max": 70, "role": "Rigorista Alternativo Milan (FM 7.07)"},
            {"name": "Dybala", "team": "Roma", "base_target": 62, "max": 70, "role": "Saldo Rigori +27.5 pt (91% realizzo)"},
            {"name": "Nkunku", "team": "Milan", "base_target": 56, "max": 64, "role": "1° Rigorista Designato Milan (FM 6.98)"},
            {"name": "Dovbyk", "team": "Bologna", "base_target": 52, "max": 60, "role": "Centravanti Titolare Tedesco (FM 6.77)"},
            {"name": "Krstovic", "team": "Atalanta", "base_target": 48, "max": 55, "role": "10 Reti Alternanza Sarri (FM 7.19)"},
            {"name": "Berardi", "team": "Sassuolo", "base_target": 45, "max": 52, "role": "Rigorista Infallibile 88% (FM 7.19)"}
        ]},
        {"tier_label": "Terzo-Quarto Slot / Rigoristi Provincia", "min_p": 20, "max_p": 40, "candidates": [
            {"name": "Gudmundsson", "team": "Fiorentina", "base_target": 40, "max": 46, "role": "1° Rigorista Fiorentina (+24.5 pt)"},
            {"name": "Simeone", "team": "Torino", "base_target": 39, "max": 45, "role": "Centravanti 11 Reti Abate (FM 7.09)"},
            {"name": "Davis K.", "team": "Udinese", "base_target": 34, "max": 40, "role": "1° Rigorista Udinese (FM 7.37)"},
            {"name": "Castro", "team": "Roma", "base_target": 34, "max": 40, "role": "Rotazione Offensiva Roma (FM 6.51)"},
            {"name": "Piccoli", "team": "Bologna", "base_target": 25, "max": 30, "role": "Alternativa Fisica Dovbyk (FM 6.23)"},
            {"name": "Noslin", "team": "Lazio", "base_target": 25, "max": 30, "role": "Titolare d'Attacco Gattuso"},
            {"name": "Raspadori", "team": "Atalanta", "base_target": 24, "max": 29, "role": "Jolly Tecnico Sarri"},
            {"name": "Pellegrino", "team": "Fiorentina", "base_target": 22, "max": 26, "role": "2° Rigorista Viola (FM 6.65)"},
            {"name": "Cutrone", "team": "Monza", "base_target": 21, "max": 25, "role": "Centravanti Salvezza e 2° Rigorista"},
            {"name": "Adams A.", "team": "Venezia", "base_target": 20, "max": 24, "role": "1° Rigorista e Centravanti Venezia"}
        ]},
        {"tier_label": "Quinto-Sesto Slot / Scommesse", "min_p": 1, "max_p": 18, "candidates": [
            {"name": "Tourè E.", "team": "Parma", "base_target": 18, "max": 22, "role": "Potenziale 7-8 Gol Parma (19.7% rose)"},
            {"name": "Colombo", "team": "Genoa", "base_target": 15, "max": 19, "role": "1° Rigorista Genoa (Allerta 93% cambi al 62')"},
            {"name": "Esposito F.P.", "team": "Inter", "base_target": 14, "max": 17, "role": "1ª Riserva Lautaro (FM 6.97)"},
            {"name": "Bonny", "team": "Inter", "base_target": 12, "max": 15, "role": "Cambio Tattico Chivu (5G+4A)"},
            {"name": "Carlos K.", "team": "Cagliari", "base_target": 11, "max": 14, "role": "Centravanti Fisico 2° Rigorista"},
            {"name": "Geubbels", "team": "Lecce", "base_target": 4, "max": 7, "role": "Seconda Punta 2° Rigorista Lecce"},
            {"name": "Raimondo", "team": "Frosinone", "base_target": 4, "max": 6, "role": "Centravanti Titolare Alvini"}
        ]}
    ]
}

TEAMS_TACTICAL_DB = {
    "Atalanta": {
        "coach": "Maurizio Sarri", "formation": "4-3-3 (Palleggio & Intensità)",
        "gk": "Carnesecchi (Sportiello vice)",
        "defense": "Scalvini, Kristensen/Kossonou; Bellanova/Zappacosta (DX), Bernasconi/Ahanor (SX)",
        "midfield": "Ederson, Gaetano, Pašalić, Samardžić",
        "attack": "De Ketelaere, Sulemana, Scamacca, Krstović",
        "penalties": ["Scamacca (1°)", "Samardžić (2°)", "De Ketelaere (3°)"],
        "advice": "Carnesecchi per il modificatore; Gaetano centrocampista inserzionista; Ahanor scommessa difensiva a 1 credito."
    },
    "Bologna": {
        "coach": "Domenico Tedesco", "formation": "4-3-3 (Verticalizzazione & Alto Pressing)",
        "gk": "Skorupski (Pessina vice)",
        "defense": "Zortea, Heggem, Helland/Vitik, Miranda",
        "midfield": "Ferguson, Moro, Bernardeschi",
        "attack": "Orsolini, Rowe, Dovbyk (Piccoli vice)",
        "penalties": ["Orsolini (1°)", "Bernardeschi (2°)", "Dovbyk (3°)"],
        "advice": "Orsolini 1° slot centrocampo; Rowe 2°-3° slot da bonus; Heggem certezza difensiva a costi contenuti."
    },
    "Cagliari": {
        "coach": "Fabio Pisacane", "formation": "4-3-2-1 (Compatto & Organizzato)",
        "gk": "Caprile (Sherri/Radunovic)",
        "defense": "Yerry Mina, Obert, Rodríguez, Zé Pedro",
        "midfield": "Adopo, Fazzini, Winks",
        "attack": "Daniel Maldini, Sebastiano Esposito, Kevin Carlos (Mendy vice)",
        "penalties": ["Mina (1°)", "Kevin Carlos (2°)", "Daniel Maldini (3°)"],
        "advice": "Mina pilastro modificatore (85% minutaggio); Fazzini e Maldini scommesse da bonus a centrocampo."
    },
    "Como": {
        "coach": "Cesc Fàbregas", "formation": "4-2-3-1 (Possesso & Fluidità)",
        "gk": "Jean Butez (Tornqvist/Vigorito)",
        "defense": "Yan Couto, Kempf, Ramón/Chalobah, Kaiki/Valle",
        "midfield": "Da Cunha, Perrone",
        "attack": "Nico Paz, Baturina, Douvikas (Morata vice)",
        "penalties": ["Da Cunha (1°)", "Douvikas (2°)", "Nico Paz (3°)"],
        "advice": "Butez primato clean sheet (19); Nico Paz e Da Cunha top centrocampo; Douvikas bomber altissima resa; Kempf e Yan Couto pilastri difesa."
    },
    "Fiorentina": {
        "coach": "Fabio Grosso", "formation": "4-3-1-2 / 4-3-3 (Valorizzazione Centrali)",
        "gk": "David De Gea (Christensen/Lezzerini)",
        "defense": "Dodò/Jiménez, Dragusin, Viery, Valdepeñas",
        "midfield": "Arthur Atta, Mastantuono, Fagioli, Oulai, Mandragora",
        "attack": "Gudmundsson, Moise Kean, Pellegrino",
        "penalties": ["Gudmundsson (1°)", "Pellegrino (2°)", "Kean (3°)"],
        "advice": "Atta e Mastantuono centrocampisti da bonus low cost; Gudmundsson e Kean riferimenti offensivi primari."
    },
    "Frosinone": {
        "coach": "Massimiliano Alvini", "formation": "4-3-3 (Verticale & Aggressivo)",
        "gk": "Palmisani / Desplanches",
        "defense": "Monterisi, Bracaglia, Akpoguma, Oyono",
        "midfield": "Calò, Schmid, Grillitsch, El Azzouzi",
        "attack": "Raimondo, Ghedjemis, Zerbin",
        "penalties": ["Calò (1°)", "Schmid (2°)"],
        "advice": "Calò rigorista economico a centrocampo; El Azzouzi slot a 1 credito per copertura; Bracaglia difensore low cost."
    },
    "Genoa": {
        "coach": "Daniele De Rossi", "formation": "3-5-2 / 4-3-3 (Flessibile)",
        "gk": "Justin Bijlow (Stolz vice)",
        "defense": "Ostigard, Vásquez, Marcandalli / Mitaj",
        "midfield": "Frendrup, Ellertsson, Ethan-Meichtry, Baldanzi/Traoré",
        "attack": "Lorenzo Colombo, Vitinha",
        "penalties": ["Colombo (1°)", "Vitinha (2°)", "Ostigard (3°)"],
        "advice": "Ostigard certezza modificatore e saltatore da corner; Colombo 4° slot rigorista (allerta cambi al 65'); Ethan-Meichtry scommessa giovane."
    },
    "Inter": {
        "coach": "Cristian Chivu", "formation": "3-5-2 (Dominio Tattico)",
        "gk": "Josep Martínez (Ivan Provedel co-titolare/vice)",
        "defense": "Dimarco, Bastoni, Akanji, Bisseck, Pavard/Stones, Spence",
        "midfield": "Calhanoglu, Barella, Zielinski, Frattesi, Diouf, Sucic, Jones",
        "attack": "Lautaro Martínez, Marcus Thuram, Francesco Pio Esposito, Bonny",
        "penalties": ["Calhanoglu (1° - 89%)", "Zielinski (2°)", "Lautaro Martínez (3°)"],
        "advice": "Dimarco top 1 assoluto di difesa; Calhanoglu top bonus centrocampo; coppia portieri Martinez-Provedel obbligatoria; Pio Esposito scommessa a 1-2 cr."
    },
    "Juventus": {
        "coach": "Luciano Spalletti", "formation": "4-2-3-1 (Propensione Offensiva)",
        "gk": "Guglielmo Vicario (Perin vice)",
        "defense": "Bremer, Kalulu, Cambiaso, Çelik",
        "midfield": "Locatelli, Thuram / McKennie",
        "attack": "Yildiz, Conceição, Alajbegović, Randal Kolo Muani (David/Boga)",
        "penalties": ["Kolo Muani (1°)", "Yildiz (2°)", "Locatelli (3°)"],
        "advice": "Bremer top difensore per modificatore; Yildiz e Kolo Muani bonus pesanti d'attacco; Alajbegović talento a 1-5 cr."
    },
    "Lazio": {
        "coach": "Gennaro Gattuso", "formation": "4-2-3-1 / 4-3-3 (Grintoso & Verticale)",
        "gk": "Christos Mandas (Motta vice)",
        "defense": "Marusic, Doekhi, Romagnoli, Provstgaard / Pedraza",
        "midfield": "Rovella, Kenneth Taylor, Davide Frattesi",
        "attack": "Zaccagni, Isaksen, Noslin (Ratkov / Dia)",
        "penalties": ["Zaccagni (1°)", "Taylor K. (2°)", "Cataldi (3°)"],
        "advice": "Frattesi centrocampista incursore alla Milinkovic; Doekhi difensore goleador da piazzato; Noslin scommessa attacco."
    },
    "Lecce": {
        "coach": "Staff Tecnico", "formation": "4-3-3 (Contenimento & Ripartenza)",
        "gk": "Wladimiro Falcone (Bleve/Penev)",
        "defense": "Tiago Gabriel, Gallo, Baschirotto",
        "midfield": "Berisha, Gandelman, Helgason",
        "attack": "Banda, Stulić / Geubbels, Pierotti",
        "penalties": ["Stulić (1°)", "Geubbels (2°)", "Berisha (3°)"],
        "advice": "Falcone certezza da modificatore; Gandelman scommessa a centrocampo; Pierotti/Geubbels slot attacco a 1-2 cr."
    },
    "Milan": {
        "coach": "Rúben Amorim", "formation": "3-4-2-1 (Iper-Dinamico)",
        "gk": "Mike Maignan (Terracciano/Torriani)",
        "defense": "Strahinja Pavlovic, Gila, Gabbia / Bartesaghi",
        "midfield": "Rabiot, Modric, Saelemaekers, Diego Moreira",
        "attack": "Christian Pulisic, Rafael Leão, Gonçalo Ramos (Nkunku)",
        "penalties": ["Nkunku (1°)", "Pulisic (2°)", "Gonçalo Ramos (3°)"],
        "advice": "Gonçalo Ramos centravanti ideale per Amorim (~90-100 cr); Pavlovic certezza modificatore e bonus; Diego Moreira bug listato C."
    },
    "Monza": {
        "coach": "Ivan Jurić", "formation": "3-4-2-1 (Duelli & Aggressività)",
        "gk": "Demba Thiam (Pizzignacco)",
        "defense": "Andrea Carboni, Delli Carri, Birindelli, Mangas",
        "midfield": "Matteo Pessina, Colpani, Akinsanmiro",
        "attack": "Patrick Cutrone, Dany Mota, Petagna",
        "penalties": ["Pessina (1°)", "Cutrone (2°)", "Petagna (3°)"],
        "advice": "Pessina garanzia rigori low cost; Cutrone ultimo slot attacco da titolarità fissa; Thiam perfetto per alternanza 100% con Milano."
    },
    "Napoli": {
        "coach": "Massimiliano Allegri", "formation": "4-3-3 / 4-2-4 (Flessibile & Diretto)",
        "gk": "Alex Meret (Vanja Milinković-Savić co-titolare)",
        "defense": "Di Lorenzo, Olivera/Spinazzola, Rrahmani, Beukema",
        "midfield": "Scott McTominay, Stanislav Lobotka, Kevin De Bruyne, Anguissa, Elmas",
        "attack": "Rasmus Højlund, Politano, Santos, Neres",
        "penalties": ["De Bruyne (1°)", "Højlund (2°)", "McTominay (3°)"],
        "advice": "McTominay 1° slot assoluto di centrocampo; Højlund bomber ideale con Allegri; Spinazzola low cost in difesa."
    },
    "Parma": {
        "coach": "Cuesta", "formation": "4-2-3-1 / 4-3-3 (Moderno & Propositivo)",
        "gk": "Daffara / Corvi",
        "defense": "Delprato, Valeri, Troilo, Britschgi",
        "midfield": "Adrián Bernabé, Mandela Keita, Sorensen, Almqvist",
        "attack": "El Bilal Touré, Luka Romero, Frigan",
        "penalties": ["Bernabé (1°)", "Touré E. (2°)", "Valeri (3°)"],
        "advice": "Bernabé centrocampista da bonus e regia; El Bilal Touré 4°-5° slot d'attacco ad altissimo potenziale; Valeri terzino assist."
    },
    "Roma": {
        "coach": "Guida Tecnica", "formation": "3-4-2-1 (Intensità & Spinta Offensiva)",
        "gk": "Mile Svilar (Gollini/De Marzi)",
        "defense": "Gianluca Mancini, Evan Ndicka, Hermoso, Rensch, Nahuel Molina / Wesley",
        "midfield": "Manu Koné, Niccolò Pisilli, Bryan Cristante",
        "attack": "Paulo Dybala, Matías Soulé / Castro, Donyell Malen",
        "penalties": ["Malen (1°)", "Dybala (2°)", "Castro (3°)"],
        "advice": "Svilar top 1 portiere (18 clean sheet); Malen top bomber d'attacco; Wesley e Molina esterni difensivi ad altissima fantamedia."
    },
    "Sassuolo": {
        "coach": "Alberto Aquilani", "formation": "4-3-3 (Propositivo)",
        "gk": "Arijanet Murić / Stefano Turati",
        "defense": "Sebastian Walukiewicz, Jay Idzes, Obrador",
        "midfield": "Kristian Thorstvedt, Ismaël Koné, Vasilije Adžić",
        "attack": "Domenico Berardi, Armand Laurienté, Andrea Pinamonti, Bowie",
        "penalties": ["Berardi (1°)", "Pinamonti (2°)", "Laurienté (3°)"],
        "advice": "Adžić gemma a centrocampo (1-5 cr); Berardi e Pinamonti certezze per rigori e gol."
    },
    "Torino": {
        "coach": "Ignazio Abate", "formation": "4-2-3-1 (Verticale & Organizzato)",
        "gk": "Alberto Paleari / Franco Perri",
        "defense": "Saul Coco, Marcus Pedersen",
        "midfield": "Nikola Vlašić, Cesare Casadei, Cacciamani",
        "attack": "Giovanni Simeone, Che Adams, Duván Zapata",
        "penalties": ["Vlašić (1°)", "Simeone (2°)", "Casadei (3°)"],
        "advice": "Vlašić centrocampista rigorista da 6-8 gol; Paleari/Perri porta low cost; Simeone 3°-4° slot attacco."
    },
    "Udinese": {
        "coach": "Staff Tecnico", "formation": "3-5-2 (Fisico & Diretto)",
        "gk": "Maduka Okoye (Padelli/Piana)",
        "defense": "Oumar Solet, Christian Kabasele, Thomas Kristensen, Mergim Vojvoda, Hassane Kamara",
        "midfield": "Jesper Karlström, Jurgen Ekkelenkamp, Nicolò Zaniolo",
        "attack": "Keinan Davis, Adam Buksa, Gueye",
        "penalties": ["Davis (1°)", "Solet (2°)", "Zaniolo (3°)"],
        "advice": "Solet difensore da bonus di prima fascia; Vojvoda costanza da modificatore; Zaniolo jolly offensivo listato centrocampista."
    },
    "Venezia": {
        "coach": "Giovanni Stroppa", "formation": "3-5-2 (Ritmo & Organizzazione)",
        "gk": "Filip Stanković (Grandi/Pozzi)",
        "defense": "Ridgeciano Haps, Correia, Jay Idzes",
        "midfield": "Gianluca Busio, Mikael Ellertsson, John Yeboah",
        "attack": "Akor Adams, Albion Rrahmani, Lauberbach",
        "penalties": ["Adams A. (1°)", "Rrahmani A. (2°)", "Yeboah (3°)"],
        "advice": "Busio regista inamovibile e tiratore low cost; Akor Adams scommessa 3ª punta ad alto potenziale realizzativo."
    }
}

# ==============================================================================
# 3. FUNZIONI ANALITICHE E DI CALCOLO
# ==============================================================================
def normalize_name(name):
    return str(name).lower().replace("'", "").replace(".", "").replace("-", " ").strip()

def get_dept_spent(role):
    return sum(p['price'] for p in st.session_state.get('my_roster', []) if p['role'] == role)

def get_dept_count(role):
    return len([p for p in st.session_state.get('my_roster', []) if p['role'] == role])

def get_player_base_target(player_row):
    name = str(player_row['Nome']).strip()
    role = str(player_row['R']).strip()
    fvm = int(player_row['FVM']) if pd.notnull(player_row.get('FVM')) else 1
    qta = int(player_row['Qt.A']) if pd.notnull(player_row.get('Qt.A')) else 1

    norm_query = normalize_name(name)
    target = None

    if name in DOC_TARGETS:
        target = DOC_TARGETS[name]
    else:
        tokens = set(norm_query.split())
        for doc_name, val in DOC_TARGETS.items():
            doc_tokens = set(normalize_name(doc_name).split())
            if tokens == doc_tokens or (len(tokens) > 1 and tokens.issubset(doc_tokens)) or (len(doc_tokens) > 1 and doc_tokens.issubset(tokens)):
                target = val
                break
        
        if target is None:
            for doc_name, val in DOC_TARGETS.items():
                norm_doc = normalize_name(doc_name)
                if norm_doc in norm_query or norm_query in norm_doc:
                    target = val
                    break

    if target is None:
        if role == 'P':
            target = max(1, int(round(qta * 1.1)))
        elif role == 'D':
            if fvm >= 200: target = max(30, int(round(fvm * 0.14)))
            elif fvm >= 50: target = max(12, int(round(fvm * 0.28)))
            elif fvm >= 20: target = max(5, int(round(fvm * 0.25)))
            else: target = max(1, int(round(qta * 0.8)))
        elif role == 'C':
            if fvm >= 200: target = max(45, int(round(fvm * 0.22)))
            elif fvm >= 80: target = max(16, int(round(fvm * 0.22)))
            elif fvm >= 25: target = max(6, int(round(fvm * 0.20)))
            else: target = max(1, int(round(qta * 0.8)))
        elif role == 'A':
            if fvm >= 250: target = max(75, int(round(fvm * 0.32)))
            elif fvm >= 120: target = max(30, int(round(fvm * 0.26)))
            elif fvm >= 40: target = max(10, int(round(fvm * 0.22)))
            else: target = max(1, int(round(qta * 0.9)))

    int_t = int(round(target))
    if role == 'P':
        max_bid = max(int_t + 1, int(round(int_t * 1.20))) if int_t > 1 else 1
    elif role == 'D':
        max_bid = max(int_t + 1, int(round(int_t * 1.18))) if int_t > 1 else 1
    elif role == 'C':
        max_bid = max(int_t + 1, int(round(int_t * 1.16))) if int_t > 2 else int_t
    else:
        max_bid = max(int_t + 1, int(round(int_t * 1.15))) if int_t > 2 else int_t

    return int_t, max_bid

def calculate_dynamic_player_evaluation(player_row, my_roster):
    role = str(player_row['R']).strip()
    base_target, base_max = get_player_base_target(player_row)
    
    # 1. Calcolo Spese Normali
    tot_spent = sum(p['price'] for p in my_roster)
    # Trova questa riga in ENTRAMBE le funzioni della Sezione 3 e modificala così:
tot_budget_left = TOTAL_BUDGET - tot_spent + st.session_state.get('budget_adjustments', 0)
    tot_slots_filled = len(my_roster)
    tot_slots_left = TOTAL_SLOTS - tot_slots_filled
    
    dept_bought = [p for p in my_roster if p['role'] == role]
    dept_spent = sum(p['price'] for p in dept_bought)
    dept_filled = len(dept_bought)
    dept_slots_left = SLOTS[role] - dept_filled

    if tot_slots_left <= 0 or dept_slots_left <= 0:
        return {"base_target": base_target, "dyn_target": 0, "dyn_max_bid": 0, "is_full": True, "dept_budget_left": 0, "dept_slots_left": 0}

    # 2. LOGICA LOCK-IN STRATEGY
    locked_budget_tot = 0
    locked_budget_dept = 0
    if st.session_state.get('lock_in_active', False):
        purchased_names = [p['name'] for p in my_roster]
        for r_code in ['P', 'D', 'C', 'A']:
            for t_name in st.session_state.get('custom_user_targets', {}).get(r_code, []):
                if t_name not in purchased_names and t_name != player_row['Nome']:
                    row = listone_df[listone_df['Nome'] == t_name]
                    if not row.empty:
                        bt, _ = get_player_base_target(row.iloc[0])
                        locked_budget_tot += bt
                        if r_code == role:
                            locked_budget_dept += bt
                            
    eff_tot_budget = max(1, tot_budget_left - locked_budget_tot)
    
    # 3. Calcolo Adattivo
    other_slots_needed = tot_slots_left - dept_slots_left
    max_dept_can_have = max(dept_slots_left, eff_tot_budget - other_slots_needed)
    effective_dept_budget = min(max_dept_can_have, max(dept_slots_left, (BASE_DEPT_BUDGET[role] - dept_spent) - locked_budget_dept))
    
    total_unfilled_baseline = sum(sum(BASELINE_DEPT_CURVES[r][len([p for p in my_roster if p['role'] == r]):]) for r in SLOTS)
    scale_factor = eff_tot_budget / max(1, total_unfilled_baseline)
    
    dyn_target = max(1, int(round(base_target * scale_factor)))
    max_single_in_dept = max(1, effective_dept_budget - (dept_slots_left - 1))
    dyn_target = min(dyn_target, max_single_in_dept)

    margin = 1.15 if dyn_target > 25 else (1.20 if dyn_target > 5 else 1.0)
    dyn_max_bid = int(round(dyn_target * margin))
    dyn_max_bid = max(dyn_target, min(eff_tot_budget - (tot_slots_left - 1), min(dyn_max_bid, max_single_in_dept)))

    # =================================================================
    # 🔥 PANIC BUTTON: MODALITÀ DIFESA DEL BUDGET ATTIVA
    # Se il budget è <= 38% e non hai attaccanti, forza offerte a 1 cr per P, D, C
    # =================================================================
    panic_active = tot_budget_left <= 190 and len([p for p in my_roster if p['role'] == 'A']) == 0
    if panic_active and role != 'A':
        dyn_target = 1
        dyn_max_bid = 1

    return {
        "base_target": base_target,
        "base_max": base_max,
        "dyn_target": dyn_target,
        "dyn_max_bid": dyn_max_bid,
        "scale_factor": round(scale_factor, 2),
        "dept_spent": dept_spent,
        "dept_budget_left": effective_dept_budget,
        "dept_slots_left": dept_slots_left,
        "is_full": False
    }

    # 2. LOGICA LOCK-IN STRATEGY
    locked_budget_tot = 0
    locked_budget_dept = 0
    if st.session_state.get('lock_in_active', False):
        purchased_names = [p['name'] for p in my_roster]
        for r_code in ['P', 'D', 'C', 'A']:
            for t_name in st.session_state.get('custom_user_targets', {}).get(r_code, []):
                if t_name not in purchased_names and t_name != player_row['Nome']:
                    row = listone_df[listone_df['Nome'] == t_name]
                    if not row.empty:
                        bt, _ = get_player_base_target(row.iloc[0])
                        locked_budget_tot += bt
                        if r_code == role:
                            locked_budget_dept += bt
                            
    eff_tot_budget = max(1, tot_budget_left - locked_budget_tot)
    
    # 3. Calcolo Adattivo
    other_slots_needed = tot_slots_left - dept_slots_left
    max_dept_can_have = max(dept_slots_left, eff_tot_budget - other_slots_needed)
    effective_dept_budget = min(max_dept_can_have, max(dept_slots_left, (BASE_DEPT_BUDGET[role] - dept_spent) - locked_budget_dept))
    
    total_unfilled_baseline = sum(sum(BASELINE_DEPT_CURVES[r][len([p for p in my_roster if p['role'] == r]):]) for r in SLOTS)
    scale_factor = eff_tot_budget / max(1, total_unfilled_baseline)
    
    dyn_target = max(1, int(round(base_target * scale_factor)))
    max_single_in_dept = max(1, effective_dept_budget - (dept_slots_left - 1))
    dyn_target = min(dyn_target, max_single_in_dept)

    margin = 1.15 if dyn_target > 25 else (1.20 if dyn_target > 5 else 1.0)
    dyn_max_bid = int(round(dyn_target * margin))
    dyn_max_bid = max(dyn_target, min(eff_tot_budget - (tot_slots_left - 1), min(dyn_max_bid, max_single_in_dept)))

    return {
        "base_target": base_target,
        "base_max": base_max,
        "dyn_target": dyn_target,
        "dyn_max_bid": dyn_max_bid,
        "scale_factor": round(scale_factor, 2),
        "dept_spent": dept_spent,
        "dept_budget_left": effective_dept_budget,
        "dept_slots_left": dept_slots_left,
        "is_full": False
    }

def calculate_dynamic_targets_for_slots(role, my_roster):
    tot_spent = sum(p['price'] for p in my_roster)
    # Trova questa riga in ENTRAMBE le funzioni della Sezione 3 e modificala così:
tot_budget_left = TOTAL_BUDGET - tot_spent + st.session_state.get('budget_adjustments', 0)
    tot_slots_left = TOTAL_SLOTS - len(my_roster)

    dept_bought = [p for p in my_roster if p['role'] == role]
    dept_spent = sum(p['price'] for p in dept_bought)
    dept_filled = len(dept_bought)
    dept_slots_left = SLOTS[role] - dept_filled

    if dept_slots_left <= 0:
        return []

    # LOCK-IN: Calcoliamo quanti slot e quanti crediti sono "prenotati"
    locked_budget_dept = 0
    locked_slots_dept = 0
    purchased_names = [p['name'] for p in my_roster]
    custom_targets = st.session_state.get('custom_user_targets', {}).get(role, [])
    
    unpurchased_locked = []
    
    if st.session_state.get('lock_in_active', False):
        for t_name in custom_targets:
            if t_name not in purchased_names:
                row = listone_df[listone_df['Nome'] == t_name]
                if not row.empty:
                    bt, _ = get_player_base_target(row.iloc[0])
                    locked_budget_dept += bt
                    locked_slots_dept += 1
                    unpurchased_locked.append(bt)

    other_slots_needed = tot_slots_left - dept_slots_left
    max_dept_can_have = max(dept_slots_left, tot_budget_left - other_slots_needed)
    effective_dept_budget = min(max_dept_can_have, max(dept_slots_left, BASE_DEPT_BUDGET[role] - dept_spent))

    distributable_budget = max(dept_slots_left - locked_slots_dept, effective_dept_budget - locked_budget_dept)
    distributable_slots = max(0, dept_slots_left - locked_slots_dept)

    weights_map = {
        'A': {6: [0.40, 0.33, 0.16, 0.07, 0.03, 0.01], 5: [0.55, 0.25, 0.12, 0.05, 0.03], 4: [0.60, 0.25, 0.10, 0.05], 3: [0.68, 0.24, 0.08], 2: [0.85, 0.15], 1: [1.0], 0: []},
        'C': {8: [0.35, 0.30, 0.13, 0.08, 0.05, 0.04, 0.03, 0.02], 7: [0.42, 0.22, 0.14, 0.09, 0.06, 0.04, 0.03], 6: [0.48, 0.24, 0.12, 0.08, 0.05, 0.03], 5: [0.55, 0.25, 0.10, 0.06, 0.04], 4: [0.60, 0.22, 0.12, 0.06], 3: [0.70, 0.20, 0.10], 2: [0.80, 0.20], 1: [1.0], 0: []},
        'D': {8: [0.40, 0.17, 0.13, 0.11, 0.08, 0.08, 0.02, 0.01], 7: [0.30, 0.22, 0.18, 0.14, 0.10, 0.04, 0.02], 6: [0.35, 0.25, 0.20, 0.12, 0.05, 0.03], 5: [0.42, 0.28, 0.18, 0.08, 0.04], 4: [0.50, 0.30, 0.14, 0.06], 3: [0.60, 0.28, 0.12], 2: [0.75, 0.25], 1: [1.0], 0: []},
        'P': {3: [max(1, distributable_budget - 4), 3, 1], 2: [max(1, distributable_budget - 1), 1], 1: [distributable_budget], 0: []}
    }

    if role == 'P':
        dist_targets = weights_map['P'].get(distributable_slots, [])
    else:
        weights = weights_map[role].get(distributable_slots, [])
        dist_targets = [max(1, int(round(distributable_budget * w))) for w in weights]
        if dist_targets:
            diff = sum(dist_targets) - distributable_budget
            dist_targets[0] = max(1, dist_targets[0] - diff)
            
    final_targets = sorted(unpurchased_locked + dist_targets, reverse=True)
    return final_targets

def get_dynamic_slot_candidates(role_code, slot_target_budget, purchased_registry, allocated_in_roadmap, custom_user_targets_list=None):
    if custom_user_targets_list:
        for cust_name in custom_user_targets_list:
            if cust_name not in purchased_registry and cust_name not in allocated_in_roadmap:
                row = listone_df[listone_df['Nome'] == cust_name]
                if not row.empty:
                    r_row = row.iloc[0]
                    base_t, base_m = get_player_base_target(r_row)
                    allocated_in_roadmap.add(cust_name)
                    
                    dyn_t = max(1, slot_target_budget)
                    margin = 1.16 if dyn_t > 20 else (1.20 if dyn_t > 5 else 1.0)
                    dyn_m = int(round(dyn_t * margin)) if dyn_t > 2 else dyn_t
                    
                    alts_df = listone_df[(listone_df['R'] == role_code) & (~listone_df['Nome'].isin(allocated_in_roadmap)) & (~listone_df['Nome'].isin(purchased_registry.keys()))]
                    alts_str = ", ".join([f"{r['Nome']} ({get_player_base_target(r)[0]} cr)" for _, r in alts_df.head(3).iterrows()])
                    
                    return {
                        "chosen_name": cust_name,
                        "chosen_team": str(r_row['Squadra']),
                        "chosen_role": "🎯 Mio Top Selezionato",
                        "base_target": base_t,
                        "dyn_target": dyn_t,
                        "dyn_max_bid": dyn_m,
                        "alts_str": alts_str if alts_str else "Nessuna alternativa disponibile"
                    }

    pool = ROLE_TIERED_POOLS.get(role_code, [])
    best_tier = None
    min_dist = 999
    for tier in pool:
        mid_p = (tier['min_p'] + tier['max_p']) / 2.0
        dist = abs(slot_target_budget - mid_p)
        if dist < min_dist:
            min_dist = dist
            best_tier = tier

    candidates_ordered = []
    if best_tier:
        for c in best_tier['candidates']:
            if c['name'] not in purchased_registry and c['name'] not in allocated_in_roadmap:
                candidates_ordered.append(c)

    if len(candidates_ordered) < 4:
        for tier in pool:
            if tier != best_tier:
                for c in tier['candidates']:
                    if c['name'] not in purchased_registry and c['name'] not in allocated_in_roadmap and c not in candidates_ordered:
                        candidates_ordered.append(c)
                        if len(candidates_ordered) >= 6:
                            break

    candidates_ordered.sort(key=lambda x: abs(x['base_target'] - slot_target_budget))

    chosen = candidates_ordered[0] if candidates_ordered else {"name": "Scommessa / Copertura", "team": "Serie A", "base_target": 1, "max": 1, "role": "Slot di Completamento"}
    allocated_in_roadmap.add(chosen['name'])

    alts = [f"{c['name']} ({c['base_target']} cr)" for c in candidates_ordered[1:4]]

    margin = 1.16 if slot_target_budget > 20 else (1.20 if slot_target_budget > 5 else 1.0)
    max_b = int(round(slot_target_budget * margin)) if slot_target_budget > 2 else slot_target_budget

    return {
        "chosen_name": chosen['name'],
        "chosen_team": chosen['team'],
        "chosen_role": chosen['role'],
        "base_target": chosen['base_target'],
        "dyn_target": slot_target_budget,
        "dyn_max_bid": max_b,
        "alts_str": ", ".join(alts) if alts else "Nessuna alternativa disponibile"
    }

def render_role_card_grid(role_code, dept_title, num_cols=4):
    slots_total = SLOTS[role_code]
    bought_list = [p for p in st.session_state.get('my_roster', []) if p['role'] == role_code]
    
    st.markdown(f"### {dept_title}")
    st.caption(f"Spesi: **{get_dept_spent(role_code)} cr** / {BASE_DEPT_BUDGET[role_code]} cr | Slot Completati: **{len(bought_list)} / {slots_total}**")
    
    allocated_in_roadmap = set(p['name'] for p in st.session_state.get('my_roster', []))
    dyn_targets_remaining = calculate_dynamic_targets_for_slots(role_code, st.session_state.get('my_roster', []))
    
    user_custom_picks = st.session_state.get('custom_user_targets', {}).get(role_code, [])

    for row_start in range(0, slots_total, num_cols):
        row_slots_count = min(num_cols, slots_total - row_start)
        cols = st.columns(num_cols)
        
        for idx in range(row_slots_count):
            global_slot_idx = row_start + idx
            slot_prefix = 'DIF' if role_code == 'D' else ('CEN' if role_code == 'C' else 'ATT')
            slot_label = f"{slot_prefix} {global_slot_idx + 1}"
            
            with cols[idx]:
                if global_slot_idx < len(bought_list):
                    p_bought = bought_list[global_slot_idx]
                    card_text = f"**{slot_label}: {p_bought['name']}** ({p_bought['team']})\n\n✅ **Acquistato:** `{p_bought['price']} cr`\n\n📌 *Ruolo:* In Rosa"
                    st.success(card_text)
                else:
                    rem_idx = global_slot_idx - len(bought_list)
                    t_budget = dyn_targets_remaining[rem_idx] if rem_idx < len(dyn_targets_remaining) else 1
                    
                    slot_res = get_dynamic_slot_candidates(role_code, t_budget, st.session_state.get('purchased_registry', {}), allocated_in_roadmap, custom_user_targets_list=user_custom_picks)
                    card_text = f"**{slot_label}: {slot_res['chosen_name']}** ({slot_res['chosen_team']})\n\n🎯 **Target Ricalcolato:** `{slot_res['dyn_target']} cr` | 🛑 **Max:** `{slot_res['dyn_max_bid']} cr`\n\n📌 *Ruolo:* **{slot_res['chosen_role']}**\n\n🔄 *Piani B/C liberi:* {slot_res['alts_str']}"
                    st.info(card_text)

# ==============================================================================
# 4. CARICAMENTO DEL LISTONE & API-FOOTBALL
# ==============================================================================
@st.cache_data
def safe_load_listone():
    excel_file = 'Quotazioni_Fantacalcio_Stagione_2026_27.xlsx'
    df = None
    if os.path.exists(excel_file):
        for skip in [1, 0, 2]:
            try:
                temp_df = pd.read_excel(excel_file, sheet_name=0, skiprows=skip)
                temp_df.columns = [str(c).strip() for c in temp_df.columns]
                for col in temp_df.columns:
                    if col.lower() in ['nome', 'calciatore', 'giocatore']:
                        temp_df.rename(columns={col: 'Nome'}, inplace=True)
                    elif col.lower() in ['r', 'ruolo']:
                        temp_df.rename(columns={col: 'R'}, inplace=True)
                    elif col.lower() in ['squadra', 'club', 'sq']:
                        temp_df.rename(columns={col: 'Squadra'}, inplace=True)
                    elif col.lower() in ['qt.a', 'qta', 'quotazione', 'quot']:
                        temp_df.rename(columns={col: 'Qt.A'}, inplace=True)
                    elif col.lower() in ['fvm', 'fvm/500']:
                        temp_df.rename(columns={col: 'FVM'}, inplace=True)
                if 'Nome' in temp_df.columns and 'R' in temp_df.columns:
                    df = temp_df
                    break
            except Exception:
                pass

    if df is None or df.empty:
        df = pd.DataFrame([
            {'Nome': 'Martinez Jo.', 'Squadra': 'Inter', 'R': 'P', 'Qt.A': 17, 'FVM': 63},
            {'Nome': 'Svilar', 'Squadra': 'Roma', 'R': 'P', 'Qt.A': 22, 'FVM': 85},
            {'Nome': 'Maignan', 'Squadra': 'Milan', 'R': 'P', 'Qt.A': 22, 'FVM': 80},
            {'Nome': 'Vicario', 'Squadra': 'Juventus', 'R': 'P', 'Qt.A': 20, 'FVM': 75},
            {'Nome': 'Butez', 'Squadra': 'Como', 'R': 'P', 'Qt.A': 20, 'FVM': 70},
            {'Nome': 'Dimarco', 'Squadra': 'Inter', 'R': 'D', 'Qt.A': 32, 'FVM': 265},
            {'Nome': 'Bremer', 'Squadra': 'Juventus', 'R': 'D', 'Qt.A': 25, 'FVM': 180},
            {'Nome': 'Mancini', 'Squadra': 'Roma', 'R': 'D', 'Qt.A': 22, 'FVM': 160},
            {'Nome': 'Wesley', 'Squadra': 'Roma', 'R': 'D', 'Qt.A': 21, 'FVM': 155},
            {'Nome': 'Bastoni', 'Squadra': 'Inter', 'R': 'D', 'Qt.A': 19, 'FVM': 145},
            {'Nome': 'Pavlovic', 'Squadra': 'Milan', 'R': 'D', 'Qt.A': 19, 'FVM': 140},
            {'Nome': 'Solet', 'Squadra': 'Udinese', 'R': 'D', 'Qt.A': 18, 'FVM': 130},
            {'Nome': 'Paz N.', 'Squadra': 'Como', 'R': 'C', 'Qt.A': 43, 'FVM': 290},
            {'Nome': 'McTominay', 'Squadra': 'Napoli', 'R': 'C', 'Qt.A': 38, 'FVM': 255},
            {'Nome': 'Calhanoglu', 'Squadra': 'Inter', 'R': 'C', 'Qt.A': 36, 'FVM': 245},
            {'Nome': 'Orsolini', 'Squadra': 'Bologna', 'R': 'C', 'Qt.A': 35, 'FVM': 235},
            {'Nome': 'De Bruyne', 'Squadra': 'Napoli', 'R': 'C', 'Qt.A': 32, 'FVM': 215},
            {'Nome': 'Rabiot', 'Squadra': 'Milan', 'R': 'C', 'Qt.A': 30, 'FVM': 200},
            {'Nome': 'Lautaro Martinez', 'Squadra': 'Inter', 'R': 'A', 'Qt.A': 55, 'FVM': 370},
            {'Nome': 'Thuram', 'Squadra': 'Inter', 'R': 'A', 'Qt.A': 47, 'FVM': 330},
            {'Nome': 'Malen', 'Squadra': 'Roma', 'R': 'A', 'Qt.A': 53, 'FVM': 350},
            {'Nome': 'Kolo Muani', 'Squadra': 'Juventus', 'R': 'A', 'Qt.A': 44, 'FVM': 310},
            {'Nome': 'Ramos G.', 'Squadra': 'Milan', 'R': 'A', 'Qt.A': 46, 'FVM': 315},
            {'Nome': 'Hojlund', 'Squadra': 'Napoli', 'R': 'A', 'Qt.A': 47, 'FVM': 300},
            {'Nome': 'Douvikas', 'Squadra': 'Como', 'R': 'A', 'Qt.A': 40, 'FVM': 240}
        ])
    return df

listone_df = safe_load_listone()

API_KEY = st.secrets.get("FOOTBALL_API_KEY", None)

@st.cache_data(ttl=86400)
def get_live_player_stats(player_name, team_name):
    if not API_KEY:
        return None
    
    url = "https://v3.football.api-sports.io/players"
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    params = {'search': player_name, 'league': '135', 'season': '2026'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data.get('response'):
            player_info = data['response'][0]
            stats = player_info['statistics'][0]
            
            apps = stats['games'].get('appearences') or 0
            shots_total = stats.get('shots', {}).get('total') or 0
            
            return {
                "appearances": apps,
                "minutes": stats['games'].get('minutes') or 0,
                "rating": stats['games'].get('rating') or "N.D.",
                "goals": stats['goals'].get('total') or 0,
                "assists": stats['goals'].get('assists') or 0,
                "yellow_cards": stats['cards'].get('yellow') or 0,
                "red_cards": stats['cards'].get('red') or 0,
                "shots_per_game": round(shots_total / apps, 2) if apps > 0 else 0.0,
                "is_injured": player_info['player'].get('injured', False),
                "photo": player_info['player'].get('photo', "")
            }
    except Exception:
        pass
    return None

# ==============================================================================
# 5. INIZIALIZZAZIONE SESSION STATE & PERSISTENZA
# ==============================================================================
def load_state_from_disk():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

saved_data = load_state_from_disk()

if 'my_roster' not in st.session_state:
    st.session_state.my_roster = saved_data["my_roster"] if saved_data and "my_roster" in saved_data else []

if 'selected_keeper_club' not in st.session_state:
    st.session_state.selected_keeper_club = saved_data["selected_keeper_club"] if saved_data and "selected_keeper_club" in saved_data else 'Inter'

if 'custom_user_targets' not in st.session_state:
    st.session_state.custom_user_targets = saved_data.get("custom_user_targets", {'P': [], 'D': [], 'C': [], 'A': []}) if saved_data else {'P': [], 'D': [], 'C': [], 'A': []}

if 'opponents' not in st.session_state:
    if saved_data and "opponents" in saved_data:
        st.session_state.opponents = saved_data["opponents"]
    else:
        st.session_state.opponents = {
            f"Avversario {i+1}": {
                'name': f"Avversario {i+1}", 'budget': TOTAL_BUDGET, 'slots_left': TOTAL_SLOTS,
                'roster': {'P': [], 'D': [], 'C': [], 'A': []}
            } for i in range(9)
        }

if 'purchased_registry' not in st.session_state:
    st.session_state.purchased_registry = saved_data["purchased_registry"] if saved_data and "purchased_registry" in saved_data else {}

if 'history' not in st.session_state:
    st.session_state.history = saved_data["history"] if saved_data and "history" in saved_data else []

if 'quick_bid_val' not in st.session_state:
    st.session_state.quick_bid_val = 1

# NUOVA VARIABILE PER PENALI/SVINCOLI
if 'budget_adjustments' not in st.session_state:
    st.session_state.budget_adjustments = saved_data.get("budget_adjustments", 0) if saved_data else 0


def save_state_to_disk():
    state_data = {
        "my_roster": st.session_state.get("my_roster", []),
        "selected_keeper_club": st.session_state.get("selected_keeper_club", 'Inter'),
        "custom_user_targets": st.session_state.get("custom_user_targets", {'P': [], 'D': [], 'C': [], 'A': []}),
        "opponents": st.session_state.get("opponents", {}),
        "purchased_registry": st.session_state.get("purchased_registry", {}),
        "history": st.session_state.get("history", []),
        "budget_adjustments": st.session_state.get("budget_adjustments", 0), # SALVATAGGIO PENALI
        "last_saved": datetime.now().strftime("%H:%M:%S")
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
# ==============================================================================
# 6. SIDEBAR: STATO, GESTIONE & NOTIZIE
# ==============================================================================
st.sidebar.title("🎛️ Pannello di Controllo")

current_stage = st.sidebar.selectbox(
    "Fase d'Asta Attuale:",
    ["🧤 Portieri", "🛡️ Difensori", "⚙️ Centrocampisti", "⚽ Attaccanti", "🔄 Fase Mista / Libera"]
)

tot_spent = sum(p['price'] for p in st.session_state.my_roster)
# Calcolo con compensazione penali
tot_budget_left = TOTAL_BUDGET - tot_spent + st.session_state.get('budget_adjustments', 0)
tot_slots_needed = TOTAL_SLOTS - len(st.session_state.my_roster)
p_max_safe = tot_budget_left - (tot_slots_needed - 1) if tot_slots_needed > 0 else 0

st.sidebar.divider()
st.sidebar.markdown(f"**Budget Rimasto:** `{tot_budget_left} / 500 cr`")
st.sidebar.markdown(f"**Slot Mancanti:** `{tot_slots_needed} / 25`")
st.sidebar.markdown(f"**Pmax Assoluto:** `{p_max_safe} cr`")

st.sidebar.divider()
st.sidebar.markdown("**📊 Avanzamento Spesa Reparti:**")
for r_code, r_name in [('P', '🧤 Portieri'), ('D', '🛡️ Difensori'), ('C', '⚙️ Centrocampisti'), ('A', '⚽ Attaccanti')]:
    sp = get_dept_spent(r_code)
    cap = BASE_DEPT_BUDGET[r_code]
    ratio = min(1.0, sp / cap) if cap > 0 else 0.0
    st.sidebar.caption(f"{r_name}: **{sp} / {cap} cr**")
    st.sidebar.progress(ratio)

if tot_budget_left <= 190 and len([p for p in st.session_state.my_roster if p['role'] == 'A']) == 0:
    st.sidebar.error("🚨 **PANIC BUTTON ATTIVO:** Budget residuo sotto al 38%! Preserva i crediti per il bomber titolare.")

st.sidebar.divider()
st.sidebar.markdown("**🔒 Lock-in Strategy (Slot Bloccati)**")
lock_in_active = st.sidebar.toggle("Congela crediti per i Top", value=st.session_state.get('lock_in_active', False))
st.session_state.lock_in_active = lock_in_active

if lock_in_active:
    locked_cr = 0
    locked_sl = 0
    purchased_names = [p['name'] for p in st.session_state.get('my_roster', [])]
    for r_code in ['P', 'D', 'C', 'A']:
        for t_name in st.session_state.get('custom_user_targets', {}).get(r_code, []):
            if t_name not in purchased_names:
                row = listone_df[listone_df['Nome'] == t_name]
                if not row.empty:
                    bt, _ = get_player_base_target(row.iloc[0])
                    locked_cr += bt
                    locked_sl += 1
    
    st.sidebar.info(f"❄️ **Congelati:** `{locked_cr} cr` per `{locked_sl}` slot\n\n💰 **Cassa Libera Reale:** `{tot_budget_left - locked_cr} cr`")

st.sidebar.divider()
col_sb1, col_sb2 = st.sidebar.columns(2)
if col_sb1.button("💾 Salva", use_container_width=True):
    save_state_to_disk()
    st.sidebar.success("Stato salvato!")

if col_sb2.button("↩️ Undo", use_container_width=True, help="Annulla l'ultima assegnazione"):
    if st.session_state.history:
        last_action = st.session_state.history.pop()
        b_name = last_action['buyer']
        p_name = last_action['name']
        p_price = last_action['price']
        p_role = last_action['role']

        if b_name == "La Mia Squadra":
            st.session_state.my_roster = [p for p in st.session_state.my_roster if p['name'] != p_name]
        else:
            for opp_k, opp_v in st.session_state.opponents.items():
                if opp_v['name'] == b_name:
                    opp_v['budget'] += p_price
                    opp_v['slots_left'] += 1
                    opp_v['roster'][p_role] = [p for p in opp_v['roster'][p_role] if p['name'] != p_name]
                    break

        if p_name in st.session_state.purchased_registry:
            del st.session_state.purchased_registry[p_name]

        save_state_to_disk()
        st.sidebar.warning(f"Annullato acquisto di {p_name}!")
        st.rerun()

with st.sidebar.expander("📰 Live News & Calciomercato (RSS Feed)"):
    try:
        feed = feedparser.parse("https://www.gazzetta.it/rss/calcio.xml")
        for entry in feed.entries[:5]:
            st.markdown(f"• **[{entry.title}]({entry.link})**")
    except Exception:
        st.caption("Feed notizie non disponibile offline.")

if st.sidebar.button("🗑️ Reset Completo Asta"):
    if os.path.exists(SAVE_FILE):
        try:
            os.remove(SAVE_FILE)
        except Exception:
            pass
    st.session_state.clear()
    st.rerun()

# ==============================================================================
# 7. HEADER & METRICHE GENERALI
# ==============================================================================
st.title("⚽ FantaAsta 2026/27 Pro Master Suite")
st.caption(f"Fase Attiva: **{current_stage}** | Modificatore Difesa: **Attivo** | Motore Dinamico: **Real-Time Active**")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Budget Rimanente", f"{tot_budget_left} cr", f"-{tot_spent} spesi")
m2.metric("Slot Mancanti", f"{tot_slots_needed} / 25")
m3.metric("Offerta Max Sicura (Pmax)", f"{p_max_safe} cr")
m4.metric("Media/Slot Rimanente", f"{(tot_budget_left / max(1, tot_slots_needed)):.1f} cr")

# Valutazione globale per il Panic Button
panic_mode = tot_budget_left <= 190 and get_dept_count('A') == 0

if panic_mode:
    st.error("""
    🚨 **PANIC BUTTON ATTIVO - MODALITÀ DIFESA DEL BUDGET!** 🚨\n
    Hai raggiunto la **soglia critica del 38% del budget** (≤ 190 cr) senza aver acquistato alcun attaccante titolare. 
    Per garantirti i fondi necessari all'acquisto dei bomber, il sistema ha **forzato il tetto d'asta massimo a 1 credito** per tutti i restanti giocatori di movimento (P, D, C). Smetti di rilanciare!
    """)

st.divider()

# ==============================================================================
# 8. TABS DELL'APPLICAZIONE (SUITE COMPLETA 10 TAB)
# ==============================================================================
tab_call, tab_roadmap, tab_tactics, tab_field, tab_barometer, tab_duel, tab_opps, tab_inspect, tab_defense, tab_export = st.tabs([
    "⚡ Assegnazione Live",
    "🗺️ Roadmap Dinamica",
    "📖 Guida Tattica 20 Squadre",
    "🏟️ Simulatore 11 Titolare",
    "🌡️ Barometro Lega (5000 cr)",
    "⚔️ Testa a Testa (Duello)",
    "👥 Tracker Rivali (Pmax)",
    "🔍 Ispezione Rose",
    "🛡️ Griglia Difesa & Portieri",
    "📥 Esportazione & Report"
])

# ------------------------------------------------------------------------------
# TAB 1: CHIAMATA & ASSEGNAZIONE LIVE
# ------------------------------------------------------------------------------
with tab_call:
    st.subheader(f"Chiamata & Analisi Istantanea Giocatore ({current_stage})")
    
    role_filter_map = {"🧤 Portieri": "P", "🛡️ Difensori": "D", "⚙️ Centrocampisti": "C", "⚽ Attaccanti": "A"}
    active_role = role_filter_map.get(current_stage, None)
    
    if active_role:
        sub_df = listone_df[listone_df['R'] == active_role]
    else:
        sub_df = listone_df

    available_names = [n for n in sub_df['Nome'].dropna().unique() if n not in st.session_state.purchased_registry]
    
    if 'target_call_player' not in st.session_state:
        st.session_state.target_call_player = available_names[0] if available_names else "Nessun dato"
        
    if st.session_state.target_call_player not in available_names and available_names:
        st.session_state.target_call_player = available_names[0]
        
    try:
        default_idx = available_names.index(st.session_state.target_call_player)
    except ValueError:
        default_idx = 0

    col_p1, col_p2, col_p3, col_p4 = st.columns([3, 1, 2, 2])
    with col_p1:
        sel_player = st.selectbox("Cerca Calciatore Chiamato", options=available_names if available_names else ["Nessun dato"], index=default_idx)
        st.session_state.target_call_player = sel_player
        
    player_info = listone_df[listone_df['Nome'] == sel_player].iloc[0] if sel_player != "Nessun dato" else None
    player_role = str(player_info['R']).strip() if player_info is not None else "C"
    player_team = str(player_info['Squadra']).strip() if player_info is not None else ""
    player_qta = int(player_info['Qt.A']) if player_info is not None and 'Qt.A' in player_info else 1
    player_fvm = int(player_info['FVM']) if player_info is not None and 'FVM' in player_info else 1

    if player_info is not None:
        eval_data = calculate_dynamic_player_evaluation(player_info, st.session_state.my_roster)
        dyn_target = eval_data["dyn_target"]
        dyn_max_bid = eval_data["dyn_max_bid"]
        base_target = eval_data["base_target"]
    else:
        dyn_target, dyn_max_bid, base_target = 1, 1, 1

    if 'last_selected_player' not in st.session_state or st.session_state.last_selected_player != sel_player:
        st.session_state.last_selected_player = sel_player
        st.session_state.quick_bid_val = int(round(dyn_target)) if dyn_target > 0 else 1

    with col_p2:
        bid_price = st.number_input("Prezzo Asta (cr)", min_value=1, max_value=max(1, tot_budget_left), value=min(max(1, tot_budget_left), st.session_state.quick_bid_val))
        st.session_state.quick_bid_val = bid_price
        
    with col_p3:
        opp_options = [st.session_state.opponents[k]['name'] for k in st.session_state.opponents]
        dest_buyer_name = st.selectbox("Aggiudicato a:", options=["La Mia Squadra"] + opp_options)
        
    with col_p4:
        st.write("")
        st.write("")
        btn_confirm = st.button("Conferma Assegnazione", use_container_width=True)

    st.markdown("**⚡ Rilancio Rapido Keypad:**")
    kp1, kp2, kp3, kp4 = st.columns(4)
    if kp1.button("➕ 1 cr", use_container_width=True):
        st.session_state.quick_bid_val = min(p_max_safe, bid_price + 1)
        st.rerun()
    if kp2.button("➕ 5 cr", use_container_width=True):
        st.session_state.quick_bid_val = min(p_max_safe, bid_price + 5)
        st.rerun()
    if kp3.button("➕ 10 cr", use_container_width=True):
        st.session_state.quick_bid_val = min(p_max_safe, bid_price + 10)
        st.rerun()
    if kp4.button("🔥 All-in Pmax", use_container_width=True):
        st.session_state.quick_bid_val = p_max_safe
        st.rerun()

    if player_info is not None:
        st.markdown("#### 🔍 Valutazione Tattica Adattata alla tua Cassa & Rosa")
        
        c_eval1, c_eval2, c_eval3, c_eval4 = st.columns(4)
        c_eval1.metric("Squadra & Ruolo", f"{player_team} ({player_role})", f"Qt: {player_qta} | FVM: {player_fvm}")
        
        delta_val = int(round(dyn_target - base_target))
        target_delta_str = f"{delta_val:+d} cr vs listino" if delta_val != 0 else "In linea con target"
        c_eval2.metric("Target Adattato alla Cassa", f"{int(round(dyn_target))} cr", target_delta_str)
        c_eval3.metric("Stop-Loss Dinamica", f"{int(round(dyn_max_bid))} cr", "Tetto massimo di sicurezza")
        c_eval4.metric(f"Cassa Reparto ({player_role})", f"{eval_data['dept_budget_left']} cr", f"{eval_data['dept_slots_left']} slot liberi")

        live_stats = get_live_player_stats(sel_player, player_team)
        if live_stats:
            st.markdown("##### 📈 Statistiche Avanzate & Scouting (API-Football)")
            
            logo_url = get_team_logo_url(player_team)
            st.markdown(f"""
                <div style="display:flex; align-items:center; gap: 15px; margin-bottom: 15px;">
                    <img src="{live_stats['photo']}" width="60" style="border-radius:50%; border: 2px solid #3b82f6;">
                    <img src="{logo_url}" width="40">
                    <h4 style="margin:0;">Status Fisico: {'🔴 Infortunato' if live_stats['is_injured'] else '🟢 Disponibile'}</h4>
                </div>
            """, unsafe_allow_html=True)
            
            st_col1, st_col2, st_col3, st_col4 = st.columns(4)
            st_col1.metric("Pres. / Minuti", f"{live_stats['appearances']} ({live_stats['minutes']} min)")
            st_col2.metric("Gol / Assist", f"⚽ {live_stats['goals']} | 🎯 {live_stats['assists']}")
            st_col3.metric("Tiri a Partita", f"🎯 {live_stats['shots_per_game']}")
            st_col4.metric("Cartellini", f"🟨 {live_stats['yellow_cards']} | 🟥 {live_stats['red_cards']}")

        threat_opps = []
        for ok, ov in st.session_state.opponents.items():
            opp_role_count = len(ov['roster'][player_role])
            opp_role_limit = SLOTS[player_role]
            if opp_role_count < opp_role_limit and ov['budget'] >= dyn_target:
                pmax_opp = ov['budget'] - (ov['slots_left'] - 1)
                threat_opps.append((ov['name'], pmax_opp, opp_role_limit - opp_role_count))
        
        threat_opps.sort(key=lambda x: x[1], reverse=True)
        if threat_opps:
            top_threat = threat_opps[0]
            st.info(f"🎯 **AI Opponent Predictor:** L'avversario più pericoloso su **{sel_player}** è **{top_threat[0]}** (Pmax: `{top_threat[1]} cr`, ha ancora `{top_threat[2]}` slot {player_role} liberi).")

        pen_info = PENALTY_TAKERS.get(player_team, [])
        is_penalty = [p for p in pen_info if sel_player.lower() in p.lower()]
        pen_str = f"⚽ Rigorista: {is_penalty[0]}" if is_penalty else "Nessun rigore primario"
        st.caption(f"📌 **Status Piazzati:** {pen_str}")

        if eval_data["is_full"]:
            st.error(f"🚫 **REPARTO {player_role} COMPLETO:** Hai già riempito tutti gli slot previsti per questo ruolo!")
        elif bid_price <= dyn_target:
            st.success(f"🟢 **OTTIMO PREZZO:** {bid_price} cr è perfettamente in target per la tua cassa. Rilancia!")
        elif bid_price <= dyn_max_bid:
            st.warning(f"🟡 **IN SICUREZZA:** {bid_price} cr è accettabile (Stop-Loss: {dyn_max_bid} cr).")
        else:
            st.error(f"🔴 **STOP RILANCIO (Limite {dyn_max_bid} cr):** Il prezzo supera la stop-loss. Lascialo all'avversario!")

    if btn_confirm and sel_player != "Nessun dato":
        if dest_buyer_name == "La Mia Squadra":
            if get_dept_count(player_role) < SLOTS[player_role]:
                st.session_state.my_roster.append({
                    'name': sel_player, 'team': player_team, 'role': player_role, 'price': bid_price
                })
                st.session_state.purchased_registry[sel_player] = ("La Mia Squadra", bid_price)
                
                if player_role == 'P' and player_team in GOALIE_HIERARCHY:
                    st.session_state.selected_keeper_club = player_team
                
                st.session_state.history.append({
                    'buyer': "La Mia Squadra", 'name': sel_player, 'team': player_team, 'role': player_role, 'price': bid_price
                })
                save_state_to_disk()
                st.success(f"{sel_player} acquistato a {bid_price} cr!")
                st.rerun()
            else:
                st.error(f"Reparto {player_role} già completato!")
        else:
            target_opp_key = next((k for k, v in st.session_state.opponents.items() if v['name'] == dest_buyer_name), None)
            if target_opp_key:
                opp_obj = st.session_state.opponents[target_opp_key]
                opp_obj['budget'] -= bid_price
                opp_obj['slots_left'] -= 1
                opp_obj['roster'][player_role].append({'name': sel_player, 'team': player_team, 'price': bid_price})
                st.session_state.purchased_registry[sel_player] = (dest_buyer_name, bid_price)

                if player_role == 'P' and get_dept_count('P') == 0:
                    current_first_p = GOALIE_HIERARCHY.get(st.session_state.selected_keeper_club, [(None,)])[0][0]
                    if sel_player == current_first_p:
                        for fb_club in ['Como', 'Juventus', 'Roma', 'Atalanta', 'Milan', 'Fiorentina']:
                            if GOALIE_HIERARCHY[fb_club][0][0] not in st.session_state.purchased_registry:
                                st.session_state.selected_keeper_club = fb_club
                                break

                st.session_state.history.append({
                    'buyer': dest_buyer_name, 'name': sel_player, 'team': player_team, 'role': player_role, 'price': bid_price
                })
                save_state_to_disk()
                st.info(f"{sel_player} assegnato a {dest_buyer_name} per {bid_price} cr.")
                st.rerun()

    # ---------------------------------------------------------
    # SCHEDA CONSIGLIATI DALLA ROADMAP (AGGIORNATA & PROFONDA)
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("### 💡 I tuoi prossimi obiettivi (Roadmap)")
    
    roles_to_check = [active_role] if active_role else ['P', 'D', 'C', 'A']
    recs = []
    
    temp_allocated = set(p['name'] for p in st.session_state.get('my_roster', []))
    purchased_reg = st.session_state.get('purchased_registry', {})
    
    for r in roles_to_check:
        slots_total = SLOTS[r]
        bought_count = get_dept_count(r)
        slots_left = slots_total - bought_count
        
        if slots_left > 0:
            dyn_targets = calculate_dynamic_targets_for_slots(r, st.session_state.get('my_roster', []))
            
            user_custom_picks = list(st.session_state.get('custom_user_targets', {}).get(r, []))
            
            if r == 'P':
                k_club = st.session_state.get('selected_keeper_club', 'Inter')
                k_list = GOALIE_HIERARCHY.get(k_club, [])
                for k_info in k_list:
                    if k_info[0] not in user_custom_picks:
                        user_custom_picks.append(k_info[0])
            
            for idx in range(min(slots_left, 4)): 
                if idx < len(dyn_targets):
                    t_budget = dyn_targets[idx]
                    
                    slot_res = get_dynamic_slot_candidates(r, t_budget, purchased_reg, temp_allocated, custom_user_targets_list=user_custom_picks)
                    
                    if slot_res['chosen_name'] != "Scommessa / Copertura":
                        is_custom = slot_res['chosen_role'] == "🎯 Mio Top Selezionato"
                        
                        card_style = "🤖 Consigliato"
                        if is_custom:
                            if r == 'P' and slot_res['chosen_name'] in [k[0] for k in GOALIE_HIERARCHY.get(st.session_state.get('selected_keeper_club', 'Inter'), [])] and slot_res['chosen_name'] not in st.session_state.get('custom_user_targets', {}).get('P', []):
                                card_style = f"🧱 Blocco {st.session_state.get('selected_keeper_club', 'Inter')}"
                            else:
                                card_style = "🎯 Tuo Top"

                        recs.append({
                            'name': slot_res['chosen_name'],
                            'team': slot_res['chosen_team'],
                            'role': r,
                            'target': slot_res['dyn_target'],
                            'max': slot_res['dyn_max_bid'],
                            'is_custom': is_custom,
                            'card_style': card_style
                        })
                        temp_allocated.add(slot_res['chosen_name'])
                        
                        if len(recs) >= 4:
                            break
        if len(recs) >= 4:
            break
            
    if recs:
        recs = sorted(recs, key=lambda x: x['is_custom'], reverse=True)
        
        rec_cols = st.columns(min(4, len(recs)))
        for i, rec in enumerate(recs[:4]):
            with rec_cols[i]:
                st.info(f"**{rec['role']} | {rec['name']}** ({rec['team']})\n\n{rec['card_style']}\n\n🎯 Target: `{rec['target']} cr`\n🛑 Max: `{rec['max']} cr`")
                
                if st.button(f"📢 Chiama", key=f"btn_call_rec_{rec['name']}_{i}", use_container_width=True):
                    st.session_state.target_call_player = rec['name']
                    st.rerun()
    else:
        st.caption("Nessun giocatore primario consigliato per questo filtro. Sei a posto con i titolari, punta su scommesse a 1 cr!")

# ------------------------------------------------------------------------------
# TAB 2: ROADMAP DINAMICA CON SELETTORE TOP & RE-TIERING
# ------------------------------------------------------------------------------
with tab_roadmap:
    st.subheader("🗺️ Roadmap & Strategia Ricalcolata con Re-Tiering Dinamico")
    
    with st.expander("⭐ Personalizza i Miei Top di Reparto (Lock-in Strategy)", expanded=False):
        st.caption("Seleziona uno o più giocatori ideali che intendi prendere: la Roadmap si riorganizzerà istantaneamente calibrando tutti gli altri slot in funzione della spesa per i tuoi prescelti.")
        
        c_tp, c_td, c_tc, c_ta = st.columns(4)
        with c_tp:
            p_names = listone_df[listone_df['R'] == 'P']['Nome'].dropna().tolist()
            sel_p_top = st.multiselect("Top Portieri:", options=p_names, default=st.session_state.custom_user_targets.get('P', []))
            st.session_state.custom_user_targets['P'] = sel_p_top
        with c_td:
            d_names = listone_df[listone_df['R'] == 'D']['Nome'].dropna().tolist()
            sel_d_top = st.multiselect("Top Difensori:", options=d_names, default=st.session_state.custom_user_targets.get('D', []))
            st.session_state.custom_user_targets['D'] = sel_d_top
        with c_tc:
            c_names = listone_df[listone_df['R'] == 'C']['Nome'].dropna().tolist()
            sel_c_top = st.multiselect("Top Centrocampisti:", options=c_names, default=st.session_state.custom_user_targets.get('C', []))
            st.session_state.custom_user_targets['C'] = sel_c_top
        with c_ta:
            a_names = listone_df[listone_df['R'] == 'A']['Nome'].dropna().tolist()
            sel_a_top = st.multiselect("Top Attaccanti:", options=a_names, default=st.session_state.custom_user_targets.get('A', []))
            st.session_state.custom_user_targets['A'] = sel_a_top

    selected_cat = st.selectbox(
        "Seleziona Categoria da Visualizzare:",
        ["Panoramica Completa", "🧤 Portieri (P)", "🛡️ Difensori (D)", "⚙️ Centrocampisti (C)", "⚽ Attaccanti (A)"]
    )

    if selected_cat in ["Panoramica Completa", "🧤 Portieri (P)"]:
        k_club = st.session_state.selected_keeper_club
        st.markdown(f"### 🧤 Portieri (Blocco Base: **{k_club}**)")
        
        k_list = GOALIE_HIERARCHY.get(k_club, [])
        p_bought = [p for p in st.session_state.my_roster if p['role'] == 'P']
        
        co_starter_lost = False
        lost_co_name = ""
        lost_co_buyer = ""
        lost_co_price = 0
        
        if len(p_bought) >= 1 and len(k_list) > 1:
            co_name = k_list[1][0]
            if co_name in st.session_state.purchased_registry:
                b_name, b_price = st.session_state.purchased_registry[co_name]
                if b_name != "La Mia Squadra":
                    co_starter_lost = True
                    lost_co_name = co_name
                    lost_co_buyer = b_name
                    lost_co_price = b_price

        if co_starter_lost:
            st.warning(f"🚨 **Allerta Vice Mancante:** {lost_co_name} è stato acquistato da **{lost_co_buyer}** a `{lost_co_price} cr`! Sfrutta gli **Incroci di Calendario Casa/Fuori** per completare la porta.")
            
            st.markdown("#### 📅 Migliori Incroci di Calendario Casa/Fuori:")
            suggested_pairings = GOALKEEPER_PAIRINGS.get(k_club, GOALKEEPER_PAIRINGS['Inter'])
            
            pair_cols = st.columns(min(3, len(suggested_pairings)))
            for p_idx, pair_info in enumerate(suggested_pairings[:3]):
                with pair_cols[p_idx]:
                    card_text = f"**{pair_info['club']}: {pair_info['starter']}**\n\n🎯 **Target:** `{pair_info['target']} cr` | 🛑 **Max:** `{pair_info['max']} cr`\n\n📊 *Incrocio:* {pair_info['diff']}\n\n💡 *Motivazione:* {pair_info['reason']}"
                    st.info(card_text)
            st.markdown("---")

        kp_cols = st.columns(3)
        for idx, (k_col, k_info) in enumerate(zip(kp_cols, k_list)):
            with k_col:
                if idx < len(p_bought):
                    p_b = p_bought[idx]
                    card_text = f"**POR {idx+1}: {p_b['name']}** ({p_b['team']})\n\n✅ **Acquistato:** `{p_b['price']} cr`\n\n📌 *Ruolo:* Titolare in Rosa"
                    st.success(card_text)
                else:
                    if idx == 1 and co_starter_lost:
                        top_pair = GOALKEEPER_PAIRINGS.get(k_club, GOALKEEPER_PAIRINGS['Inter'])[0]
                        card_text = f"**POR 2: {top_pair['starter']}** ({top_pair['club']})\n\n⚠️ *Incrocio Calendario Consigliato*\n\n🎯 **Target:** `{top_pair['target']} cr` | 🛑 **Max:** `{top_pair['max']} cr`\n\n📌 *Ruolo:* **Alternanza con {p_bought[0]['name']}**"
                        st.info(card_text)
                    else:
                        card_text = f"**POR {idx+1}: {k_info[0]}** ({k_club})\n\n🎯 **Target:** `{k_info[1]} cr` | 🛑 **Max:** `{k_info[2]} cr`\n\n📌 *Ruolo:* **Copertura Blocco {k_club}**"
                        st.info(card_text)
        st.divider()

    if selected_cat in ["Panoramica Completa", "🛡️ Difensori (D)"]:
        render_role_card_grid('D', "🛡️ Difensori (Pilastro Modificatore - Budget: 95 cr)", num_cols=4)
        st.divider()

    if selected_cat in ["Panoramica Completa", "⚙️ Centrocampisti (C)"]:
        render_role_card_grid('C', "⚙️ Centrocampisti (Motore dei Bonus - Budget: 155 cr)", num_cols=4)
        st.divider()

    if selected_cat in ["Panoramica Completa", "⚽ Attaccanti (A)"]:
        render_role_card_grid('A', "⚽ Attaccanti (Finalizzatori - Budget: 215 cr)", num_cols=3)

# ------------------------------------------------------------------------------
# TAB 3: GUIDA TATTICA DELLE 20 SQUADRE
# ------------------------------------------------------------------------------
with tab_tactics:
    st.subheader("📖 Guida Tattica Integrale delle 20 Squadre di Serie A 2026/2027")
    sel_team_guide = st.selectbox("Seleziona Club da Consultare:", options=sorted(list(TEAMS_TACTICAL_DB.keys())))
    team_data = TEAMS_TACTICAL_DB[sel_team_guide]

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        st.markdown(f"### 🛡️ {sel_team_guide}")
        st.markdown(f"**👔 Allenatore:** {team_data['coach']}")
        st.markdown(f"**📐 Modulo Tattico:** {team_data['formation']}")
        st.markdown(f"**🧤 Gerarchia Porta:** {team_data['gk']}")
        st.markdown(f"**🛡️ Linea Difensiva:** {team_data['defense']}")
        st.markdown(f"**⚙️ Centrocampo:** {team_data['midfield']}")
        st.markdown(f"**⚽ Reparto Offensivo:** {team_data['attack']}")

    with col_t2:
        st.markdown("### 🎯 Gerarchia Rigoristi & Tiratori")
        for r_idx, r_name in enumerate(team_data['penalties']):
            st.markdown(f"- **{r_name}**")
        
        st.markdown("### 💡 Consigli d'Asta & Scommesse")
        st.info(team_data['advice'])

# ------------------------------------------------------------------------------
# TAB 4: SIMULATORE 11 TITOLARE (CAMPO TATTICO 2D INTERATTIVO)
# ------------------------------------------------------------------------------
with tab_field:
    st.subheader("🏟️ Lavagna Tattica 11 Titolare")
    
    col_f_opt, col_f_metrics = st.columns([1, 2])
    with col_f_opt:
        formation_pref = st.radio("Modulo Titolare:", ["4-3-3 (Modificatore Difesa)", "3-4-3 (Tridente Offensivo)"])
    
    p_my = [p for p in st.session_state.my_roster if p['role'] == 'P']
    d_my = sorted([p for p in st.session_state.my_roster if p['role'] == 'D'], key=lambda x: x['price'], reverse=True)
    c_my = sorted([p for p in st.session_state.my_roster if p['role'] == 'C'], key=lambda x: x['price'], reverse=True)
    a_my = sorted([p for p in st.session_state.my_roster if p['role'] == 'A'], key=lambda x: x['price'], reverse=True)

    if "4-3-3" in formation_pref:
        req_p, req_d, req_c, req_a = 1, 4, 3, 3
    else:
        req_p, req_d, req_c, req_a = 1, 3, 4, 3

    starters_p = p_my[:req_p]
    starters_d = d_my[:req_d]
    starters_c = c_my[:req_c]
    starters_a = a_my[:req_a]
    total_starters_count = len(starters_p) + len(starters_d) + len(starters_c) + len(starters_a)

    with col_f_metrics:
        m_t1, m_t2, m_t3 = st.columns(3)
        m_t1.metric("Titolari Disponibili", f"{total_starters_count} / 11")
        expected_points = 66.0 + (len(starters_d)*0.5) + (len(starters_c)*0.8) + (len(starters_a)*1.8)
        if "4-3-3" in formation_pref and len(starters_d) >= 4:
            expected_points += 3.0
        m_t2.metric("Punteggio Atteso Base", f"{expected_points:.1f} pt", "Target podio ≥ 72.5 pt")
        mod_status = "🟢 Attivo (+3/+6 pt)" if ("4-3-3" in formation_pref and len(starters_d) >= 4) else "⚪ Non attivo"
        m_t3.metric("Status Modificatore", mod_status)

    st.markdown("---")
    
    st.markdown('<div class="pitch-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="pitch-row">', unsafe_allow_html=True)
    for i in range(req_a):
        if i < len(starters_a):
            st.markdown(f'<div class="player-disc">⚽ <b>{starters_a[i]["name"]}</b><br><small>{starters_a[i]["price"]} cr</small></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="player-disc-empty">⚽ Attaccante {i+1}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="pitch-row">', unsafe_allow_html=True)
    for i in range(req_c):
        if i < len(starters_c):
            st.markdown(f'<div class="player-disc">⚙️ <b>{starters_c[i]["name"]}</b><br><small>{starters_c[i]["price"]} cr</small></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="player-disc-empty">⚙️ Centrocampista {i+1}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="pitch-row">', unsafe_allow_html=True)
    for i in range(req_d):
        if i < len(starters_d):
            st.markdown(f'<div class="player-disc">🛡️ <b>{starters_d[i]["name"]}</b><br><small>{starters_d[i]["price"]} cr</small></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="player-disc-empty">🛡️ Difensore {i+1}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="pitch-row">', unsafe_allow_html=True)
    if starters_p:
        st.markdown(f'<div class="player-disc">🧤 <b>{starters_p[0]["name"]}</b><br><small>{starters_p[0]["price"]} cr</small></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="player-disc-empty">🧤 Portiere</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 5: BAROMETRO INFLAZIONE LEGA (5000 CREDITI)
# ------------------------------------------------------------------------------
with tab_barometer:
    st.subheader("🌡️ Barometro Inflazione & Liquidità Lega (5.000 Crediti Totali)")
    
    total_league_budget = 5000
    my_sp = sum(p['price'] for p in st.session_state.my_roster)
    opps_sp = sum(TOTAL_BUDGET - o['budget'] for o in st.session_state.opponents.values())
    total_spent_league = my_sp + opps_sp
    total_rem_league = total_league_budget - total_spent_league
    
    total_slots_open = (25 - len(st.session_state.my_roster)) + sum(o['slots_left'] for o in st.session_state.opponents.values())
    avg_cr_slot = total_rem_league / max(1, total_slots_open)

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Cassa Residua Lega", f"{total_rem_league} / 5.000 cr", f"-{total_spent_league} cr spesi")
    b2.metric("Slot Totali Aperti", f"{total_slots_open} / 250")
    b3.metric("Media Crediti / Slot Lega", f"{avg_cr_slot:.1f} cr")
    
    deflation_on = avg_cr_slot < 10.0
    b4.metric("Fase di Mercato", "🔴 Crollo Prezzi (Deflazione)" if deflation_on else "🟢 Fase Calda / Top Player")

    st.markdown("---")
    if deflation_on:
        st.error("""
        🚨 **ALLERTA DEFLAZIONE ATTIVA:** La cassa media della lega è scesa sotto i 10 crediti per slot! 
        I rivali non hanno più liquidità per contendersi i giocatori. Ora puoi aggiudicarti tutti i tuoi 4°/5° slot d'attacco e centrocampo a **prezzo di saldo o a 1 credito**!
        """)
    else:
        st.info("""
        📊 **MERCATO IN EQUILIBRIO:** C'è ancora liquidità per i primi slot. Mantieni la disciplina sui tetti Stop-Loss e fai sfogare i rivali sui giocatori non prioritari.
        """)

# ------------------------------------------------------------------------------
# TAB 6: COMPARATORE LIVE "TESTA A TESTA" (DECISION DUEL)
# ------------------------------------------------------------------------------
with tab_duel:
    st.subheader("⚔️ Confronto Testa a Testa Live (Decision Duel)")
    
    all_player_names = sorted(list(listone_df['Nome'].dropna().unique()))
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        p_name_1 = st.selectbox("Seleziona Calciatore A:", options=all_player_names, index=0)
    with col_d2:
        p_name_2 = st.selectbox("Seleziona Calciatore B:", options=all_player_names, index=min(1, len(all_player_names)-1))

    if p_name_1 and p_name_2:
        row1 = listone_df[listone_df['Nome'] == p_name_1].iloc[0]
        row2 = listone_df[listone_df['Nome'] == p_name_2].iloc[0]
        
        eval1 = calculate_dynamic_player_evaluation(row1, st.session_state.my_roster)
        eval2 = calculate_dynamic_player_evaluation(row2, st.session_state.my_roster)

        col_card1, col_card2 = st.columns(2)
        with col_card1:
            st.markdown(f"### 🔵 {p_name_1}")
            st.markdown(f"**Squadra & Ruolo:** {row1['Squadra']} ({row1['R']})")
            st.markdown(f"**Target Adattato:** `{int(round(eval1['dyn_target']))} cr` | **Stop-Loss:** `{int(round(eval1['dyn_max_bid']))} cr`")
            st.markdown(f"**Quotazione Listone:** {row1['Qt.A']} | **FVM:** {row1['FVM']}")
            pen1 = [p for p in PENALTY_TAKERS.get(row1['Squadra'], []) if p_name_1.lower() in p.lower()]
            st.markdown(f"**Status Rigori:** {pen1[0] if pen1 else 'Nessuno'}")
            
        with col_card2:
            st.markdown(f"### 🔴 {p_name_2}")
            st.markdown(f"**Squadra & Ruolo:** {row2['Squadra']} ({row2['R']})")
            st.markdown(f"**Target Adattato:** `{int(round(eval2['dyn_target']))} cr` | **Stop-Loss:** `{int(round(eval2['dyn_max_bid']))} cr`")
            st.markdown(f"**Quotazione Listone:** {row2['Qt.A']} | **FVM:** {row2['FVM']}")
            pen2 = [p for p in PENALTY_TAKERS.get(row2['Squadra'], []) if p_name_2.lower() in p.lower()]
            st.markdown(f"**Status Rigori:** {pen2[0] if pen2 else 'Nessuno'}")

        st.divider()
        diff_cr = int(round(eval1['dyn_target'] - eval2['dyn_target']))
        if diff_cr > 0:
            st.info(f"💡 **Verdetto Economico:** {p_name_1} richiede **+{diff_cr} cr** rispetto a {p_name_2}. Scegli {p_name_2} se vuoi preservare budget per l'attacco.")
        elif diff_cr < 0:
            st.info(f"💡 **Verdetto Economico:** {p_name_2} richiede **+{abs(diff_cr)} cr** rispetto a {p_name_1}. Scegli {p_name_1} per risparmiare.")
        else:
            st.info(f"💡 **Verdetto Economico:** I due giocatori hanno lo stesso impatto economico ({int(round(eval1['dyn_target']))} cr).")

# ------------------------------------------------------------------------------
# TAB 7: TRACKER RIVALI & MAX BID
# ------------------------------------------------------------------------------
with tab_opps:
    st.subheader("👥 Quadro Generale Avversari & Potere d'Acquisto")
    opp_summary = []
    for k, v in st.session_state.opponents.items():
        p_max = v['budget'] - (v['slots_left'] - 1) if v['slots_left'] > 0 else 0
        opp_summary.append({
            "Squadra Rivale": v['name'],
            "Budget Residuo": f"{v['budget']} cr",
            "Slot Mancanti": f"{v['slots_left']} / {TOTAL_SLOTS}",
            "Max Bid Possibile (Pmax)": p_max,
            "P": f"{len(v['roster']['P'])}/3",
            "D": f"{len(v['roster']['D'])}/8",
            "C": f"{len(v['roster']['C'])}/8",
            "A": f"{len(v['roster']['A'])}/6",
            "Livello Minaccia": "🔴 ALTISSIMA" if p_max > 120 else ("🟡 MEDIA" if p_max > 45 else "🟢 INNOCUO")
        })
    st.dataframe(pd.DataFrame(opp_summary).sort_values(by="Max Bid Possibile (Pmax)", ascending=False), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 8: ISPEZIONE ROSE RIVALI & SVINCOLI
# ------------------------------------------------------------------------------
with tab_inspect:
    st.subheader("🔍 Ispezione Dettagliata Rosa Rivale & Gestione Svincoli")
    opp_names_list = [v['name'] for v in st.session_state.opponents.values()]
    selected_inspect_name = st.selectbox("Seleziona Squadra Rivale da Ispezionare:", options=opp_names_list)
    
    inspect_opp = next((v for v in st.session_state.opponents.values() if v['name'] == selected_inspect_name), None)
    if inspect_opp:
        c_i1, c_i2, c_i3 = st.columns(3)
        c_i1.metric("Budget Residuo", f"{inspect_opp['budget']} cr")
        c_i2.metric("Slot Completati", f"{TOTAL_SLOTS - inspect_opp['slots_left']} / {TOTAL_SLOTS}")
        p_max_opp = inspect_opp['budget'] - (inspect_opp['slots_left'] - 1) if inspect_opp['slots_left'] > 0 else 0
        c_i3.metric("Offerta Max (Pmax)", f"{p_max_opp} cr")
        
        st.markdown("#### Giocatori Acquistati")
        col_rp, col_rd, col_rc, col_ra = st.columns(4)
        with col_rp:
            st.markdown("**Portieri (P)**")
            for pl in inspect_opp['roster']['P']:
                st.write(f"• {pl['name']} ({pl['team']}) - **{pl['price']} cr**")
        with col_rd:
            st.markdown("**Difensori (D)**")
            for pl in inspect_opp['roster']['D']:
                st.write(f"• {pl['name']} ({pl['team']}) - **{pl['price']} cr**")
        with col_rc:
            st.markdown("**Centrocampisti (C)**")
            for pl in inspect_opp['roster']['C']:
                st.write(f"• {pl['name']} ({pl['team']}) - **{pl['price']} cr**")
        with col_ra:
            st.markdown("**Attaccanti (A)**")
            for pl in inspect_opp['roster']['A']:
                st.write(f"• {pl['name']} ({pl['team']}) - **{pl['price']} cr**")

    st.markdown("---")
    st.markdown("---")
    with st.expander("🔄 Mercato di Riparazione (Svincoli & Penali)", expanded=False):
        st.caption("Gestisci gli svincoli per la tua squadra o per gli avversari. I crediti verranno ricalcolati o penalizzati automaticamente in base alla regola scelta.")
        
        teams_list = ["La Mia Squadra"] + [v['name'] for v in st.session_state.opponents.values()]
        selected_drop_team = st.selectbox("Seleziona Squadra:", options=teams_list)

        if selected_drop_team == "La Mia Squadra":
            team_roster = st.session_state.my_roster
        else:
            opp_key = next(k for k, v in st.session_state.opponents.items() if v['name'] == selected_drop_team)
            opp_obj = st.session_state.opponents[opp_key]
            team_roster = []
            for r_list in opp_obj['roster'].values():
                team_roster.extend(r_list)

        if team_roster:
            player_names = [p['name'] for p in team_roster]
            sel_drop_player = st.selectbox("Seleziona Calciatore da Svincolare:", options=player_names)

            dropped_p = next(p for p in team_roster if p['name'] == sel_drop_player)
            orig_price = dropped_p['price']
            
            st.write(f"💵 Prezzo di acquisto originale: **{orig_price} cr**")

            drop_mode = st.radio("Regola di Recupero Crediti:", 
                                 ["Recupero 100% (Intero Prezzo)", "Recupero 50% (Metà Prezzo)", "Recupero 1 Credito", "Personalizzato"])
            
            custom_refund = 0
            if "Personalizzato" in drop_mode:
                custom_refund = st.number_input("Crediti da rimborsare:", min_value=0, max_value=orig_price, value=0)

            if st.button(f"✂️ Conferma Svincolo di {sel_drop_player}", type="primary"):
                if "100%" in drop_mode:
                    refund = orig_price
                elif "50%" in drop_mode:
                    refund = int(round(orig_price / 2))
                elif "1 Credito" in drop_mode:
                    refund = 1
                else:
                    refund = custom_refund

                # Processo per La Mia Squadra (richiede l'aggiustamento della penale)
                if selected_drop_team == "La Mia Squadra":
                    st.session_state.my_roster = [p for p in st.session_state.my_roster if p['name'] != sel_drop_player]
                    # Calcolo della penale: siccome l'algoritmo riaggiunge l'intero costo eliminando il giocatore, 
                    # applichiamo una compensazione negativa equivalente ai crediti "bruciati".
                    penalty = refund - orig_price
                    st.session_state.budget_adjustments += penalty
                
                # Processo per Avversari (il budget è una semplice variabile intera)
                else:
                    for r_code in ['P', 'D', 'C', 'A']:
                        opp_obj['roster'][r_code] = [p for p in opp_obj['roster'][r_code] if p['name'] != sel_drop_player]
                    opp_obj['budget'] += refund
                    opp_obj['slots_left'] += 1

                if sel_drop_player in st.session_state.purchased_registry:
                    del st.session_state.purchased_registry[sel_drop_player]

                st.session_state.history.append({
                    'buyer': selected_drop_team, 'name': sel_drop_player, 'team': dropped_p['team'],
                    'role': dropped_p.get('role', 'Sconosciuto'), 'price': -refund, 'action': 'SVINCOLO'
                })

                save_state_to_disk()
                st.success(f"✅ Svincolo eseguito! {selected_drop_team} ha recuperato {refund} cr. Il PMax globale è stato ricalcolato.")
                st.rerun()
        else:
            st.info(f"Nessun giocatore attualmente presente nella rosa di {selected_drop_team}.")
# ------------------------------------------------------------------------------
# TAB 9: GRIGLIA DIFESA & PORTIERI
# ------------------------------------------------------------------------------
with tab_defense:
    st.subheader("🛡️ Griglia Solidità Difensiva & Clean Sheet 2026/27")
    grid_data = [
        {"Club": "Inter", "Guida Tecnica": "Cristian Chivu (3-5-2)", "Solidità": "🟢🟢 Altissima", "Clean Sheet Attesi": "18 - 20", "Pilastro": "Dimarco / Bastoni", "Portiere": "J. Martínez / Provedel"},
        {"Club": "Como", "Guida Tecnica": "Cesc Fàbregas (4-2-3-1)", "Solidità": "🟢🟢 Altissima", "Clean Sheet Attesi": "17 - 19 (Record Butez)", "Pilastro": "Kempf / Yan Couto", "Portiere": "Jean Butez"},
        {"Club": "Roma", "Guida Tecnica": "3-4-2-1 Spinta", "Solidità": "🟢🟢 Altissima", "Clean Sheet Attesi": "17 - 18", "Pilastro": "Ndicka / Mancini", "Portiere": "Mile Svilar"},
        {"Club": "Juventus", "Guida Tecnica": "Luciano Spalletti (4-2-3-1)", "Solidità": "🟢🟢 Alta", "Clean Sheet Attesi": "15 - 17", "Pilastro": "Bremer / Kalulu", "Portiere": "Guglielmo Vicario"},
        {"Club": "Milan", "Guida Tecnica": "Rúben Amorim (3-4-2-1)", "Solidità": "🟢 Alta", "Clean Sheet Attesi": "14 - 16", "Pilastro": "Pavlovic / Gila", "Portiere": "Mike Maignan"},
        {"Club": "Napoli", "Guida Tecnica": "Massimiliano Allegri (4-3-3)", "Solidità": "🟢 Alta", "Clean Sheet Attesi": "15 - 17", "Pilastro": "Rrahmani / Beukema", "Portiere": "Alex Meret"},
        {"Club": "Atalanta", "Guida Tecnica": "Maurizio Sarri (4-3-3)", "Solidità": "🟢 Alta", "Clean Sheet Attesi": "14 - 16", "Pilastro": "Scalvini / Kristensen", "Portiere": "Marco Carnesecchi"},
        {"Club": "Fiorentina", "Guida Tecnica": "Fabio Grosso (4-3-3)", "Solidità": "🟡 Media-Alta", "Clean Sheet Attesi": "12 - 14", "Pilastro": "Radu Dragusin", "Portiere": "David De Gea"},
        {"Club": "Udinese", "Guida Tecnica": "3-5-2 Diretto", "Solidità": "🟡 Modificatore Top", "Clean Sheet Attesi": "11 - 13", "Pilastro": "Oumar Solet / Vojvoda", "Portiere": "Maduka Okoye"},
        {"Club": "Genoa", "Guida Tecnica": "Daniele De Rossi (3-5-2)", "Solidità": "🟡 Media-Alta", "Clean Sheet Attesi": "11 - 13", "Pilastro": "Leo Ostigard", "Portiere": "Justin Bijlow"}
    ]
    st.dataframe(pd.DataFrame(grid_data), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 10: ESPORTAZIONE & REPORT FINALE
# ------------------------------------------------------------------------------
with tab_export:
    st.subheader("📥 Esportazione Dati Rosa & Report Finale")
    
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_export_my = pd.DataFrame(st.session_state.my_roster) if st.session_state.my_roster else pd.DataFrame(columns=['name', 'team', 'role', 'price'])
        df_export_my.to_excel(writer, sheet_name='La Mia Rosa', index=False)
        
        opp_export_rows = []
        for k, v in st.session_state.opponents.items():
            for r_code, p_list in v['roster'].items():
                for pl in p_list:
                    opp_export_rows.append({
                        'Squadra Asta': v['name'],
                        'Giocatore': pl['name'],
                        'Club Serie A': pl.get('team', ''),
                        'Ruolo': r_code,
                        'Prezzo Pagato': pl['price']
                    })
        df_export_opps = pd.DataFrame(opp_export_rows) if opp_export_rows else pd.DataFrame(columns=['Squadra Asta', 'Giocatore', 'Club Serie A', 'Ruolo', 'Prezzo Pagato'])
        df_export_opps.to_excel(writer, sheet_name='Rose Rivali', index=False)

    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        st.download_button(
            label="📊 Scarica Report Completo Asta (Excel)",
            data=output_excel.getvalue(),
            file_name=f"FantaAsta_2026_27_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_ex2:
        json_backup_str = json.dumps({
            "my_roster": st.session_state.my_roster,
            "opponents": st.session_state.opponents,
            "purchased_registry": st.session_state.purchased_registry,
            "history": st.session_state.history
        }, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="💾 Scarica Backup JSON Asta",
            data=json_backup_str,
            file_name="fanta_auction_backup.json",
            mime="application/json",
            use_container_width=True
        )
