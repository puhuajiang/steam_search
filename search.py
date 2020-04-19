#########################################
##### Name:     puhua jiang         #####
##### Uniqname:        puhua        #####
#########################################


import json
import requests
from bs4 import BeautifulSoup
import time
import sqlite3
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
#def show_game_lists(game_dict, number = 10):
DB_NAME = 'games.sqlite'
def creat_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_games_sql = 'DROP TABLE IF EXISTS "Games"'
    
    
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

    cur.execute(drop_games_sql)
    cur.execute(create_games_sql)
    conn.commit()
    conn.close()

def load_games(game_dict):
    creat_db()
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

if __name__ == "__main__":


    CACHE_DICT = open_cache()

    baseurl = "https://store.steampowered.com/search/?term="
    search_term = input("Plpease enter a game related word to search:")


    game_dict = get_search_results(baseurl, search_term)
    print(len(game_dict))
    load_games(game_dict)




    


    
