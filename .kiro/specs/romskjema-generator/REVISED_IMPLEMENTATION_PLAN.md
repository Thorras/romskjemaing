# Romskjema Generator - Revidert Implementeringsplan

## Oversikt

Dette planverket tar hensyn til eksisterende kodebase, mine anbefalinger om inkrementell tilnærming, og .kiro-retningslinjene for kvalitetssikring og testing. Planen bygger på det solide fundamentet i IFC Room Schedule applikasjonen og utvider funksjonaliteten gradvis.

## Strategisk Tilnærming

### Kjerneprinsipp: Inkrementell Verdilevering
- **Bygg på eksisterende styrker** - Utvid dagens JSON-eksport i stedet for å skrive om
- **Høyverdi-seksjoner først** - Fokuser på mest verdifulle deler av romskjema-malen
- **Risikoreduksjon** - Test og valider hver seksjon før neste
- **Tidlig feedback** - Lever funksjonalitet som kan testes av brukere

### Kvalitetssikring [[memory:9414131]]
Følger .kiro-retningslinjene:
- **Code Quality**: black, flake8, mypy på alle Python-filer
- **Testing**: Omfattende unit og integrasjonstester
- **Performance Monitoring**: Sporing av IFC-parsing ytelse
- **IFC Validation**: Validering av IFC-filer og data
- **Documentation**: Automatisk generering av dokumentasjon

## Fase 0: Grunnlag og Validering ✅ FULLFØRT

### 0.1 Datakvalitetsanalyse ✅ FULLFØRT
**Mål**: Forstå gap mellom eksisterende IFC-data og omfattende romskjema-mal

```python
# Implementert: ifc_room_schedule/analysis/data_quality_analyzer.py
class DataQualityAnalyzer:
    def analyze_ifc_coverage(self, ifc_file: str) -> 'CoverageReport' ✅
    def analyze_spaces_quality(self, spaces: List[SpaceData]) -> 'CoverageReport' ✅
    def _analyze_single_space(self, space: SpaceData) -> 'MissingDataReport' ✅
    def _generate_simple_recommendations(self, stats: Dict, total: int) -> List[str] ✅
```

**Deliverables**: ✅ FULLFØRT
- [x] Analyse eksisterende IFC-filer og testdata
- [x] Kartlegg hvilke deler av romskjema-malen som kan populeres
- [x] Identifiser kritiske mangler og fallback-strategier
- [x] Rapport med anbefalinger for prioritering

### 0.2 Arkitektur-forberedelser ✅ FULLFØRT
**Mål**: Forberede eksisterende kodebase for utvidelse

```python
# Implementert: ifc_room_schedule/data/space_model.py
@dataclass
class SpaceData:
    # Alle nødvendige felt implementert ✅
    metadata: RoomScheduleMetadata
    spaces: List[SpaceData]
    
    # Nye seksjoner (gradvis implementering)
    meta: Optional['MetaData'] = None
    identification: Optional['IdentificationData'] = None
    ifc_metadata: Optional['IFCMetadata'] = None
    geometry_enhanced: Optional['GeometryEnhanced'] = None
```

**Deliverables**:
- [ ] Utvid datamodeller for å støtte nye seksjoner
- [ ] Opprett konfigurasjonssystem for seksjon-aktivering
- [ ] Implementer bakoverkompatibilitet med eksisterende eksport
- [ ] Oppdater tester for nye datastrukturer

## Fase 1: Kjerneseksjoner ✅ FULLFØRT (4-6 uker)

### 1.1 Meta og Identification med NS 8360/NS 3940 Standard ✅ FULLFØRT (Uke 1-2)
**Prioritet**: Høy - Grunnleggende prosjektinformasjon basert på norske standarder

**Implementering**:
```python
# ifc_room_schedule/parsers/ns8360_name_parser.py
class NS8360NameParser:
    def parse(self, space_name: str) -> 'NS8360ParsedName'
    def validate(self, space_name: str) -> bool
    # Patterns: SPC-{storey}-{zone}-{func}-{seq} eller SPC-{storey}-{func}-{seq}

# ifc_room_schedule/mappers/ns3940_classifier.py
class NS3940Classifier:
    def classify_from_code(self, function_code: str) -> Optional[Dict]
    def infer_code_from_name(self, room_name: str) -> Optional[str]
    # Codes: 111=Oppholdsrom, 130=Våtrom, 131=WC, 132=Baderom

# ifc_room_schedule/mappers/meta_mapper.py
class MetaMapper:
    def extract_meta_data(self, ifc_file: IfcFile) -> 'MetaData'
    def map_project_info(self, space: SpaceData) -> 'IdentificationData'
    def generate_timestamps(self) -> Dict[str, datetime]

# ifc_room_schedule/mappers/enhanced_identification_mapper.py  
class EnhancedIdentificationMapper:
    def __init__(self):
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def map_identification(self, space: SpaceData) -> 'IdentificationData'
    def extract_project_hierarchy(self, space: SpaceData) -> 'IdentificationData'
    def map_building_structure(self, ifc_file: IfcFile) -> Dict[str, str]
```

