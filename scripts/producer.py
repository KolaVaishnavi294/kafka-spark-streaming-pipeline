import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

# Configuration
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    api_version=(0, 10, 1),
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

def run_producer():
    print("🚀 Producer started! Sending data to Kafka...")
    print("Press Ctrl+C to stop.")
    
    pages = ["/home", "/cart", "/checkout", "/products", "/search"]
    event_types = ["page_view", "session_start", "session_end"]
    
    try:
        while True:
            uid = f"user_{random.randint(1, 100)}"
            event = {
                "event_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + "Z",
                "user_id": uid,
                "page_url": random.choice(pages),
                "event_type": random.choice(event_types)
            }
            
            # Send current event
            producer.send('user_activity', event)
            print(f"✅ Sent: {event['event_type']} from {uid}")
            
            # 10% chance to send late data for testing Watermarks
            if random.random() < 0.1:
                late_event = event.copy()
                late_event["event_time"] = "2024-01-01T00:00:00Z"
                producer.send('user_activity', late_event)
                print(f"⚠️ Sent LATE data: {late_event['user_id']}")

            # Ensure data is pushed to Kafka immediately
            producer.flush() 
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        producer.close()

if __name__ == "__main__":
    run_producer()