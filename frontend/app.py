import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import joblib
import json
import os
from pathlib import Path

st.set_page_config(page_title="Pre-release Movie Success Analysis", layout="wide")

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
# Use __file__ so paths work both locally and on Streamlit Cloud
_HERE = Path(__file__).parent          # frontend/
_ROOT = _HERE.parent                   # repo root

ARTIFACTS_DIR = str(_ROOT / "artifacts")
VIZ_DIR = str(_ROOT / "artifacts" / "visualizations")

CANDIDATE_PATHS = [
    str(_ROOT / "artifacts" / "movies_final.csv"),
    str(_ROOT / "data" / "processed" / "movie_dataset_processed.csv"),
]

# Visualization categories for organized display
VIZ_CATEGORIES = {
    "Data Collection": [
        "movies_by_year_timeline",
        "budget_distribution_by_year",
    ],
    "Data Quality": [
        "data_completeness_heatmap",
        "missing_values_by_feature",
    ],
    "Exploratory Analysis": [
        "budget_vs_gross_roi",
        "outliers_numerical_features",
        "correlation_matrix_numerical_features",
        "feature_correlation_with_success_class",
        "pairplot_top_features",
        "runtime_outlier_capping",
    ],
    "Feature Engineering": [
        "feature_engineering_flow",
    ],
    "Model Performance": [
        "confusion_matrix_decision_tree",
        "confusion_matrix_random_forest",
        "confusion_matrix_forward_selection",
        "confusion_matrix_xgboost_tuned",
        "roc_curves",
        "precision_recall_curves",
        "learning_curve_xgboost",
        "train_vs_test_performance",
    ],
    "Feature Selection": [
        "forward_selection_progress",
        "forward_selected_feature_importances",
        "xgboost_feature_importances",
        "feature_importance_comparison",
        "feature_importances_xgboost_tuned",
        "feature_importances_grid_search",
    ],
    "Hyperparameter Tuning": [
        "validation_curve_n_estimators",
        "hyperparameter_impact_heatmap",
        "grid_search_performance_comparison",
    ],
    "Error Analysis": [
        "misclassification_error_type_distribution",
    ],
}

@st.cache_data
def load_data() -> pd.DataFrame:
    for path in CANDIDATE_PATHS:
        try:
            df = pd.read_csv(path)
            df["__source_path"] = path
            return df
        except FileNotFoundError:
            continue
    return pd.DataFrame()

@st.cache_data
def load_visualization(filename: str):
    """Load a Plotly figure from JSON file."""
    filepath = os.path.join(VIZ_DIR, filename)
    try:
        with open(filepath, "r") as f:
            return pio.from_json(f.read())
    except FileNotFoundError:
        return None

@st.cache_data
def get_available_visualizations():
    """Get all available visualization files organized by type."""
    viz_files = {"json": [], "png": [], "html": []}
    
    if os.path.exists(VIZ_DIR):
        for f in os.listdir(VIZ_DIR):
            if f.endswith('.json'):
                viz_files["json"].append(f)
            elif f.endswith('.png'):
                viz_files["png"].append(f)
            elif f.endswith('.html'):
                viz_files["html"].append(f)
    
    return viz_files

@st.cache_data
def load_metrics() -> pd.DataFrame:
    """Load model metrics from artifacts."""
    try:
        return pd.read_csv(f"{ARTIFACTS_DIR}/model_metrics.csv")
    except FileNotFoundError:
        return pd.DataFrame()

@st.cache_data
def load_feature_importance() -> pd.DataFrame:
    """Load feature importance from artifacts."""
    try:
        return pd.read_csv(f"{ARTIFACTS_DIR}/feature_importance.csv")
    except FileNotFoundError:
        return pd.DataFrame()

def get_movie_data() -> pd.DataFrame:
    return load_data()

def display_visualization(viz_name: str):
    """Display a visualization (JSON or PNG) by name."""
    json_path = os.path.join(VIZ_DIR, f"{viz_name}.json")
    png_path = os.path.join(VIZ_DIR, f"{viz_name}.png")
    
    # Try JSON first (interactive Plotly)
    if os.path.exists(json_path):
        fig = load_visualization(f"{viz_name}.json")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            return True
    
    # Fall back to PNG (static matplotlib/seaborn)
    if os.path.exists(png_path):
        st.image(png_path, use_container_width=True)
        return True
    
    return False

