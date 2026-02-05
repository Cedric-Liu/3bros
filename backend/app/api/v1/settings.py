"""
设置API路由
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks

from ...deps import get_db
from ...core.notifier import WeChatNotifier
from ...schemas.settings import (
    SettingsResponse,
    UpdateSettingsRequest,
    TestNotifyResponse,
    AllSettingsResponse
)

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """获取设置"""
    db = get_db()
    serverchan_key = db.get_setting("serverchan_key", "")
    push_time = db.get_setting("push_time", "15:30")

    # 脱敏处理
    masked_key = None
    if serverchan_key:
        if len(serverchan_key) > 8:
            masked_key = serverchan_key[:4] + "****" + serverchan_key[-4:]
        else:
            masked_key = "****"

    return SettingsResponse(
        serverchan_key=masked_key,
        serverchan_configured=bool(serverchan_key),
        push_time=push_time
    )


@router.put("")
async def update_settings(request: UpdateSettingsRequest):
    """更新设置"""
    db = get_db()

    if request.serverchan_key is not None:
        db.set_setting("serverchan_key", request.serverchan_key)

    if request.push_time is not None:
        db.set_setting("push_time", request.push_time)
        # 同步更新调度器
        try:
            from ...core.scheduler import update_push_time
            update_push_time(request.push_time)
        except Exception as e:
            print(f"更新调度器失败: {e}")

    return {"success": True, "message": "设置已更新"}


@router.post("/notify/test", response_model=TestNotifyResponse)
async def test_notify():
    """测试推送"""
    db = get_db()
    notifier = WeChatNotifier(db=db)

    if not notifier.is_configured():
        return TestNotifyResponse(
            success=False,
            message="Server酱未配置，请先设置SendKey"
        )

    success = notifier.send_test_message()

    if success:
        return TestNotifyResponse(
            success=True,
            message="测试消息已发送，请检查微信"
        )
    else:
        return TestNotifyResponse(
            success=False,
            message="发送失败，请检查SendKey是否正确"
        )


@router.get("/all", response_model=AllSettingsResponse)
async def get_all_settings():
    """获取所有设置（调试用）"""
    db = get_db()
    settings = db.get_all_settings()

    # 脱敏敏感信息
    if "serverchan_key" in settings:
        key = settings["serverchan_key"]
        if len(key) > 8:
            settings["serverchan_key"] = key[:4] + "****" + key[-4:]
        else:
            settings["serverchan_key"] = "****"

    return AllSettingsResponse(settings=settings)


@router.post("/notify/daily")
async def trigger_daily_push(background_tasks: BackgroundTasks):
    """手动触发每日推送（测试用）"""
    db = get_db()
    notifier = WeChatNotifier(db=db)

    if not notifier.is_configured():
        return {"success": False, "message": "Server酱未配置"}

    try:
        from ...core.scheduler import daily_push_job_sync
        background_tasks.add_task(daily_push_job_sync)
        return {"success": True, "message": "每日推送已触发，请稍候查看微信"}
    except Exception as e:
        return {"success": False, "message": f"触发失败: {e}"}
