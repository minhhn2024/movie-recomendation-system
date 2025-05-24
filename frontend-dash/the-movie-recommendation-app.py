import dash
from dash import Dash, html, dcc, callback, Output, Input, clientside_callback, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import json
import os

OMDB_API_KEY = 'd3e2b7b7'

def get_token(username="admin@example.com", password="changethis"):
    url = "http://localhost:8000/api/v1/login/access-token"
    payload = {
        'username': username,
        'password': password
    }
    headers = {
        'Accept': 'application/json',
        'Origin': 'http://localhost:5173',
        'Referer': 'http://localhost:5173/'
    }
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        try:
            return response.json().get("access_token", "")
        except Exception:
            return ""
    return ""

# TOKEN = get_token()


df = pd.read_csv("./movies_metadata.csv", low_memory=False)
df.release_date = pd.to_datetime(df.release_date, errors='coerce')
df['release_year'] = df.release_date.dt.year.astype('Int64')

all_genres = ['Action', 'Adventure', 'Animation', 'Aniplex', 'BROSTA TV', 'Carousel Productions', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 'Foreign', 'GoHands', 'History', 'Horror', 'Mardock Scramble Production Committee', 'Music', 'Mystery', 'Romance', 'Science Fiction', 'Sentai Filmworks', 'TV Movie', 'Telescene Film Group Productions', 'Thriller', 'Vision View Entertainment', 'War', 'Western']


all_movies = df['original_title'].dropna().unique().tolist()

