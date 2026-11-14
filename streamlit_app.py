import io
import os
import zipfile
import tempfile
import streamlit as st
import PyPDF2
import fitz  # PyMuPDF
from pdf2docx import Converter
import camelot
import pandas as pd
from PIL import Image, ImageDraw

# ---------------------------------------------------------
# PAGE CONFIG & CUSTOM STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="OmniTool — Everyday Digital Utility Hub",
    page_icon="🧰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Main header banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 1.8rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        margin: 0.4rem 0 0 0;
        color: #cbd5e1;
        font-size: 1rem;
    }
    /* Tool header card */
    .tool-header {
        background-color: #f8fafc;
        border-left: 5px solid #2563eb;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1.25rem;
    }
    .tool-header h3 {
        margin: 0;
        color: #0f172a;
    }
    .tool-header p {
        margin: 0.25rem 0 0 0;
        color: #475569;
        font-size: 0.92rem;
    }
    /* Make primary buttons pop */
    .stButton > button[kind="primary"] {
        background-color: #2563eb;
        border: none;
        border-radius: 8px;
        padding: 0.55rem 1.2rem;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# OPTIONAL SECURITY GATE (Set APP_PASSWORD in Streamlit Secrets)
# ---------------------------------------------------------
def check_password():
    app_pwd = st.secrets.get("APP_PASSWORD", None) if hasattr(st, "secrets") else None
    if not app_pwd:
        return True  # No password configured; allow access

    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div class="hero-banner">
        <h1>🧰 OmniTool Utility Hub</h1>
        <p>Protected Workspace — Enter your access PIN to continue.</p>
    </div>
    """, unsafe_allow_html=True)

    pwd_input = st.text_input("Access Password", type="password")
    if st.button("Unlock Workspace", type="primary"):
        if pwd_input == app_pwd:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


if not check_password():
    st.stop()


# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧰 OmniTool Hub")
    st.caption("All-in-One Document & Photo Utilities")
    st.divider()

    category = st.radio(
        "Category",
        ["📄 Document Tools", "🖼️ Photo & Media Tools"],
        label_visibility="collapsed"
    )

    if category == "📄 Document Tools":
        tool = st.radio(
            "Select Tool",
            [
                "➕ Merge & Sequence PDFs",
                "🔓 Unlock Protected PDF",
                "🌗 Convert PDF to B&W",
                "🗜️ Compress PDF",
                "📝 PDF to Word (.docx)",
                "📊 PDF Tables to Excel (.xlsx)",
                "🖼️ Extract Images from PDF"
            ]
        )
    else:
        tool = st.radio(
            "Select Tool",
            [
                "🪪 Passport Photo Studio"
            ]
        )

    st.divider()
    st.info("🔒 **Privacy Note:** Files are processed in temporary memory and never stored permanently.")


# ---------------------------------------------------------
# HERO BANNER
# ---------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1>🧰 OmniTool Utility Hub</h1>
    <p>Fast, browser-based tools for PDFs, office documents, and print-ready passport photos.</p>
</div>
""", unsafe_allow_html=True)


