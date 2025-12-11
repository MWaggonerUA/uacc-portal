"""
Admin upload page for Dash frontend.

This page provides a UI for administrators to upload multiple CSV/Excel files
and view processing results. Dataset types are auto-detected from column headers.
"""
import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import requests
import base64
from frontend.core.app import dash_app, API_BASE_URL


def create_upload_page():
    """
    Create the upload page layout.
    
    Returns:
        Dash layout component
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Admin Data Upload", className="mb-4"),
                html.P(
                    "Upload one or more CSV or Excel files for processing and validation. "
                    "Dataset types are automatically detected from column headers. "
                    "Files are processed in parallel for faster uploads.",
                    className="text-muted mb-4"
                ),
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("File Upload"),
                    dbc.CardBody([
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Files')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                            multiple=True  # Allow multiple files
                        ),
                        html.P(
                            "You can select multiple files at once. Supported formats: CSV, XLSX, XLS",
                            className="text-muted small mt-2 mb-3"
                        ),
                        html.Div(id='selected-files', className="mb-3"),
                        dbc.Checkbox(
                            id='write-to-db',
                            label='Write validated data to database',
                            value=False,
                            className="mb-3"
                        ),
                        dbc.Button(
                            "Process Files",
                            id="process-button",
                            color="primary",
                            className="w-100",
                            disabled=True
                        ),
                        html.Div(id='upload-status', className="mt-3"),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.Div(id='upload-results')
            ], width=12)
        ])
    ], fluid=True)


# Register the upload page layout
upload_layout = create_upload_page()


@callback(
    Output('process-button', 'disabled'),
    Output('selected-files', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_file_display(contents, filename):
    """Enable process button and display selected files."""
    # Determine if button should be disabled
    button_disabled = contents is None or len(contents) == 0 if isinstance(contents, list) else contents is None
    
    # Display selected files
    if not contents or not filename:
        file_display = html.Div()
    else:
        # Ensure we have lists
        if not isinstance(filename, list):
            filename = [filename]
        
        file_count = len(filename)
        
        if file_count == 0:
            file_display = html.Div()
        else:
            file_list = []
            for i, name in enumerate(filename, 1):
                # Determine file type icon/indicator
                file_ext = name.split('.')[-1].lower() if '.' in name else ''
                file_type_icon = {
                    'csv': '📄',
                    'xlsx': '📊',
                    'xls': '📊'
                }.get(file_ext, '📎')
                
                file_list.append(
                    html.Li([
                        f"{file_type_icon} ",
                        name
                    ], className="mb-1")
                )
            
            file_display = dbc.Alert([
                html.Strong(f"{file_count} file(s) selected:"),
                html.Ul(file_list, className="mb-0 mt-2")
            ], color="info", className="mb-0")
    
    return button_disabled, file_display


@callback(
    Output('upload-status', 'children'),
    Output('upload-results', 'children'),
    Input('process-button', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('write-to-db', 'value'),
    prevent_initial_call=True
)
def handle_upload(n_clicks, contents_list, filename_list, write_to_db):
    """
    Handle multiple file uploads and send to FastAPI backend.
    
    Args:
        n_clicks: Number of times process button was clicked
        contents_list: List of base64 encoded file contents
        filename_list: List of filenames
        write_to_db: Whether to write to database
        
    Returns:
        Tuple of (status message, results display)
    """
    if not contents_list or not filename_list:
        return "", ""
    
    # Ensure we have lists
    if not isinstance(contents_list, list):
        contents_list = [contents_list]
    if not isinstance(filename_list, list):
        filename_list = [filename_list]
    
    try:
        # Prepare files for upload
        # FastAPI expects multiple files with the same parameter name
        files_data = []
        for i, (contents, filename) in enumerate(zip(contents_list, filename_list)):
            if contents is None:
                continue
            
            # Parse the base64 content
            content_type, content_string = contents.split(',')
            
            # Decode base64
            file_data = base64.b64decode(content_string)
            
            # Add to files list - use 'files' as parameter name for each file
            files_data.append(('files', (filename, file_data, content_type.split(';')[0])))
        
        if not files_data:
            return (
                dbc.Alert("No valid files to upload", color="warning", className="mb-3"),
                html.Div()
            )
        
        # Send to FastAPI endpoint
        response = requests.post(
            f"{API_BASE_URL}/admin/uploads/raw-data-multiple",
            files=files_data,
            params={
                'write_to_db': write_to_db,
                'parallel': True
            },
            timeout=600  # 10 minute timeout for multiple large files
        )
        
        if response.status_code == 200:
            result = response.json()
            summaries = result.get('summaries', [])
            
            # Build overall status alert
            status_color = 'success' if result.get('overall_success') else 'warning'
            status_alert = dbc.Alert(
                result.get('message', 'Processing complete'),
                color=status_color,
                className="mb-3"
            )
            
            # Build results display for each file
            results_content = []
            
            # Overall summary card
            results_content.append(
                dbc.Card([
                    dbc.CardHeader("Overall Summary"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H3(result.get('total_files', 0), className="text-primary"),
                                        html.P("Total Files", className="mb-0")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H3(result.get('successful_files', 0), className="text-success"),
                                        html.P("Successful", className="mb-0")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H3(result.get('failed_files', 0), className="text-danger"),
                                        html.P("Failed", className="mb-0")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H3(
                                            "✓" if result.get('overall_success') else "✗",
                                            className="text-success" if result.get('overall_success') else "text-danger"
                                        ),
                                        html.P("Status", className="mb-0")
                                    ])
                                ])
                            ], width=3),
                        ])
                    ])
                ], className="mb-4")
            )
            
            # Individual file results
            for idx, summary in enumerate(summaries):
                file_card = dbc.Card([
                    dbc.CardHeader([
                        html.H5(f"File {idx + 1}: {summary.get('file_name', 'Unknown')}", className="mb-0"),
                        html.Small(
                            f"Type: {summary.get('file_type', 'N/A').upper()}",
                            className="text-muted"
                        )
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(summary.get('total_rows', 0), className="text-primary"),
                                        html.P("Total Rows", className="mb-0")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(summary.get('valid_rows', 0), className="text-success"),
                                        html.P("Valid Rows", className="mb-0")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(summary.get('invalid_rows', 0), className="text-danger"),
                                        html.P("Invalid Rows", className="mb-0")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Badge(
                                    "✓ Success" if summary.get('invalid_rows', 0) == 0 else "✗ Errors",
                                    color="success" if summary.get('invalid_rows', 0) == 0 else "danger",
                                    className="p-2"
                                )
                            ], width=3),
                        ], className="mb-3"),
                        
                        # Errors display (if any)
                        html.Div([
                            html.H6("Validation Errors", className="mb-2"),
                            dbc.Table([
                                html.Thead([
                                    html.Tr([
                                        html.Th("Row"),
                                        html.Th("Column"),
                                        html.Th("Error Message"),
                                        html.Th("Value")
                                    ])
                                ]),
                                html.Tbody([
                                    html.Tr([
                                        html.Td(error.get('row_number')),
                                        html.Td(error.get('column', 'N/A')),
                                        html.Td(error.get('message')),
                                        html.Td(str(error.get('value', 'N/A'))[:50])
                                    ])
                                    for error in summary.get('errors', [])[:10]  # Show first 10 errors
                                ])
                            ], bordered=True, hover=True, responsive=True, size="sm")
                        ]) if summary.get('errors') else html.Div(),
                        
                        # Preview data (if available)
                        html.Div([
                            html.H6("Data Preview (First 5 Valid Rows)", className="mb-2 mt-3"),
                            dbc.Table([
                                html.Thead([
                                    html.Tr([html.Th(col) for col in summary['preview_data'][0].keys()])
                                ]),
                                html.Tbody([
                                    html.Tr([
                                        html.Td(str(val)[:100])  # Truncate long values
                                        for val in row.values()
                                    ])
                                    for row in summary['preview_data']
                                ])
                            ], bordered=True, hover=True, responsive=True, size="sm")
                        ]) if summary.get('preview_data') else html.Div()
                    ])
                ], className="mb-3")
                results_content.append(file_card)
            
            return status_alert, html.Div(results_content)
        else:
            error_msg = response.json().get('detail', 'Unknown error occurred')
            return (
                dbc.Alert(f"Upload failed: {error_msg}", color="danger", className="mb-3"),
                html.Div()
            )
            
    except Exception as e:
        return (
            dbc.Alert(f"Error processing upload: {str(e)}", color="danger", className="mb-3"),
            html.Div()
        )
