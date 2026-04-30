import streamlit as st
import pandas as pd
import io

# ... (نفس الجزء الأول ديال الكود السابق) ...

# 4. الربط بالبوردورو (النسخة المطورة)
with tabs[3]:
    st.subheader("الربط الأوتوماتيكي بالبوردورو")
    if uploaded_bp:
        df_bp = pd.read_excel(uploaded_bp)
        
        if st.button("تحديث كل الأرتيكلات"):
            # 1. تحديث خرسانة السوميلات (بناءً على الرقم 1.06)
            if 'v_semelle' in st.session_state:
                df_bp.loc[df_bp['N°'] == '1.06', 'Quantités calculées'] = st.session_state['v_semelle']
            
            # 2. تحديث الميتري العادي (بناءً على السمية Désignation)
            # البرنامج كيشوف كل سطر في "الميتري العادي" وكيمشي يقلب على خوه في البوردورو
            if 'v_metre' in st.session_state:
                # هنا كيدير الربط بين الجدولين
                for index, row in df_m.iterrows():
                    article_name = row['Désignation']
                    total_calc = row['Total']
                    # كيقلب في البوردورو على السطر اللي فيه نفس السمية
                    df_bp.loc[df_bp['Désignation'] == article_name, 'Quantités calculées'] = total_calc
            
            st.success("✅ تم دمج الميتري العادي والسوميلات في البوردورو!")
            st.dataframe(df_bp)
            
            # زر التحميل
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df_bp.to_excel(w, index=False)
            st.download_button("📥 تحميل البوردورو النهائي المحدث", buf.getvalue(), "Bordereau_Ordo_Final.xlsx")
    else:
        st.info("ارفع ملف البوردورو (Excel) من القائمة الجانبية.")
