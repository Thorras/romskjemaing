"""
Enhanced Export Dialog

Advanced export dialog with section tree, preview, and configuration management
for the enhanced room schedule generator.
"""

import json
import os
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QTextEdit, QProgressBar,
    QGroupBox, QSplitter, QTabWidget, QScrollArea, QFrame, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QWidget, QFormLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

from ..data.space_model import SpaceData
from ..export.enhanced_json_builder import EnhancedJsonBuilder
from ..analysis.data_quality_analyzer import DataQualityAnalyzer
from ..mappers.ns3940_classifier import NS3940Classifier


class ExportWorker(QThread):
    """Worker thread for export operations."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    export_completed = pyqtSignal(dict)
    export_failed = pyqtSignal(str)
    
    def __init__(self, spaces: List[SpaceData], export_config: Dict[str, Any]):
        super().__init__()
        self.spaces = spaces
        self.export_config = export_config
        self.builder = EnhancedJsonBuilder()
    
    def run(self):
        """Run the export process."""
        try:
            self.status_updated.emit("Initializing export...")
            self.progress_updated.emit(10)
            
            # Set source file
            if self.export_config.get("source_file"):
                self.builder.set_source_file(self.export_config["source_file"])
            
            # Set IFC version
            if self.export_config.get("ifc_version"):
                self.builder.set_ifc_version(self.export_config["ifc_version"])
            
            self.status_updated.emit("Building enhanced JSON structure...")
            self.progress_updated.emit(30)
            
            # Build enhanced JSON structure
            enhanced_data = self.builder.build_enhanced_json_structure(
                spaces=self.spaces,
                export_profile=self.export_config.get("export_profile", "production")
            )
            
            self.status_updated.emit("Generating export file...")
            self.progress_updated.emit(70)
            
            # Generate export file
            output_path = self.export_config.get("output_path")
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
            self.status_updated.emit("Export completed successfully!")
            self.progress_updated.emit(100)
            self.export_completed.emit(enhanced_data)
            
        except Exception as e:
            self.export_failed.emit(str(e))


class SectionTreeWidget(QTreeWidget):
    """Custom tree widget for section selection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Export Sections")
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        
        # Section structure
        self.sections = {
            "Core Sections": {
                "identification": "Identification",
                "ifc_metadata": "IFC Metadata", 
                "geometry": "Geometry",
                "classification": "Classification"
            },
            "Phase 2B: Performance & Materials": {
                "performance_requirements": "Performance Requirements",
                "finishes": "Finishes",
                "openings": "Openings",
                "fixtures_and_equipment": "Fixtures & Equipment",
                "hse_and_accessibility": "HSE & Accessibility"
            },
            "Phase 2C: Advanced Sections": {
                "qa_qc": "QA/QC",
                "interfaces": "Interfaces",
                "logistics_and_site": "Logistics & Site",
                "commissioning": "Commissioning"
            },
            "Traditional Sections": {
                "surfaces": "Surfaces",
                "space_boundaries": "Space Boundaries",
                "relationships": "Relationships"
            }
        }
        
        self._populate_tree()
    
    def _populate_tree(self):
        """Populate the tree with sections."""
        for category, sections in self.sections.items():
            category_item = QTreeWidgetItem(self, [category])
            category_item.setCheckState(0, Qt.Checked)
            category_item.setExpanded(True)
            
            for section_id, section_name in sections.items():
                section_item = QTreeWidgetItem(category_item, [section_name])
                section_item.setData(0, Qt.UserRole, section_id)
                section_item.setCheckState(0, Qt.Checked)
    
    def get_selected_sections(self) -> List[str]:
        """Get list of selected section IDs."""
        selected = []
        for i in range(self.topLevelItemCount()):
            category_item = self.topLevelItem(i)
            for j in range(category_item.childCount()):
                section_item = category_item.child(j)
                if section_item.checkState(0) == Qt.Checked:
                    section_id = section_item.data(0, Qt.UserRole)
                    if section_id:
                        selected.append(section_id)
        return selected
    
    def set_sections_from_profile(self, profile: str):
        """Set section selection based on export profile."""
        # Reset all to unchecked
        for i in range(self.topLevelItemCount()):
            category_item = self.topLevelItem(i)
            for j in range(category_item.childCount()):
                section_item = category_item.child(j)
                section_item.setCheckState(0, Qt.Unchecked)
        
        # Set based on profile
        if profile == "core":
            core_sections = ["identification", "ifc_metadata", "geometry", "classification"]
            self._set_sections_checked(core_sections)
        elif profile == "advanced":
            advanced_sections = ["identification", "ifc_metadata", "geometry", "classification", 
                               "surfaces", "space_boundaries", "relationships"]
            self._set_sections_checked(advanced_sections)
        elif profile == "production":
            # All sections checked
            for i in range(self.topLevelItemCount()):
                category_item = self.topLevelItem(i)
                for j in range(category_item.childCount()):
                    section_item = category_item.child(j)
                    section_item.setCheckState(0, Qt.Checked)
    
    def _set_sections_checked(self, section_ids: List[str]):
        """Set specific sections as checked."""
        for i in range(self.topLevelItemCount()):
            category_item = self.topLevelItem(i)
            for j in range(category_item.childCount()):
                section_item = category_item.child(j)
                section_id = section_item.data(0, Qt.UserRole)
                if section_id in section_ids:
                    section_item.setCheckState(0, Qt.Checked)


