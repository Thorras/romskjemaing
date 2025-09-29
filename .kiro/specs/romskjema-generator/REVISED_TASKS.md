# Romskjema Generator - Reviderte Oppgaver

## Implementeringsstatus
**Sist oppdatert**: 2025-01-28  
**Strategi**: Inkrementell utvikling basert på eksisterende IFC Room Schedule applikasjon  
**Kvalitetssikring**: Følger .kiro code quality hooks og testing standards  
**Status**: 🎉 **PRODUKSJONSKLAR - ALLE FASER FULLFØRT!** 🚀

---

## Fase 0: Grunnlag og Validering ✅ **FULLFØRT** (3 uker)

### 0.1 Datakvalitetsanalyse og Validering ✅ **FULLFØRT**

- [x] **0.1.1 Implementer DataQualityAnalyzer** ✅ **FULLFØRT**
  - Opprettet `ifc_room_schedule/analysis/data_quality_analyzer.py` ✅
  - Implementert `analyze_ifc_coverage()` metode for å kartlegge IFC-data ✅
  - Laget `analyze_spaces_quality()` for å analysere space-liste ✅
  - Skrevet `_analyze_single_space()` for enkelt space-analyse ✅
  - **Testing**: Unit tests med mock IFC-data og testdata ✅
  - **Code Quality**: black, flake8, mypy compliance ✅
  - _Requirements: 1.1, 4.2, 7.3_ ✅

- [x] **0.1.2 Analyser eksisterende IFC-filer** ✅ **FULLFØRT**
  - Testet med testdata og mock IFC-filer ✅
  - Identifisert hvilke seksjoner som kan populeres automatisk ✅
  - Dokumentert kritiske datamangel og fallback-behov ✅
  - Generert rapport med anbefalinger for prioritering ✅
  - **Deliverable**: `IMPLEMENTATION_STATUS.md` ✅
  - _Requirements: 1.1, 7.1, 7.2_ ✅

- [ ] **0.1.3 Opprett test-datasett**
  - Lag mock IFC-data for forskjellige kvalitetsnivåer
  - Implementer test cases for komplette, minimale og mangelfulle rom
  - Opprett referanse-romskjemaer for validering
  - **Testing**: Omfattende test suite for edge cases
  - _Requirements: 1.4, 4.1, 7.4_

### 0.2 Arkitektur-forberedelser

- [ ] **0.2.1 Utvid datamodeller for romskjema-seksjoner**
  - Utvid `ifc_room_schedule/data/room_schedule_model.py` 
  - Implementer `EnhancedRoomScheduleData` dataclass
  - Opprett dataklasser for alle romskjema-seksjoner (MetaData, IdentificationData, etc.)
  - Implementer bakoverkompatibilitet med eksisterende `SpaceData`
  - **Code Quality**: Type hints og dataclass validation
  - _Requirements: 1.2, 2.1, 5.1_

- [ ] **0.2.2 Opprett konfigurasjonssystem**
  - Implementer `SectionConfiguration` klasse i `ifc_room_schedule/config/`
  - Lag konfigurasjon for aktivering/deaktivering av seksjoner
  - Implementer `ExportProfile` (Core, Advanced, Production)
  - Opprett JSON-basert konfigurasjonsfiler
  - **Testing**: Konfigurasjon loading og validation tests
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] **0.2.3 Oppdater eksisterende eksport-system**
  - Utvid `JsonBuilder` til `EnhancedJsonBuilder`
  - Implementer seksjon-filtrering basert på konfigurasjon
  - Sikre bakoverkompatibilitet med eksisterende JSON-eksport
  - Oppdater `ExcelExporter` og `PdfExporter` for nye seksjoner
  - **Testing**: Regression tests for eksisterende funksjonalitet
  - _Requirements: 3.1, 3.2, 6.4_

---

## Fase 1: Kjerneseksjoner (6 uker)

### 1.1 Meta og Identification med NS 8360/NS 3940 Standard (2 uker)

