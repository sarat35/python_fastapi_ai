import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",  
        host="localhost",
        port=7000,  
        reload=True
    )