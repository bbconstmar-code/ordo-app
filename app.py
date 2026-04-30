import streamlit as st
import pandas as pd
import io
from PIL import Image

st.set_page_config(page_title="Ordo Estates - Plans & Métré", layout="wide")

# محرك الحسابات
def calcul_v_semelle(A, B, a, b, e, h_p):
    return float((A * B * e) + (1/6) * h_p * (B * (2*A + a) + b * (2*a + A)))

st.title("🏗️ Ordo Estates : Gestionnaire de Plans et Métré")

# --- Sidebar: لبلانات والبوردورو ---
st.sidebar.header("📁 الملفات والرسومات")
uploaded_plans = st.sidebar.file_uploader("🖼️ ارفع المخططات (Images)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
uploaded_bp = st.sidebar.file_uploader("📊 ارفع البوردورو (Excel)", type="xlsx")

# عرض لبلانات في الجنب باش تنقل منهم
if uploaded_plans:
    st.sidebar.markdown("---")
    st.sidebar.subheader("👁️ معاينة المخططات")
    for plan in uploaded_plans:
        img = Image.open(plan)
        st.sidebar.image(img, caption=plan.name, use_column_width=True)

tabs = st.tabs(["📏 حساب السوميلات", "🏗️ الميتري العادي", "📊 الربط النهائي"])

# 1. السوميلات
with tabs[0]:
    st.info("💡 انقل الأرقام من لبلان اللي باين عندك على ليمن")
    df_s = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.06'], 'Désignation': ['S1'], 'Nb': [1], 'A': [1.10], 'B': [1.10], 'a': [0.25], 'b': [0.25], 'e': [0.20], 'h_prime': [0.15]
    }), num_rows="dynamic", key="s_v6")
    if st.button("احسب السوميلات"):
        df_s['Total_V'] = df_s.apply(lambda x: calcul_v_semelle(x['A'], x['B'], x['a'], x['b'], x['e'], x['h_prime']), axis=1) * df_s['Nb']
        st.session_state['v_semelle_v6'] = df_s[['N° Art.', 'Total_V']]
        st.dataframe(df_s)

# 2. الميتري العادي
with tabs[1]:
    df_m = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.01', '1.02'], 'Désignation': ['Terrassement', 'Fouilles'],
        'Nb': [1.0, 1.0], 'L': [10.0, 5.0], 'l': [10.0, 5.0], 'h': [0.5, 0.8]
    }), num_rows="dynamic", key="m_v6")
    df_m['Total'] = df_m['Nb'] * df_m['L'] * df_m['l'] * df_m['h']
    st.session_state['v_metre_v6'] = df_m[['N° Art.', 'Total']]
    st.dataframe(df_m)

# 3. الربط النهائي
with tabs[2]:
    if uploaded_bp:
        df_bp = pd.read_excel(uploaded_bp)
        col_n = [c for c in df_bp.columns if 'n°' in str(c).lower() or 'num' in str(c).lower()]
        
        if col_n and st.button("تحديث وتحميل البوردورو"):
            c_name = col_n[0]
            df_bp[c_name] = df_bp[c_name].astype(str).str.strip()
            
            # تجميع البيانات
            all_results = []
            if 'v_semelle_v6' in st.session_state: all_results.append(st.session_state['v_semelle_v6'].rename(columns={'N° Art.': c_name, 'Total_V': 'Q'}))
            if 'v_metre_v6' in st.session_state: all_results.append(st.session_state['v_metre_v6'].rename(columns={'N° Art.': c_name, 'Total': 'Q'}))
            
            if all_results:
                final_df = pd.concat(all_results)
                for _, row in final_df.iterrows():
                    df_bp.loc[df_bp[c_name] == str(row[c_name]), 'Quantités calculées'] = row['Q']
                
                st.dataframe(df_bp)
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as w:
                    df_bp.to_excel(w, index=False)
                st.download_button("📥 تحميل البوردورو المحدث", buf.getvalue(), "Bordereau_Ordo_V6.xlsx")
    else:
        st.warning("ارفع البوردورو أولاً")
