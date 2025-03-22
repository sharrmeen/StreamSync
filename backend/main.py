from fastapi import FastAPI

app = FastAPI(title="InfluenceIQ API", description="AI-powered influencer ranking system")

@app.get("/")
def home():
    return {"message": "Welcome to InfluenceIQ API"}
