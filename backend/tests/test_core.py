import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.geospatial import attribute_mapping

def test_attribute_mapping():
    m=attribute_mapping(['khasra_no','owner_name','random'])
    assert any(x['standard_field']=='parcel_id' for x in m)
    assert any(x['standard_field']=='owner_name' for x in m)
