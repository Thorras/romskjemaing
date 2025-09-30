"""
Data Quality Dashboard

Advanced data quality visualization and analysis dashboard for room schedule data.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QProgressBar,
    QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox, QFrame, QScrollArea,
    QPushButton, QComboBox, QSpinBox, QCheckBox, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen

from ..data.space_model import SpaceData
from ..analysis.data_quality_analyzer import DataQualityAnalyzer
from ..mappers.ns3940_classifier import NS3940Classifier
from ..parsers.ns8360_name_parser import NS8360NameParser


class QualityIndicator(QWidget):
    """Custom quality indicator widget."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = 0
        self.max_value = 100
        self.setMinimumHeight(80)
        self.setMaximumHeight(120)
    
    def set_value(self, value: int, max_value: int = 100):
        """Set the indicator value."""
        self.value = value
        self.max_value = max_value
        self.update()
    
    def paintEvent(self, event):
        """Paint the indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Calculate progress
        progress = self.value / self.max_value if self.max_value > 0 else 0
        
        # Draw background
        painter.setBrush(QColor(240, 240, 240))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 5, 5)
        
        # Draw progress bar
        bar_height = 20
        bar_y = height - bar_height - 10
        bar_width = int((width - 20) * progress)
        
        # Color based on progress
        if progress >= 0.8:
            color = QColor(76, 175, 80)  # Green
        elif progress >= 0.6:
            color = QColor(255, 193, 7)  # Yellow
        else:
            color = QColor(244, 67, 54)  # Red
        
        painter.setBrush(color)
        painter.drawRoundedRect(10, bar_y, bar_width, bar_height, 3, 3)
        
        # Draw title
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(10, 20, width - 20, 30, Qt.AlignLeft, self.title)
        
        # Draw value
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        value_text = f"{self.value}/{self.max_value} ({int(progress * 100)}%)"
        painter.drawText(10, 40, width - 20, 30, Qt.AlignLeft, value_text)


class SpaceQualityTable(QTableWidget):
    """Table widget for displaying space quality data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
    
    def setup_table(self):
        """Setup the table."""
        headers = [
            "Space Name", "NS 8360", "NS 3940", "Quantities", 
            "Surfaces", "Boundaries", "Relationships", "Overall"
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Set column widths
        self.setColumnWidth(0, 150)  # Space Name
        for i in range(1, len(headers)):
            self.setColumnWidth(i, 80)
        
        # Enable sorting
        self.setSortingEnabled(True)
        
        # Set alternating row colors
        self.setAlternatingRowColors(True)
    
    def update_data(self, spaces: List[SpaceData], quality_data: List[Dict[str, Any]]):
        """Update table with quality data."""
        self.setRowCount(len(spaces))
        
        for row, (space, quality) in enumerate(zip(spaces, quality_data)):
            # Space name
            name_item = QTableWidgetItem(space.name or "Unknown")
            self.setItem(row, 0, name_item)
            
            # Quality indicators
            indicators = [
                quality.get("ns8360_compliant", False),
                quality.get("ns3940_classified", False),
                quality.get("quantities_complete", False),
                quality.get("surfaces_present", False),
                quality.get("boundaries_present", False),
                quality.get("relationships_present", False)
            ]
            
            for col, indicator in enumerate(indicators, 1):
                item = QTableWidgetItem("✓" if indicator else "✗")
                item.setTextAlignment(Qt.AlignCenter)
                
                # Color coding
                if indicator:
                    item.setBackground(QColor(200, 255, 200))  # Light green
                else:
                    item.setBackground(QColor(255, 200, 200))  # Light red
                
                self.setItem(row, col, item)
            
            # Overall quality
            overall_score = sum(indicators) / len(indicators) * 100
            overall_item = QTableWidgetItem(f"{int(overall_score)}%")
            overall_item.setTextAlignment(Qt.AlignCenter)
            
            if overall_score >= 80:
                overall_item.setBackground(QColor(200, 255, 200))
            elif overall_score >= 60:
                overall_item.setBackground(QColor(255, 255, 200))
            else:
                overall_item.setBackground(QColor(255, 200, 200))
            
            self.setItem(row, 7, overall_item)


class RecommendationsWidget(QWidget):
    """Widget for displaying recommendations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Improvement Recommendations")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Recommendations text
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setMaximumHeight(200)
        layout.addWidget(self.recommendations_text)
        
        # Priority actions
        self.priority_group = QGroupBox("Priority Actions")
        priority_layout = QVBoxLayout(self.priority_group)
        
        self.priority_list = QTextEdit()
        self.priority_list.setReadOnly(True)
        self.priority_list.setMaximumHeight(100)
        priority_layout.addWidget(self.priority_list)
        
        layout.addWidget(self.priority_group)
    
    def update_recommendations(self, recommendations: List[str], priority_actions: List[str]):
        """Update recommendations display."""
        self.recommendations_text.setPlainText("\n".join(recommendations))
        self.priority_list.setPlainText("\n".join(priority_actions))


class DataQualityDashboard(QWidget):
    """Main data quality dashboard widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.spaces = []
        self.analyzer = DataQualityAnalyzer()
        self.classifier = NS3940Classifier()
        self.name_parser = NS8360NameParser()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Data Quality Dashboard")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Quality overview
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Quality overview
        overview_group = QGroupBox("Quality Overview")
        overview_layout = QGridLayout(overview_group)
        
        # Quality indicators
        self.quality_indicators = {}
        indicators = [
            ("NS 8360 Compliance", "ns8360_compliance"),
            ("NS 3940 Classification", "ns3940_classification"),
            ("Quantities Complete", "quantities_complete"),
            ("Surfaces Present", "surfaces_present"),
            ("Boundaries Present", "boundaries_present"),
            ("Relationships Present", "relationships_present")
        ]
        
        for i, (title, key) in enumerate(indicators):
            indicator = QualityIndicator(title)
            self.quality_indicators[key] = indicator
            overview_layout.addWidget(indicator, i // 2, i % 2)
        
        left_layout.addWidget(overview_group)
        
        # Summary statistics
        self.summary_group = QGroupBox("Summary Statistics")
        summary_layout = QVBoxLayout(self.summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        summary_layout.addWidget(self.summary_text)
        
        left_layout.addWidget(self.summary_group)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Detailed analysis
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Tab widget for detailed analysis
        tab_widget = QTabWidget()
        right_layout.addWidget(tab_widget)
        
        # Space quality table
        self.space_table = SpaceQualityTable()
        tab_widget.addTab(self.space_table, "Space Quality")
        
        # Recommendations
        self.recommendations_widget = RecommendationsWidget()
        tab_widget.addTab(self.recommendations_widget, "Recommendations")
        
        # Export readiness
        self.readiness_widget = self._create_readiness_widget()
        tab_widget.addTab(self.readiness_widget, "Export Readiness")
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Analysis")
        self.refresh_btn.clicked.connect(self.refresh_analysis)
        button_layout.addWidget(self.refresh_btn)
        
        self.export_report_btn = QPushButton("Export Report")
        self.export_report_btn.clicked.connect(self.export_report)
        button_layout.addWidget(self.export_report_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _create_readiness_widget(self) -> QWidget:
        """Create export readiness widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Readiness score
        self.readiness_score = QLabel("Export Readiness: 0%")
        self.readiness_score.setFont(QFont("Arial", 14, QFont.Bold))
        self.readiness_score.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.readiness_score)
        
        # Readiness progress bar
        self.readiness_progress = QProgressBar()
        self.readiness_progress.setRange(0, 100)
        layout.addWidget(self.readiness_progress)
        
        # Readiness checklist
        self.readiness_checklist = QTextEdit()
        self.readiness_checklist.setReadOnly(True)
        self.readiness_checklist.setMaximumHeight(200)
        layout.addWidget(self.readiness_checklist)
        
        return widget
    
    def set_spaces(self, spaces: List[SpaceData]):
        """Set spaces for analysis."""
        self.spaces = spaces
        self.refresh_analysis()
    
    def refresh_analysis(self):
        """Refresh the quality analysis."""
        if not self.spaces:
            return
        
        # Analyze quality
        quality_data = self._analyze_quality()
        
        # Update indicators
        self._update_quality_indicators(quality_data)
        
        # Update summary
        self._update_summary(quality_data)
        
        # Update space table
        self.space_table.update_data(self.spaces, quality_data)
        
        # Update recommendations
        recommendations, priority_actions = self._generate_recommendations(quality_data)
        self.recommendations_widget.update_recommendations(recommendations, priority_actions)
        
        # Update export readiness
        self._update_export_readiness(quality_data)
    
    def _analyze_quality(self) -> List[Dict[str, Any]]:
        """Analyze quality for all spaces."""
        quality_data = []
        
        for space in self.spaces:
            quality = {
                "ns8360_compliant": self._is_ns8360_compliant(space.name),
                "ns3940_classified": self._has_ns3940_classification(space.name),
                "quantities_complete": bool(space.quantities and len(space.quantities) > 0),
                "surfaces_present": bool(space.surfaces and len(space.surfaces) > 0),
                "boundaries_present": bool(space.space_boundaries and len(space.space_boundaries) > 0),
                "relationships_present": bool(space.relationships and len(space.relationships) > 0)
            }
            quality_data.append(quality)
        
        return quality_data
    
    def _is_ns8360_compliant(self, name: str) -> bool:
        """Check if name is NS 8360 compliant."""
        if not name:
            return False
        
        import re
        pattern = r"^SPC-[A-Z0-9]{1,3}-[A-Z0-9]{1,6}-\d{3}-\d{3}$|^SPC-[A-Z0-9]{1,3}-\d{3}-\d{3}$"
        return bool(re.match(pattern, name))
    
    def _has_ns3940_classification(self, name: str) -> bool:
        """Check if name has NS 3940 classification."""
        if not name:
            return False
        
        import re
        pattern = r"-\d{3}-"
        return bool(re.search(pattern, name))
    
    def _update_quality_indicators(self, quality_data: List[Dict[str, Any]]):
        """Update quality indicators."""
        total_spaces = len(quality_data)
        if total_spaces == 0:
            return
        
        # Count compliant spaces
        counts = {
            "ns8360_compliance": sum(1 for q in quality_data if q["ns8360_compliant"]),
            "ns3940_classification": sum(1 for q in quality_data if q["ns3940_classified"]),
            "quantities_complete": sum(1 for q in quality_data if q["quantities_complete"]),
            "surfaces_present": sum(1 for q in quality_data if q["surfaces_present"]),
            "boundaries_present": sum(1 for q in quality_data if q["boundaries_present"]),
            "relationships_present": sum(1 for q in quality_data if q["relationships_present"])
        }
        
        # Update indicators
        for key, count in counts.items():
            self.quality_indicators[key].set_value(count, total_spaces)
    
    def _update_summary(self, quality_data: List[Dict[str, Any]]):
        """Update summary statistics."""
        total_spaces = len(quality_data)
        if total_spaces == 0:
            self.summary_text.setPlainText("No spaces to analyze.")
            return
        
        # Calculate statistics
        stats = {
            "Total Spaces": total_spaces,
            "NS 8360 Compliant": sum(1 for q in quality_data if q["ns8360_compliant"]),
            "NS 3940 Classified": sum(1 for q in quality_data if q["ns3940_classified"]),
            "With Quantities": sum(1 for q in quality_data if q["quantities_complete"]),
            "With Surfaces": sum(1 for q in quality_data if q["surfaces_present"]),
            "With Boundaries": sum(1 for q in quality_data if q["boundaries_present"]),
            "With Relationships": sum(1 for q in quality_data if q["relationships_present"])
        }
        
        # Calculate percentages
        summary_text = "Summary Statistics:\n\n"
        for key, count in stats.items():
            if key == "Total Spaces":
                summary_text += f"{key}: {count}\n"
            else:
                percentage = (count / total_spaces) * 100
                summary_text += f"{key}: {count} ({percentage:.1f}%)\n"
        
        self.summary_text.setPlainText(summary_text)
    
    def _generate_recommendations(self, quality_data: List[Dict[str, Any]]) -> tuple:
        """Generate recommendations and priority actions."""
        total_spaces = len(quality_data)
        if total_spaces == 0:
            return [], []
        
        recommendations = []
        priority_actions = []
        
        # Calculate compliance rates
        compliance_rates = {
            "ns8360": sum(1 for q in quality_data if q["ns8360_compliant"]) / total_spaces,
            "ns3940": sum(1 for q in quality_data if q["ns3940_classified"]) / total_spaces,
            "quantities": sum(1 for q in quality_data if q["quantities_complete"]) / total_spaces,
            "surfaces": sum(1 for q in quality_data if q["surfaces_present"]) / total_spaces,
            "boundaries": sum(1 for q in quality_data if q["boundaries_present"]) / total_spaces,
            "relationships": sum(1 for q in quality_data if q["relationships_present"]) / total_spaces
        }
        
        # Generate recommendations
        if compliance_rates["ns8360"] < 0.8:
            recommendations.append("• Improve NS 8360 naming compliance")
            if compliance_rates["ns8360"] < 0.5:
                priority_actions.append("HIGH: Fix NS 8360 naming patterns")
        
        if compliance_rates["ns3940"] < 0.8:
            recommendations.append("• Add NS 3940 classification codes")
            if compliance_rates["ns3940"] < 0.5:
                priority_actions.append("HIGH: Add NS 3940 classification")
        
        if compliance_rates["quantities"] < 0.9:
            recommendations.append("• Complete quantity data for spaces")
            if compliance_rates["quantities"] < 0.7:
                priority_actions.append("MEDIUM: Complete quantity data")
        
        if compliance_rates["surfaces"] < 0.7:
            recommendations.append("• Add surface data for better material mapping")
            if compliance_rates["surfaces"] < 0.5:
                priority_actions.append("MEDIUM: Add surface data")
        
        if compliance_rates["boundaries"] < 0.7:
            recommendations.append("• Add space boundary data")
            if compliance_rates["boundaries"] < 0.5:
                priority_actions.append("MEDIUM: Add boundary data")
        
        if compliance_rates["relationships"] < 0.5:
            recommendations.append("• Add relationship data for better context")
            priority_actions.append("LOW: Add relationship data")
        
        if not recommendations:
            recommendations.append("• Data quality looks excellent!")
            priority_actions.append("✓ Ready for export")
        
        return recommendations, priority_actions
    
    def _update_export_readiness(self, quality_data: List[Dict[str, Any]]):
        """Update export readiness display."""
        total_spaces = len(quality_data)
        if total_spaces == 0:
            self.readiness_score.setText("Export Readiness: 0%")
            self.readiness_progress.setValue(0)
            self.readiness_checklist.setPlainText("No spaces to analyze.")
            return
        
        # Calculate readiness score
        readiness_factors = [
            sum(1 for q in quality_data if q["ns8360_compliant"]) / total_spaces,
            sum(1 for q in quality_data if q["ns3940_classified"]) / total_spaces,
            sum(1 for q in quality_data if q["quantities_complete"]) / total_spaces,
            sum(1 for q in quality_data if q["surfaces_present"]) / total_spaces,
            sum(1 for q in quality_data if q["boundaries_present"]) / total_spaces,
            sum(1 for q in quality_data if q["relationships_present"]) / total_spaces
        ]
        
        readiness_score = int(sum(readiness_factors) / len(readiness_factors) * 100)
        
        # Update display
        self.readiness_score.setText(f"Export Readiness: {readiness_score}%")
        self.readiness_progress.setValue(readiness_score)
        
        # Update checklist
        checklist_items = [
            f"NS 8360 Compliance: {int(readiness_factors[0] * 100)}%",
            f"NS 3940 Classification: {int(readiness_factors[1] * 100)}%",
            f"Quantities Complete: {int(readiness_factors[2] * 100)}%",
            f"Surfaces Present: {int(readiness_factors[3] * 100)}%",
            f"Boundaries Present: {int(readiness_factors[4] * 100)}%",
            f"Relationships Present: {int(readiness_factors[5] * 100)}%"
        ]
        
        self.readiness_checklist.setPlainText("\n".join(checklist_items))
    
    def export_report(self):
        """Export quality report."""
        # This would typically open a file dialog and save the report
        # For now, just show a message
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Export Report", "Quality report export functionality would be implemented here.")


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
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
    
    dashboard = DataQualityDashboard()
    dashboard.set_spaces(sample_spaces)
    dashboard.show()
    
    sys.exit(app.exec())
