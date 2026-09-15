import os
import sys
from pathlib import Path

# Ensure project root is in sys.path so 'dia' package can be imported directly
repo_root = str(Path(__file__).resolve().parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

from dia.core.orchestrator import DIAOrchestrator

st.set_page_config(page_title="Dataset Integrity Analyzer", layout="wide")

st.title("Dataset Integrity Analyzer (DIA)")
st.markdown("Automated Dataset Health Auditing and Bias Impact Prediction")

st.sidebar.header("Dataset Configuration")
dataset_path = st.sidebar.text_input("Local Dataset Path", value="data/demo_dataset", help="Path to a folder-per-class image dataset.")

if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'df' not in st.session_state:
    st.session_state.df = None

if st.sidebar.button("Run Full Analysis"):
    if not os.path.exists(dataset_path):
        st.sidebar.error("Path does not exist.")
    else:
        st.session_state.analysis_complete = False
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simple text parsing callback to update the spinner
        def update_ui(msg):
            status_text.text(msg)
            # Advance progress slightly just for UX
            current = st.session_state.get('fake_prog', 0.1)
            new_prog = min(current + 0.1, 0.9)
            st.session_state.fake_prog = new_prog
            progress_bar.progress(new_prog)
            
        st.session_state.fake_prog = 0.1
        try:
            start_time = time.time()
            orchestrator = DIAOrchestrator(dataset_path)
            results, df = orchestrator.run_all(update_callback=update_ui)
            
            progress_bar.progress(1.0)
            status_text.text(f"Analysis complete in {time.time()-start_time:.1f} seconds!")
            
            st.session_state.results = results
            st.session_state.df = df
            st.session_state.analysis_complete = True
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")

if st.session_state.analysis_complete:
    res = st.session_state.results
    df = st.session_state.df
    
    # 1. AI Readiness Score
    st.header("1. AI Readiness Score")
    score = res['readiness']['overall_score']
    verdict = res['readiness']['verdict']
    
    col1, col2 = st.columns([1, 2])
    with col1:
        color = "green" if score > 80 else "orange" if score > 50 else "red"
        st.markdown(f"<h1 style='text-align: center; color: {color}; font-size: 5em;'>{score}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{verdict}</h3>", unsafe_allow_html=True)
        
    with col2:
        # Radar Chart for sub-scores
        categories = list(res['readiness']['sub_scores'].keys())
        values = list(res['readiness']['sub_scores'].values())
        
        fig = go.Figure(data=go.Scatterpolar(
          r=values + [values[0]],
          theta=categories + [categories[0]],
          fill='toself',
          marker=dict(color='blue')
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
        
    st.divider()
    
    # 2. Bias Impact Prediction
    st.header("2. Bias Impact Predictor (C2)")
    impact = res.get('bias_impact', {})
    
    with st.expander("What does this mean?", expanded=True):
        st.write("This section predicts how much your model's performance will suffer due to the dataset's current flaws. If you train a model on this dataset, its test accuracy is expected to drop by the predicted percentage compared to training on a healthy dataset. The 'Confound Penalty' indicates the portion of this drop caused specifically by overlapping issues (e.g., blurry images always belonging to one class) that confuse the model.")
        st.caption("Technical note: The predictor uses a regression model calibrated against early feasibility spikes to map dataset structural health directly to expected downstream model performance drops. (Phase 6 Prototype)")

    i_col1, i_col2, i_col3 = st.columns(3)
    i_col1.metric("Predicted Accuracy Degradation", f"-{impact.get('expected_accuracy_drop_pct', 0)}%")
    i_col2.metric("Worst-Case Scenario", f"-{impact.get('interval_high', 0)}%")
    i_col3.metric("Confound Penalty Applied", f"{impact.get('features', {}).get('confound_count', 0)*3}%")

    st.divider()
    
    # 3. Cross-Dimensional Confounds
    st.header("3. Cross-Dimensional Confounds")
    
    with st.expander("What does this mean?", expanded=True):
        st.write("A 'confound' occurs when two different dataset issues overlap systematically. For example, if most images in the 'Bird' class are blurry, the model might learn to associate blurriness with birds rather than learning the actual visual features of a bird. This section flags those overlapping patterns so you can fix them before training.")

    confounds = res.get('confounds', {}).get('detected_confounds', [])
    if not confounds:
        st.success("No cross-dimensional confounds detected. The dimensions appear independent.")
    else:
        for c in confounds:
            st.error(f"**{c['type']}**: {c['description']}")
            
    st.divider()
    
    # 4. Dimensional Deep Dive
    st.header("4. Dimensional Deep Dive")
    st.write("This section breaks down the dataset's health into five key areas. Reviewing these individual dimensions helps pinpoint exactly what needs to be fixed to improve the overall AI Readiness Score.")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Balance", "Quality", "Duplicates", "Diversity", "Labels"])
    
    with tab1:
        st.subheader("Class Distribution")
        st.caption("Checks if all classes have enough examples. A high imbalance ratio means the model might become biased toward the majority class.")
        counts = res['distribution']['class_counts']
        fig = px.bar(x=list(counts.keys()), y=list(counts.values()), labels={'x':'Class', 'y':'Count'})
        st.plotly_chart(fig)
        st.metric("Imbalance Ratio", f"{res['distribution']['imbalance_ratio']:.2f}:1")
        
    with tab2:
        st.subheader("Image Quality")
        st.caption("Looks for image issues like blur or poor lighting that can hinder the model's ability to extract meaningful features.")
        st.metric("Blurred Images (%)", f"{res['quality']['pct_blurred']:.1f}%")
        st.metric("Underexposed Images (%)", f"{res['quality']['pct_underexposed']:.1f}%")
        if 'quality_blur' in df.columns:
            fig = px.box(df, x="ground_truth_class", y="quality_blur", title="Blur Distribution by Class")
            st.plotly_chart(fig)
            
    with tab3:
        st.subheader("Duplicates")
        st.caption("Finds copied images that can skew training and lead to data leakage if they appear in both training and testing sets.")
        st.metric("Exact Duplicates", res['duplicates']['exact_duplicates'])
        st.metric("Redundancy Ratio", f"{res['duplicates']['redundancy_ratio']*100:.1f}%")
        
    with tab4:
        st.subheader("Visual Diversity")
        st.caption("Measures visual variety. A higher cluster entropy means your dataset captures a wider variety of real-world scenarios, making your model more robust.")
        st.metric("Cluster Entropy", f"{res['diversity']['cluster_entropy']:.2f}")
        
    with tab5:
        st.subheader("Label Integrity")
        st.caption("Identifies potentially incorrect tags. High label noise can severely degrade model accuracy by teaching it the wrong associations.")
        st.metric("Suspected Mislabels", f"{res['labels']['label_noise_rate']*100:.1f}%")
        if 'flag_suspected_mislabel' in df.columns and df['flag_suspected_mislabel'].sum() > 0:
            suspicious = df[df['flag_suspected_mislabel']]
            st.dataframe(suspicious[['path', 'ground_truth_class', 'predicted_class', 'label_issue_prob']].head())

    st.divider()

    # 5. Recommendations
    st.header("5. Recommendations")
    
    with st.expander("What does this mean?", expanded=True):
        st.write("These are actionable steps to fix the issues detected above, ordered by their severity. Addressing critical recommendations will have the most significant impact on your dataset's readiness and model performance.")

    recs = res.get('recommendations', [])
    for r in recs:
        if r['priority'] in ['Critical', 'High']:
            st.error(f"**[CRITICAL: {r['category']}]**: {r['action']}")
        elif r['priority'] == 'Medium':
            st.warning(f"**[MEDIUM: {r['category']}]**: {r['action']}")
        else:
            st.success(f"**[OK: {r['category']}]**: {r['action']}")
