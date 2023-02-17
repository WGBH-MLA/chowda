from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def root():
    return {'CLAMS': 'Chowda!'}
