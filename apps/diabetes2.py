import marimo

__generated_with = "0.19.11"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # Diabetes Web Dashboard
    """)
    return


@app.cell
def _(f_csv, max_glucose_threshold, min_glucose_threshold, mo):
    mo.hstack([f_csv, mo.vstack([min_glucose_threshold, max_glucose_threshold])], align='center', gap=10)
    return


@app.cell
def _(f_csv, mo):
    mo.stop(not f_csv.value)

    single_day = mo.ui.checkbox(label='Single Day View', value=True)
    multi_day = mo.ui.checkbox(label='Multi Day View')
    hm_view = mo.ui.checkbox(label='Heat Map View')
    data_view = mo.ui.checkbox(label='Data Tables')

    mo.vstack([single_day, multi_day, hm_view, data_view])
    return data_view, hm_view, multi_day, single_day


@app.cell
def _(combined_chart, day_selector, mo, single_day):
    mo.vstack([day_selector, combined_chart]) if single_day.value else None
    return


@app.cell
def _(charts_by_day, combined_stdev_chart, date_range, mo, multi_day):
    mo.lazy(mo.vstack([date_range, combined_stdev_chart, mo.vstack(charts_by_day)]), show_loading_indicator=True) if multi_day.value else None
    return


@app.cell
def _(date_range, heatmap_charts, hm_view, mo):
    mo.vstack([date_range, heatmap_charts]) if hm_view.value else None
    return


@app.cell
def _(data_view, df_glucose, df_treatment, mo):
    mo.vstack([mo.ui.dataframe(df_glucose), mo.ui.dataframe(df_treatment)]) if data_view.value else None
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import polars as pl
    import io
    import altair as alt

    return alt, io, pl


@app.cell
def _(f_csv, io, mo, pl):
    mo.stop(not f_csv.value)

    csv_content = f_csv.value[0].contents.decode(encoding='utf-8')
    lines = csv_content.splitlines()

    tables_data = []
    current_table_lines = []

    for line in lines:
        # A "blank row" is considered an empty string or a string containing only whitespace.
        if not line.strip():
            if current_table_lines:
                table_csv_string = "\n".join(current_table_lines)
                try:
                    # Read the current block of lines as a CSV.
                    # infer_schema_length helps Polars detect column types.
                    df = pl.read_csv(io.StringIO(table_csv_string), infer_schema_length=50)
                    if not df.is_empty():
                        tables_data.append(df)
                except Exception:
                    # Silently skip blocks that cannot be parsed into valid DataFrames.
                    pass
                current_table_lines = []
        else:
            current_table_lines.append(line)

    # Add the last table if the file does not end with a blank line
    if current_table_lines:
        table_csv_string = "\n".join(current_table_lines)
        try:
            df = pl.read_csv(io.StringIO(table_csv_string), infer_schema_length=50)
            if not df.is_empty():
                tables_data.append(df)
        except Exception:
            pass

    # The 'tables_data' variable now contains a list of Polars DataFrames,
    # each representing a table extracted from the CSV file.
    # tables_data
    return (tables_data,)


@app.cell
def _(tables_data):
    df_treatment = tables_data[3]

    # df_treatment
    return (df_treatment,)


@app.cell
def _(max_glucose_threshold, min_glucose_threshold, pl, tables_data):
    df_glucose = tables_data[1].select(
        pl.col('EventDateTime').str.strptime(pl.Datetime),
        pl.col('Readings (mg/dL)')
        ).with_columns(
        HourOfDay = pl.col('EventDateTime').dt.hour(),
        DayOfWeek = pl.col('EventDateTime').dt.strftime('%A'),
        BelowRange = pl.col('Readings (mg/dL)') < min_glucose_threshold.value,
        InRange = (pl.col('Readings (mg/dL)') >= min_glucose_threshold.value) &
                   (pl.col('Readings (mg/dL)') <= max_glucose_threshold.value),
        AboveRange = pl.col('Readings (mg/dL)') > max_glucose_threshold.value
        )

    # df_glucose
    return (df_glucose,)


@app.cell
def _(df_glucose_filtered, pl):
    df_percent = df_glucose_filtered.group_by(pl.col('DayOfWeek'), pl.col('HourOfDay'), maintain_order=True).agg(
        PercentLow = pl.col("BelowRange").sum() / pl.col("BelowRange").count() * 100,
        PercentInRange = pl.col("InRange").sum() / pl.col("InRange").count() * 100,
        PercentHigh = pl.col("AboveRange").sum() / pl.col("AboveRange").count() * 100
    )

    # Define the order of days for the heatmap
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return day_order, df_percent


@app.cell(hide_code=True)
def _():
    # mo.stop(not f_csv.value)

    # mo.md(f"""
    # ### Tables Extracted from `{f_csv.value[0].name}`

    # A total of **{len(tables_data)}** tables were extracted from the uploaded CSV file, using blank rows as delimiters between tables.

    # These tables are now available as a list of Polars DataFrames, stored in the variable `tables_data`. You can access individual tables by their index, for example:
    # -   `tables_data[0]` refers to the first table.
    # -   `tables_data[1]` refers to the second table.
    # -   And so on.

    # Each item in the `tables_data` list is a Polars DataFrame that you can further analyze or visualize.
    # """)
    return


