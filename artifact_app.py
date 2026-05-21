import streamlit as st
import textstat
import re
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Writing Quality Analyser",
    page_icon="📝",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stApp { font-family: 'Times New Roman', serif; }

    .metric-box {
        background: white;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #1F3864;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 13px; color: #555; font-weight: bold; margin-bottom: 4px; }
    .metric-value { font-size: 28px; font-weight: bold; color: #1F3864; }
    .metric-sub   { font-size: 12px; color: #888; margin-top: 4px; }

    .section-header {
        background: linear-gradient(135deg, #1F3864, #2E75B6);
        color: white;
        padding: 14px 20px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        margin: 16px 0 12px 0;
    }
    .insight-box {
        background: #e8f4fd;
        border-left: 4px solid #2E75B6;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        color: #1F3864;
    }
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        color: #856404;
    }
    .good-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        color: #155724;
    }
    h1 { color: #1F3864; }
    h2 { color: #1F4E79; }
    h3 { color: #2E75B6; }
    .stTextArea textarea { font-family: 'Times New Roman', serif; font-size: 14px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def tokenise_words(text):
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())


def tokenise_sentences(text):
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def compute_metrics(text):
    if not text or len(text.strip()) < 20:
        return None
    words     = tokenise_words(text)
    sentences = tokenise_sentences(text)
    wc        = len(words)
    unique    = len(set(words))
    ttr       = round(unique / wc, 3) if wc > 0 else 0
    flesch    = round(textstat.flesch_reading_ease(text), 1)
    fk_grade  = round(textstat.flesch_kincaid_grade(text), 1)
    avg_sent  = round(wc / len(sentences), 1) if sentences else 0
    return {
        "Word Count":              wc,
        "Unique Words":            unique,
        "Lexical Diversity (TTR)": ttr,
        "Flesch Reading Ease":     flesch,
        "Flesch-Kincaid Grade":    fk_grade,
        "Avg Sentence Length":     avg_sent,
        "Sentences":               len(sentences),
    }


def render_metric(label, value, note=""):
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{note}</div>
    </div>""", unsafe_allow_html=True)


def interpret_ttr(ttr):
    if ttr >= 0.70:   return "good",    "✅ High vocabulary variety"
    elif ttr >= 0.55: return "insight", "🟡 Moderate vocabulary range"
    else:             return "warning", "⚠️ Limited vocabulary diversity"


def interpret_flesch(score):
    if 30 <= score <= 60: return "good",    "✅ Appropriate academic complexity"
    elif score > 60:      return "warning", "🟡 May be too simple for academic writing"
    else:                 return "warning", "⚠️ Very complex — may reduce clarity"


def interpret_sent(avg):
    if 15 <= avg <= 25: return "good",    "✅ Within academic norm (15–25 words)"
    elif avg < 15:      return "warning", "⚠️ Sentences may be too short/fragmented"
    else:               return "warning", "⚠️ Sentences may be too long/complex"


def alert_box(box_type, message):
    css = {"good": "good-box", "warning": "warning-box", "insight": "insight-box"}
    st.markdown(f'<div class="{css.get(box_type, "insight-box")}">{message}</div>',
                unsafe_allow_html=True)


def make_bar_chart(m1, m2, keys, title):
    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(keys))
    ax.bar([i - 0.2 for i in x], [m1[k] for k in keys], 0.38,
           label="Without AI", color="#1F3864", alpha=0.85)
    ax.bar([i + 0.2 for i in x], [m2[k] for k in keys], 0.38,
           label="With AI",    color="#2E75B6", alpha=0.85)
    ax.set_xticks(list(x))
    ax.set_xticklabels([k.replace(" ", "\n") for k in keys], fontsize=9)
    ax.set_title(title, fontweight="bold", fontsize=12, pad=10)
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_facecolor("#f8f9fa")
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# APP HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 📝 AI Writing Quality Analyser")
st.markdown("""
**Dissertation Artifact** — *Perceptions of the Impact of Generative AI on Academic Writing among International Students in the UK*  
York St John University | 2026

This tool analyses and compares writing samples produced **with** and **without** AI assistance,
generating four objective metrics: **Word Count**, **Lexical Diversity (TTR)**,
**Readability**, and **Average Sentence Length**.
""")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# THREE TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊 Writing Analyser",
    "📈 Survey Results (n=55)",
    "ℹ️ About This Study"
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — WRITING ANALYSER
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Enter Your Writing Samples")
    st.info("📌 Paste two essay excerpts (300–500 words each) responding to the **same prompt**. "
            "One written **without AI**, one written **with AI**. "
            "The tool will generate and compare all four metrics.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ✍️ Written WITHOUT AI Assistance")
        text_no_ai = st.text_area(
            "Paste your essay here (no AI tools used):",
            height=280, key="no_ai",
            placeholder="Paste your essay written without any AI assistance here..."
        )
    with col2:
        st.markdown("#### 🤖 Written WITH AI Assistance")
        text_with_ai = st.text_area(
            "Paste your essay here (AI tools used):",
            height=280, key="with_ai",
            placeholder="Paste your essay written with AI assistance here..."
        )

    st.markdown("")
    analyse = st.button("🔍 Analyse & Compare", type="primary", use_container_width=True)

    if analyse:
        if not text_no_ai.strip() or not text_with_ai.strip():
            st.error("⚠️ Please paste both essay samples before analysing.")
        else:
            m_no  = compute_metrics(text_no_ai)
            m_yes = compute_metrics(text_with_ai)

            if not m_no or not m_yes:
                st.error("⚠️ One or both samples are too short. "
                         "Please paste at least 100 words per sample.")
            else:
                st.markdown("---")
                st.markdown('<div class="section-header">📊 Metric Comparison Results</div>',
                            unsafe_allow_html=True)

                # Four metric cards
                c1, c2, c3, c4 = st.columns(4)
                for col, (key, note) in zip(
                    [c1, c2, c3, c4],
                    [("Word Count",             "Total words produced"),
                     ("Lexical Diversity (TTR)", "Vocabulary variety (0–1)"),
                     ("Flesch Reading Ease",     "Readability (30–60 ideal)"),
                     ("Avg Sentence Length",     "Words per sentence (15–25 ideal)")]
                ):
                    with col:
                        render_metric("Without AI", m_no[key],  note)
                        render_metric("With AI",    m_yes[key], note)

                # Full metric table
                st.markdown("#### 📋 Side-by-Side Metric Table")
                rows = []
                for key, hib, note in [
                    ("Word Count",             True,  "Higher = more output"),
                    ("Unique Words",           True,  "More unique = richer vocabulary"),
                    ("Lexical Diversity (TTR)",True,  "Higher = more varied vocabulary"),
                    ("Flesch Reading Ease",    None,  "30–60 = academic range"),
                    ("Flesch-Kincaid Grade",   None,  "Grade level of text"),
                    ("Avg Sentence Length",    None,  "15–25 words = academic norm"),
                    ("Sentences",              None,  "Total sentence count"),
                ]:
                    v1, v2 = m_no[key], m_yes[key]
                    if hib is True:
                        chg = ("🟢 ↑ Improved"  if v2 > v1
                               else ("🔴 ↓ Decreased" if v2 < v1 else "⚪ No change"))
                    elif hib is False:
                        chg = ("🟢 ↓ Reduced"   if v2 < v1
                               else ("🔴 ↑ Increased" if v2 > v1 else "⚪ No change"))
                    else:
                        diff = round(v2 - v1, 2)
                        chg  = f"🔵 Δ {'+' if diff >= 0 else ''}{diff}"
                    rows.append({"Metric": key, "Without AI": v1,
                                 "With AI": v2, "Change": chg, "Note": note})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                # Bar charts
                st.markdown("#### 📊 Visual Comparison")
                ch1, ch2 = st.columns(2)
                with ch1:
                    st.pyplot(make_bar_chart(m_no, m_yes,
                              ["Word Count", "Unique Words"], "Volume & Vocabulary"))
                with ch2:
                    st.pyplot(make_bar_chart(m_no, m_yes,
                              ["Flesch Reading Ease", "Avg Sentence Length"],
                              "Readability & Structure"))

                # TTR bar
                fig3, ax = plt.subplots(figsize=(6, 2.5))
                ax.barh(["Without AI", "With AI"],
                        [m_no["Lexical Diversity (TTR)"],
                         m_yes["Lexical Diversity (TTR)"]],
                        color=["#1F3864", "#2E75B6"], height=0.5)
                ax.axvline(0.55, color="orange", linestyle="--",
                           label="Academic min (0.55)", linewidth=1.5)
                ax.axvline(0.75, color="green",  linestyle="--",
                           label="High diversity (0.75)", linewidth=1.5)
                ax.set_xlim(0, 1)
                ax.set_title("Lexical Diversity (TTR)", fontweight="bold")
                ax.legend(fontsize=8)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                fig3.tight_layout()
                st.pyplot(fig3)

                # Interpretations
                st.markdown("#### 🧠 Interpretation")
                col_a, col_b = st.columns(2)
                for col, m, label in [(col_a, m_no, "Without AI"),
                                      (col_b, m_yes, "With AI")]:
                    with col:
                        st.markdown(f"**{label}**")
                        for fn, key in [
                            (interpret_ttr,    "Lexical Diversity (TTR)"),
                            (interpret_flesch, "Flesch Reading Ease"),
                            (interpret_sent,   "Avg Sentence Length"),
                        ]:
                            btype, msg = fn(m[key])
                            alert_box(btype, f"{msg}<br>{key} = {m[key]}")

                # AI impact summary
                st.markdown("#### 📌 AI Impact Summary")
                ttr_d = m_yes["Lexical Diversity (TTR)"] - m_no["Lexical Diversity (TTR)"]
                wc_d  = m_yes["Word Count"] - m_no["Word Count"]
                sl_no = 15 <= m_no["Avg Sentence Length"]  <= 25
                sl_ai = 15 <= m_yes["Avg Sentence Length"] <= 25

                if ttr_d > 0.02:
                    alert_box("good",
                        f"AI <b>increased lexical diversity</b> by {round(ttr_d,3)} "
                        "— vocabulary enrichment confirmed.")
                elif ttr_d < -0.02:
                    alert_box("warning",
                        f"AI <b>decreased lexical diversity</b> by {abs(round(ttr_d,3))} "
                        "— vocabulary may be less varied with AI.")
                else:
                    alert_box("insight",
                        "No significant change in lexical diversity between conditions.")

                if wc_d > 30:
                    alert_box("good",
                        f"AI produced <b>{wc_d} more words</b>, suggesting AI "
                        "expands and elaborates ideas.")
                elif wc_d < -30:
                    alert_box("warning",
                        f"AI produced <b>{abs(wc_d)} fewer words</b>, suggesting "
                        "AI condensed the text.")
                else:
                    alert_box("insight", "Word count is similar between conditions.")

                if sl_ai and not sl_no:
                    alert_box("good",
                        "AI <b>normalised sentence length</b> into the academic "
                        "range (15–25 words).")
                elif not sl_ai and sl_no:
                    alert_box("warning",
                        "AI-assisted writing moved <b>outside</b> the academic "
                        "sentence length norm.")

                # CSV download
                st.markdown("#### 💾 Download Results")
                csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Metrics as CSV", csv,
                                   "writing_quality_metrics.csv", "text/csv",
                                   use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — SURVEY RESULTS  (real data from 55 respondents studying at universities in the UK)
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📈 Survey Results — 55 International Students studying in the UK (April 2026)")
    st.info("Primary survey data collected from 55 international students studying in the UK for this dissertation.")

    # Demographics
    st.markdown("#### Section 1: Demographics")
    d1, d2, d3, d4 = st.columns(4)
    COLS = ["#1F3864", "#2E75B6", "#70AD47", "#ED7D31"]
    for col, (title, labels, vals) in zip([d1, d2, d3, d4], [
        ("Age Groups",       ["18–20","21–24","25–29","30+"],            [18,26,9,2]),
        ("Gender",           ["Female","Male","Non-binary"],              [38,16,1]),
        ("Level of Study",   ["Undergraduate","Postgraduate","Other"],    [34,19,2]),
        ("UK Study Duration",["< 1 year","1–2 years","2+ years"],        [14,17,24]),
    ]):
        with col:
            fig, ax = plt.subplots(figsize=(3.5, 3.5))
            ax.pie(vals, labels=labels, colors=COLS[:len(vals)],
                   autopct="%1.0f%%", startangle=90, textprops={"fontsize": 8})
            ax.set_title(title, fontweight="bold", fontsize=9, pad=6)
            st.pyplot(fig)

    st.markdown("---")

    # AI tool use
    st.markdown("#### Section 2: AI Tool Usage (Q6 & Q7)")
    ca, cb = st.columns(2)
    with ca:
        tools  = ["ChatGPT/Claude/Gemini","Grammarly","QuillBot",
                  "DeepL/Translate","AI Citations"]
        counts = [50, 34, 20, 17, 8]
        fig, ax = plt.subplots(figsize=(5, 3.5))
        bars = ax.barh(tools, counts, color="#1F3864")
        for bar, cnt in zip(bars, counts):
            ax.text(bar.get_width() + 0.5,
                    bar.get_y() + bar.get_height() / 2,
                    f"{cnt} ({round(cnt/55*100)}%)", va="center", fontsize=9)
        ax.set_xlim(0, 62)
        ax.set_title("Tools Accessed (n=55)", fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
    with cb:
        fig, ax = plt.subplots(figsize=(3.5, 3.5))
        ax.pie([53, 2], labels=["Yes (96%)","No (4%)"],
               colors=["#1F3864","#D9D9D9"], startangle=90,
               textprops={"fontsize": 10}, explode=[0.03, 0])
        ax.set_title("Have you used Generative AI tools?",
                     fontweight="bold", fontsize=9)
        st.pyplot(fig)

    st.markdown("---")

    # Feature frequency
    st.markdown("#### Section 3: AI Feature Frequency (Q8)")
    feature_data = {
        "Grammar/spelling":  {"Never":3, "Rarely":7,  "Sometimes":15,"Often":16,"Always":14},
        "Restructuring":     {"Never":2, "Rarely":12, "Sometimes":15,"Often":18,"Always":8},
        "Generating ideas":  {"Never":1, "Rarely":7,  "Sometimes":20,"Often":20,"Always":7},
        "Translating text":  {"Never":11,"Rarely":12, "Sometimes":13,"Often":13,"Always":6},
        "References":        {"Never":9, "Rarely":14, "Sometimes":10,"Often":10,"Always":12},
        "Summarising":       {"Never":6, "Rarely":12, "Sometimes":13,"Often":15,"Always":9},
    }
    order   = ["Never","Rarely","Sometimes","Often","Always"]
    colours = ["#C00000","#FF6B6B","#A9A9A9","#4472C4","#1F3864"]
    fig, ax = plt.subplots(figsize=(10, 4))
    features = list(feature_data.keys())
    bottoms  = [0] * len(features)
    for i, opt in enumerate(order):
        vals = [feature_data[f].get(opt, 0) for f in features]
        ax.bar(features, vals, bottom=bottoms, label=opt, color=colours[i])
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_xticklabels(features, rotation=15, ha="right", fontsize=9)
    ax.set_title("Frequency of AI Feature Use (n=55)", fontweight="bold")
    ax.legend(loc="upper right", fontsize=8, title="Frequency")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    st.pyplot(fig)

    st.markdown("---")

    # Likert perceived impact
    st.markdown("#### Section 4: Perceived Impact of AI (Q9)")
    likert_data = {
        "Writing confidence":          {"SD":0,"D":0, "N":20,"A":27,"SA":8},
        "Understand conventions":      {"SD":0,"D":2, "N":13,"A":30,"SA":10},
        "Over-reliant on AI":          {"SD":2,"D":9, "N":15,"A":20,"SA":9},
        "Independent skills weakened": {"SD":3,"D":10,"N":17,"A":20,"SA":5},
        "Logical argument structure":  {"SD":1,"D":4, "N":19,"A":25,"SA":6},
        "AI saves time":               {"SD":1,"D":4, "N":8, "A":22,"SA":20},
        "Clearer academic writing":    {"SD":1,"D":1, "N":13,"A":24,"SA":16},
        "Grammar accuracy improved":   {"SD":1,"D":1, "N":13,"A":27,"SA":13},
        "Organise writing":            {"SD":1,"D":2, "N":9, "A":29,"SA":14},
    }
    l_order   = ["SD","D","N","A","SA"]
    l_labels  = ["Strongly Disagree","Disagree","Neutral","Agree","Strongly Agree"]
    l_colours = ["#C00000","#FF6B6B","#A9A9A9","#4472C4","#1F3864"]
    fig, ax = plt.subplots(figsize=(11, 5))
    stmts   = list(likert_data.keys())
    bottoms = [0] * len(stmts)
    for i, opt in enumerate(l_order):
        vals = [likert_data[s].get(opt, 0) for s in stmts]
        ax.bar(stmts, vals, bottom=bottoms, label=l_labels[i], color=l_colours[i])
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_xticklabels(stmts, rotation=20, ha="right", fontsize=8)
    ax.set_title("Agreement with AI Impact Statements (n=55)", fontweight="bold")
    ax.legend(loc="upper right", fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    st.pyplot(fig)

    st.markdown("---")

    # Motivations + integrity worry
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("**Motivations for Using AI (Q10)**")
        motiv_labels = ["Improving quality","Language barriers","Time pressure",
                        "Improving grammar","Academic structure","Peer recommendation"]
        motiv_vals   = [39, 35, 30, 28, 25, 9]
        fig, ax = plt.subplots(figsize=(4.5, 3.5))
        ax.barh(motiv_labels, motiv_vals, color="#2E75B6")
        for i, v in enumerate(motiv_vals):
            ax.text(v + 0.3, i, str(v), va="center", fontsize=9)
        ax.set_xlim(0, 48)
        ax.set_title("Top Motivations (n=55)", fontweight="bold", fontsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)

    with m2:
        st.markdown("**Worry About Academic Misconduct (Q11)**")
        worry_labels = ["Never","Rarely","Sometimes","Often","Always"]
        worry_vals   = [9, 13, 18, 11, 4]
        worry_cols   = ["#1F3864","#2E75B6","#A9A9A9","#ED7D31","#C00000"]
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(worry_vals,
               labels=[f"{l}\n({v})" for l, v in zip(worry_labels, worry_vals)],
               colors=worry_cols, startangle=140,
               textprops={"fontsize": 8}, autopct="%1.0f%%")
        ax.set_title("Frequency of Integrity Concern", fontweight="bold", fontsize=9)
        fig.tight_layout()
        st.pyplot(fig)

    # University guidance + barriers
    st.markdown("**University AI Guidance & Ethical Barriers**")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("*Q12 — University provided clear guidelines?*")
        guide_labels = ["Strongly Agree","Agree","Neutral","Disagree","Strongly Disagree"]
        guide_vals   = [18, 21, 12, 3, 1]
        guide_cols   = ["#1F3864","#2E75B6","#A9A9A9","#ED7D31","#C00000"]
        fig, ax = plt.subplots(figsize=(4, 3.5))
        ax.bar(guide_labels, guide_vals, color=guide_cols)
        for i, v in enumerate(guide_vals):
            ax.text(i, v + 0.3, str(v), ha="center", fontsize=10, fontweight="bold")
        ax.set_xticklabels(guide_labels, rotation=15, ha="right", fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        st.pyplot(fig)

    with g2:
        st.markdown("*Q13 — Challenges to ethical AI use*")
        challenge_labels = ["Fear of Turnitin","Citing AI content",
                            "Uncertain what's allowed",
                            "Unclear policy",
                            "Don't know how to use effectively"]
        challenge_vals = [27, 27, 25, 21, 23]
        fig, ax = plt.subplots(figsize=(4.5, 3.5))
        ax.barh(challenge_labels, challenge_vals, color="#1F4E79")
        for i, v in enumerate(challenge_vals):
            ax.text(v + 0.2, i, str(v), va="center", fontsize=9)
        ax.set_xlim(0, 34)
        ax.set_title("Ethical AI Challenges Faced", fontweight="bold", fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)

    # Desired support
    st.markdown("**Q14 — Desired Institutional Support**")
    sup_labels = ["Workshops on ethical AI use","Guidance on appropriate use",
                  "AI-prompt engineering training","Clearer policy documents",
                  "Uncertain what's allowed"]
    sup_vals   = [31, 30, 27, 26, 12]
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.barh(sup_labels, sup_vals, color="#1F3864")
    for i, v in enumerate(sup_vals):
        ax.text(v + 0.2, i, str(v), va="center", fontsize=9)
    ax.set_xlim(0, 38)
    ax.set_title("Preferred University Support (n=55)", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — ABOUT THIS STUDY
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### ℹ️ About This Study")
    st.markdown("""
**Title:** Perceptions of the Impact of Generative AI on Academic Writing among International Students in the UK

**Institution:** York St John University | **Year:** 2026

---

#### Research Aim
This research investigates international students’ perceptions and experiences of AI-assisted academic writing in the UK, using survey-based data alongside a proposed Streamlit artifact for future objective writing analysis research.

#### Mixed-Method Design
| Component | Description |
|-----------|-------------|
| **Survey** | 55 international students studying in the UK — April 2026 |
| **Artifact** | Python/Streamlit app generating 4 objective writing metrics |
| **Integration** | Comparison of objective metrics with student perceptions |

#### The Four Metrics

| Metric | What it measures | Academic Norm |
|--------|-----------------|---------------|
| **Word Count** | Total output volume | Task-dependent |
| **Lexical Diversity (TTR)** | Unique words ÷ total words | 0.55 – 0.75 |
| **Flesch Reading Ease** | Structural/linguistic complexity | 30 – 60 |
| **Avg Sentence Length** | Mean words per sentence | 15 – 25 words |

#### Key Survey Findings (n=55)
- **96%** of international students have used generative AI tools
- **91%** use ChatGPT / Claude / Gemini for content generation
- **62%** use Grammarly for grammar and spell checking
- **78%** agree AI helps them organise writing more effectively
- **76%** agree AI saves time on academic writing tasks
- **73%** agree AI improves grammar accuracy and writing clarity
- **53%** feel they are becoming over-reliant on AI
- **45%** feel independent writing skills have been negatively affected
- **60%** worry about AI misconduct at least sometimes
- **49%** cite fear of Turnitin as a barrier to ethical AI use

#### How to Use the Writing Analyser
1. Go to the **📊 Writing Analyser** tab
2. Paste your essay written **without AI** in the left box
3. Paste your essay written **with AI** in the right box
4. Click **🔍 Analyse & Compare**
5. View the table, charts, and interpretation
6. Download your results as CSV


    """)
    st.markdown("---")
    st.caption(
        "Built with Python · Streamlit · textstat · pandas · matplotlib  |  "
        "York St John University Dissertation 2026  |  Run: streamlit run artifact_app.py"
    )