# ---------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------
def page_executive_summary():
    st.title("Pre-release Movie Success Analysis")
    st.write("Predict whether a movie will be a **Hit** or a **Flop** using only pre-release data.")
    
    st.markdown("""
    > A movie is classified as a **Hit** if its worldwide box office revenue is at least **2x its production budget** (ROI ≥ 100%), and a **Flop** otherwise.
    """)

    df = get_movie_data()
    if not df.empty:
        display_df = df.drop(columns=["__source_path"], errors="ignore")
        st.dataframe(display_df, use_container_width=True)

    st.markdown("---")

    # Problem Statement
    st.subheader("Motivation")
    st.markdown("""
    The film industry is a high-risk, capital-intensive market:
    - Studios invest **$65–100 million** per film on average
    - Only **40%** of theatrical releases are profitable
    - Industry losses: **billions annually** due to box office failures
    
    **Better prediction = Better decisions = Reduced financial risk**
    """)
    # Solution
    st.subheader("Methodology")
    st.markdown("""
    This project uses **machine learning** to predict movie success before release, enabling:
    - Data-driven greenlighting decisions
    - Optimized marketing spend and release timing
    - Early identification of high-risk projects
    - Understanding which factors drive box office success
    """)
    # Questions
    st.subheader("Questions")
    st.markdown("""
    - Can we predict movie success (Hit vs Flop) using pre-release features?
    - Which features are most important for predicting box office success?
    - How do different machine learning algorithms compare for this classification task?
    """)


def display_visualization(viz_name: str, key_suffix: str = ""):
    """Display a visualization (JSON or PNG) by name."""
    json_path = os.path.join(VIZ_DIR, f"{viz_name}.json")
    png_path = os.path.join(VIZ_DIR, f"{viz_name}.png")
    
    # Try JSON first (interactive Plotly)
    if os.path.exists(json_path):
        fig = load_visualization(f"{viz_name}.json")
        if fig:
            # Use viz_name + key_suffix as unique key
            chart_key = f"viz_{viz_name}_{key_suffix}" if key_suffix else f"viz_{viz_name}"
            st.plotly_chart(fig, use_container_width=True, key=chart_key)
            return True
    
    # Fall back to PNG (static matplotlib/seaborn)
    if os.path.exists(png_path):
        st.image(png_path, use_container_width=True)
        return True
    
    return False

def page_market_and_data_insights():
    st.header("Market and Data Insights")
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("""
        **Data:**
        - The Numbers database: 6,000+ movies with budgets, revenues, release data, other features 
        - IMDB database: Cast & Crew data
        - Google Trends: Movie popularity and search interest 
        """)
    with col_right:
        st.markdown("""
        | Source | Data Collected |
        |--------|---------------|
        | **The Numbers** | Budget, worldwide gross, domestic gross, release dates | 
        | **The Numbers (Metadata)** | Runtime, genre, creative type, franchise, production companies, countries, languages, director, cast |
        | **IMDB** | Director names, writer names | 
        | **Google Trends** | Pre-release search interest | 
        """)
    
    viz_files = get_available_visualizations()
    total_viz = len(viz_files["json"]) + len(viz_files["png"])
    
    if total_viz > 0:
        
        # Create tabs for organized sections
        tabs = st.tabs(["Data Collection", "Data Quality", "Distributions & Outliers", "Correlations"])
        
        with tabs[0]:
            st.subheader("Movies Timeline & Budget Trends")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Movies Collected by Year**")
                if not display_visualization("movies_by_year_timeline", "timeline"):
                    st.info("Timeline visualization not found. Run notebook to generate.")
            
            with col2:
                st.write("**Budget Distribution by Year**")
                if not display_visualization("budget_distribution_by_year", "budget_dist"):
                    st.info("Budget distribution visualization not found.")
        
        with tabs[1]:
            st.subheader("Data Completeness & Quality")
            col1, col2 = st.columns(2)
            with col1:
                if not display_visualization("data_completeness_heatmap", "completeness"):
                    st.info("Data completeness heatmap not found")
            with col2:
                if not display_visualization("missing_values_by_feature", "missing"):
                    st.info("Missing values chart not found")
        
        with tabs[2]:
            st.subheader("Budget vs Revenue & ROI")
            display_visualization("budget_vs_gross_roi", "roi")
            
            st.subheader("Outliers in Numerical Features")
            display_visualization("outliers_numerical_features", "outliers")
            
            st.subheader("Runtime Outlier Treatment")
            display_visualization("runtime_outlier_capping", "runtime")
        
        with tabs[3]:
            st.subheader("Correlation Matrix")
            display_visualization("correlation_matrix_numerical_features", "corr_matrix")
            
            st.subheader("Feature Correlation with Target (Hit/Flop)")
            display_visualization("feature_correlation_with_success_class", "target_corr")
        
    else:
        st.warning("No visualizations found. Run the notebook cells to generate them.")
        st.code("""
# In notebook, add these lines after creating figures:
# For Plotly:
fig.write_json(f"{VIZ_DIR}/your_chart_name.json")

# For Matplotlib/Seaborn:
plt.savefig(f"{VIZ_DIR}/your_chart_name.png", dpi=150, bbox_inches='tight')
        """)


