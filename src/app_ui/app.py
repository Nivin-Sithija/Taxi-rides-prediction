import os
from pathlib import Path
import sys
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import yaml
from dash import Input, Output, dcc, html

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
os.chdir(project_root)

from app_ui.utils import load_data, create_figure, get_current_context

with open(project_root / "conf" / "base" / "parameters.yml") as f:
    config = yaml.safe_load(f)["ui"]

ACTUAL_DATA_PATH = project_root / config["actual_data_path"]
PREDICTIONS_PATH = project_root / config["predictions_path"]

# ── Design tokens ─────────────────────────────────────────────────────────────
BG     = "#F1F5F9"
CARD   = "#FFFFFF"
ACCENT = "#3B82F6"
GREEN  = "#10B981"
AMBER  = "#F59E0B"
DARK   = "#1E293B"
MID    = "#64748B"
MUTED  = "#94A3B8"
BORDER = "#E2E8F0"

# ── Shared style dicts ────────────────────────────────────────────────────────
card_s = {
    "backgroundColor": CARD, "borderRadius": "12px",
    "padding": "20px", "marginBottom": "16px",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.07)",
}
label_s = {
    "fontSize": "11px", "fontWeight": "600",
    "textTransform": "uppercase", "letterSpacing": "0.08em",
    "color": MUTED, "marginBottom": "2px",
}


def kpi_card(label: str, cid: str, val_color: str = DARK) -> html.Div:
    return html.Div([
        html.Div(label, style={**label_s, "color": MID}),
        html.Div(id=cid, style={
            "fontSize": "22px", "fontWeight": "700",
            "color": val_color, "marginTop": "3px",
        }),
    ], style={**card_s, "marginBottom": "12px", "padding": "14px 16px"})


def ctx_tile(label: str, cid: str) -> dbc.Col:
    return dbc.Col(
        html.Div([
            html.Div(label, style={**label_s, "color": MID}),
            html.Div(id=cid, style={
                "fontSize": "20px", "fontWeight": "700",
                "color": DARK, "marginTop": "3px",
            }),
        ], style={**card_s, "marginBottom": "0", "padding": "14px 16px"}),
        xs=6, md=3,
    )


# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Colombo Taxi Demand"

app.layout = dbc.Container([
    dcc.Interval(id="interval", interval=config["update_interval_ms"], n_intervals=0),

    # ── Header ────────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.H1("Colombo Taxi Demand Forecasting", style={
                "fontSize": "20px", "fontWeight": "700", "color": DARK, "margin": 0,
            }),
            html.Div("Real-time ride demand · Colombo, Sri Lanka", style={
                "fontSize": "12px", "color": MID, "marginTop": "2px",
            }),
        ], width="auto"),
        dbc.Col([
            html.Div([
                html.Span(style={
                    "display": "inline-block", "width": "8px", "height": "8px",
                    "borderRadius": "50%", "backgroundColor": GREEN, "marginRight": "6px",
                }),
                html.Span("Live", style={"fontSize": "13px", "fontWeight": "600", "color": DARK}),
                html.Span(" · updates every 2 s", style={"fontSize": "12px", "color": MID}),
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "flex-end"}),
            html.Div(id="last-updated", style={
                "fontSize": "11px", "color": MID, "textAlign": "right", "marginTop": "2px",
            }),
        ], width="auto", style={"marginLeft": "auto"}),
    ], align="center", style={
        "padding": "18px 0 16px", "marginBottom": "20px",
        "borderBottom": f"1px solid {BORDER}",
    }),

    # ── Body ──────────────────────────────────────────────────────────────────
    dbc.Row([

        # ── Sidebar ───────────────────────────────────────────────────────────
        dbc.Col([

            # Control panel
            html.Div([
                html.Div("Control Panel", style=label_s),
                html.Div("Lookback window", style={
                    "fontSize": "12px", "color": MID,
                    "marginTop": "10px", "marginBottom": "5px",
                }),
                dcc.Input(
                    id="lookback-hours", type="number", min=1, step=1,
                    value=config["default_lookback_hours"],
                    style={
                        "width": "100%", "backgroundColor": BG,
                        "border": f"1px solid {BORDER}", "borderRadius": "6px",
                        "color": DARK, "padding": "7px 10px",
                        "fontSize": "14px", "outline": "none",
                    },
                ),
                html.Div("hours shown in chart", style={
                    "fontSize": "11px", "color": MUTED, "marginTop": "4px",
                }),
            ], style=card_s),

            # KPI cards
            kpi_card("Next Hour Forecast", "kpi-pred",   "#1E8449"),
            kpi_card("Latest Actual",      "kpi-actual", "#EF4444"),
            kpi_card("Last Hour Error",    "kpi-error",  AMBER),

            # Dataset progress
            html.Div([
                html.Div("Dataset Progress", style=label_s),
                html.Div(id="progress-text", style={
                    "fontSize": "12px", "color": MID, "margin": "6px 0 8px",
                }),
                html.Div(
                    dbc.Progress(id="progress-bar", value=0, color="success",
                                 style={"height": "5px"}),
                    style={"borderRadius": "3px", "overflow": "hidden",
                           "backgroundColor": BORDER},
                ),
            ], style=card_s),

            # ML pipeline overview
            html.Div([
                html.Div("ML Pipeline Overview", style={**label_s, "marginBottom": "14px"}),
                *[
                    html.Div([
                        html.Span(f"{n}. ", style={
                            "fontWeight": "700", "color": ACCENT, "fontSize": "12px",
                        }),
                        html.Span(txt, style={
                            "fontSize": "12px", "color": MID, "lineHeight": "1.5",
                        }),
                    ], style={"marginBottom": "9px"})
                    for n, txt in enumerate([
                        "Feature engineering — lags, time & weather signals",
                        "CatBoost model trained on historical Colombo ride data",
                        "Inference runs every 2 s, simulating 1 h of real time",
                        "Dashboard streams predictions vs actuals live",
                        "All services containerised — train → infer → UI",
                    ], start=1)
                ],
            ], style={**card_s, "marginBottom": "0"}),

        ], width=3, style={"paddingRight": "8px"}),

        # ── Main area ─────────────────────────────────────────────────────────
        dbc.Col([

            # Chart card
            html.Div([
                html.Div([
                    html.Div("Predicted vs Actual Ride Demand", style={
                        "fontSize": "15px", "fontWeight": "600", "color": DARK,
                    }),
                    html.Div(
                        "Hourly ride counts across Colombo — dashed line marks the last observed actual",
                        style={"fontSize": "12px", "color": MID, "marginTop": "2px"},
                    ),
                ], style={"marginBottom": "12px"}),
                dcc.Graph(
                    id="graph",
                    config={"displayModeBar": False},
                    style={"borderRadius": "8px", "overflow": "hidden"},
                ),
            ], style=card_s),

            # Current-hour context
            html.Div([
                html.Div("Current Hour Conditions", style={
                    "fontSize": "13px", "fontWeight": "600",
                    "color": DARK, "marginBottom": "14px",
                }),
                dbc.Row([
                    ctx_tile("Season",        "ctx-season"),
                    ctx_tile("Hour",          "ctx-hour"),
                    ctx_tile("Holiday",       "ctx-holiday"),
                    ctx_tile("Weekday",       "ctx-weekday"),
                    ctx_tile("Weather",       "ctx-weather"),
                    ctx_tile("Temp (°C)",     "ctx-temp"),
                    ctx_tile("Humidity (%)",  "ctx-humidity"),
                    ctx_tile("Wind (km/h)",   "ctx-wind"),
                ], className="g-3"),
            ], style={**card_s, "marginBottom": "0"}),

        ], width=9, style={"paddingLeft": "20px"}),
    ], align="start"),

], fluid=True, style={
    "backgroundColor": BG, "minHeight": "100vh", "padding": "0 24px 28px",
})


