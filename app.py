import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from PIL import Image

st.set_page_config(page_title="Ordo Estates V7 - PDF & Excel", layout="wide")

# --- محرك الحسابات للسوميلات ---
def calcul_v_semelle(A, B, a, b, e, h_p):
    return float((A * B * e) + (1/6) * h_p * (B * (2*A + a) + b * (2*a + A)))

st.title("🏗️ Ordo Estates : الميتري المتكامل (PDF + Excel)")

# --- القائمة الجانبية (Sidebar) ---
st.sidebar.header("📁 إدارة الملفات")
uploaded_pdf = st.sidebar.file_uploader("🖼️ ارفع المخططات (PDF)", type="pdf")
uploaded_bp = st.sidebar.file_uploader("📊 ارفع البوردورو الخاوي (Excel)", type="xlsx")

# --- عرض الـ PDF في الجانب ---
if uploaded_pdf:
    st.sidebar.markdown("---")
    st.sidebar.subheader("👁️ معاينة المخطط PDF")
    
    # فتح الـ PDF وقراءة الصفحات
    pdf_data = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    
    page_num = st.sidebar.number_input("الصفحة", min_value=1, max_value=len(doc), step=1) - 1
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # جودة واضحة للمعاينة
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    st.sidebar.image(img, caption=f"الصفحة {page_num + 1}", use_column_width=True)

tabs = st.tabs(["📏 حساب السوميلات", "🏗️ الميتري العادي", "⛓️ حساب الحديد", "📊 الربط النهائي"])

# 1. السوميلات
with tabs[0]:
    st.info("💡 انقل الأرقام من صفحة الـ PDF اللي باينة عندك على ليمن")
    df_s = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.06'], 'Désignation': ['S1'], 'Nb': [1], 'A': [1.10], 'B': [1.10], 'a': [0.25], 'b': [0.25], 'e': [0.20], 'h_prime': [0.15]
    }), num_rows="dynamic", key="s_v7")
    
    if st.button("احسب السوميلات"):
        df_s['Total_V'] = df_s.apply(lambda x: calcul_v_semelle(x['A'], x['B'], x['a'], x['b'], x['e'], x['h_prime']), axis=1) * df_s['Nb']
        st.session_state['v_semelle_v7'] = df_s[['N° Art.', 'Total_V']]
        st.dataframe(df_s)
        st.success(f"إجمالي السوميلات: {df_s['Total_V'].sum():.3f} m³")

# 2. الميتري العادي (Fouilles, Béton, etc.)
with tabs[1]:
    st.subheader("الميتري العادي (L x l x h)")
    df_m = st.data_editor(pd.DataFrame({
        'N° Art.': ['1.01', '1.02', '1.03'],
        'Désignation': ['Terrassement', 'Fouille en masse', 'Fouille en rigole'],
        'Nb': [1.0, 1.0, 1.0], 'L': [10.0, 5.0, 20.0], 'l': [10.0, 5.0, 0.5], 'h': [0.5, 0.8, 1.0]
    }), num_rows="dynamic", key="m_v7")
    
    df_m['Total'] = df_m['Nb'] * df_m['L'] * df_m['l'] * df_m['h']
    st.session_state['v_metre_v7'] = df_m[['N° Art.', 'Total']]
    st.dataframe(df_m)

# 3. حساب الحديد
with tabs[2]:
    st.subheader("حساب أوزان الحديد")
    acier_df = st.data_editor(pd.DataFrame({
        'N° Art.': ['2.02'], 'Ouvrage': ['Semelles'], 'Ø': [12], 'L.totale (ml)': [100.0]
    }), num_rows="dynamic", key="a_v7")
    
    ratios = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21, 16: 1.58, 20: 2.47}
    if st.button("احسب وزن الحديد"):
        acier_df['Poids (Kg)'] = acier_df.apply(lambda x: x['L.totale (ml)'] * ratios.get(x['Ø'], 0), axis=1)
        st.session_state['v_acier_v7'] = acier_df[['N° Art.', 'Poids (Kg)']]
        st.dataframe(acier_df)

# 4. الربط النهائي بالبوردورو Excel
with tabs[3]:
    st.subheader("تحديث البوردورو Excel أوتوماتيكياً")
    if uploaded_bp:
        df_bp = pd.read_excel(uploaded_bp)
        
        # البحث عن عمود الرقم (N°) بشكل ذكي في ملفك
        col_n = [c for c in df_bp.columns if 'n°' in str(c).lower() or 'num' in str(c).lower() or 'art' in str(c).lower()]
        
        if not col_n:
            st.error("⚠️ لم نجد عمود 'N°' في ملف Excel. تأكد من وجود عمود للأرقام.")
        else:
            c_name = col_n[0]
            if st.button("تحديث وتحميل البوردورو المحدث"):
                df_bp[c_name] = df_bp[c_name].astype(str).str.strip()
                
                # تجميع البيانات
                all_results = []
                if 'v_semelle_v7' in st.session_state: 
                    all_results.append(st.session_state['v_semelle_v7'].rename(columns={'N° Art.': c_name, 'Total_V': 'Q'}))
                if 'v_metre_v7' in st.session_state: 
                    all_results.append(st.session_state['v_metre_v7'].rename(columns={'N° Art.': c_name, 'Total': 'Q'}))
                if 'v_acier_v7' in st.session_state: 
                    all_results.append(st.session_state['v_acier_v7'].rename(columns={'N° Art.': c_name, 'Poids (Kg)': 'Q'}))
                
                if all_results:
                    final_updates = pd.concat(all_results)
                    # البحث عن عمود الكمية
                    col_q = [c for c in df_bp.columns if 'quant' in str(c).lower() or 'qte' in str(c).lower()]
                    q_col_name = col_q[0] if col_q else 'Quantités calculées'
                    
                    for _, row in final_updates.iterrows():
                        df_bp.loc[df_bp[c_name] == str(row[c_name]), q_col_name] = row['Q']
                    
                    st.success("✅ تم تحديث البوردورو بنجاح!")
                    st.dataframe(df_bp)
                    
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine='openpyxl') as w:
                        df_bp.to_excel(w, index=False)
                    st.download_button("📥 تحميل البوردورو المحدث", buf.getvalue(), "Bordereau_Ordo_Final.xlsx")
    else:
        st.warning("👈 ارفع ملف البوردورو (Excel) من القائمة الجانبية أولاً.")
