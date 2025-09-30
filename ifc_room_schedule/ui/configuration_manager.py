"""
Configuration Manager UI

Advanced configuration management for export profiles, settings, and preferences.
"""

import json
import os
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QTabWidget, QListWidget, QListWidgetItem,
    QTextEdit, QFileDialog, QMessageBox, QSplitter, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QIcon, QPixmap


class ExportProfileManager:
    """Manager for export profiles."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize export profile manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file or os.path.join(os.path.expanduser("~"), ".romskjema_profiles.json")
        self.profiles = self._load_profiles()
        self._ensure_default_profiles()
    
    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load profiles from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}
    
    def _save_profiles(self):
        """Save profiles to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise Exception(f"Failed to save profiles: {str(e)}")
    
    def _ensure_default_profiles(self):
        """Ensure default profiles exist."""
        default_profiles = {
            "core": {
                "name": "Core Export",
                "description": "Basic room data export with identification and classification",
                "sections": ["identification", "ifc_metadata", "geometry", "classification"],
                "settings": {
                    "include_metadata": True,
                    "pretty_print": True,
                    "validate_data": True
                }
            },
            "advanced": {
                "name": "Advanced Export",
                "description": "Comprehensive export with traditional sections",
                "sections": ["identification", "ifc_metadata", "geometry", "classification", 
                           "surfaces", "space_boundaries", "relationships"],
                "settings": {
                    "include_metadata": True,
                    "pretty_print": True,
                    "validate_data": True
                }
            },
            "production": {
                "name": "Production Export",
                "description": "Full production export with all Phase 2B and 2C sections",
                "sections": ["identification", "ifc_metadata", "geometry", "classification",
                           "performance_requirements", "finishes", "openings", "fixtures_and_equipment",
                           "hse_and_accessibility", "qa_qc", "interfaces", "logistics_and_site",
                           "commissioning", "surfaces", "space_boundaries", "relationships"],
                "settings": {
                    "include_metadata": True,
                    "pretty_print": True,
                    "validate_data": True
                }
            }
        }
        
        for profile_id, profile_data in default_profiles.items():
            if profile_id not in self.profiles:
                self.profiles[profile_id] = profile_data
        
        self._save_profiles()
    
    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get profile by ID."""
        return self.profiles.get(profile_id)
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all profiles."""
        return self.profiles.copy()
    
    def save_profile(self, profile_id: str, profile_data: Dict[str, Any]):
        """Save profile."""
        self.profiles[profile_id] = profile_data
        self._save_profiles()
    
    def delete_profile(self, profile_id: str):
        """Delete profile."""
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            self._save_profiles()
    
    def duplicate_profile(self, source_id: str, new_id: str, new_name: str):
        """Duplicate existing profile."""
        if source_id in self.profiles:
            profile_data = self.profiles[source_id].copy()
            profile_data["name"] = new_name
            self.profiles[new_id] = profile_data
            self._save_profiles()


