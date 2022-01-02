#Graphe
import networkx as nx
import plotly.offline as py
import plotly.graph_objects as go

#Récupération Arxiv et twitter
from datetime import datetime
import urllib, xmltodict
from classes import TwitterDoc, ArxivDoc, Corpus
import pandas as pd
import tweepy

#App
import dash
from dash import dcc
from dash import html
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc



def get_data(word, nb_points, source):
    
    '''Récupère les données relatives au mot 
        Parameters
        ----------
        x    : a tuple of the endpoints' x-coordinates in the form, tuple([x0, x1, None])
        y    : a tuple of the endpoints' y-coordinates in the form, tuple([y0, y1, None])
        width: the width of the line
        Returns
        -------
        An edge trace that goes between x0 and x1 with specified width.
        '''
        
        
    if (source=="arxiv"):
        # ================== Extraction des documents ==================== #
        arxivCorpus = Corpus("ArXiv")
        #recup data de Arxiv
        query_term = word
        
        # Requête
        url='http://export.arxiv.org/api/query?search_query=all:'+query_term+'&start=0&max_results=10'
        data = urllib.request.urlopen(url)
        data = xmltodict.parse(data.read().decode('utf-8')) 
        
        # ================ Création du corpus ======================== #
        for section in data["feed"]["entry"]:
            time_str = section["published"]
            time = datetime.strptime(time_str, '%Y-%m-%dT%XZ')
            if(isinstance(section["author"], list)):
                author = section["author"][0]["name"]
            else:
                author = section["author"]["name"]
                
            #Ajout du document formaté au corpus
            arxivCorpus.add(ArxivDoc(section["summary"].replace("\n", ""), time, author, section["title"]))   
    
        motsFreq = arxivCorpus.motsFrequents(nb_points)
        
    elif (source=="twitter"):
        twitterCorpus = Corpus("Twitter")
        
        # ================ Récupération des tweets récents via l'API ================ #
        client = tweepy.Client(bearer_token='AAAAAAAAAAAAAAAAAAAAAOOVXgEAAAAA2DJBmFtV5IcuFRsw6rWa0rbeBg8%3DPScLyXvrrvStd84C0F8q44D4LF1SDeoVyOd6NjUVSKeAY07INL')
        query = word+' -is:retweet lang:en'
        tweets = client.search_recent_tweets(query=query, tweet_fields=['created_at','author_id','id'], max_results=100)
        
        # ================ Ajout des tweets au corpus ===================== #
        for tweet in tweets.data:
            time=tweet.created_at.strftime('%Y-%m-%d')

            
            #Ajout du document formaté au corpus
            twitterCorpus.add(TwitterDoc(tweet.text.replace("\n", ""), time, tweet.author_id, tweet.id))  
            
        motsFreq = twitterCorpus.motsFrequents(nb_points)
        
    motsFreq.to_excel("motsFrequents.xlsx")
    return (motsFreq)

