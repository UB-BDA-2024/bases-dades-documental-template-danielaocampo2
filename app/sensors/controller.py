from fastapi import APIRouter, Depends, HTTPException,  status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.redis_client import RedisClient
from app.mongodb_client import MongoDBClient
from . import models, schemas, repository


# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get redis client
def get_redis_client():
    redis = RedisClient(host="redis")
    try:
        yield redis
    finally:
        redis.close()

# Dependency to get mongodb client
def get_mongodb_client():
    mongodb = MongoDBClient(host="mongodb")
    try:
        yield mongodb
    finally:
        mongodb.close()


router = APIRouter(
    prefix="/sensors",
    responses={404: {"description": "Not found"}},
    tags=["sensors"],
)


# 🙋🏽‍♀️ Add here the route to get a list of sensors near to a given location
@router.get("/near" ,summary="Get sensors near a location", description="Returns a list of sensors located within a specified radius of a given latitude and longitude.")
def get_sensors_near(latitude: float, longitude: float,radius: int, db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client), redis_client: RedisClient = Depends(get_redis_client)):
    return repository.get_sensors_near(mongodb_client=mongodb_client,  db=db, redis=redis_client,  latitude=latitude, longitude=longitude, radius=radius)

# 🙋🏽‍♀️ Add here the route to get data from a sensor
@router.get("/{sensor_id}/data", summary="Get sensor data", description="Retrieve recorded data for a specific sensor by its ID. Also includes the sensor's ID and name in the response.")
def get_data(sensor_id: int, db: Session = Depends(get_db) ,redis_client: RedisClient = Depends(get_redis_client)):
    try:
        data=repository.get_data(redis=redis_client, sensor_id= sensor_id)
        db_sensor=repository.get_sensor(db, sensor_id)
        if db_sensor is not None:
            data['id']=db_sensor.id
            data['name']=db_sensor.name
        return data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 

# 🙋🏽‍♀️ Add here the route to get all sensors
@router.get("", summary="Get all sensors", description="Retrieve a list of all registered sensors.")
def get_sensors(db: Session = Depends(get_db)):
    return repository.get_sensors(db)


# 🙋🏽‍♀️ Add here the route to create a sensor
@router.post("", summary="Create a new sensor", description="Register a new sensor in the database and its corresponding details in MongoDB and postgreSQL.")
def create_sensor(sensor: schemas.SensorCreate, db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client)):
    db_sensor = repository.get_sensor_by_name(db, sensor.name)
    if db_sensor:
        raise HTTPException(status_code=400, detail="Sensor with same name already registered")
    newSensor= repository.create_sensor(db=db, sensor=sensor)
    sensor_document = {
        "id_sensor": newSensor.id,
        "location": {
            "type": "Point",
            "coordinates": [sensor.longitude, sensor.latitude]
        },
        "type": sensor.type,
        "mac_address": sensor.mac_address,
        "manufacturer": sensor.manufacturer,
        "model": sensor.model,
        "serie_number": sensor.serie_number,
        "firmware_version": sensor.firmware_version
    }
    repository.insertMongodb(mongodb_client=mongodb_client, sensor_document=sensor_document)
    return newSensor

# 🙋🏽‍♀️ Add here the route to get a sensor by id
@router.get("/{sensor_id}", summary="Get sensor by ID", description="Retrieve detailed information of a sensor by its unique ID.")
def get_sensor(sensor_id: int, db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client)):
    db_sensor = repository.get_sensor(db, sensor_id)
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return db_sensor



# 🙋🏽‍♀️ Add here the route to update a sensor
@router.post("/{sensor_id}/data", summary="Record sensor data in Redis", description="Stores the received sensor data in Redis for a specific sensor identified by its ID. This endpoint is designed to quickly update and retrieve sensor data using Redis as a fast, in-memory data store.")
def record_data(sensor_id: int, data: schemas.SensorData,db: Session = Depends(get_db) ,redis_client: RedisClient = Depends(get_redis_client)):
    try:
        repository.get_sensor(db, sensor_id)
        repository.record_data(redis=redis_client, sensor_id=sensor_id, data=data)
        return {'message': 'Data recorded successfully'}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    
# 🙋🏽‍♀️ Add here the route to delete a sensor
@router.delete("/{sensor_id}", summary="Delete a sensor", description="Remove a sensor from the database, along with its data in Redis, MongoDB and postgreSQL.")
def delete_sensor(sensor_id: int, db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client), redis_client: RedisClient = Depends(get_redis_client)):
    db_sensor = repository.get_sensor(db, sensor_id)
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    try:
        repository.deleteSensorRedis(redis_client, sensor_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete sensor data in Redis: {str(e)}")
    try:
        repository.deleteSensorMongodb(mongodb_client, sensor_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete sensor data in MongoDB: {str(e)}")
    return repository.delete_sensor(db=db, sensor_id=sensor_id)