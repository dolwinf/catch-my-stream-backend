from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, APIRouter
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
import yt_dlp as yt
import os
import re

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(docs_url=None, redoc_url=None)
router = APIRouter()

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)



def cleanup(path):
    if os.path.exists(path):
       os.remove(path)

@router.get("/health")
@limiter.limit("2/minute")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})

@router.post("/download/youtube")
@limiter.limit("2/minute")
async def download_video(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        url = body.get("url")
       
        vid_info = yt.YoutubeDL({"skip_download": True})
        vid_info_extract = vid_info.extract_info(url)
        
        title = vid_info_extract.get("title", "")
        video_id = vid_info_extract.get("id", "")

        clean_title = re.sub(r'[^A-Za-z0-9]+', '-', title)
        
        download_file_name = f"{clean_title}-{video_id}.mp4"
        vid = yt.YoutubeDL({ 'outtmpl': download_file_name, 'format': f'bestvideo[ext={"mp4"}]+bestaudio[ext=m4a]/best[ext={"mp4"}]',})
        vid.download(url)
        
        current_path = os.getcwd()
        full_path = os.path.join(current_path, download_file_name)
        
        background_tasks.add_task(cleanup, full_path)
        
        if os.path.exists(full_path):
            return FileResponse(full_path, filename=download_file_name)
        else:
            raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading video: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))