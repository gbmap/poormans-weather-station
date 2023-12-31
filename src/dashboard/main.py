from dash import Dash, html, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px


import src.server.database as db

app = Dash(__name__)
app.layout = html.Div([
    html.H1(children='Dashboard', style={'textAlign':'center'}),
    dcc.Interval(
        id='interval-component',
        interval=5*1000, # in milliseconds
        n_intervals=0
    ),
    html.H2(children='Number of Hours of Realtime Observations'),
    dcc.Slider(id='slider-number-observations', min=1, max=24, step=1, value=6),
    dcc.Graph(id='graph-humidity'),
    dcc.Graph(id='graph-temperature'),
    html.H2(children='Number of Hours of Hourly Observations'),
    dcc.Slider(id='slider-number-observations-hourly', min=12, max=240, step=3, value=72),
    dcc.Graph(id='graph-humidity-hourly'),
    dcc.Graph(id='graph-temperature-hourly'),
])
database = db.Database("database.db")

def line_graph(
        variable, 
        n=60*30, 
        observation_frequency: db.EObservationFrequency = db.EObservationFrequency.Realtime
):
    observations = database.get_last_n_observations(variable, n, observation_frequency)
    df = pd.DataFrame({
        "Date": [o.date for o in observations],
        "Value": [o.value for o in observations]
    })
    return px.line(df, x="Date", y="Value", title=f"{variable} [{observation_frequency.name}]")


@callback(
    Output('graph-humidity', 'figure'),
    [Input('interval-component', 'n_intervals'),
    Input('slider-number-observations', 'value')]
)
def update_graph_humidity(n, hours_obs):
    return line_graph("HUMIDITY", hours_obs*60*30, db.EObservationFrequency.Realtime)

@callback(
    Output('graph-temperature', 'figure'),
    [Input('interval-component', 'n_intervals'),
    Input('slider-number-observations', 'value')]
)
def update_graph_temperature(n, hours_obs):
    return line_graph("TEMPERATURE", hours_obs*60*30, db.EObservationFrequency.Realtime)

@callback(
    Output('graph-humidity-hourly', 'figure'),
    [Input('interval-component', 'n_intervals'),
    Input('slider-number-observations-hourly', 'value')]
)
def update_graph_humidity_hourly(n, n_hours):
    return line_graph("HUMIDITY", n_hours, db.EObservationFrequency.Hourly)

@callback(
    Output('graph-temperature-hourly', 'figure'),
    [Input('interval-component', 'n_intervals'),
    Input('slider-number-observations-hourly', 'value')]
)
def update_graph_humidity_hourly(n, n_hours):
    return line_graph("TEMPERATURE", n_hours, db.EObservationFrequency.Hourly)

if __name__ == '__main__':
    app.run(debug=True)