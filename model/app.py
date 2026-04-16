import streamlit as st
import torch
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

from utils.model_loader import load_model
from utils.predict import predict_image, transform
from utils.gradcam import GradCAM
from utils.lime_explain import generate_lime


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="NeuroScan AI - Alzheimer's Detection",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------- CUSTOM CSS ----------------

st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #f8fafc;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .header-container h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .header-container p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Prediction card */
    .prediction-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    
    .prediction-card h3 {
        color: #2d3748;
        margin-top: 0;
    }
    
    /* Class confidence cards */
    .class-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    
    .class-card:hover {
        transform: translateX(5px);
    }
    
    .class-card.highlight {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
    }
    
    .class-card.moderate {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
    }
    
    .class-card.mild {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
    }
    
    .class-card.very-mild {
        background: #f0f9ff;
        border-left: 4px solid #3b82f6;
    }
    
    /* Progress bar custom styling */
    .stProgress > div > div > div > div {
        background-color: #667eea;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    
    /* Sidebar styling */
    .sidebar-content {
        background-color: #f1f5f9;
    }
    
    /* Info box */
    .info-box {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .info-box h4 {
        color: #1e40af;
        margin-top: 0;
    }
    
    .info-box p {
        color: #1e3a8a;
        margin: 0;
        font-size: 0.9rem;
    }
    
    /* Warning box */
    .warning-box {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box p {
        color: #92400e;
        margin: 0;
        font-size: 0.85rem;
    }
    
    /* Upload area */
    .upload-section {
        background: white;
        border: 2px dashed #cbd5e1;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        transition: border-color 0.3s;
    }
    
    .upload-section:hover {
        border-color: #667eea;
    }
    
    /* Explanation section */
    .explanation-section {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 1.5rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- LOAD MODEL ----------------

@st.cache_resource
def get_model():
    return load_model("model/alzheimer_resnet18.pth")

model = get_model()


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown("### 🧠 NeuroScan AI")
    st.markdown("---")
    
    st.markdown("""
    **About This Tool**
    
    This AI-powered system analyzes brain MRI scans to detect and classify 
    neurodegenerative disorders, specifically Alzheimer's disease stages.
    """)
    
    st.markdown("**Disease Stages**")
    st.info("""
    - **No Impairment**: Normal cognitive function
    - **Very Mild**: Early stage, subtle memory issues
    - **Mild**: Noticeable cognitive decline
    - **Moderate**: Significant impairment, needs assistance
    """)
    
    st.markdown("---")
    st.markdown("**How to Use**")
    st.markdown("""
    1. Upload a brain MRI scan (JPG, PNG)
    2. View the AI prediction and confidence scores
    3. Explore explanations using Grad-CAM or LIME
    """)
    
    st.markdown("---")
    st.warning("""
    **Disclaimer**: This tool is for research and educational purposes only. 
    It should not be used for medical diagnosis. Always consult healthcare 
    professionals for medical advice.
    """)

    st.markdown("---")
    st.markdown("**Interactive Controls**")
    overlay_opacity = st.slider(
        "Grad-CAM Overlay Opacity",
        min_value=0.1,
        max_value=0.9,
        value=0.5,
        step=0.05,
        help="Adjust how strongly the heatmap appears on top of the MRI scan."
    )
    lime_samples = st.slider(
        "LIME Perturbation Samples",
        min_value=200,
        max_value=1500,
        value=1000,
        step=100,
        help="Higher values can improve stability but take longer to generate."
    )
    show_technical_details = st.toggle(
        "Show Technical Details by Default",
        value=True
    )


# ---------------- HEADER ----------------

st.markdown("""
<div class="header-container">
    <h1>🧠 NeuroScan AI</h1>
    <p>Advanced AI-Powered Alzheimer's Detection & Explanation System</p>
</div>
""", unsafe_allow_html=True)


# ---------------- UPLOAD SECTION ----------------

st.markdown("""
<div class="upload-section">
    <h3>📤 Upload Brain MRI Scan</h3>
    <p style="color: #64748b;">Supports JPG, JPEG, PNG formats</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose an MRI image file",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed"
)


if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    classes = [
        "No Impairment",
        "Very Mild Impairment",
        "Mild Impairment",
        "Moderate Impairment"
    ]
    
    # -------- IMAGE DISPLAY --------
    st.markdown("### 🖼️ Uploaded Scan")
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image(
            image, 
            caption="Uploaded MRI Scan", 
            use_container_width=True,
            output_format="PNG"
        )
    
    # -------- PREDICTION --------
    with col2:
        st.markdown("### 📊 Analysis Results")
        
        label, probs = predict_image(model, image)
        predicted_idx = int(np.argmax(probs))
        confidence = float(probs[predicted_idx])
        sorted_probs = np.sort(probs)[::-1]
        confidence_gap = float(sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) > 1 else float(sorted_probs[0])
        
        # Determine severity color
        severity_colors = {
            "No Impairment": "🟢",
            "Very Mild Impairment": "🔵",
            "Mild Impairment": "🟡",
            "Moderate Impairment": "🔴"
        }
        
        severity_emoji = severity_colors.get(label, "⚪")
        
        # Main prediction display
        st.markdown(f"""
        <div class="prediction-card">
            <h3>{severity_emoji} Predicted Stage: {label}</h3>
            <p style="color: #64748b; font-size: 0.9rem;">
                The AI model has analyzed the MRI scan and classified it as 
                <strong>{label}</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Top Prediction Confidence", f"{confidence * 100:.1f}%")
    metric_col2.metric("Confidence Gap vs Runner-Up", f"{confidence_gap * 100:.1f}%")
    metric_col3.metric("Classes Evaluated", f"{len(classes)}")

    dashboard_tab, explain_tab, export_tab = st.tabs([
        "Prediction Dashboard",
        "Explainability Studio",
        "Export Center"
    ])

    with dashboard_tab:
        st.markdown("#### Confidence Scores")
        class_focus = st.selectbox(
            "Inspect a class prediction",
            classes,
            index=predicted_idx,
            help="Switch between stages to inspect the model's confidence distribution."
        )

        class_descriptions = {
            "No Impairment": "The model sees this scan as most aligned with normal cognitive patterns.",
            "Very Mild Impairment": "The model detects subtle features associated with very early-stage impairment.",
            "Mild Impairment": "The model identifies signs consistent with noticeable cognitive decline.",
            "Moderate Impairment": "The model sees stronger features associated with advanced impairment."
        }

        st.info(class_descriptions[class_focus])

        for i, cls in enumerate(classes):
            value = probs[i]
            is_predicted = cls == label
            is_focused = cls == class_focus

            color_map = {
                0: "#22c55e",
                1: "#3b82f6",
                2: "#f59e0b",
                3: "#ef4444"
            }

            bar_color = color_map[i]
            border_color = bar_color if is_focused else "#e2e8f0"

            st.markdown(f"""
            <div class="class-card {'highlight' if is_predicted else ''}" style="border: 2px solid {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: {'bold' if is_predicted else 'normal'}; color: {'#166534' if is_predicted else '#374151'};">
                        {'✅' if is_predicted else '⚪'} {cls}
                    </span>
                    <span style="font-weight: bold; color: {bar_color};">
                        {value*100:.1f}%
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="
                width: 100%;
                height: 8px;
                background-color: #e2e8f0;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 12px;
            ">
                <div style="
                    width: {value*100}%;
                    height: 100%;
                    background-color: {bar_color};
                    border-radius: 4px;
                    transition: width 0.5s ease;
                "></div>
            </div>
            """, unsafe_allow_html=True)

        insight_col1, insight_col2 = st.columns([1.2, 1])
        with insight_col1:
            st.markdown("#### Clinical Context")
            st.success(
                f"The current prediction is **{label}** with **{confidence * 100:.1f}%** confidence."
            )
            st.caption(
                "This should be interpreted as a model estimate for research use, not as a clinical diagnosis."
            )
        with insight_col2:
            st.markdown("#### Quick Comparison")
            fig_conf, ax_conf = plt.subplots(figsize=(7, 3.5))
            ax_conf.barh(classes, probs, color=["#22c55e", "#3b82f6", "#f59e0b", "#ef4444"])
            ax_conf.set_xlim(0, 1)
            ax_conf.set_xlabel("Probability")
            ax_conf.set_title("Class Probability Overview")
            ax_conf.invert_yaxis()
            st.pyplot(fig_conf, use_container_width=True)
            plt.close(fig_conf)
    
    with explain_tab:
        st.markdown("### 🔍 Model Explanation")
        st.markdown("""
        <div class="info-box">
            <h4>Understanding AI Decisions</h4>
            <p>Choose an explanation method to visualize which areas of the brain MRI 
            influenced the AI's prediction. This helps build trust and understanding 
            in the model's decision-making process.</p>
        </div>
        """, unsafe_allow_html=True)

        explain_option = st.radio(
            "Select Explanation Method",
            ["🎯 Grad-CAM (Gradient-weighted Class Activation Mapping)",
             "🔬 LIME (Local Interpretable Model-agnostic Explanations)"],
            horizontal=True,
            index=0
        )

        img_tensor = transform(image).unsqueeze(0)
        heatmap = None
        lime_img = None

        with st.spinner("Generating explanation... Please wait."):
            if "Grad-CAM" in explain_option:
                st.markdown("#### Grad-CAM Visualization")
                st.markdown("""
                <div class="info-box">
                    <h4>How Grad-CAM Works</h4>
                    <p>Grad-CAM highlights the important regions in the image by using 
                    gradient information flowing into the last convolutional layer. 
                    Warm colors indicate areas that strongly influenced the prediction.</p>
                </div>
                """, unsafe_allow_html=True)

                gradcam = GradCAM(model, model.layer4)
                heatmap = gradcam.generate(img_tensor)

                compare_col1, compare_col2 = st.columns(2)
                with compare_col1:
                    st.image(image, caption="Original MRI Scan", use_container_width=True)
                with compare_col2:
                    fig, ax = plt.subplots(figsize=(8, 8))
                    ax.imshow(image)
                    ax.imshow(heatmap, cmap="jet", alpha=overlay_opacity)
                    ax.set_title("Grad-CAM Heatmap Overlay", fontsize=14, fontweight="bold")
                    ax.axis("off")
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)

                if show_technical_details:
                    with st.expander("📊 Technical Details", expanded=True):
                        st.markdown(f"""
                        - **Target Layer**: `layer4` (last convolutional layer of ResNet18)
                        - **Method**: Gradient-weighted Class Activation Mapping
                        - **Overlay Opacity**: `{overlay_opacity:.2f}`
                        - **Output**: Heatmap showing spatial importance
                        """)

            if "LIME" in explain_option:
                st.markdown("#### LIME Visualization")
                st.markdown("""
                <div class="info-box">
                    <h4>How LIME Works</h4>
                    <p>LIME creates interpretable explanations by perturbing the input 
                    image and observing how predictions change. It identifies superpixels 
                    that have the most impact on the model's prediction.</p>
                </div>
                """, unsafe_allow_html=True)

                lime_img = generate_lime(model, image, transform, num_samples=lime_samples)

                compare_col1, compare_col2 = st.columns(2)
                with compare_col1:
                    st.image(image, caption="Original MRI Scan", use_container_width=True)
                with compare_col2:
                    fig2, ax2 = plt.subplots(figsize=(8, 8))
                    ax2.imshow(lime_img)
                    ax2.set_title("LIME Feature Importance", fontsize=14, fontweight="bold")
                    ax2.axis("off")
                    st.pyplot(fig2, use_container_width=True)
                    plt.close(fig2)

                if show_technical_details:
                    with st.expander("📊 Technical Details", expanded=True):
                        st.markdown(f"""
                        - **Method**: Local Interpretable Model-agnostic Explanations
                        - **Samples**: `{lime_samples}` perturbed samples
                        - **Features**: Top 5 important superpixels shown
                        - **Interpretation**: Highlighted segments positively contribute to prediction
                        """)

    with export_tab:
        st.markdown("#### Export & Reset")
        st.caption("Save the current explanation output or export a lightweight text report.")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("🔄 Analyze Another Scan", use_container_width=True):
                st.rerun()

        with col2:
            fig_save, ax_save = plt.subplots(figsize=(8, 8))
            if heatmap is None and lime_img is None:
                ax_save.imshow(image)
            elif heatmap is not None:
                ax_save.imshow(image)
                ax_save.imshow(heatmap, cmap="jet", alpha=overlay_opacity)
            else:
                ax_save.imshow(lime_img)
            ax_save.axis("off")
            plt.tight_layout()

            buf = io.BytesIO()
            fig_save.savefig(buf, format="PNG", bbox_inches="tight", dpi=150)
            buf.seek(0)

            st.download_button(
                label="📥 Download Explanation",
                data=buf,
                file_name=f"explanation_{label.replace(' ', '_')}.png",
                mime="image/png",
                use_container_width=True
            )
            plt.close(fig_save)

        with col3:
            st.download_button(
                label="📄 Download Report",
                data=f"""NeuroScan AI Analysis Report
============================
Predicted Stage: {label}
Confidence Scores:
- No Impairment: {probs[0]*100:.2f}%
- Very Mild Impairment: {probs[1]*100:.2f}%
- Mild Impairment: {probs[2]*100:.2f}%
- Moderate Impairment: {probs[3]*100:.2f}%

Explanation Method: {explain_option}

Note: This report is for research purposes only.
""",
                file_name=f"report_{label.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )


# ---------------- FOOTER ----------------

st.markdown("""
<div class="footer">
    <p>NeuroScan AI v1.0 | Built with Streamlit & PyTorch | For Research Use Only</p>
    <p>Model: ResNet18 | Dataset: Alzheimer MRI Dataset | Explainability: Grad-CAM & LIME</p>
</div>
""", unsafe_allow_html=True)
