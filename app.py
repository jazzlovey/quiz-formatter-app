from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

import streamlit as st
import re
import html
from docx import Document

# ---------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------

st.set_page_config(
    page_title="KIET's LMS Quiz Preparation AI Tool"
)

st.title("KIET's LMS Quiz Preparation AI Tool")

st.write(
    "Upload a quiz file and let AI generate a clean LMS-ready quiz text file."
)

# ---------------------------------------------------
# INPUT FIELDS
# ---------------------------------------------------

chapter = st.text_input(
    "Chapter #"
)

quiz = st.text_input(
    "Quiz #"
)

uploaded_file = st.file_uploader(
    "Upload TXT or DOCX Quiz File",
    type=["txt", "docx"]
)

# ---------------------------------------------------
# READ FILE
# ---------------------------------------------------

def read_uploaded_file(uploaded_file):

    if uploaded_file.type == "text/plain":

        return uploaded_file.read().decode("utf-8")

    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":

        doc = Document(uploaded_file)

        full_text = []

        for para in doc.paragraphs:

            full_text.append(para.text)

        return "\n".join(full_text)

    return ""

# ---------------------------------------------------
# NORMALIZATION ENGINE
# ---------------------------------------------------

def normalize_quiz(text):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are a strict Moodle Aiken quiz formatting engine.

You are NOT a chatbot.

You ONLY output strict Moodle-compatible Aiken quiz text.

STRICT OUTPUT RULES:

1. Each question stem must appear on its own line.
2. Each option must appear on a SEPARATE new line.
3. Each option must start exactly with:
A.
B.
C.
D.
followed by a space.
4. The answer line must appear immediately after options.
5. Correct answer format must be EXACTLY:
ANSWER: X
6. Insert exactly ONE blank line between separate questions.
7. Remove all question numbering.
8. Professionally capitalize ONLY question stems.
9. Preserve option text EXACTLY as written by the teacher.
10. Never rewrite, re-capitalize, paraphrase, or grammatically alter option text.
11. Preserve abbreviations like APA, SPSS, AI, LMS.
12. Do NOT add explanations.
13. Do NOT add markdown.
14. Do NOT add bullets.
15. Do NOT add examples.
16. Do NOT add notes.
17. Do NOT rewrite meanings.
18. Output ONLY the formatted quiz text.

CORRECT FORMAT EXAMPLE:

What is the capital of France?
A. London
B. Berlin
C. Paris
D. Madrid
ANSWER: C
"""
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0
    )

    formatted_text = response.choices[0].message.content
    
    formatted_text = html.unescape(formatted_text)

    # Remove markdown double spaces
    formatted_text = formatted_text.replace("  \n", "\n")

    # Remove excessive blank lines
    formatted_text = re.sub(
        r'\n{3,}',
        '\n\n',
        formatted_text
    )

    # Trim whitespace
    formatted_text = formatted_text.strip()

    return formatted_text

# ---------------------------------------------------
# VALIDATION ENGINE
# ---------------------------------------------------

def validate_quiz(text):

    errors = []

    question_blocks = text.split("ANSWER:")

    for index, block in enumerate(question_blocks[:-1], start=1):

        options = re.findall(
            r'^[A-F]\.',
            block,
            re.MULTILINE
        )

        if len(options) < 2:

            errors.append(
                f"Question {index} has less than 2 options."
            )

    return errors

# ---------------------------------------------------
# MAIN APP LOGIC
# ---------------------------------------------------

if uploaded_file:

    raw_text = read_uploaded_file(uploaded_file)

    st.subheader("Raw Uploaded Quiz")

    st.text(raw_text)

    normalized_text = normalize_quiz(raw_text)

    st.subheader("Normalized Quiz")

    st.text(normalized_text)

    validation_errors = validate_quiz(normalized_text)

    if validation_errors:

        st.error("Validation Errors Found")

        for err in validation_errors:

            st.write(err)

    else:

        st.success("Quiz formatted successfully!")

        # Ensure two-digit formatting
        chapter = chapter.zfill(2)

        quiz = quiz.zfill(2)

        filename = (
            f"Chapter_{chapter}_Quiz_{quiz}_for_LMS_import.txt"
        )

        st.download_button(
            label="Download LMS Quiz File",
            data=normalized_text,
            file_name=filename,
            mime="text/plain"
        )