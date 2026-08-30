import streamlit as st
import pandas as pd
import numpy as np
import json
import io
import os
import requests
import feedparser
from datetime import datetime
import random
import time

# ==============================================================================
# 1. SETUP GENERALE & THEME STYLING
# ==============================================================================
st.set_page_config(
    page_title="FantaAsta 2026/27 Pro Master Suite",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Sfondo Antracite Profondo */
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    
    /* Metriche in stile Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(22, 27, 38, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 20px 24px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #64748B !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 34px !important;
        font-weight: 900 !important;
        color: #F8FAFC !important;
    }
    
    /* Stile Moderno Bottoni (Pillola & Hover Violetto) */
    div[data-testid="stButton"] button {
        border-radius: 50px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        color: #F8FAFC !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] button:hover {
        background: #8B5CF6 !important;
        border-color: #8B5CF6 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(139, 92, 246, 0.3) !important;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background: #8B5CF6 !important;
        border-color: #8B5CF6 !important;
    }
    
    /* Stile Tab: Gerarchia e Pillole */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 12px;
        border: none;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(22, 27, 38, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 50px;
        padding: 8px 22px;
        font-weight: 600;
        color: #94A3B8;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #8B5CF6 !important;
        color: #ffffff !important;
        border-color: #8B5CF6 !important;
        box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
    }

    /* Glass Cards per Roadmap e Consigliati */
    .glass-card {
        background: rgba(22, 27, 38, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 20px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        height: 100%;
        color: #F8FAFC;
        transition: transform 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(255, 255, 255, 0.1);
    }
    .glass-card-accent {
        border-color: rgba(139, 92, 246, 0.5);
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.1);
    }
    .glass-card-mini-text {
        font-size: 13px;
        color: #94A3B8;
        margin-top: 10px;
    }

    /* Simulatore Campo */
    .pitch-container {
        background: #161B26;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px;
        padding: 24px 16px;
        position: relative;
        margin-bottom: 20px;
    }
    .pitch-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin: 18px 0;
    }
    .player-disc {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
        border-radius: 16px;
        padding: 10px 16px;
        text-align: center;
        min-width: 120px;
        backdrop-filter: blur(6px);
    }
    .player-disc-empty {
        background: transparent;
        border: 1px dashed rgba(255, 255, 255, 0.2);
        color: #64748B;
        border-radius: 16px;
        padding: 10px 16px;
        text-align: center;
        min-width: 120px;
    }
    
    hr {
        border-color: rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. COSTANTI DI GIOCO & DATI
# ==============================================================================
SAVE_FILE = "fanta_auction_save.json"
TOTAL_BUDGET = 500
SLOTS = {'P': 3, 'D': 8, 'C': 8, 'A': 6}
TOTAL_SLOTS = sum(SLOTS.values())
BOT_PROFILES = ["Conservatore", "Smanioso", "Scommettitore", "Ostruzionista", "Equilibrato"]

STRATEGIES = {
    "Equilibrata (Mediana di Mercato)": {'P': 35, 'D': 95, 'C': 160, 'A': 210},
    "Rischio Calcolato (Centrocampo Dominante)": {'P': 30, 'D': 135, 'C': 210, 'A': 125},
    "Attacco Pesante (Stars & Scrubs)": {'P': 35, 'D': 75, 'C': 150, 'A': 240}
}

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
    "Frosinone": "512", "Como": "895", "Parma": "523", "Venezia": "517"
}

def get_team_logo_url(team_name):
    team_id = SERIE_A_LOGOS.get(team_name, "505")
    return f"https://media.api-sports.io/football/teams/{team_id}.png"

DOC_TARGETS = {
    "Malen Donyell": 141.20, "Malen": 141.20,
    "Martinez Lautaro": 132.29, "Lautaro Martinez": 132.29, "Martinez L.": 132.29,
    "Hojlund Rasmus": 125.13, "Hojlund": 125.13,
    "Kean Moise": 124.26, "Kean": 124.26,
    "Ramos Goncalo Matias": 104.96, "Ramos G.": 104.96, "Gonçalo Ramos": 104.96,
    "Yildiz Kenan": 102.07, "Yildiz": 102.07,
    "Thuram Marcus": 101.75, "Thuram": 101.75,
    "Paz Nico": 95.02, "Nico Paz": 95.02,
    "Kolo Muani Randal": 93.91, "Kolo Muani": 93.91,
    "Pulisic Christian": 72.81, "Pulisic": 72.81,
    "Calhanoglu Hakan": 72.98, "Calhanoglu": 72.98,
    "Scamacca Gianluca": 69.55, "Scamacca": 69.55,
    "McTominay Scott": 69.12, "McTominay": 69.12,
    "Orsolini Riccardo": 64.56, "Orsolini": 64.56,
    "Dimarco Federico": 64.05, "Dimarco": 64.05,
    "Douvikas Tasos": 62.16, "Douvikas": 62.16,
    "Mora Carvalho Rodrigo": 59.08, "Mora Carvalho": 59.08,
    "Davis Keinan": 54.63, "Davis K.": 54.63, "Davis": 54.63,
    "Jones Curtis": 53.92, "Jones": 53.92,
    "Dovbyk Artem": 53.68, "Dovbyk": 53.68,
    "De Ketelaere Charles": 51.38, "De Ketelaere": 51.38,
    "Krstovic Nikola": 51.03, "Krstovic": 51.03,
    "Alajbegovic Kerim-Sam": 50.14, "Alajbegovic": 50.14,
    "Simeone Giovanni": 48.83, "Simeone": 48.83,
    "Svilar Mile": 48.17, "Svilar": 48.17,
    "Esposito FP Francesco Pio": 47.28, "Esposito FP": 47.28, "Esposito F.P.": 47.28,
    "Dybala Paulo": 47.09, "Dybala": 47.09,
    "Lukaku Romelu": 44.67, "Lukaku": 44.67,
    "Atta Arthur": 43.99, "Atta": 43.99,
    "Da Silva Moreira Diego": 42.95, "Moreira Diego": 42.95, "Diego Moreira": 42.95,
    "De Bruyne Kevin": 42.92, "De Bruyne": 42.92,
    "Baturina Martin": 42.62, "Baturina": 42.62,
    "Meret Alex": 41.66, "Meret": 41.66,
    "Gudmundsson Albert": 41.63, "Gudmundsson": 41.63,
    "Berardi Domenico": 40.87, "Berardi": 40.87,
    "Da Cunha Lucas": 39.67, "Da Cunha": 39.67,
    "Zaccagni Mattia": 39.29, "Zaccagni": 39.29,
    "Raspadori Giacomo": 38.21, "Raspadori": 38.21,
    "Vlasic Nikola": 37.74, "Vlasic": 37.74,
    "Zaniolo Nicolò": 37.46, "Zaniolo": 37.46,
    "Mastantuono Franco": 37.27, "Mastantuono": 37.27,
    "Castro Santiago": 36.82, "Castro": 36.82,
    "Wesley França Lima": 36.67, "Wesley": 36.67, "Wesley França": 36.67,
    "Maignan Mike": 36.08, "Maignan": 36.08,
    "Barella Nicolò": 35.50, "Barella": 35.50,
    "Santos Alisson": 34.98, "Santos": 34.98,
    "Carnesecchi Marco": 34.95, "Carnesecchi": 34.95,
    "Rabiot Adrien": 34.59, "Rabiot": 34.59,
    "Conceicao Fernandes Francisco": 34.33, "Conceicao": 34.33,
    "Vicario Guglielmo": 34.19, "Vicario": 34.19,
    "Pinamonti Andrea": 33.50, "Pinamonti": 33.50,
    "Rowe Jonathan": 33.12, "Rowe": 33.12,
    "Leao Rafael": 33.07, "Leao": 33.07, "Leão Rafael": 33.07,
    "Martinez Josep": 32.69, "Martinez Jo.": 32.69, "Martinez J": 32.69,
    "Butez Jean": 31.21, "Butez": 31.21,
    "Diao Assane": 30.93, "Diao": 30.93,
    "McKennie Weston": 30.46, "McKennie": 30.46,
    "Di Lorenzo Giovanni": 30.29, "Di Lorenzo": 30.29,
    "Molina Nahuel": 29.88, "Molina": 29.88, "Molina N.": 29.88,
    "Bremer Gleison": 29.69, "Bremer": 29.69,
    "Lauriente Armand": 29.40, "Lauriente": 29.40,
    "Spence Djed": 28.35, "Spence": 28.35,
    "Bastoni Alessandro": 28.02, "Bastoni": 28.02,
    "Samardzic Lazar": 27.90, "Samardzic": 27.90,
    "Soule Matias": 27.12, "Soule": 27.12,
    "Ederson -": 27.00, "Ederson": 27.00, "Ederson Dos Santos": 27.00,
    "Mancini Gianluca": 26.90, "Mancini": 26.90,
    "Colombo Lorenzo": 26.29, "Colombo": 26.29,
    "Banda Lameck": 26.17, "Banda": 26.17,
    "Zielinski Piotr": 25.83, "Zielinski": 25.83,
    "Bisseck Yann Aurel": 25.73, "Bisseck": 25.73, "Bisseck Yann": 25.73,
    "Kone Manu": 25.54, "Kone M.": 25.54, "Manu Koné": 25.54,
    "Messias Junior": 25.03, "Messias": 25.03,
    "Thuram Khéphren": 24.90, "Thuram K": 24.90, "Khéphren Thuram": 24.90,
    "Taylor Kenneth": 24.65, "Taylor K.": 24.65,
    "Piccoli Roberto": 24.63, "Piccoli": 24.63,
    "Solet Oumar": 24.22, "Solet": 24.22,
    "Kalulu Pierre": 23.42, "Kalulu": 23.42,
    "Modric Luka": 23.35, "Modric": 23.35,
    "Audero Emil": 23.29, "Audero": 23.29,
    "Akanji Manuel": 23.16, "Akanji": 23.16,
    "Esposito S Sebastiano": 23.06, "Esposito S": 23.06,
    "Adams Che": 22.70, "Adams": 22.70, "Adams A.": 22.70, "Akor Adams": 22.70,
    "David Jonathan": 22.70, "David": 22.70,
    "Cambiaso Andrea": 22.43, "Cambiaso": 22.43,
    "Luis Henrique de Lima": 22.34, "Luis Henrique": 22.34,
    "Politano Matteo": 22.33, "Politano": 22.33,
    "Pavlovic Strahinja": 22.09, "Pavlovic": 22.09,
    "Anguissa André Zambo": 21.73, "Anguissa": 21.73,
    "Cutrone Patrick": 21.72, "Cutrone": 21.72,
    "Nkunku Christopher": 21.66, "Nkunku": 21.66,
    "Saelemaekers Alexis": 21.56, "Saelemaekers": 21.56,
    "Elmas Eljif": 21.34, "Elmas": 21.34,
    "Sucic Petar": 21.19, "Sucic": 21.19,
    "Rodriguez Jesús": 21.06, "Rodriguez": 21.06,
    "Perrone Maximo": 20.98, "Perrone": 20.98,
    "Ndicka Evan": 20.79, "Ndicka": 20.79,
    "Zapata Duvan": 20.71, "Zapata": 20.71,
    "Bonny Ange-Yoan": 20.67, "Bonny": 20.67,
    "Casadei Cesare": 20.61, "Casadei": 20.61,
    "Baldanzi Tommaso": 20.20, "Baldanzi": 20.20,
    "Pellegrini Lorenzo": 20.06, "Pellegrini": 20.06,
    "Ekkelenkamp Jurgen": 19.82, "Ekkelenkamp": 19.82,
    "Rrahmani Amir": 19.66, "Rrahmani": 19.66,
    "Gila Mario": 19.36, "Gila": 19.36,
    "Fagioli Nicolo": 19.11, "Fagioli": 19.11,
    "Morata Alvaro": 19.11, "Morata": 19.11,
    "Vitinha -": 18.91, "Vitinha": 18.91,
    "Stones John": 18.69, "Stones": 18.69,
    "Scalvini Giorgio": 18.16, "Scalvini": 18.16,
    "Lobotka Stanislav": 17.82, "Lobotka": 17.82,
    "Neres David Campos": 17.01, "Neres": 17.01,
    "Thorstvedt Kristian": 17.00, "Thorstvedt": 17.00,
    "Pasalic Mario": 16.88, "Pasalic": 16.88,
    "Isaksen Gustav": 16.81, "Isaksen": 16.81,
    "Bowie Kieron": 16.68, "Bowie": 16.68,
    "Estupinan Pervis": 16.23, "Estupinan": 16.23,
    "Montipo' Lorenzo": 15.19, "Montipo'": 15.19, "Montipo": 15.19,
    "Lovric Sandi": 14.77, "Lovric": 14.77,
    "Bayo Vakoun": 7.42, "Bayo": 7.42,
    "Mazzitelli Luca": 6.87, "Mazzitelli": 6.87,
    "Ziolkowski Jan": 5.85, "Ziolkowski": 5.85,
    "Joao Mario Neto Lopes": 5.03, "Joao Mario": 5.03,
    "Perin Mattia": 3.53, "Perin": 3.53,
    "Ilic Mihajlo": 3.18, "Ilic": 3.18,
    "Mendy Paul": 3.00, "Mendy": 3.00,
    "Milik Arek": 1.50, "Milik": 1.50,
    "Christensen Oliver": 1.23, "Christensen O.": 1.23,
    "Zelezny Radoslaw": 1.20, "Zelezny": 1.20,
    "Contini Nikita": 1.18, "Contini": 1.18,
    "Pinsoglio Carlo": 1.16, "Pinsoglio": 1.16,
    "Mlacic Branimir": 1.06, "Mlacic": 1.06,
    "Cremaschi Benjamín": 1.06, "Cremaschi": 1.06
}

