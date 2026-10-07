import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # Blank slide

    # Color Palette Definitions
    NAVY = RGBColor(15, 23, 42)          # #0F172A Dark Slate Navy
    NAVY_LIGHT = RGBColor(30, 41, 59)    # #1E293B
    BLUE_ACCENT = RGBColor(37, 99, 235)  # #2563EB Primary Blue
    CYAN_ACCENT = RGBColor(14, 165, 233) # #0EA5E9 Vivid Cyan
    EMERALD = RGBColor(16, 185, 129)     # #10B981 Success Green
    ROSE = RGBColor(225, 29, 72)         # #E11D48 Alert Red
    AMBER = RGBColor(217, 119, 6)        # #D97706 Warning Orange
    BG_LIGHT = RGBColor(248, 250, 252)   # #F8FAFC Clean Off-white
    CARD_BG = RGBColor(255, 255, 255)    # Pure White
    TEXT_DARK = RGBColor(15, 23, 42)     # #0F172A Body text
    TEXT_MUTED = RGBColor(100, 116, 139) # #64748B Secondary text
    WHITE = RGBColor(255, 255, 255)

    def add_header(slide, title_text, category_tag="PROJECT PRESENTATION"):
        # Top banner background
        header_shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.15)
        )
        header_shape.fill.solid()
        header_shape.fill.fore_color.rgb = NAVY
        header_shape.line.color.rgb = NAVY

        # Small cyan category badge
        tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(11.5), Inches(0.3))
        tf = tx_box.text_frame
        tf.word_wrap = True
        p_tag = tf.paragraphs[0]
        p_tag.text = category_tag.upper()
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = CYAN_ACCENT

        # Title text
        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE

    def set_slide_bg(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.color.rgb = color
        return bg

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=None):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # -------------------------------------------------------------
    # SLIDE 1: TITLE SLIDE (Dark Navy Premium Theme)
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s1, NAVY)

    # Decorative Cyan Line
    dec = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.2), Inches(1.5), Inches(0.08))
    dec.fill.solid()
    dec.fill.fore_color.rgb = CYAN_ACCENT
    dec.line.fill.background()

    # Title & Subtitle Box
    tbox = s1.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(11.3), Inches(4.2))
    tf1 = tbox.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "RESEARCH & ENGINEERING PRESENTATION"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = CYAN_ACCENT

    p1 = tf1.add_paragraph()
    p1.text = "ZK-CaMBio"
    p1.font.size = Pt(40)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_after = Pt(10)

    p2 = tf1.add_paragraph()
    p2.text = "Privacy-Preserving Multimodal Biometric Authentication\nUsing Cancelable Chaotic Templates"
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = RGBColor(226, 232, 240)
    p2.space_after = Pt(18)

    p3 = tf1.add_paragraph()
    p3.text = "Solving Biometric Identity Theft • Face & Fingerprint Feature Fusion • 1.29% EER Accuracy • Provable ISO/IEC 30136 Revocability"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(148, 163, 184)

    # 3 Summary Badge Cards at the bottom of Title Slide
    badges = [
        ("MULTIMODAL FUSION", "FaceNet (512-d) + FingerResNet (256-d)", BLUE_ACCENT),
        ("HIGH ACCURACY", "1.29% Equal Error Rate (98.81% Rank-1)", EMERALD),
        ("ZERO-KNOWLEDGE PRIVACY", "Zero Raw Biometrics Stored in DB", CYAN_ACCENT),
    ]
    for i, (b_title, b_desc, b_col) in enumerate(badges):
        b_left = Inches(1.0 + i * 3.85)
        card = add_card(s1, b_left, Inches(5.6), Inches(3.6), Inches(1.3), bg_color=NAVY_LIGHT, border_color=b_col)
        tx = s1.shapes.add_textbox(b_left + Inches(0.2), Inches(5.7), Inches(3.2), Inches(1.1))
        tf = tx.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = b_title
        pt.font.size = Pt(11)
        pt.font.bold = True
        pt.font.color.rgb = b_col
        pd = tf.add_paragraph()
        pd.text = b_desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = WHITE

    s1.notes_slide.notes_text_frame.text = (
        "WELCOME AND INTRODUCTORY REMARKS:\n\n"
        "Good morning/afternoon everyone. Today, I am presenting ZK-CaMBio, an advanced privacy-preserving "
        "multimodal biometric authentication system.\n\n"
        "In simple terms, biometrics like our face and fingerprints are widely used for security, but they suffer "
        "from a major vulnerability: once your face or fingerprint data is stolen or leaked from a database, "
        "you can never change it. You cannot reset your face or change your fingerprints.\n\n"
        "ZK-CaMBio completely solves this problem. It fuses facial recognition and fingerprint scanning, converts "
        "them into scrambled, cancelable 512-bit binary codes using chaotic mathematics, and ensures that the server "
        "never stores any raw biometric images or templates. If a template is ever stolen, it can be instantly revoked "
        "and replaced with a fresh one without losing high accuracy."
    )

    # -------------------------------------------------------------
    # SLIDE 2: THE PROBLEM (Why Traditional Biometrics Are Dangerous)
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2, BG_LIGHT)
    add_header(s2, "The Core Problem: Why Traditional Biometrics Are High-Risk", "PROBLEM STATEMENT")

    # Left Column: Problems
    left_card = add_card(s2, Inches(0.8), Inches(1.4), Inches(5.6), Inches(5.6), CARD_BG)
    tx = s2.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(5.2), Inches(5.3))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "The Permanence Vulnerability"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ROSE
    p.space_after = Pt(8)

    points = [
        ("Biometrics Cannot Be Reset:", "If your password is stolen, you change it in 10 seconds. But if your face or fingerprint template is leaked, you are permanently compromised for life."),
        ("Cross-Service Tracking:", "If you use your face to unlock your phone, your bank, and your office, a leaked database allows malicious actors to link and track your identity across all services."),
        ("Single-Modality Weaknesses:", "A single biometric trait often fails: fingerprints get smudged or dry, and face recognition struggles under low light, leading to high false rejections.")
    ]
    for title, desc in points:
        pt = tf.add_paragraph()
        pt.text = "• " + title + " "
        pt.font.bold = True
        pt.font.size = Pt(13)
        pt.font.color.rgb = TEXT_DARK
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = TEXT_MUTED
        pd.space_after = Pt(10)

    # Right Column: The Comparison Card
    right_card = add_card(s2, Inches(6.8), Inches(1.4), Inches(5.7), Inches(5.6), CARD_BG)
    tx2 = s2.shapes.add_textbox(Inches(7.0), Inches(1.5), Inches(5.3), Inches(5.3))
    tf2 = tx2.text_frame
    tf2.word_wrap = True

    p = tf2.paragraphs[0]
    p.text = "Passwords vs. Traditional Biometrics"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p.space_after = Pt(12)

    rows = [
        ("Credential Type", "Random digital strings", "Your physical body traits"),
        ("Revocability", "Instant re-issuance", "Biologically impossible"),
        ("Cross-Service Salt", "Unique hash per service", "Same face & finger everywhere"),
        ("Data Breach Risk", "Change password, risk ends", "Permanent identity compromise")
    ]
    for criterion, pwd, bio in rows:
        p_row = tf2.add_paragraph()
        p_row.text = f"{criterion}:"
        p_row.font.bold = True
        p_row.font.size = Pt(12)
        p_row.font.color.rgb = NAVY_LIGHT

        p_desc = tf2.add_paragraph()
        p_desc.text = f"  • Password: {pwd}\n  • Biometric: {bio}"
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = TEXT_MUTED
        p_desc.space_after = Pt(8)

    s2.notes_slide.notes_text_frame.text = (
        "SLIDE 2 SPEAKER NOTES:\n\n"
        "Let's understand the core problem this project solves.\n\n"
        "When we use passwords or PIN numbers, if someone hacks the server and steals the password, "
        "it's bad, but it's easily fixable: the user simply changes their password.\n\n"
        "However, with biometrics, your face, fingerprint, or iris is permanently tied to your body. "
        "If a hospital, an employer, or a government database gets hacked, your biometric features are leaked forever. "
        "You cannot go to a clinic and get a new set of fingerprints or a new face.\n\n"
        "Furthermore, unimodal systems—using only face or only fingerprint—often struggle. A fingerprint sensor "
        "gets dirty, or lighting changes for face recognition, causing false rejections.\n\n"
        "Therefore, modern biometrics desperately needs two things: multimodal fusion for high accuracy, "
        "and cancelable templates so that credentials can be revoked and re-issued just like passwords."
    )

    # -------------------------------------------------------------
    # SLIDE 3: OUR SOLUTION (ZK-CaMBio Core Architecture)
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3, BG_LIGHT)
    add_header(s3, "What Problems Does ZK-CaMBio Solve & How?", "PROPOSED SOLUTION")

    cards_data = [
        ("1. Multimodal Fusion", "Solves Single-Sensor Failures",
         "Combines deep facial features and convolutional fingerprint features at the feature level.\n\n"
         "• Face weight = 0.60, Fingerprint = 0.40.\n"
         "• Creates a unified 768-dimensional unit-norm vector that makes authentication far more accurate than any single trait.",
         BLUE_ACCENT, Inches(0.8)),
        ("2. Cancelable Chaotic Projection", "Solves Permanent Leaks",
         "Transforms continuous biometrics into a 512-bit binary template using a key-dependent chaotic logistic map.\n\n"
         "• If stolen, the key is revoked and changed.\n"
         "• A new, completely different template is generated from the exact same face and fingerprint without re-sampling.",
         CYAN_ACCENT, Inches(4.8)),
        ("3. 'Zero-Knowledge' Privacy", "Solves Server Data Breaches",
         "Guarantees data-at-rest structural privacy on the server:\n\n"
         "• ZERO raw face photos or fingerprint images stored.\n"
         "• ZERO continuous floating-point embeddings stored.\n"
         "• The database stores ONLY a 64-byte scrambled binary bitstring.",
         EMERALD, Inches(8.8)),
    ]

    for title, subtitle, content, color, left_pos in cards_data:
        add_card(s3, left_pos, Inches(1.4), Inches(3.7), Inches(5.6), CARD_BG, border_color=color)
        tx = s3.shapes.add_textbox(left_pos + Inches(0.2), Inches(1.6), Inches(3.3), Inches(5.2))
        tf = tx.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(16)
        p1.font.bold = True
        p1.font.color.rgb = color
        p1.space_after = Pt(4)

        p2 = tf.add_paragraph()
        p2.text = subtitle.upper()
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_MUTED
        p2.space_after = Pt(14)

        p3 = tf.add_paragraph()
        p3.text = content
        p3.font.size = Pt(12)
        p3.font.color.rgb = TEXT_DARK

    s3.notes_slide.notes_text_frame.text = (
        "SLIDE 3 SPEAKER NOTES:\n\n"
        "Here is the solution we built: ZK-CaMBio.\n\n"
        "It is built on three major pillars:\n"
        "First: Multimodal Fusion. We don't rely on just a face or just a finger. We extract deep features from both "
        "and combine them into a single 768-dimensional vector. This solves false rejections and gives extreme accuracy.\n\n"
        "Second: Cancelable Chaotic Projection. We use a deterministic mathematical chaotic map parameterized by a user's secret key. "
        "It projects the combined biometric features into a 512-bit binary code (which is only 64 bytes). "
        "If a template is ever compromised, we simply rotate the key and re-enroll. The old template is immediately useless, "
        "and the new template is completely unlinkable.\n\n"
        "Third: Zero-Knowledge Data-at-Rest. We formally define zero-knowledge in this project as a structural storage guarantee: "
        "the authentication server never saves raw pictures, never saves unquantized floating-point vectors, and under user-secret mode, "
        "never stores passphrases. Even if an attacker steals the entire database, all they get are scrambled 64-byte bitstrings."
    )

    # -------------------------------------------------------------
    # SLIDE 4: TECHNOLOGY STACK (What Did We Use?)
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s4, BG_LIGHT)
    add_header(s4, "Technology Stack: Models, Cryptography & Systems", "WHAT DID WE USE?")

    tech_boxes = [
        ("Face Recognition", "InceptionResnetV1 (FaceNet)",
         "• Pretrained on VGGFace2 (3.31M images)\n• Input: 160x160 face crops\n• Output: 512-dimensional L2-normalized deep embedding vector", BLUE_ACCENT),
        ("Fingerprint Recognition", "Custom FingerResNet18 V2",
         "• ResNet-18 adapted for single-channel 128x128 impressions\n• Fine-tuned using CosFace large-margin loss\n• Output: 256-dimensional L2-normalized vector", CYAN_ACCENT),
        ("Multimodal Fusion", "Weighted Feature Concatenation",
         "• Formula: [sqrt(0.60)*Face, sqrt(0.40)*Finger]\n• Produces a 768-dimensional unit-norm vector\n• Mathematically preserves unit length (||x||=1)", EMERALD),
        ("Chaotic Engine (C++17)", "Fixed-Point Logistic Map",
         "• Q64 fixed-point math (zero floating-point divergence)\n• Compiled with -ffp-contract=off for 100% bit-exact Windows/Linux matching\n• Generates 512x768 random matrix from user key", NAVY_LIGHT),
        ("Key Derivation", "scrypt + HMAC-SHA256",
         "• scrypt memory-hard key stretching (N=16384, r=8, p=1)\n• Binds user ID, salt, and version into HMAC-SHA256 seed\n• Effective keyspace >= 2^126 operations", AMBER),
        ("Production Backend", "FastAPI + PostgreSQL + Streamlit",
         "• REST API endpoints: /enroll, /verify, /identify, /revoke\n• PostgreSQL 16 Alpine with BYTEA(64) templates\n• Air-gapped Streamlit web UI + multi-stage Docker", NAVY)
    ]

    for i, (cat, title, desc, col) in enumerate(tech_boxes):
        row = i // 3
        col_idx = i % 3
        x = Inches(0.8 + col_idx * 4.0)
        y = Inches(1.4 + row * 2.85)

        add_card(s4, x, y, Inches(3.8), Inches(2.65), CARD_BG, border_color=col)
        tx = s4.shapes.add_textbox(x + Inches(0.15), y + Inches(0.15), Inches(3.5), Inches(2.35))
        tf = tx.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = cat.upper()
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.size = Pt(14)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_DARK
        p2.space_after = Pt(6)

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.size = Pt(11)
        p3.font.color.rgb = TEXT_MUTED

    s4.notes_slide.notes_text_frame.text = (
        "SLIDE 4 SPEAKER NOTES:\n\n"
        "Now let's examine what technologies and models we used in this project:\n\n"
        "1. For facial feature extraction: We used InceptionResnetV1 (FaceNet) pretrained on the VGGFace2 dataset, "
        "which converts a 160x160 face crop into a 512-dimensional continuous feature vector.\n\n"
        "2. For fingerprints: Off-the-shelf Gabor filters fail on noisy images, so we built FingerResNet18 V2, "
        "fine-tuned with CosFace margin loss to extract clean 256-dimensional fingerprint embeddings.\n\n"
        "3. For fusion: We use weighted concatenation with square root weights (0.60 for face, 0.40 for finger). "
        "This produces a 768-dimensional combined vector that mathematically maintains unit length.\n\n"
        "4. For the chaotic engine: We wrote a custom C++17 engine bound to Python using pybind11. "
        "We used 64-bit integer fixed-point math and disabled compiler fused-multiply-add (-ffp-contract=off). "
        "This guarantees that the exact same bitstring is calculated whether running on Windows MSVC or a Linux Docker container.\n\n"
        "5. For cryptography: We use scrypt for memory-hard passphrase stretching and HMAC-SHA256 with per-user salts.\n\n"
        "6. For deployment: A FastAPI REST backend, PostgreSQL database, Docker containerization, and an interactive Streamlit UI."
    )

    # -------------------------------------------------------------
    # SLIDE 5: DATABASE DETAILS (Datasets, Images, Classes, Pairing)
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s5, BG_LIGHT)
    add_header(s5, "Database Breakdown: Corpora, Images & Subject Pairing", "DATASET & EXPERIMENTAL SETUP")

    # Left Column: Detailed stats
    add_card(s5, Inches(0.8), Inches(1.4), Inches(5.8), Inches(5.6), CARD_BG)
    tx = s5.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(5.4), Inches(5.3))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "How Was the Database Constructed?"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p.space_after = Pt(8)

    db_details = [
        ("Face Database (UMDFaces):", "367,888 total images across 8,277 identity folders. We selected identities with >= 20 high-quality images (7,173 eligible classes), and randomly sampled 300 identities using fixed seed 42."),
        ("Fingerprint Database (FVC2004):", "DB1_A (optical 500 dpi), DB2_A (optical 569 dpi), DB3_A (thermal sweep 512 dpi). Exactly 100 fingers per DB x 8 impressions = 2,400 raw images across 300 fingers. (Plus DB4_A synthetic and DB*_B for pretraining)."),
        ("Virtual Chimeric Pairing:", "Because no freely downloadable paired face+fingerprint dataset exists with open research rights, face identity k was paired with fingerprint k using seed 42, creating 300 Virtual Subjects (VS_0001 to VS_0300)."),
        ("Images Used Per Subject:", "Exactly 5 enrollment images (averaged to create gallery template) and 3 probe images (for genuine testing) = 8 images per subject (2,400 faces and 2,400 fingerprints used).")
    ]
    for title, desc in db_details:
        pt = tf.add_paragraph()
        pt.text = "• " + title
        pt.font.bold = True
        pt.font.size = Pt(12)
        pt.font.color.rgb = TEXT_DARK
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_MUTED
        pd.space_after = Pt(6)

    # Right Column: Visual Preprocessing / Sample Card
    add_card(s5, Inches(6.8), Inches(1.4), Inches(5.7), Inches(5.6), CARD_BG)
    tx2 = s5.shapes.add_textbox(Inches(7.0), Inches(1.5), Inches(5.3), Inches(1.2))
    tf2 = tx2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Fingerprint Sensor Enhancement (FVC2004)"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = NAVY_LIGHT
    p2_sub = tf2.add_paragraph()
    p2_sub.text = "Raw impressions enhanced via 4-stage CLAHE & foreground segmentation:"
    p2_sub.font.size = Pt(11)
    p2_sub.font.color.rgb = TEXT_MUTED

    # Insert Image: finger_preproc_check.png or face_folder_check.png
    img_path = r"D:\Biometric Project\results\face_folder_check.png"
    if os.path.exists(img_path):
        s5.shapes.add_picture(img_path, Inches(7.0), Inches(2.7), width=Inches(5.3))

    s5.notes_slide.notes_text_frame.text = (
        "SLIDE 5 SPEAKER NOTES:\n\n"
        "Here are the exact details of the dataset and how the database was built:\n\n"
        "1. For the face modality, we used UMDFaces, which contains 367,888 images across 8,277 identity folders. "
        "We filtered for subjects with at least 20 images to avoid label noise, leaving 7,173 eligible identities. "
        "We then sorted and sampled 300 identities using fixed seed 42.\n\n"
        "2. For fingerprints, we used the international benchmark FVC2004 across 3 real sensors: DB1 (optical), "
        "DB2 (optical), and DB3 (thermal sweep). Each sensor has 100 fingers with 8 impressions each, giving 2,400 raw images.\n\n"
        "3. Chimeric Pairing: In biometric literature, because privacy laws prevent freely releasing public paired datasets "
        "with both faces and fingerprints from the same real people, we followed the standard accepted research protocol: "
        "pairing face subject k with fingerprint k to create 300 Virtual Subjects.\n\n"
        "4. Per subject, we use 5 images for enrollment and 3 separate images for probe queries. "
        "That's 8 images per subject, or 2,400 face images and 2,400 fingerprint impressions evaluated in total."
    )

    # -------------------------------------------------------------
    # SLIDE 6: DATASET PARTITIONING (Train, Val, Test & Protocol D-009)
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s6, BG_LIGHT)
    add_header(s6, "Subject-Disjoint Splits & Protocol D-009", "DATASET PARTITIONING")

    # 3 Split Cards Across Top
    splits = [
        ("Training Split (60%)", "180 Virtual Subjects (1,440 images/modality)",
         "• Used to fine-tune FingerResNet18 encoder\n• Computes public centering vector mu\n• Trains adversarial reconstruction attack decoders\n• Zero test-subject data ever seen", BLUE_ACCENT, Inches(0.8)),
        ("Validation Split (10%)", "30 Virtual Subjects (240 images/modality)",
         "• Calibrates modality fusion weight w = 0.60\n• Selects projection dimension m = 512 bits\n• Tunes enrollment quality gates (0.45 / 0.60)\n• Sets operational decision thresholds (tau)", AMBER, Inches(4.8)),
        ("Test Split (40%)", "120 Virtual Subjects (960 images/modality)",
         "• STRICTLY HELD-OUT evaluation set\n• 40 subjects per fingerprint sensor database\n• All reported EER, ROC, CMC & Security metrics evaluated exclusively on this set", EMERALD, Inches(8.8)),
    ]

    for title, sub, content, col, left_pos in splits:
        add_card(s6, left_pos, Inches(1.4), Inches(3.7), Inches(2.7), CARD_BG, border_color=col)
        tx = s6.shapes.add_textbox(left_pos + Inches(0.15), Inches(1.5), Inches(3.4), Inches(2.5))
        tf = tx.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_MUTED
        p2.space_after = Pt(8)

        p3 = tf.add_paragraph()
        p3.text = content
        p3.font.size = Pt(11)
        p3.font.color.rgb = TEXT_DARK

    # Bottom Banner: Protocol D-009 Rigorous Impostor Matching
    add_card(s6, Inches(0.8), Inches(4.3), Inches(11.7), Inches(2.7), CARD_BG, border_color=NAVY)
    tx = s6.shapes.add_textbox(Inches(1.1), Inches(4.45), Inches(11.1), Inches(2.4))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "How Did We Identify Users? Protocol D-009 (Within-Sensor Impostors)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(6)

    proto_points = [
        "Rigorous Sensor Stratification: 120 test subjects are divided equally: 40 on DB1 (optical), 40 on DB2 (optical), and 40 on DB3 (thermal sweep).",
        "Within-Sensor Impostor Constraint: Cross-matching an optical sensor against a thermal sensor gives artificially easy impostor scores. To prevent fake inflated accuracy, impostor comparisons were strictly restricted to the SAME sensor database.",
        "Total Test Comparisons: Each of the 40 gallery subjects is compared against 3 probe impressions of the 39 other subjects: 40 x 39 x 3 = 4,680 impostors per database x 3 databases = 14,040 rigorous impostor comparisons, and 120 subjects x 3 probes = 360 genuine trials.",
        "Split Manifest Integrity: Cryptographically hashed to SHA-256 (a3454a7c...) in data/processed/split_manifest.json to ensure 100% scientific reproducibility."
    ]
    for pt_text in proto_points:
        p_item = tf.add_paragraph()
        p_item.text = "• " + pt_text
        p_item.font.size = Pt(11)
        p_item.font.color.rgb = TEXT_DARK
        p_item.space_after = Pt(3)

    s6.notes_slide.notes_text_frame.text = (
        "SLIDE 6 SPEAKER NOTES:\n\n"
        "How did we partition the data and identify people without data leakage?\n\n"
        "1. We strictly separated our 300 virtual subjects into three subject-disjoint groups:\n"
        "   - 180 subjects (60%) for training the fingerprint model and attack decoders.\n"
        "   - 30 subjects (10%) for validation (tuning fusion weights and selecting projection size m).\n"
        "   - 120 subjects (40%) for our final test evaluation. No test data was ever used in training!\n\n"
        "2. Crucially, we implemented Protocol D-009 for identification:\n"
        "   In fingerprint testing, comparing a thermal scanner to an optical scanner is too easy because the sensor styles look different. "
        "   To avoid cheating ourselves with artificially inflated accuracy, we restricted all impostor comparisons strictly to the SAME sensor database. "
        "   That gave us 14,040 impostor comparisons and 360 genuine test trials across our 120 test subjects."
    )

    # -------------------------------------------------------------
    # SLIDE 7: UNPROTECTED ACCURACY (Face vs Finger vs Multimodal Fusion)
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s7, BG_LIGHT)
    add_header(s7, "Unprotected Baseline: Multimodal Fusion Accuracy", "BASELINE ACCURACY RESULTS")

    # Left Column: Metrics Table & Explanations
    add_card(s7, Inches(0.8), Inches(1.4), Inches(5.8), Inches(5.6), CARD_BG)
    tx = s7.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(5.4), Inches(5.3))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Unprotected Recognition Metrics (120 Test Subjects)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p.space_after = Pt(8)

    results_table = [
        ("S1: Face Only (512-d)", "EER = 2.00%", "Rank-1 = 97.22%", "d' = 4.78", "FNMR@1% = 3.33%"),
        ("S2: Finger Only (256-d)", "EER = 5.81%", "Rank-1 = 78.89%", "d' = 3.42", "FNMR@1% = 26.67%"),
        ("S3: Fused System (768-d)", "EER = 1.11%", "Rank-1 = 99.44%", "d' = 5.91", "FNMR@1% = 1.11%"),
    ]
    for sys_name, eer, r1, dp, fnmr in results_table:
        p_sys = tf.add_paragraph()
        p_sys.text = sys_name
        p_sys.font.bold = True
        p_sys.font.size = Pt(13)
        p_sys.font.color.rgb = NAVY if "Fused" not in sys_name else EMERALD
        p_stat = tf.add_paragraph()
        p_stat.text = f"  • {eer}  |  {r1}\n  • Decidability: {dp}  |  {fnmr}"
        p_stat.font.size = Pt(11)
        p_stat.font.color.rgb = TEXT_MUTED
        p_stat.space_after = Pt(6)

    p_takeaway = tf.add_paragraph()
    p_takeaway.text = "Key Takeaway in Simple Terms:"
    p_takeaway.font.bold = True
    p_takeaway.font.size = Pt(13)
    p_takeaway.font.color.rgb = BLUE_ACCENT
    p_t_desc = tf.add_paragraph()
    p_t_desc.text = (
        "Combining face and fingerprint reduces the error rate from 2.00% down to 1.11%—a 44.5% error reduction! "
        "Rank-1 identification reaches near-perfection at 99.44% across 40-subject galleries."
    )
    p_t_desc.font.size = Pt(11)
    p_t_desc.font.color.rgb = TEXT_DARK

    # Right Column: fusion_roc.png
    add_card(s7, Inches(6.8), Inches(1.4), Inches(5.7), Inches(5.6), CARD_BG)
    img_path = r"D:\Biometric Project\results\fusion_roc.png"
    if os.path.exists(img_path):
        s7.shapes.add_picture(img_path, Inches(7.0), Inches(1.7), width=Inches(5.3))
    caption = s7.shapes.add_textbox(Inches(7.0), Inches(6.2), Inches(5.3), Inches(0.6))
    caption.text_frame.word_wrap = True
    p_cap = caption.text_frame.paragraphs[0]
    p_cap.text = "Figure: ROC Curves showing Fused System S3 (green) pushing curve tightly toward top-left."
    p_cap.font.size = Pt(10)
    p_cap.font.color.rgb = TEXT_MUTED

    s7.notes_slide.notes_text_frame.text = (
        "SLIDE 7 SPEAKER NOTES:\n\n"
        "Here are the baseline accuracy results before applying any cancelable protection:\n\n"
        "1. Face recognition alone achieves an Equal Error Rate (EER) of 2.00%, with a Rank-1 identification accuracy of 97.22%.\n"
        "2. Fingerprint recognition alone achieves an EER of 5.81%, with Rank-1 accuracy of 78.89%.\n"
        "3. When we fuse them together at the feature level (weighting 0.60 for face, 0.40 for finger), our error rate drops to just 1.11%, "
        "and our Rank-1 identification surges to 99.44%!\n\n"
        "This proves that multimodal fusion significantly outperforms any single biometric modality. "
        "Now, the big question is: when we convert this fused vector into a scrambled cancelable binary code, do we lose this accuracy?"
    )

    # -------------------------------------------------------------
    # SLIDE 8: CANCELABLE ACCURACY (Performance Preservation)
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s8, BG_LIGHT)
    add_header(s8, "Cancelable Biometric Accuracy: Performance Preservation", "CANCELABLE ACCURACY FINDINGS")

    # Left Column: Real Numbers & Bootstrap
    add_card(s8, Inches(0.8), Inches(1.4), Inches(5.8), Inches(5.6), CARD_BG)
    tx = s8.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(5.4), Inches(5.3))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Scenario K (Operational / Stolen-Key Case)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = EMERALD
    p.space_after = Pt(8)

    scen_k_points = [
        ("Cancelable EER (m = 512 bits):", "1.29% ± 0.23% (tested across 10 random master keys)"),
        ("Unprotected Baseline EER:", "1.11% ± 0.22% (Delta EER = only +0.213%)"),
        ("Paired Bootstrap Test (1,000 resamples):", "95% Confidence Interval: [-0.135%, +0.688%]. Because 0 is included, the slight difference is STATISTICALLY ZERO (p > 0.05)!"),
        ("Decidability Index (d'):", "5.29 (extremely clean separation between genuine and impostor)"),
        ("Rank-1 Identification Accuracy:", "98.81% ± 0.31% (Rank-3 reaches 100.00%)"),
        ("Scenario U (Attacker uses wrong key):", "EER = 0.0000% (Hamming distance = 0.50, perfect random separation)")
    ]
    for title, desc in scen_k_points:
        pt = tf.add_paragraph()
        pt.text = "• " + title + " "
        pt.font.bold = True
        pt.font.size = Pt(12)
        pt.font.color.rgb = TEXT_DARK
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_MUTED
        pd.space_after = Pt(5)

    # Right Column: cancelable_roc.png
    add_card(s8, Inches(6.8), Inches(1.4), Inches(5.7), Inches(5.6), CARD_BG)
    img_path = r"D:\Biometric Project\results\cancelable_roc.png"
    if os.path.exists(img_path):
        s8.shapes.add_picture(img_path, Inches(7.0), Inches(1.6), width=Inches(5.3))
    caption = s8.shapes.add_textbox(Inches(7.0), Inches(6.2), Inches(5.3), Inches(0.6))
    caption.text_frame.word_wrap = True
    p_cap = caption.text_frame.paragraphs[0]
    p_cap.text = "Figure: ROC Curves showing cancelable Scenario K closely tracking unprotected baseline S3."
    p_cap.font.size = Pt(10)
    p_cap.font.color.rgb = TEXT_MUTED

    s8.notes_slide.notes_text_frame.text = (
        "SLIDE 8 SPEAKER NOTES:\n\n"
        "This slide presents one of the most important findings of our research: Performance Preservation.\n\n"
        "Historically, many cancelable biometric schemes ruined accuracy when scrambling the template. "
        "In our system, under Scenario K (which evaluates the biometric accuracy using the same key):\n\n"
        "- The cancelable template achieves an EER of 1.29% ± 0.23%.\n"
        "- The unprotected baseline had an EER of 1.11%.\n"
        "- The difference is only +0.21%.\n\n"
        "We ran a rigorous 1,000-iteration paired bootstrap test. The 95% confidence interval spans from -0.135% to +0.688%. "
        "Because zero is inside this interval, the null hypothesis is retained: the difference is NOT statistically significant!\n\n"
        "In simple words: We get full privacy and revocability at zero practical cost to biometric recognition accuracy."
    )

    # -------------------------------------------------------------
    # SLIDE 9: 1:N IDENTIFICATION (CMC Analysis)
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s9, BG_LIGHT)
    add_header(s9, "1:N Identification Accuracy: Finding Users in a Database", "IDENTIFICATION PERFORMANCE")

    # Left Column: CMC Numbers
    add_card(s9, Inches(0.8), Inches(1.4), Inches(5.8), Inches(5.6), CARD_BG)
    tx = s9.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(5.4), Inches(5.3))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Cumulative Match Characteristic (CMC) Analysis"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p.space_after = Pt(8)

    cmc_stats = [
        ("DB1_A Gallery (Optical 500 dpi):", "Rank-1 Accuracy = 98.42%"),
        ("DB2_A Gallery (Optical 569 dpi):", "Rank-1 Accuracy = 98.00%"),
        ("DB3_A Gallery (Thermal Sweep 512 dpi):", "Rank-1 Accuracy = 100.00%"),
        ("Overall Pooled Rank-1 Accuracy:", "98.81% ± 0.31% (across 10 random keys)"),
        ("Rank-3 Accuracy:", "100.00% across all galleries and sensors"),
        ("How 1:N Search Works:", "A probe image is projected using the server's key, and its 512-bit template is compared against all enrolled templates in the database using fast bitwise XOR (Hamming distance). The closest match is identified in under 1 millisecond!")
    ]
    for title, desc in cmc_stats:
        pt = tf.add_paragraph()
        pt.text = "• " + title
        pt.font.bold = True
        pt.font.size = Pt(12)
        pt.font.color.rgb = TEXT_DARK
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_MUTED
        pd.space_after = Pt(6)

    # Right Column: cancelable_cmc.png
    add_card(s9, Inches(6.8), Inches(1.4), Inches(5.7), Inches(5.6), CARD_BG)
    img_path = r"D:\Biometric Project\results\cancelable_cmc.png"
    if os.path.exists(img_path):
        s9.shapes.add_picture(img_path, Inches(7.0), Inches(1.6), width=Inches(5.3))
    caption = s9.shapes.add_textbox(Inches(7.0), Inches(6.2), Inches(5.3), Inches(0.6))
    caption.text_frame.word_wrap = True
    p_cap = caption.text_frame.paragraphs[0]
    p_cap.text = "Figure: CMC curves showing Rank-1 reaching 98.81% and Rank-3 reaching 100.00%."
    p_cap.font.size = Pt(10)
    p_cap.font.color.rgb = TEXT_MUTED

    s9.notes_slide.notes_text_frame.text = (
        "SLIDE 9 SPEAKER NOTES:\n\n"
        "In real-world applications, systems don't just verify 1-to-1 ('Are you Alice?'); they also identify 1-to-N ('Who are you in this database?').\n\n"
        "Here are our 1:N identification results:\n"
        "- Across our 40-subject gallery per sensor, DB1 achieves 98.42% Rank-1 accuracy.\n"
        "- DB2 achieves 98.00% Rank-1 accuracy.\n"
        "- DB3 (the thermal sweep sensor) achieves a perfect 100.00% Rank-1 accuracy.\n"
        "- Our overall pooled Rank-1 accuracy is 98.81% ± 0.31%, and by Rank-3, accuracy is exactly 100.00%.\n\n"
        "Because templates are compact 512-bit arrays, searching through a database requires only fast CPU bitwise XOR instructions. "
        "It takes less than 1 millisecond per query."
    )

    # -------------------------------------------------------------
    # SLIDE 10: REVOCABILITY & UNLINKABILITY (ISO/IEC 30136 Compliance)
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s10, BG_LIGHT)
    add_header(s10, "ISO/IEC 30136 Compliance: Revocability & Unlinkability", "STANDARDS COMPLIANCE")

    # Left Column: Revocability
    add_card(s10, Inches(0.8), Inches(1.4), Inches(5.7), Inches(5.6), CARD_BG, border_color=EMERALD)
    tx = s10.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(5.3), Inches(5.3))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "1. Template Revocability"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = EMERALD
    p.space_after = Pt(4)

    p_sub = tf.add_paragraph()
    p_sub.text = "Can we cancel a compromised credential?"
    p_sub.font.size = Pt(11)
    p_sub.font.bold = True
    p_sub.font.color.rgb = TEXT_MUTED
    p_sub.space_after = Pt(8)

    rev_points = [
        ("100.00% Rejection of Revoked Key:", "Presenting a probe with the old revoked key against the renewed template results in a 100.00% False Non-Match Rate (FNMR = 100.00% rejection across both operating thresholds)."),
        ("Genuine Recognition Restored:", "Re-enrolling with a new key version completely restores genuine recognition: FNMR = 1.67% at operating threshold."),
        ("No Trait Burnout:", "The user enrolls the exact same face and fingerprint, but receives a fresh, valid credential.")
    ]
    for t, d in rev_points:
        pt = tf.add_paragraph()
        pt.text = "• " + t
        pt.font.bold = True
        pt.font.size = Pt(11)
        pt.font.color.rgb = TEXT_DARK
        pd = tf.add_paragraph()
        pd.text = d
        pd.font.size = Pt(10)
        pd.font.color.rgb = TEXT_MUTED
        pd.space_after = Pt(4)

    # Insert revocability chart
    img_path = r"D:\Biometric Project\results\cancelable_revocability_dist.png"
    if os.path.exists(img_path):
        s10.shapes.add_picture(img_path, Inches(1.0), Inches(4.3), width=Inches(5.2))

    # Right Column: Unlinkability
    add_card(s10, Inches(6.8), Inches(1.4), Inches(5.7), Inches(5.6), CARD_BG, border_color=CYAN_ACCENT)
    tx2 = s10.shapes.add_textbox(Inches(7.0), Inches(1.5), Inches(5.3), Inches(5.3))
    tf2 = tx2.text_frame
    tf2.word_wrap = True

    p = tf2.paragraphs[0]
    p.text = "2. Cross-Service Unlinkability"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT
    p.space_after = Pt(4)

    p_sub2 = tf2.add_paragraph()
    p_sub2.text = "Can someone link my accounts across websites?"
    p_sub2.font.size = Pt(11)
    p_sub2.font.bold = True
    p_sub2.font.color.rgb = TEXT_MUTED
    p_sub2.space_after = Pt(8)

    unlink_points = [
        ("Evaluated with Different Samples:", "We tested templates generated under different keys using different biological impressions to ensure real independence."),
        ("ISO/IEC 30136 Unlinkability Metric:", "D_sys = 0.0245 (well below the 0.10 benchmark threshold for complete unlinkability)."),
        ("Identical Score Overlap:", "Mean Hamming distance between same-person templates under different keys is 0.5006, virtually identical to different people (0.4999).")
    ]
    for t, d in unlink_points:
        pt = tf2.add_paragraph()
        pt.text = "• " + t
        pt.font.bold = True
        pt.font.size = Pt(11)
        pt.font.color.rgb = TEXT_DARK
        pd = tf2.add_paragraph()
        pd.text = d
        pd.font.size = Pt(10)
        pd.font.color.rgb = TEXT_MUTED
        pd.space_after = Pt(4)

    # Insert unlinkability chart
    img_path2 = r"D:\Biometric Project\results\cancelable_unlinkability.png"
    if os.path.exists(img_path2):
        s10.shapes.add_picture(img_path2, Inches(7.0), Inches(4.3), width=Inches(5.2))

    s10.notes_slide.notes_text_frame.text = (
        "SLIDE 10 SPEAKER NOTES:\n\n"
        "Under the international biometric standard ISO/IEC 30136, a biometric template protection system must prove Revocability and Unlinkability.\n\n"
        "1. For Revocability: When a key is compromised, the user revokes it. We tested old probes against the new template: "
        "rejection was 100.00%! Zero false acceptances. And when the user presents their traits with the fresh key, "
        "their genuine access is restored with an FNMR of 1.67%.\n\n"
        "2. For Unlinkability: If you enroll at Bank A and Office B using the same face and fingerprint, can someone link your accounts? "
        "We calculated the Gomez-Barrero benchmark metric D_sys. "
        "Our score is 0.0245, far below the standard threshold of 0.10. "
        "The Hamming distance between the same person across two keys is 0.5006—completely identical to two total strangers! "
        "Therefore, cross-service tracking is impossible."
    )

    # -------------------------------------------------------------
    # SLIDE 11: SECURITY & NON-INVERTIBILITY (Honest Findings)
    # -------------------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s11, BG_LIGHT)
    add_header(s11, "Security Analysis & Non-Invertibility Boundaries", "ADVERSARIAL ATTACK FINDINGS")

    # Left Column: Attack Results
    add_card(s11, Inches(0.8), Inches(1.4), Inches(5.8), Inches(5.6), CARD_BG)
    tx = s11.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(5.4), Inches(5.3))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Can an Attacker Invert the Template?"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ROSE
    p.space_after = Pt(8)

    attacks = [
        ("Case A1: Template Stolen, Key Secret (Safe):",
         "• Effective keyspace >= 2^126 operations.\n"
         "• Brute-force would require > 10^22 GPU-years.\n"
         "• Classifier distinguishing User A vs B achieves AUC = 0.4767 (pure random coin flip = 0.5000, 0% leakage)."),
        ("Case A2: Template AND Key BOTH Stolen (Vulnerable):",
         "• We trained 4 Machine Learning attack decoders.\n"
         "• A learned linear Ridge decoder achieves 0.9335 cosine similarity to the victim's true vector!\n"
         "• Enables 100.0% false match replay against unprotected systems."),
        ("CRITICAL SCIENTIFIC CONCLUSION:",
         "Random projection binarization is NOT an irreversible one-way cryptographic hash. "
         "Security rests strictly on transformation key secrecy! This establishes an honest empirical boundary.")
    ]
    for title, desc in attacks:
        pt = tf.add_paragraph()
        pt.text = "• " + title
        pt.font.bold = True
        pt.font.size = Pt(12)
        pt.font.color.rgb = ROSE if "Vulnerable" in title or "CONCLUSION" in title else NAVY
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_DARK if "CONCLUSION" in title else TEXT_MUTED
        pd.space_after = Pt(8)

    # Right Column: privacy_utility_tradeoff.png
    add_card(s11, Inches(6.8), Inches(1.4), Inches(5.7), Inches(5.6), CARD_BG)
    img_path = r"D:\Biometric Project\results\privacy_utility_tradeoff.png"
    if os.path.exists(img_path):
        s11.shapes.add_picture(img_path, Inches(7.0), Inches(1.7), width=Inches(5.3))
    caption = s11.shapes.add_textbox(Inches(7.0), Inches(6.0), Inches(5.3), Inches(0.8))
    caption.text_frame.word_wrap = True
    p_cap = caption.text_frame.paragraphs[0]
    p_cap.text = "Figure: The Privacy-Utility Tradeoff. Higher projection dimension m improves accuracy (EER 1.29%), but increases reconstruction cosine (0.9335) if keys leak."
    p_cap.font.size = Pt(10)
    p_cap.font.color.rgb = TEXT_MUTED

    s11.notes_slide.notes_text_frame.text = (
        "SLIDE 11 SPEAKER NOTES:\n\n"
        "Now for the scientific security analysis: Can an attacker reverse-engineer the original biometric from the stored template?\n\n"
        "We analyzed this under two threat models:\n\n"
        "1. Case A1: The attacker steals the database, but does NOT have the projection keys. "
        "Here, the system is completely safe. The keyspace is 2^126, which would take over 10^22 GPU-years to brute-force. "
        "A machine learning distinguisher trying to guess user identity achieves an AUC of 0.4767, which is a pure coin flip.\n\n"
        "2. Case A2: The attacker acquires BOTH the template AND the secret key. "
        "Here, our research uncovered an important truth: many past papers claim random projections are one-way trapdoors, "
        "but our Ridge regression decoder was able to reconstruct continuous features with 0.9335 cosine similarity, "
        "achieving a 100% replay match against unprotected systems!\n\n"
        "This proves that cancelable biometrics is NOT an irreversible one-way cryptographic hash. "
        "Its security relies strictly on keeping the transformation keys confidential."
    )

    # -------------------------------------------------------------
    # SLIDE 12: SYSTEM HARDENING & PRODUCTION CONTROLS
    # -------------------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s12, BG_LIGHT)
    add_header(s12, "Software Hardening: Defense-in-Depth Implementation", "PRODUCTION ENGINEERING")

    hardening_features = [
        ("Zero Raw Biometric Storage", "Data-at-Rest Minimization",
         "The PostgreSQL schema stores only 64-byte packed binary templates (BYTEA). Images and continuous floating-point embeddings exist in RAM only during inference and are deleted immediately.", BLUE_ACCENT),
        ("Score Suppression Defense", "Neutralizing Hill-Climbing Attacks",
         "In production mode, the API returns strictly boolean 'MATCH / NO MATCH'. Decimal similarity scores are suppressed, preventing attackers from iteratively crafting synthetic biometrics.", CYAN_ACCENT),
        ("Escalating Delay Lockout", "Thwarting Online Brute-Force",
         "The database tracks consecutive failed attempts per IP and username. Delays increase exponentially (2^(fails-3) seconds), shutting down automated probing.", AMBER),
        ("Air-Gapped UI Architecture", "Client-Server Isolation",
         "The Streamlit demo interface communicates strictly via HTTP REST API. It never imports PyTorch, feature models, cryptographic master keys, or the C++ chaos engine.", NAVY_LIGHT),
        ("Timing-Safe Token Comparison", "Preventing Side-Channel Leaks",
         "Bearer token authentication uses hmac.compare_digest() for constant-time validation, preventing byte-by-byte timing attacks during API authorization.", EMERALD),
        ("Cross-Platform Bit Determinism", "MSVC and Linux GCC Identity",
         "C++17 engine compiled with -ffp-contract=off and Q64 fixed-point math. Known-Answer Tests (KAT) verified bit-exact identical hash outputs across Windows and Linux Docker.", NAVY)
    ]

    for i, (title, sub, desc, col) in enumerate(hardening_features):
        row = i // 3
        col_idx = i % 3
        x = Inches(0.8 + col_idx * 4.0)
        y = Inches(1.4 + row * 2.85)

        add_card(s12, x, y, Inches(3.8), Inches(2.65), CARD_BG, border_color=col)
        tx = s12.shapes.add_textbox(x + Inches(0.15), y + Inches(0.15), Inches(3.5), Inches(2.35))
        tf = tx.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = sub.upper()
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.size = Pt(13)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_DARK
        p2.space_after = Pt(6)

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.size = Pt(11)
        p3.font.color.rgb = TEXT_MUTED

    s12.notes_slide.notes_text_frame.text = (
        "SLIDE 12 SPEAKER NOTES:\n\n"
        "Because our research showed that security depends on key secrecy, we built extensive production-grade software hardening into the code:\n\n"
        "1. Zero raw biometrics stored: The database stores only 64-byte bitstrings. No photos or floating-point vectors ever hit the disk.\n"
        "2. Score suppression: When authenticating, the API only returns 'MATCH' or 'NO MATCH'. It does not give a decimal score like 0.84, "
        "because hackers can use floating-point scores to climb the hill and reconstruct the user's face.\n"
        "3. Escalating delay lockout: Exponential delays stop brute-force password guessing.\n"
        "4. Architectural UI isolation: The Streamlit user interface is completely decoupled from the AI models. It only talks to the server over REST APIs.\n"
        "5. Constant-time token checks and cross-platform bit determinism between Windows and Linux Docker."
    )

    # -------------------------------------------------------------
    # SLIDE 13: SUMMARY & VIVA TAKEAWAYS
    # -------------------------------------------------------------
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s13, NAVY)

    # Header in White
    tbox = s13.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(1.2))
    tf13 = tbox.text_frame
    tf13.word_wrap = True
    p0 = tf13.paragraphs[0]
    p0.text = "PROJECT SUMMARY & KEY TAKEAWAYS"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = CYAN_ACCENT
    p1 = tf13.add_paragraph()
    p1.text = "ZK-CaMBio Core Conclusions"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    summary_cards = [
        ("Problem Solved",
         "Eliminated the biometric permanence dilemma. Leaked biometric templates can now be cancelled, revoked, and reissued instantly without burning the user's biological identity.",
         BLUE_ACCENT, Inches(0.8)),
        ("High Accuracy Retained",
         "1.29% Equal Error Rate and 98.81% Rank-1 identification accuracy. Paired bootstrap test (p > 0.05) proves zero statistically significant accuracy degradation vs unprotected baseline.",
         EMERALD, Inches(3.8)),
        ("ISO/IEC 30136 Compliance",
         "100.00% rejection against revoked templates, and near-zero cross-service linkability (D_sys = 0.0245 << 0.10). Users cannot be tracked across independent databases.",
         CYAN_ACCENT, Inches(6.8)),
        ("Honest Scientific Boundary",
         "Empirically demonstrated that random projection security requires key confidentiality (0.9335 cosine under key compromise), reinforced with production defense-in-depth controls.",
         AMBER, Inches(9.8)),
    ]

    for title, desc, col, left_pos in summary_cards:
        add_card(s13, left_pos, Inches(2.0), Inches(2.75), Inches(4.8), NAVY_LIGHT, border_color=col)
        tx = s13.shapes.add_textbox(left_pos + Inches(0.15), Inches(2.2), Inches(2.45), Inches(4.4))
        tf = tx.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = col
        pt.space_after = Pt(12)

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = RGBColor(226, 232, 240)

    s13.notes_slide.notes_text_frame.text = (
        "SLIDE 13 SPEAKER NOTES (CONCLUSION & DEFENSE SCRIPT):\n\n"
        "To summarize our project in four simple points:\n\n"
        "1. We solved the biometric permanence problem: users no longer have to worry about permanent identity theft from database breaches.\n"
        "2. We achieved high accuracy: multimodal fusion cuts error rates to 1.11%, and our cancelable template achieves 1.29% EER "
        "and 98.81% Rank-1 identification accuracy. The accuracy penalty is statistically zero.\n"
        "3. We met ISO/IEC 30136 standards: 100% revocation rejection and complete cross-service unlinkability (D_sys = 0.0245).\n"
        "4. We established honest scientific ground: proving that cancelable templates are not magic one-way hashes, but secure "
        "key-dependent protections that require strong software engineering and key management.\n\n"
        "Thank you! I am now ready to answer any questions."
    )

    output_path = r"D:\Biometric Project\presentation\ZK-CaMBio_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    build_presentation()