# ── Callback ──────────────────────────────────────────────────────────────────
@app.callback(
    [
        Output("graph",         "figure"),
        Output("kpi-pred",      "children"),
        Output("kpi-actual",    "children"),
        Output("kpi-error",     "children"),
        Output("progress-bar",  "value"),
        Output("progress-text", "children"),
        Output("last-updated",  "children"),
        Output("ctx-season",    "children"),
        Output("ctx-hour",      "children"),
        Output("ctx-holiday",   "children"),
        Output("ctx-weekday",   "children"),
        Output("ctx-weather",   "children"),
        Output("ctx-temp",      "children"),
        Output("ctx-humidity",  "children"),
        Output("ctx-wind",      "children"),
    ],
    [
        Input("lookback-hours", "value"),
        Input("interval",       "n_intervals"),
    ],
)
def update_all(lookback_hours, _):
    df_actual = load_data(ACTUAL_DATA_PATH)
    df_pred   = load_data(PREDICTIONS_PATH)

    if not lookback_hours or lookback_hours < 1:
        lookback_hours = config["default_lookback_hours"]

    figure = create_figure(df_actual, df_pred, lookback_hours)

    # KPIs
    # All three KPIs anchor to the current inference time T:
    #   T   = df_pred["datetime"].max() - 1h  (the hour that just completed)
    #   T+1 = df_pred["datetime"].max()       (the hour being forecast)
    kpi_pred = kpi_actual = kpi_error = "—"

    if df_pred is not None and not df_pred.empty and df_actual is not None:
        t_next = df_pred["datetime"].max()          # T+1 (next hour)
        t_curr = t_next - pd.Timedelta(hours=1)    # T   (current completed hour)

        # Next hour forecast
        kpi_pred = f"{df_pred['prediction'].iloc[-1]:,.0f}"

        # Actual at T (from the inference dataset, not the full dataset end)
        actual_at_t = df_actual[df_actual["datetime"] == t_curr]
        if not actual_at_t.empty:
            a = actual_at_t["ride_count"].iloc[-1]
            kpi_actual = f"{a:,.0f}"

            # Prediction that was made for T (second-to-last prediction)
            pred_at_t = df_pred[df_pred["datetime"] == t_curr]
            if not pred_at_t.empty:
                kpi_error = f"{abs(pred_at_t['prediction'].iloc[-1] - a):,.0f}"

    # Progress
    progress_val  = 0
    progress_text = "No data"
    if df_pred is not None and df_actual is not None and len(df_actual) > 0:
        total         = len(df_actual)
        done          = min(len(df_pred), total)
        progress_val  = int(done / total * 100)
        progress_text = f"{done:,} of {total:,} hours  ({progress_val}%)"

    last_updated = f"Last updated {datetime.now().strftime('%H:%M:%S')}"
    ctx = get_current_context(df_actual, df_pred)

    return (
        figure,
        kpi_pred, kpi_actual, kpi_error,
        progress_val, progress_text, last_updated,
        ctx["season"], ctx["hour"], ctx["holiday"], ctx["weekday"],
        ctx["weather"], ctx["temp"], ctx["humidity"], ctx["wind"],
    )


server = app.server

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=8050)
