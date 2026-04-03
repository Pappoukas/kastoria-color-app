import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kastoria Visual Identity | Data Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DATA LOADING (Σχεσιακή Δομή με 4 αρχεία) ---
@st.cache_data
def load_data():
    # Φορτώνουμε και τα 4 αρχεία. Πλέον δεν χρειάζεται skiprows γιατί οι επικεφαλίδες είναι στην πρώτη γραμμή!
    info_df = pd.read_csv('data/color_summary_batch_Info.csv', sep=';', decimal=',')
    summary_raw = pd.read_csv('data/color_summary_batch_Summary.csv', sep=';', decimal=',')
    clusters_raw = pd.read_csv('data/color_summary_batch_Clusters.csv', sep=';', decimal=',')
    stats_df = pd.read_csv('data/color_summary_batch_Statistics.csv', sep=';', decimal=',')
    
    # Καθορισμός του ονόματος μνημείου από το Info.csv
    if 'placeInfo/name' in info_df.columns:
        info_df['Monument'] = info_df['placeInfo/name'].fillna('Unknown')
    else:
        info_df['Monument'] = 'Kastoria Place'
        
    # --- MERGING (ΕΝΩΣΗ ΔΕΔΟΜΕΝΩΝ) ---
    # Ενώνουμε τις πληροφορίες (Μνημείο, Filename) με τα Summary δεδομένα με βάση το '#'
    summary_df = pd.merge(info_df[['#', 'Filename', 'Monument']], summary_raw, on='#', how='inner')
    
    # Ενώνουμε τις πληροφορίες (Μνημείο, Filename) με τα Clusters δεδομένα με βάση το '#'
    clusters_df = pd.merge(info_df[['#', 'Filename', 'Monument']], clusters_raw, on='#', how='inner')
    
    # Προσαρμογή ονομάτων στηλών για το 3D Γράφημα (γιατί το νέο Excel τα βγάζει αλλιώς)
    rename_map = {'Lightness': 'L*', 'Green-Red': 'a*', 'Blue-Yellow': 'b*'}
    clusters_df.rename(columns=rename_map, inplace=True)
    
    return summary_df, clusters_df, stats_df

try:
    summary_df, clusters_df, stats_df = load_data()
