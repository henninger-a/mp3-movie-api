import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, HealthResponse, setup_logging, ProcessConfig, ProcessingReport, log_requests
from data_pipeline import create_cleaning_report, process_data, validate_dataframe
from src import (
    MovieStorage,
    MovieUploadInfo,
    MovieDataResponse,
    MovieProcessingReport,
)
from src.storage import MOVIE_COLUMNS


setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = MovieStorage()
app.middleware("http")(log_requests)

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    if Path(file.filename or '').suffix.lower() != '.csv':
        logger.warning(f"Unsupported file format: {Path(file.filename).suffix}")
        raise HTTPException( status_code=400, detail="Invalid file extension")
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (pd.errors.EmptyDataError,pd.errors.ParserError,UnicodeDecodeError) as error:
        logger.warning(f"Cannot read CSV: {error}")
        raise HTTPException(status_code=400, detail="Cannot read the uploaded CSV")

    for col in df.columns.tolist():
        if col not in MOVIE_COLUMNS:
            raise HTTPException(status_code=400, detail="Does not contain required columns")
    if df.empty:
        raise HTTPException(status_code=400, detail="Dataframe is empty")
    if df.columns.tolist() != MOVIE_COLUMNS:
        df = df[MOVIE_COLUMNS]

    storage.save(df)
    logger.info(f'uploaded movies, filename: {file.filename} rows saved: {len(df)}')
    return MovieUploadInfo(filename=file.filename, rows=len(df), columns=df.shape[1], column_names=df.columns)
    

@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get()
    if df is None:
        return {"data": [], "total_rows": 0}
    records = storage.select_columns(MOVIE_COLUMNS, limit)
    num_movies = storage.count_movies()
    logger.info(f'rows count: {num_movies}')
    return MovieDataResponse(data=records, total_rows=num_movies)


@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1)
):

    try:
        returned_movies = storage.query_movies(columns, min_rating, limit)
        logger.info(f'columns: {columns}, row count: {len(returned_movies)}')
        return returned_movies
    except ValueError:
        raise HTTPException(status_code=400, detail='Value Error')


@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    result = storage.get()
    if result is None:
        raise HTTPException( status_code=400, detail="Data not found")
    
    config = config.model_dump()
    required_columns = config['validation']['required_columns']
    numeric_columns = config['validation']['numeric_columns']
    for col in numeric_columns:
        if col not in result.columns.to_list():
            raise HTTPException( status_code=400, detail="Column not found")
    try:
        df = validate_dataframe(result, required_columns, numeric_columns)
        rows_removed = len(result) - len(df)
        validated_df = df.copy()
        processed_df = process_data(validated_df, config)
    except ValueError:
        HTTPException(status_code=400, detail=str(ValueError))
    report = create_cleaning_report(validated_df, processed_df)
    logger.info(f'validation row(s) removed: {rows_removed} processing row(s) removed {len(validated_df) - len(processed_df)}')
    
    storage.save(validated_df)
    return {'validation rows removed': rows_removed, 'cleaning report': report}
