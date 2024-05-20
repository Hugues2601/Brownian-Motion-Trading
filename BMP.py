#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
import dash_table
import plotly.graph_objs as go
import numpy as np
from datetime import datetime
import random
import string

S0 = 100 
r = 0.05 
sigma = 0.5 
dt = 1/252 
initial_balance = 100_000 

initial_data = {
    'open': [S0],
    'high': [S0],
    'low': [S0],
    'close': [S0],
    'transactions': [],
    'news': [],
    'positions': [],
    'portfolio': {
        'balance': initial_balance,
        'shares': 0,
        'value': initial_balance
    }
}


# In[2]:


app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

index_page = html.Div(
    [
        html.H1("Brownian Motion Simulation", style={'textAlign': 'center', 'color': '#4CAF50'}),
        html.Button('Start', id='start-button', style={'display': 'block', 'margin': 'auto', 'background-color': '#4CAF50', 'color': 'white', 'padding': '10px 20px', 'fontSize': '20px'}),
    ],
    style={'textAlign': 'center', 'padding': '50px'}
)


simulation_page = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id='live-graph', animate=True),
                        dcc.Interval(
                            id='graph-update',
                            interval=2*1000, 
                            n_intervals=0
                        )
                    ],
                    style={'width': '66%', 'display': 'inline-block', 'verticalAlign': 'top'}
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dash_table.DataTable(
                                    id='positions-table',
                                    columns=[
                                        {'name': 'Type', 'id': 'type'},
                                        {'name': 'Shares', 'id': 'shares'},
                                        {'name': 'Open Price', 'id': 'open_price'},
                                        {'name': 'Current Price', 'id': 'current_price'},
                                        {'name': 'Profit/Loss', 'id': 'profit_loss'}
                                    ],
                                    data=[],
                                    row_deletable=True,
                                    style_table={'margin-top': '20px'},
                                    style_header={
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold'
                                    },
                                    style_cell={'textAlign': 'center', 'padding': '10px'},
                                    style_data_conditional=[
                                        {
                                            'if': {
                                                'filter_query': '{profit_loss} > 0',
                                                'column_id': 'profit_loss'
                                            },
                                            'color': 'green',
                                            'fontWeight': 'bold'
                                        },
                                        {
                                            'if': {
                                                'filter_query': '{profit_loss} < 0',
                                                'column_id': 'profit_loss'
                                            },
                                            'color': 'red',
                                            'fontWeight': 'bold'
                                        }
                                    ],
                                ),
                                html.Div(id='close-buttons-container', style={'textAlign': 'center'}),
                            ],
                            style={'marginBottom': '30px'}
                        ),
                        dash_table.DataTable(
                            id='news-table',
                            columns=[
                                {'name': 'Timestamp', 'id': 'timestamp'},
                                {'name': 'Type', 'id': 'type'},
                                {'name': 'Impact', 'id': 'impact'}
                            ],
                            data=[],
                            style_table={'margin-top': '20px'},
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            },
                            style_cell={'textAlign': 'center', 'padding': '10px'},
                            style_data_conditional=[
                                {
                                    'if': {
                                        'filter_query': '{impact} = "positive"'
                                    },
                                    'backgroundColor': 'lightgreen',
                                    'color': 'black'
                                },
                                {
                                    'if': {
                                        'filter_query': '{impact} = "negative"'
                                    },
                                    'backgroundColor': 'lightcoral',
                                    'color': 'black'
                                }
                            ],
                            sort_action='native'
                        )
                    ],
                    style={'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top'}
                ),
            ],
            style={'display': 'flex', 'width': '100%'}
        ),
        html.Div(
            [
                html.Div(id='portfolio-value', style={'fontWeight': 'bold', 'margin-top': '20px', 'fontSize': '20px', 'textAlign': 'center'}),
                html.Div(
                    [
                        dcc.Input(id='shares-input', type='number', value=100, min=1, step=1, style={'margin-right': '10px', 'padding': '5px', 'width': '100px'}),
                        html.Button('Long', id='long-button', n_clicks=0, style={'margin-right': '10px', 'background-color': '#4CAF50', 'color': 'white'}),
                        html.Button('Short', id='short-button', n_clicks=0, style={'background-color': '#f44336', 'color': 'white'})
                    ],
                    style={'padding': '10px', 'textAlign': 'center'}
                ),
                dash_table.DataTable(
                    id='transaction-table',
                    columns=[
                        {'name': 'Transaction ID', 'id': 'transaction_id'},
                        {'name': 'Timestamp', 'id': 'timestamp'},
                        {'name': 'Price of the transaction', 'id': 'price'},
                        {'name': 'Volume', 'id': 'volume'},
                        {'name': 'Type', 'id': 'transaction_type'},
                        {'name': 'Market', 'id': 'market_type'},
                        {'name': 'Order', 'id': 'order_type'}
                    ],
                    data=[],
                    style_table={'margin-top': '20px'},
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_cell={'textAlign': 'center', 'padding': '10px'},
                    style_data_conditional=[
                        {
                            'if': {
                                'filter_query': '{transaction_type} = "Buy"'
                            },
                            'backgroundColor': 'green',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'filter_query': '{transaction_type} = "Sell"'
                            },
                            'backgroundColor': 'red',
                            'color': 'white'
                        }
                    ],
                    sort_action='native'
                )
            ],
            style={'width': '100%', 'textAlign': 'center', 'padding': '20px'}
        ),
        html.Div(
            [
                html.Button('Pause', id='pause-button', n_clicks=0, style={'margin-right': '10px', 'background-color': '#f44336', 'color': 'white'}),
                html.Button('Resume', id='resume-button', n_clicks=0, style={'background-color': '#4CAF50', 'color': 'white'})
            ],
            style={'padding': '10px', 'textAlign': 'center'}
        ),
        dcc.Store(id='ohlc-data', data=initial_data),
        dcc.Store(id='long-clicks', data=0),
        dcc.Store(id='short-clicks', data=0),
    ],
    style={
        'fontFamily': 'Arial, sans-serif',
        'backgroundColor': '#f4f4f9',
        'padding': '20px'
    }
)

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/simulation':
        return simulation_page
    else:
        return index_page

