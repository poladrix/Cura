# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import math
import xml.etree.ElementTree as ET

import UM.Settings

def _tag_without_namespace(element):
        return element.tag[element.tag.rfind("}") + 1:]

class XmlMaterialProfile(UM.Settings.InstanceContainer):
    def __init__(self, container_id, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

    def serialize(self):
        raise NotImplementedError("Writing material profiles has not yet been implemented")

    def deserialize(self, serialized):
        print("deserialize material profile")
        data = ET.fromstring(serialized)

        self.addMetaDataEntry("type", "material")

        # TODO: Add material verfication
        self.addMetaDataEntry("status", "Unknown")

        metadata = data.iterfind("./um:metadata/*", self.__namespaces)
        for entry in metadata:
            # The namespace is prepended to the tag name but between {}.
            # We are only interested in the actual tag name.
            tag_name = entry.tag[entry.tag.rfind("}") + 1:]

            if tag_name == "name":
                brand = entry.find("./um:brand", self.__namespaces)
                material = entry.find("./um:material", self.__namespaces)
                color = entry.find("./um:color", self.__namespaces)

                self.setName("{0} {1} ({2})".format(brand.text, material.text, color.text))

                self.addMetaDataEntry("brand", brand.text)
                self.addMetaDataEntry("material", material.text)
                self.addMetaDataEntry("color_name", color.text)

            self.addMetaDataEntry(tag_name, entry.text)

        property_values = {}
        properties = data.iterfind("./um:properties/*", self.__namespaces)
        for entry in properties:
            tag_name = entry.tag[entry.tag.rfind("}") + 1:]
            property_values[tag_name] = entry.text

        diameter = float(property_values.get("diameter", 2.85)) # In mm
        density = float(property_values.get("density", 1.3)) # In g/cm3

        weight_per_cm = (math.pi * (diameter / 20) ** 2 * 0.1) * density

        spool_weight = property_values.get("spool_weight")
        spool_length = property_values.get("spool_length")
        if spool_weight:
            length = float(spool_weight) / weight_per_cm
            property_values["spool_length"] = str(length / 100)
        elif spool_length:
            weight = (float(spool_length) * 100) * weight_per_cm
            property_values["spool_weight"] = str(weight)

        self.addMetaDataEntry("properties", property_values)

        settings = data.iterfind("./um:settings/um:setting", self.__namespaces)
        for entry in settings:
            tag_name = _tag_without_namespace(entry)

            if tag_name in self.__material_property_setting_map:
                self.setProperty(self.__material_property_setting_map[tag_name], "value", entry.text)

    __material_property_setting_map = {
        "print temperature": "material_print_temperature",
        "heated bed temperature": "material_bed_temperature",
        "standby temperature": "material_standby_temperature",
    }

    __namespaces = {
        "um": "http://www.ultimaker.com/material"
    }
