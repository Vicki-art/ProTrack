import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    client = request.client.host if request.client else "unknown"

    response = await call_next(request)

    process_time = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"Request | {request.method} {request.url.path} | "
        f"status={response.status_code} | "
        f"time={process_time}ms | client={client}"
    )

    return response