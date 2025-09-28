# Design Document

## Overview

Applikasjonen fryser når den importerer IFC-filer på grunn av flere problemer i den nåværende implementeringen:

1. **Threading-problemer**: Progress dialog blokkerer main thread med `progress_dialog.exec()` mens worker thread kjører
2. **For strenge minnesjekker**: IFC file reader har for konservative minnekrav som blokkerer små filer
3. **Manglende timeout-håndtering**: Ingen timeout for lange operasjoner
4. **Ineffektiv ressurshåndtering**: Unødvendig kompleks threading for relativt små filer

Løsningen fokuserer på å forenkle threading-logikken, justere minnesjekker, og forbedre brukeropplevelsen under import.

## Architecture

### Current Architecture Issues
```
User clicks "Load IFC File"
    ↓
process_ifc_file() 
    ↓
extract_spaces_threaded()
    ↓
show_operation_progress() → Creates QThread + Worker
    ↓
progress_dialog.exec() → BLOCKS MAIN THREAD
    ↓
Worker runs in background → Can't update UI properly
    ↓
FREEZE: Main thread blocked, worker can't communicate
```

### New Architecture
```
User clicks "Load IFC File"
    ↓
process_ifc_file() 
    ↓
Smart loading decision:
    - Small files (<10MB): Direct loading with progress bar
    - Large files (>10MB): Threaded loading with non-blocking progress
    ↓
Proper UI updates and error handling
```

## Components and Interfaces

### 1. Enhanced IFC File Reader
**File**: `ifc_room_schedule/parser/ifc_file_reader.py`

**Changes**:
- Justere minnesjekker for å være mindre konservative
- Legge til timeout-håndtering for store filer
- Forbedre feilmeldinger

```python
class IfcFileReader:
    def load_file(self, file_path: str, timeout: int = 30) -> Tuple[bool, str]:
        # Adjusted memory checks:
        # - Files < 10MB: Always allow
        # - Files 10-100MB: Check available memory more reasonably
        # - Files > 100MB: Require explicit user confirmation
```

### 2. Simplified Threading Logic
**File**: `ifc_room_schedule/ui/main_window.py`

**Changes**:
- Fjerne blocking progress dialog
- Bruke QProgressBar i status bar i stedet
- Implementere timeout for operasjoner
- Forenkle worker thread kommunikasjon

```python
class MainWindow:
    def process_ifc_file_smart(self, file_path: str):
        file_size = os.path.getsize(file_path)
        
        if file_size < 10 * 1024 * 1024:  # < 10MB
            # Direct loading with progress bar
            self.load_file_directly(file_path)
        else:
            # Threaded loading with non-blocking progress
            self.load_file_threaded(file_path)
```

### 3. Non-blocking Progress Indication
**Implementation**:
- Bruke QProgressBar i status bar
- Implementere QTimer for timeout
- Legge til cancel-funksjonalitet

```python
def show_non_blocking_progress(self, title: str, operation_func):
    # Show progress in status bar instead of blocking dialog
    self.progress_bar.setVisible(True)
    self.progress_bar.setRange(0, 0)  # Indeterminate
    
    # Set timeout timer
    self.timeout_timer = QTimer()
    self.timeout_timer.timeout.connect(self.handle_operation_timeout)
    self.timeout_timer.start(30000)  # 30 second timeout
```

### 4. Improved Error Handling
**Changes**:
- Legge til timeout-håndtering
- Forbedre minnefeil-meldinger
- Implementere graceful degradation

## Data Models

### File Size Categories
```python
class FileSizeCategory(Enum):
    SMALL = "small"      # < 10MB - Direct loading
    MEDIUM = "medium"    # 10-50MB - Threaded with progress
    LARGE = "large"      # 50-100MB - Threaded with warning
    HUGE = "huge"        # > 100MB - Require confirmation
```

### Operation State
```python
@dataclass
class OperationState:
    is_running: bool = False
    operation_type: str = ""
    start_time: datetime = None
    timeout_seconds: int = 30
    can_cancel: bool = True
```

## Error Handling

### 1. Memory Error Handling
```python
def handle_memory_constraints(self, file_size: int) -> Tuple[bool, str]:
    """
    More reasonable memory checking:
    - < 10MB: Always allow
    - 10-50MB: Check if 2x file size available
    - 50-100MB: Check if 3x file size available + warn user
    - > 100MB: Require explicit confirmation
    """
```

### 2. Timeout Handling
```python
def handle_operation_timeout(self):
    """Handle operation timeout with user options."""
    recovery_options = {
        'wait_longer': 'Wait 30 more seconds',
        'cancel': 'Cancel operation',
        'force_direct': 'Try direct loading (may freeze)'
    }
```

### 3. Threading Error Recovery
```python
def handle_threading_error(self, error: Exception):
    """Fallback to direct loading if threading fails."""
    self.logger.warning(f"Threading failed, falling back to direct loading: {error}")
    return self.load_file_directly(self.current_file_path)
```

## Testing Strategy

### 1. File Size Testing
- Test med begge testfiler (AkkordSvingen 23_ARK.ifc ~2.4MB, DEICH_Test.ifc ~1.4MB)
- Verifiser at små filer lastes direkte uten threading
- Test timeout-funksjonalitet med store filer

### 2. Threading Testing
- Test at UI forblir responsiv under lasting
- Verifiser at cancel-funksjonalitet fungerer
- Test fallback til direct loading

### 3. Memory Testing
- Test minnesjekker med forskjellige filstørrelser
- Verifiser at testfilene ikke trigger minnefeil
- Test graceful degradation ved lav minne

### 4. Error Recovery Testing
- Test timeout-håndtering
- Test threading-feil recovery
- Test bruker-avbrytelse av operasjoner

## Implementation Approach

### Phase 1: Fix Memory Checks
1. Justere minnesjekker i `IfcFileReader.load_file()`
2. Gjøre sjekker mindre konservative for små filer
3. Test med eksisterende testfiler

### Phase 2: Simplify Threading
1. Implementere smart loading basert på filstørrelse
2. Fjerne blocking progress dialog
3. Bruke status bar progress i stedet

### Phase 3: Add Timeout Handling
1. Implementere timeout for alle operasjoner
2. Legge til cancel-funksjonalitet
3. Implementere fallback-strategier

### Phase 4: Improve Error Messages
1. Forbedre feilmeldinger for minneproblemer
2. Legge til bedre logging
3. Implementere recovery-alternativer

## Success Criteria

1. **Testfiler fungerer**: Begge testfiler (AkkordSvingen 23_ARK.ifc og DEICH_Test.ifc) skal laste uten å fryse
2. **UI responsivitet**: Brukergrensesnittet skal forbli responsivt under lasting
3. **Timeout-håndtering**: Operasjoner skal ha timeout og cancel-mulighet
4. **Minneoptimalisering**: Minnesjekker skal være rimelige for normale filer
5. **Feilhåndtering**: Tydelige feilmeldinger og recovery-alternativer