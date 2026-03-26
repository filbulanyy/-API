import json
import argparse
import asyncio
import sys
from datetime import datetime

from config import load_config
from fetcher import fetch_all
from aggregator import aggregate
from report import generate_text_report, generate_json_report, save_report


def parse_args():
    parser = argparse.ArgumentParser(
        description="API Aggregator - асинхронный сбор данных из API"
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        metavar='FILE',
        help='Путь к файлу конфигурации'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        metavar='SECONDS',
        help='Таймаут на один запрос в секундах'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        metavar='N',
        help='Максимальное количество одновременных запросов)'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        metavar='N',
        help='Количество повторных попыток при ошибке'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        metavar='FILE',
        help='Путь для сохранения отчёта'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        default=False,
        help='Формировать отчёт в формате JSON'
    )
    
    parser.add_argument(
        '--serve',
        action='store_true',
        default=False,       
        help='Запустить FastAPI-сервер с результатами'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        metavar='PORT',
        help='Порт для FastAPI-сервера'
    )
    
    return parser.parse_args()


async def run_report_mode(args):
    sources = load_config(args.config)
    
    results = await fetch_all(
        sources=sources,
        timeout=args.timeout,
        max_concurrent=args.max_concurrent,
        retries=args.retries
    )
    
    mappings = {s.name: s.response_mapping for s in sources}
    report = aggregate(results, mappings)
    
    if args.json:
        if args.output:
            save_report(report, args.output, as_json=True)
        else:
            print(json.dumps(generate_json_report(report), indent=2, ensure_ascii=False))
    else:
        if args.output:
            save_report(report, args.output, as_json=False)
        else:
            print(generate_text_report(report))


def run_serve_mode(args):
    from server import run_server
    run_server(
        config_path=args.config,
        port=args.port,
        timeout=args.timeout,
        max_concurrent=args.max_concurrent,
        retries=args.retries
    )


def main():
    args = parse_args()
    
    if args.serve:
        run_serve_mode(args)
    else:
        asyncio.run(run_report_mode(args))


if __name__ == "__main__":
    main()