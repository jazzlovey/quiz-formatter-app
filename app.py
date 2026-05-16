import streamlit as st
import re
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
    "Chapter# (in two digits)"
)

quiz = st.text_input(
    "Quiz# (in two digits)"
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

    lines = text.split("\n")

    cleaned_lines = []

    option_letters = ["A", "B", "C", "D", "E", "F"]

    option_counter = 0

    for line in lines:

        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # -----------------------------------------
        # REMOVE QUESTION NUMBERING
        # Example:
        # 1)
        # 1.
        # Q1.
        # -----------------------------------------

        line = re.sub(
            r'^(Q\s*)?\d+[\)\.\:]?\s*',
            '',
            line,
            flags=re.IGNORECASE
        )

        # -----------------------------------------
        # NORMALIZE ANSWER LINE
        # -----------------------------------------

        if re.match(r'(?i)^answer', line):

            answer = re.sub(
                r'(?i)^answer\s*[:=\-]?\s*',
                '',
                line
            ).strip()

            answer = answer.upper()

            # Convert numeric answer to letter
            if answer.isdigit():

                num = int(answer)

                if 1 <= num <= 6:

                    answer = option_letters[num - 1]

            cleaned_lines.append(f"ANSWER: {answer}")

            cleaned_lines.append("")

            option_counter = 0

            continue

        # -----------------------------------------
        # DETECT OPTIONS
        # Supports:
        # a)
        # a.
        # A)
        # 1)
        # etc.
        # -----------------------------------------

        option_match = re.match(
            r'^([a-fA-F1-6])[\)\.\:]?\s*(.*)',
            line
        )

        if option_match:

            option_text = option_match.group(2).strip()

            letter = option_letters[option_counter]

            cleaned_lines.append(
                f"{letter}. {option_text}"
            )

            option_counter += 1

            continue

        # -----------------------------------------
        # TREAT AS QUESTION
        # -----------------------------------------

        option_counter = 0

        # Capitalize first letter
        if line:

            line = line[0].upper() + line[1:]

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

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