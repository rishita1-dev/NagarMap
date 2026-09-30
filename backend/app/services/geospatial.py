import json, math, os, uuid
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, LineString
from shapely.validation import explain_validity

TARGET_CRS='EPSG:4326'
BASE=Path(__file__).resolve().parents[2]
DATA=BASE/'data'


def load_vector(path):
    p=Path(path)
    if p.suffix.lower()=='.csv':
        df=pd.read_csv(p)
        lat=next((c for c in df.columns if c.lower() in ['lat','latitude']),None)
        lon=next((c for c in df.columns if c.lower() in ['lon','lng','longitude']),None)
        if lat and lon:
            return gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df[lon],df[lat])], crs=TARGET_CRS)
        raise ValueError('CSV must contain latitude/longitude columns')
    gdf=gpd.read_file(p)
    if gdf.crs is None: gdf=gdf.set_crs(TARGET_CRS)
    return gdf.to_crs(TARGET_CRS)


def validate(gdf):
    invalid=[i for i,g in enumerate(gdf.geometry) if g is not None and not g.is_valid]
    return {'features':len(gdf),'geometry_types':sorted(gdf.geom_type.dropna().unique().tolist()),'crs':str(gdf.crs),'invalid_geometries':len(invalid),'invalid_indexes':invalid[:20]}


def normalize_name(s):
    return ''.join(ch for ch in str(s).lower() if ch.isalnum())

ALIASES={'parcel_id':['parcelid','parcel','plotno','plotnumber','khasrano','survey_no','surveyno','id'],'owner_name':['owner','ownername','propertyowner'],'area':['area','areasqm','area_sqm','parcelarea'],'building_id':['buildingid','building','bldgid']}

def attribute_mapping(columns):
    out=[]
    for c in columns:
        n=normalize_name(c); best=None; score=0
        for standard, aliases in ALIASES.items():
            for a in aliases:
                an=normalize_name(a)
                if n==an: s=1.0
                elif n in an or an in n: s=.82
                else: s=0
                if s>score: score=s; best=standard
        if best:
            out.append({'source_field':c,'standard_field':best,'confidence':round(score*100)})
    return out


def spatial_match(a,b):
    matches=[]
    if a.empty or b.empty:return matches
    for i,ga in a.geometry.items():
        if ga is None or ga.is_empty: continue
        candidates=b[b.geometry.intersects(ga.buffer(0.0005))]
        for j,gb in candidates.geometry.items():
            inter=ga.intersection(gb).area
            union=ga.union(gb).area
            overlap=(inter/union) if union else 0
            dist=ga.centroid.distance(gb.centroid)
            dist_score=max(0,1-dist/0.002)
            attr_score=0
            for col in ['parcel_id','survey_no','khasra_no','building_id']:
                if col in a.columns and col in b.columns and str(a.loc[i,col])==str(b.loc[j,col]): attr_score=1; break
            conf=round((overlap*.55+dist_score*.30+attr_score*.15)*100,1)
            matches.append({'source_a_index':int(i),'source_b_index':int(j),'overlap':round(overlap,3),'distance':round(dist,6),'confidence':conf,'status':'high' if conf>=90 else 'medium' if conf>=70 else 'review'})
    return sorted(matches,key=lambda x:x['confidence'],reverse=True)


def topology(gdf):
    invalid=[]
    for i,g in enumerate(gdf.geometry):
        if g is not None and not g.is_valid: invalid.append({'index':i,'reason':explain_validity(g)})
    overlaps=[]
    geoms=list(gdf.geometry)
    for i in range(len(geoms)):
        if geoms[i] is None: continue
        for j in range(i+1,min(len(geoms),i+30)):
            if geoms[i].overlaps(geoms[j]): overlaps.append({'a':i,'b':j})
    return {'invalid':invalid,'overlaps':overlaps[:50],'count':len(invalid)+len(overlaps)}


def demo_summary():
    return {'demo':'NAKSHA Urban Harmonization Demo','sources':['Cadastral Parcels','Revenue Records','Municipal Buildings','Utility Network','GNSS / Ground Truth'],'synthetic':True}
