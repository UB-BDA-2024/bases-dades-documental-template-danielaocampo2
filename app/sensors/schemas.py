from pydantic import BaseModel

class Sensor(BaseModel):
    id: int
    name: str # sql 
    latitude: float  # mongo
    longitude: float  # mongo
    joined_at: str   # sql
    last_seen: str # redis
    type: str #mongo 
    mac_address: str # mongo 
    battery_level: float # redis
    temperature: float # redis
    humidity: float # redis
    velocity: float # redis
    
    
    class Config:
        orm_mode = True
        
class SensorCreate(BaseModel):
    name: str
    longitude: float
    latitude: float
    type: str
    mac_address: str
    manufacturer: str
    model: str
    serie_number: str
    firmware_version: str

class SensorData(BaseModel):
    velocity: float 
    temperature: float 
    humidity: float 
    battery_level: float
    last_seen: str
    