def page_feature_engineering():
    st.header("Feature Engineering")
    
    # Feature Engineering Flow
    st.subheader("Feature Transformation Pipeline")
    if not display_visualization("feature_engineering_flow"):
        st.info("Feature engineering flow diagram not found")
    

def page_performance_comparison():
    st.header("Performance Comparison")
    
    # Load metrics
    metrics_df = load_metrics()
    
    if not metrics_df.empty:

        # Train vs Test Performance
        st.subheader("Train vs Test Performance")
        display_visualization("train_vs_test_performance")

        # Forward Selection
        st.subheader("Forward Feature Selection")
        col1, col2 = st.columns(2)
        with col1:
            display_visualization("forward_selection_progress")
        with col2:
            display_visualization("forward_selected_feature_importances")
        
        # Feature Importance Comparison
        st.subheader("Feature Importance Across Models")
        display_visualization("feature_importance_comparison")
    else:
        st.warning("Model metrics not found. Run notebook to generate artifacts/model_metrics.csv")
    
    # Tabs for different performance views
    tabs = st.tabs(["ROC Curves", "Learning Curves", "Feature Importance"])
    
    with tabs[0]:
        st.subheader("ROC Curves")
        display_visualization("roc_curves")
    
    with tabs[1]:
        st.subheader("Learning Curve - XGBoost")
        display_visualization("learning_curve_xgboost")
    
    with tabs[2]:
        st.subheader("Feature Importance - Tuned XGBoost")
        fi_df = load_feature_importance()
        
        if not fi_df.empty:
            fig_fi = px.bar(
                fi_df.head(15), 
                x='importance', 
                y='feature', 
                orientation='h',
                title='Top Feature Importances'
            )
            fig_fi.update_layout(
                template='plotly_white', 
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_fi, use_container_width=True)
        
        display_visualization("feature_importances_xgboost_tuned")