ROLE_TIERED_POOLS = {
    'P': [
        {"tier_label": "Top Clean Sheet (5% - 10%)", "min_p": 25, "max_p": 50, "candidates": [
            {"name": "Svilar", "team": "Roma", "base_target": 48, "max": 55, "role": "Top Clean Sheet (18 CS)"},
            {"name": "Meret", "team": "Napoli", "base_target": 42, "max": 48, "role": "Titolare Napoli"},
            {"name": "Maignan", "team": "Milan", "base_target": 36, "max": 41, "role": "Top Portiere Amorim"},
            {"name": "Carnesecchi", "team": "Atalanta", "base_target": 35, "max": 40, "role": "Top Modificatore Sarri"},
            {"name": "Vicario", "team": "Juventus", "base_target": 34, "max": 39, "role": "Portiere Spalletti"},
            {"name": "Martinez Jo.", "team": "Inter", "base_target": 33, "max": 38, "role": "Titolare Inter Chivu"},
            {"name": "Butez", "team": "Como", "base_target": 31, "max": 36, "role": "Record 19 Clean Sheet"}
        ]},
        {"tier_label": "Portiere Rendimento / Semi-Top (3% - 5%)", "min_p": 15, "max_p": 24, "candidates": [
            {"name": "De Gea", "team": "Fiorentina", "base_target": 21, "max": 24, "role": "Esperienza Internazionale"},
            {"name": "Skorupski", "team": "Bologna", "base_target": 17, "max": 20, "role": "Affidabile Tedesco"},
            {"name": "Mandas", "team": "Lazio", "base_target": 15, "max": 17, "role": "Titolare Gattuso"},
            {"name": "Okoye", "team": "Udinese", "base_target": 14, "max": 16, "role": "Fisicità e Rendimento"}
        ]},
        {"tier_label": "Portiere Low-Cost / Alternanza (0% - 3%)", "min_p": 1, "max_p": 14, "candidates": [
            {"name": "Falcone", "team": "Lecce", "base_target": 12, "max": 14, "role": "Re del Modificatore"},
            {"name": "Milinkovic-Savic V.", "team": "Napoli", "base_target": 11, "max": 13, "role": "Co-titolare Napoli"},
            {"name": "Caprile", "team": "Cagliari", "base_target": 10, "max": 12, "role": "Titolare Pisacane"},
            {"name": "Bijlow", "team": "Genoa", "base_target": 9, "max": 10, "role": "Titolare De Rossi"},
            {"name": "Provedel", "team": "Inter", "base_target": 8, "max": 9, "role": "Copertura Porta Inter"},
            {"name": "Perri", "team": "Torino", "base_target": 4, "max": 5, "role": "Titolare Abate"},
            {"name": "Thiam", "team": "Monza", "base_target": 4, "max": 5, "role": "Titolare Low-Cost Jurić"}
        ]}
    ],
    'D': [
        {"tier_label": "Top Modificatore / Assist (4% - 13%)", "min_p": 20, "max_p": 65, "candidates": [
            {"name": "Dimarco", "team": "Inter", "base_target": 64, "max": 74, "role": "Top Assist / Piazzati (FM 7.64)"},
            {"name": "Wesley", "team": "Roma", "base_target": 37, "max": 43, "role": "Terzino di Spinta Modificatore (5 gol)"},
            {"name": "Di Lorenzo", "team": "Napoli", "base_target": 30, "max": 35, "role": "Intoccabile a Destra (FM 6.33)"},
            {"name": "Molina N.", "team": "Roma", "base_target": 30, "max": 35, "role": "Esterno Offensivo da Bonus"},
            {"name": "Bremer", "team": "Juventus", "base_target": 30, "max": 35, "role": "Top Difensore Modificatore (FM 6.81)"},
            {"name": "Bastoni", "team": "Inter", "base_target": 28, "max": 32, "role": "Garanzia 6.5 Modificatore (FM 6.34)"},
            {"name": "Mancini", "team": "Roma", "base_target": 27, "max": 31, "role": "Centrale Goleador / Saltatore (FM 6.51)"}
        ]},
        {"tier_label": "Centrale da Bonus / Saltatore (3% - 5%)", "min_p": 17, "max_p": 26, "candidates": [
            {"name": "Bisseck", "team": "Inter", "base_target": 26, "max": 30, "role": "Centrale in Ascesa da Bonus (FM 6.65)"},
            {"name": "Solet", "team": "Udinese", "base_target": 24, "max": 28, "role": "Centrale Regista Aggiunto (FM 6.40)"},
            {"name": "Akanji", "team": "Inter", "base_target": 23, "max": 26, "role": "Centrale Titolare Senza Malus (FM 6.41)"},
            {"name": "Kalulu", "team": "Juventus", "base_target": 23, "max": 26, "role": "Titolare Fisso Senza Sbavature (FM 6.35)"},
            {"name": "Cambiaso", "team": "Juventus", "base_target": 22, "max": 25, "role": "Laterale Titolare Spalletti (3G+4A)"},
            {"name": "Pavlovic", "team": "Milan", "base_target": 22, "max": 25, "role": "Centrale Goleador da Piazzato (5 gol)"},
            {"name": "Ndicka", "team": "Roma", "base_target": 21, "max": 24, "role": "Centrale Solido (FM 6.32)"},
            {"name": "Rrahmani", "team": "Napoli", "base_target": 20, "max": 23, "role": "Centrale Titolarissimo Allegri (FM 6.45)"},
            {"name": "Kempf", "team": "Como", "base_target": 19, "max": 22, "role": "Pilastro Difesa Fabregas (FM 6.52)"},
            {"name": "Gila", "team": "Milan", "base_target": 19, "max": 22, "role": "Affidabilità Pura Difesa a 3 Amorim"},
            {"name": "Scalvini", "team": "Atalanta", "base_target": 18, "max": 21, "role": "Perno Difensivo Sarri (3 gol)"},
            {"name": "Ostigard", "team": "Genoa", "base_target": 18, "max": 21, "role": "Specialista Aereo da Corner (5 gol)"}
        ]},
        {"tier_label": "Titolare Modificatore / Spinta (2% - 3%)", "min_p": 10, "max_p": 16, "candidates": [
            {"name": "Yan Couto", "team": "Como", "base_target": 16, "max": 18, "role": "Esterno Spinta Fabregas"},
            {"name": "Dragusin", "team": "Fiorentina", "base_target": 15, "max": 17, "role": "Titolare Fisso Modificatore Grosso"},
            {"name": "Spinazzola", "team": "Napoli", "base_target": 14, "max": 16, "role": "Jolly Bonus Allegri (FM 6.53)"},
            {"name": "Mina", "team": "Cagliari", "base_target": 11, "max": 13, "role": "1° Rigorista / Minutaggio 85%"},
            {"name": "Doekhi", "team": "Lazio", "base_target": 11, "max": 13, "role": "Centrale Goleador da Piazzato"},
            {"name": "Vojvoda", "team": "Udinese", "base_target": 10, "max": 12, "role": "Titolare Frequente nelle Rose"}
        ]},
        {"tier_label": "Titolare Low Cost / Scommessa (0% - 2%)", "min_p": 1, "max_p": 8, "candidates": [
            {"name": "Kaiki", "team": "Como", "base_target": 8, "max": 9, "role": "Terzino Sinistro Fabregas"},
            {"name": "Rensch", "team": "Roma", "base_target": 8, "max": 9, "role": "Scommessa Assist (FM 6.48)"},
            {"name": "Heggem", "team": "Bologna", "base_target": 7, "max": 8, "role": "Centrale Mancino Tedesco"},
            {"name": "Ahanor", "team": "Atalanta", "base_target": 7, "max": 8, "role": "Giovane Talento Sarri"},
            {"name": "Ziolkowski", "team": "Roma", "base_target": 6, "max": 7, "role": "Under Low Cost a 1 Credito"}
        ]}
    ],
    'C': [
        {"tier_label": "Supertop / Rigorista Primario (9% - 20%)", "min_p": 45, "max_p": 100, "candidates": [
            {"name": "Paz N.", "team": "Como", "base_target": 95, "max": 109, "role": "Supertop Assoluto (12G, FM 7.30)"},
            {"name": "Calhanoglu", "team": "Inter", "base_target": 73, "max": 84, "role": "Top 1° Rigorista (89% realizzo, 9G)"},
            {"name": "McTominay", "team": "Napoli", "base_target": 69, "max": 79, "role": "Dominante Inserimenti (FM 7.26)"},
            {"name": "Orsolini", "team": "Bologna", "base_target": 65, "max": 75, "role": "Ala d'Attacco / 1° Rigorista (10G)"},
            {"name": "Atta", "team": "Fiorentina", "base_target": 44, "max": 51, "role": "Mezzala Inserimento Rivelazione (FM 6.88)"},
            {"name": "De Bruyne", "team": "Napoli", "base_target": 43, "max": 49, "role": "1° Rigorista Napoli (FM 7.24)"},
            {"name": "Moreira Diego", "team": "Milan", "base_target": 43, "max": 49, "role": "Asimmetria Tattica (Attaccante listato C)"},
            {"name": "Baturina", "team": "Como", "base_target": 43, "max": 49, "role": "Trequartista Puro (FM 7.12)"}
        ]},
        {"tier_label": "Top / Mezzala da Bonus (5% - 8%)", "min_p": 25, "max_p": 40, "candidates": [
            {"name": "Da Cunha", "team": "Como", "base_target": 40, "max": 46, "role": "1° Rigorista Como (6G, FM 6.91)"},
            {"name": "Vlasic", "team": "Torino", "base_target": 38, "max": 44, "role": "100% Rigori 7/7 (FM 6.66)"},
            {"name": "Mastantuono", "team": "Fiorentina", "base_target": 37, "max": 43, "role": "Talento Trequartista Viola"},
            {"name": "Zaniolo", "team": "Udinese", "base_target": 37, "max": 43, "role": "Attaccante Aggiunto (FM 6.77)"},
            {"name": "Barella", "team": "Inter", "base_target": 36, "max": 41, "role": "Mezzala Totale Titolarità 100% (FM 6.71)"},
            {"name": "Rabiot", "team": "Milan", "base_target": 35, "max": 40, "role": "Perno Mediana Amorim (6G+4A)"},
            {"name": "Rowe", "team": "Bologna", "base_target": 33, "max": 38, "role": "Ala Offensiva Tedesco (FM 6.62)"},
            {"name": "McKennie", "team": "Juventus", "base_target": 30, "max": 35, "role": "Incursore Spalletti (5G+6A)"},
            {"name": "Ederson", "team": "Atalanta", "base_target": 27, "max": 31, "role": "Perno Intoccabile Sarri (FM 6.43)"},
            {"name": "Zielinski", "team": "Inter", "base_target": 26, "max": 30, "role": "2° Rigorista Inter Rigenerato"},
            {"name": "Koné M.", "team": "Roma", "base_target": 26, "max": 30, "role": "Media Voto Pura 6.26 Senza Insufficienze"}
        ]},
        {"tier_label": "Incursore / Asimmetria Tattica (3% - 5%)", "min_p": 15, "max_p": 24, "candidates": [
            {"name": "Politano", "team": "Napoli", "base_target": 22, "max": 25, "role": "Esterno d'Attacco Tridente Allegri"},
            {"name": "Saelemaekers", "team": "Milan", "base_target": 22, "max": 25, "role": "Esterno Offensivo Amorim (FM 6.41)"},
            {"name": "Perrone", "team": "Como", "base_target": 21, "max": 24, "role": "Regista da Voto Fabregas (FM 6.47)"},
            {"name": "Gaetano", "team": "Atalanta", "base_target": 21, "max": 24, "role": "Regista da Bonus Sarri (FM 6.31)"},
            {"name": "Lobotka", "team": "Napoli", "base_target": 18, "max": 21, "role": "Regista Intoccabile Allegri"},
            {"name": "Frattesi", "team": "Lazio", "base_target": 17, "max": 20, "role": "Mezzala Offensiva con Licenza di Tiro"}
        ]},
        {"tier_label": "Regista Low Cost / Scommesse (0% - 3%)", "min_p": 1, "max_p": 14, "candidates": [
            {"name": "Locatelli", "team": "Juventus", "base_target": 12, "max": 14, "role": "Garanzia Voto e 3° Rigorista Juve"},
            {"name": "Diouf", "team": "Inter", "base_target": 11, "max": 13, "role": "Jolly Incursore Rotazioni Chivu"},
            {"name": "Adzic", "team": "Sassuolo", "base_target": 8, "max": 9, "role": "Scommessa Talento Trequarti"},
            {"name": "Busio", "team": "Venezia", "base_target": 8, "max": 9, "role": "Leader Tecnico e Piazzati Venezia"},
            {"name": "El Azzouzi A.", "team": "Frosinone", "base_target": 2, "max": 2, "role": "Titolare Low Cost 1-2 Crediti"}
        ]}
    ],
    'A': [
        {"tier_label": "Supertop Bomber (16% - 30%)", "min_p": 80, "max_p": 150, "candidates": [
            {"name": "Malen", "team": "Roma", "base_target": 141, "max": 162, "role": "Record FM 8.84 e 1° Rigorista Roma"},
            {"name": "Martinez L.", "team": "Inter", "base_target": 132, "max": 152, "role": "Top 1 Assoluto Spesa (FM 8.25)"},
            {"name": "Hojlund", "team": "Napoli", "base_target": 125, "max": 144, "role": "Prima Punta 4-3-3 Allegri (FM 7.56)"},
            {"name": "Kean", "team": "Fiorentina", "base_target": 124, "max": 143, "role": "Terminale Centrale Grosso"},
            {"name": "Ramos G.", "team": "Milan", "base_target": 105, "max": 121, "role": "Centravanti 3-4-2-1 Amorim"},
            {"name": "Yildiz", "team": "Juventus", "base_target": 102, "max": 117, "role": "Talento Puro e 2° Rigorista (FM 7.30)"},
            {"name": "Thuram", "team": "Inter", "base_target": 102, "max": 117, "role": "Partner d'Attacco Lautaro (FM 7.95)"},
            {"name": "Kolo Muani", "team": "Juventus", "base_target": 94, "max": 108, "role": "1° Rigorista Juventus Spalletti"}
        ]},
        {"tier_label": "Secondo Slot / Bomber Affidabili (9% - 15%)", "min_p": 45, "max_p": 75, "candidates": [
            {"name": "Pulisic", "team": "Milan", "base_target": 73, "max": 84, "role": "Rigorista Alternativo Milan (FM 7.07)"},
            {"name": "Scamacca", "team": "Atalanta", "base_target": 70, "max": 80, "role": "1° Rigorista Sarri (FM 7.55)"},
            {"name": "Douvikas", "team": "Como", "base_target": 62, "max": 71, "role": "14 Gol Como Fabregas (FM 7.38)"},
            {"name": "Davis K.", "team": "Udinese", "base_target": 55, "max": 63, "role": "1° Rigorista Udinese (FM 7.37)"},
            {"name": "Dovbyk", "team": "Bologna", "base_target": 54, "max": 62, "role": "Centravanti Titolare Tedesco (FM 6.77)"},
            {"name": "Krstovic", "team": "Atalanta", "base_target": 51, "max": 59, "role": "10 Reti Alternanza Sarri (FM 7.19)"},
            {"name": "Simeone", "team": "Torino", "base_target": 49, "max": 56, "role": "Centravanti 11 Reti Abate (FM 7.09)"},
            {"name": "Dybala", "team": "Roma", "base_target": 47, "max": 54, "role": "Saldo Rigori +27.5 pt (91% realizzo)"},
            {"name": "Esposito F.P.", "team": "Inter", "base_target": 47, "max": 54, "role": "1ª Riserva Lautaro (FM 6.97)"}
        ]},
        {"tier_label": "Terzo-Quarto Slot / Rigoristi Provincia (4% - 9%)", "min_p": 20, "max_p": 44, "candidates": [
            {"name": "Gudmundsson", "team": "Fiorentina", "base_target": 42, "max": 48, "role": "1° Rigorista Fiorentina (+24.5 pt)"},
            {"name": "Berardi", "team": "Sassuolo", "base_target": 41, "max": 47, "role": "Rigorista Infallibile 88% (FM 7.19)"},
            {"name": "Raspadori", "team": "Atalanta", "base_target": 38, "max": 44, "role": "Jolly Tecnico Sarri"},
            {"name": "Castro", "team": "Roma", "base_target": 37, "max": 43, "role": "Rotazione Offensiva Roma (FM 6.51)"},
            {"name": "Leao", "team": "Milan", "base_target": 33, "max": 38, "role": "Esterno Offensivo Amorim (FM 6.86)"},
            {"name": "Colombo", "team": "Genoa", "base_target": 26, "max": 30, "role": "1° Rigorista Genoa (Allerta 93% cambi al 62')"},
            {"name": "Piccoli", "team": "Bologna", "base_target": 25, "max": 29, "role": "Alternativa Fisica Dovbyk (FM 6.23)"},
            {"name": "Noslin", "team": "Lazio", "base_target": 25, "max": 29, "role": "Titolare d'Attacco Gattuso"},
            {"name": "Adams A.", "team": "Venezia", "base_target": 23, "max": 26, "role": "1° Rigorista e Centravanti Venezia"},
            {"name": "Pellegrino", "team": "Fiorentina", "base_target": 22, "max": 25, "role": "2° Rigorista Viola (FM 6.65)"},
            {"name": "Cutrone", "team": "Monza", "base_target": 22, "max": 25, "role": "Centravanti Salvezza e 2° Rigorista"},
            {"name": "Nkunku", "team": "Milan", "base_target": 22, "max": 25, "role": "1° Rigorista Designato Milan (FM 6.98)"},
            {"name": "Bonny", "team": "Inter", "base_target": 21, "max": 24, "role": "Cambio Tattico Chivu (5G+4A)"}
        ]},
        {"tier_label": "Quinto-Sesto Slot / Scommesse (0% - 4%)", "min_p": 1, "max_p": 18, "candidates": [
            {"name": "Tourè E.", "team": "Parma", "base_target": 18, "max": 21, "role": "Potenziale 7-8 Gol Parma (19.7% rose)"},
            {"name": "Carlos K.", "team": "Cagliari", "base_target": 11, "max": 13, "role": "Centravanti Fisico 2° Rigorista"},
            {"name": "Geubbels", "team": "Lecce", "base_target": 4, "max": 5, "role": "Seconda Punta 2° Rigorista Lecce"},
            {"name": "Raimondo", "team": "Frosinone", "base_target": 4, "max": 5, "role": "Centravanti Titolare Alvini"}
        ]}
    ]
}

