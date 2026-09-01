import sys
sys.path.insert(0, 'backend')
from pathlib import Path
from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.services.geo_origin import GeoOriginService

print("DEMO EMAILS AUDIT (BASELINE):")
print("-" * 100)
for eml in sorted(Path('sample_emails').glob('*.eml')):
    data = IngestionService.parse_raw_email(eml.read_bytes())
    hops, ear, anom = HeaderForensicsService.parse_received_chain(data['received_headers'])
    orig = GeoOriginService.evaluate_origin(ear, len(hops))
    geo = orig.get('geolocation', {})
    ip_str = str(orig.get("probable_origin_ip"))
    country = str(geo.get("country"))
    isp = str(geo.get("isp"))
    asn = str(geo.get("asn"))
    print(f"{eml.name:32} | {ip_str:16} | {country:15} | {isp:26} | {asn}")
