import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    from datetime import datetime
    import time

    # State initialization
    get_roast_state, set_roast_state = mo.state({
        "is_running": False,
        "start_time": None,
        "current_time": 0.0, # Time in minutes
        "temperature_data": [], # List of dicts: {'time': float, 'temp': float, 'event': str}
        "batch_info": {
            "origin": "",
            "batch_size": "",
            "ambient_temp": "",
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    })

    get_input_trigger, set_input_trigger = mo.state(0)
    return alt, get_roast_state, mo, pd, set_roast_state, time


@app.cell
def _(get_roast_state, mo, update_batch_info):
    state = get_roast_state()
    batch_info = state["batch_info"]

    mo.md(f"""
    # ☕ Coffee Roast Profile Tracker

    Enter the details of your coffee batch below.
    """)

    origin_input = mo.ui.text(label="Coffee Origin:", value=batch_info["origin"], on_change=lambda v: update_batch_info("origin", v))
    size_input = mo.ui.text(label="Batch Size (g/lbs):", value=batch_info["batch_size"], on_change=lambda v: update_batch_info("batch_size", v))
    ambient_temp_input = mo.ui.text(label="Ambient Temp:", value=batch_info["ambient_temp"], on_change=lambda v: update_batch_info("ambient_temp", v))

    mo.hstack([origin_input, size_input, ambient_temp_input])
    return


@app.cell
def _(get_roast_state, set_roast_state, time):
    def update_batch_info(key, value):
        current_state = get_roast_state()
        new_batch_info = current_state["batch_info"].copy()
        new_batch_info[key] = value
        set_roast_state({**current_state, "batch_info": new_batch_info})

    def start_roast():
        current_state = get_roast_state()
        if not current_state["is_running"]:
            set_roast_state({
                **current_state, 
                "is_running": True, 
                "start_time": time.time(),
                "temperature_data": [],
                "current_time": 0.0
            })

    def stop_roast():
        current_state = get_roast_state()
        if current_state["is_running"]:
            set_roast_state({**current_state, "is_running": False})

    def log_temperature(temp, event=None):
        current_state = get_roast_state()
        if current_state["is_running"]:
            elapsed_time = (time.time() - current_state["start_time"]) / 60.0
            new_data = current_state["temperature_data"].copy()
            new_data.append({'time': elapsed_time, 'temp': float(temp), 'event': event})
            set_roast_state({**current_state, "temperature_data": new_data, "current_time": elapsed_time})


    return log_temperature, start_roast, stop_roast, update_batch_info


@app.cell
def _(get_roast_state, log_temperature, mo, start_roast, stop_roast):
    state_timer = get_roast_state()
    is_running = state_timer["is_running"]

    start_btn = mo.ui.button(label="▶️ Start Roast", on_click=lambda _: start_roast(), disabled=is_running)
    stop_btn = mo.ui.button(label="⏹️ Stop Roast", on_click=lambda _: stop_roast(), disabled=not is_running)

    # Event Buttons
    fc_start_btn = mo.ui.button(label="FC Start", on_click=lambda _: log_temperature(temp_input.value, "FC Start"), disabled=not is_running)
    fc_end_btn = mo.ui.button(label="FC End", on_click=lambda _: log_temperature(temp_input.value, "FC End"), disabled=not is_running)
    sc_start_btn = mo.ui.button(label="SC Start", on_click=lambda _: log_temperature(temp_input.value, "SC Start"), disabled=not is_running)
    sc_end_btn = mo.ui.button(label="SC End", on_click=lambda _: log_temperature(temp_input.value, "SC End"), disabled=not is_running)

    temp_input = mo.ui.number(label="Current Temp (°C/°F):", step=0.1)
    log_btn = mo.ui.button(label="Log Temp", on_click=lambda _: log_temperature(temp_input.value) if temp_input.value is not None else None, disabled=not is_running)

    mo.vstack([
        mo.hstack([start_btn, stop_btn]),
        mo.md("### Log Events"),
        mo.hstack([fc_start_btn, fc_end_btn, sc_start_btn, sc_end_btn]),
        mo.md("### Log Temperature"),
        mo.hstack([temp_input, log_btn])
    ])
    return


@app.cell
def _(events, mo):
    mo.ui.table(events)
    return


@app.cell
def _(alt, get_roast_state, pd):
    current_state_graph = get_roast_state()
    data = current_state_graph["temperature_data"]

    if not data:
        chart_view = "No data yet. Start the roast and log temperatures."
    else:
        df = pd.DataFrame(data)

        # Filter rows with actual temperature readings for RoR calculation
        df_temps = df.dropna(subset=['temp']).copy()

        # Calculate RoR (Rate of Rise) - typically degrees per minute
        df_temps['ror'] = 0.0
        if len(df_temps) > 1:
            df_temps['ror'] = df_temps['temp'].diff() / df_temps['time'].diff()
            # Smooth RoR slightly
            df_temps['ror'] = df_temps['ror'].rolling(window=2, min_periods=1).mean()

        # Merge back RoR
        df = pd.merge(df, df_temps[['time', 'ror']], on='time', how='left')

        # Base Chart
        base = alt.Chart(df).encode(x=alt.X('time:Q', title='Time (minutes)'))

        # Temperature Line
        temp_line = base.mark_line(color='blue', point=True).encode(
            y=alt.Y('temp:Q', title='Temperature', scale=alt.Scale(zero=False)),
            tooltip=['time', 'temp']
        ).transform_filter(alt.datum.temp != None)

        # RoR Line (secondary axis conceptually, plotted on same for simplicity or separate if preferred)
        # Altair handles dual axis but let's keep it clean or side-by-side. 
        # For a standard roast profile, they are often on same chart with dual axis.

        ror_line = base.mark_line(color='red').encode(
            y=alt.Y('ror:Q', title='Rate of Rise (Δ/min)', axis=alt.Axis(orient='right')),
            tooltip=['time', 'ror']
        ).transform_filter(alt.datum.ror != None)

        # Event Markers
        events = df.dropna(subset=['event'])
        if not events.empty:
            event_rules = alt.Chart(events).mark_rule(color='green', strokeDash=[5, 5]).encode(
                x='time:Q',
                size=alt.value(2)
            )
            event_labels = alt.Chart(events).mark_text(
                align='left', baseline='bottom', dy=-5, color='green', angle=270
            ).encode(
                x='time:Q',
                y=alt.value(10), # Arbitrary high position
                text='event:N'
            )

            # Combine charts
            combined_chart = alt.layer(
                temp_line, ror_line, event_rules, event_labels
            ).resolve_scale(
                y='independent'
            ).properties(
                width=700,
                height=400,
                title="Roast Profile"
            ).interactive()
        else:
            combined_chart = alt.layer(
                temp_line, ror_line
            ).resolve_scale(
                y='independent'
            ).properties(
                width=700,
                height=400,
                title="Roast Profile"
            ).interactive()

        chart_view = combined_chart

    chart_view
    return (events,)


@app.cell
def _(get_roast_state, mo):
    summary_state = get_roast_state()

    if not summary_state["is_running"] and len(summary_state["temperature_data"]) > 0:
        info = summary_state["batch_info"]
        summary_view = mo.md(f"""
        ### Roast Summary

        *   **Date/Time:** {info['date_time']}
        *   **Origin:** {info['origin']}
        *   **Batch Size:** {info['batch_size']}
        *   **Ambient Temp:** {info['ambient_temp']}
        *   **Total Duration:** {summary_state['current_time']:.2f} minutes
        """)
    else:
        summary_view = mo.md("")

    summary_view
    return


if __name__ == "__main__":
    app.run()
