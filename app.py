import streamlit as st
import pandas as pd
import random

# Nastavení stránky
st.set_page_config(page_title="Letecký Radiotelefonista - Kvíz", layout="wide")

# Načtení dat z CSV
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("otazky.csv")
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        st.error("Soubor 'otazky.csv' nebyl nalezen. Ujistěte se, že se jmenuje přesně 'otazky.csv' a je ve stejné složce.")
        return None
    except Exception as e:
        st.error(f"Chyba při načítání souboru: {e}")
        return None

df_all = load_data()

if df_all is not None:
    # --- HORNÍ LIŠTA S VÝBĚREM REŽIMŮ ---
    col_title, col_mode = st.columns([2, 1])
    with col_title:
        st.title("✈️ Příprava na zkoušky radiotelefonisty")
    with col_mode:
        mod = st.selectbox(
            "Vyberte režim studia:",
            ["Učení (Všechny otázky + nápověda)", "Čistý test (Ostrá zkouška)"]
        )

    # --- BOČNÍ PANEL S KATEGORIEMI ---
    st.sidebar.header("📂 Výběr kategorie")
    kat_vyber = st.sidebar.radio(
        "Zvolte okruh:",
        ["Radiokomunikační předpisy", "Radiokomunikační provoz", "Elektrotechnika a radiotechnika"]
    )

    # Detekce prvního sloupce s kategoriemi
    sloupec_kategorie = 'Unnamed: 0' if 'Unnamed: 0' in df_all.columns else df_all.columns[0]

    # Vyfiltrování otázek podle zvoleného okruhu
    df_kategorie = df_all[df_all[sloupec_kategorie].str.strip() == kat_vyber]
    
    if kat_vyber == "Radiokomunikační předpisy":
        pocet_do_testu = 20
    elif kat_vyber == "Radiokomunikační provoz":
        pocet_do_testu = 40
    else:
        pocet_do_testu = 20

    # Inicializace stavu relace (Session State)
    state_key = f"q_{kat_vyber}_{mod}"
    if state_key not in st.session_state:
        seznam = df_kategorie.to_dict('records')
        
        if mod == "Čistý test (Ostrá zkouška)":
            random.shuffle(seznam)
            seznam = seznam[:min(pocet_do_testu, len(seznam))]
            
        for q in seznam:
            odpovedi = list(set([str(q['Správná odpověď']), str(q['Distraktor 1']), str(q['Distraktor 2']), str(q['Distraktor 3'])]))
            random.shuffle(odpovedi)
            q['_moznosti'] = odpovedi
            
        st.session_state[state_key] = seznam
        st.session_state[f"a_{kat_vyber}_{mod}"] = {}
        st.session_state[f"sub_{kat_vyber}_{mod}"] = False

    aktualni_otazky = st.session_state[state_key]
    answers_dict = st.session_state[f"a_{kat_vyber}_{mod}"]
    test_odeslan = st.session_state[f"sub_{kat_vyber}_{mod}"]

    # --- ZOBRAZENÍ CELKOVÉHO VÝSLEDKU NAHOŘE ---
    if mod == "Čistý test (Ostrá zkouška)" and test_odeslan:
        spravne = sum(1 for idx, q in enumerate(aktualni_otazky) if answers_dict.get(idx) == str(q['Správná odpověď']))
        celkem = len(aktualni_otazky)
        procenta = (spravne / celkem) * 100 if celkem > 0 else 0
        prospel = procenta >= 90.0

        if prospel:
            st.success(f"🎉 USPĚL ({spravne}/{celkem}) — Vaše úspěšnost je {procenta:.1f} %")
        else:
            st.error(f"❌ NEUSPĚL ({spravne}/{celkem}) — Vaše úspěšnost je {procenta:.1f} % (Pro úspěch je potřeba aspoň 90 %)")

    # --- VÝPIS OTÁZEK ---
    st.subheader(f"{kat_vyber} ({len(aktualni_otazky)} otázek)")
    st.write("---")

    for idx, q in enumerate(aktualni_otazky):
        st.markdown(f"**{idx + 1}. {q['Otázka']}**")
        
        stary_vyber = q['_moznosti'].index(answers_dict[idx]) if idx in answers_dict else None
        
        # Zobrazení odpovědí (v Ostrém testu se po odeslání zamknou pro úpravy)
        user_ans = st.radio(
            "Odpověď:", q['_moznosti'], 
            key=f"ans_{kat_vyber}_{idx}_{mod}", 
            index=stary_vyber, 
            disabled=(mod == "Čistý test (Ostrá zkouška)" and test_odeslan)
        )
        
        if user_ans and not test_odeslan:
            answers_dict[idx] = user_ans

        # REŽIM UČENÍ: okamžité vyhodnocení přímo pod výběrem
        if mod == "Učení (Všechny otázky + nápověda)" and user_ans:
            if user_ans == str(q['Správná odpověď']):
                st.success("🟢 Správně")
            else:
                st.error(f"🔴 Chyba. Správná odpověď je: {q['Správná odpověď']}")
            if pd.notna(q.get('Vysvětlivky a poznámky')) and str(q['Vysvětlivky a poznámky']).strip() != "":
                st.info(f"💡 {q['Vysvětlivky a poznámky']}")

        # REŽIM ČISTÝ TEST: zabudování vyhodnocení přímo pod odpovědi po odeslání
        if mod == "Čistý test (Ostrá zkouška)" and test_odeslan:
            tvoje = answers_dict.get(idx, "Nezodpovězeno")
            spravna = str(q['Správná odpověď'])
            
            if tvoje == spravna:
                st.success(f"🟢 Vaše odpověď byla SPRÁVNÁ: {tvoje}")
            else:
                st.error(f"🔴 CHYBA. Vybrali jste: {tvoje} | Správná odpověď je: {spravna}")
                
            if pd.notna(q.get('Vysvětlivky a poznámky')) and str(q['Vysvětlivky a poznámky']).strip() != "":
                st.info(f"💡 {q['Vysvětlivky a poznámky']}")

        st.write("---")

    # Tlačítko pro odeslání testu na konci
    if mod == "Čistý test (Ostrá zkouška)" and not test_odeslan:
        if st.button("📊 Odeslat a vyhodnotit test", type="primary"):
            st.session_state[f"sub_{kat_vyber}_{mod}"] = True
            st.rerun()

    # Tlačítko pro restartování testu (zobrazí se po odeslání)
    if test_odeslan:
        if st.button("🔄 Spustit nový test"):
            del st.session_state[state_key]
            del st.session_state[f"a_{kat_vyber}_{mod}"]
            st.session_state[f"sub_{kat_vyber}_{mod}"] = False
            st.rerun()