GOALIE_HIERARCHY = {
    'Roma': [('Svilar', 48, 55), ('Gollini', 1, 2), ('De Marzi', 1, 1)],
    'Napoli': [('Meret', 42, 48), ('Milinkovic-Savic V.', 11, 13), ('Contini', 1, 1)],
    'Milan': [('Maignan', 36, 41), ('Terracciano', 1, 2), ('Torriani', 1, 1)],
    'Atalanta': [('Carnesecchi', 35, 40), ('Sportiello', 1, 2), ('Vismara', 1, 1)],
    'Juventus': [('Vicario', 34, 39), ('Perin', 4, 5), ('Pinsoglio', 1, 1)],
    'Inter': [('Martinez Jo.', 33, 38), ('Provedel', 8, 9), ('Di Gennaro', 1, 1)],
    'Como': [('Butez', 31, 36), ('Tornqvist', 1, 2), ('Vigorito', 1, 1)],
    'Fiorentina': [('De Gea', 21, 24), ('Christensen O.', 1, 2), ('Lezzerini', 1, 1)],
    'Bologna': [('Skorupski', 17, 20), ('Pessina Mas.', 1, 2), ('Happonen', 1, 1)],
    'Lazio': [('Mandas', 15, 17), ('Motta', 1, 2), ('Renzetti', 1, 1)],
    'Udinese': [('Okoye', 14, 16), ('Padelli', 1, 2), ('Piana', 1, 1)],
    'Lecce': [('Falcone', 12, 14), ('Bleve', 1, 2), ('Penev', 1, 1)],
    'Cagliari': [('Caprile', 10, 12), ('Sherri', 1, 2), ('Radunovic', 1, 1)],
    'Genoa': [('Bijlow', 9, 10), ('Stolz', 1, 2), ('Sommariva', 1, 1)],
    'Sassuolo': [('Muric', 5, 6), ('Turati', 1, 2), ('Russo A.', 1, 1)],
    'Torino': [('Perri', 4, 5), ('Paleari', 4, 5), ('Siviero', 1, 1)],
    'Monza': [('Thiam', 4, 5), ('Pizzignacco', 1, 1), ('Strajnar', 1, 1)],
    'Parma': [('Corvi', 4, 5), ('Daffara', 4, 5), ('Rinaldi', 1, 1)],
    'Venezia': [('Stankovic F.', 4, 5), ('Grandi', 1, 1), ('Pozzi', 1, 1)],
    'Frosinone': [('Palmisani', 3, 4), ('Desplanches', 2, 3), ('Lolic', 1, 1)]
}

