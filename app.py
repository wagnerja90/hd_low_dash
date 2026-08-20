"""
HD & LOW — US Comp Sales Forecast
Streamlit app built on top of HD_LOW_Quarterly_Data.xlsx (the project's
single source-of-truth quarterly workbook). See data_loader.py for how each
tab's data is pulled.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
 
from data_loader import (
    load_quarterly_data, load_overview, load_macro_correlation,
    load_naics_correlation, load_lira_series, load_lira_correlation,
)
 
st.set_page_config(page_title="HD & LOW Comp Sales Forecast", layout="wide")
 
# ---- palette (dataviz skill reference palette) ----
BLUE = "#2a78d6"     # HD
ORANGE = "#eb6834"   # LOW
AQUA = "#1baf7a"
YELLOW = "#eda100"
RED_NEG = "#b3382c"
GREEN_POS = "#1a9c56"
GRID = "#e9e7e1"
TEXT_SEC = "#52514e"
 
COMPANY_COLOR = {"HD": BLUE, "LOW": ORANGE}
HEAT_SCALE = [[0, RED_NEG], [0.5, "#ffffff"], [1, GREEN_POS]]
RANGE_BUTTONS = dict(
    buttons=[
        dict(count=1, label="1Y", step="year", stepmode="backward"),
        dict(count=3, label="3Y", step="year", stepmode="backward"),
        dict(count=5, label="5Y", step="year", stepmode="backward"),
        dict(step="all", label="All"),
    ]
)
 
 
def base_layout(**kwargs):
    layout = dict(
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        font=dict(family="Arial, sans-serif", size=12, color="#0b0b0b"),
        margin=dict(t=45, r=50, l=55, b=40),
        legend=dict(orientation="h", y=1.15, x=0),
        hovermode="x unified",
    )
    layout.update(kwargs)
    return layout
 
 
def dated_xaxis(default_years_back=3, df=None):
    """`default_years_back` is unused -- kept for call-site compatibility. Every chart's range slider
    now opens showing the FULL time series by default (i.e. as if 'All' were already selected);
    users can still narrow the view with the 1Y/3Y/5Y preset buttons or by dragging the slider."""
    ax = dict(type="date", rangeslider=dict(visible=True, thickness=0.06), rangeselector=RANGE_BUTTONS)
    if df is not None and len(df):
        start = df["Quarter Start"].min()
        end = df["Quarter Start"].max()
        ax["range"] = [start - pd.DateOffset(months=1), end + pd.DateOffset(months=1)]
    return ax
 
 
def window_bounds(df, default_years_back=3):
    """Full start/end date bounds of the series. The y-axis range is sized to fit ALL data (not just
    the x-axis's default zoomed-in window), so that dragging the range slider or clicking a wider
    preset (e.g. to see the 2020 pandemic spike) never clips a trend line that's out of the y-axis's
    fixed range. `default_years_back` is unused here (kept for call-site compatibility) -- it still
    controls the x-axis's initial zoom via dated_xaxis, just not the y-axis range anymore."""
    if df is None or not len(df):
        return None, None
    return df["Quarter Start"].min(), df["Quarter Start"].max()
 
 
def windowed_range(df, col, start, end, scale=1, pad_frac=0.12, stack_with=None):
    """Y-axis [min, max] padded range, computed ONLY from rows within [start, end] -- so the chart
    opens with the y-axis fit to the visible window, not the full history. `scale` multiplies values
    (e.g. 100 for a fraction-to-percent column). `stack_with` is an optional second column to SUM with
    `col` first (for stacked-bar y-ranges, e.g. existing + new home sales)."""
    if start is None or df is None or not len(df):
        return None
    mask = (df["Quarter Start"] >= start) & (df["Quarter Start"] <= end)
    sub = df.loc[mask]
    vals = (sub[col].fillna(0) + sub[stack_with].fillna(0)) if stack_with else sub[col]
    vals = (vals.dropna() * scale)
    if not len(vals):
        return None
    lo, hi = min(0, vals.min()), vals.max()
    span = hi - lo
    if span == 0:
        span = abs(hi) if hi != 0 else 1
    pad = span * pad_frac
    return [lo - pad, hi + pad]
 
 
quarterly = load_quarterly_data()
overview = load_overview()
macro_corr = load_macro_correlation()
naics_corr = load_naics_correlation()
lira_series = load_lira_series()
lira_corr = load_lira_correlation()
 
st.title("HD & LOW — US Comp Sales Forecast")
st.caption("US Comp Sales point estimates for 3Q FY2026 - 2Q FY2027 for HD and LOW.")
 
tab_trend, tab_industry, tab_macro, tab_explorer, tab_overview = st.tabs(
    ["Comp Sales Trends", "Industry Trends", "Macro Trends", "Data Explorer", "Methodology Notes"]
)
 
# =====================================================================
# TAB 1: Overview & Methodology (kept simple per user direction)
# =====================================================================
with tab_overview:
    st.subheader("Point Estimates — Q3 FY2026 through Q2 FY2027")
    st.caption(
        "Single-variable regression per quarter: mortgage rate near-term, consumer sentiment far-term "
        "(trained on FY2022-present to exclude the pandemic-distorted 2019-2021 period). "
        "Full methodology detail coming soon to this tab."
    )
 
    card_cols = st.columns(4)
    for i, row in overview[overview["Company"] == "HD"].reset_index(drop=True).iterrows():
        with card_cols[i]:
            st.metric(f"HD · {row['Fiscal Quarter']}", f"{row['Point Estimate']*100:.1f}%", help=row["Predictor Used"])
    card_cols2 = st.columns(4)
    for i, row in overview[overview["Company"] == "LOW"].reset_index(drop=True).iterrows():
        with card_cols2[i]:
            st.metric(f"LOW · {row['Fiscal Quarter']}", f"{row['Point Estimate']*100:.1f}%", help=row["Predictor Used"])
 
    col_a, col_b = st.columns([1.4, 1])
    with col_a:
        labels = (overview["Company"] + " " + overview["Fiscal Quarter"]).tolist()
        vals = (overview["Point Estimate"] * 100).tolist()
        colors = [BLUE if c == "HD" else ORANGE for c in overview["Company"]]
        fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors, text=[f"{v:.1f}%" for v in vals], textposition="outside"))
        fig.update_layout(**base_layout(height=340, yaxis=dict(title="Point Estimate %", gridcolor=GRID, ticksuffix="%"), showlegend=False))
        st.plotly_chart(fig, width='stretch')
    with col_b:
        st.markdown("**Key finding**")
        st.write(
            "All 8 estimates come out modestly negative — softer than both companies' FY2026 guidance "
            "(flat to +2.0% HD, flat LOW) and LIRA's projected direction (+0.5% to +2.1%, decelerating)."
        )
        st.markdown("**Guidance cross-check**")
        st.write("HD: flat to +2.0% total comp (reaffirmed 8/18/26).")
        st.write("LOW: flat total comp (narrowed 8/19/26).")
 
    with st.expander("Full point estimate detail"):
        show = overview.copy()
        show["Point Estimate"] = (show["Point Estimate"] * 100).round(2).astype(str) + "%"
        show["LIRA Cross-Check"] = (show["LIRA Cross-Check"] * 100).round(1).astype(str) + "%"
        st.dataframe(show, width='stretch', hide_index=True)
 