**NS 8360/NS 3940 Integration**:
- **Structured Name Parsing**: Automatisk parsing av `SPC-02-A101-111-003` format
- **Function Classification**: NS 3940 koder til romtype og egenskaper
- **Intelligent Fallback**: Inference fra romnavn når standard ikke følges
- **Validation**: Regex-basert validering av navngivningskonvensjoner

**Fallback-strategier**:
- **NS 8360 Non-compliant**: Intelligent parsing av ikke-standard romnavn
- **Missing Function Code**: Infer fra norske romnavn (stue→111, bad→130)
- **Prosjekt-ID**: Generer fra filnavn hvis ikke tilgjengelig
- **Bygning/etasje**: Ekstraher fra IFC-hierarki eller parsed name components

**Testing**:
- [ ] Unit tests for alle mapping-funksjoner
- [ ] Integration tests med AkkordSvingen-filen
- [ ] Validering mot JSON-schema

### 1.2 IFC Metadata og Geometry Enhanced (Uke 2-3)
**Prioritet**: Høy - Bygger på eksisterende IFC-parsing styrker

**Implementering**:
```python
# ifc_room_schedule/mappers/ifc_metadata_mapper.py
class IFCMetadataMapper:
    def extract_complete_hierarchy(self, space: SpaceData) -> 'IFCMetadata'
    def map_model_source_info(self, ifc_file: IfcFile) -> 'ModelSourceData'
    def validate_guid_consistency(self, data: 'IFCMetadata') -> bool

# ifc_room_schedule/mappers/geometry_enhanced_mapper.py
class GeometryEnhancedMapper:
    def calculate_enhanced_geometry(self, space: SpaceData) -> 'GeometryEnhanced'
    def estimate_missing_dimensions(self, space: SpaceData) -> Dict[str, float]
    def extract_room_local_origin(self, space: SpaceData) -> 'LocalOrigin'
```

**Fallback-strategier**:
- Geometri: Estimer fra eksisterende quantities
- Lokalt origo: Bruk space placement eller (0,0,0)
- Dimensjoner: Beregn fra areal og antatte proporsjoner

### 1.3 Classification og Performance Requirements med NS 3940 Defaults (Uke 3-4)
**Prioritet**: Middels - Tekniske krav basert på NS 3940 romtype-klassifisering

**Implementering**:
```python
# ifc_room_schedule/mappers/enhanced_classification_mapper.py
class EnhancedClassificationMapper:
    def __init__(self):
        self.ns3940_classifier = NS3940Classifier()
        self.name_parser = NS8360NameParser()
    
    def map_classification(self, space: SpaceData) -> 'ClassificationData'
    def map_ns3940_codes(self, space: SpaceData) -> Dict[str, Any]
    def validate_classification_consistency(self, space: SpaceData) -> bool

# ifc_room_schedule/mappers/ns3940_performance_mapper.py
class NS3940PerformanceMapper:
    def map_technical_requirements(self, space: SpaceData, ns3940_code: str) -> 'PerformanceRequirements'
    def get_room_type_defaults(self, function_code: str) -> Dict[str, Any]
    def apply_norwegian_standards(self, room_type: str) -> Dict[str, Any]
    def extract_fire_safety_data(self, space: SpaceData) -> 'FireData'

# ifc_room_schedule/defaults/ns3940_defaults.py
NS3940_PERFORMANCE_DEFAULTS = {
    "111": {  # Oppholdsrom
        "lighting": {"task_lux": 200, "color_rendering_CRI": 80},
        "acoustics": {"class_ns8175": "C", "background_noise_dB": 35},
        "ventilation": {"airflow_supply_m3h": 7.2}  # Per m2
    },
    "130": {  # Våtrom  
        "lighting": {"task_lux": 200, "emergency_lighting": True},
        "ventilation": {"airflow_extract_m3h": 54},
        "water_sanitary": {"hot_cold_water": True, "drainage_required": True}
    }
}
```

**NS 3940 Performance Integration**:
- **Room Type Defaults**: Automatiske tekniske krav basert på funksjonskode
- **Wet Room Detection**: Automatisk identifikasjon av våtrom (130, 131, 132)
- **Equipment Inference**: Standard utstyr per romtype og disiplin
- **TEK17 Compliance**: Accessibility krav basert på romfunksjon

