import concurrent.futures
import os
from typing import Annotated, List
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponseModel(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponseModel)
async def health():
    return HealthResponseModel(status="ok")


class LogsQueryParamsModel(BaseModel):
    count: int = Field(10, ge=1, le=20)


@router.get("/logs", response_model=List[str])
async def logs(query_params: Annotated[LogsQueryParamsModel, Query()]):
    count = query_params.count
    log_file_path = "app.log"
    if os.path.exists(log_file_path):
        logs: List[str] = []
        with open(log_file_path, "r", encoding='utf-8') as log_file:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(lambda x: logs.append(x), log_file.readlines()[-count:])

        return logs[::-1]
    else:
        raise Exception("Log file not found")
