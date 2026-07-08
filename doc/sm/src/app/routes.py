from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/ping")
async def ping(request: Request) -> Response:
    if request.app.state.handler is None:
        return Response(status_code=503)
    return Response(status_code=200)


@router.post("/invocations", response_class=PlainTextResponse)
async def invocations(request: Request) -> PlainTextResponse:
    content_type = request.headers.get("content-type", "")
    handler = request.app.state.handler

    if "multipart/form-data" in content_type:
        form = await request.form()
        raw_images = [await f.read() for f in form.getlist("images")]
    elif "application/x-image" in content_type or "image/" in content_type:
        raw_images = [await request.body()]
    else:
        raise HTTPException(status_code=415, detail=f"Unsupported Content-Type: {content_type}")

    try:
        results = handler.run(raw_images)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PlainTextResponse(
        content=handler.serialize_jsonl(results),
        media_type="application/jsonlines",
    )
