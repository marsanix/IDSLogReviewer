import json
import os
from datetime import datetime
from app import app, db, LogEntry

LOG_FILE = os.environ.get('LOG_FILE', "logs/eve.json")

def import_logs():
    if not os.path.exists(LOG_FILE):
        print(f"Log file not found: {LOG_FILE}")
        return

    print(f"Importing logs from {LOG_FILE}...")
    
    count = 0
    skipped = 0
    
    with app.app_context():
        # Get all existing fingerprints to minimize DB queries
        # Fingerprint: (timestamp, src_ip, dest_ip, signature)
        # Note: This might be heavy if DB is huge, but for this scale it's fine.
        # Alternatively, check one by one. Let's check one by one for safety and simplicity code-wise.
        
        with open(LOG_FILE, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'alert' not in data:
                        continue
                        
                    timestamp_str = data.get('timestamp')
                    if timestamp_str:
                         try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                         except:
                            timestamp = datetime.now()
                    else:
                        timestamp = datetime.now()

                    src_ip = data.get('src_ip')
                    dest_ip = data.get('dest_ip')
                    signature = data['alert'].get('signature', 'Unknown')
                    
                    # Check for duplicates
                    exists = LogEntry.query.filter_by(
                        timestamp=timestamp,
                        src_ip=src_ip,
                        dest_ip=dest_ip,
                        signature=signature
                    ).first()
                    
                    if exists:
                        skipped += 1
                        continue

                    # Create entry
                    entry = LogEntry(
                        timestamp=timestamp,
                        event_type=data.get('event_type'),
                        src_ip=src_ip,
                        dest_ip=dest_ip,
                        src_port=data.get('src_port'),
                        dest_port=data.get('dest_port'),
                        protocol=data.get('proto'),
                        signature=signature,
                        severity=data['alert'].get('severity', 3),
                        payload=json.dumps(data)
                    )
                    db.session.add(entry)
                    count += 1
                    
                    if count % 100 == 0:
                        db.session.commit()
                        print(f"Imported {count} logs...")
                        
                except Exception as e:
                    print(f"Error processing line: {e}")
                    continue
        
        db.session.commit()
    
    print(f"Import finished. Added: {count}, Skipped: {skipped}")

if __name__ == '__main__':
    import_logs()
