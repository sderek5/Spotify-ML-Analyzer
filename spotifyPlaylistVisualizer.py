# Spotify Playlist Visualizer
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.spatial.distance import cdist
import numpy as np

# Load playlist data
playlist_df = pd.read_csv("playlist_audio_features.csv")

# Convert important columns to numeric, ignore errors
cols_to_numeric = [
    "acousticness", "danceability", "energy", "instrumentalness",
    "liveness", "loudness", "mode", "speechiness", "tempo", "valence", "popularity"
]

for col in cols_to_numeric:
    playlist_df[col] = pd.to_numeric(playlist_df[col], errors='coerce')

# Drop rows with missing key information
playlist_df = playlist_df.dropna(subset=cols_to_numeric)

# Quick Stats
print("=== Top 5 most popular songs ===")
print(playlist_df.sort_values("popularity", ascending=False)[["track_name", "artist_names", "popularity"]].head())

print("\n=== Average audio features in your playlist ===")
print(playlist_df[cols_to_numeric].mean())

# Audio Feature Distributions
# Setup a 2x2 grid for main features
fig_dist = make_subplots(
    rows=2, cols=2,
    subplot_titles=("Danceability", "Energy", "Valence", "Tempo")
)

# Add histograms for each feature
fig_dist.add_trace(px.histogram(playlist_df, x="danceability").data[0], row=1, col=1)
fig_dist.add_trace(px.histogram(playlist_df, x="energy").data[0], row=1, col=2)
fig_dist.add_trace(px.histogram(playlist_df, x="valence").data[0], row=2, col=1)
fig_dist.add_trace(px.histogram(playlist_df, x="tempo").data[0], row=2, col=2)

fig_dist.update_layout(title_text="Distribution of Key Audio Features", height=700, width=900)
fig_dist.show()

# Energy Vs Danceability
scatter_plot = px.scatter(
    playlist_df,
    x="danceability",
    y="energy",
    size="popularity",
    color="valence",
    hover_data=["track_name", "artist_names", "album_name"],
    title="Danceability vs Energy (Bubble size = Popularity, Color = Valence)"
)
scatter_plot.show()

# Top Artists
artist_count_df = playlist_df['artist_names'].value_counts().reset_index()
artist_count_df.columns = ["artist", "num_songs"]

top_artists_fig = px.bar(
    artist_count_df.head(10),
    x="artist",
    y="num_songs",
    text="num_songs",
    title="Top 10 Artists in Your Playlist",
    color="num_songs",
    color_continuous_scale="Viridis"
)
top_artists_fig.update_traces(textposition="outside")
top_artists_fig.show()

# Trends Over Time
playlist_df['release_year'] = pd.to_datetime(playlist_df['release_date'], errors='coerce').dt.year
playlist_df = playlist_df.dropna(subset=['release_year'])

features_over_time = ["danceability", "energy", "valence", "tempo"]
avg_features_year = playlist_df.groupby('release_year')[features_over_time].mean().reset_index()

line_trend_fig = px.line(
    avg_features_year,
    x="release_year",
    y=features_over_time,
    title="Average Audio Features Over Years"
)
line_trend_fig.show()

# Correlation Heatmap
corr_matrix = playlist_df[cols_to_numeric].corr()
heatmap_fig = px.imshow(
    corr_matrix,
    text_auto=True,
    color_continuous_scale="RdBu_r",
    title="Correlation Between Audio Features"
)
heatmap_fig.show()

# Song Similarity Example
# Use Euclidean distance to find songs that sound similar
feature_subset = playlist_df[["danceability", "energy", "valence", "tempo"]].values
distance_matrix = cdist(feature_subset, feature_subset, metric='euclidean')

# Ignore self-distance by adding a large number on the diagonal
most_similar_index = np.argmin(distance_matrix + np.eye(len(distance_matrix)) * 1e6, axis=1)
similar_songs_df = playlist_df.iloc[most_similar_index][['track_name', 'artist_names']].reset_index(drop=True)
similar_songs_df['original_track'] = playlist_df['track_name'].values

print("\n=== Example similar songs based on audio features ===")
print(similar_songs_df.head(10))