import streamlit as st
import openai
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import matplotlib.pyplot as plt
from io import BytesIO
from dotenv import load_dotenv
import time
import base64

# --- Load API Key ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- App UI ---
st.set_page_config(page_title="Patient-Friendly AI Assistant", layout="wide")
st.title("🩺 Patient-Friendly AI Assistant")

pdf_file = "project_report.pdf"
# PDF 읽기
with open(pdf_file, "rb") as f:
    pdf_bytes = f.read()
# base64 인코딩 (브라우저에서 다운로드 가능하게)
b64_pdf = base64.b64encode(pdf_bytes).decode()
# 오른쪽 끝 정렬, 작은 글씨, 색상 버튼
st.markdown(f"""
    <div style="text-align: right; margin-top: 10px;">
        <a href="data:application/pdf;base64,{b64_pdf}" download="project_report.pdf">
            <button style="
                background-color:#FF5733; 
                color:white; 
                padding:0.3em 0.8em; 
                border:none; 
                border-radius:5px; 
                cursor:pointer; 
                font-size:12px;">
                📄 프로젝트 요약 보고서 다운로드해서 읽기
            </button>
        </a>
    </div>
""", unsafe_allow_html=True)

st.markdown("내외국인 환자와의 원활한 소통을 지원하는 스마트 의료 도구 \n\n 1. 왼쪽 상단 >> 을 클릭하세요. \n 2. 샘플 예시 메모를 선택하거나 직접 입력하세요. \n 3. 리포트 생성하기를 클릭하세요.")

# --- Author & Data Credit ---
st.markdown("""
<p style='text-align:right; color: gray; font-size:12px;'>
Created by Ha-neul Jung | Data sources: World Health Organization(WHO),
Centers for Disease Control and Prevention(CDC), and publicly available medical datasets
</p>
""", unsafe_allow_html=True)

# --- Sidebar: Sample Notes & Settings ---
st.sidebar.title("📝 환자 메모 입력")

# 분야 선택
# category = st.sidebar.radio("분야 선택", ["의학", "치의학"])

# 샘플 노트 정의
medical_samples = {
    "예시 메모 선택": "",
    "고혈압 & 고지혈증": "45세 남성, 고혈압(2기) 및 고지혈증 진단. 아토르바스타틴 20mg 처방 예정.",
    "당뇨병 & 비만": "52세 여성, 제2형 당뇨병 (HbA1C 8.2%), BMI 32. 메트포르민 복용 중, 생활습관 개선 권장.",
    "천식 악화": "30세 환자, 호흡곤란 및 쌕쌕거림으로 내원. 흡입용 스테로이드 처방.",
    "만성신질환 & 고혈압": "60세 여성, CKD 3단계 (eGFR 42). 아몰로디핀 복용 중. 저염식 및 신장내과 추적 관찰 필요.",
    "심부전 & 부정맥": "70세 남성, 심부전 EF 35%. 이뇨제 및 베타차단제 복용 중. 간헐적 심실 조기수축 관찰."
}

# dental_samples = {
#     "예시 메모 선택": "",
#     "충치 및 치은염": "35세 남성, 어금니 충치 및 잇몸 염증. 복합 레진 충전 및 스케일링 권고.",
#     "사랑니 매복": "22세 환자, 하악 제3대구치 매복으로 경미한 통증. 발치 예정, 수술 후 관리 안내.",
#     "치아 민감증": "40세 여성, 차가운 음료 섭취 시 상악 전치 민감. 불소 도포 및 과도한 양치 압력 조절 권고.",
#     "치주질환 관리": "50세 남성, 치주낭 5mm 이상, 치석 다수 발견. 정기 스케일링 및 구강 위생 교육 권장.",
#     "보철물 교체": "60세 여성, 기존 브릿지 변색 및 부착 불량. 새 브릿지 제작 및 잇몸 상태 관리 안내."
# }

# --- Dropdown to select sample ---
# if category == "의학":
#     note_choice = st.sidebar.selectbox("샘플 선택", list(medical_samples.keys()))
#     doctor_note_text = medical_samples[note_choice]
# else:
#     note_choice = st.sidebar.selectbox("샘플 선택", list(dental_samples.keys()))
#     doctor_note_text = dental_samples[note_choice]
note_choice = st.sidebar.selectbox("샘플 선택", list(medical_samples.keys()))
doctor_note_text = medical_samples[note_choice]

# --- Fill text area automatically ---
if note_choice and note_choice != "예시 메모 선택":
    doctor_note_text = st.sidebar.text_area("또는 의사 메모를 직접 입력하세요:", value=doctor_note_text, height=300)