class DataQualityWidget(QWidget):
    """Widget for displaying data quality information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.analyzer = DataQualityAnalyzer()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Data Quality Analysis")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Quality metrics
        self.metrics_frame = QFrame()
        self.metrics_frame.setFrameStyle(QFrame.StyledPanel)
        metrics_layout = QGridLayout(self.metrics_frame)
        
        # Quality indicators
        self.quality_indicators = {}
        metrics = [
            ("NS 8360 Compliance", "ns8360_compliance"),
            ("NS 3940 Classification", "ns3940_classification"),
            ("Quantities Complete", "quantities_complete"),
            ("Surfaces Present", "surfaces_present"),
            ("Boundaries Present", "boundaries_present"),
            ("Relationships Present", "relationships_present")
        ]
        
        for i, (label, key) in enumerate(metrics):
            metrics_layout.addWidget(QLabel(label), i, 0)
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            self.quality_indicators[key] = progress
            metrics_layout.addWidget(progress, i, 1)
        
        layout.addWidget(self.metrics_frame)
        
        # Recommendations
        self.recommendations_label = QLabel("Recommendations:")
        self.recommendations_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.recommendations_label)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(100)
        self.recommendations_text.setReadOnly(True)
        layout.addWidget(self.recommendations_text)
    
    def update_quality_analysis(self, spaces: List[SpaceData]):
        """Update the quality analysis display."""
        if not spaces:
            return
        
        # Analyze data quality
        total_spaces = len(spaces)
        compliance_stats = {
            "ns8360_compliance": 0,
            "ns3940_classification": 0,
            "quantities_complete": 0,
            "surfaces_present": 0,
            "boundaries_present": 0,
            "relationships_present": 0
        }
        
        for space in spaces:
            # Check NS 8360 compliance
            if space.name and self._is_ns8360_compliant(space.name):
                compliance_stats["ns8360_compliance"] += 1
            
            # Check NS 3940 classification
            if space.name and self._has_ns3940_classification(space.name):
                compliance_stats["ns3940_classification"] += 1
            
            # Check quantities
            if space.quantities and len(space.quantities) > 0:
                compliance_stats["quantities_complete"] += 1
            
            # Check surfaces
            if space.surfaces and len(space.surfaces) > 0:
                compliance_stats["surfaces_present"] += 1
            
            # Check boundaries
            if space.space_boundaries and len(space.space_boundaries) > 0:
                compliance_stats["boundaries_present"] += 1
            
            # Check relationships
            if space.relationships and len(space.relationships) > 0:
                compliance_stats["relationships_present"] += 1
        
        # Update progress bars
        for key, count in compliance_stats.items():
            percentage = int((count / total_spaces) * 100) if total_spaces > 0 else 0
            self.quality_indicators[key].setValue(percentage)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(compliance_stats, total_spaces)
        self.recommendations_text.setPlainText("\n".join(recommendations))
    
    def _is_ns8360_compliant(self, name: str) -> bool:
        """Check if name is NS 8360 compliant."""
        # Simple pattern check
        import re
        pattern = r"^SPC-[A-Z0-9]{1,3}-[A-Z0-9]{1,6}-\d{3}-\d{3}$|^SPC-[A-Z0-9]{1,3}-\d{3}-\d{3}$"
        return bool(re.match(pattern, name))
    
    def _has_ns3940_classification(self, name: str) -> bool:
        """Check if name has NS 3940 classification."""
        # Check if name contains 3-digit function code
        import re
        pattern = r"-\d{3}-"
        return bool(re.search(pattern, name))
    
    def _generate_recommendations(self, stats: Dict[str, int], total: int) -> List[str]:
        """Generate recommendations based on quality stats."""
        recommendations = []
        
        if stats["ns8360_compliance"] < total * 0.8:
            recommendations.append("• Improve NS 8360 naming compliance")
        
        if stats["ns3940_classification"] < total * 0.8:
            recommendations.append("• Add NS 3940 classification codes")
        
        if stats["quantities_complete"] < total * 0.9:
            recommendations.append("• Complete quantity data for spaces")
        
        if stats["surfaces_present"] < total * 0.7:
            recommendations.append("• Add surface data for better material mapping")
        
        if stats["boundaries_present"] < total * 0.7:
            recommendations.append("• Add space boundary data")
        
        if stats["relationships_present"] < total * 0.5:
            recommendations.append("• Add relationship data for better context")
        
        if not recommendations:
            recommendations.append("• Data quality looks good!")
        
        return recommendations


class ConfigurationWidget(QWidget):
    """Widget for export configuration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QFormLayout(self)
        
        # Export profile
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["core", "advanced", "production"])
        self.profile_combo.setCurrentText("production")
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        layout.addRow("Export Profile:", self.profile_combo)
        
        # Source file
        self.source_file_edit = QLineEdit()
        self.source_file_edit.setPlaceholderText("Select IFC source file...")
        self.source_file_btn = QPushButton("Browse...")
        self.source_file_btn.clicked.connect(self._browse_source_file)
        
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_file_edit)
        source_layout.addWidget(self.source_file_btn)
        layout.addRow("Source File:", source_layout)
        
        # IFC version
        self.ifc_version_combo = QComboBox()
        self.ifc_version_combo.addItems(["IFC2x3", "IFC4", "IFC4x1", "IFC4x3"])
        self.ifc_version_combo.setCurrentText("IFC4")
        layout.addRow("IFC Version:", self.ifc_version_combo)
        
        # Output file
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setPlaceholderText("Select output file...")
        self.output_file_btn = QPushButton("Browse...")
        self.output_file_btn.clicked.connect(self._browse_output_file)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_file_edit)
        output_layout.addWidget(self.output_file_btn)
        layout.addRow("Output File:", output_layout)
        
        # Advanced options
        self.advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(self.advanced_group)
        
        self.include_metadata_check = QCheckBox("Include metadata")
        self.include_metadata_check.setChecked(True)
        advanced_layout.addRow(self.include_metadata_check)
        
        self.pretty_print_check = QCheckBox("Pretty print JSON")
        self.pretty_print_check.setChecked(True)
        advanced_layout.addRow(self.pretty_print_check)
        
        self.validate_data_check = QCheckBox("Validate data before export")
        self.validate_data_check.setChecked(True)
        advanced_layout.addRow(self.validate_data_check)
        
        layout.addRow(self.advanced_group)
    
    def _on_profile_changed(self, profile: str):
        """Handle profile change."""
        # Emit signal to update section tree
        if hasattr(self.parent(), 'section_tree'):
            self.parent().section_tree.set_sections_from_profile(profile)
    
    def _browse_source_file(self):
        """Browse for source file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select IFC Source File", "", "IFC Files (*.ifc);;All Files (*)"
        )
        if file_path:
            self.source_file_edit.setText(file_path)
    
    def _browse_output_file(self):
        """Browse for output file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.output_file_edit.setText(file_path)
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "export_profile": self.profile_combo.currentText(),
            "source_file": self.source_file_edit.text() or None,
            "ifc_version": self.ifc_version_combo.currentText(),
            "output_path": self.output_file_edit.text() or None,
            "include_metadata": self.include_metadata_check.isChecked(),
            "pretty_print": self.pretty_print_check.isChecked(),
            "validate_data": self.validate_data_check.isChecked()
        }


