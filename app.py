import streamlit as st
import pandas as pd
import io

# إعدادات الواجهة
st.set_page_config(page_title="Ordo Estates - Système Intégré", layout="wide")

# --- محرك الحسابات ---
def calcul_v_semelle(A, B, a, b, e, h_p):
    V1 = A * B * e
    V2 = (1/6) * h_p * (B * (2*A + a) + b * (2*a + A))
    return float(V1 + V2)

st.title("🏗️ Ordo Estates : اللوجيسيال المتكامل للميتري")

# --- القائمة الجانبية لرفع الملفات (لبلانات والميتري) ---
st.sidebar.header("📁 مركز رفع الملفات")
# هنا فين كدخل لبلانات (PDF أو صور)
uploaded_plans = st.sidebar.file_uploader("🖼️ ارفع لبلانات (PDF/Images)", accept_multiple_files=True)
# هنا فين كدخل الميتري العادي إلا كان عندك فـ Excel
uploaded_metre_ex = st.sidebar.file_uploader("📊 ارفع الميتري العادي (Excel)", type="xlsx")
# هنا فين كترفع البوردورو باش يتربط
uploaded_bp = st.sidebar.file_uploader("📝 ارفع البوردورو النهائي", type="xlsx")

# --- الأقسام الرئيسية ---
tabs = st.tabs(["📏 حساب السوميلات", "🏗️ الميتري العادي", "⛓️ حساب الحديد", "📊 البوردورو النهائي"])

# 1. قسم السوميلات
with tabs[0]:
    st.subheader("حساب خرسانة السوميلات (V1 + V2)")
    df_s = st.data_editor(pd.DataFrame({
        'Dés.': ['S1'], 'Nb': [1], 'A': [1.10], 'B': [1.10],
        'a': [0.25], 'b': [0.25], 'e': [0.20], 'h_prime': [0.15]
    }), num_rows="dynamic", key="s_edit")
    
    if st.button("احسب السوميلات"):
        df_s['Total_V'] = df_s.apply(lambda x: calcul_v_semelle(x['A'], x['B'], x['a'], x['b'], x['e'], x['h_prime']), axis=1) * df_s['Nb']
        st.session_state['v_semelle'] = df_s['Total_V'].sum()
        st.dataframe(df_s)
        st.success(f"مجموع السوميلات: {st.session_state['v_semelle']:.3f} m³")

# 2. قسم الميتري العادي (البيطون، الحفر، الخ)
with tabs[1]:
    st.subheader("الميتري العادي (Métré Classique)")
    st.write("تقدر تدخل هنا أي أشغال أخرى (Terrassement, Béton armé, etc.)")
    df_m = st.data_editor(pd.DataFrame({
        'N° Article': ['1.01', '1.02'],
        'Désignation': ['Terrassement', 'Béton de propreté'],
        'Unité': ['m³', 'm³'],
        'Nombre': [1.0, 1.0],
        'Dim 1': [10.0, 5.0],
        'Dim 2': [10.0, 5.0],
        'Dim 3': [0.5, 0.1]
    }), num_rows="dynamic", key="m_edit")
    
    df_m['Total'] = df_m['Nombre'] * df_m['Dim 1'] * df_m['Dim 2'] * df_m['Dim 3']
    st.dataframe(df_m)
    st.session_state['v_metre'] = df_m['Total'].sum()

# 3. قسم الحديد
with tabs[2]:
    st.subheader("حساب وزن الحديد (Acier)")
    acier_df = st.data_editor(pd.DataFrame({
        'Ouvrage': ['Semelles'], 'Ø': [12], 'L.totale (ml)': [100.0]
    }), num_rows="dynamic", key="a_edit")
    
    ratios = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21, 16: 1.58, 20: 2.47}
    if st.button("احسب الحديد"):
        acier_df['Poids (Kg)'] = acier_df.apply(lambda x: x['L.totale (ml)'] * ratios.get(x['Ø'], 0), axis=1)
        st.session_state['poids_total'] = acier_df['Poids (Kg)'].sum()
        st.dataframe(acier_df)

# 4. الربط بالبوردورو
with tabs[3]:
    st.subheader("الربط النهائي بالبوردورو")
    if uploaded_bp:
        df_bp = pd.read_excel(uploaded_bp)
        if st.button("دمج كاع الحسابات"):
            # ربط السوميلات بأرتيكل 1.06 مثلا
            if 'v_semelle' in st.session_state:
                df_bp.loc[df_bp['N°'] == '1.06', 'Quantités calculées'] = st.session_state['v_semelle']
            
            # ربط الحديد بأرتيكل 2.02 مثلا
            if 'poids_total' in st.session_state:
                df_bp.loc[df_bp['N°'] == '2.02', 'Quantités calculées'] = st.session_state['poids_total']
            
            st.dataframe(df_bp)
            
            # زر التحميل
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df_bp.to_excel(w, index=False)
            st.download_button("📥 تحميل البوردورو المحدث", buf.getvalue(), "Bordereau_Ordo.xlsx")
    else:
        st.info("ارفع ملف البوردورو من القائمة الجانبية باش تربط الحسابات.")
