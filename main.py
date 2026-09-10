from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import duckdb
from huggingface_hub import HfFileSystem

app = FastAPI()

# ---- DuckDB with public Hugging Face access ----
con = duckdb.connect()
hf_fs = HfFileSystem(token=False)
con.register_filesystem(hf_fs)

# ---- Public file URL ----
FILE_URL = "hf://buckets/zxzengzo/truecaller/*.parquet"

# ---- Error handler ----
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "status": "rejected",
                "message": "Invalid endpoint. Use /?number=XXXXXXXXXX",
                "Developer": "@Hye_Genzo"
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail, "Developer": "@Hye_Genzo"}
    )

# ---- Single endpoint ----
@app.get("/")
async def fetch_data(number: str = Query(None)):
    # Validate input
    if not number or not number.isdigit() or len(number) < 10 or len(number) > 15:
        return JSONResponse(
            status_code=400,
            content={
                "status": "rejected",
                "message": "Invalid parameter. Use /?number=XXXXXXXXXX",
                "Developer": "@Hye_Genzo"
            }
        )

    try:
        # Query the remote Parquet file directly (no caching)
        query = f"""
        SELECT * FROM read_parquet('{FILE_URL}')
        WHERE "mobile" = '{number}'
        """
        result = con.execute(query)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        records = [dict(zip(columns, row)) for row in rows]

        if not records:
            return JSONResponse(
                status_code=404,
                content={"status": "not_found", "phone": number, "Developer": "@Hye_Genzo"}
            )

        return {
            "status": "success",
            "Data": records,
            "Developer": "@Hye_Genzo"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Database error: {str(e)}",
                "Developer": "@Hye_Genzo"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
