"""
Clinical Trials upload page for Dash frontend.

This page provides a UI for uploading Banner Billing Excel files
and downloading the processed report.
"""
import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import requests
import base64
from io import BytesIO
import os

# Get the FastAPI base URL from environment or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def create_clinical_trials_page():
    """
    Create the clinical trials upload page layout.
    
    Returns:
        Dash layout component
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Clinical Trials Data Upload", className="mb-4"),
                html.P([
                    "Upload Banner Billing Excel files for processing. ",
                    "Each file can contain multiple tabs (one bill per tab). ",
                    "Files will be processed and combined into a single downloadable report."
                ], className="text-muted mb-4"),
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("File Upload"),
                    dbc.CardBody([
                        dcc.Upload(
                            id='ct-upload-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Files')
                            ]),
                            style={
                                'width': '100%',
                                'height': '80px',
                                'lineHeight': '80px',
                                'borderWidth': '2px',
                                'borderStyle': 'dashed',
                                'borderRadius': '10px',
                                'textAlign': 'center',
                                'margin': '10px',
                                'cursor': 'pointer'
                            },
                            multiple=True  # Allow multiple files
                        ),
                        html.P(
                            "You can select multiple Excel files at once. "
                            "Supported formats: XLSX, XLS",
                            className="text-muted small mt-2 mb-3"
                        ),
                        html.Div(id='ct-selected-files', className="mb-3"),
                        dbc.Button(
                            "Process Files",
                            id="ct-process-button",
                            color="primary",
                            className="w-100",
                            disabled=True
                        ),
                        # Loading spinner
                        dcc.Loading(
                            id="ct-loading",
                            type="default",
                            children=html.Div(id='ct-loading-output')
                        ),
                        html.Div(id='ct-upload-status', className="mt-3"),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Hidden download component
        dcc.Download(id='ct-download-report'),
        
        dbc.Row([
            dbc.Col([
                html.Div(id='ct-upload-results')
            ], width=12)
        ])
    ], fluid=True)


# Register the upload page layout
clinical_trials_layout = create_clinical_trials_page()


@callback(
    Output('ct-process-button', 'disabled'),
    Output('ct-selected-files', 'children'),
    Input('ct-upload-data', 'contents'),
    State('ct-upload-data', 'filename')
)
def update_file_display(contents, filenames):
    """Enable process button and display selected files."""
    # Determine if button should be disabled
    if contents is None:
        button_disabled = True
    elif isinstance(contents, list):
        button_disabled = len(contents) == 0
    else:
        button_disabled = False
    
    # Display selected files
    if not contents or not filenames:
        file_display = html.Div()
    else:
        # Ensure we have lists
        if not isinstance(filenames, list):
            filenames = [filenames]
        
        file_count = len(filenames)
        
        if file_count == 0:
            file_display = html.Div()
        else:
            # Validate file types
            valid_files = []
            invalid_files = []
            
            for name in filenames:
                file_ext = name.split('.')[-1].lower() if '.' in name else ''
                if file_ext in ['xlsx', 'xls']:
                    valid_files.append(name)
                else:
                    invalid_files.append(name)
            
            file_list = []
            for name in valid_files:
                file_list.append(
                    html.Li([
                        "📊 ",
                        name
                    ], className="mb-1 text-success")
                )
            
            for name in invalid_files:
                file_list.append(
                    html.Li([
                        "⚠️ ",
                        name,
                        " (unsupported format)"
                    ], className="mb-1 text-danger")
                )
            
            alert_color = "info" if not invalid_files else "warning"
            
            file_display = dbc.Alert([
                html.Strong(f"{file_count} file(s) selected:"),
                html.Ul(file_list, className="mb-0 mt-2"),
                html.Small(
                    "Only Excel files (.xlsx, .xls) will be processed.",
                    className="text-muted"
                ) if invalid_files else None
            ], color=alert_color, className="mb-0")
            
            # Disable button if no valid files
            if not valid_files:
                button_disabled = True
    
    return button_disabled, file_display


@callback(
    Output('ct-upload-status', 'children'),
    Output('ct-upload-results', 'children'),
    Output('ct-download-report', 'data'),
    Output('ct-loading-output', 'children'),
    Input('ct-process-button', 'n_clicks'),
    State('ct-upload-data', 'contents'),
    State('ct-upload-data', 'filename'),
    prevent_initial_call=True
)
def handle_upload(n_clicks, contents_list, filename_list):
    """
    Handle file uploads and trigger processing.
    
    Args:
        n_clicks: Number of times process button was clicked
        contents_list: List of base64 encoded file contents
        filename_list: List of filenames
        
    Returns:
        Tuple of (status message, results display, download data, loading output)
    """
    if not contents_list or not filename_list:
        return "", "", None, ""
    
    # Ensure we have lists
    if not isinstance(contents_list, list):
        contents_list = [contents_list]
    if not isinstance(filename_list, list):
        filename_list = [filename_list]
    
    try:
        # Filter to only Excel files
        files_data = []
        for contents, filename in zip(contents_list, filename_list):
            if contents is None:
                continue
            
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            if file_ext not in ['xlsx', 'xls']:
                continue
            
            # Parse the base64 content
            content_type, content_string = contents.split(',')
            
            # Decode base64
            file_data = base64.b64decode(content_string)
            
            # Add to files list
            files_data.append(('files', (filename, file_data, 
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')))
        
        if not files_data:
            return (
                dbc.Alert("No valid Excel files to upload", color="warning", className="mb-3"),
                html.Div(),
                None,
                ""
            )
        
        # Send to FastAPI endpoint
        response = requests.post(
            f"{API_BASE_URL}/clinical-trials/process-billings",
            files=files_data,
            timeout=600  # 10 minute timeout for large files
        )
        
        if response.status_code == 200:
            # Get filename from Content-Disposition header
            content_disp = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disp:
                download_filename = content_disp.split('filename=')[1].strip('"')
            else:
                download_filename = 'banner_billings_report.xlsx'
            
            # Prepare download
            download_data = {
                'content': base64.b64encode(response.content).decode('utf-8'),
                'filename': download_filename,
                'base64': True,
                'type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            
            # Success message
            status_alert = dbc.Alert([
                html.Strong("Success! "),
                f"Processed {len(files_data)} file(s). Your report is downloading."
            ], color="success", className="mb-3")
            
            # Results display
            results_content = dbc.Card([
                dbc.CardHeader("Processing Complete"),
                dbc.CardBody([
                    html.P([
                        html.Strong(f"{len(files_data)}"),
                        " file(s) processed successfully."
                    ]),
                    html.P([
                        "Your report ",
                        html.Strong(download_filename),
                        " should download automatically."
                    ]),
                    html.Hr(),
                    dbc.Button(
                        "Download Report Again",
                        id="ct-download-again",
                        color="primary",
                        className="me-2"
                    ),
                    html.Small(
                        "If the download didn't start, click the button above.",
                        className="text-muted d-block mt-2"
                    )
                ])
            ], className="mb-4")
            
            return status_alert, results_content, download_data, ""
        else:
            # Error response
            try:
                error_detail = response.json().get('detail', 'Unknown error occurred')
            except:
                error_detail = response.text or 'Unknown error occurred'
            
            return (
                dbc.Alert(f"Processing failed: {error_detail}", color="danger", className="mb-3"),
                html.Div(),
                None,
                ""
            )
            
    except requests.exceptions.Timeout:
        return (
            dbc.Alert(
                "Request timed out. The files may be too large or the server is busy. "
                "Please try again with fewer files.",
                color="danger",
                className="mb-3"
            ),
            html.Div(),
            None,
            ""
        )
    except requests.exceptions.ConnectionError:
        return (
            dbc.Alert(
                "Could not connect to the server. Please check if the server is running.",
                color="danger",
                className="mb-3"
            ),
            html.Div(),
            None,
            ""
        )
    except Exception as e:
        return (
            dbc.Alert(f"Error processing upload: {str(e)}", color="danger", className="mb-3"),
            html.Div(),
            None,
            ""
        )
