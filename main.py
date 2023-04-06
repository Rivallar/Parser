from fastapi import FastAPI
from fastapi_pagination import add_pagination
import uvicorn


from routes.lamoda_routes import lamoda_router

app = FastAPI()

app.include_router(lamoda_router)
add_pagination(app)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)