@app.cell
def _(df_glucose, mo):
    # Get min and max dates from df_glucose to set the range for the date picker
    min_date = df_glucose["EventDateTime"].dt.date().min()
    max_date = df_glucose["EventDateTime"].dt.date().max()

    day_selector = mo.ui.date(
        value=min_date, # Default to the earliest date
        start=min_date,
        stop=max_date,
        label="Select a Day"
    )

    # day_selector
    return (day_selector,)


@app.cell
def _(mo):
    min_glucose_threshold = mo.ui.slider(
        value=80,
        start=50,
        stop=250,
        step=1,
        show_value=True,
        label="Minimum Glucose Threshold (mg/dL)"
    )

    max_glucose_threshold = mo.ui.slider(
        value=180,
        start=50,
        stop=250,
        step=1,
        show_value=True,
        label="Maximum Glucose Threshold (mg/dL)"
    )

    # min_glucose_threshold, max_glucose_threshold
    return max_glucose_threshold, min_glucose_threshold


@app.cell
def _(mo):
    f_csv = mo.ui.file(filetypes=['.csv'], kind='area', label='Upload Tandem Source csv file')

    # f_csv
    return (f_csv,)


@app.cell
def _(mo, pl, tables_data):
    date_range = mo.ui.date_range.from_series(
        tables_data[1]['EventDateTime'].str.strptime(pl.Datetime),
        label='Date Range'
        )

    # date_range
    return (date_range,)


@app.cell
def _(alt, df_glucose_filtered):
    # Base chart for common encoding
    base = alt.Chart(df_glucose_filtered).encode(
        x=alt.X('HourOfDay:O', title='Hour of Day (24-hour)', axis=alt.Axis(tickCount=24)),
        tooltip=[
            alt.Tooltip('HourOfDay:O', title='Hour'),
            alt.Tooltip('mean(Readings (mg/dL)):Q', title='Average BG', format='.1f'),
            alt.Tooltip('stdev(Readings (mg/dL)):Q', title='Standard Deviation', format='.2f'),
            alt.Tooltip('count(Readings (mg/dL)):Q', title='Number of Readings')
        ]
    ).properties(
        title='Average Glucose Values and Quartile Bands by Hour of Day'
    )

    # Layer for the mean line
    mean_line_stdev = base.mark_line(point=True, color='darkgreen').encode(
        y=alt.Y('mean(Readings (mg/dL)):Q', title='Glucose Value (mg/dL)')
    )

    # Layer for the standard deviation band
    iqr_band = base.mark_errorband(extent='iqr', opacity=0.5, color='lightgreen').encode(
        y=alt.Y('Readings (mg/dL):Q') # Altair will automatically compute the standard deviation for 'sgv' based on 'extent'
    )

    # Combine the layers
    combined_stdev_chart = (iqr_band + mean_line_stdev).interactive()

    # combined_stdev_chart
    return (combined_stdev_chart,)


@app.cell
def _(date_range, df_glucose, pl):
    # Filter df_glucose based on the selected date_range
    df_glucose_filtered = df_glucose.filter(
        (pl.col("EventDateTime").dt.date() >= date_range.value[0]) &
        (pl.col("EventDateTime").dt.date() <= date_range.value[1])
    )

    # Get unique dates in the filtered data
    unique_dates = df_glucose_filtered.select(pl.col('EventDateTime').dt.date().unique()).sort('EventDateTime').to_series().to_list()
    return df_glucose_filtered, unique_dates


@app.cell
def _(alt, df_glucose_filtered, pl, unique_dates):
    charts_by_day = []
    # Iterate through unique dates, creating a chart for every 7 days
    for i in range(0, len(unique_dates), 7):
        current_seven_days = unique_dates[i:i+7]
        df_seven_days = df_glucose_filtered.filter(
            pl.col('EventDateTime').dt.date().is_in(current_seven_days)
        )

        chart = alt.Chart(df_seven_days).mark_line(point=True).encode(
            x=alt.X('hoursminutes(EventDateTime):T', title='Time of Day'),
            y=alt.Y('Readings (mg/dL):Q', title='Glucose Readings (mg/dL)'),
            color=alt.Color('monthdate(EventDateTime):N', title='Day', legend=alt.Legend(title='Date')),
            tooltip=[
                alt.Tooltip('monthdate(EventDateTime):N', title='Date'),
                alt.Tooltip('hoursminutes(EventDateTime):T', title='Time'),
                alt.Tooltip('Readings (mg/dL):Q', title='Reading')
            ]
        ).properties(
            title=f"Glucose Readings by Time of Day ({current_seven_days[0].strftime('%Y-%m-%d')} to {current_seven_days[-1].strftime('%Y-%m-%d')})"
        ).interactive()

        charts_by_day.append(chart)

    # charts_by_day
    return (charts_by_day,)


