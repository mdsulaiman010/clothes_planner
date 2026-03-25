from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    from auth.routes import router as auth_router
    from wardrobe.routes import router as wardrobe_router
    from tryon.routes import router as tryon_router
    from chat.routes import router as chat_router

    app.include_router(auth_router, prefix='/api/auth', tags=['auth'])
    app.include_router(wardrobe_router, prefix='/api/wardrobe', tags=['wardrobe'])
    app.include_router(tryon_router, prefix='/api/tryon', tags=['tryon'])
    app.include_router(chat_router, prefix='/api/chat', tags=['chat'])

    return app


if __name__ == '__main__':
    import uvicorn
    app = create_app()
    uvicorn.run(app, host='0.0.0.0', port=5000)