# =====================================================================
# TAB 2: Comp Sales Trend
# =====================================================================
with tab_trend:
    st.subheader("Point Estimates")
    card_cols = st.columns(4)
    for i, row in overview[overview["Company"] == "HD"].reset_index(drop=True).iterrows():
        with card_cols[i]:
            st.metric(f"HD · {row['Fiscal Quarter']}", f"{row['Point Estimate']*100:.1f}%", help=row["Predictor Used"])
    card_cols2 = st.columns(4)
    for i, row in overview[overview["Company"] == "LOW"].reset_index(drop=True).iterrows():
        with card_cols2[i]:
            st.metric(f"LOW · {row['Fiscal Quarter']}", f"{row['Point Estimate']*100:.1f}%", help=row["Predictor Used"])
 
    st.subheader("US Comp Sales for HD & LOW: Actuals and Projections")
    st.caption(
        "Solid line = reported comp sales.  \n"
        "Dashed line = estimated comp sales.  \n"
        "Use the range slider to adjust the time series shown."
    )
 
    fig = go.Figure()
    for company, color in COMPANY_COLOR.items():
        d = quarterly[quarterly["Company"] == company].sort_values("Quarter Start")
        actual = d[d["Period Type"] == "Actual"]
        proj = d[d["Period Type"] == "Projected"]
        bridge = pd.concat([actual.tail(1), proj]) if len(actual) else proj
 
        fig.add_trace(go.Scatter(
            x=actual["Quarter Start"], y=actual["Comp Sales % (US)"] * 100,
            name=f"{company} (reported)", mode="lines", line=dict(color=color, width=2.2),
            customdata=actual["Fiscal Quarter"],
            hovertemplate="%{customdata}: %{y:.1f}%<extra>" + company + " reported</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=bridge["Quarter Start"], y=bridge["Comp Sales % (US)"] * 100,
            name=f"{company} (projected)", mode="lines", line=dict(color=color, width=2.2, dash="dash"),
            customdata=bridge["Fiscal Quarter"],
            hovertemplate="%{customdata}: %{y:.1f}%<extra>" + company + " projected</extra>",
        ))
 
    _start, _end = window_bounds(quarterly, 3)
    fig.update_layout(**base_layout(
        height=520,
        yaxis=dict(title="US Comp Sales %", ticksuffix="%", gridcolor=GRID, zeroline=True, zerolinecolor="#ccc",
                    range=windowed_range(quarterly, "Comp Sales % (US)", _start, _end, scale=100)),
        xaxis=dated_xaxis(default_years_back=3, df=quarterly),
    ))
    st.plotly_chart(fig, width='stretch')
 