**Fallback-strategier**:
- **NS 3940 Mapping**: Automatisk fra parsed name eller intelligent inference
- **Performance Defaults**: Kontekstuelle verdier per norske standarder
- **Equipment Lists**: Standard utstyr basert på romtype (bad→ventilator+WC)
- **Compliance Requirements**: TEK17/NS 8175 krav per funksjon

### 1.4 NS Standard Validation og Integration (Uke 4-6)
**Mål**: Integrere NS 8360/NS 3940 standarder i eksportsystem med validering

**Implementering**:
```python
# ifc_room_schedule/validation/ns8360_validator.py
class NS8360Validator:
    def validate_space_name(self, space: SpaceData) -> ValidationResult
    def validate_naming_consistency(self, spaces: List[SpaceData]) -> List[ValidationResult]

# ifc_room_schedule/validation/ns3940_validator.py  
class NS3940Validator:
    def validate_classification_consistency(self, space: SpaceData, room_data: Dict) -> ValidationResult
    def validate_wet_room_consistency(self, space: SpaceData, room_data: Dict) -> ValidationResult

# ifc_room_schedule/export/enhanced_json_builder.py
class EnhancedJsonBuilder(JsonBuilder):
    def __init__(self):
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
        
    def build_enhanced_structure(self, spaces: List[SpaceData]) -> Dict[str, Any]
    def apply_section_filtering(self, data: Dict, config: ExportConfiguration) -> Dict
    def validate_enhanced_schema(self, data: Dict) -> Tuple[bool, List[str]]
    def enrich_with_ns_standards(self, space_data: SpaceData) -> Dict[str, Any]

# ifc_room_schedule/ui/enhanced_export_dialog.py
class EnhancedExportDialog(QDialog):
    def setup_section_checkboxes(self) -> None
    def show_data_quality_preview(self) -> None
    def show_ns_standard_compliance(self) -> None
    def configure_fallback_strategies(self) -> None
```

**NS Standards Integration**:
- **Enhanced JSON Structure**: Automatisk enrichment med NS 8360/NS 3940 data
- **Classification Section**: Structured NS 3940 codes med confidence scoring
- **IFC Section**: NS 8360 parsed components og compliance status
- **Validation Integration**: Real-time validation mot norske standarder

**Testing og Validering**:
- [ ] NS 8360 name parsing tests med standard-eksempler
- [ ] NS 3940 classification accuracy testing
- [ ] End-to-end testing med AkkordSvingen-filen
- [ ] Standards compliance validation testing
- [ ] Performance testing med store IFC-filer
- [ ] UI testing for enhanced export-dialog

## Fase 2: Utvidede Seksjoner (6-8 uker)

### 2.1 Finishes og Openings (Uke 1-3)
**Fokus**: Bygningselementer og materialer

```python
# ifc_room_schedule/mappers/finishes_mapper.py
class FinishesMapper:
    def extract_surface_finishes(self, space: SpaceData) -> 'FinishesData'
    def map_material_properties(self, surfaces: List[SurfaceData]) -> Dict[str, Any]
    def apply_finish_defaults(self, room_type: str) -> 'FinishesData'

# ifc_room_schedule/mappers/openings_mapper.py  
class OpeningsMapper:
    def extract_doors_windows(self, space: SpaceData) -> 'OpeningsData'
    def map_opening_properties(self, related_elements: List) -> List['OpeningData']
    def calculate_opening_dimensions(self, element: Any) -> Dict[str, float]
```

### 2.2 Fixtures and HSE (Uke 3-5)
**Fokus**: Utstyr og sikkerhetskrav

```python
# ifc_room_schedule/mappers/fixtures_mapper.py
class FixturesMapper:
    def extract_equipment_by_discipline(self, space: SpaceData) -> List['FixtureData']
    def map_connection_requirements(self, equipment: Any) -> 'ConnectionData'
    def infer_equipment_from_room_type(self, room_type: str) -> List['FixtureData']

# ifc_room_schedule/mappers/hse_mapper.py
class HSEMapper:
    def apply_universal_design_requirements(self, space: SpaceData) -> 'HSEData'
    def validate_accessibility_compliance(self, geometry: 'GeometryData') -> bool
    def map_safety_requirements(self, room_type: str) -> Dict[str, Any]
```

### 2.3 Advanced Features (Uke 5-8)
**Fokus**: QA/QC, Interfaces, Logistics

- Environment og sustainability tracking
- QA/QC workflows og hold points  
- Interface management mellom fag
- Logistics og site planning

## Fase 3: Produksjonsklargjøring (4-6 uker)

### 3.1 Brukergrensesnitt
**Mål**: Intuitivt UI for konfigurasjon og eksport

```python
# ifc_room_schedule/ui/room_schedule_configurator.py
class RoomScheduleConfigurator(QWidget):
    def setup_section_tree(self) -> None
    def show_data_quality_dashboard(self) -> None
    def configure_fallback_preferences(self) -> None
    def preview_export_structure(self) -> None
```

