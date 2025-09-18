import streamlit as st
import openai
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import matplotlib.pyplot as plt
from io import BytesIO
from dotenv import load_dotenv
import time

# --- Load API Key ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- App UI ---
st.set_page_config(page_title="AI Patient-Friendly Note Translator", layout="wide")
st.title("🩺 AI Healthcare Translator")
st.markdown("**Ha-neul Jung created** – Making doctor’s notes accessible for foreign patients")

# --- Author & Data Credit ---
st.markdown("""
<p style='text-align:right; color: gray; font-size:12px;'>
Created by Ha-neul Jung | Data source: WHO, CDC, and publicly available medical datasets
</p>
""", unsafe_allow_html=True)

# --- Sidebar: Sample Notes & Settings ---
st.sidebar.title("📝 Patient Note Input & Settings")

sample_notes = {
    "Select an example note": "",
    "Hypertension & Hyperlipidemia": "45-year-old male presents for routine follow-up. BP 152/94 mmHg. On losartan 50mg daily. LDL 172 mg/dL, HDL 42 mg/dL, TG 190 mg/dL. Advised diet modification, exercise, and initiation of atorvastatin 20mg nightly.",
    "Diabetes & Obesity": "52-year-old female with type 2 diabetes, last HbA1c 8.2%. BMI 32. Blood pressure 138/88 mmHg. Currently on metformin 1000mg BID. Discussed dietary plan, weight reduction, and physical activity goal of 150 min/week. Consider GLP-1 agonist if target not met.",
    "Asthma Exacerbation": "30-year-old patient presents with wheezing and shortness of breath for 3 days. PE: expiratory wheezes bilaterally. PEF 280 L/min (personal best 400 L/min). Prescribed albuterol inhaler PRN, fluticasone 110 mcg BID. Advised trigger avoidance and follow-up in 1 week.",
    "Acute Bronchitis & Smoking History": "38-year-old male with 10-year smoking history presents with productive cough and low-grade fever x 5 days. CXR negative for consolidation. Prescribed supportive care: hydration, OTC antitussives, and nicotine cessation counseling.",
    "Chronic Kidney Disease & Hypertension": "60-year-old female with CKD stage 3 (eGFR 42), HTN on amlodipine 10mg daily. Labs: Cr 1.5 mg/dL, K+ 4.8 mmol/L. Discussed low-sodium diet, BP log monitoring, and nephrology follow-up. Advised avoiding NSAIDs.",
    "Heart Failure & Arrhythmia": "70-year-old male with HFrEF (EF 35%) presents for routine cardiology visit. NYHA II symptoms. Medications: carvedilol 25mg BID, furosemide 40mg daily. ECG shows occasional PVCs. Encouraged daily weight monitoring and low-salt diet. Discussed signs of fluid overload."
}

# --- Dropdown to select sample ---
note_choice = st.sidebar.selectbox("Choose a sample note:", options=list(sample_notes.keys()))

# --- Fill text area automatically ---
if note_choice and note_choice != "Select an example note":
    doctor_note_text = st.sidebar.text_area("Or paste a doctor's note:", value=sample_notes[note_choice], height=300)
else:
    doctor_note_text = st.sidebar.text_area("Or paste a doctor's note:", height=300)

language = st.sidebar.radio(
    "🌐 Select display language:",
    options=["English", "Korean"]
)

# --- Risk Keywords & Conditions ---
risk_keywords = {
    "hypertension": {"high": ["stage 2", "severe", "crisis"], "moderate": ["elevated", "stage 1"], "low": ["borderline"]},
    "diabetes": {"high": ["hba1c >9", "insulin"], "moderate": ["hba1c 7-9", "metformin"], "low": ["prediabetes"]},
    "hyperlipidemia": {"high": ["ldl >190"], "moderate": ["ldl 130-189"], "low": ["borderline cholesterol"]},
    "asthma": {"high": ["status asthmaticus", "severe"], "moderate": ["moderate"], "low": ["mild"]},
    "obesity": {"high": ["bmi >35"], "moderate": ["bmi 30-35"], "low": ["bmi 25-30"]},
}

# --- Helper: sanitize text for Streamlit & PDF ---
def sanitize_text(text):
    return ''.join(
        c if ('\u0000' <= c <= '\u007F') or ('\uAC00' <= c <= '\uD7AF') or c in ".,!?()-/:%" else ' '
        for c in text
    )

