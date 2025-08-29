from tools.metadata_utils import parse_decimal_from_exif_gps

lat = parse_decimal_from_exif_gps("32 deg 54' 10.48\" S")
lon = parse_decimal_from_exif_gps("60 deg 44' 4.91\" W")

print(lat, lon)
