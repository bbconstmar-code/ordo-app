import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from PIL import Image

st.set_page_config(page_title="Ordo Estates - Fusion Métré", layout="wide")

st.title("🏗️ Ordo Estates : إدخال البوردورو في الميتري")

# --- القائمة الجانبية ---
st.sidebar.header("📁 الملفات")
uploaded_pdf = st.sidebar.file_uploader("🖼️ المخططات (PDF)", type="pdf")
uploaded_bp = st.sidebar.file_uploader("📊 البوردورو (Excel)", type="xlsx")

# عرض لبلان PDF للتأكد من القياسات
if uploaded_pdf:
    pdf_data = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page_num = st.sidebar.number_input("الصفحة", min_value=1, max_value=len(doc), step=1) - 1
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    st.sidebar.image(img, use_column_width=True)

# --- الجداول الأساسية للميتري ---
tabs = st.tabs(["📝 الميتري العام", "📐 السوميلات", "⛓️ الحديد", "⚙️ عملية الدمج"])

with tabs[0]:
    st.subheader("إدخال الميتري (القياسات العادية)")
    # هذا الجدول هو اللي كيمثل "الميتري" اللي غيدخل في البوردورو
    df_metre = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.01', '1.02', '1.03', '1.04', '1.05'],
        'Désignation': ['Terrassement', 'Fouille en masse', 'Fouille en rigole', 'Béton de propreté', 'Béton armé'],
        'Nb': [1.0] * 5, 'L': [0.0] * 5, 'l': [0.0] * 5, 'h': [0.0] * 5
    }), num_rows="dynamic", key="m_v9")
    df_metre['Total'] = df_metre['Nb'] * df_metre['L'] * df_metre['l'] * df_metre['h']
    st.dataframe(df_metre)

with tabs[1]:
    # حساب السوميلات بنفس الطريقة
    st.subheader("ميتري السوميلات (V1 + V2)")
    df_s = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.06'], 'Nb': [1], 'A': [1.1], 'B': [1.1], 'a': [0.25], 'b': [0.25], 'e': [0.2], 'h_p': [0.15]
    }), num_rows="dynamic", key="s_v9")
    def calc_v(r): return (r.A*r.B*r.e) + (1/6)*r.h_p*(r.B*(2*r.A+r.a)+r.b*(2*r.a+r.A))
    if st.button("حساب حجم السوميلات"):
        df_s['Total'] = df_s.apply(calc_v, axis=1) * df_s['Nb']
        st.session_state['res_s'] = df_s[['N° Art.', 'Total']]
        st.dataframe(df_s)

with tabs[2]:
    st.subheader("ميتري الحديد")
    df_a = st.data_editor(pd.DataFrame({'N° Art.': ['2.01'], 'Ø': [12], 'L.tot': [100.0]}), num_rows="dynamic")
    ratios = {6:0.222, 8:0.395, 10:0.617, 12:0.888, 14:1.21, 16:1.58, 20:2.47}
    if st.button("حساب الوزن"):
        df_a['Total'] = df_a['L.tot'] * df_a.apply(lambda x: ratios.get(x['Ø'], 0), axis=1)
        st.session_state['res_a'] = df_a[['N° Art.', 'Total']]
        st.dataframe(df_a)

# --- أهم مرحلة: دمج الميتري في البوردورو ---
with tabs[3]:
    st.subheader("الدمج النهائي (Bordereau + Métré)")
    if uploaded_bp:
        df_bp = pd.read_excel(uploaded_bp)
        
        st.info("اختار الأعمدة المناسبة من ملف Excel اللي رفعتيه")
        c1, c2 = st.columns(2)
        with c1:
            col_n = st.selectbox("عمود رقم الأرتيكل (N°):", df_bp.columns)
        with c2:
            col_q = st.selectbox("عمود الكمية (Quantité) اللي غايتعمر:", df_bp.columns)
            
        if st.button("بدء عملية الدمج"):
            # تجهيز البيانات
            df_bp[col_n] = df_bp[col_n].astype(str).str.strip()
            
            # دمج الميتري العادي
            for _, row in df_metre.iterrows():
                if row['Total'] > 0:
                    df_bp.loc[df_bp[col_n] == str(row['N° Art.']), col_q] = row['Total']
            
            # دمج السوميلات والحديد
            if 'res_s' in st.session_state:
                for _, row in st.session_state['res_s'].iterrows():
                    df_bp.loc[df_bp[col_n] == str(row['N° Art.']), col_q] = row['Total']
            
            if 'res_a' in st.session_state:
                for _, row in st.session_state['res_a'].iterrows():
                    df_bp.loc[df_bp[col_n] == str(row['N° Art.']), col_q] = row['Total']
            
            st.success("✅ تم إدخال الميتري في البوردورو بنجاح!")
            st.dataframe(df_bp)
            
            # تصدير الملف
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df_bp.to_excel(w, index=False)
            st.download_button("📥 تحميل البوردورو المكتمل", buf.getvalue(), "Bordereau_Final_Ordo.xlsx")
    else:
        st.warning("يرجى رفع ملف البوردورو (Excel) من القائمة الجانبية لبدء الدمج.")