# --- Button Action ---
if st.button("Generate Patient-Friendly Report 🩺"):
    if not doctor_note_text.strip():
        st.error("Please enter a doctor's note first.")
    else:
        with st.spinner("Generating patient-friendly report... ⏳"):
            try:
                # --- AI Prompts ---
                eng_prompt = f"""Explain this doctor's note in simple, clear language for the patient.
                                Include specific, actionable insights tailored to this patient’s conditions and lab values, 
                                highlighting potential risks that are not immediately obvious.
                                Patient note: {doctor_note_text}
                                """ 
                kor_prompt = f"""Translate this note into clear Korean for the patient.
                                Include explanations of medical terms, why each treatment is suggested, and practical daily tips.
                                Keep it conversational and patient-focused.
                                Patient note: {doctor_note_text}
                                """
                edu_prompt = f"""Provide a short patient education summary based on this doctor's note.
                                Include:
                                1. Specific risk factors related to the patient's conditions.
                                2. Practical, actionable tips that the patient might not already know.
                                3. Insights based on the patient’s age, lab results, or medications.
                                4. Explanations of why certain treatments or lifestyle changes are recommended.
                                Patient note: {doctor_note_text}
                                """
                risk_summary_prompt = f"""Based on the following doctor's note, generate:

                                1. A short patient-friendly summary highlighting the main health risks.
                                2. A practical checklist of lifestyle or monitoring steps for the patient.

                                Doctor's note:
                                {doctor_note_text}
                                """

                # --- Progress simulation ---
                progress = st.progress(0)
                for i in range(20, 101, 20):
                    time.sleep(0.2)
                    progress.progress(i)

                # --- OpenAI API calls ---
                translation_eng = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": eng_prompt}]
                ).choices[0].message.content.strip()

                translation_kor = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": kor_prompt}]
                ).choices[0].message.content.strip()

                awareness_text = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": edu_prompt}]
                ).choices[0].message.content.strip()

                risk_summary_ai = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": risk_summary_prompt}]
                ).choices[0].message.content.strip()

                # Translate awareness_text and risk_summary_ai to Korean
                kor_edu_prompt = f"Translate the following patient education summary to Korean:\n\n{awareness_text}"
                translation_kor_edu = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": kor_edu_prompt}]
                ).choices[0].message.content.strip()
                
                kor_risk_prompt = f"Translate the following patient risk summary to Korean:\n\n{risk_summary_ai}"
                translation_kor_risk = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": kor_risk_prompt}]
                ).choices[0].message.content.strip()

                # --- Sanitize AI outputs for Streamlit display ---
                translation_eng_safe = sanitize_text(translation_eng)
                translation_kor_safe = sanitize_text(translation_kor)
                awareness_text_safe = sanitize_text(awareness_text)
                translation_kor_edu_safe = sanitize_text(translation_kor_edu)
                risk_summary_text = sanitize_text(risk_summary_ai)
                risk_summary_text_kor = sanitize_text(translation_kor_risk)

                # --- Display Translations & Awareness ---
                if language == "English":
                    st.subheader("✅ Patient-Friendly Explanation")
                    st.write(translation_eng_safe)
                    st.subheader("📖 Awareness & Education")
                    st.write(awareness_text_safe)
                    st.subheader("🩺 Summary & Checklist")
                    st.write(risk_summary_text)
                else:
                    st.subheader("✅ 환자 친화적 설명")
                    st.write(translation_kor_safe)
                    st.subheader("📖 환자 교육 및 정보")
                    st.write(translation_kor_edu_safe)
                    st.subheader("🩺 건강 상태 요약 & 체크 리스트")
                    st.write(risk_summary_text_kor)

                # --- PDF Export (same as before) ---
                pdf = FPDF()
                pdf.add_page()
                pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf")
                pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf")
                pdf.add_font("DejaVu", "I", "fonts/DejaVuSans-Oblique.ttf")
                pdf.add_font("DejaVu", "BI", "fonts/DejaVuSans-BoldOblique.ttf")
                pdf.set_font("DejaVu", size=14)
                pdf.add_font("NotoSansKR", "", "fonts/NotoSansKR-Regular.ttf")
                pdf.add_font("NotoSansKR", "B", "fonts/NotoSansKR-Bold.ttf")
                pdf.add_font("NotoSansKR", "I", "fonts/NotoSansKR-ExtraLight.ttf")
                pdf.set_font("NotoSansKR", size=12)
                pdf.set_text_color(0, 51, 102)
                pdf.cell(0, 12, "Patient Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                pdf.ln(8)

                if language == "English":
                    pdf.set_font("DejaVu", size=14, style="B")
                    pdf.cell(0, 10, "Patient-Friendly Translation", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("DejaVu", size=12)
                    pdf.multi_cell(0, 8, translation_eng_safe)
                    pdf.ln(4)
                    pdf.set_font("DejaVu", size=14, style="B")
                    pdf.cell(0, 10, "Awareness & Education", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("DejaVu", size=12)
                    pdf.multi_cell(0, 8, awareness_text_safe)
                    pdf.ln(4)
                    pdf.set_font("DejaVu", size=14, style="B")
                    pdf.cell(0, 10, "Patient Health Risk Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("DejaVu", size=12)
                    pdf.multi_cell(0, 8, risk_summary_text)
                    pdf.ln(4)
                else:
                    pdf.set_font("NotoSansKR", size=14, style="B")
                    pdf.cell(0, 10, "환자 친화적 설명", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("NotoSansKR", size=12)
                    pdf.multi_cell(0, 8, translation_kor_safe)
                    pdf.ln(4)
                    pdf.set_font("NotoSansKR", size=14, style="B")
                    pdf.cell(0, 10, "환자 교육 및 정보", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("NotoSansKR", size=12)
                    pdf.multi_cell(0, 8, translation_kor_edu_safe)
                    pdf.ln(4)
                    pdf.set_font("NotoSansKR", size=14, style="B")
                    pdf.cell(0, 10, "건강 상태 요약 & 체크 리스트", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("NotoSansKR", size=12)
                    pdf.multi_cell(0, 8, risk_summary_text_kor)
                    pdf.ln(4)

                if language == "English":
                    pdf.set_font("DejaVu", size=10, style="I")
                    pdf.set_text_color(100, 100, 100)
                    pdf.multi_cell(0, 6, "Disclaimer: This report is for educational purposes only and not a substitute for professional medical advice.")
                    pdf.ln(3)
                    pdf.set_font("DejaVu", size=10, style="I")
                    pdf.set_text_color(120, 120, 120)
                    page_width = pdf.w - 2 * pdf.l_margin  # page width minus left/right margins
                    pdf.multi_cell(page_width, 6, "Created by Ha-neul Jung | Data source: WHO, CDC, publicly available datasets", align="R")
                else:
                    pdf.set_font("NotoSansKR", size=10, style="I")
                    pdf.set_text_color(100, 100, 100)
                    pdf.multi_cell(0, 6, "면책 조항: 이 보고서는 전문적인 의학적 조언을 대신하는 것이 아니라 교육 목적으로만 작성되었습니다.")
                    pdf.ln(3)
                    pdf.set_font("NotoSansKR", size=10, style="I")
                    pdf.set_text_color(120, 120, 120)
                    page_width = pdf.w - 2 * pdf.l_margin  # page width minus left/right margins
                    pdf.multi_cell(page_width, 6, "정하늘 작성 | 데이터 출처: WHO, CDC, 공개 데이터셋", align="R")

                pdf_file = "translation_report.pdf"
                pdf.output(pdf_file)
                with open(pdf_file, "rb") as f:
                    st.download_button("⬇️ Download Full Report (PDF)", f, file_name="patient_report_byHaneulJung.pdf")

                # --- Follow-up Q&A ---
                st.subheader("💬 Ask a Question About Your Note")
                user_q = st.text_input("Type your question here:")
                if st.button("Ask AI"):
                    if user_q.strip():
                        q_response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a helpful medical explainer for patients."},
                                {"role": "user", "content": f"Doctor's note: {doctor_note_text}"},
                                {"role": "user", "content": f"Patient question: {user_q}"}
                            ]
                        )
                        st.info(sanitize_text(q_response.choices[0].message.content.strip()))

            except Exception as e:
                st.error(f"Error: {e}")

