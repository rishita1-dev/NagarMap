from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import shutil, json, uuid
from .services.geospatial import *

app=FastAPI(title='GeoHarmonize API',version='1.0.0',description='SIH26013 AI-assisted geospatial harmonization MVP')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
ROOT=Path(__file__).resolve().parents[2]; UPLOAD=ROOT/'data'/'uploads'; UPLOAD.mkdir(parents=True,exist_ok=True)
DATASETS={}; AUDIT=[]; CONFLICTS=[]

@app.get('/health')
def health(): return {'status':'ok','service':'GeoHarmonize API'}
@app.get('/demo')
def demo(): return demo_summary()

@app.post('/datasets/upload')
async def upload(file:UploadFile=File(...),source_type:str='Other'):
    ext=Path(file.filename).suffix.lower()
    if ext not in ['.geojson','.json','.csv','.gpkg','.shp']: raise HTTPException(400,'Supported MVP formats: GeoJSON, JSON, CSV, GPKG, SHP')
    fid=str(uuid.uuid4()); dest=UPLOAD/f'{fid}{ext}'
    with dest.open('wb') as f: shutil.copyfileobj(file.file,f)
    try: gdf=load_vector(dest); v=validate(gdf)
    except Exception as e: dest.unlink(missing_ok=True); raise HTTPException(400,str(e))
    DATASETS[fid]={'id':fid,'filename':file.filename,'source_type':source_type,'path':str(dest),'validation':v,'fields':attribute_mapping(gdf.columns)}
    AUDIT.append({'action':'Dataset uploaded','dataset_id':fid,'detail':file.filename})
    return DATASETS[fid]

@app.get('/datasets')
def datasets(): return list(DATASETS.values())

@app.post('/datasets/{fid}/validate')
def validate_dataset(fid:str):
    d=DATASETS.get(fid)
    if not d: raise HTTPException(404,'Dataset not found')
    g=load_vector(d['path']); d['validation']=validate(g); AUDIT.append({'action':'Dataset validated','dataset_id':fid}); return d['validation']

@app.post('/integration/match')
def match(payload:dict):
    a=DATASETS.get(payload.get('source_a')); b=DATASETS.get(payload.get('source_b'))
    if not a or not b: raise HTTPException(404,'Both datasets are required')
    ga,gb=load_vector(a['path']),load_vector(b['path']); result=spatial_match(ga,gb)
    high=sum(x['status']=='high' for x in result); medium=sum(x['status']=='medium' for x in result)
    AUDIT.append({'action':'Spatial matching completed','detail':f'{len(result)} candidate matches'})
    return {'matches':result,'stats':{'candidate_matches':len(result),'high_confidence':high,'medium_confidence':medium,'review_required':len(result)-high-medium}}

@app.post('/topology/check')
def topology_check(payload:dict):
    d=DATASETS.get(payload.get('dataset_id'))
    if not d: raise HTTPException(404,'Dataset not found')
    result=topology(load_vector(d['path'])); AUDIT.append({'action':'Topology check','detail':f"{result['count']} issues"}); return result

@app.post('/conflicts/detect')
def conflicts(payload:dict):
    a=DATASETS.get(payload.get('source_a')); b=DATASETS.get(payload.get('source_b'))
    if not a or not b: raise HTTPException(404,'Both datasets are required')
    ga,gb=load_vector(a['path']),load_vector(b['path']); matches=spatial_match(ga,gb); found=[]
    for m in matches:
        if m['confidence']<90:
            found.append({'id':str(uuid.uuid4())[:8],'type':'Spatial mismatch','source_a':a['filename'],'source_b':b['filename'],'feature':f"{m['source_a_index']} ↔ {m['source_b_index']}",'severity':'High' if m['confidence']<70 else 'Medium','confidence':m['confidence'],'status':'Review Required'})
    CONFLICTS.extend(found); AUDIT.append({'action':'Conflict detection','detail':f'{len(found)} conflicts'})
    return {'conflicts':found,'count':len(found)}

@app.get('/conflicts')
def get_conflicts(): return CONFLICTS
@app.get('/audit')
def audit(): return AUDIT

@app.get('/analytics')
def analytics():
    features=sum(d['validation']['features'] for d in DATASETS.values())
    invalid=sum(d['validation']['invalid_geometries'] for d in DATASETS.values())
    return {'datasets':len(DATASETS),'features':features,'invalid_geometries':invalid,'conflicts':len(CONFLICTS),'high_confidence':max(0,features-len(CONFLICTS)-invalid),'processing_complete':len(DATASETS)>0}

@app.get('/map/layers')
def map_layers():
    out=[]
    for d in DATASETS.values():
        try:
            g=load_vector(d['path']); out.append({'id':d['id'],'name':d['filename'],'source_type':d['source_type'],'geojson':json.loads(g.to_json())})
        except Exception: pass
    return out

@app.get('/export/{fid}')
def export(fid:str):
    d=DATASETS.get(fid)
    if not d: raise HTTPException(404,'Dataset not found')
    g=load_vector(d['path']); out=UPLOAD/f'{fid}_harmonized.geojson'; g.to_file(out,driver='GeoJSON'); return FileResponse(out,filename='harmonized_land_dataset.geojson',media_type='application/geo+json')
