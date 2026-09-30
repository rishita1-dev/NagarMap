# GeoHarmonize — SIH26013 MVP

**Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management**

GeoHarmonize is a lightweight SIH 2026 prototype demonstrating an end-to-end workflow for ingesting multiple urban land datasets, standardizing them to a common CRS, intelligently mapping attributes, spatially matching features, detecting conflicts/topology issues, calculating explainable confidence and visualizing the unified result in a WebGIS.

> **Demo data is synthetic and fictional. It is not official government data.**

## Core workflow

`Ingest → Validate → CRS Standardize → Attribute Mapping → Spatial Matching → Conflict Detection → Confidence → WebGIS → Export`

## Tech stack

- **Frontend:** React + Vite + Leaflet + Recharts
- **Backend:** FastAPI
- **Geospatial:** GeoPandas + Shapely + PyProj
- **Data:** GeoJSON + CSV + SQLite-ready architecture
- **AI-assisted logic:** fuzzy/alias attribute matching + spatial overlap + centroid distance + identifier evidence

No paid AI API is required.

## Run on Windows

### 1. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs

### 2. Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Judge demo

1. Open **Dashboard**.
2. Click **Start Demo**.
3. The sample cadastral, revenue, buildings, utility and GNSS layers are loaded.
4. Open **Data Integration** and run spatial matching.
5. Open **Conflict Review** and detect mismatches.
6. Open **Map Workspace** to show the unified layers.
7. Open **Analytics** to show live processing metrics.
8. Open **Export** to download GeoJSON.

## Why this MVP is credible

The core spatial operations are actual GeoPandas/Shapely calculations rather than random scores. Matching confidence combines geometry overlap, centroid distance and identifier evidence. Dataset statistics are calculated from loaded data.

## Supported MVP inputs

- GeoJSON
- JSON GeoJSON
- CSV containing latitude/longitude
- GPKG where supported by the local Fiona environment

## Limitations

This MVP intentionally does not attempt full production-grade drone/ORI/DSM computer vision, cadastral legal adjudication, CORS infrastructure or national-scale distributed processing. Those are extension paths. The demonstrable MVP focuses on the multi-source vector harmonization and audit workflow that can be run locally on a normal laptop.