# =====================================================================
# TAB 3: Industry Trends
# =====================================================================
with tab_industry:
    st.subheader("Industry Trends")
    st.caption("HD (left) and LOW (right) comp sales against two industry-level series: public retail-sector sales (NAICS444) and Harvard JCHS's remodeling activity index (LIRA).")
 
    NAICS_CORR_COLS = ["Contemporaneous r", "Retail Leads 1Q r", "Retail Lags 1Q r"]
    NAICS_CORR_LABELS = ["Contemporaneous", "Retail Leads 1Q", "Retail Lags 1Q"]
 
    st.markdown(
        """
        <style>
        div[data-testid="stColumn"]:has(div.hd-low-divider-marker) {
            border-left: 2px solid #000;
            padding-left: 28px;
            margin-left: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    col_hd, col_low = st.columns(2)
    for col, company in ((col_hd, "HD"), (col_low, "LOW")):
        with col:
            if company == "LOW":
                st.markdown("<div class='hd-low-divider-marker'></div>", unsafe_allow_html=True)
            st.markdown(f"### {company}")
 
            st.markdown("**Correlation between US Comp Sales & NAICS444 Retail Sales**")
            nc = naics_corr[naics_corr["Company"] == company].set_index("Sample")[NAICS_CORR_COLS]
            fig_nc = go.Figure(go.Heatmap(
                z=nc.values, x=NAICS_CORR_LABELS, y=nc.index, colorscale=HEAT_SCALE, zmid=0, zmin=-1, zmax=1,
                colorbar=dict(title="r", thickness=12),
                text=[[f"{v:.2f}" for v in row] for row in nc.values], texttemplate="%{text}",
                textfont=dict(color="#000000"),
                hovertemplate="%{y} · %{x}: r=%{z:.3f}<extra></extra>",
            ))
            fig_nc.update_layout(**base_layout(height=220, margin=dict(t=10, r=10, l=170, b=40)))
            st.plotly_chart(fig_nc, width='stretch', key=f"naics_heat_{company}")
 
            d = quarterly[(quarterly["Company"] == company) & (quarterly["Period Type"] == "Actual")].sort_values("Quarter Start")
            d = d[d["NAICS444 Y/Y Growth"].notna() | (d["Fiscal Quarter"] == d["Fiscal Quarter"])]
 
            st.markdown("**Comp Sales vs. NAICS444 Retail Sales**")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=d["Quarter Start"], y=d["Comp Sales % (US)"] * 100, name="Comp Sales % (US)",
                                      mode="lines", line=dict(color=BLUE if company == "HD" else ORANGE, width=2),
                                      customdata=d["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}%<extra>Comp Sales</extra>"))
            fig.add_trace(go.Scatter(x=d["Quarter Start"], y=d["NAICS444 Y/Y Growth"] * 100, name="NAICS444 Y/Y Growth",
                                      mode="lines", line=dict(color=AQUA, width=2), yaxis="y2",
                                      customdata=d["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}%<extra>NAICS444</extra>"))
            _start, _end = window_bounds(d, 3)
            fig.update_layout(**base_layout(
                height=380,
                yaxis=dict(title="Comp Sales %", ticksuffix="%", gridcolor=GRID,
                           range=windowed_range(d, "Comp Sales % (US)", _start, _end, scale=100)),
                yaxis2=dict(title="NAICS444 Y/Y %", ticksuffix="%", overlaying="y", side="right", showgrid=False,
                            range=windowed_range(d, "NAICS444 Y/Y Growth", _start, _end, scale=100)),
                xaxis=dated_xaxis(default_years_back=3, df=d),
            ))
            st.plotly_chart(fig, width='stretch', key=f"naics_{company}")
 
            st.markdown("**Comp Sales vs. LIRA Remodeling Index**")
            l = lira_series.copy()
            company_dates = quarterly[quarterly["Company"] == company].drop_duplicates("Fiscal Quarter").set_index("Fiscal Quarter")["Quarter Start"]
            l["Quarter Start"] = l["Fiscal Quarter"].map(company_dates)
            comp_col = f"{company} Comp % (US)"
            actual_l = l[l["Period Type"] == "Historical"]
            proj_l = l[l["Period Type"] == "Projected"]
            bridge_l = pd.concat([actual_l.tail(1), proj_l])
 
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=actual_l["Quarter Start"], y=actual_l[comp_col] * 100, name="Comp Sales % (reported)",
                                       mode="lines", line=dict(color=BLUE if company == "HD" else ORANGE, width=2),
                                       customdata=actual_l["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}%<extra>Comp (reported)</extra>"))
            proj_est = overview[overview["Company"] == company].set_index("Fiscal Quarter")["Point Estimate"]
            bridge_vals = bridge_l["Fiscal Quarter"].map(lambda fq: proj_est.get(fq, bridge_l.set_index("Fiscal Quarter")[comp_col].get(fq)))
            fig2.add_trace(go.Scatter(x=bridge_l["Quarter Start"], y=bridge_vals * 100, name="Comp Sales % (projected)",
                                       mode="lines", line=dict(color=BLUE if company == "HD" else ORANGE, width=2, dash="dash"),
                                       customdata=bridge_l["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}%<extra>Comp (projected)</extra>"))
            actual_lira = l[l["Period Type"] == "Historical"]
            proj_lira = l[l["Period Type"] == "Projected"]
            bridge_lira = pd.concat([actual_lira.tail(1), proj_lira])
            fig2.add_trace(go.Scatter(x=actual_lira["Quarter Start"], y=actual_lira["LIRA Rate of Change"] * 100, name="LIRA Y/Y Growth % (reported)",
                                       mode="lines", line=dict(color=YELLOW, width=2), yaxis="y2",
                                       customdata=actual_lira["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}%<extra>LIRA (reported)</extra>"))
            fig2.add_trace(go.Scatter(x=bridge_lira["Quarter Start"], y=bridge_lira["LIRA Rate of Change"] * 100, name="LIRA Y/Y Growth % (projected)",
                                       mode="lines", line=dict(color=YELLOW, width=2, dash="dash"), yaxis="y2",
                                       customdata=bridge_lira["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}%<extra>LIRA (projected)</extra>"))
            _start, _end = window_bounds(l, 4)
            comp_all = pd.concat([actual_l[[ "Quarter Start", comp_col]], pd.DataFrame({"Quarter Start": bridge_l["Quarter Start"], comp_col: bridge_vals})])
            fig2.update_layout(**base_layout(
                height=380,
                yaxis=dict(title="Comp Sales %", ticksuffix="%", gridcolor=GRID,
                           range=windowed_range(comp_all, comp_col, _start, _end, scale=100)),
                yaxis2=dict(title="LIRA Y/Y Growth %", ticksuffix="%", overlaying="y", side="right", showgrid=False,
                            range=windowed_range(l, "LIRA Rate of Change", _start, _end, scale=100)),
                xaxis=dated_xaxis(default_years_back=4, df=l),
            ))
            st.plotly_chart(fig2, width='stretch', key=f"lira_{company}")
            st.caption("LIRA's 4 rightmost quarters are Harvard's own projections, shown alongside our estimate for the same period.")
 
# =====================================================================
# TAB 4: Macro Trends
# =====================================================================
with tab_macro:
    st.subheader("Macro Trends")
    st.caption("HD (left) and LOW (right). Correlation heatmap shows which macro predictor is strongest at which forecast horizon.")
 
    LEAD_COLS = ["Contemporaneous", "Leads 1Q", "Leads 2Q", "Leads 3Q", "Leads 4Q"]
    MACRO_SERIES_LABELS = {
        "Mortgage Rate (%)": "US 30Y Fixed Mortgage Rate (%)",
        "New Home Sales (M, SAAR)": "New Home Sales (M)",
        "Existing Home Sales (M, SAAR)": "Existing Home Sales (M)",
    }
 
    st.markdown(
        """
        <style>
        div[data-testid="stColumn"]:has(div.hd-low-divider-marker) {
            border-left: 2px solid #000;
            padding-left: 28px;
            margin-left: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    col_hd, col_low = st.columns(2)
    for col, company in ((col_hd, "HD"), (col_low, "LOW")):
        with col:
            if company == "LOW":
                st.markdown("<div class='hd-low-divider-marker'></div>", unsafe_allow_html=True)
            st.markdown(f"### {company}")
            st.markdown("**Correlation between US Comp Sales & Macro Analyses**")
            mc = macro_corr[macro_corr["Company"] == company].set_index("Macro Series")[LEAD_COLS]
            mc = mc.rename(index=MACRO_SERIES_LABELS)
            fig = go.Figure(go.Heatmap(
                z=mc.values, x=LEAD_COLS, y=mc.index, colorscale=HEAT_SCALE, zmid=0, zmin=-1, zmax=1,
                colorbar=dict(title="r", thickness=12),
                text=[[f"{v:.2f}" for v in row] for row in mc.values], texttemplate="%{text}",
                textfont=dict(color="#000000"),
                hovertemplate="%{y} · %{x}: r=%{z:.3f}<extra></extra>",
            ))
            fig.update_layout(**base_layout(height=280, margin=dict(t=10, r=10, l=140, b=40)))
            st.plotly_chart(fig, width='stretch', key=f"heat_{company}")
 
            d = quarterly[(quarterly["Company"] == company)].sort_values("Quarter Start")
            d_actual = d[d["Period Type"] == "Actual"]
 
            st.markdown("**Comp Sales vs. US 30Y Fixed Mortgage Rate**")
            fig1 = go.Figure()
            _comp_color = BLUE if company == "HD" else ORANGE
            _bridge1 = pd.concat([d_actual.tail(1), d[d["Period Type"] == "Projected"]])
            fig1.add_trace(go.Scatter(x=d_actual["Quarter Start"], y=d_actual["Comp Sales % (US)"] * 100, name="Comp Sales % (actual)",
                                       mode="lines", line=dict(color=_comp_color, width=2),
                                       customdata=d_actual["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}%<extra>Comp (actual)</extra>"))
            fig1.add_trace(go.Scatter(x=_bridge1["Quarter Start"], y=_bridge1["Comp Sales % (US)"] * 100, name="Comp Sales % (projected)",
                                       mode="lines", line=dict(color=_comp_color, width=2, dash="dash"),
                                       customdata=_bridge1["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}%<extra>Comp (projected)</extra>"))
            fig1.add_trace(go.Scatter(x=d_actual["Quarter Start"], y=d_actual["Mortgage Rate (%)"], name="US 30Y Fixed Mortgage Rate",
                                       mode="lines", line=dict(color=YELLOW, width=2), yaxis="y2",
                                       customdata=d_actual["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.2f}%<extra>Mortgage</extra>"))
            _start, _end = window_bounds(d, 3)
            fig1.update_layout(**base_layout(
                height=340, yaxis=dict(title="Comp Sales %", ticksuffix="%", gridcolor=GRID,
                                        range=windowed_range(d, "Comp Sales % (US)", _start, _end, scale=100)),
                yaxis2=dict(title="US 30Y Fixed Mortgage Rate %", ticksuffix="%", overlaying="y", side="right", showgrid=False,
                            range=windowed_range(d_actual, "Mortgage Rate (%)", _start, _end, scale=1)),
                xaxis=dated_xaxis(default_years_back=3, df=d),
            ))
            st.plotly_chart(fig1, width='stretch', key=f"mort_{company}")
 
            st.markdown("**US 30Y Fixed Mortgage Rate vs. Home Sales**")
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=d_actual["Quarter Start"], y=d_actual["Existing Home Sales (M, SAAR)"], name="Existing Home Sales", marker_color=AQUA))
            fig2.add_trace(go.Bar(x=d_actual["Quarter Start"], y=d_actual["New Home Sales (M, SAAR)"], name="New Home Sales", marker_color=YELLOW))
            fig2.add_trace(go.Scatter(x=d_actual["Quarter Start"], y=d_actual["Mortgage Rate (%)"], name="US 30Y Fixed Mortgage Rate",
                                       mode="lines", line=dict(color=RED_NEG, width=2), yaxis="y2",
                                       customdata=d_actual["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.2f}%<extra>Mortgage</extra>"))
            _start, _end = window_bounds(d_actual, 3)
            fig2.update_layout(**base_layout(
                height=340, barmode="stack",
                yaxis=dict(title="Home Sales (M)", gridcolor=GRID,
                           range=windowed_range(d_actual, "Existing Home Sales (M, SAAR)", _start, _end,
                                                 stack_with="New Home Sales (M, SAAR)")),
                yaxis2=dict(title="US 30Y Fixed Mortgage Rate %", ticksuffix="%", overlaying="y", side="right", showgrid=False,
                            range=windowed_range(d_actual, "Mortgage Rate (%)", _start, _end, scale=1)),
                xaxis=dated_xaxis(default_years_back=3, df=d_actual),
            ))
            st.plotly_chart(fig2, width='stretch', key=f"homesales_{company}")
 
            st.markdown("**CPI-U vs. Consumer Sentiment**")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=d_actual["Quarter Start"], y=d_actual["CPI-U Index (NSA)"], name="CPI-U Index",
                                       mode="lines", line=dict(color=BLUE if company == "HD" else ORANGE, width=2),
                                       customdata=d_actual["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}<extra>CPI-U</extra>"))
            fig3.add_trace(go.Scatter(x=d_actual["Quarter Start"], y=d_actual["Consumer Sentiment"], name="Consumer Sentiment",
                                       mode="lines", line=dict(color=YELLOW, width=2), yaxis="y2",
                                       customdata=d_actual["Fiscal Quarter"], hovertemplate="%{customdata}: %{y:.1f}<extra>Sentiment</extra>"))
            _start, _end = window_bounds(d_actual, 3)
            fig3.update_layout(**base_layout(
                height=340, yaxis=dict(title="CPI-U Index", gridcolor=GRID,
                                        range=windowed_range(d_actual, "CPI-U Index (NSA)", _start, _end, scale=1)),
                yaxis2=dict(title="Consumer Sentiment", overlaying="y", side="right", showgrid=False,
                            range=windowed_range(d_actual, "Consumer Sentiment", _start, _end, scale=1)),
                xaxis=dated_xaxis(default_years_back=3, df=d_actual),
            ))
            st.plotly_chart(fig3, width='stretch', key=f"cpi_{company}")
 
# =====================================================================
# TAB 5: Data Explorer
# =====================================================================
with tab_explorer:
    st.subheader("Data Explorer")
    st.caption("Browse the quarterly data powering the exhibits on this dashboard. Filter and download as needed.")
 
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        companies = st.multiselect("Company", ["HD", "LOW"], default=["HD", "LOW"])
    with f2:
        periods = st.multiselect("Period Type", ["Actual", "Projected"], default=["Actual", "Projected"])
    with f3:
        yr_min, yr_max = int(quarterly["Fiscal Year"].min()), int(quarterly["Fiscal Year"].max())
        yr_range = st.slider("Fiscal Year Range", yr_min, yr_max, (yr_min, yr_max))
 
    filtered = quarterly[
        quarterly["Company"].isin(companies)
        & quarterly["Period Type"].isin(periods)
        & quarterly["Fiscal Year"].between(*yr_range)
    ].drop(columns=["Fiscal Year"])
 
    st.dataframe(filtered, width='stretch', hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        file_name="hd_low_quarterly_data.csv",
        mime="text/csv",
    )
 


