#!/usr/bin/env python3
"""
Data Lineage Tracker
Tracks the complete lifecycle of data transformations through the ETL pipeline
"""

from datetime import datetime
import json
import os
import hashlib


class DataLineageTracker:
    """Tracks data lineage throughout the ETL pipeline"""

    def __init__(self):
        self.lineage_records = []
        self.current_batch_id = None
        self.pipeline_start_time = None

    def start_pipeline(self, batch_id=None):
        """Start tracking a new pipeline execution"""
        if batch_id is None:
            batch_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.current_batch_id = batch_id
        self.pipeline_start_time = datetime.now()

        self.add_lineage_record(
            stage='PIPELINE_START',
            operation='initialize',
            description='ETL pipeline started',
            metadata={'batch_id': batch_id}
        )

        return batch_id

    def add_lineage_record(self, stage, operation, description, input_data=None,
                          output_data=None, metadata=None, record_count=None):
        """Add a lineage record for a transformation"""

        record = {
            'timestamp': datetime.now().isoformat(),
            'batch_id': self.current_batch_id,
            'stage': stage,
            'operation': operation,
            'description': description,
            'record_count': record_count,
            'metadata': metadata or {}
        }

        # Add data checksums for traceability
        if input_data is not None:
            record['input_checksum'] = self._calculate_checksum(input_data)

        if output_data is not None:
            record['output_checksum'] = self._calculate_checksum(output_data)

        self.lineage_records.append(record)

    def _calculate_checksum(self, data):
        """Calculate checksum for data"""
        try:
            data_str = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()[:16]
        except:
            return None

    def record_extraction(self, source, record_count, metadata=None):
        """Record data extraction stage"""
        self.add_lineage_record(
            stage='EXTRACT',
            operation='load_raw_data',
            description=f'Extracted {record_count} records from {source}',
            record_count=record_count,
            metadata=metadata or {'source': source}
        )

    def record_validation(self, valid_count, invalid_count, error_count, warning_count):
        """Record data validation stage"""
        self.add_lineage_record(
            stage='VALIDATE',
            operation='validate_data',
            description=f'Validated data: {valid_count} valid, {invalid_count} invalid',
            record_count=valid_count,
            metadata={
                'valid_records': valid_count,
                'invalid_records': invalid_count,
                'total_errors': error_count,
                'total_warnings': warning_count
            }
        )

    def record_transformation(self, transformation_type, input_count, output_count, metadata=None):
        """Record data transformation stage"""
        self.add_lineage_record(
            stage='TRANSFORM',
            operation=transformation_type,
            description=f'Applied {transformation_type}: {input_count} → {output_count} records',
            record_count=output_count,
            metadata=metadata or {}
        )

    def record_rule_application(self, rule_name, records_affected, alerts_generated):
        """Record business rule application"""
        self.add_lineage_record(
            stage='TRANSFORM',
            operation='apply_rule',
            description=f'Applied rule: {rule_name}',
            record_count=records_affected,
            metadata={
                'rule_name': rule_name,
                'records_affected': records_affected,
                'alerts_generated': alerts_generated
            }
        )

    def record_model_prediction(self, model_name, record_count, high_risk_count, metadata=None):
        """Record ML model predictions"""
        self.add_lineage_record(
            stage='PREDICT',
            operation='model_prediction',
            description=f'{model_name} processed {record_count} records',
            record_count=record_count,
            metadata={
                'model_name': model_name,
                'high_risk_predictions': high_risk_count,
                **(metadata or {})
            }
        )

    def record_explainability(self, explainer_type, record_count, metadata=None):
        """Record explainability computation"""
        self.add_lineage_record(
            stage='EXPLAIN',
            operation='compute_explainability',
            description=f'{explainer_type} computed for {record_count} records',
            record_count=record_count,
            metadata={'explainer_type': explainer_type, **(metadata or {})}
        )

    def record_load(self, destination, record_count, table_name=None):
        """Record data loading stage"""
        self.add_lineage_record(
            stage='LOAD',
            operation='load_data',
            description=f'Loaded {record_count} records to {destination}',
            record_count=record_count,
            metadata={
                'destination': destination,
                'table_name': table_name
            }
        )

    def record_dashboard_generation(self, dashboard_type, record_count, output_path):
        """Record dashboard generation"""
        self.add_lineage_record(
            stage='VISUALIZE',
            operation='generate_dashboard',
            description=f'Generated {dashboard_type} dashboard',
            record_count=record_count,
            metadata={
                'dashboard_type': dashboard_type,
                'output_path': output_path
            }
        )

    def end_pipeline(self, success=True, error_message=None):
        """End pipeline tracking"""
        duration = (datetime.now() - self.pipeline_start_time).total_seconds() if self.pipeline_start_time else 0

        self.add_lineage_record(
            stage='PIPELINE_END',
            operation='complete' if success else 'failed',
            description='ETL pipeline completed' if success else f'Pipeline failed: {error_message}',
            metadata={
                'success': success,
                'duration_seconds': duration,
                'error_message': error_message
            }
        )

    def get_lineage_summary(self):
        """Get summary of lineage records"""
        stages = {}
        for record in self.lineage_records:
            stage = record['stage']
            if stage not in stages:
                stages[stage] = {'count': 0, 'operations': []}
            stages[stage]['count'] += 1
            stages[stage]['operations'].append(record['operation'])

        return {
            'batch_id': self.current_batch_id,
            'total_records': len(self.lineage_records),
            'stages': stages,
            'start_time': self.lineage_records[0]['timestamp'] if self.lineage_records else None,
            'end_time': self.lineage_records[-1]['timestamp'] if self.lineage_records else None
        }

    def save_lineage(self, output_dir='lineage'):
        """Save lineage records to file"""
        os.makedirs(output_dir, exist_ok=True)

        filename = f"lineage_{self.current_batch_id}.json"
        filepath = os.path.join(output_dir, filename)

        lineage_data = {
            'batch_id': self.current_batch_id,
            'pipeline_start': self.pipeline_start_time.isoformat() if self.pipeline_start_time else None,
            'records': self.lineage_records,
            'summary': self.get_lineage_summary()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(lineage_data, f, indent=2)

        print(f"\n✓ Data lineage saved to: {filepath}")
        return filepath

    def print_lineage(self):
        """Print lineage records in readable format"""
        print("\n" + "=" * 80)
        print("DATA LINEAGE TRACE")
        print("=" * 80 + "\n")
        print(f"Batch ID: {self.current_batch_id}\n")

        for i, record in enumerate(self.lineage_records, 1):
            stage_icon = {
                'PIPELINE_START': '🚀',
                'EXTRACT': '📥',
                'VALIDATE': '✅',
                'TRANSFORM': '⚙️',
                'PREDICT': '🤖',
                'EXPLAIN': '💡',
                'LOAD': '💾',
                'VISUALIZE': '📊',
                'PIPELINE_END': '🏁'
            }.get(record['stage'], '▶️')

            print(f"{i}. {stage_icon} [{record['stage']}] {record['operation']}")
            print(f"   {record['description']}")
            if record.get('record_count'):
                print(f"   Records: {record['record_count']}")
            if record.get('metadata'):
                key_info = {k: v for k, v in record['metadata'].items() if k not in ['batch_id']}
                if key_info:
                    print(f"   Metadata: {key_info}")
            print()

        print("=" * 80 + "\n")

    def generate_lineage_visualization_html(self):
        """Generate HTML visualization of lineage with improved formatting"""

        # Add CSS for lineage visualization
        html = """
        <style>
            .lineage-visualization {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 25px;
                margin: 20px 0;
                color: white;
            }
            .lineage-visualization h3 {
                color: white;
                margin-bottom: 20px;
                font-size: 22px;
                text-align: center;
            }
            .lineage-flow {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .lineage-stage {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s;
            }
            .lineage-stage:hover {
                transform: translateX(5px);
            }
            .stage-header {
                font-weight: bold;
                font-size: 16px;
                color: #667eea;
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 2px solid #667eea;
            }
            .stage-operations {
                color: #333;
                font-size: 14px;
            }
            .operation {
                padding: 6px 0;
                display: flex;
                align-items: center;
            }
            .operation strong {
                color: #764ba2;
                margin-right: 8px;
                min-width: 150px;
            }
            .stage-count {
                margin-top: 8px;
                padding: 6px 12px;
                background: #667eea;
                color: white;
                border-radius: 4px;
                display: inline-block;
                font-size: 12px;
                font-weight: bold;
            }
            .lineage-arrow {
                text-align: center;
                font-size: 24px;
                color: white;
                margin: 5px 0;
            }
            .lineage-metadata {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 12px;
                margin-top: 15px;
                font-size: 13px;
            }
            .lineage-metadata strong {
                color: #ffd700;
            }
        </style>
        <div class="lineage-visualization">
            <h3>📋 Data Lineage Trace</h3>
        """

        # Add batch info
        if self.current_batch_id:
            html += f"""
            <div class="lineage-metadata">
                <strong>Batch ID:</strong> {self.current_batch_id} | 
                <strong>Total Operations:</strong> {len(self.lineage_records)}
            </div>
            """

        html += '<div class="lineage-flow">'

        # Only show stages that actually occurred
        stage_order = ['EXTRACT', 'VALIDATE', 'TRANSFORM', 'LOAD', 'VISUALIZE']
        stage_records = {stage: [] for stage in stage_order}

        for record in self.lineage_records:
            stage = record['stage']
            if stage in stage_records:
                stage_records[stage].append(record)

        for idx, stage in enumerate(stage_order):
            records = stage_records[stage]
            if not records:
                continue

            stage_icon = {
                'EXTRACT': '📥',
                'VALIDATE': '✅',
                'TRANSFORM': '⚙️',
                'LOAD': '💾',
                'VISUALIZE': '📊'
            }.get(stage, '▶️')

            total_records = sum(r.get('record_count', 0) for r in records if r.get('record_count'))

            html += f"""
                <div class="lineage-stage">
                    <div class="stage-header">{stage_icon} Stage {idx + 1}: {stage}</div>
                    <div class="stage-operations">
            """

            for record in records:
                # Format metadata if present
                metadata_str = ""
                if record.get('metadata'):
                    key_metadata = {k: v for k, v in record['metadata'].items()
                                  if k not in ['batch_id'] and v is not None}
                    if key_metadata and len(str(key_metadata)) < 100:
                        metadata_str = f" <span style='color: #999; font-size: 12px;'>({', '.join(f'{k}: {v}' for k, v in list(key_metadata.items())[:2])})</span>"

                html += f"""
                        <div class="operation">
                            <strong>{record['operation']}</strong>
                            <span>{record['description']}{metadata_str}</span>
                        </div>
                """

            if total_records > 0:
                html += f"<div class='stage-count'>📊 {total_records:,} records processed</div>"

            html += """
                    </div>
                </div>
            """

            # Add arrow if not last stage
            if idx < len([s for s in stage_order if stage_records[s]]) - 1:
                html += '<div class="lineage-arrow">↓</div>'

        html += """
            </div>
        </div>
        """

        return html


# Global lineage tracker instance
_global_tracker = None

def get_lineage_tracker():
    """Get or create global lineage tracker"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = DataLineageTracker()
    return _global_tracker


def reset_lineage_tracker():
    """Reset global lineage tracker"""
    global _global_tracker
    _global_tracker = None

