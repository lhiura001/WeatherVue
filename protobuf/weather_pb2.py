# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: weather.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rweather.proto\x12\x07weather\",\n\x0eWeatherRequest\x12\x0c\n\x04\x63ity\x18\x01 \x01(\t\x12\x0c\n\x04unit\x18\x02 \x01(\t\"\x90\x02\n\x0fWeatherResponse\x12\x17\n\x0fweather_summary\x18\x01 \x01(\t\x12\x1b\n\x13weather_description\x18\x02 \x01(\t\x12\x14\n\x0chigh_temp_pm\x18\x03 \x01(\x02\x12\x14\n\x0chigh_temp_am\x18\x04 \x01(\x02\x12\x17\n\x0fhigh_temp_night\x18\x05 \x01(\x02\x12\x13\n\x0blow_temp_pm\x18\x06 \x01(\x02\x12\x13\n\x0blow_temp_am\x18\x07 \x01(\x02\x12\x16\n\x0elow_temp_night\x18\x08 \x01(\x02\x12\x13\n\x0bhumidity_pm\x18\t \x01(\x02\x12\x13\n\x0bhumidity_am\x18\n \x01(\x02\x12\x16\n\x0ehumidity_night\x18\x0b \x01(\x02\x32Q\n\x0eWeatherService\x12?\n\nGetWeather\x12\x17.weather.WeatherRequest\x1a\x18.weather.WeatherResponseb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'weather_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _WEATHERREQUEST._serialized_start=26
  _WEATHERREQUEST._serialized_end=70
  _WEATHERRESPONSE._serialized_start=73
  _WEATHERRESPONSE._serialized_end=345
  _WEATHERSERVICE._serialized_start=347
  _WEATHERSERVICE._serialized_end=428
# @@protoc_insertion_point(module_scope)