def render_tool_header(title, description):
    st.markdown(f"""
    <div class="tool-header">
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# TOOL 1: MERGE & SEQUENCE PDFs
# =========================================================
if tool == "➕ Merge & Sequence PDFs":
    render_tool_header(
        "➕ Merge & Sequence PDFs",
        "Upload multiple PDF files, assign their exact order, and combine them into one document."
    )

    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if len(uploaded_files) < 2:
            st.warning("Upload at least 2 PDF files to merge.")
        else:
            st.subheader("1. Set Merge Order")
            st.caption("Assign a position number to each file. Lower numbers appear first.")

            sequenced_items = []
            for idx, file in enumerate(uploaded_files):
                col1, col2 = st.columns([1, 5])
                with col1:
                    order = st.number_input(
                        "Order",
                        min_value=1,
                        max_value=len(uploaded_files),
                        value=idx + 1,
                        key=f"seq_{file.name}_{idx}",
                        label_visibility="collapsed"
                    )
                with col2:
                    size_kb = round(file.size / 1024, 1)
                    st.markdown(f"**{file.name}** `({size_kb} KB)`")
                sequenced_items.append((order, idx, file))

            # Sort by user-assigned order, breaking ties by upload index
            ordered_files = [item[2] for item in sorted(sequenced_items, key=lambda x: (x[0], x[1]))]

            with st.expander("Preview Final Merge Sequence", expanded=True):
                for pos, f in enumerate(ordered_files, start=1):
                    st.write(f"**{pos}.** {f.name}")

            if st.button("Merge PDFs Now", type="primary"):
                with st.spinner("Merging documents..."):
                    try:
                        writer = PyPDF2.PdfWriter()
                        for f in ordered_files:
                            f.seek(0)
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                writer.add_page(page)

                        output_buf = io.BytesIO()
                        writer.write(output_buf)
                        output_buf.seek(0)

                        st.success(f"Successfully merged {len(ordered_files)} PDFs!")
                        st.download_button(
                            label="⬇️ Download Merged PDF",
                            data=output_buf,
                            file_name="merged_document.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Merge failed: {e}")


# =========================================================
# TOOL 2: UNLOCK PROTECTED PDF
# =========================================================
elif tool == "🔓 Unlock Protected PDF":
    render_tool_header(
        "🔓 Unlock Protected PDF",
        "Remove password protection from a PDF when you know the password."
    )

    uploaded_file = st.file_uploader("Upload encrypted PDF", type=["pdf"])
    password = st.text_input("Enter PDF Password", type="password")

    if uploaded_file and st.button("Unlock PDF", type="primary"):
        with st.spinner("Decrypting PDF..."):
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                if reader.is_encrypted:
                    if not reader.decrypt(password):
                        st.error("Incorrect password. Please try again.")
                        st.stop()

                writer = PyPDF2.PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)

                out_buf = io.BytesIO()
                writer.write(out_buf)
                out_buf.seek(0)

                st.success("PDF unlocked successfully!")
                st.download_button(
                    label="⬇️ Download Unlocked PDF",
                    data=out_buf,
                    file_name=f"unlocked_{uploaded_file.name}",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error unlocking PDF: {e}")


# =========================================================
# TOOL 3: CONVERT PDF TO BLACK & WHITE
# =========================================================
elif tool == "🌗 Convert PDF to B&W":
    render_tool_header(
        "🌗 Convert PDF to Black & White (Grayscale)",
        "Converts color pages to crisp grayscale with optimized JPEG compression to keep file sizes small."
    )

    uploaded_file = st.file_uploader("Upload color PDF", type=["pdf"])

    col1, col2 = st.columns(2)
    with col1:
        dpi = st.slider("Resolution (DPI)", min_value=96, max_value=250, value=150, step=10)
    with col2:
        quality = st.slider("Compression Quality", min_value=50, max_value=95, value=75, step=5)

    if uploaded_file and st.button("Convert to Black & White", type="primary"):
        with st.spinner("Converting pages to grayscale..."):
            try:
                src_bytes = uploaded_file.read()
                src_doc = fitz.open(stream=src_bytes, filetype="pdf")
                bw_doc = fitz.open()

                for pno in range(src_doc.page_count):
                    page = src_doc.load_page(pno)
                    pix = page.get_pixmap(colorspace=fitz.csGRAY, dpi=dpi)
                    new_page = bw_doc.new_page(width=page.rect.width, height=page.rect.height)
                    new_page.insert_image(
                        page.rect,
                        stream=pix.tobytes("jpeg", jpg_quality=quality)
                    )

                out_bytes = bw_doc.tobytes(garbage=4, deflate=True, clean=True)
                src_doc.close()
                bw_doc.close()

                orig_mb = len(src_bytes) / (1024 * 1024)
                new_mb = len(out_bytes) / (1024 * 1024)
                st.success(f"Done! Size changed from **{orig_mb:.2f} MB** to **{new_mb:.2f} MB**.")

                st.download_button(
                    label="⬇️ Download B&W PDF",
                    data=out_bytes,
                    file_name=f"bw_{uploaded_file.name}",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Conversion failed: {e}")


# =========================================================
# TOOL 4: COMPRESS PDF
# =========================================================
elif tool == "🗜️ Compress PDF":
    render_tool_header(
        "🗜️ Compress PDF",
        "Shrink large scanned or image-heavy PDFs for email attachments and portal uploads."
    )

    uploaded_file = st.file_uploader("Upload PDF to compress", type=["pdf"])
    level = st.select_slider(
        "Compression Strength",
        options=["Light (150 DPI)", "Balanced (110 DPI)", "Maximum (85 DPI)"],
        value="Balanced (110 DPI)"
    )

    dpi_map = {"Light (150 DPI)": 150, "Balanced (110 DPI)": 110, "Maximum (85 DPI)": 85}
    qual_map = {"Light (150 DPI)": 80, "Balanced (110 DPI)": 70, "Maximum (85 DPI)": 60}

    if uploaded_file and st.button("Compress PDF", type="primary"):
        with st.spinner("Compressing PDF..."):
            try:
                src_bytes = uploaded_file.read()
                src_doc = fitz.open(stream=src_bytes, filetype="pdf")
                comp_doc = fitz.open()

                target_dpi = dpi_map[level]
                target_qual = qual_map[level]

                for pno in range(src_doc.page_count):
                    page = src_doc.load_page(pno)
                    pix = page.get_pixmap(dpi=target_dpi)
                    new_page = comp_doc.new_page(width=page.rect.width, height=page.rect.height)
                    new_page.insert_image(
                        page.rect,
                        stream=pix.tobytes("jpeg", jpg_quality=target_qual)
                    )

                out_bytes = comp_doc.tobytes(garbage=4, deflate=True, clean=True, linear=True)
                src_doc.close()
                comp_doc.close()

                orig_mb = len(src_bytes) / (1024 * 1024)
                new_mb = len(out_bytes) / (1024 * 1024)
                reduction = max(0.0, (1 - new_mb / orig_mb) * 100) if orig_mb > 0 else 0

                st.success(f"Compressed from **{orig_mb:.2f} MB** → **{new_mb:.2f} MB** ({reduction:.0f}% smaller).")
                st.download_button(
                    label="⬇️ Download Compressed PDF",
                    data=out_bytes,
                    file_name=f"compressed_{uploaded_file.name}",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Compression failed: {e}")


# =========================================================
# TOOL 5: PDF TO WORD (.docx)
# =========================================================
elif tool == "📝 PDF to Word (.docx)":
    render_tool_header(
        "📝 Convert PDF to Word (.docx)",
        "Convert PDF text, paragraphs, and formatting into an editable Microsoft Word document."
    )

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file and st.button("Convert to Word", type="primary"):
        with st.spinner("Converting PDF to Word..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    tmp_pdf.write(uploaded_file.read())
                    tmp_pdf_path = tmp_pdf.name

                tmp_docx_path = tmp_pdf_path.replace(".pdf", ".docx")
                cv = Converter(tmp_pdf_path)
                cv.convert(tmp_docx_path, start=0, end=None)
                cv.close()

                with open(tmp_docx_path, "rb") as f:
                    docx_bytes = f.read()

                os.remove(tmp_pdf_path)
                os.remove(tmp_docx_path)

                st.success("Converted to Word successfully!")
                base_name = os.path.splitext(uploaded_file.name)[0]
                st.download_button(
                    label="⬇️ Download Word Document (.docx)",
                    data=docx_bytes,
                    file_name=f"{base_name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Word conversion failed: {e}")


# =========================================================
# TOOL 6: PDF TABLES TO EXCEL (.xlsx)
# =========================================================
elif tool == "📊 PDF Tables to Excel (.xlsx)":
    render_tool_header(
        "📊 Extract PDF Tables to Excel (.xlsx)",
        "Automatically detect structured tables inside a PDF and export each table to an Excel sheet."
    )

    uploaded_file = st.file_uploader("Upload PDF containing tables", type=["pdf"])
    flavor = st.radio(
        "Table Border Style",
        ["lattice (Tables with visible grid lines)", "stream (Tables separated by whitespace)"],
        horizontal=True
    )

    if uploaded_file and st.button("Extract Tables to Excel", type="primary"):
        with st.spinner("Scanning PDF for tables..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    tmp_pdf.write(uploaded_file.read())
                    tmp_pdf_path = tmp_pdf.name

                selected_flavor = "lattice" if flavor.startswith("lattice") else "stream"
                tables = camelot.read_pdf(tmp_pdf_path, pages="all", flavor=selected_flavor)
                os.remove(tmp_pdf_path)

                if not tables:
                    st.warning("No tables were detected. Try switching the Table Border Style above.")
                else:
                    excel_buf = io.BytesIO()
                    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                        for i, table in enumerate(tables):
                            table.df.to_excel(writer, sheet_name=f"Table_{i+1}", index=False)
                    excel_buf.seek(0)

                    st.success(f"Extracted **{len(tables)}** table(s)!")
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    st.download_button(
                        label="⬇️ Download Excel Workbook (.xlsx)",
                        data=excel_buf,
                        file_name=f"{base_name}_tables.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(f"Table extraction failed: {e}")


# =========================================================
# TOOL 7: EXTRACT IMAGES FROM PDF
# =========================================================
elif tool == "🖼️ Extract Images from PDF":
    render_tool_header(
        "🖼️ Extract Embedded Images from PDF",
        "Pull all embedded photos and graphics out of a PDF and download them as a single ZIP archive."
    )

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file and st.button("Extract Images", type="primary"):
        with st.spinner("Extracting embedded images..."):
            try:
                src_doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                zip_buf = io.BytesIO()
                images_found = 0

                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for page_num, page in enumerate(src_doc):
                        for img_idx, img in enumerate(page.get_images(full=True)):
                            xref = img[0]
                            base_img = src_doc.extract_image(xref)
                            img_bytes = base_img["image"]
                            img_ext = base_img["ext"]
                            zf.writestr(f"page{page_num+1}_img{img_idx+1}.{img_ext}", img_bytes)
                            images_found += 1

                src_doc.close()

                if images_found == 0:
                    st.info("No embedded images were found in this PDF.")
                else:
                    zip_buf.seek(0)
                    st.success(f"Extracted **{images_found}** images!")
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    st.download_button(
                        label="⬇️ Download Images (.zip)",
                        data=zip_buf,
                        file_name=f"{base_name}_images.zip",
                        mime="application/zip"
                    )
            except Exception as e:
                st.error(f"Image extraction failed: {e}")


# =========================================================
# TOOL 8: PASSPORT PHOTO STUDIO
# =========================================================
elif tool == "🪪 Passport Photo Studio":
    render_tool_header(
        "🪪 Passport & ID Photo Studio",
        "Crop and resize photos at 300 DPI for USA, India, or custom ID specs, with single or 4×6″ printable sheet layouts."
    )

    uploaded_photo = st.file_uploader(
        "Upload Portrait Photo",
        type=["jpg", "jpeg", "png", "webp", "bmp"]
    )

    col_cfg, col_prev = st.columns([1, 1], gap="large")

    with col_cfg:
        st.subheader("1. Choose Template")
        template = st.radio(
            "Country / Standard",
            [
                "USA Passport (2.0 × 2.0 in)",
                "India Passport / Visa (35 × 45 mm)",
                "Custom Dimensions"
            ]
        )

        if template.startswith("USA"):
            unit = "in"
            w_val, h_val = 2.0, 2.0
            tmpl_tag = "usa"
        elif template.startswith("India"):
            unit = "mm"
            w_val, h_val = 35.0, 45.0
            tmpl_tag = "india"
        else:
            tmpl_tag = "custom"
            c1, c2, c3 = st.columns(3)
            with c1:
                w_val = st.number_input("Width", min_value=5.0 if True else 0.5, value=35.0, step=1.0)
            with c2:
                h_val = st.number_input("Height", min_value=5.0 if True else 0.5, value=45.0, step=1.0)
            with c3:
                unit = st.selectbox("Unit", ["mm", "in"])

        layout = st.radio(
            "Output Format",
            [
                "4×6 inch Printable Sheet (Multiple copies + cut guides)",
                "Single Cropped Photo (For online portal upload)"
            ]
        )

        head_bias = st.slider(
            "Vertical Framing Adjustment (Top vs. Bottom)",
            min_value=0.0,
            max_value=1.0,
            value=0.25,
            step=0.05,
            help="0.0 keeps the top of the frame (headroom); 0.5 centers vertically."
        )

    if uploaded_photo:
        w_in = w_val if unit == "in" else w_val / 25.4
        h_in = h_val if unit == "in" else h_val / 25.4
        target_w = int(round(w_in * 300))
        target_h = int(round(h_in * 300))

        img = Image.open(uploaded_photo).convert("RGB")
        src_ratio = img.width / img.height
        target_ratio = target_w / target_h

        if src_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            left = (img.width - new_w) // 2
            cropped = img.crop((left, 0, left + new_w, img.height))
        else:
            new_h = int(img.width / target_ratio)
            top = int((img.height - new_h) * head_bias)
            cropped = img.crop((0, top, img.width, top + new_h))

        single_photo = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

        if layout.startswith("Single"):
            final_img = single_photo
            caption = f"Single Photo ({target_w} × {target_h} px @ 300 DPI)"
            file_suffix = "single"
        else:
            sheet_w, sheet_h = 1800, 1200  # 6x4 inches at 300 DPI
            gap = 30
            cols_land = max(1, (sheet_w - gap) // (target_w + gap))
            rows_land = max(1, (sheet_h - gap) // (target_h + gap))
            cols_port = max(1, (sheet_h - gap) // (target_w + gap))
            rows_port = max(1, (sheet_w - gap) // (target_h + gap))

            if (cols_port * rows_port) > (cols_land * rows_land):
                sheet_w, sheet_h = sheet_h, sheet_w
                cols, rows = cols_port, rows_port
            else:
                cols, rows = cols_land, rows_land

            sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
            draw = ImageDraw.Draw(sheet)

            total_grid_w = cols * target_w + (cols - 1) * gap
            total_grid_h = rows * target_h + (rows - 1) * gap
            start_x = (sheet_w - total_grid_w) // 2
            start_y = (sheet_h - total_grid_h) // 2

            count = 0
            for r in range(rows):
                for c in range(cols):
                    x = start_x + c * (target_w + gap)
                    y = start_y + r * (target_h + gap)
                    sheet.paste(single_photo, (x, y))
                    draw.rectangle(
                        [x - 1, y - 1, x + target_w, y + target_h],
                        outline="#cbd5e1",
                        width=2
                    )
                    count += 1

            final_img = sheet
            caption = f"4×6″ Print Sheet ({count} copies @ 300 DPI)"
            file_suffix = "4x6_sheet"

        with col_prev:
            st.subheader("2. Live Preview & Download")
            st.image(final_img, caption=caption, use_container_width=True)

            out_buf = io.BytesIO()
            final_img.save(out_buf, format="JPEG", dpi=(300, 300), quality=95)
            out_buf.seek(0)

            st.download_button(
                label="⬇️ Download Print-Ready JPEG",
                data=out_buf,
                file_name=f"passport_{tmpl_tag}_{file_suffix}.jpg",
                mime="image/jpeg",
                type="primary"
            )