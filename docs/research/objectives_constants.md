# Objective Functions Constants
Extracted from research documents (Week 1)

## Construction Costs (TL/m²)
Source: Construction_Cost_and_NPV_Optimization_Guide.docx

| Building Type    | Cost (TL/m²) | Notes |
|-----------------|--------------|-------|
| RESIDENTIAL     | 1,500        | Standard dormitory |
| EDUCATIONAL     | 2,000        | Classroom buildings |
| ADMINISTRATIVE  | 1,800        | Office buildings |
| HEALTH          | 2,500        | Medical facilities |
| SOCIAL          | 1,600        | Student centers |
| COMMERCIAL      | 2,200        | Shops, cafes |
| LIBRARY         | 2,300        | Library buildings |
| SPORTS          | 1,900        | Gyms, fields |
| DINING          | 1,700        | Cafeterias |

**Reference Total:** 100,000,000 TL (typical campus)

## Walking Distance (15-Minute City)
Source: 15-Minute_City_Optimization_Analysis.docx

- **Ideal Distance:** 200 meters
- **Max Acceptable:** 800 meters
- **Focus Pairs:** Residential ↔ Educational

## Adjacency Matrix
Source: Building_Typology_Spatial_Optimization_Research.docx

| Type 1       | Type 2         | Weight | Meaning |
|--------------|----------------|--------|---------|
| Residential  | Educational    | +5.0   | Should be close |
| Residential  | Social         | +4.0   | Should be close |
| Residential  | Health         | -3.0   | Should be apart |
| Educational  | Administrative | +3.0   | Should be close |
| Educational  | Social         | +2.0   | Should be close |
| Educational  | Library        | +4.0   | Should be close |
| Health       | Health         | -5.0   | Should be far apart |
| Commercial   | Residential    | +3.0   | Should be close |
| Dining       | Residential    | +4.0   | Should be close |
| Dining       | Educational    | +3.0   | Should be close |

**Reference Distance:** 100 meters (decay scale)
**Max Consideration:** 500 meters (cutoff)
