import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.redis_client import RedisClient
from app.mongodb_client import MongoDBClient


from . import models, schemas

#change
def get_sensor(db: Session, sensor_id: int) -> Optional[models.Sensor]:
    db_sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return db_sensor

def get_sensor_by_name(db: Session, name: str) -> Optional[models.Sensor]:
    return db.query(models.Sensor).filter(models.Sensor.name == name).first()

def get_sensors(db: Session, skip: int = 0, limit: int = 100) -> List[models.Sensor]:
    return db.query(models.Sensor).offset(skip).limit(limit).all()

def create_sensor(db: Session, sensor: schemas.SensorCreate) -> models.Sensor:
    db_sensor = models.Sensor(name=sensor.name)
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor

def insertMongodb(mongodb_client: MongoDBClient, sensor_document):
    try:
        mongodb_client.getDatabase('P2Documentales')
        mongodb_client.getCollection('sensors')
        mongodb_client.collection.insert_one(sensor_document)
    except Exception as e:
        # Aquí podrías manejar o registrar la excepción específica
        print(f"Error al insertar en MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to insert sensor data into MongoDB")


def record_data(redis: RedisClient, sensor_id: int, data: schemas.SensorData) -> schemas.Sensor:
    data_dict = data.dict()
    redis_key = f"sensor:{sensor_id}:data"
    data_json = json.dumps(data_dict)
    success = redis.set(redis_key, data_json)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set data in Redis")


def delete_sensor(db: Session, sensor_id: int):
    db_sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    db.delete(db_sensor)
    db.commit()
    return db_sensor

#change
def get_data(redis: RedisClient, sensor_id: int) -> schemas.Sensor:
    redis_key = f"sensor:{sensor_id}:data"
    stored_data = redis.get(redis_key)
    if stored_data is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    stored_data = json.loads(stored_data.decode("utf-8"))
    return stored_data