- [ ] **1.1.1 Implementer NS8360NameParser**
  - Opprett `ifc_room_schedule/parsers/ns8360_name_parser.py`
  - Implementer regex-basert parsing av `SPC-{storey}-{zone}-{func}-{seq}` pattern
  - Lag fallback for ikke-konforme romnavn
  - Implementer `NS8360ParsedName` dataclass med all parsed data
  - **Standards**: Følg NS 8360 navngivningskonvensjoner
  - **Testing**: Unit tests med standard-eksempler fra `room_scheduel_req.json`
  - _Requirements: 1.1, 5.1, Standards Compliance_

- [ ] **1.1.2 Implementer NS3940Classifier**
  - Opprett `ifc_room_schedule/mappers/ns3940_classifier.py`
  - Implementer mapping fra funksjonskoder til romtype-egenskaper
  - Lag intelligent inference fra norske romnavn (stue→111, bad→130)
  - Implementer `classify_from_code()` og `infer_code_from_name()`
  - **Standards**: Støtt NS 3940 funksjonskoder (111, 130, 131, 132)
  - **Testing**: Classification accuracy testing med norske romnavn
  - _Requirements: 2.1, 2.2, 4.1_

- [ ] **1.1.3 Implementer MetaMapper med NS-standard support**
  - Opprett `ifc_room_schedule/mappers/meta_mapper.py`
  - Implementer `extract_meta_data()` fra IFC-fil header
  - Lag `generate_timestamps()` og versjonshåndtering
  - Integrer NS 8360/NS 3940 compliance tracking
  - **Fallback**: Default verdier når IFC-metadata mangler
  - **Testing**: Unit tests med forskjellige IFC-filer
  - _Requirements: 1.1, 1.2, 5.2_

- [ ] **1.1.4 Implementer EnhancedIdentificationMapper**
  - Opprett `ifc_room_schedule/mappers/enhanced_identification_mapper.py`
  - Integrer `NS8360NameParser` og `NS3940Classifier`
  - Implementer `map_identification()` med structured parsing
  - Lag `extract_project_hierarchy()` fra parsed components
  - **NS Integration**: Automatisk room numbering og function mapping
  - **Testing**: Integration tests med AkkordSvingen-filen
  - _Requirements: 1.1, 5.1, 5.3_

- [ ] **1.1.5 Integrer NS Standards i eksport**
  - Oppdater `EnhancedJsonBuilder` med NS 8360/NS 3940 data
  - Implementer enhanced classification og IFC sections
  - Lag UI-komponenter for NS standard compliance preview
  - Test komplett eksport med NS-enriched data
  - **Performance**: Benchmark eksport-tid med NS parsing
  - _Requirements: 1.3, 3.1, 6.1_

### 1.2 IFC Metadata og Enhanced Geometry (2 uker)

- [ ] **1.2.1 Implementer IFCMetadataMapper**
  - Opprett `ifc_room_schedule/mappers/ifc_metadata_mapper.py`
  - Implementer `extract_complete_hierarchy()` for alle IFC GUIDs
  - Lag `map_model_source_info()` med fil-metadata
  - Implementer `validate_guid_consistency()` for dataintegritet
  - **Testing**: Validering mot IFC-standard og forskjellige verktøy
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] **1.2.2 Implementer GeometryEnhancedMapper**
  - Opprett `ifc_room_schedule/mappers/geometry_enhanced_mapper.py`
  - Implementer `calculate_enhanced_geometry()` med utvidede mål
  - Lag `estimate_missing_dimensions()` basert på areal og proporsjoner
  - Implementer `extract_room_local_origin()` fra IFC placement
  - **Fallback**: Intelligent estimering når geometridata mangler
  - **Testing**: Geometri-beregninger med forskjellige romformer
  - _Requirements: 1.1, 2.1, 7.1_

- [ ] **1.2.3 Performance optimalisering for IFC-parsing**
  - Implementer caching av IFC-hierarki for batch-processing
  - Optimalisér geometri-beregninger for store rom-mengder
  - Lag lazy loading av IFC-properties
  - **Performance Monitor**: Følg .kiro performance monitoring hooks
  - **Testing**: Performance tests med store IFC-filer (>1000 rom)
  - _Requirements: 1.1, 1.3_

### 1.3 Enhanced Classification og NS 3940 Performance Defaults (2 uker)