else:
    doctor_note_text = st.sidebar.text_area("또는 의사 메모를 직접 입력하세요:", height=300)

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
if st.button("리포트 생성하기 🩺"):
    if not doctor_note_text.strip():
        st.error("Doctor's note 를 먼저 기입해주세요.")
    else:
        with st.spinner("생성중... ⏳"):
            try:
                # --- AI Prompts ---
                translation_eng_prompt = f"""Based on the following Korean doctor's note, provide a patient-friendly English explanation for the foreign patient in a **clear, bullet point list format**.
                
                                    Requirements:
                                    1. Present each point as a separate item for clarity.
                                    2. Explain medical terms in simple language. And it should be **5-7 sentences long** to provide sufficient detail., e.g.,
                                    - Instead of just "eGFR", write "eGFR (estimated Glomerular Filtration Rate), which indicates how well the kidneys are working".
                                    3. Describe why each treatment or medication is suggested. And it should be **5-7 sentences long** to provide sufficient detail.
                                    - The name of the drug.
                                    - A simple explanation of what it is for (e.g., "Amlodipine: helps lower blood pressure to reduce strain on the heart").
                                    - Potential side effects the patient should watch for.
                                    4. Keep the tone concise, clear, and patient-focused, suitable for direct display in a PDF.

                                    Patient note: {doctor_note_text}
                                    """
                edu_eng_prompt = f"""Based on the following Korean doctor's note, provide a patient-friendly English potential risk, guidance for the foreign patient in a **clear, bullet point list format**.
                                    Do not provide any explantion about doctor's note.
                
                                    Requirements:
                                    1. Present each point as a separate item for clarity and must reference and cite public health statistics data from WHO or CDC or open data. Reference FDI World Dental Federation if Doctor's Note related to dental.
                                    2. Highlight potential risks related to the patient's conditions that are not immediately obvious in **5-7 sentences long** to provide sufficient detail.
                                    3. Include practical, actionable daily diet tips and lifestyle guidance or work out routines tailored to this patient's conditions, lab results, and age that the patient might not already know **5-7 sentences long** to provide sufficient detail.
                                    4. Explanations of why certain treatments or lifestyle changes are recommended **3-5 sentences long** to provide sufficient detail.
                                    5. Keep the tone concise, clear, and patient-focused, suitable for direct display in a PDF.

                                    Patient note: {doctor_note_text}
                                    """

                # --- Progress simulation ---
                progress = st.progress(0)
                for i in range(20, 101, 20):
                    time.sleep(0.2)
                    progress.progress(i)

                # --- OpenAI API calls ---
                translation_eng = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": translation_eng_prompt}]
                ).choices[0].message.content.strip()

                edu_eng = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": edu_eng_prompt}]
                ).choices[0].message.content.strip()

                # --- Sanitize AI outputs for Streamlit display ---
                translation_eng_safe = sanitize_text(translation_eng)
                edu_eng_safe = sanitize_text(edu_eng)

                tab1, tab2 = st.tabs(["🇺🇸 English", "🇰🇷 Korean"])

                with tab1:
                    # --- Display Translations & Awareness ---
                    st.markdown("""
                                <p style='text-align:center; color: gray; font-size:14px;'>
                                Disclaimer: This report is for educational purposes only and not a substitute for professional medical advice.
                                </p>
                                """, unsafe_allow_html=True)   
                    st.subheader("✅ Patient-Friendly Explanation")
                    st.write(translation_eng_safe)
                    st.subheader("📖 Awareness & Education")
                    st.write(edu_eng_safe)

                    # --- PDF Export (same as before) ---
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf")
                    pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf")
                    pdf.add_font("DejaVu", "I", "fonts/DejaVuSans-Oblique.ttf")
                    pdf.add_font("DejaVu", "BI", "fonts/DejaVuSans-BoldOblique.ttf")
                    pdf.set_font("DejaVu", size=14)     
                    pdf.set_text_color(0, 51, 102)
                    pdf.cell(0, 12, "Patient Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.ln(8)    

                    pdf.set_font("DejaVu", size=14, style="B")
                    pdf.cell(0, 10, "Patient-Friendly Translation", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("DejaVu", size=12)
                    pdf.multi_cell(0, 8, translation_eng_safe)
                    pdf.ln(4)
                    pdf.set_font("DejaVu", size=14, style="B")
                    pdf.cell(0, 10, "Awareness & Education", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("DejaVu", size=12)
                    pdf.multi_cell(0, 8, edu_eng_safe)
                    pdf.ln(4)

                    pdf.set_font("DejaVu", size=10, style="I")
                    pdf.set_text_color(100, 100, 100)
                    pdf.multi_cell(0, 6, "Disclaimer: This report is for educational purposes only and not a substitute for professional medical advice.")
                    pdf.ln(3)
                    pdf.set_font("DejaVu", size=10, style="I")
                    pdf.set_text_color(120, 120, 120)
                    page_width = pdf.w - 2 * pdf.l_margin  # page width minus left/right margins
                    pdf.multi_cell(page_width, 6, "Created by Ha-neul Jung | Data sources: World Health Organization(WHO), Centers for Disease Control and Prevention(CDC), World Dental Federation(FDI) and publicly available medical datasets", align="R")
                    
                    pdf_file = "translation_report.pdf"
                    pdf.output(pdf_file)
                    with open(pdf_file, "rb") as f:
                        st.download_button("⬇️ Download Full Report (PDF)", f, file_name="patient_report_eng.pdf")

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

                with tab2:
                    # Translate into Korean
                    translation_kor_prompt = f"""Translate the following doctor's note to Korean:\n\n{translation_eng_safe}.
                                                 Aware that the patient is one person not people, so avoid using '여러분'.
                                                 And the response format must follow the english format."""
                    translation_kor = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": translation_kor_prompt}]
                    ).choices[0].message.content.strip()

                    edu_kor_prompt = f"""Translate the following doctor's note to Korean:\n\n{edu_eng_safe}.
                                         Aware that the patient is one person not people, so avoid using '여러분'.
                                         And the response format must follow the english format.
                                         Translate CDC into 미국질병통제예방센터(CDC), WHO into 세계보건기구(WHO), FDI into 세계치과의사연맹(FDI) if it's mentioned in the note."""
                    edu_kor = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": edu_kor_prompt}]
                    ).choices[0].message.content.strip()

                    # --- Sanitize AI outputs for Streamlit display ---
                    translation_kor_safe = sanitize_text(translation_kor)
                    edu_kor_safe = sanitize_text(edu_kor)

                    # --- Display Translations & Awareness ---
                    st.markdown("""
                                <p style='text-align:center; color: gray; font-size:14px;'>
                                면책 조항: 이 보고서는 전문적인 의학적 조언을 대신하는 것이 아니라 교육 목적으로만 작성되었습니다.
                                </p>
                                """, unsafe_allow_html=True)   
                    st.subheader("✅ 환자 친화적 설명")
                    st.write(translation_kor_safe)
                    st.subheader("📖 환자 교육 및 정보")
                    st.write(edu_kor_safe)

                    # --- PDF Export (same as before) ---
                    pdf_kor = FPDF()
                    pdf_kor.add_page()
                    pdf_kor.add_font("NotoSansKR", "", "fonts/NotoSansKR-Regular.ttf")
                    pdf_kor.add_font("NotoSansKR", "B", "fonts/NotoSansKR-Bold.ttf")
                    pdf_kor.add_font("NotoSansKR", "I", "fonts/NotoSansKR-ExtraLight.ttf")
                    pdf_kor.set_font("NotoSansKR", size=12)
                    pdf_kor.set_text_color(0, 51, 102)
                    pdf_kor.cell(0, 12, "Patient Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf_kor.ln(8)

                    pdf_kor.set_font("NotoSansKR", size=14, style="B")
                    pdf_kor.cell(0, 10, "환자 친화적 설명", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf_kor.set_font("NotoSansKR", size=12)
                    pdf_kor.multi_cell(0, 8, translation_kor_safe)
                    pdf_kor.ln(4)
                    pdf_kor.set_font("NotoSansKR", size=14, style="B")
                    pdf_kor.cell(0, 10, "환자 교육 및 정보", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf_kor.set_font("NotoSansKR", size=12)
                    pdf_kor.multi_cell(0, 8, edu_kor_safe)
                    pdf_kor.ln(4)

                    pdf_kor.set_font("NotoSansKR", size=10, style="I")
                    pdf_kor.set_text_color(100, 100, 100)
                    pdf_kor.multi_cell(0, 6, "면책 조항: 이 보고서는 전문적인 의학적 조언을 대신하는 것이 아니라 교육 목적으로만 작성되었습니다.")
                    pdf_kor.ln(3)
                    pdf_kor.set_font("NotoSansKR", size=10, style="I")
                    pdf_kor.set_text_color(120, 120, 120)
                    page_width = pdf_kor.w - 2 * pdf_kor.l_margin  # page width minus left/right margins
                    pdf_kor.multi_cell(page_width, 6, "정하늘 작성 | 데이터 출처: 세계보건기구(WHO), 미국질병통제예방센터(CDC), 세계치과의사연맹(FDI)과 공개 의료 데이터셋", align="R")

                    pdf_file_kor = "translation_report_kor.pdf"
                    pdf_kor.output(pdf_file_kor)
                    with open(pdf_file_kor, "rb") as f:
                        st.download_button("⬇️ Download Full Report (PDF)", f, file_name="patient_report_kor.pdf")

                    # --- Follow-up Q&A ---
                    st.subheader("💬 궁금한 사항을 더 물어보세요")
                    user_q = st.text_input("질문을 입력해 주세요:")
                    if st.button("AI에게 물어보기"):
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

