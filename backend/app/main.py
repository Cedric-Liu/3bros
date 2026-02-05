"""
反转三兄弟 - FastAPI 后端入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings, get_database_path
from .db.models import Database
from .deps import set_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化数据库
    db_path = get_database_path()
    db = Database(db_path)
    set_db(db)
    print(f"Database initialized: {db_path}")

    # 启动定时推送调度器
    from .core.scheduler import start_scheduler, stop_scheduler
    start_scheduler()

    yield

    # 停止调度器
    stop_scheduler()
    print("App shutdown")


# 创建FastAPI应用
app_settings = get_settings()
app = FastAPI(
    title=app_settings.app_name,
    version=app_settings.app_version,
    description="反转三兄弟股票分析系统API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 (lazy import to avoid circular)
from .api.v1 import stocks, etfs, market, settings as settings_api  # noqa: E402

app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["stocks"])
app.include_router(etfs.router, prefix="/api/v1/etfs", tags=["etf"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(settings_api.router, prefix="/api/v1/settings", tags=["settings"])


@app.get("/")
async def root():
    return {
        "name": app_settings.app_name,
        "version": app_settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
