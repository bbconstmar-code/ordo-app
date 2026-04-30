import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from PIL import Image

st.set_page_config(page_title="Ordo Estates V10 - Auto-Métré", layout="wide")

st.title("🏗️ Ordo Estates : الميتري الذكي المستخرج من البوردورو")

# --- القائمة الجانبية ---
st.sidebar.header("📁 إدارة الملفات")
uploaded_pdf = st.sidebar.file_uploader("🖼️ المخططات (PDF)", type="pdf")
uploaded_bp = st.sidebar.file_uploader("📊 ارفع البوردورو (Excel)", type="xlsx")

# عرض لبلان PDF للمساعدة في النقل
if uploaded_pdf:
    pdf_data = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page_num = st.sidebar.number_input("الصفحة", min_value=1, max_value=len(doc), step=1) - 1
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    st.sidebar.image(img, use_column_width=True)

# --- منطق قراءة البوردورو وتحويله لميتري ---
if uploaded_bp:
    # قراءة الملف الأصلي
    df_original = pd.read_excel(uploaded_bp)
    
    st.info("⚠️ اختار أعمدة البوردورو باش نصاوب ليك جدول الميتري:")
    c1, c2, c3 = st.columns(3)
    with c1:
        col_n = st.selectbox("عمود الرقم (N°):", df_original.columns)
    with c2:
        col_des = st.selectbox("عمود البيان (Désignation):", df_original.columns)
    with c3:
        col_q = st.selectbox("عمود الكمية (Quantité):", df_original.columns)

    # تحويل البوردورو لجدول ميتري خاوي
    # كناخذو غير الأسطر اللي فيها الأرقام والبيانات
    df_template = df_original[[col_n, col_des]].copy()
    df_template.columns = ['N° Art.', 'Désignation']
    df_template = df_template.dropna(subset=['N° Art.']) # حيد الأسطر الخاوية

    # إضافة خانات الحساب (L, l, h, Nb)
    for col in ['Nb', 'L', 'l', 'h']:
        df_template[col] = 1.0

    st.subheader("📝 جدول الميتري المستخرج (عمر غير القياسات)")
    # مستخدم كيدخل غير القياسات هنا
    df_final_metre = st.data_editor(df_template, num_rows="always", key="editor_v10")
    
    # حساب المجموع لكل سطر
    df_final_metre['Total'] = df_final_metre['Nb'] * df_final_metre['L'] * df_final_metre['l'] * df_final_metre['h']

    st.markdown("---")
    
    if st.button("🚀 دمج الميتري في البوردورو الأصلي وتحميل الملف"):
        # عملية الدمج بناءً على رقم الأرتيكل
        df_output = df_original.copy()
        df_output[col_n] = df_output[col_n].astype(str).str.strip()
        
        for _, row in df_final_metre.iterrows():
            art_id = str(row['N° Art.']).strip()
            df_output.loc[df_output[col_n] == art_id, col_q] = row['Total']
        
        st.success("✅ تم تحديث البوردورو بجميع قياسات الميتري!")
        st.dataframe(df_output)
        
        # تحويل للتحميل
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df_output.to_excel(w, index=False)
        st.download_button("📥 تحميل البوردورو النهائي", buf.getvalue(), "Bordereau_Final_Ordo.xlsx")

else:
    st.warning("👈 ارفع ملف البوردورو (Excel) أولاً باش السيستيم يصاوب ليك جدول الميتري أوتوماتيكياً.")