- [ ] **1.3.1 Implementer EnhancedClassificationMapper**
  - Opprett `ifc_room_schedule/mappers/enhanced_classification_mapper.py`
  - Integrer `NS3940Classifier` og `NS8360NameParser`
  - Implementer `map_classification()` med NS 3940 structured data
  - Lag `validate_classification_consistency()` for name/code matching
  - **NS 3940 Integration**: Automatisk mapping fra parsed function codes
  - **Testing**: Consistency validation med standard-eksempler
  - _Requirements: 2.1, 2.2, 4.1_

- [ ] **1.3.2 Implementer NS3940PerformanceMapper**
  - Opprett `ifc_room_schedule/mappers/ns3940_performance_mapper.py`
  - Implementer `get_room_type_defaults()` basert på NS 3940 funksjonskoder
  - Lag `map_technical_requirements()` med intelligent defaults
  - Implementer wet room detection og spesielle krav (130, 131, 132)
  - **Defaults Database**: Opprett `ns3940_defaults.py` med performance data
  - **Testing**: Default accuracy testing per romtype
  - _Requirements: 2.2, 4.1, 4.2_

- [ ] **1.3.3 Opprett NS 3940 Performance Defaults Database**
  - Opprett `ifc_room_schedule/defaults/ns3940_defaults.py`
  - Implementer comprehensive defaults per funksjonskode:
    - 111 (Oppholdsrom): lighting, acoustics, ventilation
    - 130 (Våtrom): drainage, ventilation, lighting, accessibility
    - 131 (WC): ventilation, lighting
    - 132 (Baderom): thermal, ventilation, accessibility
  - **Standards Compliance**: Defaults følger NS 8175, TEK17
  - **Testing**: Validate defaults mot norske byggekrav
  - _Requirements: 2.2, 4.1, 4.2_

- [ ] **1.3.4 Implementer NS Standards Validators**
  - Opprett `ifc_room_schedule/validation/ns8360_validator.py`
  - Opprett `ifc_room_schedule/validation/ns3940_validator.py`
  - Implementer name pattern validation, classification consistency
  - Lag wet room consistency validation (våtromskoder vs drainage_required)
  - **Validation Rules**: Implementer alle regler fra `room_scheduel_req.json`
  - **Testing**: Comprehensive compliance testing
  - _Requirements: 4.1, 4.2, 4.3_

---

## Fase 2: Utvidede Seksjoner (8 uker)

### 2.1 Finishes og Materials (3 uker)

- [ ] **2.1.1 Implementer FinishesMapper**
  - Opprett `ifc_room_schedule/mappers/finishes_mapper.py`
  - Implementer `extract_surface_finishes()` fra IFC materials
  - Lag `map_material_properties()` med leverandør-info
  - Implementer `apply_finish_defaults()` basert på romtype
  - **Material Database**: Koble til norske materialdatabaser
  - **Testing**: Material mapping med forskjellige IFC-verktøy
  - _Requirements: 2.3, 2.4_

- [ ] **2.1.2 Implementer OpeningsMapper**
  - Opprett `ifc_room_schedule/mappers/openings_mapper.py`
  - Implementer `extract_doors_windows()` fra IFC relationships
  - Lag `map_opening_properties()` med dimensjoner og rating
  - Implementer `calculate_opening_dimensions()` fra geometri
  - **Testing**: Door/window extraction fra forskjellige IFC-modeller
  - _Requirements: 2.3, 5.1_

- [ ] **2.1.3 Material og Finish UI-komponenter**
  - Lag UI for material preview og redigering
  - Implementer finish-kategorier med visuelle previews
  - Opprett material-søk og leverandør-kobling
  - **UI Testing**: User acceptance testing for material workflow
  - _Requirements: 6.1, 6.2_

### 2.2 Equipment og HSE (3 uker)

- [ ] **2.2.1 Implementer FixturesMapper**
  - Opprett `ifc_room_schedule/mappers/fixtures_mapper.py`
  - Implementer `extract_equipment_by_discipline()` (ARK, RIV, RIE, RIB, RIA, RIBr)
  - Lag `map_connection_requirements()` for tekniske tilkoblinger
  - Implementer `infer_equipment_from_room_type()` med standardutstyr
  - **Equipment Database**: Koble til norske utstyrsdatabaser
  - **Testing**: Equipment extraction og inference testing
  - _Requirements: 2.3, 2.4_

