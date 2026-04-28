from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

_SEASON  = {1: "Dry", 2: "Pre-Monsoon", 3: "SW Monsoon", 4: "Post-Monsoon"}
_WEATHER = {1: "☀  Clear", 2: "⛅  Misty", 3: "🌧  Light Rain", 4: "⛈  Heavy Rain"}
_WEEKDAY = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}


def load_data(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


def get_current_context(
    df_actual: pd.DataFrame | None,
    df_pred: pd.DataFrame | None,
) -> dict:
    empty = {k: "—" for k in ("season", "hour", "holiday", "weekday",
                                "weather", "temp", "humidity", "wind")}
    if df_actual is None or df_actual.empty:
        return empty

    if df_pred is not None and not df_pred.empty:
        target = df_pred["datetime"].max() - pd.Timedelta(hours=1)
    else:
        target = df_actual["datetime"].max()

    mask = df_actual["datetime"] <= target
    if not mask.any():
        return empty

    r = df_actual[mask].iloc[-1]
    return {
        "season":   _SEASON.get(int(r["season"]), str(int(r["season"]))),
        "hour":     f"{int(r['hour']):02d}:00",
        "holiday":  "Yes" if int(r["holiday"]) == 1 else "No",
        "weekday":  _WEEKDAY.get(int(r["weekday"]), str(int(r["weekday"]))),
        "weather":  _WEATHER.get(int(r["weathersit"]), str(int(r["weathersit"]))),
        "temp":     f"{float(r['temp']):.1f}",
        "humidity": f"{float(r['humidity']):.0f}",
        "wind":     f"{float(r['windspeed']):.1f}",
    }


def create_figure(
    df_actual: pd.DataFrame | None,
    df_pred: pd.DataFrame | None,
    lookback_hours: int,
    datetime_col: str = "datetime",
) -> go.Figure:
    if df_pred is not None and not df_pred.empty:
        max_time     = df_pred[datetime_col].max()
        current_time = max_time - pd.Timedelta(hours=1)
    elif df_actual is not None and not df_actual.empty:
        current_time = df_actual[datetime_col].max()
        max_time     = current_time
    else:
        return go.Figure()

    min_time = max_time - pd.Timedelta(hours=lookback_hours)
    fig = go.Figure()

    if df_pred is not None:
        filt = df_pred[df_pred[datetime_col].between(min_time, max_time)]
        if not filt.empty:
            fig.add_trace(go.Scattergl(
                x=filt[datetime_col], y=filt["prediction"],
                name="Predicted", mode="lines+markers",
                line=dict(color="#1E8449", width=2.5),
                marker=dict(size=5, color="#1E8449"),
                hovertemplate="<b>Predicted</b>: %{y:,.0f}<extra></extra>",
            ))

    if df_actual is not None:
        filt = df_actual[df_actual[datetime_col].between(min_time, current_time)]
        if not filt.empty:
            fig.add_trace(go.Scattergl(
                x=filt[datetime_col], y=filt["ride_count"],
                name="Actual", mode="lines+markers",
                line=dict(color="#EF4444", width=2.5),
                marker=dict(symbol="x", size=6, color="#EF4444"),
                hovertemplate="<b>Actual</b>: %{y:,.0f}<extra></extra>",
            ))
            last_t = str(filt[datetime_col].iloc[-1])
            fig.add_vline(x=last_t, line_width=1.5, line_dash="dash",
                          line_color="#94A3B8")
            fig.add_annotation(
                x=last_t, y=1, yref="paper",
                text="Now", showarrow=False,
                xanchor="left", yanchor="top",
                font=dict(size=11, color="#64748B"),
                bgcolor="rgba(255,255,255,0.8)", borderpad=3,
            )

    fig.update_layout(
        template="plotly_white",
        height=400,
        hovermode="x unified",
        margin=dict(l=55, r=20, t=30, b=40),
        yaxis=dict(title="Rides / hour", gridcolor="#F1F5F9",
                   tickformat=",", zeroline=False),
        xaxis=dict(showgrid=False, showspikes=True, spikemode="across",
                   spikethickness=1, spikecolor="#CBD5E1", spikedash="dot"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        font=dict(family="system-ui,-apple-system,sans-serif", size=12,
                  color="#1E293B"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
    )
    return fig
