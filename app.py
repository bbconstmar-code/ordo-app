import streamlit as st
import pandas as pd
import io

# واجهة Ordo Estates
st.set_page_config(page_title="Ordo Estates Cloud", layout="wide")

# محرك الحسابات (V1 + V2)
def calcul_v(A, B, a, b, e, h_p):
    V1 = A * B * e
    V2 = (1/6) * h_p * (B * (2*A + a) + b * (2*a + A))
    return float(V1 + V2)

st.title("🏗️ Ordo Estates : Système de Gestion Cloud")

tab1, tab2, tab3 = st.tabs(["📏 حساب السوميلات", "⛓️ حساب الحديد", "📊 الربط بالبوردورو"])

with tab1:
    st.subheader("إدخال قياسات السوميلات")
    # جدول تفاعلي كيدخل فيه مروان القياسات من لبلان
    df_s = st.data_editor(pd.DataFrame({
        'Dés.': ['S1'], 'Nb': [1], 'A': [1.10], 'B': [1.10],
        'a': [0.25], 'b': [0.25], 'e': [0.20], 'h_prime': [0.15]
    }), num_rows="dynamic")
    
    if st.button("احسب خرسانة السوميلات"):
        df_s['Total_V'] = df_s.apply(lambda x: calcul_v(x['A'], x['B'], x['a'], x['b'], x['e'], x['h_prime']), axis=1) * df_s['Nb']
        st.session_state['v_final'] = df_s['Total_V'].sum()
        st.dataframe(df_s)
        st.success(f"إجمالي الحجم: {st.session_state['v_final']:.3f} m³")

with tab2:
    st.subheader("حساب وزن الحديد")
    # منطق الحديد اللي عندك في ملف métré acier
    acier_df = st.data_editor(pd.DataFrame({
        'Ouvrage': ['Semelles'], 'Ø': [12], 'L.totale (ml)': [100.0]
    }), num_rows="dynamic")
    
    ratios = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21, 16: 1.58, 20: 2.47}
    if st.button("احسب وزن الحديد"):
        acier_df['Poids (Kg)'] = acier_df.apply(lambda x: x['L.totale (ml)'] * ratios.get(x['Ø'], 0), axis=1)
        st.session_state['poids_total'] = acier_df['Poids (Kg)'].sum()
        st.dataframe(acier_df)
        st.info(f"إجمالي وزن الحديد: {st.session_state['poids_total']:.2f} Kg")

with tab3:
    st.subheader("تحديث البوردورو النهائي")
    # هنا كترفع ملف Excel ديالك (metri.xls)
    file_bp = st.file_uploader("ارفع ملف البوردورو (Excel)", type="xlsx")
    
    if file_bp and 'v_final' in st.session_state:
        df_bp = pd.read_excel(file_bp)
        # الربط الأوتوماتيكي: البرنامج كيقلب على أرتيكل 1.06 ويحط فيه النتيجة
        if 'N°' in df_bp.columns:
            df_bp.loc[df_bp['N°'] == '1.06', 'Quantités calculées'] = st.session_state['v_final']
            st.write("✅ تم تحديث أرتيكل الخرسانة (1.06)")
            st.dataframe(df_bp)
            
            # تحميل الملف الجديد
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df_bp.to_excel(w, index=False)
            st.download_button("📥 تحميل البوردورو المحدث", buf.getvalue(), "Bordereau_Ordo.xlsx")
