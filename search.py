#########################################
##### Name:     puhua jiang         #####
##### Uniqname:        puhua        #####
#########################################


import json
import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import plotly.graph_objs as go
from flask import Flask, render_template, request

CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}



def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILE_NAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 
 


def make_request_with_cache(url, cache):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    hashtag: string
        The hashtag to search(i.e. "#2020election")
    count: int
        The number of tweets to retrieve
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    #TODO Implement function
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]



def get_search_results(baseurl, search_term):
    search_url = baseurl + search_term + '&category1=998'
    response_text = make_request_with_cache(search_url, CACHE_DICT)
    soup = BeautifulSoup(response_text, 'html.parser')
    search_results = soup.find(id='search_resultsRows')
    search_lists = search_results.find_all('a')
    results = []
    
    for game_info in search_lists:
        game_dict = {}
        if 'data-ds-appid' not in game_info.attrs.keys():
            continue
        else:
            game_dict['game_id'] = game_info.attrs['data-ds-appid']

        title = game_info.find('span', class_='title').text
        game_dict['title'] = title if title is not None else 'None'

        release_date = game_info.find('div', class_='search_released').text
        game_dict['release_date'] = release_date if release_date is not None and len(release_date) > 0 else 'None'

        reviewscore = game_info.find('div', class_='search_reviewscore').find('span')
        if reviewscore is not None:
            score = reviewscore.attrs['data-tooltip-html'].split('<br>')
            game_dict['review'] = score[0]
            game_dict['score_rate'] = score[1][0:2]
        else:
            game_dict['review'] = 'None'
            game_dict['score_rate'] = 'None'
        
        price = game_info.find('div', class_ ='search_price').text.strip()
        if price is None or len(price) == 0:
            game_dict['price'] = 'None'
        else:
            if price == "Free" or price == "Free To Play" or price == "Free to Play":
                game_dict['price'] = '0'
            else:
                game_dict['price'] = price.split('$')[-1]
        results.append(game_dict)  
    return results

def get_detail_results(game_dicts):
    results =[]
    url = 'https://store.steampowered.com/app/'
    game_num_url = 'https://steamcommunity.com/app/'
    for game_info in game_dicts:
        detail_dict = {}
        detail_dict['id'] = game_info['game_id']
        detail_dict['title'] = game_info['title']
        detail_dict['url'] = url + game_info['game_id']
        response_text = make_request_with_cache(detail_dict['url'], CACHE_DICT)
        soup = BeautifulSoup(response_text, 'html.parser')
        description = soup.find('div', class_='game_description_snippet').text.strip()
        detail_dict['description'] = description
        image_url = soup.find('img', class_='game_header_image_full')['src']
        detail_dict['image_url'] = image_url
        developer = soup.find('div', id="developers_list")
        if developer == None:
            detail_dict['developer'] = "None"
        else:
            developer=developer.find('a').text.strip()
            detail_dict['developer'] = developer
        results.append(detail_dict)
    return results


        
DB_NAME = 'games.sqlite'
def creat_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_games_sql = 'DROP TABLE IF EXISTS "Games"'
    drop_details_sql = 'DROP TABLE IF EXISTS "Details"'
    
    create_games_sql = '''
        CREATE TABLE IF NOT EXISTS "Games" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT, 
            "TITLE" TEXT NOT NULL,
            "RELEASE_DATE" TEXT NOT NULL, 
            "REVIEW" TEXT NOT NULL,
            "SCORE_RATE" INTEGER NOT NULL,
            "PRICE" REAL NOT NULL
        )
    '''

    create_details_sql = '''
        CREATE TABLE IF NOT EXISTS "Details" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT, 
            "TITLE" TEXT ,
            "URL" TEXT NOT NULL, 
            "DESCRIPTION" TEXT NOT NULL,
            "IMAGE_URL" TEXT NOT NULL,
            "DEVELOPER" TEXT NOT NULL,
            FOREIGN KEY(TITLE) REFERENCES Games(TITLE)
        )
    '''
    cur.execute(drop_details_sql)
    cur.execute(drop_games_sql)
    cur.execute(create_games_sql)
    cur.execute(create_details_sql)
    conn.commit()
    conn.close()

