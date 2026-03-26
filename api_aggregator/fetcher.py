import aiohttp
import asyncio
import time
from typing import List
from models import FetchResult, SourceConfig


retry_statuses = {429, 500, 502, 503, 504}


def should_retry(exception: Exception, status_code: int = None) -> bool:
    
    if status_code in retry_statuses:
        return True
    
    if isinstance(exception, asyncio.TimeoutError):
        return True
    
    if isinstance(exception, aiohttp.ClientError):
        return True
    
    return False


async def fetch_source(
    session: aiohttp.ClientSession, 
    source: SourceConfig, 
    semaphore: asyncio.Semaphore, 
    timeout: int, 
    retries: int
) -> FetchResult:
    
    async with semaphore:  
        url = str(source.url)
        start_time = time.time()
        
        #мотивировано вылезшей ошибкой после запуска проекта
        params = {}
        for key, value in source.params.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()  
            else:
                params[key] = value
        
        for attempt in range(retries):
            try:
                async with session.request(
                    method=source.method,
                    url=url,
                    params=params,
                    headers=source.headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status in retry_statuses:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"{response.status}"
                        )
                    
                    data = await response.json()
                    #тоже мотивировано вылезшей ошибкой после запуска проекта
                    if isinstance(data, list):
                        data = {"results": data}
                        
                    elapsed_ms = (time.time() - start_time) * 1000
                    
                    return FetchResult(
                        source_name=source.name,
                        success=True,
                        status_code=response.status,
                        elapsed_ms=elapsed_ms,
                        data=data,
                        error=None,
                        retries_used=attempt
                    )
                    
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                
                status_code = None
                if isinstance(e, aiohttp.ClientResponseError):
                    status_code = e.status
                
                if not should_retry(e, status_code):
                    return FetchResult(
                        source_name=source.name,
                        success=False,
                        status_code=status_code,
                        elapsed_ms=elapsed_ms,
                        data=None,
                        error=str(e),
                        retries_used=attempt
                    )
                
                if attempt == retries - 1:
                    return FetchResult(
                        source_name=source.name,
                        success=False,
                        status_code=status_code,
                        elapsed_ms=elapsed_ms,
                        data=None,
                        error=str(e),
                        retries_used=attempt
                    )
                
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        


async def fetch_all(
    sources: List[SourceConfig],
    timeout: int = 10,
    max_concurrent: int = 5,
    retries: int = 3
) -> List[FetchResult]:
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_source(
                session=session,
                source=source,
                semaphore=semaphore,
                timeout=timeout,
                retries=retries
            )
            for source in sources
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)