def create_graph(word, points,source):
    motsFrequents=get_data(word,points,source)
    
    #Création du graphe
    graph = nx.Graph()
    
    #Liste des mots du graphe
    wordsList = []
    
    #On crée une node par mot et on ajoute chaque mot à la liste
    for index, row in motsFrequents.iterrows():
         wordsList.append(row['mot'])
         graph.add_node(row["mot"], size = row["freq"])
      
    #Création du dataframe servant à stocker les co-occurences de chaque mot
    coOccurence = pd.DataFrame(0, index=wordsList, columns=wordsList)
    
    #On parcourt le tableau deux fois pour récupérer les co-occurences de chaque mot
    for index, rowi in motsFrequents.iterrows(): 
        for index, rowj in motsFrequents.iterrows():
            mot1 = rowi['mot']
            mot2 = rowj['mot']
            count=0
            if (mot1 != mot2) and (coOccurence[mot1][mot2] == 0):
                for key in rowj['docs']:
                    if key in rowi['docs']:
                        count += min(rowi['docs'][key], rowj['docs'][key])
            coOccurence[mot2][mot1] = count
    
    #On trace les liens entre les points du graphe suivant la co-occurence des mots
    for indexi, rowi in coOccurence.iterrows():
        for indexj, rowj in coOccurence.iterrows():
            if coOccurence[indexj][indexi] != 0 :
                graph.add_edge(indexj, indexi, weight = coOccurence[indexj][indexi])
            
    
    #On place les différents points selon une forme, ici le spring_layout
    pos_ = nx.spring_layout(graph)
    
    def make_edge(x, y, text, width):
        
        '''Creates a scatter trace for the edge between x's and y's with given width
        Parameters
        ----------
        x    : a tuple of the endpoints' x-coordinates in the form, tuple([x0, x1, None])
        y    : a tuple of the endpoints' y-coordinates in the form, tuple([y0, y1, None])
        width: the width of the line
        Returns
        -------
        An edge trace that goes between x0 and x1 with specified width.
        '''
        return  go.Scatter(x         = x,
                           y         = y,
                           line      = dict(width = width,
                                       color = 'RGBA(168,184,229,0.8)'),
                           hoverinfo = 'text',
                           text      = ([text]),
                           mode      = 'lines')
    
    # For each edge, make an edge_trace, append to list
    edge_trace = []
    for edge in graph.edges():
        if graph.edges()[edge]['weight'] > 0:
            mot_1 = edge[0]
            mot_2 = edge[1]
    
            x0, y0 = pos_[mot_1]
            x1, y1 = pos_[mot_2]
    
            text   = mot_1 + '--' + mot_2 + ': ' + str(graph.edges()[edge]['weight'])
            
            trace  = make_edge([x0, x1, None], [y0, y1, None], text,
                               0.3*graph.edges()[edge]['weight']**1.75)
    
            edge_trace.append(trace)
    
    # Make a node trace
    node_trace = go.Scatter(x         = [],
                            y         = [],
                            text      = [],
                            textposition = "top center",
                            textfont_size = 10,
                            mode      = 'markers+text',
                            hoverinfo = 'none',
                            marker    = dict(color = [],
                                             size  = [],
                                             line  = None))
    
    
    #On détermine la taille min et max des points pour ajuster leur taille finale
    minSize=10000
    maxSize=0
    
    for node in graph.nodes():
        if graph.nodes()[node]['size'] < minSize:
            minSize=graph.nodes()[node]['size']
            
        if graph.nodes()[node]['size'] > maxSize:
            maxSize=graph.nodes()[node]['size']
    
    middle=(maxSize+minSize)/2
    quartile3=middle+(middle/2)
    
            
    #On prend chaque point du graphe et on ajoute sa position et sa taille à node_trace        
    for node in graph.nodes():
        x, y = pos_[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['marker']['color'] += tuple(['cornflowerblue'])
        #On n'applique pas de multiplicateur de tailles aux plus grands points
        if (graph.nodes()[node]['size'] > quartile3):
            node_trace['marker']['size'] += tuple([graph.nodes()[node]['size']])
        else :
            node_trace['marker']['size'] += tuple([3*graph.nodes()[node]['size']])
        node_trace['text'] += tuple(['<b>' + node + '</b>'])     
        
    return([edge_trace, node_trace])


# ================= Création de l'application graphique ====================== #
app= dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H2(id="titre", style={'text-align':"center"},children=["Graphe des termes liés à : "]),
    
    html.Div(
    [
        html.Div(
        [
            dbc.Label("Recherche", html_for="type_word"),
            dbc.Input(id="type_word", autoFocus=True, value="covid", placeholder="Recherchez un mot"),
        ],
            className="flex-grow-2"
        ),
        
        html.Div(
        [
            dbc.Label("Nombre de points", html_for="nb_points"),
            dbc.Input(id="nb_points", type='number', min=5, max=30, value="10"),
        ],
            className="flex-grow-2"
        ),
        
        html.Div(
        [
            dbc.Label("Source des données", html_for="source"),
            dcc.Dropdown(
            id="source",
            options=[
                {"label": "ArXiv", "value": "arxiv"},
                {"label": "Twitter", "value": "twitter"},
            ],
            value="arxiv"
            ),
        ],
            className="flex-grow-2",
        ),
        
        dbc.Button('Valider',id="okay",color="primary", className="mt-4 ms-auto"),
        
    ],className="d-grid gap-4 d-md-flex justify-content-lg-start align-items-sm-start",
    ),

    
    dcc.Graph(id="my_graph",figure={},style={"height":"90vh"})
    ],
    className="mx-5"
    )

@app.callback(
     Output(component_id="my_graph", component_property="figure"),
     Input(component_id="okay", component_property="n_clicks"),
    [State(component_id="type_word", component_property="value"),
     State('nb_points','value'),
     State('source','value')]
)
def update_graph(n_clicks, mot, nb_points, source):
    
    #Tracage du graphe
    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    graph_trace=create_graph(mot, int(nb_points),source)
    
    fig = go.Figure(layout = layout)
    
    for trace in graph_trace[0]:
        fig.add_trace(trace)
    
    fig.add_trace(graph_trace[1])
    
    fig.update_layout(showlegend = False)
    fig.update_xaxes(showticklabels = False)
    fig.update_yaxes(showticklabels = False)
    
    #On sauvegarde la figure au format html
    py.plot(fig, filename='word_network.html')
    
    return fig

@app.callback(
    Output('titre','children'),
    Input('okay','n_clicks'),
    State('type_word','value')    
)
def update_title(n_clicks, value):
    return "Graphe des termes liés à : {}".format(value)

# --------------------------
if __name__ == '__main__':
    app.run_server(debug=False, dev_tools_hot_reload=False)