def load_games(game_dict):

    insert_games_sql = '''
        INSERT INTO Games
        VALUES (?,?,?,?,?,?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for game in game_dict:
        cur.execute(insert_games_sql,[
            game['game_id'],
            game['title'],
            game['release_date'],
            game['review'],
            game['score_rate'],
            game['price']
        ])
    conn.commit()
    conn.close()

def load_details(detail_dict):

    insert_details_sql = '''
        INSERT INTO Details
        VALUES (?,?,?,?,?,?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for detail in detail_dict:
        cur.execute(insert_details_sql,[
            detail['id'],
            detail['title'],
            detail['url'],
            detail['description'],
            detail['image_url'],
            detail['developer'],

        ])
    conn.commit()
    conn.close()


def Execute_Query(Query):
    '''Connect the Database
        
    Parameters
    ----------
    None
    
    Returns
    -------
    list
        a list of tuples that represent the query result
        
    '''
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    query = Query
    result = cursor.execute(query).fetchall()
    connection.close()
    return result

def get_db_results(method):
    if method == '1':
        query = '''
        SELECT * FROM Games
        LIMIT 10 
        '''
    elif method == '2':
        query = '''
        SELECT * FROM Games
        WHERE PRICE <> 'None'
        ORDER BY PRICE ASC 
        LIMIT 10 
        '''
    elif method == '3':
        query = '''
        SELECT * FROM Games
        WHERE SCORE_RATE <> 'None'
        ORDER BY SCORE_RATE DESC 
        LIMIT 10 
        '''   
    else:
        print("ERROR PLEASE INPUT VALID NUMBER")
    results = Execute_Query(query)
    return results


def get_details(ID):
    query = '''
        SELECT * FROM Details
        WHERE Id = {}
        '''.format(ID)
    results = Execute_Query(query)
    return results
    

def print_query_result(raw_query_result):
    ''' Pretty prints raw query result
    
    Parameters
    ----------
    list 
        a list of tuples that represent raw query result
    
    Returns
    -------
    None
    '''
    if raw_query_result is not None and len(raw_query_result) > 0:
        num = 0
        for Tuple in raw_query_result:
            lists = list(map(str, Tuple))
            output = str(num) + "|"
            for string in lists:
                if len(string) >= 12:
                    string = string[0:15] + "..."
                output += string.center(18) + "|"
            print(output)
            num += 1
    else:
        print("NO DATA, Command not recognized!")

def plot_query_result(raw_query_result):
    '''plot query result
        
    Parameters
    ----------
    list
        raw query data
    str
        command
    
    Returns
    -------
    none
        
    '''
    x_axis = []
    y_axis1 = []
    y_axis2 = []
    for line in raw_query_result:
        x_axis.append(line[1])
        y_axis1.append(line[4])
        y_axis2.append(line[5])
    bar_data = [
    go.Bar(name='score_rate', x=x_axis, y=y_axis1, text=y_axis1, textposition='auto'),
    go.Bar(name='price', x=x_axis, y=y_axis2, text=y_axis2, textposition='auto')
    ]
    basic_layout = go.Layout(title="RESULT")
    fig = go.Figure(data=bar_data, layout=basic_layout)
    div = fig.to_html(full_html=False)
    return div
    

    
    









app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') # just the static HTML

@app.route('/handle_form', methods=['POST'])
def handle_the_form():
    name = request.form["name"]
    load_database(name)
    order = request.form["order"]
    results = get_db_results(order)
    way = request.form["way"]
    if way == '2':
        div = plot_query_result(results)
        return render_template('plot.html', plot_div=div, results=results)
    elif way == '3':
        url = 'https://store.steampowered.com/app/'
        return render_template('results.html', results=results, base_url=url)

@app.route('/detail_form', methods=['POST'])
def show_detail_form():
    num = request.form["num"]
    results = get_details(int(num))
    return render_template('detail.html', 
        game=results[0])



def load_database(name):
    baseurl = "https://store.steampowered.com/search/?term="
    game_dict = get_search_results(baseurl, name)
    details_dict = get_detail_results(game_dict)
    creat_db()
    load_games(game_dict)
    load_details(details_dict)



if __name__ == "__main__":
    CACHE_DICT = open_cache()
    app.run(debug=True)
    


    