def page_decision_simulator():
    st.header("Decision Simulator")
    
    st.markdown("""
    Enter movie details below to predict whether it will be a **Hit** or a **Flop** based on pre-release data.
    """)
    
    # Try to load the model
    model = None
    try:
        model = joblib.load(f"{ARTIFACTS_DIR}/best_model.joblib")
        st.success("Model loaded successfully!")
    except FileNotFoundError:
        st.warning(" Model not found. Using demo heuristic instead.")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Movie Details")
        
        # Budget input (in millions)
        budget_millions = st.number_input(
            "Production Budget ($ millions)", 
            min_value=0.1, 
            max_value=500.0, 
            value=50.0, 
            step=5.0,
            help="Typical range: $10M - $200M"
        )
        log_budget = np.log(budget_millions * 1_000_000)
        
        # Director performance
        director_avg_gross_millions = st.number_input(
            "Director's Average Box Office ($ millions)", 
            min_value=0.0, 
            max_value=2000.0, 
            value=100.0, 
            step=10.0,
            help="Average worldwide gross from director's previous films"
        )
        director_avg_gross = np.log(director_avg_gross_millions * 1_000_000 + 1)
        
        # Writer performance
        writer_avg_gross_millions = st.number_input(
            "Writer's Average Box Office ($ millions)", 
            min_value=0.0, 
            max_value=1500.0, 
            value=75.0, 
            step=10.0,
            help="Average worldwide gross from writer's previous films"
        )
        writer_avg_gross = np.log(writer_avg_gross_millions * 1_000_000 + 1)
        
        # Categorical features
        col_a, col_b = st.columns(2)
        
        with col_a:
            is_franchise = st.checkbox("Franchise/Sequel", value=False)
            is_summer_release = st.checkbox("Summer Release (May-Aug)", value=True)
        
        with col_b:
            is_holiday_release = st.checkbox("Holiday Release (Nov-Dec)", value=False)
            is_action = st.checkbox("Action/Adventure Genre", value=False)
        
        # Google Trends (interest score)
        google_trends = st.slider(
            "Pre-Release Interest (Google Trends)", 
            min_value=0, 
            max_value=100, 
            value=50, 
            step=5,
            help="Google search interest score (0-100)"
        )
        log_trends = np.log(google_trends + 1)
        
        # Runtime
        runtime_minutes = st.slider(
            "Runtime (minutes)", 
            min_value=60, 
            max_value=240, 
            value=120, 
            step=5
        )

        release_year = st.number_input(
            "Release Year",
            min_value=1980,
            max_value=2026,
            value=2024,
            step=1
        )
    
    with col2:
        st.subheader("Prediction Results")
        
        # Display input summary
        with st.expander("Input Summary", expanded=True):
            st.markdown(f"""
            - **Budget:** ${budget_millions:.1f}M
            - **Director Track Record:** ${director_avg_gross_millions:.1f}M avg
            - **Writer Track Record:** ${writer_avg_gross_millions:.1f}M avg
            - **Franchise:** {'Yes' if is_franchise else 'No'}
            - **Summer Release:** {'Yes' if is_summer_release else 'No'}
            - **Holiday Release:** {'Yes' if is_holiday_release else 'No'}
            - **Action/Adventure:** {'Yes' if is_action else 'No'}
            - **Pre-Release Interest:** {google_trends}/100
            - **Runtime:** {runtime_minutes} min
            - **Release Year:** {release_year}
            """)
        
        if st.button("Predict Success", type="primary", use_container_width=True):
            if model:
                # Create input DataFrame with selected features
                try:
                    selected_features = pd.read_csv(f"{ARTIFACTS_DIR}/selected_features.csv")['feature'].tolist()
                    
                    # Build input dict with zeros for all features
                    input_data = {feat: 0 for feat in selected_features}
                    
                    # Fill in known values
                    if 'log_budget' in input_data:
                        input_data['log_budget'] = log_budget
                    if 'director_avg_gross' in input_data:
                        input_data['director_avg_gross'] = director_avg_gross
                    if 'writer_avg_gross' in input_data:
                        input_data['writer_avg_gross'] = writer_avg_gross
                    if 'is_franchise' in input_data:
                        input_data['is_franchise'] = int(is_franchise)
                    if 'is_summer_release' in input_data:
                        input_data['is_summer_release'] = int(is_summer_release)
                    if 'is_holiday_release' in input_data:
                        input_data['is_holiday_release'] = int(is_holiday_release)
                    if 'log_google_trends_average' in input_data:
                        input_data['log_google_trends_average'] = log_trends
                    if 'runtime' in input_data:
                        input_data['runtime'] = runtime_minutes
                    if 'is_action' in input_data or 'genre_Action' in input_data:
                        key = 'is_action' if 'is_action' in input_data else 'genre_Action'
                        input_data[key] = int(is_action)
                    if 'release_year' in input_data:
                        input_data['release_year'] = release_year
                    
                    X_input = pd.DataFrame([input_data])
                    prediction = model.predict(X_input)[0]
                    proba = model.predict_proba(X_input)[0]
                    
                    st.markdown("---")
                    

                    if prediction == 1:
                        st.success("### Predicted: **HIT!**")
                        st.metric("Success Probability", f"{proba[1]*100:.1f}%", delta=None)
                        st.progress(float(proba[1]))  # Convert to float
                        
                        st.info("""
                        **Confidence Level:** This movie has strong indicators for commercial success. 
                        Consider moving forward with production and marketing.
                        """)
                    else:
                        st.error("### Predicted: **FLOP**")
                        st.metric("Success Probability", f"{proba[1]*100:.1f}%", delta=f"{(proba[1]-0.5)*100:.1f}%")
                        st.progress(float(proba[1]))  # Convert to float
                        
                        st.warning("""
                        **Risk Assessment:** This movie shows weak indicators for profitability. 
                        Consider adjusting budget, talent, or release strategy.
                        """)

                    
                    # ROI Estimation
                    expected_roi = proba[1] * 150 + (1 - proba[1]) * (-30)
                    st.markdown(f"**Estimated ROI:** {expected_roi:.1f}%")
                        
                except Exception as e:
                    st.error(f" Prediction error: {e}")
            else:
                # Demo heuristic (simplified scoring)
                score = 0
                score += (budget_millions / 100) * 2  # Budget weight
                score += (director_avg_gross_millions / 100) * 1.5  # Director weight
                score += (writer_avg_gross_millions / 100) * 1.0  # Writer weight
                score += 1.5 if is_franchise else 0
                score += 0.8 if is_summer_release else 0
                score += 0.6 if is_holiday_release else 0
                score += 0.5 if is_action else 0
                score += (google_trends / 50) * 0.5
                
                st.markdown("---")
                
                if score > 5:
                    st.success("###  Predicted: **HIT!** (Demo)")
                    success_prob = min(0.95, 0.5 + (score - 5) * 0.1)
                    st.metric("Success Probability", f"{success_prob*100:.1f}%")
                    st.progress(success_prob)
                    st.info(f"Demo Score: {score:.2f}/10")
                else:
                    st.error("###  Predicted: **FLOP** (Demo)")
                    success_prob = max(0.05, 0.5 - (5 - score) * 0.1)
                    st.metric("Success Probability", f"{success_prob*100:.1f}%")
                    st.progress(success_prob)
                    st.warning(f"Demo Score: {score:.2f}/10")
    
    st.markdown("---")