@app.callback(Output('url', 'pathname'),
              [Input('start-button', 'n_clicks')])
def start_simulation(n_clicks):
    if n_clicks:
        return '/simulation'
    return '/'


# In[3]:


# Cellule 3
@app.callback(
    Output('graph-update', 'disabled'),
    [Input('pause-button', 'n_clicks'),
     Input('resume-button', 'n_clicks')]
)
def update_interval_disabled(pause_clicks, resume_clicks):
    if pause_clicks > resume_clicks:
        return True
    return False

def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

news_types = [
    {"type": "Quarterly financial results exceed expectations", "impact": "positive"},
    {"type": "Quarterly financial results disappoint investors", "impact": "negative"},
    {"type": "Successful mergers and acquisitions boost company growth", "impact": "positive"},
    {"type": "Failed merger talks lead to stock decline", "impact": "negative"},
    {"type": "New CEO brings fresh vision to the company", "impact": "positive"},
    {"type": "CEO resignation creates uncertainty in the market", "impact": "negative"},
    {"type": "Innovative new product launch drives sales surge", "impact": "positive"},
    {"type": "New product launch fails to meet market expectations", "impact": "negative"},
    {"type": "Regulatory approval paves the way for expansion", "impact": "positive"},
    {"type": "New regulations pose challenges for the industry", "impact": "negative"},
    {"type": "Positive macroeconomic data supports market rally", "impact": "positive"},
    {"type": "Negative macroeconomic data triggers market sell-off", "impact": "negative"},
    {"type": "Central bank policies stimulate economic growth", "impact": "positive"},
    {"type": "Tightening monetary policies concern investors", "impact": "negative"},
    {"type": "Company outperforms competitors in the sector", "impact": "positive"},
    {"type": "Intense competition affects company's market share", "impact": "negative"},
    {"type": "Scandal-free reputation strengthens brand loyalty", "impact": "positive"},
    {"type": "Corporate scandal damages company's reputation", "impact": "negative"},
    {"type": "Sector performance shows robust growth", "impact": "positive"},
    {"type": "Sector performance shows signs of slowdown", "impact": "negative"},
]

def generate_random_news():
    news = random.choice(news_types)
    return {
        "type": news["type"],
        "impact": news["impact"],
        "timestamp": datetime.now().strftime('%H:%M:%S')
    }

def adjust_stock_price(current_price, news):
    if news["impact"] == "positive":
        return current_price * (1 + random.uniform(0.1, 0.2))
    elif news["impact"] == "negative":
        return current_price * (1 - random.uniform(0.1, 0.2))
    return current_price


# In[7]:


# Cellule 4
@app.callback(
    [Output('ohlc-data', 'data'), Output('transaction-table', 'data'), Output('news-table', 'data'), 
     Output('portfolio-value', 'children'), Output('long-clicks', 'data'), Output('short-clicks', 'data'), Output('positions-table', 'data'), Output('close-buttons-container', 'children')],
    [Input('graph-update', 'n_intervals'), Input('long-button', 'n_clicks'), Input('short-button', 'n_clicks'), Input({'type': 'close-button', 'index': ALL}, 'n_clicks')],
    [State('ohlc-data', 'data'), State('shares-input', 'value'), State('long-clicks', 'data'), State('short-clicks', 'data')]
)
def update_ohlc_data(n, long_clicks, short_clicks, close_clicks, data, shares_input, long_clicks_state, short_clicks_state):
    ctx = dash.callback_context

    last_close = data['close'][-1]
    new_open = last_close
    new_close = last_close * np.exp((r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * np.random.normal())
    new_high = max(new_open, new_close) * (1 + 0.01 * np.random.normal())
    new_low = min(new_open, new_close) * (1 - 0.01 * np.random.normal())

    data['open'].append(new_open)
    data['high'].append(new_high)
    data['low'].append(new_low)
    data['close'].append(new_close)

    num_transactions = random.randint(1, 10)
    total_volume = np.random.randint(100, 1000)
    volume_per_transaction = total_volume // num_transactions

    transactions = []

    for _ in range(num_transactions):
        transaction_id = generate_transaction_id()
        timestamp = datetime.now().strftime('%H:%M:%S')
        transaction_type = np.random.choice(['Buy', 'Sell'])
        market_type = np.random.choice(['Exchange', 'OTC'])
        order_type = np.random.choice(['Market', 'Limit'])

        transaction = {
            'transaction_id': transaction_id,
            'timestamp': timestamp,
            'price': new_close,
            'volume': volume_per_transaction,
            'transaction_type': transaction_type,
            'market_type': market_type,
            'order_type': order_type
        }

        transactions.append(transaction)

    data['transactions'].extend(transactions)

    if random.random() < (2 / 60):  
        news = generate_random_news()
        data['news'].append(news)
        new_close = adjust_stock_price(new_close, news)
        data['close'][-1] = new_close

    portfolio = data['portfolio']
    if 'long-button.n_clicks' in ctx.triggered[0]['prop_id']:
        # Buy shares
        shares_to_buy = shares_input
        total_cost = shares_to_buy * new_close
        if portfolio['balance'] >= total_cost:
            portfolio['balance'] -= total_cost
            portfolio['shares'] += shares_to_buy
            position = {
                'type': 'Long',
                'shares': shares_to_buy,
                'open_price': new_close,
                'current_price': new_close,
                'profit_loss': 0
            }
            data['positions'].append(position)
        long_clicks_state = long_clicks
    elif 'short-button.n_clicks' in ctx.triggered[0]['prop_id']:

        shares_to_short = shares_input
        total_gain = shares_to_short * new_close
        portfolio['balance'] += total_gain
        position = {
            'type': 'Short',
            'shares': shares_to_short,
            'open_price': new_close,
            'current_price': new_close,
            'profit_loss': 0
        }
        data['positions'].append(position)
        short_clicks_state = short_clicks

    for i, n_click in enumerate(close_clicks):
        if n_click:
            closed_position = data['positions'].pop(i)
            if closed_position['type'] == 'Long':
                portfolio['balance'] += closed_position['shares'] * closed_position['current_price']
                portfolio['shares'] -= closed_position['shares']
            else: 
                portfolio['balance'] -= closed_position['shares'] * closed_position['current_price']
            break

    for position in data['positions']:
        position['current_price'] = new_close
        if position['type'] == 'Long':
            position['profit_loss'] = (new_close - position['open_price']) * position['shares']
        else: 
            position['profit_loss'] = (position['open_price'] - new_close) * position['shares']

    portfolio_value = portfolio['balance']
    for position in data['positions']:
        if position['type'] == 'Long':
            portfolio_value += position['shares'] * position['current_price']
        else:  # Short
            portfolio_value -= position['shares'] * position['current_price']
    portfolio['value'] = portfolio_value
    portfolio_value_text = f"Portfolio Value: {portfolio['value']:.2f} EUR | Current Stock Price: {new_close:.2f} EUR"

    positions_table_data = [
        {
            'type': position['type'],
            'shares': position['shares'],
            'open_price': position['open_price'],
            'current_price': position['current_price'],
            'profit_loss': position['profit_loss']
        } for position in data['positions']
    ]

    close_buttons = [
        html.Button('Close', id={'type': 'close-button', 'index': i}, n_clicks=0, style={'margin': '5px', 'background-color': '#f44336', 'color': 'white'})
        for i in range(len(data['positions']))
    ]

    return data, list(reversed(data['transactions'])), list(reversed(data['news'])), portfolio_value_text, long_clicks_state, short_clicks_state, positions_table_data, close_buttons


# In[8]:


@app.callback(
    Output('live-graph', 'figure'),
    [Input('ohlc-data', 'data')],
    [State('live-graph', 'relayoutData')]
)
def update_graph_scatter(data, relayoutData):
    trace = go.Candlestick(
        x=list(range(len(data['close']))),
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Candlestick',
        increasing=dict(line=dict(color='green', width=1), fillcolor='green'),
        decreasing=dict(line=dict(color='red', width=1), fillcolor='red')
    )
    
    layout = go.Layout(
        title='Simulated Stock Price Movements',
        xaxis=dict(
            title='Time',
            range=[0, len(data['close'])],
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            title='Price',
            range=[min(data['low']), max(data['high'])]
        ),
        plot_bgcolor='#f4f4f9',
        paper_bgcolor='#f4f4f9'
    )

    if relayoutData and 'xaxis.range[0]' in relayoutData:
        layout['xaxis']['range'] = [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]
    if relayoutData and 'yaxis.range[0]' in relayoutData:
        layout['yaxis']['range'] = [relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']]

    figure = {
        'data': [trace],
        'layout': layout
    }
    
    return figure


# In[9]:


#if __name__ == '__main__':
    #app.run_server(debug=True, host='127.0.0.1', port=8050)


# In[95]:


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))


# In[ ]:




