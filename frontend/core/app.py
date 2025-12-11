"""
Core Dash application setup.

This module creates the base Dash app that will be mounted under FastAPI.
Individual modules can register their pages with this app.
"""
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import os

# Get the FastAPI base URL from environment or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Create Dash app with Bootstrap theme
# Configured for mounting under FastAPI at /dash path
# routes_pathname_prefix is '/' because FastAPI handles the /dash prefix via mounting
# requests_pathname_prefix is '/dash/' so Dash generates correct asset URLs
dash_app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    routes_pathname_prefix='/',
    requests_pathname_prefix='/dash/'
)

# Base layout - modules will add their own layouts
dash_app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