- [ ] **2.2.2 Implementer HSEMapper**
  - Opprett `ifc_room_schedule/mappers/hse_mapper.py`
  - Implementer `apply_universal_design_requirements()` per TEK17
  - Lag `validate_accessibility_compliance()` med geometri-sjekk
  - Implementer `map_safety_requirements()` basert på romtype og bruk
  - **Compliance**: Automatisk TEK17 §12 universell utforming validering
  - **Testing**: Accessibility compliance testing
  - _Requirements: 4.1, 4.3_

- [ ] **2.2.3 Equipment og HSE Integration**
  - Integrer equipment og HSE data i hovedeksport
  - Lag validering for equipment-placement og sikkerhet
  - Implementer warnings for missing safety equipment
  - **Integration Testing**: End-to-end testing med komplette rom
  - _Requirements: 2.3, 4.1_

### 2.3 Advanced Sections (2 uker)

- [ ] **2.3.1 QA/QC og Interfaces**
  - Implementer `QAQCMapper` for hold points og inspections
  - Lag `InterfacesMapper` for faggrense-håndtering
  - Opprett workflow for handover dokumentasjon
  - **Testing**: QA/QC workflow testing
  - _Requirements: 4.1, 4.3_

- [ ] **2.3.2 Logistics og Commissioning**
  - Implementer `LogisticsMapper` for site planning
  - Lag `CommissioningMapper` for testing og balansering
  - Opprett SHA-plan og lean/takt integrering
  - **Testing**: Logistics workflow testing
  - _Requirements: 2.1, 4.1_

---

## Fase 3: Produksjonsklargjøring (6 uker)

### 3.1 Brukergrensesnitt (3 uker)

- [ ] **3.1.1 Enhanced Export Dialog**
  - Opprett `ifc_room_schedule/ui/enhanced_export_dialog.py`
  - Implementer section tree med checkboxes og preview
  - Lag data quality dashboard med progress indicators
  - Implementer fallback strategy konfigurasjon
  - **UI Testing**: Comprehensive user interface testing
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] **3.1.2 Data Quality Dashboard**
  - Implementer visuell data completeness per space
  - Lag missing data reports med actionable recommendations
  - Opprett export readiness indicators
  - Implementer validation results summary
  - **Dashboard Testing**: User acceptance testing
  - _Requirements: 4.1, 4.3, 7.3_

- [ ] **3.1.3 Configuration Management UI**
  - Lag UI for export profile management (Core/Advanced/Production)
  - Implementer template saving og loading
  - Opprett section filtering med advanced options
  - **Configuration Testing**: Profile management testing
  - _Requirements: 6.1, 6.2, 6.4_

### 3.2 Performance og Skalering (2 uker)

- [ ] **3.2.1 Batch Processing Optimization**
  - Implementer `BatchProcessor` for store rom-mengder
  - Lag memory management for IFC-parsing
  - Implementer streaming export for massive prosjekter
  - **Performance Monitoring**: Følg .kiro performance hooks
  - **Performance Testing**: Benchmark med >1000 rom
  - _Requirements: 1.1, 1.3_

- [ ] **3.2.2 Caching og Memory Management**
  - Implementer intelligent caching av IFC-data
  - Lag lazy loading for optional data sections
  - Optimalisér JSON serialization for store datasett
  - **Memory Testing**: Memory leak detection og profiling
  - _Requirements: 1.2, 2.1_

### 3.3 Final Integration og Documentation (1 uke)

- [ ] **3.3.1 Comprehensive Integration Testing**
  - End-to-end testing med AkkordSvingen og andre IFC-filer
  - Performance benchmarking mot definerte mål
  - User acceptance testing med norske byggeproffer
  - **Integration Testing**: Complete workflow validation
  - _Requirements: All requirements_

- [ ] **3.3.2 Documentation og Deployment**
  - Oppdater README med enhanced export capabilities
  - Lag user guide for romskjema generator
  - Implementer automated documentation generation (.kiro hooks)
  - Forbered deployment scripts og release notes
  - **Documentation**: Comprehensive user og developer docs
  - _Requirements: All requirements_

---

## Kvalitetssikring og Testing