GOALKEEPER_PAIRINGS = {
    'Inter': [
        {"club": "Bologna", "starter": "Skorupski", "target": 17, "max": 20, "diff": "🟢 95 - Sinergia Simmetrica", "reason": "La copertura tecnica totale per le trasferte ostiche dell'Inter."},
        {"club": "Monza", "starter": "Thiam", "target": 4, "max": 5, "diff": "🟢 93 - Alternanza", "reason": "Copertura a basso costo per Chivu."},
        {"club": "Cagliari", "starter": "Caprile", "target": 10, "max": 12, "diff": "🟢 93 - Alternanza", "reason": "Solidità casalinga sarda a costi contenuti."}
    ],
    'Roma': [
        {"club": "Bologna", "starter": "Skorupski", "target": 17, "max": 20, "diff": "🟢 95 - Massima Efficienza", "reason": "Bologna garantisce turni casalinghi favorevoli quando la Roma è in trasferte proibitive."},
        {"club": "Monza", "starter": "Thiam", "target": 4, "max": 5, "diff": "🟢 93 - Alternanza", "reason": "Sinergia economica eccellente."}
    ],
    'Milan': [
        {"club": "Fiorentina", "starter": "De Gea", "target": 21, "max": 24, "diff": "🟢 93 - Lusso", "reason": "Coppia lussuosa, potenzialmente troppo onerosa ma copre bene."},
        {"club": "Lecce", "starter": "Falcone", "target": 12, "max": 14, "diff": "🟢 93 - Ottima", "reason": "Alternanza ottimale ed economica per la squadra di Amorim."},
        {"club": "Parma", "starter": "Corvi/Daffara", "target": 4, "max": 5, "diff": "🟢 93 - Economica", "reason": "Ottima sinergia, ma occhio al dualismo nel Parma."}
    ],
    'Juventus': [
        {"club": "Bologna", "starter": "Skorupski", "target": 17, "max": 20, "diff": "🟢 92 - Flessibilità", "reason": "Fornisce sicurezza per i turni esterni della Juve."},
        {"club": "Cagliari", "starter": "Caprile", "target": 10, "max": 12, "diff": "🟢 92 - Ottimo Qualità/Prezzo", "reason": "Sfrutta la solidità casalinga di Pisacane."}
    ],
    'Napoli': [
        {"club": "Lecce", "starter": "Falcone", "target": 12, "max": 14, "diff": "🟢 93 - Paracadute", "reason": "Fornisce un eccellente paracadute per la squadra di Allegri."},
        {"club": "Torino", "starter": "Perri", "target": 4, "max": 5, "diff": "🟢 93 - Paracadute Economico", "reason": "Costo marginale per ottima resa incrociata."}
    ],
    'Atalanta': [
        {"club": "Sassuolo", "starter": "Muric", "target": 5, "max": 6, "diff": "🟢 95 - Sinergia Simmetrica", "reason": "Copertura perfetta vitale considerata l'emergenza difensiva orobica (Sarri)."},
        {"club": "Monza", "starter": "Thiam", "target": 4, "max": 5, "diff": "🟢 92 - Alternanza", "reason": "Buona copertura per il turnover Champions."}
    ],
    'Como': [
        {"club": "Bologna", "starter": "Skorupski", "target": 17, "max": 20, "diff": "🟢 93 - Top Clean Sheet", "reason": "Alterna i 19 CS storici di Butez con la compattezza felsinea."},
        {"club": "Udinese", "starter": "Okoye", "target": 14, "max": 16, "diff": "🟢 93 - Copertura Rilevante", "reason": "Protezione a quota 93 senza intaccare troppo le finanze."}
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
        "advice": "Carnesecchi per il modificatore; Gaetano centrocampista inserzionista. Il passaggio al 4-3-3 esalta le mezzali palleggiatrici (Samardzic, Gaetano). Scamacca rilanciato ma occhio al turnover."
    },
    "Bologna": {
        "coach": "Domenico Tedesco", "formation": "4-3-3 (Verticalizzazione & Alto Pressing)",
        "gk": "Skorupski (Pessina vice)",
        "defense": "Zortea, Heggem, Helland/Vitik, Miranda",
        "midfield": "Ferguson, Moro, Bernardeschi",
        "attack": "Orsolini, Rowe, Dovbyk (Piccoli vice)",
        "penalties": ["Orsolini (1°)", "Bernardeschi (2°)", "Dovbyk (3°)"],
        "advice": "Tedesco conferma il 4-3-3 offensivo. Orsolini monopolizza i rigori e non fa coppe, ottimo a 64 cr. Heggem certezza difensiva a costi contenuti."
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
        "midfield": "Da Cunha, Perrone, Baturina",
        "attack": "Nico Paz (Trequartista), Douvikas (Morata vice)",
        "penalties": ["Da Cunha (1°)", "Douvikas (2°)", "Nico Paz (3°)"],
        "advice": "Butez è il portiere più efficiente del listino. Nico Paz agisce da falso nove ed è un Super Top. Douvikas bomber altissima resa."
    },
    "Fiorentina": {
        "coach": "Fabio Grosso", "formation": "4-3-1-2 / 4-3-3 (Valorizzazione Centrali)",
        "gk": "David De Gea (Christensen/Lezzerini)",
        "defense": "Dodò/Jiménez, Dragusin, Viery, Valdepeñas",
        "midfield": "Arthur Atta, Mastantuono, Fagioli, Oulai, Mandragora",
        "attack": "Gudmundsson, Moise Kean, Pellegrino",
        "penalties": ["Gudmundsson (1°)", "Pellegrino (2°)", "Kean (3°)"],
        "advice": "Attenzione a Kean: valutato 124 cr, è considerato la 'Trappola Estrema' a causa dell'alto rischio di fallimento. Mastantuono ottima scommessa trequartista."
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
        "defense": "Dimarco (Trequartista occulto), Bastoni, Akanji, Bisseck, Pavard/Stones, Spence",
        "midfield": "Calhanoglu, Barella, Zielinski, Frattesi, Diouf, Sucic, Jones",
        "attack": "Lautaro Martínez, Marcus Thuram, Francesco Pio Esposito, Bonny",
        "penalties": ["Calhanoglu (1° - 89%)", "Zielinski (2°)", "Lautaro Martínez (3°)"],
        "advice": "Dimarco è un'anomalia di mercato: produce come un top d'attacco, vale l'investimento massiccio. Calhanoglu dominatore per i rigori."
    },
    "Juventus": {
        "coach": "Luciano Spalletti", "formation": "4-2-3-1 (Propensione Offensiva)",
        "gk": "Guglielmo Vicario (Perin vice)",
        "defense": "Bremer, Kalulu, Cambiaso, Çelik",
        "midfield": "Locatelli, Thuram / McKennie",
        "attack": "Yildiz, Conceição, Alajbegović, Randal Kolo Muani (David/Boga)",
        "penalties": ["Kolo Muani (1°)", "Yildiz (2°)", "Locatelli (3°)"],
        "advice": "Kolo Muani è il terminale di Spalletti e rigorista, fortemente sottovalutato dal mercato. Bremer garantisce certezze in difesa."
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
        "attack": "Christian Pulisic (Trequartista), Rafael Leão, Gonçalo Ramos (Nkunku)",
        "penalties": ["Nkunku (1°)", "Pulisic (2°)", "Gonçalo Ramos (3°)"],
        "advice": "Il sistema di Amorim esalta Ramos e Pulisic (trequartista atipico). Penalizzato Rafael Leao, che sconta un crollo delle quotazioni."
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
        "coach": "Massimiliano Allegri", "formation": "4-3-3 / Baricentro Basso",
        "gk": "Alex Meret (Vanja Milinković-Savić co-titolare)",
        "defense": "Di Lorenzo, Olivera/Spinazzola, Rrahmani, Beukema",
        "midfield": "Scott McTominay, Stanislav Lobotka, Kevin De Bruyne, Anguissa, Elmas",
        "attack": "Rasmus Højlund, Politano, Santos, Neres",
        "penalties": ["De Bruyne (1°)", "Højlund (2°)", "McTominay (3°)"],
        "advice": "Il pragmatismo di Allegri valorizza i difensori (Rrahmani, Di Lorenzo) ma penalizza l'attacco. Hojlund a prezzi alti è un azzardo matematico letale."
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
        "coach": "Gian Piero Gasperini", "formation": "3-4-2-1 / 3-5-2 (Intensità)",
        "gk": "Mile Svilar (Gollini/De Marzi)",
        "defense": "Gianluca Mancini, Evan Ndicka, Hermoso, Rensch, Nahuel Molina / Wesley (Esterni)",
        "midfield": "Manu Koné, Niccolò Pisilli, Bryan Cristante",
        "attack": "Paulo Dybala, Matías Soulé / Castro, Donyell Malen",
        "penalties": ["Malen (1°)", "Dybala (2°)", "Castro (3°)"],
        "advice": "La difesa a tre di Gasperini trasforma Mancini e Wesley in incursori offensivi: acquisti obbligati per il modificatore. Malen è il Super Top dell'attacco."
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

INJURY_LIST = {
    "Hien": {"team": "Atalanta", "infortunio": "Lesione del tendine prossimale del muscolo semimembranoso", "rientro": "Inizio Ottobre", "status": "🔴 Lungodegente"},
    "Sulemana K.": {"team": "Atalanta", "infortunio": "Lesione di 2° grado del legamento collaterale mediale", "rientro": "Inizio Ottobre", "status": "🔴 Lungodegente"},
    "Kristensen T.": {"team": "Atalanta", "infortunio": "Trauma distorsivo alla caviglia", "rientro": "Da valutare", "status": "🟡 In dubbio"},
    "El Azzouzi O.": {"team": "Bologna", "infortunio": "Lesione del bicipite femorale", "rientro": "Metà Settembre", "status": "🟠 Medio Termine"},
    "Casale": {"team": "Bologna", "infortunio": "Fastidio muscolare", "rientro": "A breve", "status": "🟡 In dubbio"},
    "Idrissi R.": {"team": "Cagliari", "infortunio": "Ricostruzione LCA", "rientro": "Fine Ottobre", "status": "🔴 Lungodegente"},
    "Addai": {"team": "Como", "infortunio": "Rottura tendine d'Achille", "rientro": "Metà Settembre", "status": "🟠 Medio Termine"},
    "Parisi": {"team": "Fiorentina", "infortunio": "Ricostruzione LCA", "rientro": "Novembre", "status": "🔴 Lungodegente"},
    "Yildiz Kenan": {"team": "Juventus", "infortunio": "Trauma al piede sx", "rientro": "Circa 3 mesi", "status": "🔴 Lungodegente"},
    "Cataldi": {"team": "Lazio", "infortunio": "Ernia bilaterale", "rientro": "Inizio Ottobre", "status": "🟠 Medio Termine"},
    "Pulisic Christian": {"team": "Milan", "infortunio": "Edema osseo e microfrattura al perone", "rientro": "Da valutare", "status": "🟠 Medio Termine"},
    "Pessina": {"team": "Monza", "infortunio": "Lussazione traumatica rotula dx", "rientro": "Inizio Novembre", "status": "🔴 Lungodegente"},
    "Buongiorno": {"team": "Napoli", "infortunio": "Post-operatorio menisco dx", "rientro": "Metà Novembre", "status": "🔴 Lungodegente"},
    "Nicolussi Caviglia": {"team": "Parma", "infortunio": "Lesione miotendinea", "rientro": "Novembre", "status": "🔴 Lungodegente"},
    "Rensch": {"team": "Roma", "infortunio": "Risentimento flessore", "rientro": "A breve", "status": "🟡 In dubbio"},
    "Konè I.": {"team": "Sassuolo", "infortunio": "Rottura tibia e perone", "rientro": "Dicembre", "status": "🔴 Lungodegente"},
    "Berardi Domenico": {"team": "Sassuolo", "infortunio": "Distorsione caviglia dx", "rientro": "Inizio Settembre", "status": "🟡 In dubbio"},
    "Zaniolo Nicolò": {"team": "Udinese", "infortunio": "Lesione bicipite femorale", "rientro": "Metà Settembre", "status": "🟠 Medio Termine"},
    "Kabasele": {"team": "Udinese", "infortunio": "Squalifica", "rientro": "1 Turno", "status": "🔴 Squalificato"}
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

# ==========================================
# LOGICA BOT INTELLIGENZA ARTIFICIALE E DINAMICHE AVANZATE
# ==========================================
BOT_TRASH_TALK = [
    "Ma lo hai visto come ha giocato l'anno scorso?", 
    "Questo è mio, non ci provate.", 
    "State spendendo troppo, siete pazzi!", 
    "A 1 credito va bene, oltre è un furto.",
    "Se lo volete, dovete sanguinare.",
    "Ottimo per la mia panchina.",
    "Rilancio, ma solo per darvi fastidio.",
    "Hype esagerato, vi lascio scannare."
]

def analizza_giocatore_avanzato(player_info):
    base_t, _ = get_player_base_target(player_info)
    fvm = player_info.get('FVM', 1)
    ruolo = player_info['R']
    
    # Tier Dinamico (su base 500)
    if fvm >= 75: tier = "Top"
    elif fvm >= 35: tier = "Semitop"
    elif fvm >= 12: tier = "Ottimo Titolare"
    elif fvm >= 5: tier = "Scommessa"
    else: tier = "Basso Costo"
    
    # Indice Hype (0-100) basato su scostamento tra target e FVM
    hype = min(100, max(0, int((base_t / max(1, fvm)) * 50)))
    if tier == "Top": hype += 20
    
    # Propensione Bonus (Base semplice: se FVM alto e difensore/centrocampista, probabile bonus/modificatore)
    prop_bonus = "Alta" if (ruolo in ['D', 'C'] and fvm > 20) else ("Media" if fvm > 8 else "Bassa")
    
    return tier, hype, prop_bonus

def calcola_limite_massimo_bot(bot, player_info, active_fomo=False):
    role = player_info['R']
    base_t, _ = get_player_base_target(player_info)
    tier, hype, prop_bonus = analizza_giocatore_avanzato(player_info)
    prof = bot.get('profile', "Equilibrato")
    
    # 1. MACROECONOMIA (Inflazione/Deflazione)
    tot_creds_lega = sum(v['budget'] for v in st.session_state.opponents.values()) + (TOTAL_BUDGET - sum(p['price'] for p in st.session_state.my_roster) + st.session_state.budget_adjustments)
    max_creds_iniziali = TOTAL_BUDGET * 10
    inflazione_mult = 1.0 + ((tot_creds_lega / max_creds_iniziali) - 0.5) * 0.3 
    
    # 2. MOLTIPLICATORE CARATTERE & HYPE
    c_mult = 1.0
    if prof == "Conservatore": c_mult = 0.85 if hype > 70 else 1.05
    elif prof == "Smanioso": c_mult = 1.4 if (tier == "Top" or hype > 80) else 0.8
    elif prof == "Scommettitore": c_mult = 0.6 if tier == "Top" else (1.5 if tier == "Scommessa" else 1.1)
    elif prof == "Ostruzionista": c_mult = 1.25 
        
    # 3. URGENZA & MODIFICATORE
    slots_filled = len(bot['roster'][role])
    slots_total = SLOTS[role]
    slots_left = slots_total - slots_filled
    if slots_left <= 0: return 0
    
    urgency = 1.0
    if slots_left == slots_total: urgency = 1.15
    elif slots_left == 1 and role == 'A': urgency = 1.5
    
    if role == 'D' and prop_bonus == "Alta" and prof in ["Conservatore", "Equilibrato"]:
        urgency *= 1.2
        
    # 4. PANICO ULTIMI SLOT (FOMO VERA)
    top_rimasti = len(listone_df[(listone_df['R'] == role) & (listone_df['FVM'] >= 75) & (~listone_df['Nome'].isin(st.session_state.purchased_registry.keys()))])
    if active_fomo and top_rimasti <= 2 and tier == "Top" and len([p for p in bot['roster'][role] if get_player_base_target(p)[0] >= 35]) == 0:
        urgency *= 1.25 
    
    raw_max = base_t * c_mult * inflazione_mult * urgency
    max_possibile = bot['budget'] - (bot['slots_left'] - 1)
    limite = min(int(raw_max), max_possibile)
    
    if prof == "Ostruzionista" and tier == "Top": limite = min(limite, int(base_t * 0.90))
        
    return max(0, limite)

def bot_effettua_chiamata(bot_key, role):
    bot = st.session_state.opponents[bot_key]
    prof = bot.get('profile', 'Equilibrato')
    
    avail_df = listone_df[(listone_df['R'] == role) & (~listone_df['Nome'].isin(st.session_state.purchased_registry.keys()))]
    if avail_df.empty: return None
    
    avail_df['Tier_Hype'] = avail_df.apply(lambda x: analizza_giocatore_avanzato(x), axis=1)
    
    if prof == "Ostruzionista" or bot['budget'] < 100:
        top_esche = avail_df[avail_df['FVM'] >= 50].sort_values(by='FVM', ascending=False)
        if not top_esche.empty: return top_esche.iloc[0].to_dict()
        
    if prof == "Scommettitore" or bot['slots_left'] < 5:
        low_cost = avail_df[(avail_df['FVM'] <= 5) & (avail_df['FVM'] > 1)].sample(frac=1)
        if not low_cost.empty: return low_cost.iloc[0].to_dict()
        
    if prof == "Smanioso":
        hypes = avail_df.sort_values(by='FVM', ascending=False).head(15).sample(frac=1)
        if not hypes.empty: return hypes.iloc[0].to_dict()
        
    solidi = avail_df[(avail_df['FVM'] >= 15) & (avail_df['FVM'] <= 60)]
    if not solidi.empty: return solidi.sample(n=1).iloc[0].to_dict()
    
    return avail_df.sample(n=1).iloc[0].to_dict()

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
    
    tot_spent = sum(p['price'] for p in my_roster)
    tot_budget_left = TOTAL_BUDGET - tot_spent + st.session_state.get('budget_adjustments', 0)
    tot_slots_filled = len(my_roster)
    tot_slots_left = TOTAL_SLOTS - tot_slots_filled
    
    dept_bought = [p for p in my_roster if p['role'] == role]
    dept_spent = sum(p['price'] for p in dept_bought)
    dept_filled = len(dept_bought)
    dept_slots_left = SLOTS[role] - dept_filled

    if tot_slots_left <= 0 or dept_slots_left <= 0:
        return {"base_target": base_target, "dyn_target": 0, "dyn_max_bid": 0, "is_full": True, "dept_budget_left": 0, "dept_slots_left": 0}

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
    
    other_slots_needed = tot_slots_left - dept_slots_left
    max_dept_can_have = max(dept_slots_left, eff_tot_budget - other_slots_needed)
    
    current_dept_base_budget = st.session_state.base_dept_budget[role]
    effective_dept_budget = min(max_dept_can_have, max(dept_slots_left, (current_dept_base_budget - dept_spent) - locked_budget_dept))
    
    total_unfilled_baseline = sum(sum(BASELINE_DEPT_CURVES[r][len([p for p in my_roster if p['role'] == r]):]) for r in SLOTS)
    scale_factor = eff_tot_budget / max(1, total_unfilled_baseline)
    
    dyn_target = max(1, int(round(base_target * scale_factor)))
    max_single_in_dept = max(1, effective_dept_budget - (dept_slots_left - 1))
    dyn_target = min(dyn_target, max_single_in_dept)

    margin = 1.15 if dyn_target > 25 else (1.20 if dyn_target > 5 else 1.0)
    dyn_max_bid = int(round(dyn_target * margin))
    dyn_max_bid = max(dyn_target, min(eff_tot_budget - (tot_slots_left - 1), min(dyn_max_bid, max_single_in_dept)))

    panic_threshold = st.session_state.base_dept_budget['A'] * 0.9
    panic_active = tot_budget_left <= panic_threshold and len([p for p in my_roster if p['role'] == 'A']) == 0
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

def calculate_dynamic_targets_for_slots(role, my_roster):
    tot_spent = sum(p['price'] for p in my_roster)
    tot_budget_left = TOTAL_BUDGET - tot_spent + st.session_state.get('budget_adjustments', 0)
    tot_slots_left = TOTAL_SLOTS - len(my_roster)

    dept_bought = [p for p in my_roster if p['role'] == role]
    dept_spent = sum(p['price'] for p in dept_bought)
    dept_filled = len(dept_bought)
    dept_slots_left = SLOTS[role] - dept_filled

    if dept_slots_left <= 0:
        return []

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
    
    current_dept_base_budget = st.session_state.base_dept_budget[role]
    effective_dept_budget = min(max_dept_can_have, max(dept_slots_left, current_dept_base_budget - dept_spent))

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

def get_dynamic_slot_candidates(role_code, slot_target_budget, purchased_registry, allocated_in_roadmap, custom_user_targets_list=None, rejected_players=None):
    if rejected_players is None:
        rejected_players = []
        
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
                        "chosen_role": "Mio Top Selezionato",
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
            if c['name'] not in purchased_registry and c['name'] not in allocated_in_roadmap and c['name'] not in rejected_players:
                candidates_ordered.append(c)

    if len(candidates_ordered) < 4:
        for tier in pool:
            if tier != best_tier:
                for c in tier['candidates']:
                    if c['name'] not in purchased_registry and c['name'] not in allocated_in_roadmap and c['name'] not in rejected_players and c not in candidates_ordered:
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
    
    current_dept_base = st.session_state.base_dept_budget[role_code]
    st.markdown(f"### {dept_title}")
    
    allocated_in_roadmap = set(p['name'] for p in st.session_state.get('my_roster', []))
    dyn_targets_remaining = calculate_dynamic_targets_for_slots(role_code, st.session_state.get('my_roster', []))
    
    user_custom_picks = st.session_state.get('custom_user_targets', {}).get(role_code, [])
    rejected_list = st.session_state.get('rejected_players', [])

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
                    logo_img = f"<img src='{get_team_logo_url(p_bought['team'])}' width='22' style='vertical-align: middle; margin-right: 6px;'>"
                    card_html = (
                        "<div class='glass-card'>"
                        f"<div style='margin-bottom: 10px;'>{logo_img}<b>{slot_label}: {p_bought['name']}</b></div>"
                        f"<span style='color:#10B981;'>✓ Acquistato:</span> <b>{p_bought['price']} cr</b><br>"
                        "<div class='glass-card-mini-text'>In Rosa</div>"
                        "</div>"
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                else:
                    rem_idx = global_slot_idx - len(bought_list)
                    t_budget = dyn_targets_remaining[rem_idx] if rem_idx < len(dyn_targets_remaining) else 1
                    
                    slot_res = get_dynamic_slot_candidates(role_code, t_budget, st.session_state.get('purchased_registry', {}), allocated_in_roadmap, custom_user_targets_list=user_custom_picks, rejected_players=rejected_list)
                    logo_img = f"<img src='{get_team_logo_url(slot_res['chosen_team'])}' width='22' style='vertical-align: middle; margin-right: 6px;'>"
                    
                    is_custom = slot_res['chosen_name'] in user_custom_picks
                    accent_class = " glass-card-accent" if is_custom else ""
                    
                    card_html = (
                        f"<div class='glass-card{accent_class}'>"
                        f"<div style='margin-bottom: 10px;'>{logo_img}<b>{slot_label}: {slot_res['chosen_name']}</b></div>"
                        f"Target: <b>{slot_res['dyn_target']} cr</b> | Max: <b>{slot_res['dyn_max_bid']} cr</b><br>"
                        f"<div class='glass-card-mini-text'>Ruolo: {slot_res['chosen_role']}</div>"
                        f"<div class='glass-card-mini-text'>Piani B: {slot_res['alts_str']}</div>"
                        "</div>"
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    st.markdown("<div style='margin-top: 8px;'>", unsafe_allow_html=True)
                    bc1, bc2 = st.columns(2)
                    
                    if slot_res['chosen_name'] != "Scommessa / Copertura":
                        if is_custom:
                            if bc1.button("Sblocca", key=f"unlock_{role_code}_{global_slot_idx}", use_container_width=True):
                                st.session_state.custom_user_targets[role_code].remove(slot_res['chosen_name'])
                                save_state_to_disk()
                                st.rerun()
                        else:
                            if bc1.button("Blocca", key=f"lock_{role_code}_{global_slot_idx}", use_container_width=True):
                                st.session_state.custom_user_targets[role_code].append(slot_res['chosen_name'])
                                save_state_to_disk()
                                st.rerun()
                            if bc2.button("Cambia", key=f"change_{role_code}_{global_slot_idx}", use_container_width=True):
                                if 'rejected_players' not in st.session_state:
                                    st.session_state.rejected_players = []
                                st.session_state.rejected_players.append(slot_res['chosen_name'])
                                save_state_to_disk()
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

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
    if 'FVM' in df.columns:
        df['FVM'] = df['FVM'].apply(lambda x: max(1, int(round(float(x) / 2))) if pd.notnull(x) else 1)
        
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
def init_state():
    if 'my_roster' not in st.session_state: st.session_state.my_roster = []
    
    if 'opponents' not in st.session_state:
        st.session_state.opponents = {}
        for i in range(9):
            st.session_state.opponents[f"Avversario {i+1}"] = {
                'name': f"Avversario {i+1}", 'budget': TOTAL_BUDGET, 'slots_left': TOTAL_SLOTS,
                'roster': {'P': [], 'D': [], 'C': [], 'A': []},
                'profile': BOT_PROFILES[i % len(BOT_PROFILES)]
            }
            
    profiles = [v.get('profile', 'Equilibrato') for v in st.session_state.opponents.values()]
    if all(p == 'Equilibrato' for p in profiles):
        for i, k in enumerate(st.session_state.opponents.keys()):
            st.session_state.opponents[k]['profile'] = BOT_PROFILES[i % len(BOT_PROFILES)]
            
    if 'history' not in st.session_state: st.session_state.history = []
    if 'purchased_registry' not in st.session_state: st.session_state.purchased_registry = {}
    if 'budget_adjustments' not in st.session_state: st.session_state.budget_adjustments = 0
    if 'selected_strategy' not in st.session_state: st.session_state.selected_strategy = list(STRATEGIES.keys())[0]
    if 'base_dept_budget' not in st.session_state: st.session_state.base_dept_budget = STRATEGIES[st.session_state.selected_strategy]
    if 'rejected_players' not in st.session_state: st.session_state.rejected_players = []
    if 'custom_user_targets' not in st.session_state: st.session_state.custom_user_targets = {'P': [], 'D': [], 'C': [], 'A': []}
    
    # GESTIONE TURNI E FLUSSO ASTA LIVE
    if 'auction_sequence' not in st.session_state: st.session_state.auction_sequence = ["Tu"] + list(st.session_state.opponents.keys())
    if 'turn_idx' not in st.session_state: st.session_state.turn_idx = 0
    if 'role_sequence' not in st.session_state: st.session_state.role_sequence = ['P', 'D', 'C', 'A']
    if 'current_role_idx' not in st.session_state: st.session_state.current_role_idx = 0

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

if 'budget_adjustments' not in st.session_state:
    st.session_state.budget_adjustments = saved_data.get("budget_adjustments", 0) if saved_data else 0

if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = saved_data.get("selected_strategy", "Equilibrata (Mediana di Mercato)") if saved_data else "Equilibrata (Mediana di Mercato)"

if 'base_dept_budget' not in st.session_state:
    try:
        st.session_state.base_dept_budget = STRATEGIES[st.session_state.selected_strategy]
    except KeyError:
        st.session_state.selected_strategy = "Equilibrata (Mediana di Mercato)"
        st.session_state.base_dept_budget = STRATEGIES["Equilibrata (Mediana di Mercato)"]

if 'rejected_players' not in st.session_state:
    st.session_state.rejected_players = saved_data.get("rejected_players", []) if saved_data else []

def save_state_to_disk():
    state_data = {
        "my_roster": st.session_state.get("my_roster", []),
        "selected_keeper_club": st.session_state.get("selected_keeper_club", 'Inter'),
        "custom_user_targets": st.session_state.get("custom_user_targets", {'P': [], 'D': [], 'C': [], 'A': []}),
        "opponents": st.session_state.get("opponents", {}),
        "purchased_registry": st.session_state.get("purchased_registry", {}),
        "history": st.session_state.get("history", []),
        "budget_adjustments": st.session_state.get("budget_adjustments", 0),
        "selected_strategy": st.session_state.get("selected_strategy", "Equilibrata (Mediana di Mercato)"),
        "rejected_players": st.session_state.get("rejected_players", []),
        "last_saved": datetime.now().strftime("%H:%M:%S")
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ==============================================================================
# 6. SIDEBAR: STATO E GESTIONE
# ==============================================================================
st.sidebar.title("Pannello di Controllo")

st.sidebar.markdown("**Strategia d'Asta**")

try:
    strat_index = list(STRATEGIES.keys()).index(st.session_state.selected_strategy)
except ValueError:
    strat_index = 0
    st.session_state.selected_strategy = list(STRATEGIES.keys())[0]

selected_strat = st.sidebar.selectbox("Imposta Allocazione Budget:", options=list(STRATEGIES.keys()), index=strat_index)
if selected_strat != st.session_state.selected_strategy:
    st.session_state.selected_strategy = selected_strat
    st.session_state.base_dept_budget = STRATEGIES[selected_strat]
    st.rerun()

current_stage = st.sidebar.selectbox(
    "Fase d'Asta Attuale:",
    ["Portieri", "Difensori", "Centrocampisti", "Attaccanti", "Fase Libera"]
)

# Rimappa il filtro per i calcoli logici
role_filter_map = {"Portieri": "P", "Difensori": "D", "Centrocampisti": "C", "Attaccanti": "A", "Fase Libera": None}

tot_spent = sum(p['price'] for p in st.session_state.my_roster)
tot_budget_left = TOTAL_BUDGET - tot_spent + st.session_state.get('budget_adjustments', 0)
tot_slots_needed = TOTAL_SLOTS - len(st.session_state.my_roster)
p_max_safe = tot_budget_left - (tot_slots_needed - 1) if tot_slots_needed > 0 else 0

st.sidebar.divider()
st.sidebar.markdown(f"**Budget Rimasto:** `{tot_budget_left} / 500 cr`")
st.sidebar.markdown(f"**Slot Mancanti:** `{tot_slots_needed} / 25`")
st.sidebar.markdown(f"**Pmax Assoluto:** `{p_max_safe} cr`")

st.sidebar.divider()
st.sidebar.markdown("**Avanzamento Spesa Reparti:**")
for r_code, r_name in [('P', 'Portieri'), ('D', 'Difensori'), ('C', 'Centrocampisti'), ('A', 'Attaccanti')]:
    sp = get_dept_spent(r_code)
    cap = st.session_state.base_dept_budget[r_code]
    ratio = min(1.0, sp / cap) if cap > 0 else 0.0
    st.sidebar.markdown(f"<span style='color:#94A3B8; font-size:13px;'>{r_name}: {sp}/{cap} cr</span>", unsafe_allow_html=True)
    st.sidebar.progress(ratio)

st.sidebar.divider()
st.sidebar.markdown("**Lock-in Strategy (Slot Bloccati)**")
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
    
    st.sidebar.info(f"Congelati: `{locked_cr} cr` per `{locked_sl}` slot\n\nCassa Libera Reale: `{tot_budget_left - locked_cr} cr`")

st.sidebar.divider()
col_sb1, col_sb2 = st.sidebar.columns(2)
if col_sb1.button("Salva", use_container_width=True):
    save_state_to_disk()
    st.sidebar.success("Salvato!")

if col_sb2.button("Undo", use_container_width=True):
    if st.session_state.history:
        last_action = st.session_state.history.pop()
        b_name = last_action['buyer']
        p_name = last_action['name']
        p_price = last_action['price']
        p_role = last_action.get('role', 'Sconosciuto')

        if b_name == "La Mia Squadra":
            st.session_state.my_roster = [p for p in st.session_state.my_roster if p['name'] != p_name]
            if last_action.get('action') == 'SVINCOLO':
                st.session_state.budget_adjustments -= last_action.get('penalty', 0)
        else:
            for opp_k, opp_v in st.session_state.opponents.items():
                if opp_v['name'] == b_name:
                    if last_action.get('action') == 'SVINCOLO':
                        opp_v['budget'] -= abs(p_price)
                        opp_v['slots_left'] -= 1
                    else:
                        opp_v['budget'] += p_price
                        opp_v['slots_left'] += 1
                        opp_v['roster'][p_role] = [p for p in opp_v['roster'][p_role] if p['name'] != p_name]
                    break

        if p_name in st.session_state.purchased_registry and last_action.get('action') != 'SVINCOLO':
            del st.session_state.purchased_registry[p_name]

        save_state_to_disk()
        st.rerun()

with st.sidebar.expander("Infermeria & Squalificati"):
    for p_name, p_data in INJURY_LIST.items():
        logo_inj = get_team_logo_url(p_data['team'])
        st.markdown(f"<img src='{logo_inj}' width='16' style='vertical-align: middle; margin-right: 5px;'> **{p_name}**", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:12px; color:#94A3B8;'>{p_data['status']} | {p_data['rientro']}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 5px 0px;'>", unsafe_allow_html=True)

if st.sidebar.button("Reset Completo Asta"):
    if os.path.exists(SAVE_FILE):
        try: os.remove(SAVE_FILE)
        except Exception: pass
    st.session_state.clear()
    st.rerun()

# ==============================================================================
# 7. HEADER & METRICHE GENERALI
# ==============================================================================
st.title("FantaAsta 2026/27 Pro Master Suite")
st.markdown(f"<span style='color:#94A3B8;'>Fase Attiva: <b>{current_stage}</b> | Modificatore Difesa: <b>Attivo</b></span>", unsafe_allow_html=True)
st.write("")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Budget Rimanente", f"{tot_budget_left} cr", f"-{tot_spent} spesi")
m2.metric("Slot Mancanti", f"{tot_slots_needed} / 25")
m3.metric("Offerta Max Sicura", f"{p_max_safe} cr")
m4.metric("Media/Slot", f"{(tot_budget_left / max(1, tot_slots_needed)):.1f} cr")

panic_threshold = st.session_state.base_dept_budget['A'] * 0.9
panic_mode = tot_budget_left <= panic_threshold and get_dept_count('A') == 0

if panic_mode:
    st.error(
        f"**PANIC BUTTON ATTIVO**\n\n"
        f"Hai raggiunto la soglia critica di budget (≤ {panic_threshold} cr) senza aver acquistato alcun attaccante titolare. "
        "Per garantirti i fondi necessari all'acquisto dei bomber previsti dalla tua strategia, il sistema ha forzato il tetto d'asta massimo a 1 credito per tutti i restanti giocatori di movimento. Smetti di rilanciare!"
    )

st.write("")

# ==============================================================================
# 8. MACRO-AREE E NAVIGAZIONE (DASHBOARD MODERNA)
# ==============================================================================
macro_tabs = st.tabs([
    "Asta Live & Strategia",
    "Tattica & Studio",
    "Lega & Avversari",
    "Dati & Export"
])

# ------------------------------------------------------------------------------
# MACRO AREA 1: ASTA LIVE & STRATEGIA
# ------------------------------------------------------------------------------
with macro_tabs[0]:
    t_live, t_road, t_simul, t_duel = st.tabs(["Assegnazione Live", "Roadmap Dinamica", "Simulatore Asta", "Testa a Testa"])
    
    with t_live:
        st.subheader(f"Chiamata & Analisi Istantanea ({current_stage})")
        
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
            btn_confirm = st.button("Conferma Assegnazione", use_container_width=True, type="primary")

        st.markdown("<span style='color:#94A3B8; font-size:14px; font-weight:500;'>Rilancio Rapido Keypad:</span>", unsafe_allow_html=True)
        kp1, kp2, kp3, kp4 = st.columns(4)
        if kp1.button("+ 1 cr", use_container_width=True):
            st.session_state.quick_bid_val = min(p_max_safe, bid_price + 1)
            st.rerun()
        if kp2.button("+ 5 cr", use_container_width=True):
            st.session_state.quick_bid_val = min(p_max_safe, bid_price + 5)
            st.rerun()
        if kp3.button("+ 10 cr", use_container_width=True):
            st.session_state.quick_bid_val = min(p_max_safe, bid_price + 10)
            st.rerun()
        if kp4.button("All-in Pmax", use_container_width=True):
            st.session_state.quick_bid_val = p_max_safe
            st.rerun()

        if player_info is not None:
            # Controllo Infortuni Istantaneo
            inj_key = next((k for k in INJURY_LIST.keys() if k.lower() in sel_player.lower() or sel_player.lower() in k.lower()), None)
            if inj_key:
                inj_data = INJURY_LIST[inj_key]
                st.error(f"**ALLERTA INFORTUNIO/SQUALIFICA:** {sel_player} soffre di {inj_data['infortunio'].lower()}. \n\nRientro stimato: {inj_data['rientro']} ({inj_data['status']})")

            st.write("")
            c_eval1, c_eval2, c_eval3, c_eval4 = st.columns(4)
            c_eval1.metric("Squadra & Ruolo", f"{player_team} ({player_role})", f"Qt: {player_qta} | FVM: {player_fvm}")
            
            delta_val = int(round(dyn_target - base_target))
            target_delta_str = f"{delta_val:+d} cr vs listino" if delta_val != 0 else "In linea con target"
            c_eval2.metric("Target Adattato", f"{int(round(dyn_target))} cr", target_delta_str)
            c_eval3.metric("Stop-Loss Dinamica", f"{int(round(dyn_max_bid))} cr", "Tetto massimo")
            c_eval4.metric(f"Cassa Reparto ({player_role})", f"{eval_data['dept_budget_left']} cr", f"{eval_data['dept_slots_left']} slot liberi")

            live_stats = get_live_player_stats(sel_player, player_team)
            if live_stats:
                st.markdown("<br><span style='color:#94A3B8; font-size:15px; font-weight:600;'>Statistiche Avanzate & Scouting</span>", unsafe_allow_html=True)
                
                logo_url = get_team_logo_url(player_team)
                photo_url = live_stats.get('photo', '')
                status_txt = 'Infortunato' if live_stats.get('is_injured') else 'Disponibile'
                
                html_block = (
                    '<div style="display:flex; align-items:center; gap: 15px; margin-bottom: 15px;">'
                    f'<img src="{photo_url}" width="60" style="border-radius:50%; border: 2px solid #8B5CF6;">'
                    f'<img src="{logo_url}" width="40">'
                    f'<h4 style="margin:0; font-weight:600;">Status: {status_txt}</h4>'
                    '</div>'
                )
                st.markdown(html_block, unsafe_allow_html=True)
                
                st_col1, st_col2, st_col3, st_col4 = st.columns(4)
                st_col1.metric("Pres. / Minuti", f"{live_stats['appearances']} ({live_stats['minutes']} min)")
                st_col2.metric("Gol / Assist", f"{live_stats['goals']} / {live_stats['assists']}")
                st_col3.metric("Tiri a Partita", f"{live_stats['shots_per_game']}")
                st_col4.metric("Cartellini (G/R)", f"{live_stats['yellow_cards']} / {live_stats['red_cards']}")

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
                st.info(f"**AI Predictor:** L'avversario più pericoloso su {sel_player} è **{top_threat[0]}** (Pmax: `{top_threat[1]} cr`, {top_threat[2]} slot liberi).")

            pen_info = PENALTY_TAKERS.get(player_team, [])
            is_penalty = [p for p in pen_info if sel_player.lower() in p.lower()]
            pen_str = f"Rigorista: {is_penalty[0]}" if is_penalty else "Nessun rigore primario"
            st.caption(f"Status Piazzati: {pen_str}")

            if eval_data["is_full"]:
                st.error(f"Reparto {player_role} completo.")
            elif bid_price <= dyn_target:
                st.success(f"{bid_price} cr è in target. Rilancia.")
            elif bid_price <= dyn_max_bid:
                st.warning(f"{bid_price} cr è accettabile (Stop-Loss: {dyn_max_bid} cr).")
            else:
                st.error(f"Stop rilancio. Limite di {dyn_max_bid} cr superato.")

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
                    st.rerun()
                else:
                    st.error(f"Reparto {player_role} completo!")
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
                    st.rerun()

        # Consigliati dalla Roadmap
        st.write("")
        st.subheader("Obiettivi Suggeriti")
        
        roles_to_check = [active_role] if active_role else ['P', 'D', 'C', 'A']
        recs = []
        
        temp_allocated = set(p['name'] for p in st.session_state.get('my_roster', []))
        purchased_reg = st.session_state.get('purchased_registry', {})
        rejected_list = st.session_state.get('rejected_players', [])
        
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
                        slot_res = get_dynamic_slot_candidates(r, t_budget, purchased_reg, temp_allocated, custom_user_targets_list=user_custom_picks, rejected_players=rejected_list)
                        
                        if slot_res['chosen_name'] != "Scommessa / Copertura":
                            is_custom = slot_res['chosen_name'] in user_custom_picks
                            card_style = "Consigliato"
                            
                            if is_custom:
                                if r == 'P' and slot_res['chosen_name'] in [k[0] for k in GOALIE_HIERARCHY.get(st.session_state.get('selected_keeper_club', 'Inter'), [])] and slot_res['chosen_name'] not in st.session_state.get('custom_user_targets', {}).get('P', []):
                                    card_style = f"Blocco {st.session_state.get('selected_keeper_club', 'Inter')}"
                                else:
                                    card_style = "Tuo Top"

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
                            
                            if len(recs) >= 4: break
            if len(recs) >= 4: break
                
        if recs:
            recs = sorted(recs, key=lambda x: x['is_custom'], reverse=True)
            rec_cols = st.columns(min(4, len(recs)))
            for i, rec in enumerate(recs[:4]):
                with rec_cols[i]:
                    logo_img = f"<img src='{get_team_logo_url(rec['team'])}' width='22' style='vertical-align: middle; margin-right: 6px;'>"
                    accent_class = " glass-card-accent" if rec['is_custom'] else ""
                    
                    card_html = (
                        f"<div class='glass-card{accent_class}'>"
                        f"<div style='margin-bottom: 8px;'>{logo_img}<b>{rec['role']} | {rec['name']}</b></div>"
                        f"<span style='font-size:12px; color:#94A3B8;'>{rec['card_style']}</span><br><br>"
                        f"Target: <b>{rec['target']} cr</b><br>"
                        f"Max: <b>{rec['max']} cr</b>"
                        "</div>"
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    st.write("")
                    if st.button(f"Chiama", key=f"btn_call_rec_{rec['name']}_{i}", use_container_width=True):
                        st.session_state.target_call_player = rec['name']
                        st.rerun()
                    
                    bc1, bc2 = st.columns(2)
                    if rec['is_custom']:
                        if bc1.button("Sblocca", key=f"unlock_rec_{rec['name']}_{i}", use_container_width=True):
                            st.session_state.custom_user_targets[rec['role']].remove(rec['name'])
                            save_state_to_disk()
                            st.rerun()
                    else:
                        if bc1.button("Blocca", key=f"lock_rec_{rec['name']}_{i}", use_container_width=True):
                            st.session_state.custom_user_targets[rec['role']].append(rec['name'])
                            save_state_to_disk()
                            st.rerun()
                        if bc2.button("Cambia", key=f"change_rec_{rec['name']}_{i}", use_container_width=True):
                            st.session_state.rejected_players.append(rec['name'])
                            save_state_to_disk()
                            st.rerun()
        else:
            st.caption("Nessun giocatore primario consigliato. Sei a posto con i titolari, punta su scommesse a 1 cr!")

        # ==========================================
        # 🎣 SEZIONE: GIOCATORI ESCA (BLUFF)
        # ==========================================
        st.markdown("---")
        st.subheader("🎣 Giocatori Esca (Fai svenare i rivali)")
        st.caption("Chiama questi top player per prosciugare i crediti degli avversari. Sono giocatori costosi che l'algoritmo sa che NON rientrano nei tuoi obiettivi bloccati.")
        
        # Raccogliamo i giocatori che vogliamo assolutamente
        wanted_players = []
        for r_code in ['P', 'D', 'C', 'A']:
            wanted_players.extend(st.session_state.custom_user_targets.get(r_code, []))
            
        # Filtriamo il listone: prendiamo chi NON è stato comprato e NON è tra i nostri target, ordinato per FVM (i più costosi)
        df_esca = listone_df[
            (~listone_df['Nome'].isin(st.session_state.purchased_registry.keys())) & 
            (~listone_df['Nome'].isin(wanted_players))
        ].sort_values(by='FVM', ascending=False).head(4)
        
        if not df_esca.empty:
            esca_cols = st.columns(len(df_esca))
            for i, (_, dec_p) in enumerate(df_esca.iterrows()):
                with esca_cols[i]:
                    logo_img = f"<img src='{get_team_logo_url(dec_p['Squadra'])}' width='22' style='vertical-align: middle; margin-right: 6px;'>"
                    
                    # Card con effetto glow rosso per le esche
                    card_html = (
                        f"<div class='glass-card' style='border-color: rgba(244, 63, 94, 0.4); background: rgba(244, 63, 94, 0.05);'>"
                        f"<div style='margin-bottom: 8px;'>{logo_img}<b>{dec_p['R']} | {dec_p['Nome']}</b></div>"
                        f"<span style='font-size:12px; color:#F43F5E; font-weight:bold;'>🔥 Esca ad alto costo</span><br><br>"
                        f"FVM Stimato: <b>{int(dec_p['FVM'])} cr</b><br>"
                        f"Quotazione: <b>{int(dec_p['Qt.A'])}</b>"
                        "</div>"
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    st.write("")
                    # Bottone rapido per caricare l'esca in cima per l'asta
                    if st.button(f"Chiama Esca", key=f"btn_esca_call_{dec_p['Nome']}_{i}", use_container_width=True):
                        st.session_state.target_call_player = dec_p['Nome']
                        st.rerun()
        else:
            st.caption("Nessuna esca disponibile ad alto costo al momento.")

    with t_road:
        col_rm1, col_rm2 = st.columns([3, 1])
        with col_rm1:
            st.subheader("Roadmap Dinamica")
            st.caption(f"Strategia attiva: {st.session_state.selected_strategy}")
        with col_rm2:
            if st.button("Ripristina Scartati", use_container_width=True):
                st.session_state.rejected_players = []
                save_state_to_disk()
                st.rerun()
                
        with st.expander("Personalizza i tuoi Top di Reparto", expanded=False):
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
            ["Panoramica Completa", "Portieri (P)", "Difensori (D)", "Centrocampisti (C)", "Attaccanti (A)"]
        )

        if selected_cat in ["Panoramica Completa", "Portieri (P)"]:
            k_club = st.session_state.selected_keeper_club
            st.markdown(f"### Portieri (Blocco Base: **{k_club}**)")
            
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
                st.warning(f"Vice Mancante: {lost_co_name} acquistato da {lost_co_buyer} a {lost_co_price} cr. Sfrutta gli incroci di calendario.")
                
                st.markdown("##### Migliori Incroci:")
                suggested_pairings = GOALKEEPER_PAIRINGS.get(k_club, GOALKEEPER_PAIRINGS['Inter'])
                
                pair_cols = st.columns(min(3, len(suggested_pairings)))
                for p_idx, pair_info in enumerate(suggested_pairings[:3]):
                    with pair_cols[p_idx]:
                        logo_p = get_team_logo_url(pair_info['club'])
                        card_text = (
                            "<div class='glass-card'>"
                            f"<div style='margin-bottom: 8px;'><img src='{logo_p}' width='20' style='vertical-align: middle;'> <b>{pair_info['club']}: {pair_info['starter']}</b></div>"
                            f"Target: <b>{pair_info['target']} cr</b> | Max: <b>{pair_info['max']} cr</b><br>"
                            f"<span style='font-size:13px; color:#94A3B8;'>{pair_info['diff']}</span>"
                            "</div>"
                        )
                        st.markdown(card_text, unsafe_allow_html=True)
                st.write("")

            kp_cols = st.columns(3)
            for idx, (k_col, k_info) in enumerate(zip(kp_cols, k_list)):
                with k_col:
                    slot_label = f"POR {idx+1}"
                    if idx < len(p_bought):
                        p_b = p_bought[idx]
                        logo_img = f"<img src='{get_team_logo_url(p_b['team'])}' width='22' style='vertical-align: middle; margin-right: 6px;'>"
                        card_html = (
                            "<div class='glass-card'>"
                            f"<div style='margin-bottom: 10px;'>{logo_img}<b>{slot_label}: {p_b['name']}</b></div>"
                            f"<span style='color:#10B981;'>✓ Acquistato:</span> <b>{p_b['price']} cr</b><br>"
                            "<div class='glass-card-mini-text'>In Rosa</div>"
                            "</div>"
                        )
                        st.markdown(card_html, unsafe_allow_html=True)
                    else:
                        if idx == 1 and co_starter_lost:
                            top_pair = GOALKEEPER_PAIRINGS.get(k_club, GOALKEEPER_PAIRINGS['Inter'])[0]
                            logo_img = f"<img src='{get_team_logo_url(top_pair['club'])}' width='22' style='vertical-align: middle; margin-right: 6px;'>"
                            card_html = (
                                "<div class='glass-card glass-card-accent'>"
                                f"<div style='margin-bottom: 10px;'>{logo_img}<b>{slot_label}: {top_pair['starter']}</b></div>"
                                f"Target: <b>{top_pair['target']} cr</b> | Max: <b>{top_pair['max']} cr</b><br>"
                                f"<div class='glass-card-mini-text'>Alternanza con {p_bought[0]['name']}</div>"
                                "</div>"
                            )
                            st.markdown(card_html, unsafe_allow_html=True)
                        else:
                            logo_img = f"<img src='{get_team_logo_url(k_club)}' width='22' style='vertical-align: middle; margin-right: 6px;'>"
                            card_html = (
                                "<div class='glass-card'>"
                                f"<div style='margin-bottom: 10px;'>{logo_img}<b>{slot_label}: {k_info[0]}</b></div>"
                                f"Target: <b>{k_info[1]} cr</b> | Max: <b>{k_info[2]} cr</b><br>"
                                f"<div class='glass-card-mini-text'>Copertura Blocco {k_club}</div>"
                                "</div>"
                            )
                            st.markdown(card_html, unsafe_allow_html=True)
            st.write("")

        if selected_cat in ["Panoramica Completa", "Difensori (D)"]:
            render_role_card_grid('D', f"Difensori (Modificatore - Budget Base: {st.session_state.base_dept_budget['D']} cr)", num_cols=4)
            st.write("")

        if selected_cat in ["Panoramica Completa", "Centrocampisti (C)"]:
            render_role_card_grid('C', f"Centrocampisti (Bonus - Budget Base: {st.session_state.base_dept_budget['C']} cr)", num_cols=4)
            st.write("")

        if selected_cat in ["Panoramica Completa", "Attaccanti (A)"]:
            render_role_card_grid('A', f"Attaccanti (Finalizzatori - Budget Base: {st.session_state.base_dept_budget['A']} cr)", num_cols=3)

    with t_simul:
        st.subheader("🤖 Asta Simulatore RPG (Turni, Hype, Countdown)")
        
        # --- FIX MEMORIA ---
        # --- FIX MEMORIA E SINCRONIZZAZIONE NOMI ---
        expected_bidders = ["Tu"] + list(st.session_state.opponents.keys())
        if 'auction_sequence' not in st.session_state or set(st.session_state.auction_sequence) != set(expected_bidders):
            st.session_state.auction_sequence = expected_bidders
            st.session_state.turn_idx = 0
        if 'turn_idx' not in st.session_state: st.session_state.turn_idx = 0
        if 'role_sequence' not in st.session_state: st.session_state.role_sequence = ['P', 'D', 'C', 'A']
        if 'current_role_idx' not in st.session_state: st.session_state.current_role_idx = 0
        
        current_draft_role = st.session_state.role_sequence[st.session_state.current_role_idx]
        
        all_completed = True
        if len([p for p in st.session_state.my_roster if p['role'] == current_draft_role]) < SLOTS[current_draft_role]: all_completed = False
        for opp in st.session_state.opponents.values():
            if len(opp['roster'][current_draft_role]) < SLOTS[current_draft_role]: all_completed = False
            
        if all_completed and st.session_state.current_role_idx < 3:
            st.session_state.current_role_idx += 1
            current_draft_role = st.session_state.role_sequence[st.session_state.current_role_idx]
            st.success(f"✅ Ruolo completato da tutti! Si passa a: **{current_draft_role}**")
            st.rerun()

        caller_key = st.session_state.auction_sequence[st.session_state.turn_idx]
        caller_prof = st.session_state.opponents[caller_key].get('profile', '') if caller_key != "Tu" else "Umano"
        
        if 'sim_state' not in st.session_state: st.session_state.sim_state = "IDLE"
        if 'sim_player' not in st.session_state: st.session_state.sim_player = None
        if 'sim_logs' not in st.session_state: st.session_state.sim_logs = []
        
        st.markdown(f"#### 🏟️ Turno di Chiamata: <span style='color:#8B5CF6;'>{caller_key}</span> | Ruolo Obbligatorio: <span style='color:#10B981;'>{current_draft_role}</span>", unsafe_allow_html=True)
        with st.expander("📊 Tabellone Live Crediti & Pmax (Clicca per espandere)", expanded=False):
            live_data = [{"Squadra": "Tu", "Crediti": tot_budget_left, "PMax": p_max_safe}]
            for k, v in st.session_state.opponents.items():
                pm = v['budget'] - (v['slots_left'] - 1) if v['slots_left'] > 0 else 0
                live_data.append({"Squadra": v['name'], "Crediti": v['budget'], "PMax": pm})
            st.dataframe(pd.DataFrame(live_data).sort_values(by="PMax", ascending=False).transpose())
        st.markdown("---")

        def advance_turn():
            st.session_state.turn_idx = (st.session_state.turn_idx + 1) % len(st.session_state.auction_sequence)

        def plan_next_bot_bid():
            bidders = st.session_state.sim_bidders_limits
            curr_bid = st.session_state.sim_current_bid
            curr_winner = st.session_state.sim_current_winner
            active_bots = {k: v for k, v in bidders.items() if v > curr_bid and k != curr_winner}
            
            if active_bots:
                now = time.time()
                time_left = max(0.0, st.session_state.sim_deadline - now)
                
                next_bot = random.choice(list(active_bots.keys()))
                gap = active_bots[next_bot] - curr_bid
                prof = st.session_state.opponents[next_bot].get('profile', 'Equilibrato')
                
                if prof == "Smanioso" and gap > 15: inc = random.choice([5, 10])
                elif prof == "Scommettitore" and gap > 5: inc = random.choice([2, 3])
                elif gap > 20: inc = random.choice([2, 5])
                else: inc = 1
                
                reaction_time = random.uniform(0.5, 3.0) if time_left > 4.0 else random.uniform(0.1, 1.5)
                st.session_state.sim_bot_next_bid = {
                    'name': next_bot, 'amount': curr_bid + inc, 'time': time.time() + reaction_time
                }
            else:
                st.session_state.sim_bot_next_bid = None

        def handle_user_bid(inc):
            new_bid = st.session_state.sim_current_bid + inc
            if new_bid <= p_max_safe:
                st.session_state.sim_current_bid = new_bid
                st.session_state.sim_current_winner = "Tu"
                st.session_state.sim_deadline = time.time() + 10.0 
                st.session_state.sim_logs.append(f"<div class='log-entry user'>👉 <b>Tu</b> rilanci a <b>{new_bid} cr</b></div>")
                plan_next_bot_bid()
                
        def handle_user_fold():
            st.session_state.sim_user_folded = True
            st.session_state.sim_logs.append("<div class='log-entry drop'>👉 <b>Tu</b> passi la mano.</div>")
            
        c_sim1, c_sim2 = st.columns([1, 2])
        
        with c_sim1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if st.session_state.sim_state in ["IDLE", "SOLD"]:
                if caller_key == "Tu":
                    avail_df = listone_df[(listone_df['R'] == current_draft_role) & (~listone_df['Nome'].isin(st.session_state.purchased_registry.keys()))]
                    sel_p = st.selectbox(f"Tocca a Te! Scegli un {current_draft_role}:", options=avail_df['Nome'].tolist() if not avail_df.empty else ["Nessuno"])
                    if st.button("📢 Chiama Giocatore", type="primary", use_container_width=True) and sel_p != "Nessuno":
                        st.session_state.sim_player = listone_df[listone_df['Nome'] == sel_p].iloc[0].to_dict()
                        st.session_state.sim_state = "READY"
                        st.rerun()
                else:
                    st.info(f"Tocca a **{caller_key} ({caller_prof})** chiamare.")
                    if st.button("Fai chiamare il Bot", use_container_width=True):
                        picked = bot_effettua_chiamata(caller_key, current_draft_role)
                        if picked:
                            st.session_state.sim_player = picked
                            st.session_state.sim_state = "READY"
                            st.rerun()
                        else:
                            st.warning(f"Nessun {current_draft_role} rimasto.")
                            advance_turn()
                            st.rerun()
                        
            if st.session_state.sim_player:
                p = st.session_state.sim_player
                bt, mb = get_player_base_target(p)
                tier, hype, prop = analizza_giocatore_avanzato(p)
                dyn_stop = min(mb, p_max_safe)
                
                st.markdown(f"### <img src='{get_team_logo_url(p.get('Squadra',''))}' width='30' style='vertical-align: middle;'> {p['Nome']}", unsafe_allow_html=True)
                st.write(f"**Ruolo:** {p['R']} | **Fascia:** {tier}")
                st.markdown("---")
                st.markdown(f"🔥 **Hype Estivo:** `{hype}/100`")
                st.markdown(f"📈 **Propensione Bonus:** `{prop}`")
                st.markdown(f"🎯 **Target:** `{bt} cr` | 🛑 **Stop-Loss:** `{dyn_stop} cr`")
                st.markdown("---")
                
                if st.session_state.sim_state == "READY":
                    if st.button("🔨 Inizia Asta!", type="primary", use_container_width=True):
                        st.session_state.sim_state = "RUNNING"
                        st.session_state.sim_current_bid = 1
                        st.session_state.sim_current_winner = caller_key 
                        st.session_state.sim_user_folded = False
                        st.session_state.sim_deadline = time.time() + 10.0 
                        st.session_state.sim_logs = [f"<div class='log-entry'>🎙️ <b>{caller_key}</b> chiama {p['Nome']} a 1 credito!</div>"]
                        
                        st.session_state.sim_bidders_limits = {}
                        for k, v in st.session_state.opponents.items():
                            m = calcola_limite_massimo_bot(v, p, active_fomo=True)
                            if m > 0: st.session_state.sim_bidders_limits[k] = m
                            
                        plan_next_bot_bid()
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with c_sim2:
            if st.session_state.sim_state == "RUNNING":
                html_log = f"<div class='log-box'>{''.join(st.session_state.sim_logs[-10:])}</div>"
                st.markdown(html_log, unsafe_allow_html=True)
                
                st.markdown(f"<h3 style='text-align:center;'>Offerta Attuale: <span style='color:#10B981;'>{st.session_state.sim_current_bid} cr</span> ({st.session_state.sim_current_winner})</h3>", unsafe_allow_html=True)
                
                if not st.session_state.sim_user_folded:
                    cb1, cb2, cb3, cb4 = st.columns(4)
                    cb1.button("+ 1 cr", use_container_width=True, key="sim1", on_click=handle_user_bid, args=(1,))
                    cb2.button("+ 5 cr", use_container_width=True, key="sim5", on_click=handle_user_bid, args=(5,))
                    cb3.button("+ 10 cr", use_container_width=True, key="sim10", on_click=handle_user_bid, args=(10,))
                    cb4.button("Lascia", use_container_width=True, key="sim_f", on_click=handle_user_fold)

                now = time.time()
                time_left = max(0.0, st.session_state.sim_deadline - now)
                
                if st.session_state.sim_bot_next_bid and now >= st.session_state.sim_bot_next_bid['time']:
                    b_info = st.session_state.sim_bot_next_bid
                    st.session_state.sim_current_bid = b_info['amount']
                    st.session_state.sim_current_winner = b_info['name']
                    prof = st.session_state.opponents[b_info['name']].get('profile', '')
                    
                    trash_msg = ""
                    if random.random() < 0.15:
                        trash_msg = f"<br><span style='font-size:12px; color:#A78BFA; font-style:italic;'>💬 \"{random.choice(BOT_TRASH_TALK)}\"</span>"
                        
                    st.session_state.sim_logs.append(f"<div class='log-entry bot'>👉 <b>{b_info['name']} ({prof})</b> rilancia a <b>{b_info['amount']} cr</b>{trash_msg}</div>")
                    st.session_state.sim_deadline = time.time() + 10.0 
                    plan_next_bot_bid()
                    st.rerun()

                if time_left < 3.0 and st.session_state.sim_bot_next_bid is None:
                    if random.random() < 0.2: plan_next_bot_bid()

                if time_left == 0.0:
                    st.session_state.sim_state = "SOLD"
                    w = st.session_state.sim_current_winner
                    b = st.session_state.sim_current_bid
                    p = st.session_state.sim_player
                    
                    st.session_state.sim_logs.append(f"<div class='log-entry win'>🔨 AGGIUDICATO! <b>{w}</b> si porta a casa {p['Nome']} per <b>{b} cr</b>.</div>")
                    
                    if w == "Tu": st.session_state.my_roster.append({'name': p['Nome'], 'team': p['Squadra'], 'role': p['R'], 'price': b})
                    elif w != "Nessuno":
                        st.session_state.opponents[w]['budget'] -= b
                        st.session_state.opponents[w]['slots_left'] -= 1
                        st.session_state.opponents[w]['roster'][p['R']].append({'name': p['Nome'], 'team': p['Squadra'], 'price': b})
                    
                    if w != "Nessuno":
                        st.session_state.purchased_registry[p['Nome']] = (w, b)
                        st.session_state.history.append({'buyer': w, 'name': p['Nome'], 'team': p['Squadra'], 'role': p['R'], 'price': b})
                        save_state_to_disk()
                        
                    advance_turn() 
                    st.rerun()
                else:
                    color = "#10B981" if time_left > 5.0 else ("#F59E0B" if time_left > 2.0 else "#F43F5E")
                    st.markdown(f"<h1 style='text-align:center; color:{color}; font-size:4rem;'>⏱️ {time_left:.1f}</h1>", unsafe_allow_html=True)
                    time.sleep(0.3)
                    st.rerun()

            elif st.session_state.sim_state == "SOLD":
                html_log = f"<div class='log-box'>{''.join(st.session_state.sim_logs[-10:])}</div>"
                st.markdown(html_log, unsafe_allow_html=True)
                
                w = st.session_state.sim_current_winner
                b = st.session_state.sim_current_bid
                p = st.session_state.sim_player
                bt, _ = get_player_base_target(p)
                
                if w == "Nessuno": st.info("Giocatore Svincolato. Si passa al prossimo turno.")
                elif w == "Tu": st.success(f"🎉 **HAI VINTO!** {p['Nome']} aggiunto alla rosa.")
                else: st.error(f"❌ **ASTA PERSA.** Assegnato a {w} per {b} cr.")
                
                if st.button("Avanti al Prossimo Turno 👉", type="primary", use_container_width=True):
                    st.session_state.sim_state = "IDLE"
                    st.rerun()
            else:
                st.markdown("<div class='log-box'><div class='log-entry drop'>Inizia l'asta per far partire il timer real-time a 10 secondi.</div></div>", unsafe_allow_html=True)
   
    with t_duel:
        st.subheader("Confronto Testa a Testa")
        
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
                logo1 = get_team_logo_url(row1['Squadra'])
                st.markdown(f"### <img src='{logo1}' width='28' style='vertical-align: middle;'> {p_name_1}", unsafe_allow_html=True)
                st.write(f"Squadra: {row1['Squadra']} ({row1['R']})")
                st.write(f"Target Adattato: **{int(round(eval1['dyn_target']))} cr** | Max: **{int(round(eval1['dyn_max_bid']))} cr**")
                pen1 = [p for p in PENALTY_TAKERS.get(row1['Squadra'], []) if p_name_1.lower() in p.lower()]
                st.caption(f"Status Rigori: {pen1[0] if pen1 else 'Nessuno'}")
                
            with col_card2:
                logo2 = get_team_logo_url(row2['Squadra'])
                st.markdown(f"### <img src='{logo2}' width='28' style='vertical-align: middle;'> {p_name_2}", unsafe_allow_html=True)
                st.write(f"Squadra: {row2['Squadra']} ({row2['R']})")
                st.write(f"Target Adattato: **{int(round(eval2['dyn_target']))} cr** | Max: **{int(round(eval2['dyn_max_bid']))} cr**")
                pen2 = [p for p in PENALTY_TAKERS.get(row2['Squadra'], []) if p_name_2.lower() in p.lower()]
                st.caption(f"Status Rigori: {pen2[0] if pen2 else 'Nessuno'}")

            st.divider()
            diff_cr = int(round(eval1['dyn_target'] - eval2['dyn_target']))
            if diff_cr > 0:
                st.info(f"**Verdetto:** {p_name_1} richiede **+{diff_cr} cr** rispetto a {p_name_2}. Scegli {p_name_2} per risparmiare.")
            elif diff_cr < 0:
                st.info(f"**Verdetto:** {p_name_2} richiede **+{abs(diff_cr)} cr** rispetto a {p_name_1}. Scegli {p_name_1} per risparmiare.")
            else:
                st.info(f"**Verdetto:** Stesso impatto economico ({int(round(eval1['dyn_target']))} cr).")

# ------------------------------------------------------------------------------
# MACRO AREA 2: TATTICA & STUDIO
# ------------------------------------------------------------------------------
with macro_tabs[1]:
    t_guide, t_syn, t_sim = st.tabs(["Guida Tattica Squadre", "Sinergie & Abbinamenti", "Simulatore 11 Titolare"])
    
    with t_guide:
        st.subheader("Guida Tattica Integrale")
        sel_team_guide = st.selectbox("Seleziona Club:", options=sorted(list(TEAMS_TACTICAL_DB.keys())))
        team_data = TEAMS_TACTICAL_DB[sel_team_guide]

        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            logo_t = get_team_logo_url(sel_team_guide)
            st.markdown(f"### <img src='{logo_t}' width='35' style='vertical-align: middle; margin-right: 8px;'> {sel_team_guide}", unsafe_allow_html=True)
            st.write(f"**Allenatore:** {team_data['coach']}")
            st.write(f"**Modulo Tattico:** {team_data['formation']}")
            st.write(f"**Gerarchia Porta:** {team_data['gk']}")
            st.write(f"**Difesa:** {team_data['defense']}")
            st.write(f"**Centrocampo:** {team_data['midfield']}")
            st.write(f"**Attacco:** {team_data['attack']}")

        with col_t2:
            st.markdown("#### Gerarchia Rigoristi")
            for r_idx, r_name in enumerate(team_data.get('penalties', [])):
                st.write(f"- {r_name}")
            
            st.write("")
            st.info(team_data['advice'])

    with t_syn:
        st.subheader("Sinergie & Abbinamenti Perfetti 2026/27")
        st.caption("Ottimizza il capitale studiando gli incroci di calendario.")
        
        analisi_sel = st.radio("Seleziona Analisi:", ["Griglia Portieri", "Coppie & Terzetti Attacco", "Sinergie Simmetriche"], horizontal=True)
        st.write("")
        
        if analisi_sel == "Griglia Portieri":
            st.markdown("#### Abbinamenti per Portieri Top (3° Slot)")
            portieri_top = [
                {"Portiere Top": "Mile Svilar (48.17 cr)", "Squadra": "Roma", "Migliori Abbinamenti": "Bologna (95), Monza (93), Venezia (92), Genoa (89)", "Analisi": "L'indice 95 con il Bologna rappresenta la massima efficienza statistica per le trasferte proibitive della Roma."},
                {"Portiere Top": "Alex Meret (41.66 cr)", "Squadra": "Napoli", "Migliori Abbinamenti": "Lecce (93), Torino (93), Frosinone (91), Fiorentina (89)", "Analisi": "Il pragmatismo di Allegri tutela Meret. Accoppiarlo a Falcone o Mascardi/Perri fornisce un paracadute eccellente a costo marginale."},
                {"Portiere Top": "Mike Maignan (36.08 cr)", "Squadra": "Milan", "Migliori Abbinamenti": "Fiorentina (93), Lecce (93), Parma (93), Sassuolo (92), Torino (92)", "Analisi": "L'accoppiamento con il Lecce (Falcone) è il più economico e redditizio per il sistema di Amorim."},
                {"Portiere Top": "M. Carnesecchi (34.95 cr)", "Squadra": "Atalanta", "Migliori Abbinamenti": "Sassuolo (95), Monza (92), Bologna (91), Udinese (91)", "Analisi": "L'abbinamento a 95 con il Sassuolo offre una copertura perfetta, cruciale per l'emergenza infortuni atalantina (Hien, Kristensen) sotto Sarri."},
                {"Portiere Top": "Guglielmo Vicario (34.19 cr)", "Squadra": "Juventus", "Migliori Abbinamenti": "Bologna (92), Cagliari (92), Lazio (92), Torino (92), Parma (91), Fiorentina (91)", "Analisi": "L'accoppiata con il Cagliari è ottimale per il rapporto qualità-prezzo, sfruttando la solidità casalinga di Spalletti e Pisacane."},
                {"Portiere Top": "Josep Martinez (32.69 cr)", "Squadra": "Inter", "Migliori Abbinamenti": "Bologna (95), Cagliari (93), Monza (93), Torino (92), Sassuolo (91)", "Analisi": "Affiancare il duo interista (di Chivu) a Skorupski crea un fortino quasi impenetrabile."},
                {"Portiere Top": "Jean Butez (31.21 cr)", "Squadra": "Como", "Migliori Abbinamenti": "Bologna (93), Udinese (93), Fiorentina (92), Sassuolo (92), Torino (92)", "Analisi": "L'incredibile resa del Como di Fabregas rende Butez un top assoluto, affiancabile a Okoye."}
            ]
            st.dataframe(pd.DataFrame(portieri_top), use_container_width=True)
            
            st.markdown("#### Coppie Low Cost (Massimizzare Elasticità)")
            low_cost_p = [
                {"Coppia": "Genoa - Lecce", "Indice": 93, "Portieri": "Bijlow - Falcone", "Analisi": "La miglior combinazione economica assoluta, libera 15-20 crediti rispetto alla media."},
                {"Coppia": "Genoa - Frosinone", "Indice": 92, "Portieri": "Bijlow - Palmisani / Desplanches", "Analisi": "Ottima resa statistica, ma il dualismo nel Frosinone richiede l'acquisto dell'intero blocco ciociaro."},
                {"Coppia": "Parma - Genoa", "Indice": 91, "Portieri": "Corvi/Daffara - Bijlow", "Analisi": "Il ballottaggio parmense richiede l'acquisto di almeno 3 portieri in rosa."},
                {"Coppia": "Bologna - Venezia", "Indice": 91, "Portieri": "Skorupski - Stankovic", "Analisi": "Leggermente più costosa per l'entusiasmo attorno a Stankovic e alla solidità del Bologna di Tedesco."}
            ]
            st.dataframe(pd.DataFrame(low_cost_p), use_container_width=True)
            
        elif analisi_sel == "Coppie & Terzetti Attacco":
            st.markdown("#### Le 5 Coppie Primarie in Attacco")
            att_pairs = [
                {"Coppia": "Atalanta - Sassuolo (95)", "Interpreti": "Scamacca / Raspadori + Berardi / Laurienté", "Analisi": "Costo stimato 110 cr. Il turnover di Sarri post-Champions viene mitigato dalle ali del Sassuolo (Berardi/Laurienté) che non fa coppe."},
                {"Coppia": "Inter - Bologna (95)", "Interpreti": "Thuram / Lautaro + Dovbyk / Orsolini", "Analisi": "Affiancare Thuram a Dovbyk genera un tandem formidabile da ~155 cr, schierando sempre un terminale contro difese deboli."},
                {"Coppia": "Como - Udinese (93)", "Interpreti": "Douvikas / Paz + Davis", "Analisi": "Douvikas e Davis costano ~116 cr combinati (23% del budget): due specialisti rigoristi perfetti per il tridente."},
                {"Coppia": "Milan - Fiorentina (93)", "Interpreti": "Ramos / Pulisic + Gudmundsson / Kean", "Analisi": "Ramos e Gudmundsson costano ~146 cr. Evita la sovrapposizione dei match più ostici."},
                {"Coppia": "Juventus - Cagliari (92)", "Interpreti": "Kolo Muani / Yildiz + Maldini / Kevin Carlos", "Analisi": "Rotazione asimmetrica: Kolo Muani è il perno centrale, le scommesse sarde a basso costo coprono i match difficili della Juve."}
            ]
            st.dataframe(pd.DataFrame(att_pairs), use_container_width=True)
            
            st.markdown("#### Terzetti in Attacco")
            st.write("- **Frosinone - Genoa - Lecce (Indice 99):** Raimondo + Colombo/Vitinha + Krstovic. Costo ~84 cr. Lascia 125 cr per un Super Top.")
            st.write("- **Parma - Genoa - Monza (Indice 99):** Touré + Cutrone/Mota + Colombo. Costo ~70 cr. Ideale per formazioni 4-2-3-1.")

        else:
            st.markdown("#### Sinergie Simmetriche Attacco-Porta")
            st.info("**1. Blocco Atalanta - Sassuolo (Indice 95 per Porta e Attacco)**")
            st.write("- **Spesa Stimata:** ~195 crediti (39% del budget totale).\n- **Portieri:** Carnesecchi + Muric (~55 cr).\n- **Attaccanti:** Scamacca + Berardi + Laurienté (~139.82 cr).")
            
            st.info("**2. Blocco Inter - Bologna (Indice 95 per Porta e Attacco)**")
            st.write("- **Spesa Stimata:** ~258 crediti (51.6% del budget totale).\n- **Portieri:** Martinez + Skorupski (~55 cr).\n- **Attaccanti:** Thuram + Orsolini + Castro (~203.13 cr).")

    with t_sim:
        st.subheader("Simulatore 11 Titolare")
        
        col_f_opt, col_f_metrics = st.columns([1, 2])
        with col_f_opt:
            formation_pref = st.radio("Modulo Titolare:", ["4-3-3 (Modificatore)", "3-4-3 (Tridente)"])
        
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
            m_t2.metric("Punteggio Atteso Base", f"{expected_points:.1f} pt")
            mod_status = "Attivo (+3/+6 pt)" if ("4-3-3" in formation_pref and len(starters_d) >= 4) else "Non attivo"
            m_t3.metric("Status Modificatore", mod_status)

        st.write("")
        
        st.markdown('<div class="pitch-container">', unsafe_allow_html=True)
        
        st.markdown('<div class="pitch-row">', unsafe_allow_html=True)
        for i in range(req_a):
            if i < len(starters_a):
                p = starters_a[i]
                logo = f"<img src='{get_team_logo_url(p['team'])}' width='22' style='margin-bottom: 4px;'><br>"
                st.markdown(f'<div class="player-disc">{logo}<b>{p["name"]}</b><br><small style="color:#94A3B8;">{p["price"]} cr</small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="player-disc-empty">Attaccante {i+1}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="pitch-row">', unsafe_allow_html=True)
        for i in range(req_c):
            if i < len(starters_c):
                p = starters_c[i]
                logo = f"<img src='{get_team_logo_url(p['team'])}' width='22' style='margin-bottom: 4px;'><br>"
                st.markdown(f'<div class="player-disc">{logo}<b>{p["name"]}</b><br><small style="color:#94A3B8;">{p["price"]} cr</small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="player-disc-empty">Centrocampista {i+1}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="pitch-row">', unsafe_allow_html=True)
        for i in range(req_d):
            if i < len(starters_d):
                p = starters_d[i]
                logo = f"<img src='{get_team_logo_url(p['team'])}' width='22' style='margin-bottom: 4px;'><br>"
                st.markdown(f'<div class="player-disc">{logo}<b>{p["name"]}</b><br><small style="color:#94A3B8;">{p["price"]} cr</small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="player-disc-empty">Difensore {i+1}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="pitch-row">', unsafe_allow_html=True)
        if starters_p:
            p = starters_p[0]
            logo = f"<img src='{get_team_logo_url(p['team'])}' width='22' style='margin-bottom: 4px;'><br>"
            st.markdown(f'<div class="player-disc">{logo}<b>{p["name"]}</b><br><small style="color:#94A3B8;">{p["price"]} cr</small></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="player-disc-empty">Portiere</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# MACRO AREA 3: LEGA E AVVERSARI
# ------------------------------------------------------------------------------
with macro_tabs[2]:
    t_insp, t_track, t_baro = st.tabs(["Ispezione Rose & Svincoli", "Tracker Rivali (Pmax)", "Barometro Lega"])
    
    with t_insp:
        st.subheader("Ispezione Dettagliata Rosa Rivale & Gestione Svincoli")
        opp_names_list = [v['name'] for v in st.session_state.opponents.values()]
        selected_inspect_name = st.selectbox("Seleziona Squadra Rivale da Ispezionare:", options=opp_names_list)
        
        inspect_opp = next((v for v in st.session_state.opponents.values() if v['name'] == selected_inspect_name), None)
        if inspect_opp:
            c_i1, c_i2, c_i3 = st.columns(3)
            c_i1.metric("Budget Residuo", f"{inspect_opp['budget']} cr")
            c_i2.metric("Slot Completati", f"{TOTAL_SLOTS - inspect_opp['slots_left']} / {TOTAL_SLOTS}")
            p_max_opp = inspect_opp['budget'] - (inspect_opp['slots_left'] - 1) if inspect_opp['slots_left'] > 0 else 0
            c_i3.metric("Offerta Max (Pmax)", f"{p_max_opp} cr")
            
            st.write("")
            col_rp, col_rd, col_rc, col_ra = st.columns(4)
            with col_rp:
                st.markdown("**Portieri (P)**")
                for pl in inspect_opp['roster']['P']:
                    st.markdown(f"<img src='{get_team_logo_url(pl['team'])}' width='16' style='vertical-align: middle; margin-right: 4px;'> {pl['name']} - **{pl['price']} cr**", unsafe_allow_html=True)
            with col_rd:
                st.markdown("**Difensori (D)**")
                for pl in inspect_opp['roster']['D']:
                    st.markdown(f"<img src='{get_team_logo_url(pl['team'])}' width='16' style='vertical-align: middle; margin-right: 4px;'> {pl['name']} - **{pl['price']} cr**", unsafe_allow_html=True)
            with col_rc:
                st.markdown("**Centrocampisti (C)**")
                for pl in inspect_opp['roster']['C']:
                    st.markdown(f"<img src='{get_team_logo_url(pl['team'])}' width='16' style='vertical-align: middle; margin-right: 4px;'> {pl['name']} - **{pl['price']} cr**", unsafe_allow_html=True)
            with col_ra:
                st.markdown("**Attaccanti (A)**")
                for pl in inspect_opp['roster']['A']:
                    st.markdown(f"<img src='{get_team_logo_url(pl['team'])}' width='16' style='vertical-align: middle; margin-right: 4px;'> {pl['name']} - **{pl['price']} cr**", unsafe_allow_html=True)

        st.markdown("---")
        with st.expander("Mercato di Riparazione (Svincoli & Penali)", expanded=False):
            st.caption("Gestisci gli svincoli per la tua squadra o per gli avversari. I crediti verranno ricalcolati automaticamente.")
            
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
                
                st.write(f"Prezzo di acquisto originale: **{orig_price} cr**")

                drop_mode = st.radio("Regola di Recupero Crediti:", 
                                     ["Recupero 100% (Intero Prezzo)", "Recupero 50% (Metà Prezzo)", "Recupero 1 Credito", "Personalizzato"], horizontal=True)
                
                custom_refund = 0
                if "Personalizzato" in drop_mode:
                    custom_refund = st.number_input("Crediti da rimborsare:", min_value=0, max_value=orig_price, value=0)

                if st.button(f"Conferma Svincolo di {sel_drop_player}", type="primary"):
                    if "100%" in drop_mode:
                        refund = orig_price
                    elif "50%" in drop_mode:
                        refund = int(round(orig_price / 2))
                    elif "1 Credito" in drop_mode:
                        refund = 1
                    else:
                        refund = custom_refund

                    if selected_drop_team == "La Mia Squadra":
                        st.session_state.my_roster = [p for p in st.session_state.my_roster if p['name'] != sel_drop_player]
                        penalty = refund - orig_price
                        st.session_state.budget_adjustments += penalty
                    else:
                        for r_code in ['P', 'D', 'C', 'A']:
                            opp_obj['roster'][r_code] = [p for p in opp_obj['roster'][r_code] if p['name'] != sel_drop_player]
                        opp_obj['budget'] += refund
                        opp_obj['slots_left'] += 1

                    if sel_drop_player in st.session_state.purchased_registry:
                        del st.session_state.purchased_registry[sel_drop_player]

                    st.session_state.history.append({
                        'buyer': selected_drop_team, 'name': sel_drop_player, 'team': dropped_p['team'],
                        'role': dropped_p.get('role', 'Sconosciuto'), 'price': -refund, 'action': 'SVINCOLO', 'penalty': penalty if selected_drop_team == "La Mia Squadra" else 0
                    })

                    save_state_to_disk()
                    st.success("Svincolo eseguito!")
                    st.rerun()
            else:
                st.info(f"Nessun giocatore attualmente presente nella rosa di {selected_drop_team}.")

    with t_track:
        st.subheader("Quadro Generale Avversari & Potere d'Acquisto")
        
        # ==========================================
        # ✏️ SEZIONE: RINOMINA E PROFILI AVVERSARI
        # ==========================================
        with st.expander("✏️ Personalizza Nomi e Profili IA", expanded=True):
            st.caption("Modifica i nomi dei tuoi avversari o la loro personalità. Clicca su Salva in fondo per applicare le modifiche.")
            
            new_names = {}
            new_profs = {}
            
            cols = st.columns(3)
            for i, old_name in enumerate(list(st.session_state.opponents.keys())):
                with cols[i % 3]:
                    st.markdown(f"**Slot {i+1}**")
                    # Campi senza form, così si legano direttamente all'interfaccia
                    new_names[old_name] = st.text_input("Nome:", value=old_name, key=f"name_input_{i}")
                    
                    curr_p = st.session_state.opponents[old_name].get('profile', 'Equilibrato')
                    try: prof_idx = BOT_PROFILES.index(curr_p)
                    except ValueError: prof_idx = 4
                    
                    new_profs[old_name] = st.selectbox("Personalità:", options=BOT_PROFILES, index=prof_idx, key=f"prof_input_{i}")
                    st.write("---")
            
            if st.button("💾 Salva Modifiche Avversari", type="primary", use_container_width=True):
                changed = False
                
                # 1. Aggiorna i Profili IA forzatamente
                for old_name in list(st.session_state.opponents.keys()):
                    if st.session_state.opponents[old_name].get('profile') != new_profs[old_name]:
                        st.session_state.opponents[old_name]['profile'] = new_profs[old_name]
                        changed = True
                        
                # 2. Aggiorna i Nomi
                for old_name in list(st.session_state.opponents.keys()):
                    new_name = new_names[old_name].strip()
                    if new_name and new_name != old_name and new_name != "La Mia Squadra":
                        if new_name not in st.session_state.opponents:
                            st.session_state.opponents[new_name] = st.session_state.opponents.pop(old_name)
                            st.session_state.opponents[new_name]['name'] = new_name
                            
                            # Aggiorna lo storico e la memoria per non far crashare nulla
                            for p, (b, pr) in st.session_state.purchased_registry.items():
                                if b == old_name: 
                                    st.session_state.purchased_registry[p] = (new_name, pr)
                                    
                            for a in st.session_state.history:
                                if a.get('buyer') == old_name: 
                                    a['buyer'] = new_name
                            changed = True
                            
                if changed:
                    save_state_to_disk()
                    st.rerun()
        # ==========================================

        # TABELLA TRACKER AVVERSARI
        opp_summary = []
        for k, v in st.session_state.opponents.items():
            p_max = v['budget'] - (v['slots_left'] - 1) if v['slots_left'] > 0 else 0
            opp_summary.append({
                "Squadra Rivale": v['name'],
                "Profilo IA": v.get('profile', 'Equilibrato'),
                "Budget Residuo": f"{v['budget']} cr",
                "Slot Mancanti": f"{v['slots_left']} / {TOTAL_SLOTS}",
                "Max Bid Possibile (Pmax)": p_max,
                "P": f"{len(v['roster']['P'])}/3",
                "D": f"{len(v['roster']['D'])}/8",
                "C": f"{len(v['roster']['C'])}/8",
                "A": f"{len(v['roster']['A'])}/6",
                "Livello Minaccia": "🔴 ALTISSIMA" if p_max > 120 else ("🟡 MEDIA" if p_max > 45 else "🟢 INNOCUO")
            })
            
        if opp_summary:
            st.dataframe(pd.DataFrame(opp_summary).sort_values(by="Max Bid Possibile (Pmax)", ascending=False), use_container_width=True)
            
    with t_baro:
        st.subheader("Barometro Inflazione & Liquidità Lega")
        
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
        b4.metric("Fase di Mercato", "🔴 Deflazione" if deflation_on else "🟢 Fase Calda")

        st.markdown("---")
        if deflation_on:
            st.error("ALLERTA DEFLAZIONE: I rivali non hanno più liquidità. Ora puoi aggiudicarti tutti i tuoi 4°/5° slot a prezzo di saldo!")
        else:
            st.info("MERCATO IN EQUILIBRIO: Mantieni la disciplina sui tetti Stop-Loss e fai sfogare i rivali sui giocatori non prioritari.")

# ------------------------------------------------------------------------------
# MACRO AREA 4: DATI & EXPORT
# ------------------------------------------------------------------------------
with macro_tabs[3]:
    t_macro, t_exp = st.tabs(["Macroeconomia & Trend", "Esportazione & Report Finale"])
    
    with t_macro:
        st.subheader("Analisi Macroeconomica e Tattica (Stagione 2026/27)")
        
        st.markdown("#### Modello Comportamentale vs. Rischio Calcolato")
        st.write("- I fantallenatori tendono a sovrappesare l'attacco, spendendo il 41.9% del budget per un reparto che ha un tasso di conferma di appena il 33%.")
        st.write("- Il centrocampo è il reparto più prevedibile (62% di conferma).")
        st.write("- Il modello a rischio suggerisce di investire fino al 40-43% del budget per i centrocampisti.")
        st.write("- Nelle leghe con il Trequartista, questo ruolo assorbe il 16.1% del budget.")
        
        st.markdown("#### Modificatore di Difesa e Nuove Tattiche")
        st.write("- L'Anomalia Dimarco: valutato 64,05 cr, agisce da trequartista occulto nel 3-5-2 di Chivu.")
        st.write("- L'Effetto Gasperini a Roma trasforma Mancini e Wesley in esterni d'assalto.")
        st.write("- Nel Milan, il paradigma Amorim esalta Pavlovic come braccetto nel 3-4-2-1.")
        
        st.markdown("#### Trappole in Attacco")
        st.write("- Hojlund (125.13 cr) è penalizzato dal modulo difensivo di Allegri ed è considerato una trappola letale.")
        st.write("- Kean (124.26 cr) ha un rischio di fallimento estremo ed è over-priced rispetto ai suoi limiti algoritmici.")

    with t_exp:
        st.subheader("Esportazione Dati Rosa")
        
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
                label="Scarica Report (Excel)",
                data=output_excel.getvalue(),
                file_name=f"FantaAsta_2026_27_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

        with col_ex2:
            json_backup_str = json.dumps({
                "my_roster": st.session_state.my_roster,
                "opponents": st.session_state.opponents,
                "purchased_registry": st.session_state.purchased_registry,
                "history": st.session_state.history,
                "budget_adjustments": st.session_state.budget_adjustments
            }, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="Scarica Backup (JSON)",
                data=json_backup_str,
                file_name="fanta_auction_backup.json",
                mime="application/json",
                use_container_width=True
            )
