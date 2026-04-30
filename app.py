import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from PIL import Image

st.set_page_config(page_title="Ordo Estates V8 - Flexible Mapping", layout="wide")

# محرك الحسابات
def calcul_v_semelle(A, B, a, b, e, h_p):
    return float((A * B * e) + (1/6) * h_p * (B * (2*A + a) + b * (2*a + A)))

st.title("🏗️ Ordo Estates : الميتري الذكي (نسخة مرنة)")

# --- Sidebar ---
st.sidebar.header("📁 إدارة الملفات")
uploaded_pdf = st.sidebar.file_uploader("🖼️ ارفع المخططات (PDF)", type="pdf")
uploaded_bp = st.sidebar.file_uploader("📊 ارفع البوردورو (Excel)", type="xlsx")

if uploaded_pdf:
    st.sidebar.markdown("---")
    pdf_data = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page_num = st.sidebar.number_input("الصفحة", min_value=1, max_value=len(doc), step=1) - 1
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    st.sidebar.image(img, use_column_width=True)

tabs = st.tabs(["📏 السوميلات", "🏗️ الميتري العادي", "⛓️ الحديد", "📊 الربط النهائي"])

# (أقسام الحسابات كتبقى كما هي)
with tabs[0]:
    df_s = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.06'], 'Désignation': ['S1'], 'Nb': [1], 'A': [1.10], 'B': [1.10], 'a': [0.25], 'b': [0.25], 'e': [0.20], 'h_prime': [0.15]
    }), num_rows="dynamic", key="s_v8")
    if st.button("احسب السوميلات"):
        df_s['Total_V'] = df_s.apply(lambda x: calcul_v_semelle(x['A'], x['B'], x['a'], x['b'], x['e'], x['h_prime']), axis=1) * df_s['Nb']
        st.session_state['res_s'] = df_s[['N° Art.', 'Total_V']]
        st.dataframe(df_s)

with tabs[1]:
    df_m = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.01', '1.02'], 'Désignation': ['Terrassement', 'Fouille'],
        'Nb': [1.0, 1.0], 'L': [10.0, 5.0], 'l': [10.0, 5.0], 'h': [0.5, 0.8]
    }), num_rows="dynamic", key="m_v8")
    df_m['Total'] = df_m['Nb'] * df_m['L'] * df_m['l'] * df_m['h']
    st.session_state['res_m'] = df_m[['N° Art.', 'Total']]
    st.dataframe(df_m)

with tabs[2]:
    acier_df = st.data_editor(pd.DataFrame({'N° Art.': ['2.02'], 'Ø': [12], 'L.totale (ml)': [100.0]}), num_rows="dynamic")
    ratios = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21, 16: 1.58, 20: 2.47}
    if st.button("احسب الحديد"):
        acier_df['Poids (Kg)'] = acier_df.apply(lambda x: x['L.totale (ml)'] * ratios.get(x['Ø'], 0), axis=1)
        st.session_state['res_a'] = acier_df[['N° Art.', 'Poids (Kg)']]
        st.dataframe(acier_df)

# --- قسم الربط المطور ---
with tabs[3]:
    if uploaded_bp:
        df_bp = pd.read_excel(uploaded_bp)
        st.write("✅ تم تحميل الملف. دابا اختار السمية ديال الأعمدة:")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_n_col = st.selectbox("اختار العمود اللي فيه رقم الأرتيكل (N°):", df_bp.columns)
        with col2:
            selected_q_col = st.selectbox("اختار العمود فين بغيتي تحط الحساب (Quantité):", df_bp.columns)
            
        if st.button("تحديث وتحميل البوردورو"):
            df_bp[selected_n_col] = df_bp[selected_n_col].astype(str).str.strip()
            
            all_res = []
            if 'res_s' in st.session_state: all_res.append(st.session_state['res_s'].rename(columns={'N° Art.': selected_n_col, 'Total_V': 'Q'}))
            if 'res_m' in st.session_state: all_res.append(st.session_state['res_m'].rename(columns={'N° Art.': selected_n_col, 'Total': 'Q'}))
            if 'res_a' in st.session_state: all_res.append(st.session_state['res_a'].rename(columns={'N° Art.': selected_n_col, 'Poids (Kg)': 'Q'}))
            
            if all_res:
                final_data = pd.concat(all_res)
                for _, row in final_data.iterrows():
                    df_bp.loc[df_bp[selected_n_col] == str(row[selected_n_col]), selected_q_col] = row['Q']
                
                st.success("تم التحديث!")
                st.dataframe(df_bp)
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as w:
                    df_bp.to_excel(w, index=False)
                st.download_button("📥 تحميل الملف المحدث", buf.getvalue(), "Bordereau_Ordo_Final.xlsx")
    else:
        st.warning("👈 ارفع ملف البوردورو (Excel) أولاً")
