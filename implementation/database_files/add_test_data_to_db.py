from Database_specification import db, app, Data, AMR, Error
import random
from datetime import datetime, timedelta
from time import sleep

import sys

if sys.platform == "linux":
    file_sep = '/'
else:
    file_sep = '\\'
cur_parent_dirs = sys.path[0].split(file_sep)
parent_dir_index = cur_parent_dirs.index("P2")
sys.path.append(file_sep.join(cur_parent_dirs[0:parent_dir_index+1])) # allows imports from P2 folder

from implementation.network_monitorer import NetworkMonitorer

"""

This script is simply for adding some test data to the database

"""

ErrorTypes = [
    "QuantumBufferOverflow",
    "SilentCacheMismatch",
    "PhantomTokenFailure",
    "BrokenSessionLatch",
    "TurboIndexCorruption",
    "HiddenRouteTimeout",
    "MysticPayloadError",
    "RapidSchemaConflict",
    "FrozenThreadCollapse",
    "ShadowMemoryLeak"
]

Descriptions = [
    "Data exceeded the allowed buffer size during parallel processing",
    "Cached values differ from the latest source without triggering alerts.",
    "Authentication token appears valid but fails verification.",
    "User session could not reconnect after temporary interruption.",
    "Search index became damaged during high-speed updates.",
    "Internal network route took too long to respond.",
    "Incoming request payload contains unknown or malformed fields.",
    "Database schema changed while active requests were running.",
    "Background thread stopped responding and caused task failure.",
    "Memory usage increased gradually due to unreleased hidden objects."
]


if __name__ == '__main__':
    AMR_list = []
    network_monitorer = NetworkMonitorer('','')

    with app.app_context():
        db.drop_all() # remove current tables in database.db
        db.create_all() # create new tables in database.db

        for i in range(2,255):
            network_monitorer.add_amr_to_database(ip=f'192.168.100.{i}',name=f'AMR #{i}',dev_eui=f'192.168.2.{i}')
            AMR_list.append(f'192.168.100.{i}')
        print("AMR's created")

        # Create test data with timestamps spread across 1 hour
        base_time = datetime.now() - timedelta(hours=1)
        
        for i in range(1000):
            # Spread timestamps across 60 minutes (3600 seconds)
            time_offset = timedelta(seconds=(i / 1000) * 3600)
            timestamp = base_time + time_offset
            
            new_data = Data(
                amr_ip=AMR_list[i%253],
                timestamp=timestamp,
            )
        
        for i in range(1000*255):
            new_data = Data(
                amr_ip=AMR_list[i%253],
                rtt=random.random()*40,
                jitter=random.random()*10,
                packet_loss=random.random()*0.1,
                quality=random.random()*(-72),
                noise=random.random()*(-80),
                battery=(1000-i)/1000,
                pos_x=0.0102*(i),
                pos_y=-0.01*(i),
                timestamp=datetime.now()+timedelta(seconds=i)
            )
            db.session.add(new_data)
            sleep(0.1/255)
            db.session.commit()

        for i in range(100):
            error_type = random.randint(0,9)
            amr_ip = random.randint(2,254)
            new_error = Error(
                amr_ip=f'192.168.100.{amr_ip}',
                error=ErrorTypes[error_type],
                error_desc=Descriptions[error_type],
                timestamp=datetime.now()+timedelta(seconds=i)
            )
            db.session.add(new_error)
        db.session.commit()
