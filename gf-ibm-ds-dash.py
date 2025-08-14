# Import required libraries
import pandas as pd
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.express as px

# Read the airline data into pandas dataframe
spacex_df = pd.read_csv("spacex_launch_dash.csv")
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

launch_sites = sorted(spacex_df['Launch Site'].unique().tolist())
options = [{'label': 'All Sites', 'value': 'ALL'}] + [{'label': x, 'value': x} for x in launch_sites]

# Create a dash application
app = dash.Dash(__name__)

# Create an app layout
app.layout = html.Div(children=[html.H1('SpaceX Launch Records Dashboard',
                                        style={'textAlign': 'center', 'color': '#503D36',
                                               'font-size': 40}),
                                # TASK 1: Add a dropdown list to enable Launch Site selection
                                # The default select value is for ALL sites
                                dcc.Dropdown(id='site-dropdown', 
                                             options=options, 
                                             value='ALL',
                                             placeholder='Select a launch site',
                                             searchable=True),
                                html.Br(),

                                # TASK 2: Add a pie chart to show the total successful launches count for all sites
                                # If a specific launch site was selected, show the Success vs. Failed counts for the site
                                html.Div(dcc.Graph(id='success-pie-chart')),
                                html.Br(),

                                html.P("Payload range (Kg):"),
                                # TASK 3: Add a slider to select payload range

                                # GF NOTE Setting step to 1000 because that's what IBM instructions say.
                                #   Also, setting marks to 2500 increments because that's what example screenshot shows
                                #   but these settings don't really make sense together if this was a real dashboard.  
                                #   These marks don't align to the step size. A stepsize of something like 500 would make more sense.
                                #   Likewise the instructions suggestion to set initial value to min/max payload
                                #   Those don't align with the stepsize or the marks, so will only have those values when first
                                #   loaded, but user can't manually get back to those values without reloading page.
                                dcc.RangeSlider(id='payload-slider',
                                                min=0, max=10000, step=1000,
                                                marks={x: str(x) for x in range(0, 10001, 2500)},
                                                value=[min_payload, max_payload]),

                                # TASK 4: Add a scatter chart to show the correlation between payload and launch success
                                html.Div(dcc.Graph(id='success-payload-scatter-chart')),
                                ])

# TASK 2:
# Add a callback function for `site-dropdown` as input, `success-pie-chart` as output
# Function decorator to specify function input and output
@app.callback(Output(component_id='success-pie-chart', component_property='figure'),
              Input(component_id='site-dropdown', component_property='value'))
def get_pie_chart(entered_site):
    if entered_site == 'ALL':
        return px.pie(spacex_df, 
                      values='class', 
                      names='Launch Site', 
                      title='Total Success Launches By Site')
    else:
        # color map to ensure "Success" and "Failure" colors consistent as different launch sites selected
        # Redish color for failure, Blueish color for success.
        color_map = {'Failure': px.colors.qualitative.Plotly[1], 'Success': px.colors.qualitative.Plotly[0]}

        # explicitly setting order of success/failure so consistent as different launch sites selected
        category_orders={'class': ['Success', 'Failure']}

        # return the outcomes piechart for a selected site
        filtered_df = spacex_df[spacex_df['Launch Site'] == entered_site]['class'].value_counts().reset_index()
        filtered_df.columns = ['class', 'count']

        # maping 0/1 class values to Failure/Success for clarity for users that aren't familiar with boolean 0/1 class
        filtered_df['class'] = filtered_df['class'].map({0: 'Failure', 1: 'Success'})

        return px.pie(filtered_df, 
                      values='count', 
                      names='class', 
                      title=f'Total Success Launches for Site {entered_site}',
                      color='class',
                      color_discrete_map=color_map,
                      category_orders=category_orders)

# TASK 4:
# Add a callback function for `site-dropdown` and `payload-slider` as inputs, `success-payload-scatter-chart` as output
@app.callback(Output(component_id='success-payload-scatter-chart', component_property='figure'),
              [Input(component_id='site-dropdown', component_property='value'), Input(component_id='payload-slider', component_property='value')])
def get_scatter_chart(entered_site, entered_payload):
    # First filter by payload range (range used by both the "ALL" option and by selected sites)
    entered_payload_min = entered_payload[0]
    entered_payload_max = entered_payload[-1]
    payloads = spacex_df['Payload Mass (kg)']
    filtered_df = spacex_df[(payloads >= entered_payload_min) & (payloads <= entered_payload_max)]

    # If specific site selected, then also need to filter by selected launch site
    if entered_site != 'ALL':
        filtered_df = filtered_df[filtered_df['Launch Site'] == entered_site]

    # color map to ensure booster colors remain consistent as different launch sites and payload ranges selected
    # without this, the color of boosters in the scatter plot can change as the dashboard is interacted with
    color_map = {}
    boosters = spacex_df['Booster Version Category'].unique().tolist()
    for i, x in enumerate(boosters):
        color_map[x] = px.colors.qualitative.Plotly[i]

    # Set title based on whether showing data for all sites of for specific site.
    title_suffix = 'all Sites' if entered_site == 'ALL' else f'site {entered_site}'
    title = f'Correlation between Payload and Success for {title_suffix}'

    fig = px.scatter(filtered_df, 
                        x='Payload Mass (kg)', 
                        y='class', 
                        color='Booster Version Category',
                        size='Payload Mass (kg)',
                        title=title,
                        color_discrete_map=color_map, 
                        height=400)
    
    # Changing y axis label and tick text for clarity. Failure/Success more intuitive for most people to understand than 0/1
    fig.update_yaxes(title_text='Success or Failure', tickmode='array', tickvals=[0, 1], ticktext=['Failure', 'Success'])
    return fig 

# Run the app
if __name__ == '__main__':
    app.run()
