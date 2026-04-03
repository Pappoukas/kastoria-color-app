import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kastoria Visual Identity | Data Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DATA LOADING (Με Caching & Διορθωμένο CSV Parsing) ---
@st.cache_data
def load_data():
    # Προσθέσαμε το sep=';' και decimal=',' για να διαβάζει σωστά τα ευρωπαϊκά CSVs
    # Επιπλέον, το skiprows προσαρμόστηκε ακριβώς στις κενές γραμμές κάθε αρχείου
    summary_df = pd.read_csv('data/color_summary_batch_Summary.csv', sep=';', decimal=',', skiprows=2)
    clusters_df = pd.read_csv('data/color_summary_batch_Clusters.csv', sep=';', decimal=',', skiprows=1)
    stats_df = pd.read_csv('data/color_summary_batch_Statistics.csv', sep=';', decimal=',', skiprows=2)
    
    # Καθαρισμός στηλών για το όνομα του μνημείου
    if 'placeInfo/name' in summary_df.columns:
        summary_df['Monument'] = summary_df['placeInfo/name'].fillna('Unknown')
    else:
        summary_df['Monument'] = 'Kastoria Place'
        
    # Merge για να έχουμε τα μνημεία και στα clusters
    clusters_full = pd.merge(clusters_df, summary_df[['Filename', 'Monument']], on='Filename', how='left')
    
    return summary_df, clusters_full, stats_df

try:
    summary_df, clusters_df, stats_df = load_data()
except FileNotFoundError:
    st.error("⚠️ Σφάλμα: Τα αρχεία δεν βρέθηκαν. Βεβαιώσου ότι τα έχεις μετονομάσει ακριβώς σε: 'color_summary_batch_Summary.csv', 'color_summary_batch_Clusters.csv', 'color_summary_batch_Statistics.csv' και τα έχεις βάλει μέσα στο φάκελο 'data'.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Απρόσμενο σφάλμα φόρτωσης: {e}")
    st.stop()

# --- 3. SIDEBAR & BRANDING ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Kastoria_lake.jpg/800px-Kastoria_lake.jpg", use_container_width=True)
st.sidebar.title("Οπτική Ταυτότητα Καστοριάς")
st.sidebar.markdown("""
Ανακαλύψτε την **χρωματική παλέτα** της Καστοριάς μέσα από τα μάτια των επισκεπτών στο TripAdvisor. 
Ένα data-driven εργαλείο για Marketing & PR professionals.
""")

st.sidebar.markdown("---")
# Global Filter
monuments_list = summary_df['Monument'].dropna().unique().tolist()
selected_monument = st.sidebar.selectbox("Επιλογή Μνημείου / Τοποθεσίας", ["Όλα"] + monuments_list)

# Εφαρμογή φίλτρου
if selected_monument != "Όλα":
    summary_df = summary_df[summary_df['Monument'] == selected_monument]
    clusters_df = clusters_df[clusters_df['Monument'] == selected_monument]

# --- 4. MAIN LAYOUT & KPI METRICS ---
st.title("🎨 Kastoria Visitors' Color Analysis")
st.markdown("Ανάλυση χρωμάτων από φωτογραφίες επισκεπτών για την εξαγωγή συμπερασμάτων branding και αισθητικής.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Συνολικές Φωτογραφίες", len(summary_df))
col2.metric("Μοναδικά Μνημεία", summary_df['Monument'].nunique())
col3.metric("Μέση Φωτεινότητα (V%)", f"{summary_df['V% mean'].mean():.1f}%")
col4.metric("Μέση Ενταση (Saturation)", f"{summary_df['S% mean'].mean():.1f}%")

st.markdown("---")

# --- 5. TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Color Frequencies", "🔥 Intensity & Maps", "🌌 Color Profiling (Clusters)"])