@app.cell
def _(alt, day_selector, df_glucose, df_treatment, pl):
    # Filter df_glucose for the selected day
    df_glucose_single_day = df_glucose.filter(
        pl.col("EventDateTime").dt.date() == day_selector.value
    )

    # Filter df_treatment for the selected day
    # Assuming 'CompletionDateTime' is the relevant column for treatment events
    df_treatment_single_day = df_treatment.filter(
        pl.col("CompletionDateTime").str.to_date('%Y-%m-%dT%H:%M:%S').dt.date() == day_selector.value
    )

    # Process Bolus data from df_treatment
    df_bolus = df_treatment_single_day.filter(pl.col("Type") == "Bolus").select(
        pl.col('CompletionDateTime').str.strptime(pl.Datetime, '%Y-%m-%dT%H:%M:%S').alias('EventDateTime'),
        pl.col('InsulinDelivered').alias('Bolus')
    )

    # Create the glucose readings chart
    # Use a common x-axis definition
    x_axis = alt.X('hoursminutes(EventDateTime):T', title='Time of Day', axis=alt.Axis(format="%H:%M"))

    # Glucose line chart
    glucose_line = alt.Chart(df_glucose_single_day).mark_line(point=True, color='blue').encode(
        x=x_axis,
        y=alt.Y('Readings (mg/dL):Q', title='Glucose (mg/dL)', scale=alt.Scale(domain=[0, 300])),
        tooltip=[
            alt.Tooltip('EventDateTime:T', title='Timestamp', format='%Y-%m-%d %H:%M:%S'),
            alt.Tooltip('Readings (mg/dL):Q', title='Glucose')
        ]
    )

    # Bolus bar chart (using a secondary y-axis for units)
    bolus_bars = alt.Chart(df_bolus).mark_bar(color='green', opacity=0.7, size=5).encode(
        x=x_axis,
        y=alt.Y('Bolus:Q', title='Bolus (Units)', scale=alt.Scale(domain=[0, 15])), # Assuming max 15 units bolus
        tooltip=[
            alt.Tooltip('EventDateTime:T', title='Timestamp', format='%Y-%m-%d %H:%M:%S'),
            alt.Tooltip('Bolus:Q', title='Bolus')
        ]
    )

    # Combine the charts
    # Layering: Glucose line as the base, then bolus bars, then food markers.
    # Use 'resolve_scale(y='independent')' if you want separate y-axes for glucose and bolus.
    # Here, we'll layer them and let Altair try to align them. If scales are too different,
    # consider using two separate charts stacked or side-by-side.

    combined_chart = alt.layer(
            glucose_line,
            bolus_bars
        ).resolve_scale(
            y='independent'
        ).properties(
            title=f"Glucose, Bolus, and Food Data for {day_selector.value.strftime('%Y-%m-%d')}"
        ).interactive()

    # [day_selector, combined_chart]
    return (combined_chart,)


@app.cell
def _(
    alt,
    day_order,
    df_percent,
    max_glucose_threshold,
    min_glucose_threshold,
):
    heatmap_charts = []

    for col in [['PercentLow', 'reds'], ['PercentInRange', 'greens'], ['PercentHigh', 'blues']]:
        heatmap_charts.append(
            alt.Chart(df_percent).mark_rect().encode(
                alt.X('HourOfDay:O', title='Hour of Day (24-hour)', axis=alt.Axis(tickCount=24)),
                alt.Y('DayOfWeek:O', title='Day of Week', sort=day_order),
                color=alt.Color(f'{col[0]}:Q',
                                title=f'{col[0]} (%)',
                                scale=alt.Scale(scheme=f'{col[1]}')), # Use a heatmap color scheme
                tooltip=[
                    alt.Tooltip('DayOfWeek:O', title='Day'),
                    alt.Tooltip('HourOfDay:O', title='Hour'),
                    alt.Tooltip(f'{col[0]}:Q', title=f'{col[0]}', format='.1f')
                ]
            ).properties(
                title=f'{col[0]} Heatmap (Target: {min_glucose_threshold.value}-{max_glucose_threshold.value} mg/dL)'
            ).interactive()
        )

    # heatmap_charts
    return (heatmap_charts,)


if __name__ == "__main__":
    app.run()