def page_business_insights():
    st.header("Business Insights")
    
    st.markdown("""
    Our analysis of pre-release movie data highlights several clear patterns that consistently influence box office outcomes:
    """)
    # Key Findings
    st.subheader("Key Findings")
    
    finding_col1, finding_col2, finding_col3, finding_col4 = st.columns(4)
    with finding_col1:
        st.info("**Franchise Status** \n\nSequels and franchises have higher success rates") 
    with finding_col2:
        st.info("**Marketing** \n\n Pre-release buzz strongly predicts performance")
    with finding_col3:
        st.info("**Crew Track Record** \n\nTeams' past box office performance is highly predictive")
    with finding_col4:   
        st.info("**Budget Matters** \n\nHigher production budgets correlate with greater commercial success")
    
    st.markdown("---")
    
    # Strategic Recommendations
    st.subheader("Strategic Recommendations")
    
    rec_col1, rec_col2, rec_col3 = st.columns(3)
    
    with rec_col1:
        st.markdown("""
        **For Producers:**
        -  Secure proven directors/writers
        -  Align budget with genre norms
        -  Consider franchise potential early
        -  Plan release windows strategically
        """)
    
    with rec_col2:
        st.markdown("""
        **For Studios:**
        -  Invest in franchise development
        -  Use ML models for greenlight decisions
        -  Optimize portfolio across risk levels
        """)
    
    with rec_col3:
        st.markdown("""
        **For Marketers:**
        -  Amplify pre-release buzz metrics
        -  Target release windows carefully
        -  Leverage franchise recognition
        -  Adjust spend based on success probability
        """)

def page_limitations_and_future_work():
    st.header("Limitations and Future Work")
    
    st.subheader("Current Limitations")
    st.markdown("""
    - **Data Scope:** Limited to The Numbers dataset; may miss niche markets and may not be representative globally
    - **Feature Set:** Only pre-release features; excludes social media sentiment
    - **Model Generalizability:** Performance may vary across genres/markets
    - **Dynamic Market Factors:** Unpredictable events like pandemics not modeled
    """)
    
    st.subheader("Future Enhancements")
    st.markdown("""
    - **Expanded Datasets:** Integrate IMDb, Rotten Tomatoes, social media data and cast details
    - **Real-time Updates:** Incorporate live pre-release buzz metrics
    - **User Interface:** Develop a full-featured web app for industry use
    """)

# ---------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------
PAGES = {
    "Executive Summary": page_executive_summary,
    "Market and Data Insights": page_market_and_data_insights,
    "Feature Engineering": page_feature_engineering,
    "Performance Comparison": page_performance_comparison,
    "Decision Simulator": page_decision_simulator,
    "Business Insights": page_business_insights,
    "Limitations and Future Work": page_limitations_and_future_work,
}


st.sidebar.title("Movie Success Analysis")
choice = st.sidebar.radio("Go to", list(PAGES.keys()))
PAGES[choice]()

# Sidebar 
st.sidebar.markdown("---")
st.sidebar.markdown("**Author:**")
st.sidebar.markdown("""Saptak Chakraborty""")
st.sidebar.markdown("[GitLab](https://code.ovgu.de/laqy26jo/movie-success-analysis) | [Website](https://movie-success-analysis.netlify.app/)")