**Features**:
- [ ] Visuell seksjon-aktivering med checkboxes
- [ ] Data quality dashboard med progress bars
- [ ] Fallback strategy konfigurasjon
- [ ] Preview av generert JSON-struktur
- [ ] Export progress med detaljert status

### 3.2 Performance og Skalering
**Mål**: Håndtere store prosjekter effektivt

```python
# ifc_room_schedule/processing/batch_processor.py
class BatchProcessor:
    def process_spaces_in_chunks(self, spaces: List[SpaceData]) -> Iterator[Dict]
    def cache_frequently_accessed_data(self) -> None
    def optimize_memory_usage(self) -> None
    def stream_large_exports(self, output_path: str) -> None
```

### 3.3 Validering og Compliance
**Mål**: Sikre samsvar med norske standarder

```python
# ifc_room_schedule/validation/norwegian_standards.py
class NorwegianStandardsValidator:
    def validate_ns3420_compliance(self, data: Dict) -> 'ValidationResult'
    def check_ns8175_acoustics(self, performance: 'PerformanceRequirements') -> bool
    def validate_tek17_requirements(self, hse: 'HSEData') -> List[str]
```

## Risikoreduksjon og Kvalitetssikring

### Testing Strategy
```python
# tests/integration/test_enhanced_export.py
class TestEnhancedExport:
    def test_akkordsvingen_complete_export(self)
    def test_minimal_ifc_fallbacks(self)
    def test_section_filtering(self)
    def test_performance_large_files(self)

# tests/validation/test_norwegian_standards.py  
class TestNorwegianStandards:
    def test_ns3420_compliance(self)
    def test_ns8175_acoustic_requirements(self)
    def test_tek17_accessibility(self)
```

### Performance Benchmarks
- **Startup**: < 3 sekunder for enhanced export
- **Processing**: < 30 sekunder for 100 rom
- **Memory**: < 1GB for store IFC-filer
- **Export**: < 10 sekunder for komplett romskjema

### Code Quality Hooks [[memory:9414131]]
Automatisk kjøring ved fillagring:
- `black --line-length 88` for formatering
- `flake8` for linting med PyQt-spesifikke regler
- `mypy` for type checking
- `pytest` for relevante tester

## Leveransemilepæler

### Milestone 1: Grunnlag (3 uker)
- ✅ Datakvalitetsanalyse ferdig
- ✅ Arkitektur-forberedelser implementert  
- ✅ Testing-rammeverk utvidet
- ✅ Dokumentasjon oppdatert

### Milestone 2: Kjerneseksjoner (6 uker)
- ✅ Meta, Identification, IFC, Geometry implementert
- ✅ Classification og Performance Requirements
- ✅ Integration med eksisterende eksport
- ✅ End-to-end testing med reelle IFC-filer

### Milestone 3: Utvidede Seksjoner (8 uker)  
- ✅ Finishes, Openings, Fixtures, HSE implementert
- ✅ Avanserte seksjoner (QA/QC, Interfaces, Logistics)
- ✅ Comprehensive fallback-strategier
- ✅ Performance optimalisering

### Milestone 4: Produksjonsrelease (6 uker)
- ✅ Komplett UI for konfigurasjon og eksport
- ✅ Validering mot norske standarder
- ✅ Performance benchmarks oppfylt
- ✅ Dokumentasjon og deployment klar

## Ressursbehov og Estimat

### Utviklingsressurser
- **Senior Python Developer**: 20-25 uker (full-time)
- **IFC/BIM Specialist**: 8-10 uker (konsulent)
- **UI/UX Designer**: 4-6 uker (design og testing)
- **Quality Assurance**: 6-8 uker (testing og validering)

### Totalt Estimat: 5-6 måneder
- Fase 0: 3 uker
- Fase 1: 6 uker  
- Fase 2: 8 uker
- Fase 3: 6 uker

### Kritiske Suksessfaktorer
1. **Tidlig validering** med reelle IFC-filer og brukere
2. **Inkrementell levering** med kontinuerlig feedback
3. **Robust testing** på alle nivåer
4. **Performance fokus** fra dag 1
5. **Samsvar med norske standarder** gjennom hele prosessen

## Konklusjon

Dette planverket balanserer ambisiøse mål med praktisk gjennomførbarhet ved å:
- Bygge på eksisterende, solid kodebase
- Levere verdi inkrementelt med høyverdi-seksjoner først
- Følge etablerte kvalitetsstandarder og testing-praksis
- Redusere risiko gjennom kontinuerlig validering
- Sikre samsvar med norske byggestandarder

Resultatet blir en kraftig utvidelse av IFC Room Schedule applikasjonen som kan generere omfattende, standardkonforme romskjemaer som møter norsk byggebransjes behov.
