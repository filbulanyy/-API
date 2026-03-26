import json
from typing import Dict, Any

from models import AggregatedReport

def generate_text_report(report: AggregatedReport) -> str:
    lines = []
    
    lines.append("== API Aggregator Report ==")
    
    lines.append(f"Timestamp: {report.timestamp.isoformat()}")
    lines.append(f"Sources: {report.total_sources} total, {report.successful} successful, {report.failed} failed")
    lines.append(f"Total time: {report.total_time_ms:.1f} ms")
    lines.append("")
    
    for result in report.results:
        if result.success:
            lines.append(f"--- {result.source_name} (OK, {result.elapsed_ms:.0f} ms) ---")
            if result.data:
                lines.append(f"  {json.dumps(result.data, ensure_ascii=False)}")
        else:
            lines.append(f"--- {result.source_name} (FAILED, {result.elapsed_ms:.0f} ms, retries: {result.retries_used}) ---")
            if result.error:
                lines.append(f"  error: {result.error}")
        lines.append("")
    
    return "\n".join(lines).rstrip()

def generate_json_report(report: AggregatedReport) -> Dict[str, Any]:
 
    return report.model_dump(mode="json")


def save_report(report: AggregatedReport, file_path: str, as_json: bool = False) -> None:
 
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            if as_json:
                json.dump(generate_json_report(report), f, indent=2, ensure_ascii=False)
            else:
                f.write(generate_text_report(report))
    except Exception as e:
        raise IOError(f"Ошибка записи отчёта в файл {file_path}: {e}")