class EnhancedExportDialog(QDialog):
    """Enhanced export dialog with advanced features."""
    
    def __init__(self, spaces: List[SpaceData], parent=None):
        super().__init__(parent)
        self.spaces = spaces
        self.export_worker = None
        self.setup_ui()
        self.setup_connections()
        
        # Initialize data quality analysis
        if spaces:
            self.data_quality_widget.update_quality_analysis(spaces)
    
    def setup_ui(self):
        """Setup the UI."""
        self.setWindowTitle("Enhanced Export Dialog")
        self.setModal(True)
        self.resize(1000, 700)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Configuration and sections
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Configuration widget
        self.config_widget = ConfigurationWidget()
        left_layout.addWidget(self.config_widget)
        
        # Section tree
        self.section_tree = SectionTreeWidget()
        left_layout.addWidget(self.section_tree)
        
        # Connect profile change
        self.config_widget.profile_combo.currentTextChanged.connect(
            self.section_tree.set_sections_from_profile
        )
        
        splitter.addWidget(left_panel)
        
        # Right panel - Preview and quality
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Tab widget
        tab_widget = QTabWidget()
        right_layout.addWidget(tab_widget)
        
        # Data quality tab
        self.data_quality_widget = DataQualityWidget()
        tab_widget.addTab(self.data_quality_widget, "Data Quality")
        
        # Preview tab
        self.preview_widget = QTextEdit()
        self.preview_widget.setReadOnly(True)
        self.preview_widget.setFont(QFont("Consolas", 9))
        tab_widget.addTab(self.preview_widget, "Preview")
        
        # Progress and status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to export")
        right_layout.addWidget(self.status_label)
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.preview_export)
        button_layout.addWidget(self.preview_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.start_export)
        button_layout.addWidget(self.export_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections."""
        pass
    
    def preview_export(self):
        """Preview the export."""
        try:
            config = self.config_widget.get_configuration()
            selected_sections = self.section_tree.get_selected_sections()
            
            # Build preview data
            builder = EnhancedJsonBuilder()
            if config.get("source_file"):
                builder.set_source_file(config["source_file"])
            if config.get("ifc_version"):
                builder.set_ifc_version(config["ifc_version"])
            
            # Use first space for preview
            if self.spaces:
                preview_data = builder._build_enhanced_space_dict(
                    self.spaces[0], config.get("export_profile", "production")
                )
                
                # Filter selected sections
                if selected_sections:
                    filtered_data = {k: v for k, v in preview_data.items() if k in selected_sections}
                else:
                    filtered_data = preview_data
                
                # Display preview
                preview_json = json.dumps(filtered_data, indent=2, ensure_ascii=False)
                self.preview_widget.setPlainText(preview_json)
                
                # Switch to preview tab
                tab_widget = self.preview_widget.parent().parent()
                tab_widget.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Failed to generate preview: {str(e)}")
    
    def start_export(self):
        """Start the export process."""
        try:
            config = self.config_widget.get_configuration()
            
            # Validate configuration
            if not config.get("output_path"):
                QMessageBox.warning(self, "Configuration Error", "Please select an output file.")
                return
            
            # Start export worker
            self.export_worker = ExportWorker(self.spaces, config)
            self.export_worker.progress_updated.connect(self.progress_bar.setValue)
            self.export_worker.status_updated.connect(self.status_label.setText)
            self.export_worker.export_completed.connect(self.export_completed)
            self.export_worker.export_failed.connect(self.export_failed)
            
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.export_btn.setEnabled(False)
            
            # Start worker
            self.export_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to start export: {str(e)}")
    
    def export_completed(self, data: Dict[str, Any]):
        """Handle export completion."""
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(True)
        self.status_label.setText("Export completed successfully!")
        
        QMessageBox.information(
            self, "Export Complete", 
            f"Successfully exported {len(self.spaces)} spaces to {self.config_widget.output_file_edit.text()}"
        )
        
        self.accept()
    
    def export_failed(self, error: str):
        """Handle export failure."""
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(True)
        self.status_label.setText("Export failed!")
        
        QMessageBox.critical(self, "Export Failed", f"Export failed: {error}")


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create sample spaces
    from ..data.space_model import SpaceData
    
    sample_spaces = [
        SpaceData(
            guid="test_space_1",
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111",
            description="Test space 1",
            object_type="IfcSpace",
            zone_category="A101",
            number="003",
            elevation=0.0,
            quantities={"Height": 2.4, "NetArea": 25.0},
            surfaces=[],
            space_boundaries=[],
            relationships=[]
        ),
        SpaceData(
            guid="test_space_2",
            name="SPC-02-A101-130-001",
            long_name="Bad | 02/A101 | NS3940:130",
            description="Test space 2",
            object_type="IfcSpace",
            zone_category="A101",
            number="001",
            elevation=0.0,
            quantities={"Height": 2.4, "NetArea": 8.0},
            surfaces=[],
            space_boundaries=[],
            relationships=[]
        )
    ]
    
    dialog = EnhancedExportDialog(sample_spaces)
    dialog.show()
    
    sys.exit(app.exec_())
