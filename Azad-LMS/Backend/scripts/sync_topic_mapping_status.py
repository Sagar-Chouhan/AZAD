"""
Sync TopicMapping status with SelfPacedLearning.is_active and TopicMaster.is_active.
"""

import sys
import os

# Add Backend to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from datetime import datetime
from app.database.database import SessionLocal
from app.modules.module.model import SelfPacedLearning, TopicMapping
from app.modules.document.model import TopicMaster


def sync_topic_mappings(dry_run: bool = False):
    db = SessionLocal()
    try:
        print(f"--- TopicMapping Sync (dry_run={dry_run}) ---")
        
        # 1. Sync from SelfPacedLearning
        spl_records = db.query(SelfPacedLearning).all()
        synced_spl = 0
        
        for spl in spl_records:
            expected_status = str(spl.is_active)  # "1" or "0"
            mappings = db.query(TopicMapping).filter(
                TopicMapping.module_id == spl.module_id,
                TopicMapping.topic_id == spl.topic_id,
                TopicMapping.doc_id == spl.doc_id,
            ).all()
            
            for m in mappings:
                if m.status != expected_status:
                    print(
                        f"[SPL Sync] TopicMapping {m.topic_mapping_id} (mod={m.module_id}, top={m.topic_id}, doc={m.doc_id}): "
                        f"status '{m.status}' -> '{expected_status}' (SPL {spl.self_paced_learning_id} is_active={spl.is_active})"
                    )
                    if not dry_run:
                        m.status = expected_status
                        m.updated_at = datetime.now()
                    synced_spl += 1

        # 2. Sync from TopicMaster (if parent topic is inactive '0', mapping should be '0')
        inactive_topics = db.query(TopicMaster).filter(TopicMaster.is_active == "0").all()
        synced_topics = 0
        for t in inactive_topics:
            mappings = db.query(TopicMapping).filter(
                TopicMapping.topic_id == t.parent_id,
                TopicMapping.status != "0",
            ).all()
            for m in mappings:
                print(
                    f"[Topic Sync] TopicMapping {m.topic_mapping_id} (mod={m.module_id}, top={m.topic_id}, doc={m.doc_id}): "
                    f"status '{m.status}' -> '0' (TopicMaster {t.topic_id} is_active=0)"
                )
                if not dry_run:
                    m.status = "0"
                    m.updated_at = datetime.now()
                synced_topics += 1

        if not dry_run:
            db.commit()
            print(f"Successfully committed changes: {synced_spl} SPL mappings synced, {synced_topics} inactive topic mappings synced.")
        else:
            print(f"Dry run complete: {synced_spl} SPL mappings to sync, {synced_topics} inactive topic mappings to sync.")
            
    finally:
        db.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    sync_topic_mappings(dry_run=dry_run)
