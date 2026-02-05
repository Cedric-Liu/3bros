"""
设置相关的Pydantic模型
"""
from typing import Optional, Dict
from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    """设置响应"""
    serverchan_key: Optional[str] = Field(None, description="Server酱Key（已脱敏）")
    serverchan_configured: bool = Field(False, description="Server酱是否已配置")
    push_time: Optional[str] = Field("15:30", description="推送时间")


class UpdateSettingsRequest(BaseModel):
    """更新设置请求"""
    serverchan_key: Optional[str] = Field(None, description="Server酱Key")
    push_time: Optional[str] = Field(None, description="推送时间")


class TestNotifyRequest(BaseModel):
    """测试通知请求"""
    pass


class TestNotifyResponse(BaseModel):
    """测试通知响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")


class AllSettingsResponse(BaseModel):
    """所有设置响应"""
    settings: Dict[str, str]
