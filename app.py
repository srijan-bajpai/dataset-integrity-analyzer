import os
import sys
from pathlib import Path

repo_root = str(Path(__file__).resolve().parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import numpy as np

from dia.core.orchestrator import DIAOrchestrator

st.set_page_config(page_title="Dataset Integrity Analyzer", layout="wide")

st.title("Dataset Integrity Analyzer (DIA)")
st.markdown("Legacy local demo interface; use the DIA 2.0 API for database-backed audits")

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

# --- Helper: generate a dynamic conclusion sentence based on actual data ---
def _readiness_conclusion(score, verdict, sub_scores):
    """Return a plain-language summary of the AI Readiness Score."""
    weak = [k for k, v in sub_scores.items() if v < 50]
    if verdict == "Insufficient Coverage":
        return "Too few audit dimensions were available for a readiness verdict. Review unavailable checks and provide metadata or image labels where appropriate."
    if score > 85:
        return "This dataset is in strong shape overall. All dimensions score well, and the dataset is suitable for production model training without major remediation."
    elif score > 70:
        return f"The dataset is in acceptable condition but has room for improvement. Consider reviewing the weaker dimensions ({', '.join(weak) if weak else 'none flagged'}) before finalising your training pipeline."
    elif score > 50:
        msg = f"The dataset needs remediation before it can reliably train a model. "
        if weak:
            msg += f"The following dimensions are dragging the score down: {', '.join(weak)}. Fixing these will have the most impact."
        return msg
    else:
        msg = "This dataset has critical issues that will severely harm any model trained on it. "
        if weak:
            msg += f"The worst-performing areas are: {', '.join(weak)}. These must be addressed before proceeding."
        return msg


if st.session_state.analysis_complete:
    res = st.session_state.results
    df = st.session_state.df
    
    # ------------------------------------------------------------------ #
    # 1. AI Readiness Score
    # ------------------------------------------------------------------ #
    st.header("1. AI Readiness Score")
    score = res['readiness']['overall_score']
    verdict = res['readiness']['verdict']
    sub_scores = res['readiness']['sub_scores']
    score_coverage = res['readiness'].get('coverage_pct', 100)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        color = "green" if score > 80 else "orange" if score > 50 else "red"
        st.markdown(f"<h1 style='text-align: center; color: {color}; font-size: 5em;'>{score}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{verdict}</h3>", unsafe_allow_html=True)
        st.caption(f"Scored coverage: {score_coverage:.0f}%")
        
    with col2:
        # Radar Chart for sub-scores
        categories = list(sub_scores.keys())
        values = list(sub_scores.values())
        
        # Map dimension names to plain-language hover descriptions
        dim_explanations = {
            'Balance': 'How evenly samples are distributed across classes (100 = perfectly even)',
            'Fairness': 'Group representation compared with targets you provide; without a target this dimension is not scored',
            'Quality': 'Image sharpness, exposure, and contrast (100 = no defects found)',
            'Uniqueness': 'How free the dataset is from duplicate images (100 = no duplicates)',
            'Diversity': 'How visually varied the images are (100 = maximum variety)',
            'Label Integrity': 'How reliable the class labels are (100 = no suspected mislabels)',
        }
        hover_texts = [dim_explanations.get(c, c) + f'<br>Score: {v:.1f}/100' for c, v in zip(categories, values)]

        fig = go.Figure(data=go.Scatterpolar(
          r=values + [values[0]],
          theta=categories + [categories[0]],
          fill='toself',
          marker=dict(color='blue'),
          text=hover_texts + [hover_texts[0]],
          hoverinfo='text',
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=300)
        st.plotly_chart(fig, width='stretch')

    st.info(_readiness_conclusion(score, verdict, sub_scores))
        
    st.divider()
    
    # ------------------------------------------------------------------ #
    # 2. Bias Impact Prediction
    # ------------------------------------------------------------------ #
    st.header("2. Accuracy Impact Estimate")
    impact = res.get('bias_impact', {})
    if impact.get("is_validated") and impact.get("expected_accuracy_drop_pct") is not None:
        st.metric("Validated estimated accuracy change", f"-{impact['expected_accuracy_drop_pct']}%")
        st.caption("This estimate is available only for dataset conditions covered by the validation benchmark.")
    else:
        st.info("A training-impact estimate is unavailable because DIA has no validated impact model yet. Review the measured dataset findings below.")

    st.divider()
    
    # ------------------------------------------------------------------ #
    # 3. Cross-Dimensional Confounds
    # ------------------------------------------------------------------ #
    st.header("3. Cross-Dimensional Confounds")

    confounds = res.get('confounds', {}).get('detected_confounds', [])
    if not confounds:
        st.info("No configured association crossed the current screening thresholds. This does not establish that dataset dimensions are independent.")
    else:
        for c in confounds:
            ctype = c['type']
            desc = c['description']
            
            # Render the finding
            st.error(f"**{ctype}** -- {desc}")

        # Dynamic summary based on what was actually found
        quality_confounds = [c for c in confounds if c['type'] == 'Quality-Class Confound']
        redundancy_confounds = [c for c in confounds if c['type'] == 'Redundancy-Class Confound']
        label_confounds = [c for c in confounds if c['type'] == 'LabelNoise-Class Confound']

        parts = []
        if quality_confounds:
            metrics = [c['dimension_a'].replace('quality_', '') for c in quality_confounds]
            parts.append(
                f"Image quality ({', '.join(metrics)}) is not uniform across classes. "
                "This means the model may learn to associate visual artefacts (e.g. blur or brightness) "
                "with specific classes instead of learning their actual distinguishing features."
            )
        if redundancy_confounds:
            affected = [c.get('affected_group', '?') for c in redundancy_confounds]
            parts.append(
                f"Class(es) '{', '.join(affected)}' contain a high proportion of duplicate images. "
                "The model may memorise these repeated examples rather than generalising, "
                "and duplicates leaking into the test set will inflate reported accuracy."
            )
        if label_confounds:
            affected = [c.get('affected_group', '?') for c in label_confounds]
            parts.append(
                f"Class(es) '{', '.join(affected)}' have an unusually high rate of suspected mislabels. "
                "The model will be trained on contradictory information for these categories, "
                "which typically results in lower confidence and accuracy for those classes."
            )

        if parts:
            st.info("**In plain terms:** " + " Additionally, ".join(parts))
            
    st.divider()
    
    # ------------------------------------------------------------------ #
    # 4. Dimensional Deep Dive
    # ------------------------------------------------------------------ #
    st.header("4. Dimensional Deep Dive")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Balance", "Quality", "Duplicates", "Diversity", "Labels"])
    
    # --- Balance ---
    with tab1:
        st.subheader("Class Distribution")
        counts = res['distribution']['class_counts']
        ir = res['distribution']['imbalance_ratio']
        severity = res['distribution'].get('imbalance_severity', '')

        fig = px.bar(x=list(counts.keys()), y=list(counts.values()), labels={'x':'Class', 'y':'Sample Count'})
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>Sample Count: %{y}<br><i>Number of images in this class</i><extra></extra>'
        )
        st.plotly_chart(fig)
        st.metric("Imbalance Ratio", f"{ir:.2f}:1",
                  help="The ratio of the largest class to the smallest class. A ratio of 1:1 means perfectly balanced. Higher ratios mean some classes have far more images than others.")

        # Dynamic conclusion
        max_class = max(counts, key=counts.get)
        min_class = min(counts, key=counts.get)
        if ir <= 1.5:
            st.info(
                f"The classes are well balanced. The largest class ('{max_class}', {counts[max_class]} samples) "
                f"and the smallest ('{min_class}', {counts[min_class]} samples) are close in size. "
                "No rebalancing is needed."
            )
        elif ir <= 3.0:
            st.info(
                f"There is a mild imbalance: '{max_class}' has {counts[max_class]} samples while "
                f"'{min_class}' has only {counts[min_class]}. The model may slightly favour the larger class, "
                "but this is generally manageable with standard techniques like class-weighted loss."
            )
        else:
            st.warning(
                f"The dataset is significantly imbalanced ({severity.lower()} severity). "
                f"'{max_class}' has {counts[max_class]} samples, which is {ir:.1f}x more than "
                f"'{min_class}' ({counts[min_class]} samples). A model trained on this will likely "
                "perform poorly on the minority classes. Consider collecting more data for underrepresented "
                "classes, or applying oversampling / undersampling techniques."
            )
        
    # --- Quality ---
    with tab2:
        st.subheader("Image Quality")

        pct_blur = res['quality']['pct_blurred']
        pct_under = res['quality']['pct_underexposed']

        q_col1, q_col2 = st.columns(2)
        q_col1.metric("Blurred Images", f"{pct_blur:.1f}%",
                       help="Percentage of images with a blur score below the sharpness threshold (variance of Laplacian < 100). Blurry images make it harder for models to learn fine-grained features.")
        q_col2.metric("Underexposed Images", f"{pct_under:.1f}%",
                       help="Percentage of images that are too dark (average brightness below 40 on a 0-255 scale). Dark images contain less distinguishable detail for the model.")

        if 'quality_blur' in df.columns:
            fig = go.Figure()
            classes_sorted = sorted(df['ground_truth_class'].unique())
            for cls in classes_sorted:
                cls_vals = df[df['ground_truth_class'] == cls]['quality_blur'].dropna()
                if len(cls_vals) == 0:
                    continue

                q1_val = float(np.percentile(cls_vals, 25))
                med_val = float(np.percentile(cls_vals, 50))
                q3_val = float(np.percentile(cls_vals, 75))
                iqr = q3_val - q1_val
                lower_f = float(max(cls_vals.min(), q1_val - 1.5 * iqr))
                upper_f = float(min(cls_vals.max(), q3_val + 1.5 * iqr))
                min_val = float(cls_vals.min())
                max_val = float(cls_vals.max())

                # Standard box trace (default hover disabled)
                fig.add_trace(go.Box(
                    y=cls_vals,
                    name=cls,
                    boxpoints='outliers',
                    hoverinfo='skip',
                    marker_color='#636EFA',
                ))

                # Invisible scatter at the median to carry the custom hover
                hover_text = (
                    f"<b>{cls}</b><br><br>"
                    f"<b>Max</b> (highest blur score): {max_val:,.1f}<br>"
                    f"<b>Upper Fence</b> (above this = outlier): {upper_f:,.1f}<br>"
                    f"<b>Q3</b> (75% of images are below this): {q3_val:,.1f}<br>"
                    f"<b>Median</b> (middle value): {med_val:,.1f}<br>"
                    f"<b>Q1</b> (25% of images are below this): {q1_val:,.1f}<br>"
                    f"<b>Lower Fence</b> (below this = outlier): {lower_f:,.1f}<br>"
                    f"<b>Min</b> (lowest blur score): {min_val:,.1f}<br>"
                    f"<br><i>Higher score = sharper image</i>"
                )
                fig.add_trace(go.Scatter(
                    x=[cls], y=[med_val],
                    mode='markers',
                    marker=dict(size=12, color='rgba(0,0,0,0)'),
                    hoverinfo='text',
                    hovertext=hover_text,
                    showlegend=False,
                ))

            fig.update_layout(
                title="Blur Distribution by Class",
                xaxis_title="Class",
                yaxis_title="Blur Score (Variance of Laplacian)",
                showlegend=False,
            )
            st.plotly_chart(fig)
            st.caption(
                "**How to read this chart:** Each box shows the middle 50% of blur scores for a class. "
                "The line inside the box is the median. Whiskers extend to the farthest non-outlier values. "
                "Dots beyond the whiskers are outliers. Higher blur scores mean sharper images."
            )

        total_defect = pct_blur + pct_under
        if total_defect < 3:
            st.info(
                f"Image quality is strong. Only {pct_blur:.1f}% of images are blurry and {pct_under:.1f}% "
                "are underexposed. The model should have no trouble extracting useful features from this data."
            )
        elif total_defect < 15:
            st.info(
                f"A moderate number of images have quality issues: {pct_blur:.1f}% are blurry and "
                f"{pct_under:.1f}% are too dark. These images provide weaker training signal. "
                "Review the box plot above -- if quality problems cluster in specific classes, "
                "that is a more serious concern (see the Confounds section)."
            )
        else:
            st.warning(
                f"A substantial portion of the dataset has quality problems ({pct_blur:.1f}% blurry, "
                f"{pct_under:.1f}% underexposed). This will reduce the model's ability to learn "
                "meaningful patterns. Consider removing or re-capturing the worst offenders."
            )
            
    # --- Duplicates ---
    with tab3:
        st.subheader("Duplicates")

        exact_dups = res['duplicates']['exact_duplicates']
        redundancy = res['duplicates']['redundancy_ratio']
        dup_groups = res['duplicates'].get('duplicate_groups', 0)

        d_col1, d_col2 = st.columns(2)
        d_col1.metric("Exact Duplicates", exact_dups,
                      help="The number of images that are visually identical to another image in the dataset (detected via perceptual hashing).")
        d_col2.metric("Redundancy Rate", f"{redundancy*100:.1f}%",
                      help="The percentage of total images that are duplicates. A high rate means a significant fraction of your dataset is repeated data rather than new information.")

        if exact_dups == 0:
            st.info(
                "No exact duplicate images were found. Each sample in the dataset is visually unique, "
                "which means no risk of data leakage from identical images appearing in train and test splits."
            )
        elif redundancy < 0.05:
            st.info(
                f"{exact_dups} duplicate image(s) were found across {dup_groups} group(s), "
                f"resulting in a {redundancy*100:.1f}% redundancy rate. This is a low level "
                "and unlikely to meaningfully affect training, but deduplicating is still recommended "
                "to avoid any risk of train/test leakage."
            )
        else:
            st.warning(
                f"{exact_dups} duplicate images were found ({redundancy*100:.1f}% of the dataset). "
                "This is a significant amount. Duplicates can cause the model to memorise specific images "
                "instead of learning general patterns, and if duplicates appear in both training and test "
                "sets, your evaluation metrics will be artificially inflated. Remove the duplicates before training."
            )
        
    # --- Diversity ---
    with tab4:
        st.subheader("Visual Diversity")

        cluster_entropy = res['diversity']['cluster_entropy']
        mean_dist = res['diversity'].get('mean_pairwise_distance', 0)

        dv_col1, dv_col2 = st.columns(2)
        dv_col1.metric("Cluster Entropy", f"{cluster_entropy:.2f}",
                       help="Measures how evenly images are spread across visual groups (clusters). Ranges from 0 to 1. A value near 1.0 means images are spread evenly across many visual styles. A value near 0 means most images look alike.")
        dv_col2.metric("Avg. Pairwise Distance", f"{mean_dist:.3f}",
                       help="The average visual difference between any two randomly chosen images (measured via cosine distance on feature embeddings). Higher values mean the images are more visually distinct from each other.")

        if cluster_entropy > 0.85:
            st.info(
                f"Visual diversity is high (entropy {cluster_entropy:.2f} out of 1.0). "
                "The images are spread across many visual clusters, meaning the dataset covers "
                "a broad range of appearances. This generally leads to more robust models."
            )
        elif cluster_entropy > 0.5:
            st.info(
                f"Visual diversity is moderate (entropy {cluster_entropy:.2f} out of 1.0). "
                "Some visual clusters dominate, which means certain types of images are over-represented. "
                "The model may underperform on less-represented visual styles."
            )
        else:
            st.warning(
                f"Visual diversity is low (entropy {cluster_entropy:.2f} out of 1.0). "
                "Most images look similar to each other. A model trained on this data may fail "
                "when encountering real-world images that differ from this narrow visual distribution."
            )
        
    # --- Labels ---
    with tab5:
        st.subheader("Label Integrity")

        noise_rate = res['labels']['label_noise_rate']
        noise_pct = noise_rate * 100

        st.metric("Suspected Mislabel Rate", f"{noise_pct:.1f}%",
                  help="The percentage of images whose assigned class label may be wrong, detected by training a classifier and finding samples where the model's prediction confidently disagrees with the given label.")

        if 'flag_suspected_mislabel' in df.columns and df['flag_suspected_mislabel'].sum() > 0:
            suspicious = df[df['flag_suspected_mislabel']]
            display_df = suspicious[['path', 'ground_truth_class', 'predicted_class', 'label_issue_prob']].head(10)
            display_df = display_df.rename(columns={
                'path': 'File Path',
                'ground_truth_class': 'Current Label',
                'predicted_class': 'Model Thinks It Is',
                'label_issue_prob': 'Confidence Gap',
            })
            st.dataframe(display_df)
            st.caption(
                "**Column guide:** "
                "'Current Label' is the class this image is tagged as in the dataset. "
                "'Model Thinks It Is' is what the classifier predicted instead. "
                "'Confidence Gap' is how strongly the model disagrees with the current label "
                "(higher = more likely to be a genuine mislabel)."
            )

        if noise_pct < 2:
            st.info(
                f"Label quality is high: only {noise_pct:.1f}% of samples were flagged as potential mislabels. "
                "This is within normal tolerance and should not noticeably affect training."
            )
        elif noise_pct < 10:
            st.info(
                f"{noise_pct:.1f}% of images may be mislabelled. This means roughly 1 in "
                f"{int(100/max(noise_pct,0.01))} images could be tagged with the wrong class. "
                "Review the table above to decide whether these are genuine errors. "
                "Even moderate label noise can reduce model accuracy by several percentage points."
            )
        else:
            st.warning(
                f"A high proportion of labels appear incorrect ({noise_pct:.1f}%). "
                "This level of label noise will significantly confuse the model during training. "
                "A manual review of the flagged samples (shown above) is strongly recommended, "
                "or consider re-annotating the most affected classes."
            )

    st.divider()

    # ------------------------------------------------------------------ #
    # 5. Recommendations
    # ------------------------------------------------------------------ #
    st.header("5. Recommendations")

    recs = res.get('recommendations', [])
    if not recs:
        st.success("No issues severe enough to generate recommendations. The dataset is in good shape.")
    else:
        for r in recs:
            if r['priority'] in ['Critical', 'High']:
                st.error(f"**[{r['priority'].upper()}: {r['category']}]** {r['action']}")
            elif r['priority'] == 'Medium':
                st.warning(f"**[MEDIUM: {r['category']}]** {r['action']}")
            else:
                st.success(f"**[{r['category']}]** {r['action']}")

        # Overall recommendation summary
        critical_count = sum(1 for r in recs if r['priority'] in ['Critical', 'High'])
        medium_count = sum(1 for r in recs if r['priority'] == 'Medium')
        if critical_count > 0:
            st.info(
                f"There are {critical_count} high-priority issue(s) that should be resolved before training. "
                f"{'An additional ' + str(medium_count) + ' moderate issue(s) should also be reviewed.' if medium_count else ''} "
                "Start with the items marked CRITICAL or HIGH, as these have the largest effect on model performance."
            )
        elif medium_count > 0:
            st.info(
                f"No critical issues were found, but {medium_count} moderate recommendation(s) are worth addressing "
                "to improve the dataset's overall quality before training."
            )
