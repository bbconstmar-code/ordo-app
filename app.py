import streamlit as st
import pandas as pd
import io

# إعدادات الواجهة الاحترافية لـ Ordo Estates
st.set_page_config(page_title="Ordo Estates - Métré & Bordereau", layout="wide")

# --- محرك الحسابات (Semelles V1 + V2) ---
def calcul_v_semelle(A, B, a, b, e, h_p):
    V1 = A * B * e
    V2 = (1/6) * h_p * (B * (2*A + a) + b * (2*a + A))
    return float(V1 + V2)

st.title("🏗️ Ordo Estates : Système de Métré Intégré")
st.markdown("---")

# --- القائمة الجانبية (Sidebar) ---
st.sidebar.header("📁 إدارة الملفات")
uploaded_plans = st.sidebar.file_uploader("🖼️ ارفع المخططات (PDF/Images)", accept_multiple_files=True)
uploaded_bp = st.sidebar.file_uploader("📊 ارفع البوردورو الخاوي (Excel)", type="xlsx")

# --- الأقسام الرئيسية ---
tabs = st.tabs(["📏 حساب السوميلات", "🏗️ الميتري العادي (Métré)", "⛓️ حساب الحديد", "📊 الربط النهائي"])

# 1. قسم السوميلات (يرتبط عادة بـ 1.06)
with tabs[0]:
    st.subheader("حساب خرسانة السوميلات")
    df_s = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.06'], # الرقم الشائع لخرسانة الأساسات
        'Désignation': ['S1'], 'Nb': [1], 'A': [1.10], 'B': [1.10],
        'a': [0.25], 'b': [0.25], 'e': [0.20], 'h_prime': [0.15]
    }), num_rows="dynamic", key="s_edit")
    
    if st.button("احسب حجم السوميلات"):
        df_s['Total_V'] = df_s.apply(lambda x: calcul_v_semelle(x['A'], x['B'], x['a'], x['b'], x['e'], x['h_prime']), axis=1) * df_s['Nb']
        st.session_state['v_semelle_data'] = df_s[['N° Art.', 'Total_V']]
        st.dataframe(df_s)
        st.success(f"المجموع: {df_s['Total_V'].sum():.3f} m³")

# 2. قسم الميتري العادي (الحفر، الردم، الخ)
with tabs[1]:
    st.subheader("الميتري العادي (L x l x h)")
    # هنا مروان كيدخل أرقام الأرتيكلات كيف كاينين فالبوردورو
    df_m = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.01', '1.02'],
        'Désignation': ['Fouille en masse', 'Fouille en tranchée'],
        'Nb': [1.0, 1.0], 'L': [10.0, 5.0], 'l': [10.0, 5.0], 'h': [0.5, 0.8]
    }), num_rows="dynamic", key="m_edit")
    
    df_m['Total'] = df_m['Nb'] * df_m['L'] * df_m['l'] * df_m['h']
    st.session_state['v_metre_data'] = df_m[['N° Art.', 'Total']]
    st.dataframe(df_m)

# 3. قسم الحديد
with tabs[2]:
    st.subheader("حساب أوزان الحديد")
    acier_df = st.data_editor(pd.DataFrame({
        'N° Art.': ['2.02'], # مثال لرقم أرتيكل الحديد
        'Ouvrage': ['Semelles'], 'Ø': [12], 'L.totale (ml)': [100.0]
    }), num_rows="dynamic", key="a_edit")
    
    ratios = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21, 16: 1.58, 20: 2.47}
    if st.button("احسب وزن الحديد"):
        acier_df['Poids (Kg)'] = acier_df.apply(lambda x: x['L.totale (ml)'] * ratios.get(x['Ø'], 0), axis=1)
        st.session_state['v_acier_data'] = acier_df[['N° Art.', 'Poids (Kg)']]
        st.dataframe(acier_df)

# 4. الربط الذكي بالبوردورو (المرحلة الأخيرة)
with tabs[3]:
    st.subheader("تحديث البوردورو بالنتائج")
    if uploaded_bp:
        df_bp = pd.read_excel(uploaded_bp)
        # توحيد نوع البيانات في عمود الرقم لضمان الربط
        df_bp['N°'] = df_bp['N°'].astype(str)
        
        if st.button("تحديث كل الكميات (Par N° Article)"):
            # دمج نتائج السوميلات
            if 'v_semelle_data' in st.session_state:
                for _, row in st.session_state['v_semelle_data'].iterrows():
                    df_bp.loc[df_bp['N°'] == str(row['N° Art.']), 'Quantités calculées'] = row['Total_V']
            
            # دمج نتائج الميتري العادي
            if 'v_metre_data' in st.session_state:
                for _, row in st.session_state['v_metre_data'].iterrows():
                    df_bp.loc[df_bp['N°'] == str(row['N° Art.']), 'Quantités calculées'] = row['Total']
            
            # دمج نتائج الحديد
            if 'v_acier_data' in st.session_state:
                for _, row in st.session_state['v_acier_data'].iterrows():
                    df_bp.loc[df_bp['N°'] == str(row['N° Art.']), 'Quantités calculées'] = row['Poids (Kg)']

            st.success("✅ تم تحديث جميع الأرتيكلات بنجاح!")
            st.dataframe(df_bp)
            
            # تصدير الملف المحدث
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df_bp.to_excel(w, index=False)
            st.download_button("📥 تحميل البوردورو النهائي المحدث", buf.getvalue(), "Bordereau_Final_Ordo.xlsx")
    else:
        st.warning("يرجى رفع ملف البوردورو (Excel) من القائمة الجانبية أولاً.")
