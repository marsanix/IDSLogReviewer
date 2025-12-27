import json
import os
import time
from datetime import datetime

class LogParser:
    def __init__(self, log_file):
        self.log_file = log_file

    def read_logs(self, limit=100):
        """Reads the last N logs from the file."""
        logs = []
        if not os.path.exists(self.log_file):
            return logs

        try:
            with open(self.log_file, 'r') as f:
                # This is a simple implementation. For huge files, we should seek from end.
                # But for a demo/personal host IDS, reading lines is okay for now.
                lines = f.readlines()
                for line in reversed(lines):
                    try:
                        log_entry = json.loads(line)
                        if log_entry.get('event_type') == 'alert':
                            # Simplify timestamp for UI
                            ts = log_entry.get('timestamp', '')
                            try:
                                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                log_entry['display_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                log_entry['display_time'] = ts
                            logs.append(log_entry)
                            if len(logs) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading logs: {e}")
        
        return logs

    def get_stats(self):
        """Calculate basic stats from all logs (expensive for large files, optimize later)."""
        stats = {
            'total_alerts': 0,
            'severity_high': 0,
            'severity_medium': 0,
            'severity_low': 0,
            'top_signatures': {}
        }
        
        if not os.path.exists(self.log_file):
            return stats

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get('event_type') == 'alert':
                            stats['total_alerts'] += 1
                            alert = entry.get('alert', {})
                            severity = alert.get('severity', 3)
                            
                            if severity == 1:
                                stats['severity_high'] += 1
                            elif severity == 2:
                                stats['severity_medium'] += 1
                            else:
                                stats['severity_low'] += 1
                                
                            sig = alert.get('signature', 'Unknown')
                            stats['top_signatures'][sig] = stats['top_signatures'].get(sig, 0) + 1
                    except:
                        continue
        except Exception as e:
            print(f"Error getting stats: {e}")
            
        # Sort top signatures
        stats['top_signatures'] = dict(sorted(stats['top_signatures'].items(), key=lambda item: item[1], reverse=True)[:5])
        return stats
