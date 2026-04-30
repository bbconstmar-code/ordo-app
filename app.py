import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Ordo Estates V5", layout="wide")

# محرك الحسابات للسوميلات
def calcul_v_semelle(A, B, a, b, e, h_p):
    return float((A * B * e) + (1/6) * h_p * (B * (2*A + a) + b * (2*a + A)))

st.title("🏗️ Ordo Estates : Système de Métré Intégré")

# القائمة الجانبية
st.sidebar.header("📁 إدارة الملفات")
uploaded_bp = st.sidebar.file_uploader("ارفع البوردورو (Excel)", type="xlsx")

tabs = st.tabs(["📏 السوميلات", "🏗️ الميتري العادي", "⛓️ الحديد", "📊 الربط النهائي"])

# 1. السوميلات
with tabs[0]:
    df_s = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.06'], 'Désignation': ['S1'], 'Nb': [1], 'A': [1.10], 'B': [1.10], 'a': [0.25], 'b': [0.25], 'e': [0.20], 'h_prime': [0.15]
    }), num_rows="dynamic", key="s_edit")
    if st.button("احسب السوميلات"):
        df_s['Total_V'] = df_s.apply(lambda x: calcul_v_semelle(x['A'], x['B'], x['a'], x['b'], x['e'], x['h_prime']), axis=1) * df_s['Nb']
        st.session_state['v_semelle_data'] = df_s[['N° Art.', 'Total_V']]
        st.dataframe(df_s)

# 2. الميتري العادي (Terrassement, Fouilles...)
with tabs[1]:
    st.subheader("الميتري العادي (L x l x h)")
    df_m = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.01', '1.02', '1.03'],
        'Désignation': ['Terrassement', 'Fouille en masse', 'Fouille en rigole'],
        'Nb': [1.0, 1.0, 1.0], 'L': [10.0, 5.0, 20.0], 'l': [10.0, 5.0, 0.5], 'h': [0.5, 0.8, 1.0]
    }), num_rows="dynamic", key="m_edit")
    df_m['Total'] = df_m['Nb'] * df_m['L'] * df_m['l'] * df_m['h']
    st.session_state['v_metre_data'] = df_m[['N° Art.', 'Total']]
    st.dataframe(df_m)

# 3. الحديد
with tabs[2]:
    acier_df = st.data_editor(pd.DataFrame({
        'N° Art.': ['2.02'], 'Ouvrage': ['Semelles'], 'Ø': [12], 'L.totale (ml)': [100.0]
    }), num_rows="dynamic")
    ratios = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21, 16: 1.58, 20: 2.47}
    if st.button("احسب وزن الحديد"):
        acier_df['Poids (Kg)'] = acier_df.apply(lambda x: x['L.totale (ml)'] * ratios.get(x['Ø'], 0), axis=1)
        st.session_state['v_acier_data'] = acier_df[['N° Art.', 'Poids (Kg)']]
        st.dataframe(acier_df)

# 4. الربط النهائي (هنا فين كان المشكل)
with tabs[3]:
    if uploaded_bp:
        df_bp = pd.read_excel(uploaded_bp)
        # كود ذكي لتحديد عمود الأرقام كيفما كانت سميتو
        col_n = [c for c in df_bp.columns if 'n°' in str(c).lower() or 'num' in str(c).lower()]
        
        if col_n and st.button("تحديث البوردورو"):
            c_name = col_n[0]
            df_bp[c_name] = df_bp[c_name].astype(str).str.strip()
            
            # دمج كل الحسابات
            all_data = []
            if 'v_semelle_data' in st.session_state: all_data.append(st.session_state['v_semelle_data'].rename(columns={'N° Art.': c_name, 'Total_V': 'Q'}))
            if 'v_metre_data' in st.session_state: all_data.append(st.session_state['v_metre_data'].rename(columns={'N° Art.': c_name, 'Total': 'Q'}))
            if 'v_acier_data' in st.session_state: all_data.append(st.session_state['v_acier_data'].rename(columns={'N° Art.': c_name, 'Poids (Kg)': 'Q'}))
            
            if all_data:
                final_calc = pd.concat(all_data)
                for _, row in final_calc.iterrows():
                    df_bp.loc[df_bp[c_name] == str(row[c_name]), 'Quantités calculées'] = row['Q']
                
                st.success("✅ تم تحديث الكميات!")
                st.dataframe(df_bp)
                
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as w:
                    df_bp.to_excel(w, index=False)
                st.download_button("📥 تحميل الملف النهائي", buf.getvalue(), "Bordereau_Ordo_Final.xlsx")
    else:
        st.warning("ارفع ملف البوردورو من القائمة الجانبية")
