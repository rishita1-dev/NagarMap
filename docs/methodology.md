# GeoHarmonize Methodology

## Confidence model

Candidate feature pairs are scored from measurable evidence:

- 55% geometry overlap
- 30% centroid proximity
- 15% identifier agreement

Thresholds:

- High: >= 90
- Medium: 70–89.9
- Review: < 70

## Attribute harmonization

Source field names are normalized and compared against a small domain alias dictionary. The MVP maps common cadastral/revenue variations such as `khasra_no`, `survey_no`, `plot_no` and `parcel_id` to a common `parcel_id` concept.

## Topology

The backend checks invalid geometries and overlapping vector features. Geometry repair can be extended with Shapely `make_valid` in the next iteration.

## Governance principle

The system is decision-support software. It surfaces evidence and conflicts; it does not silently overwrite official land records.
