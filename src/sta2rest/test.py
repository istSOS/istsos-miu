"""
Module: STA2REST Test

Author: Filippo Finke

This module provides unit tests for the STA2REST module.
"""
import unittest
from sta2rest import STA2REST

class STA2RESTTestCase(unittest.TestCase):
    def test_convert_entity(self):
        entity_mappings = {
            "Things": 'sensorthings."Thing"',
            "Locations": 'sensorthings."Location"',
            "Sensors": 'sensorthings."Sensor"',
            "ObservedProperties": 'sensorthings."ObservedProperty"',
            "Datastreams": 'sensorthings."Datastream"',
            "Observations": 'sensorthings."Observation"',
            "FeaturesOfInterest": 'sensorthings."FeatureOfInterest"',
            "HistoricalLocations": 'sensorthings."HistoricalLocation"'
            # Add more entity mappings as needed
        }

        for entity, expected in entity_mappings.items():
            self.assertEqual(STA2REST.convert_entity(entity), expected)

    def test_convert_property(self):
        property_mappings = {
            "name": '"name"',
            "description": '"description"',
            "encodingType": '"encodingType"',
            "metadata": '"metadata"'
            # Add more property mappings as needed
        }

        for prop, expected in property_mappings.items():
            self.assertEqual(STA2REST.convert_property(prop), expected)

    def test_convert_query_param(self):
        query_param_mappings = {
            "filter": "filter",
            "orderby": "order",
            "top": "limit",
            "skip": "offset"
            # Add more query parameter mappings as needed
        }

        for param, expected in query_param_mappings.items():
            self.assertEqual(STA2REST.convert_query_param(param), expected)

    def test_convert_sensor_things_query(self):
        query_mappings = {
            "$filter=type eq 'temperature'&$orderby=timestamp desc&$top=10&$skip=5":
                "filter=type eq 'temperature'&order=timestamp desc&limit=10&offset=5",
            "$filter=type eq 'humidity'&$top=5":
                "filter=type eq 'humidity'&limit=5",
            "$orderby=timestamp asc&$skip=2":
                "order=timestamp asc&offset=2"
            # Add more query mappings as needed
        }

        for query, expected in query_mappings.items():
            self.assertEqual(STA2REST.convert_query(query), expected)

if __name__ == '__main__':
    unittest.main()