def fetch_all_api_genres():
    url = "http://localhost:8000/api/v1/genres"
    payload = {}
    headers = {
        'accept': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception:
        return []

all_api_genres = fetch_all_api_genres()
# sau khi lấy dữ liệu genres thì trích xuất ra danh sách genre và truyền vào all_genres

def fetch_all_api_movies(token: str = "", skip: int = 0, limit: int = 10):
    url = "http://localhost:8000/api/v1/movies"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    params = {
        'skip': skip,
        'limit': limit
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception:
        return []

all_api_movies = fetch_all_api_movies(token=get_token(), skip=0, limit=10)
# sau khi lấy dữ liệu movies thì trích xuất ra danh sách movie và truyền vào all_movies

# muốn lấy id thì truyền vào một biến khác để mapping movie title với id


num_suggestions = 20

def get_movie_poster(imdb_id: str) -> str:

    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data.get('Poster', '')

def func_suggestions_by_movies(df: pd.DataFrame, title: str, num_suggestions: int = 5) -> pd.DataFrame:

    if title not in df['original_title'].values:
        return pd.DataFrame()
    genre = df.loc[df['original_title'] == title, 'genres'].values[0]
    suggestions = df[df['genres'] == genre]
    suggestions = suggestions[suggestions['original_title'] != title]
    return suggestions[['original_title', 'release_date', 'vote_average', 'popularity', 'imdb_id', 'release_year']].sort_values(by='vote_average', ascending=False).head(num_suggestions)

def func_suggestions_by_movies_api_content_base(df: pd.DataFrame, title: str, num_suggestions: int = 5, token: str = "") -> pd.DataFrame:

    if title not in df['original_title'].values:
        return pd.DataFrame()
    movie_row = df.loc[df['original_title'] == title].iloc[0]
    movie_id = movie_row.get('id')
    if pd.isna(movie_id):
        return pd.DataFrame()
    url = "http://localhost:8000/api/v1/recommender/content-base"
    payload = {
        "movieId": int(movie_id),
        "limit": num_suggestions
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': token
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        return pd.DataFrame()
    data = response.json()

    return pd.DataFrame(data)

def func_suggestions_by_movies_api_collaborative_filtering(df: pd.DataFrame, title: str, num_suggestions: int = 5, token: str = "") -> pd.DataFrame:

    if title not in df['original_title'].values:
        return pd.DataFrame()
    movie_row = df.loc[df['original_title'] == title].iloc[0]
    movie_id = movie_row.get('id')
    if pd.isna(movie_id):
        return pd.DataFrame()
    url = "http://localhost:8000/api/v1/recommender/collaborative-filtering"
    payload = {
        "movieId": int(movie_id),
        "limit": num_suggestions
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': token
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        return pd.DataFrame()
    data = response.json()

    return pd.DataFrame(data)

def func_suggestions_by_genres_api(df: pd.DataFrame, genres: list, num_suggestions: int = 5, token: str = "") -> pd.DataFrame:

    if not genres:
        return pd.DataFrame()
    url = "http://localhost:8000/api/v1/recommender/by-genres"
    payload = {
        "genres": genres,
        "limit": num_suggestions
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': token
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        return pd.DataFrame()
    data = response.json()

    return pd.DataFrame(data)

# def func_suggestions_by_genres(df: pd.DataFrame, genre_lst: list, num_suggestions: int = 5) -> pd.DataFrame:

#     if title not in df['original_title'].values:
#         return pd.DataFrame()
#     genre = df.loc[df['original_title'] == title, 'genres'].values[0]
#     suggestions = df[df['genres'] == genre]
#     suggestions = suggestions[suggestions['original_title'] != title]
#     return suggestions[['original_title', 'release_date', 'vote_average', 'popularity', 'imdb_id', 'release_year']].sort_values(by='vote_average', ascending=False).head(num_suggestions)

def create_card(card_id: int) -> dbc.Card:

    return dbc.Card(
        dbc.CardBody(
            [
                html.Img(src="", id=f"card-img-{card_id}", style={"width": "100%", "height": "300px", "object-fit": "cover", "margin-bottom": "10px"}),
                html.H4("Title", id=f"card-title-{card_id}", style={"text-align": "center", "white-space": "nowrap", "overflow": "hidden", "text-overflow": "ellipsis"}, title="Title"),
                html.H6("Card subtitle", id=f"card-subtitle-{card_id}", style={"text-align": "center", "color": "#6c757d"}),
                html.Div(
                    [
                        dbc.CardLink("Trailer", id=f"card-trailer-{card_id}", href="https://www.youtube.com/results?search_query=up+trailer", target="_blank", style={"text-align": "center", "margin": "0 5px"}),
                        dbc.CardLink("Info", id=f"card-info-{card_id}", href=f"https://www.imdb.com/title/tt1049413/", target="_blank", style={"text-align": "center", "margin": "0 5px"}),
                    ],
                    style={"text-align": "center"}
                ),
            ]
        ),
        style={"width": "18rem", "margin": "10px"}
    )

def create_buttons() -> list:

    return [
        dbc.Col(
            dbc.Button(
                [
                    html.Img(src="https://cdn-icons-png.flaticon.com/512/1828/1828884.png", style={"width": "20px", 'margin': '0px 10px 5px 0px'}),
                    "Phim đã xem"
                ],
                id="button-model-1",
                color="light",
                outline=True,
                style={"width": "18rem", "border": "2px solid #6c757d", "color": "#6c757d", "transition": "all 0.3s", "textAlign": "left"},
                className="hover-button"
            ),
            width='auto',
            style={"margin": "10px"}
        ),
        dbc.Col(
            dbc.Button(
                [
                    html.Img(src="https://cdn-icons-png.flaticon.com/512/833/833472.png", style={"width": "20px", 'margin': '0px 10px 5px 0px'}),
                    "Thể loại phim yêu thích"
                ],
                id="button-model-2",
                color="light",
                outline=True,
                style={"width": "18rem", "border": "2px solid #6c757d", "color": "#6c757d", "transition": "all 0.3s", "textAlign": "left"},
                className="hover-button"
            ),
            width='auto',
            style={"margin": "10px"}
        ),
    ]


cards = [dbc.Col(create_card(i), className='d-flex justify-content-center', width=3) for i in range(0, num_suggestions)]


buttons = create_buttons()

color_mode_switch =  html.Span(
    [
        dbc.Label(className="fa fa-moon", html_for="switch"),
        dbc.Switch( id="switch", value=True, className="d-inline-block ms-1", persistence=True),
        dbc.Label(className="fa fa-sun", html_for="switch"),
    ]
)

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"


app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME, dbc_css])
navbar = dbc.NavbarSimple(
    id='navbar',
    brand=html.Div(
        [
            html.Img(src="/assets/owl-logo.png", height="30px", style={"margin-right": "10px"}),  
            "Cú Cine"
        ],
        style={"display": "flex", "align-items": "center"}
    ),
    brand_href="#",
    children=[
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("Home", href="#")),
                dbc.NavItem(dbc.NavLink("About", href="#")),
                dbc.NavItem(dbc.NavLink("Contact", href="#")),
                dbc.NavItem(color_mode_switch, style={'padding':'8px 8px 8px 8px'}),
            ],
        ),
    ],
    fixed="top",
    className="dbc",
)