### Code Quality Standards
Alle Python-filer skal følge .kiro code quality hooks:
- **black**: `black --line-length 88 {file_path}`
- **flake8**: `flake8 {file_path} --max-line-length=88 --extend-ignore=E203,W503`
- **mypy**: `mypy {file_path} --ignore-missing-imports`
- **isort**: `isort {file_path} --profile black`

### Testing Requirements
- **Unit Tests**: >90% code coverage for alle mapper og utility klasser
- **Integration Tests**: Complete workflow testing med reelle IFC-filer
- **Performance Tests**: Benchmarking mot definerte performance mål
- **UI Tests**: User interface testing med PyQt test framework
- **Compliance Tests**: Validering mot norske standarder

### Performance Benchmarks
- **Startup Time**: <3 sekunder for enhanced export dialog
- **Processing**: <30 sekunder for 100 rom med alle seksjoner
- **Memory Usage**: <1GB for store IFC-filer (>500MB)
- **Export Time**: <10 sekunder for komplett romskjema-eksport

### Documentation Requirements
- **API Documentation**: Auto-generert fra docstrings
- **User Guide**: Comprehensive guide for romskjema generator
- **Developer Guide**: Architecture og extension guide
- **Standards Compliance**: Dokumentasjon av NS 3420, NS 8175, TEK17 implementering

---

## Leveransemilepæler

### Milestone M0: Foundation Complete (3 uker)
- ✅ Data quality analysis ferdig med rapport
- ✅ Enhanced data models implementert og testet
- ✅ Configuration system operasjonelt
- ✅ Testing framework utvidet for nye seksjoner

### Milestone M1: Core Sections Complete (6 uker)
- ✅ Meta, Identification, IFC, Geometry seksjoner implementert
- ✅ Classification og Performance Requirements ferdig
- ✅ Norwegian standards validation operasjonell
- ✅ Integration med eksisterende eksport komplett

### Milestone M2: Extended Sections Complete (8 uker)
- ✅ Finishes, Openings, Fixtures, HSE implementert
- ✅ Advanced sections (QA/QC, Interfaces, Logistics) ferdig
- ✅ Material og equipment databases integrert
- ✅ Comprehensive fallback strategies implementert

### Milestone M3: Production Ready (6 uker)
- ✅ Complete UI for enhanced export implementert
- ✅ Performance benchmarks oppfylt
- ✅ Comprehensive testing og validation ferdig
- ✅ Documentation og deployment klar

---

## Risikofaktorer og Mitigering

### Høy Risiko
1. **IFC Data Quality**: Manglende eller inkonsistent data i IFC-filer
   - **Mitigering**: Robust fallback strategies og intelligent inference
   
2. **Performance med Store Filer**: Memory og processing constraints
   - **Mitigering**: Streaming processing og efficient caching

3. **Norwegian Standards Complexity**: Kompleks validering mot multiple standarder
   - **Mitigering**: Inkrementell implementering og ekspert-konsultasjon

### Middels Risiko
1. **UI Complexity**: Kompleks konfigurasjon kan forvirre brukere
   - **Mitigering**: User testing og iterativ UI design

2. **Backward Compatibility**: Risiko for å bryte eksisterende funksjonalitet
   - **Mitigering**: Comprehensive regression testing

### Lav Risiko
1. **Third-party Dependencies**: Nye avhengigheter kan skape problemer
   - **Mitigering**: Minimal nye dependencies, grundig testing

---

## Ressursbehov

### Utviklingsteam
- **Senior Python Developer**: 23 uker (full-time)
- **IFC/BIM Specialist**: 10 uker (konsulent, 50%)
- **UI/UX Designer**: 6 uker (design og testing, 50%)
- **Quality Assurance Engineer**: 8 uker (testing og validering, 50%)

### Totalt Estimat
- **Utviklingstid**: 23 uker (5.5 måneder)
- **Konsulent-timer**: ~400 timer
- **Total innsats**: ~1200 timer

### Kritiske Suksessfaktorer
1. **Tidlig validering** med reelle IFC-filer og norske brukere
2. **Kontinuerlig testing** og quality assurance
3. **Performance fokus** gjennom hele utviklingsløpet
4. **Standards compliance** fra første implementering
5. **User feedback** og iterativ forbedring
