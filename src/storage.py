import logging
import sqlite3

import pandas as pd

from .database import get_connection, initialize_database

logger = logging.getLogger(__name__)
MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]


class MovieStorage:
    def __init__(self, db_path="data/movies.db"):
        self.db_path = db_path
        initialize_database(self.db_path)

    def save(self, df):
        """Replace all movie rows in one transaction."""
        connection = get_connection(self.db_path)
        try:
            sql_statement = "DELETE FROM movies"
            connection.execute(sql_statement)
            rows = [tuple(inner_list) for inner_list in df.values.tolist()]
            sql_statement = "INSERT INTO movies (title, release_year, rating, genre) VALUES (?, ?, ?, ?)"
            connection.executemany(sql_statement, rows)
            connection.commit()
            logger.debug(f"Saved rows: {len(df)}")
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(self):
        """Return the four movie columns as a DataFrame, ordered by id."""
        connection = get_connection(self.db_path)
        try:
            sql_statement = f"SELECT * FROM movies"
            rows = connection.execute(sql_statement,).fetchall()
            id_movie_columns = MOVIE_COLUMNS.insert(0, 'id')
            df = pd.DataFrame(rows, columns=id_movie_columns)
            connection.commit()
            return df
        finally:
            connection.close()

    def select_columns(self, columns, limit=5):
        """Return id plus the requested movie columns, ordered by id."""
        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")

        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")

        selected_columns = ", ".join(["id"] + columns)
        connection = get_connection(self.db_path)
        try:
            sql_statement = f"SELECT {selected_columns} FROM movies ORDER BY id LIMIT ?"
            rows = connection.execute(sql_statement, (limit,)).fetchall()
            logger.debug(f'{limit} rows returned from movies')
            connection.commit()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def count_movies(self):
        """Return the number of stored movies using SQL COUNT(*)."""
        connection = get_connection(self.db_path)
        try:
            sql_statement = "SELECT COUNT(*) AS total FROM movies"
            row = connection.execute(sql_statement).fetchone()
            connection.commit()
            return row["total"]
        finally:
            connection.close()

    def query_movies(self, columns, min_rating, limit):
        """Return selected fields from matching movies using SQL."""
        connection = get_connection(self.db_path)
        selected_columns = ", ".join(["id"] + columns)
        try:
            sql_statement = f"SELECT {selected_columns} FROM movies WHERE rating >= ? ORDER BY rating DESC, id ASC LIMIT ?"
            rows = connection.execute(sql_statement, (min_rating, limit)).fetchall()
            rows_dicts = [dict(row) for row in rows]
            logger.debug(f'queried movies, columns: {columns} row count: {len(rows_dicts)}')
            connection.commit()
            return rows_dicts
        finally:
            connection.close()
        
