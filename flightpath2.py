import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Flight Profile Editor", layout="wide")

# --- INITIAL DATA ---
DEFAULT_POINTS = [
    {"time_min": 1.0, "altitude_kft": 0.0, "label": "ENGINES RUNNING"},
    {"time_min": 7.0, "altitude_kft": 0.0, "label": "180° TURN F/O & CAPT"},
    {"time_min": 12.0, "altitude_kft": 0.0, "label": "DELAYED WINGTIPS EXTENSION"},
    {"time_min": 15.0, "altitude_kft": 0.0, "label": "HUD TAKEOFF"},
    {"time_min": 23.0, "altitude_kft": 40.0, "label": "VSD DEMO"},
    {"time_min": 39.0, "altitude_kft": 40.0, "label": ""},
    {"time_min": 41.0, "altitude_kft": 26.0, "label": "ILS"},
    {"time_min": 45.0, "altitude_kft": 0.0, "label": ""},
    {"time_min": 54.0, "altitude_kft": 0.0, "label": "HUD TAKEOFF"},
    {"time_min": 55.0, "altitude_kft": 5.0, "label": "ENG FAIL R (SEVERE DAMAGE)"},
    {"time_min": 65.0, "altitude_kft": 36.0, "label": ""},
    {"time_min": 82.0, "altitude_kft": 36.0, "label": ""},
    {"time_min": 83.0, "altitude_kft": 33.0, "label": "RNAV Y (LPV MINIMA)"},
    {"time_min": 91.0, "altitude_kft": 0.0, "label": "OEI G/A & M/A"},
    {"time_min": 99.0, "altitude_kft": 5.0, "label": "[ ] FUEL IMBALANCE"},
    {"time_min": 104.0, "altitude_kft": 5.0, "label": "[ ] WINGTIPS DRIVE FAULT"},
    {"time_min": 106.0, "altitude_kft": 1.5, "label": "OEI MANUAL ILS"},
    {"time_min": 116.0, "altitude_kft": 0.0, "label": "AFTER LANDING"},
]

if "points_df" not in st.session_state:
    st.session_state.points_df = pd.DataFrame(DEFAULT_POINTS)

# --- SIDEBAR CONTROLS ---
st.sidebar.title("Flight Controls & Shading")

st.sidebar.subheader("Vertical Shaded Bands")
b1_l, b1_r = st.sidebar.slider("Band 1 Range (Mins)", 0.0, 120.0, (12.0, 26.0), step=0.5)
b2_l, b2_r = st.sidebar.slider("Band 2 Range (Mins)", 0.0, 120.0, (81.0, 93.0), step=0.5)

st.sidebar.subheader("Level-Off (FL) Annotations")
fl1_text = st.sidebar.text_input("FL Label 1 Text", "FL 360")
fl1_time = st.sidebar.number_input("FL Label 1 Time (Mins)", value=23.0, step=1.0)
fl1_alt = st.sidebar.number_input("FL Label 1 Alt (kft)", value=34.0, step=1.0)

fl2_text = st.sidebar.text_input("FL Label 2 Text", "FL 360")
fl2_time = st.sidebar.number_input("FL Label 2 Time (Mins)", value=65.0, step=1.0)
fl2_alt = st.sidebar.number_input("FL Label 2 Alt (kft)", value=34.0, step=1.0)

# --- MAIN GRAPH ---
st.title("Interactive Flight Profile Editor")

fig = go.Figure()

# Background Bands
fig.add_vrect(x0=b1_l, x1=b1_r, fillcolor="#b9e0f7", opacity=0.6, layer="below", line_width=0)
fig.add_vrect(x0=b2_l, x1=b2_r, fillcolor="#b9e0f7", opacity=0.6, layer="below", line_width=0)

# FL Annotations
if fl1_text:
    fig.add_annotation(x=fl1_time, y=fl1_alt, text=f"<b>{fl1_text}</b>",
                       showarrow=False, font=dict(color="red", size=13))
if fl2_text:
    fig.add_annotation(x=fl2_time, y=fl2_alt, text=f"<b>{fl2_text}</b>",
                       showarrow=False, font=dict(color="red", size=13))

# Profile Curve
df = st.session_state.points_df.sort_values(by="time_min").reset_index(drop=True)
fig.add_trace(go.Scatter(
    x=df["time_min"],
    y=df["altitude_kft"],
    mode="lines+markers",
    line=dict(color="#17557d", width=3),
    marker=dict(size=8, color="#17557d"),
    hoverinfo="text",
    hovertext=[f"Time: {r['time_min']:.1f}m<br>Alt: {r['altitude_kft']:.1f}k<br>{r['label']}" 
               for _, r in df.iterrows()]
))

# Waypoint Vertical Labels
for _, row in df.iterrows():
    if row["label"]:
        fig.add_annotation(
            x=row["time_min"],
            y=row["altitude_kft"],
            text=f"<b>{row['label']}</b>",
            textangle=-90,
            showarrow=False,
            yshift=40,
            font=dict(color="#005596", size=10)
        )

fig.update_layout(
    plot_bgcolor="#d7ecf8",
    paper_bgcolor="white",
    xaxis=dict(title="<b>TIME (Mins)</b>", range=[-2, 126], dtick=10, gridcolor="#ffffff"),
    yaxis=dict(title="<b>ALTITUDE (x1,000)</b>", range=[-2, 72], dtick=10, gridcolor="#ffffff"),
    margin=dict(l=40, r=40, t=20, b=40),
    height=540
)

st.plotly_chart(fig, use_container_width=True)

# --- EDITABLE TABLE INTERFACE ---
st.subheader("Edit Profile Data")
st.caption("Change values, add rows (using '+' icon), or delete rows. The graph updates live.")

edited_df = st.data_editor(
    st.session_state.points_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "time_min": st.column_config.NumberColumn("Time (Mins)", min_value=0.0, max_value=150.0, step=0.5),
        "altitude_kft": st.column_config.NumberColumn("Altitude (x1,000)", min_value=0.0, max_value=100.0, step=0.5),
        "label": st.column_config.TextColumn("Waypoint Label"),
    }
)
st.session_state.points_df = edited_df

# --- EXPORT & DOWNLOAD ---
export_payload = {
    "points": edited_df.to_dict(orient="records"),
    "bands": [{"left": b1_l, "right": b1_r}, {"left": b2_l, "right": b2_r}],
    "fl_labels": [
        {"text": fl1_text, "time_min": fl1_time, "altitude_kft": fl1_alt},
        {"text": fl2_text, "time_min": fl2_time, "altitude_kft": fl2_alt}
    ]
}

st.download_button(
    label="Download Flight Profile (JSON)",
    data=json.dumps(export_payload, indent=4),
    file_name="flight_profile.json",
    mime="application/json"
)
