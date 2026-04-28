from Database_specification import db, app, Data, AMR, Error
import random

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



AMR_list = []

with app.app_context():
    db.drop_all() # remove current tables in database.db
    db.create_all() # create new tables in database.db

    for i in range(2,255):
        new_amr = AMR(ip=f'192.168.1.{i}',name=f'AMR #{i}',raspi_ip=f'192.168.2.{i}')
        AMR_list.append(new_amr)
        db.session.add(new_amr)
    db.session.commit()

    for i in range(1000):
        new_data = Data(
            amr_ip=AMR_list[i%253].ip,
            rtt=random.random()*40,
            jitter=random.random()*10,
            packet_loss=random.random()*0.1,
            signal_strength=random.random()*(-72),
            noise=random.random()*(-80),
            battery=(1000-i)/1000,
            pos_x=0.2*i,
            pos_y=-0.04*i
        )
        db.session.add(new_data)
    db.session.commit()

    for i in range(100):
        error_type = random.randint(0,9)
        amr_ip = random.randint(2,254)
        new_error = Error(
            amr_ip=f'192.168.1.{amr_ip}',
            error=ErrorTypes[error_type],
            error_desc=Descriptions[error_type]
        )
        db.session.add(new_error)
    db.session.commit()
