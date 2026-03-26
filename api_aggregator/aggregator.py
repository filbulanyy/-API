import time
from datetime import datetime
from typing import Any, Dict, List
from models import AggregatedReport, FetchResult

def extract_value(data: Any, path: str) -> Any:

    if path == "$":
        return data
    
    parts = path.split('.')
    current = data
    
    for part in parts:
        if current is None:
            return None
        
        if part.isdigit():
            if isinstance(current, list) and int(part) < len(current):
                current = current[int(part)]
            else:
                return None
        else:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
    
    return current


def apply_mapping(data: Any, mapping: Dict[str, str]) -> Dict[str, Any]:
    result = {}
    for report_key, json_path in mapping.items():
        result[report_key] = extract_value(data, json_path)
    return result


def aggregate(
    results: List[FetchResult],
    response_mappings: Dict[str, Dict[str, str]]  
) -> AggregatedReport:

    total_sources = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total_sources - successful
    
    total_time_ms = max((r.elapsed_ms for r in results), default=0)
    
    processed_results = []
    for result in results:
        if result.success and result.data is not None:
            mapping = response_mappings.get(result.source_name, {})
            if mapping:
                mapped_data = apply_mapping(result.data, mapping)
            else:
                mapped_data = result.data
            
            processed_results.append(
                FetchResult(
                    source_name=result.source_name,
                    success=result.success,
                    data=mapped_data,
                    status_code=result.status_code,
                    elapsed_ms=result.elapsed_ms,
                    error=result.error,
                    retries_used=result.retries_used
                )
            )
        else:
            processed_results.append(result)
    
    return AggregatedReport(
        timestamp=datetime.now(),
        total_sources=total_sources,
        successful=successful,
        failed=failed,
        total_time_ms=total_time_ms,
        results=processed_results
    )