except FileNotFoundError as e:
    st.error(f"⚠️ Σφάλμα: Δεν βρέθηκε κάποιο αρχείο. Βεβαιώσου ότι τα αρχεία υπάρχουν στο φάκελο 'data/'. Λεπτομέρειες: {e}")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Απρόσμενο σφάλμα κατά την ένωση των δεδομένων: {e}")
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
    st.header("Η Παλέτα της Καστοριάς")
    st.markdown("Τα κυρίαρχα χρώματα που συνθέτουν την οπτική ταυτότητα της επιλεγμένης τοποθεσίας.")
    
    # UI ΠΑΛΕΤΑΣ ΧΡΩΜΑΤΩΝ
    top_palette = clusters_df.groupby(['Name', 'HEX'])['%'].mean().nlargest(12).reset_index()
    
    cols_per_row = 6
    for i in range(0, len(top_palette), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(top_palette):
                row = top_palette.iloc[i + j]
                hex_color = row['HEX']
                color_name = str(row['Name']).title()
                percentage = f"{row['%']:.1f}"
                
                card_html = f"""
                <div style="border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid #eaeaea;">
                    <div style="background-color: {hex_color}; height: 90px; width: 100%;"></div>
                    <div style="padding: 12px; background-color: white;">
                        <div style="font-weight: 600; font-size: 14px; color: #2c3e50; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{color_name}">
                            {color_name}
                        </div>
                        <div style="font-size: 13px; color: #7f8c8d; font-family: monospace;">{hex_color}</div>
                        <div style="font-size: 11px; color: #95a5a6; margin-top: 8px; font-weight: 500;">ΚΑΛΥΨΗ: {percentage}%</div>
                    </div>
                </div>
                """
                col.markdown(card_html, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Στατιστική Ανάλυση Συχνότητας")
    
    col_bar, col_pie = st.columns(2)
    
    with col_bar:
        bar_option = st.radio("Προβολή Bar Chart:", ["Top 10 Χρώματα", "Top 5 ανά Μνημείο"], horizontal=True)
        if bar_option == "Top 10 Χρώματα":
            fig_bar = px.bar(top_palette.head(10), x='Name', y='%', color='Name', 
                             color_discrete_map={row['Name']: row['HEX'] for i, row in top_palette.iterrows()},
                             title="Απόλυτη Συχνότητα (Top 10)", text_auto='.1f')
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            top_per_mon = clusters_df.groupby(['Monument', 'Name', 'HEX'])['%'].mean().reset_index()
            top_per_mon = top_per_mon.sort_values(['Monument', '%'], ascending=[True, False]).groupby('Monument').head(5)
            color_map = {row['Name']: row['HEX'] for i, row in top_per_mon.iterrows()}
            fig_bar2 = px.bar(top_per_mon, x='Monument', y='%', color='Name', barmode='group',
                              color_discrete_map=color_map, title="Top 5 ανά Τοποθεσία")
            st.plotly_chart(fig_bar2, use_container_width=True)
            
    with col_pie:
        st.write("") 
        st.write("")
        pie_data = clusters_df.groupby(['Name', 'HEX'])['%'].sum().nlargest(8).reset_index()
        pie_color_map = {row['Name']: row['HEX'] for i, row in pie_data.iterrows()}
        fig_pie = px.pie(pie_data, values='%', names='Name', color='Name', color_discrete_map=pie_color_map,
                         title="Μερίδιο Κυρίαρχων Χρωμάτων (Top 8)", hole=0.45)
        fig_pie.update_traces(textposition='inside', textinfo='percent')
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.header("Ένταση Χρωμάτων & Ιδιότητες Φωτογραφιών")
    col_heat, col_scatter = st.columns(2)
    
    with col_heat:
        st.subheader("Heatmap: RGB Intensity ανά Τοποθεσία")
        heatmap_data = summary_df.groupby('Monument')[['R mean', 'G mean', 'B mean']].mean().reset_index().set_index('Monument')
        fig_heat = px.imshow(heatmap_data, text_auto=".1f", aspect="auto", color_continuous_scale="Viridis",
                             title="Μέση Τιμή RGB Καναλιών")
        st.plotly_chart(fig_heat, use_container_width=True)
        st.info("💡 **PR Insight:** Μνημεία με υψηλό 'B mean' (Blue) υποδηλώνουν κυριαρχία λίμνης/ουρανού.")
        
    with col_scatter:
        st.subheader("Scatter Plot: Φωτεινότητα vs Κορεσμός")
        fig_scatter = px.scatter(summary_df, x='S% mean', y='V% mean', color='Monument', 
                                 hover_data=['Filename'], size_max=10, opacity=0.7,
                                 title="Saturation vs Brightness",
                                 labels={'S% mean': 'Κορεσμός (Saturation %)', 'V% mean': 'Φωτεινότητα (Brightness/Value %)'})
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    st.header("Χρωματικά Προφίλ (Color Space Clustering)")
    st.markdown("Εδώ βλέπουμε πώς ομαδοποιούνται τα χρώματα στον τρισδιάστατο χώρο CIELAB.")
    
    sample_clusters = clusters_df.sample(min(2000, len(clusters_df))) if len(clusters_df) > 2000 else clusters_df
    cluster_color_map = {row['Name']: row['HEX'] for i, row in sample_clusters.iterrows()}
    
    fig_3d = px.scatter_3d(sample_clusters, x='L*', y='a*', z='b*',
                           color='Name', color_discrete_map=cluster_color_map,
                           opacity=0.7, hover_name='Filename', size='%',
                           title="3D Απεικόνιση Χρωματικών Κέντρων")
    
    fig_3d.update_traces(marker=dict(line=dict(width=0)))
    fig_3d.update_layout(scene=dict(bgcolor="whitesmoke"))
    st.plotly_chart(fig_3d, use_container_width=True, height=700)
