import pytest

from src import MovieStorage
import main
import pandas as pd

def test_movies_persist(client, test_storage, uploaded_movies):
    movie_storage = MovieStorage(test_storage.db_path)
    movies = movie_storage.get()
    assert len(movies) == 20
    assert set(movies.columns.tolist()).issubset(["title", "release_year", "rating", "genre"])
    print(movies['title'])
    titles = ['Movie A', 'Movie B', 'Movie B', 'Movie C', 
              'Movie D', 'Movie D', 'Movie E', 'Movie F', 
              'Movie G', 'Movie H', 'Movie I', 'Movie J', 
              'Movie K', 'Movie L', 'Movie M', 'Movie N', ''
              'Movie O', 'Movie P', 'Movie Q', 'Movie R']
    assert movies['title'].tolist() == titles
    response = client.get("/movies", params={"limit":100})
    df = pd.DataFrame(response.json()['data'])
    print(movies)
    movies.index += 1
    assert movies.index.tolist() == df['id'].tolist()


def test_cache_and_processing(client, uploaded_movies, processing_body):
    response1 = client.get("/movies", params={"limit": 1})
    response100 = client.get("/movies", params={"limit": 100})
    assert response1.status_code == 200
    assert response100.status_code == 200
    assert response1.json() == main.cache.get(limit=1)
    assert response100.json() == main.cache.get(limit=100)

    response2100 = client.get("/movies", params={"limit": 100})
    assert response100.json() == response2100.json()

    response2 = client.post("/movies/process", json=processing_body)
    assert response2.status_code == 200
    assert response2.json()['validation_rows_removed'] == 0
    assert response2.json()['cleaning_report']['rows_before'] == 20
    assert response2.json()['cleaning_report']['rows_after'] == 16

    assert main.cache.get(limit=1) is None
    assert main.cache.get(limit=100) is None

    response3 = client.get("/movies", params={"limit": 100})
    assert response3.json()['total_rows'] == 16
    titles = ['Movie A', 'Movie B', 'Movie C', 'Movie D', 
              'Movie E', 'Movie F', 'Movie G', 'Movie H', 
              'Movie I', 'Movie J', 'Movie K', 'Movie L', 
              'Movie M', 'Movie N', 'Movie O', 'Movie P',]
    df = pd.DataFrame(response3.json()['data'])
    assert df['title'].tolist() == titles
    assert df['id'].tolist() == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    assert response3.json() == main.cache.get(limit=100)


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    response1 = client.get("/movies", params={"limit": 100})
    assert response1.status_code == 200

    monkeypatch.setattr(main.storage, "select_columns", lambda *args, **kwargs: pytest.fail("select_columns shouldn't have been called"))
    monkeypatch.setattr(main.storage, "count_movies", lambda *args, **kwargs: pytest.fail("count_movies shouldn't have been called"))
    
    response2 = client.get("/movies", params={"limit": 100})
    assert response2.status_code == 200
    assert response2.json() == response1.json()