with tab1:
    st.header("Συχνότητα & Κυριαρχία Χρωμάτων")
    
    col_bar, col_pie = st.columns(2)
    
    with col_bar:
        # Bar Chart Options
        bar_option = st.radio("Προβολή Bar Chart:", ["Top 10 Χρώματα (Συνολικά)", "Top 5 ανά Μνημείο"], horizontal=True)
        
        if bar_option == "Top 10 Χρώματα (Συνολικά)":
            top_colors = clusters_df.groupby(['Name', 'HEX'])['%'].mean().nlargest(10).reset_index()
            # Δημιουργία dictionary για να παίρνει το plot το ακριβές HEX χρώμα
            color_map = {row['Name']: row['HEX'] for i, row in top_colors.iterrows()}
            
            fig_bar = px.bar(top_colors, x='Name', y='%', color='Name', color_discrete_map=color_map,
                             title="Top 10 Συχνότερα Χρώματα", text_auto='.1f')
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        else:
            # Top 5 per monument
            top_per_mon = clusters_df.groupby(['Monument', 'Name', 'HEX'])['%'].mean().reset_index()
            top_per_mon = top_per_mon.sort_values(['Monument', '%'], ascending=[True, False]).groupby('Monument').head(5)
            color_map = {row['Name']: row['HEX'] for i, row in top_per_mon.iterrows()}
            
            fig_bar2 = px.bar(top_per_mon, x='Monument', y='%', color='Name', barmode='group',
                              color_discrete_map=color_map, title="Top 5 Χρώματα ανά Τοποθεσία")
            st.plotly_chart(fig_bar2, use_container_width=True)
            
    with col_pie:
        st.write("") # Spacer
        st.write("")
        pie_data = clusters_df.groupby(['Name', 'HEX'])['%'].sum().nlargest(8).reset_index()
        pie_color_map = {row['Name']: row['HEX'] for i, row in pie_data.iterrows()}
        
        fig_pie = px.pie(pie_data, values='%', names='Name', color='Name', color_discrete_map=pie_color_map,
                         title="Κυρίαρχα Χρώματα (Dominant Colors Share)", hole=0.4)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.header("Ένταση Χρωμάτων & Ιδιότητες Φωτογραφιών")
    
    col_heat, col_scatter = st.columns(2)
    
    with col_heat:
        st.subheader("Heatmap: RGB Intensity ανά Τοποθεσία")
        heatmap_data = summary_df.groupby('Monument')[['R mean', 'G mean', 'B mean']].mean().reset_index()
        heatmap_data = heatmap_data.set_index('Monument')
        
        fig_heat = px.imshow(heatmap_data, text_auto=".1f", aspect="auto", 
                             color_continuous_scale="Viridis",
                             title="Μέση Τιμή RGB Καναλιών ανά Τοποθεσία")
        st.plotly_chart(fig_heat, use_container_width=True)
        st.info("💡 **PR Insight:** Μνημεία με υψηλό 'B mean' (Blue) υποδηλώνουν κυριαρχία λίμνης/ουρανού, ιδανικά για 'ήρεμη' διαφήμιση.")
        
    with col_scatter:
        st.subheader("Scatter Plot: Φωτεινότητα vs Κορεσμός")
        fig_scatter = px.scatter(summary_df, x='S% mean', y='V% mean', color='Monument', 
                                 hover_data=['Filename'], size_max=10, opacity=0.7,
                                 title="Saturation vs Brightness ανά Εικόνα",
                                 labels={'S% mean': 'Κορεσμός (Saturation %)', 'V% mean': 'Φωτεινότητα (Brightness/Value %)'})
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    st.header("Χρωματικά Προφίλ (Color Space Clustering)")
    st.markdown("Εδώ βλέπουμε πώς ομαδοποιούνται τα χρώματα στον τρισδιάστατο χώρο CIELAB.")
    
    # 3D Scatter plot using L*, a*, b*
    sample_clusters = clusters_df.sample(min(2000, len(clusters_df))) if len(clusters_df) > 2000 else clusters_df
    cluster_color_map = {row['Name']: row['HEX'] for i, row in sample_clusters.iterrows()}
    
    fig_3d = px.scatter_3d(sample_clusters, x='L*', y='a*', z='b*',
                           color='Name', color_discrete_map=cluster_color_map,
                           opacity=0.7, hover_name='Filename', size='%',
                           title="3D Απεικόνιση Χρωματικών Κέντρων (L*a*b* Space)")
    
    fig_3d.update_traces(marker=dict(line=dict(width=0)))
    fig_3d.update_layout(scene=dict(bgcolor="whitesmoke"))
    
    st.plotly_chart(fig_3d, use_container_width=True, height=700)
    
    st.markdown("""
    ---
    ### 🌟 Bonus Marketing Insight
    Με βάση τα παραπάνω δεδομένα, η παλέτα της Καστοριάς διαμορφώνεται κυρίως από **φυσικούς, γήινους τόνους** και τα **χρώματα της λίμνης**.
    """)