app.layout = dbc.Container([
    navbar,
    html.Div(
        className="scroll-container",
        style={'padding-top': '70px', 'padding-bottom': '0px'},  
        children=[
            html.Div(
                className="scroll-content",
                children=[
                    html.Img(
                        src=get_movie_poster(imdb_id),
                        style={'height': '100px', 'margin-right': '10px'}
                    ) for imdb_id in df.sort_values(by='popularity', ascending=False).head(20)['imdb_id'].dropna().tolist()
                ] * 3
            )
        ]
    ),
    html.Hr(),
    dbc.Row(
        html.Div(
            html.Img(src="/assets/owl-logo.png", height='260px', style={"margin-top": "10px"}),
            style={"textAlign": "center"} 
        )
    ),
    html.H1('Cú Cine', style={'textAlign': 'center', 'margin-top': '10px'}), 
    html.P("Xin chào chủ nhân", style={'textAlign': 'center'}),
    html.P("Cú Cine là ứng dụng gợi ý phim dựa trên sở thích của chủ nhân!", style={'textAlign': 'center'}),
    html.P("Bước 1: Chủ nhân có muốn tôi gợi ý phim không?", style={'textAlign': 'center'}),
    dbc.Row(
        [
            dbc.Col(
                dbc.Button("Có", id="button-yes", color="success", style={"margin": "10px"}),
                width='auto',
                style={'margin':'10px'}
            ),dbc.Col(
                dbc.Button("Không", id="button-no", color="danger", style={"margin": "10px"}),
                width='auto',
                style={'margin':'10px'}
            ),
        ],
        justify='center'
    ),
    html.P("Bước 2: Chủ nhân muốn tìm phim dựa theo...", style={'textAlign': 'center'}),
    dbc.Row(buttons, justify='center'),
    html.P("Bước 3: Chủ nhân hãy lựa chọn...", style={'textAlign': 'center'}),
    dcc.Dropdown(
        options=[],
        value=[],
        id='dropdown-selection',
        placeholder='Phim hay Thể loại?',
        multi=True,
        style={'margin': '0 auto', 'width': '100%', 'maxWidth': '500px'}
    ),
    dbc.Row(
        dbc.Col(
            dbc.Button("Gợi ý phim", id="dropdown-submit", color="primary", style={"margin-top": "10px"}),
            width='auto',
            style={'textAlign': 'center'}
        ),
        justify='center'
    ),
    html.Br(),
    html.H5("Cú Cine chúc chủ nhân có những giây giúp xem phim vui vẻ!", style={'textAlign': 'center'}),
    dbc.Row(cards, style={'margin-top': '10px'}),
], style={'padding': '10px'}, className="dbc")

@callback(
    [Output("button-model-1", "style"), Output("button-model-2", "style"), Output("dropdown-selection", "options"), Output("dropdown-selection", "value"), Output("dropdown-selection","placeholder")],
    [Input("button-model-1", "n_clicks"), Input("button-model-2", "n_clicks")],
    prevent_initial_call=True
)
def update_button_styles_and_dropdown(btn1_clicks, btn2_clicks):
    default_style = {"width": "18rem", "border": "2px solid #6c757d", "color": "#6c757d", "transition": "all 0.3s", "textAlign": "left"}
    active_style = {"width": "18rem", "border": "2px solid #6c757d", "color": "#ffffff", "background-color": "#6c757d", "transition": "all 0.3s", "textAlign": "left"}
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return [default_style, default_style, [], [], "Phim hay Thể loại?"]
    
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id == "button-model-1":
        options = all_movies
        return [active_style, default_style, options, [], "Phim yêu thích..."]
    elif triggered_id == "button-model-2":
        options = all_genres
        return [default_style, active_style, options, [], "Thể loại yêu thích..."]
    return [default_style, default_style, [], []]

