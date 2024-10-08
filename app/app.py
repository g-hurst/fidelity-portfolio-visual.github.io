from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import flask

import os
import sys

from scripts.process import make_dataframe, save_csv
from scripts.plotting import get_sankey_data

exports_path = 'data/portfolio_exports' 
df_portfolio = None 

def get_charts() -> list:
  pie_category_fig = px.pie(df_portfolio, names='Category', values='Current Value')
  pie_category_fig.update_layout(
    title=f'Investment Categories',
  )
  pie_sector_fig = px.pie(df_portfolio[df_portfolio['Category'] == 'Stock'], names='Sector', values='Current Value')
  pie_sector_fig.update_layout(
    title=f'Stock Sectors',
  )
  pie_account_fig = px.pie(df_portfolio, names='Account Name', values='Current Value')
  pie_account_fig.update_layout(
    title=f'Account Breakdown',
  )
  return list(
    [
      html.Div(
        className='body',
        children=[
          html.Div(
            className='chart-card',
            children=[
              dcc.Graph(
                figure={
                    'data':[
                      get_sankey_data(df_portfolio, excluded_accts=['Cash Management (Individual - TOD)',]),
                      ],
                    "layout": {
                      "title": "Sankey Breakdown of Portfolio",
                      "height":800,
                      "width":800
                      },
                  }
                )
            ],
          ),
          html.Div(
            className='chart-card',
            children=[
              html.Div(
                className='positions_bar-category-buttons',
                children=[
                  dcc.Dropdown(
                      id="positions_bar-category-filter",
                      options=[
                          {"label": opt, "value": opt}
                          for opt in ['All', ] + list(df_portfolio['Category'].unique())
                      ],
                      value="All",
                      clearable=False,
                      className="positions_bar-dropdown",
                  ),
                  dcc.Dropdown(
                      id="positions_bar-sort-filter",
                      options=[
                          {"label":'Alphabetical', "value":'alpha'},
                          {"label":'Numerical', "value":'num'}
                      ],
                      value="alpha",
                      clearable=False,
                      className="positions_bar-dropdown",
                  ),
                ]
              ),
              dcc.Graph(id='positions_bar'),
            ],
          )
        ],
      ),
      html.Div(
        className='body',
        children=[
          html.Div(className='pie-card', children=[dcc.Graph(figure=pie_account_fig ),],),
          html.Div(className='pie-card', children=[dcc.Graph(figure=pie_category_fig),],),
          html.Div(className='pie-card', children=[dcc.Graph(figure=pie_sector_fig  ),],),
        ],
      )
    ]
  )

server = flask.Flask(__name__)
app = Dash(__name__, server=server)
app.layout = html.Div(
  className='app',
  children=[
    html.H1(children='Fidelity Portfolio Visual'),
    html.Div(
      className='body',
      children=[
        html.Div(
          className='upload-data',
          children=[
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
            ),  
          ]
        ),
      ]
    ),
    html.Div(id='charts'),
  ]
)

@app.callback(Output('charts', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'))
def update_output(content, f_name):
  # make file name none if the save fails
  if (content is not None) and \
     (f_name is not None) and \
     (not save_csv(content, exports_path, f_name)):
    f_name = None

  global df_portfolio
  df_portfolio = make_dataframe(exports_path, f_name)
  if df_portfolio is not None:
    return get_charts()
  else:
    return None,

@app.callback(
  Output('positions_bar', 'figure'),
  [Input('positions_bar-category-filter', 'value'),
   Input('positions_bar-sort-filter', 'value'),]
)
def update_positions_bar(filter, sort_type):
  global df_portfolio
  if df_portfolio is not None:
    df = df_portfolio
    if filter != 'All':
      df = df[df['Category'] == filter]
    
    if sort_type == 'alpha':
        sort_value = 'category descending'
    elif sort_type == 'num':
        sort_value = 'total ascending'


    fig = px.bar(df, x='Current Value', y='Symbol')
    fig.update_layout()
    fig.update_layout(
      title=f'Postion breakdown: {filter}',
      yaxis={'categoryorder':sort_value},
      width=800,
      height=800
    )
    return fig


if __name__ == '__main__':
  # check to make sure that the app is run from the correct dir
  run_dir = 'app'
  if os.path.basename(os.getcwd()) != run_dir:
    print(f'Error: must run project from `{run_dir}` directory')
    sys.exit(-1)

  app.run_server(
    debug=True, 
    host='127.0.0.1', 
    port=8050
  )
