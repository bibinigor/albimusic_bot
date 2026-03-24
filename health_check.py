#!/usr/bin/env python3
"""
Health check script for AlBi-music Bot
Checks all critical components and sends summary
"""

import sys
import logging
import psutil
import time
from datetime import datetime
import redis
import subprocess
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_bot_process():
    """Check if bot process is running"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and 'main_with_payments.py' in ' '.join(proc.info['cmdline']):
                return {
                    'status': 'running',
                    'pid': proc.info['pid'],
                    'memory_mb': round(proc.memory_info().rss / 1024 / 1024, 1)
                }
        return {'status': 'stopped', 'error': 'Process not found'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_celery_workers():
    """Check if celery workers are running"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'celery.*worker'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return {
                'status': 'running',
                'worker_count': len(pids),
                'pids': pids
            }
        return {'status': 'stopped', 'error': 'No workers found'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_redis():
    """Check Redis connection"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
        r.ping()
        info = r.info()
        return {
            'status': 'running',
            'used_memory_mb': round(info['used_memory'] / 1024 / 1024, 1),
            'connected_clients': info['connected_clients']
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_postgresql():
    """Check PostgreSQL connection"""
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', 'albimusic_bot', '-c', 'SELECT 1'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return {'status': 'running'}
        return {'status': 'error', 'error': result.stderr[:100]}
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'Connection timeout'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_disk_space():
    """Check disk space on root partition"""
    try:
        disk = psutil.disk_usage('/')
        return {
            'status': 'ok' if disk.percent < 90 else 'warning',
            'total_gb': round(disk.total / 1024**3, 1),
            'used_gb': round(disk.used / 1024**3, 1),
            'free_gb': round(disk.free / 1024**3, 1),
            'percent': disk.percent
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_system_resources():
    """Check CPU and memory usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / 1024**3, 1),
            'status': 'ok' if cpu_percent < 90 and memory.percent < 90 else 'warning'
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_log_files():
    """Check if log files are being written"""
    log_files = [
        '/var/log/albimusic-bot/bot/bot.log',
        '/var/log/albimusic-bot/celery/celery.log'
    ]
    results = {}
    
    for log_file in log_files:
        try:
            if os.path.exists(log_file):
                size_kb = os.path.getsize(log_file) / 1024
                mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                age_minutes = (datetime.now() - mod_time).total_seconds() / 60
                
                results[log_file] = {
                    'exists': True,
                    'size_kb': round(size_kb, 1),
                    'age_minutes': round(age_minutes, 1),
                    'status': 'ok' if age_minutes < 60 else 'warning'
                }
            else:
                results[log_file] = {'exists': False, 'status': 'error'}
        except Exception as e:
            results[log_file] = {'exists': False, 'status': 'error', 'error': str(e)}
    
    return results

def generate_report():
    """Generate comprehensive health report"""
    timestamp = datetime.now().isoformat()
    
    report = {
        'timestamp': timestamp,
        'components': {
            'bot_process': check_bot_process(),
            'celery_workers': check_celery_workers(),
            'redis': check_redis(),
            'postgresql': check_postgresql(),
            'disk_space': check_disk_space(),
            'system_resources': check_system_resources(),
            'log_files': check_log_files()
        },
        'overall_status': 'healthy'
    }
    
    # Determine overall status
    for component_name, component_status in report['components'].items():
        if component_status.get('status') in ['error', 'stopped']:
            report['overall_status'] = 'unhealthy'
            break
        elif component_status.get('status') == 'warning':
            report['overall_status'] = 'degraded'
    
    return report

def print_report(report):
    """Print formatted report to console"""
    print("=" * 60)
    print("ALBI-MUSIC BOT - HEALTH CHECK REPORT")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Overall Status: {report['overall_status'].upper()}")
    print("-" * 60)
    
    for component, status in report['components'].items():
        print(f"\n🔍 {component.upper().replace('_', ' ')}:")
        
        if component == 'log_files':
            for log_file, log_status in status.items():
                print(f"   {log_file.split('/')[-1]}:")
                for key, value in log_status.items():
                    print(f"     {key}: {value}")
        else:
            for key, value in status.items():
                print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    
    # Generate recommendations based on status
    if report['overall_status'] == 'unhealthy':
        print("❌ CRITICAL: Some components are not working!")
        for component, status in report['components'].items():
            if status.get('status') in ['error', 'stopped']:
                print(f"   - {component} needs immediate attention")
    elif report['overall_status'] == 'degraded':
        print("⚠️  WARNING: System is running but with issues")
    else:
        print("✅ All systems operational")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        report = generate_report()
        print_report(report)
        
        # Return appropriate exit code
        if report['overall_status'] == 'unhealthy':
            sys.exit(1)
        elif report['overall_status'] == 'degraded':
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        sys.exit(1)