@callback(
    [Output(f'card-title-{i}', 'children') for i in range(0, num_suggestions)] +
    [Output(f'card-title-{i}', 'title') for i in range(0, num_suggestions)] +
    [Output(f'card-subtitle-{i}', 'children') for i in range(0, num_suggestions)] +
    [Output(f'card-img-{i}', 'src') for i in range(0, num_suggestions)] + 
    [Output(f'card-info-{i}', 'href') for i in range(0, num_suggestions)] +
    [Output(f'card-trailer-{i}', 'href') for i in range(0, num_suggestions)],
    Input('dropdown-submit', 'n_clicks'),
    State('dropdown-selection', 'value'),
    State('button-model-1', 'n_clicks'),
    State('button-model-2', 'n_clicks'),
)
def update_cards(submit, selected_value, btn1_clicks, btn2_clicks):
    default_titles = ["N/A"] * num_suggestions
    default_subtitles = ["N/A"] * num_suggestions
    default_posters = ["/assets/owl.png"] * num_suggestions
    default_infos = ["N/A"] * num_suggestions
    default_trailers = ["N/A"] * num_suggestions


    ctx = dash.callback_context
    if not ctx.triggered or not selected_value:
        return default_titles + default_titles + default_subtitles + default_posters + default_infos + default_trailers

    token = get_token()
    triggered_id = None
    for t in ctx.triggered:
        if t['prop_id'].startswith('button-model-1'):
            triggered_id = 'button-model-1'
        elif t['prop_id'].startswith('button-model-2'):
            triggered_id = 'button-model-2'

    if triggered_id is None:
        if (btn1_clicks or 0) > (btn2_clicks or 0):
            triggered_id = 'button-model-1'
        elif (btn2_clicks or 0) > (btn1_clicks or 0):
            triggered_id = 'button-model-2'


    if triggered_id == 'button-model-1':
        # By movie
        if not selected_value:
            return default_titles + default_titles + default_subtitles + default_posters + default_infos + default_trailers
        suggestions = func_suggestions_by_movies_api_collaborative_filtering(df, selected_value[0], num_suggestions, token)
    elif triggered_id == 'button-model-2':
        # By genres
        if not selected_value:
            return default_titles + default_titles + default_subtitles + default_posters + default_infos + default_trailers
        suggestions = func_suggestions_by_genres_api(df, selected_value, num_suggestions, token)
    else:
        return default_titles + default_titles + default_subtitles + default_posters + default_infos + default_trailers

    if suggestions.empty:
        return default_titles + default_titles + default_subtitles + default_posters + default_infos + default_trailers

    titles = suggestions['original_title'].tolist() if 'original_title' in suggestions else default_titles
    subtitles = suggestions['release_year'].tolist() if 'release_year' in suggestions else default_subtitles
    posters = [get_movie_poster(imdb_id) if pd.notna(imdb_id) else "/assets/owl.png" for imdb_id in suggestions['imdb_id'].tolist()] if 'imdb_id' in suggestions else default_posters
    infos = [f"https://www.imdb.com/title/{imdb_id}/" if pd.notna(imdb_id) else "N/A" for imdb_id in suggestions['imdb_id'].tolist()] if 'imdb_id' in suggestions else default_infos
    trailers = [f"https://www.youtube.com/results?search_query={title.replace(' ', '+')}+trailer" if title != "N/A" else "N/A" for title in titles]

    def pad(lst, fill, n=num_suggestions):
        return lst + [fill] * (n - len(lst))

    titles = pad(titles, "N/A")
    subtitles = pad(subtitles, "N/A")
    posters = pad(posters, "/assets/owl.png")
    infos = pad(infos, "N/A")
    trailers = pad(trailers, "N/A")

    return titles + titles + subtitles + posters + infos + trailers

clientside_callback(
    """
    (switchOn) => {
       document.documentElement.setAttribute("data-bs-theme", switchOn ? "light" : "dark");
       return window.dash_clientside.no_update
    }
    """,
    Output("switch", "id"),
    Input("switch", "value"),
)

@app.callback(
    Output("navbar", "color"),  
    Output("navbar", "dark"),  
    Input("switch", "value")  
)
def update_navbar_color(color_mode):
    if color_mode == False: 
        return "dark", True
    else:
        return "light", False
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