class ProfileEditorWidget(QWidget):
    """Widget for editing export profiles."""
    
    profile_saved = pyqtSignal(str, dict)  # profile_id, profile_data
    profile_deleted = pyqtSignal(str)  # profile_id
    
    def __init__(self, profile_manager: ExportProfileManager, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.current_profile_id = None
        self.setup_ui()
        self.load_profiles()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Export Profile Manager")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Profile selection
        profile_group = QGroupBox("Profile Selection")
        profile_layout = QHBoxLayout(profile_group)
        
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self._on_profile_selected)
        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo)
        
        self.new_profile_btn = QPushButton("New Profile")
        self.new_profile_btn.clicked.connect(self._new_profile)
        profile_layout.addWidget(self.new_profile_btn)
        
        self.duplicate_btn = QPushButton("Duplicate")
        self.duplicate_btn.clicked.connect(self._duplicate_profile)
        profile_layout.addWidget(self.duplicate_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_profile)
        profile_layout.addWidget(self.delete_btn)
        
        layout.addWidget(profile_group)
        
        # Profile editor
        editor_group = QGroupBox("Profile Editor")
        editor_layout = QFormLayout(editor_group)
        
        # Basic info
        self.name_edit = QLineEdit()
        editor_layout.addRow("Name:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        editor_layout.addRow("Description:", self.description_edit)
        
        # Sections
        self.sections_list = QListWidget()
        self.sections_list.setMaximumHeight(150)
        editor_layout.addRow("Sections:", self.sections_list)
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.include_metadata_check = QCheckBox()
        self.include_metadata_check.setChecked(True)
        settings_layout.addRow("Include Metadata:", self.include_metadata_check)
        
        self.pretty_print_check = QCheckBox()
        self.pretty_print_check.setChecked(True)
        settings_layout.addRow("Pretty Print JSON:", self.pretty_print_check)
        
        self.validate_data_check = QCheckBox()
        self.validate_data_check.setChecked(True)
        settings_layout.addRow("Validate Data:", self.validate_data_check)
        
        editor_layout.addRow(settings_group)
        
        layout.addWidget(editor_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Profile")
        self.save_btn.clicked.connect(self._save_profile)
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_profile)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def load_profiles(self):
        """Load profiles into combo box."""
        self.profile_combo.clear()
        profiles = self.profile_manager.get_all_profiles()
        
        for profile_id, profile_data in profiles.items():
            display_name = f"{profile_data.get('name', profile_id)} ({profile_id})"
            self.profile_combo.addItem(display_name, profile_id)
    
    def _on_profile_selected(self, display_name: str):
        """Handle profile selection."""
        if not display_name:
            return
        
        profile_id = self.profile_combo.currentData()
        if not profile_id:
            return
        
        profile = self.profile_manager.get_profile(profile_id)
        if profile:
            self.current_profile_id = profile_id
            self._load_profile(profile)
    
    def _load_profile(self, profile: Dict[str, Any]):
        """Load profile data into editor."""
        self.name_edit.setText(profile.get("name", ""))
        self.description_edit.setPlainText(profile.get("description", ""))
        
        # Load sections
        self.sections_list.clear()
        sections = profile.get("sections", [])
        for section in sections:
            item = QListWidgetItem(section)
            item.setCheckState(Qt.Checked)
            self.sections_list.addItem(item)
        
        # Load settings
        settings = profile.get("settings", {})
        self.include_metadata_check.setChecked(settings.get("include_metadata", True))
        self.pretty_print_check.setChecked(settings.get("pretty_print", True))
        self.validate_data_check.setChecked(settings.get("validate_data", True))
    
    def _new_profile(self):
        """Create new profile."""
        self.current_profile_id = None
        self.name_edit.clear()
        self.description_edit.clear()
        self.sections_list.clear()
        self.include_metadata_check.setChecked(True)
        self.pretty_print_check.setChecked(True)
        self.validate_data_check.setChecked(True)
    
    def _duplicate_profile(self):
        """Duplicate current profile."""
        if not self.current_profile_id:
            QMessageBox.warning(self, "No Profile", "Please select a profile to duplicate.")
            return
        
        # Get new profile ID and name
        new_id, ok = QInputDialog.getText(self, "Duplicate Profile", "Enter new profile ID:")
        if not ok or not new_id:
            return
        
        new_name, ok = QInputDialog.getText(self, "Duplicate Profile", "Enter new profile name:")
        if not ok or not new_name:
            return
        
        try:
            self.profile_manager.duplicate_profile(self.current_profile_id, new_id, new_name)
            self.load_profiles()
            QMessageBox.information(self, "Success", f"Profile duplicated as '{new_name}'")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to duplicate profile: {str(e)}")
    
    def _delete_profile(self):
        """Delete current profile."""
        if not self.current_profile_id:
            QMessageBox.warning(self, "No Profile", "Please select a profile to delete.")
            return
        
        # Don't allow deletion of default profiles
        if self.current_profile_id in ["core", "advanced", "production"]:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete default profiles.")
            return
        
        reply = QMessageBox.question(
            self, "Delete Profile", 
            f"Are you sure you want to delete profile '{self.current_profile_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.profile_manager.delete_profile(self.current_profile_id)
                self.load_profiles()
                self._new_profile()  # Clear editor
                self.profile_deleted.emit(self.current_profile_id)
                QMessageBox.information(self, "Success", "Profile deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete profile: {str(e)}")
    
    def _save_profile(self):
        """Save current profile."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a profile name.")
            return
        
        # Get profile ID
        if not self.current_profile_id:
            profile_id = name.lower().replace(" ", "_")
        else:
            profile_id = self.current_profile_id
        
        # Get sections
        sections = []
        for i in range(self.sections_list.count()):
            item = self.sections_list.item(i)
            if item.checkState() == Qt.Checked:
                sections.append(item.text())
        
        # Create profile data
        profile_data = {
            "name": name,
            "description": self.description_edit.toPlainText().strip(),
            "sections": sections,
            "settings": {
                "include_metadata": self.include_metadata_check.isChecked(),
                "pretty_print": self.pretty_print_check.isChecked(),
                "validate_data": self.validate_data_check.isChecked()
            }
        }
        
        try:
            self.profile_manager.save_profile(profile_id, profile_data)
            self.load_profiles()
            self.current_profile_id = profile_id
            self.profile_saved.emit(profile_id, profile_data)
            QMessageBox.information(self, "Success", "Profile saved successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")
    
    def _reset_profile(self):
        """Reset profile to original state."""
        if self.current_profile_id:
            profile = self.profile_manager.get_profile(self.current_profile_id)
            if profile:
                self._load_profile(profile)


class SettingsManager:
    """Manager for application settings."""
    
    def __init__(self):
        """Initialize settings manager."""
        self.settings = QSettings("RomskjemaGenerator", "Settings")
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default settings."""
        defaults = {
            "default_export_profile": "production",
            "default_output_directory": os.path.expanduser("~"),
            "auto_save_profiles": True,
            "show_advanced_options": False,
            "cache_enabled": True,
            "cache_memory_mb": 512,
            "cache_disk_mb": 1024,
            "batch_chunk_size": 100,
            "max_memory_mb": 1024,
            "log_level": "INFO",
            "auto_validate_data": True,
            "backup_enabled": True,
            "backup_retention_days": 30
        }
        
        for key, value in defaults.items():
            if not self.settings.contains(key):
                self.settings.setValue(key, value)
    
    def get(self, key: str, default=None):
        """Get setting value."""
        return self.settings.value(key, default)
    
    def set(self, key: str, value):
        """Set setting value."""
        self.settings.setValue(key, value)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        settings_dict = {}
        for key in self.settings.allKeys():
            settings_dict[key] = self.settings.value(key)
        return settings_dict


class SettingsWidget(QWidget):
    """Widget for application settings."""
    
    settings_changed = pyqtSignal(dict)  # settings_dict
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Application Settings")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # General settings
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "General")
        
        # Export settings
        export_tab = self._create_export_tab()
        tab_widget.addTab(export_tab, "Export")
        
        # Performance settings
        performance_tab = self._create_performance_tab()
        tab_widget.addTab(performance_tab, "Performance")
        
        # Advanced settings
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.default_profile_combo = QComboBox()
        self.default_profile_combo.addItems(["core", "advanced", "production"])
        layout.addRow("Default Export Profile:", self.default_profile_combo)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_btn = QPushButton("Browse...")
        self.output_dir_btn.clicked.connect(self._browse_output_dir)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.output_dir_btn)
        layout.addRow("Default Output Directory:", output_layout)
        
        self.auto_save_check = QCheckBox()
        layout.addRow("Auto-save Profiles:", self.auto_save_check)
        
        self.show_advanced_check = QCheckBox()
        layout.addRow("Show Advanced Options:", self.show_advanced_check)
        
        return widget
    
    def _create_export_tab(self) -> QWidget:
        """Create export settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.auto_validate_check = QCheckBox()
        layout.addRow("Auto-validate Data:", self.auto_validate_check)
        
        self.backup_enabled_check = QCheckBox()
        layout.addRow("Enable Backup:", self.backup_enabled_check)
        
        self.backup_retention_spin = QSpinBox()
        self.backup_retention_spin.setRange(1, 365)
        self.backup_retention_spin.setSuffix(" days")
        layout.addRow("Backup Retention:", self.backup_retention_spin)
        
        return widget
    
    def _create_performance_tab(self) -> QWidget:
        """Create performance settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.cache_enabled_check = QCheckBox()
        layout.addRow("Enable Caching:", self.cache_enabled_check)
        
        self.cache_memory_spin = QSpinBox()
        self.cache_memory_spin.setRange(64, 4096)
        self.cache_memory_spin.setSuffix(" MB")
        layout.addRow("Cache Memory Limit:", self.cache_memory_spin)
        
        self.cache_disk_spin = QSpinBox()
        self.cache_disk_spin.setRange(128, 8192)
        self.cache_disk_spin.setSuffix(" MB")
        layout.addRow("Cache Disk Limit:", self.cache_disk_spin)
        
        self.batch_chunk_spin = QSpinBox()
        self.batch_chunk_spin.setRange(10, 1000)
        layout.addRow("Batch Chunk Size:", self.batch_chunk_spin)
        
        self.max_memory_spin = QSpinBox()
        self.max_memory_spin.setRange(256, 8192)
        self.max_memory_spin.setSuffix(" MB")
        layout.addRow("Max Memory Usage:", self.max_memory_spin)
        
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout.addRow("Log Level:", self.log_level_combo)
        
        return widget
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_edit.setText(directory)
    
    def load_settings(self):
        """Load settings into UI."""
        settings = self.settings_manager.get_all()
        
        # General settings
        self.default_profile_combo.setCurrentText(settings.get("default_export_profile", "production"))
        self.output_dir_edit.setText(settings.get("default_output_directory", ""))
        self.auto_save_check.setChecked(settings.get("auto_save_profiles", True))
        self.show_advanced_check.setChecked(settings.get("show_advanced_options", False))
        
        # Export settings
        self.auto_validate_check.setChecked(settings.get("auto_validate_data", True))
        self.backup_enabled_check.setChecked(settings.get("backup_enabled", True))
        self.backup_retention_spin.setValue(settings.get("backup_retention_days", 30))
        
        # Performance settings
        self.cache_enabled_check.setChecked(settings.get("cache_enabled", True))
        self.cache_memory_spin.setValue(settings.get("cache_memory_mb", 512))
        self.cache_disk_spin.setValue(settings.get("cache_disk_mb", 1024))
        self.batch_chunk_spin.setValue(settings.get("batch_chunk_size", 100))
        self.max_memory_spin.setValue(settings.get("max_memory_mb", 1024))
        
        # Advanced settings
        self.log_level_combo.setCurrentText(settings.get("log_level", "INFO"))
    
    def _save_settings(self):
        """Save settings."""
        settings = {
            "default_export_profile": self.default_profile_combo.currentText(),
            "default_output_directory": self.output_dir_edit.text(),
            "auto_save_profiles": self.auto_save_check.isChecked(),
            "show_advanced_options": self.show_advanced_check.isChecked(),
            "auto_validate_data": self.auto_validate_check.isChecked(),
            "backup_enabled": self.backup_enabled_check.isChecked(),
            "backup_retention_days": self.backup_retention_spin.value(),
            "cache_enabled": self.cache_enabled_check.isChecked(),
            "cache_memory_mb": self.cache_memory_spin.value(),
            "cache_disk_mb": self.cache_disk_spin.value(),
            "batch_chunk_size": self.batch_chunk_spin.value(),
            "max_memory_mb": self.max_memory_spin.value(),
            "log_level": self.log_level_combo.currentText()
        }
        
        for key, value in settings.items():
            self.settings_manager.set(key, value)
        
        self.settings_changed.emit(settings)
        QMessageBox.information(self, "Success", "Settings saved successfully")
    
    def _reset_settings(self):
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset Settings", 
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.settings.clear()
            self.settings_manager._load_defaults()
            self.load_settings()
            QMessageBox.information(self, "Success", "Settings reset to defaults")


class ConfigurationManagerDialog(QDialog):
    """Main configuration manager dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile_manager = ExportProfileManager()
        self.settings_manager = SettingsManager()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        self.setWindowTitle("Configuration Manager")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Profile management tab
        self.profile_editor = ProfileEditorWidget(self.profile_manager)
        tab_widget.addTab(self.profile_editor, "Export Profiles")
        
        # Settings tab
        self.settings_widget = SettingsWidget(self.settings_manager)
        tab_widget.addTab(self.settings_widget, "Settings")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QInputDialog
    
    app = QApplication(sys.argv)
    
    dialog = ConfigurationManagerDialog()
    dialog.show()
    
    sys.exit(app.exec())
