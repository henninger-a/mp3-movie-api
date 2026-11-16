This application uploads, retrieves, and processes data about movies. When the dataset is uploaded it is saved to the database, so it can then be queried using SQL, this is all done by the files in the src module. The data can then be processed using the files in the data pipeline module. Addisonally data can be retrieved, when this is done using GET /movies the result is cached so if the same result is needed again it doesn't have to be fetched twice. The cache is cleared when data is uploaded using POST /upload or altered using POST /movies/process so out of date information isn't returned. Along with the modules mentioned above there is also fixtures which contains sample data, and tests which contains test.

Also include:

the commands to start the API and run tests
one sample processing request and its expected result

Start API:
python -m uvicorn main:app --reload

Run Tests:
python -m pytest tests -v

Sample Processing Request:
    Input:
    GET /movies/search
    columns = title, rating
    min_rating = 7.5
    limit = 100

    Output:
    [{"id": 3, "title": "Movie C", "rating": 9},
    {"id": 2, "title": "Movie B", "rating": 8.5},
    {"id": 11, "title": "Movie K", "rating": 8.4},
    {"id": 9, "title": "Movie I", "rating": 8.3},
    {"id": 4, "title": "Movie D", "rating": 8.2},
    {"id": 16, "title": "Movie P", "rating": 8.2},
    {"id": 7, "title": "Movie G", "rating": 8.1},
    {"id": 1, "title": "Movie A", "rating": 8},
    {"id": 14, "title": "Movie N", "rating": 8},
    {"id": 12, "title": "Movie L", "rating": 7.9},
    {"id": 6, "title": "Movie F", "rating": 7.8},
    {"id": 10, "title": "Movie J", "rating": 7.7},
    {"id": 5, "title": "Movie E", "rating": 7.6},
    {"id": 15, "title": "Movie O", "rating": 7.6},
    {"id": 8, "title": "Movie H", "rating": 7.5}]

    Server Logs:
    20:27:20 DEBUG    src.storage — queried movies, columns: ['title', 'rating'] row count: 15
    20:27:20 INFO     main — columns: ['title', 'rating'], row count: 15
    20:27:20 INFO     src.middleware — request id:2b014f41 request method: GET url path: /movies/search status: 200 duration: 5.0848999817389995ms
    INFO:     127.0.0.1:52966 - "GET /movies/search?columns=title&columns=rating&min_rating=7.5&limit=100 HTTP/1.1" 200 OK

