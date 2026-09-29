import os
import shutil
import datetime
from pathlib import Path
from database.db_manager import get_db
from config import PRIMARY_DB_PATH, SECONDARY_DB_PATH, SECONDARY_DRIVE, EXPORTS_DIR

class BackupService:
    @staticmethod
    def get_backup_status():
        """Retourne l'état des deux bases de données (Partition C: et D:)."""
        db = get_db()
        
        # État C:
        c_exists = PRIMARY_DB_PATH.exists()
        c_size = PRIMARY_DB_PATH.stat().st_size / 1024 if c_exists else 0 # Ko
        c_time = datetime.datetime.fromtimestamp(PRIMARY_DB_PATH.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S") if c_exists else "Inexistant"

        # État D:
        d_drive_available = SECONDARY_DRIVE.exists()
        d_exists = SECONDARY_DB_PATH.exists()
        d_size = SECONDARY_DB_PATH.stat().st_size / 1024 if d_exists else 0 # Ko
        d_time = datetime.datetime.fromtimestamp(SECONDARY_DB_PATH.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S") if d_exists else "Inexistant"

        return {
            "primary": {
                "path": str(PRIMARY_DB_PATH),
                "exists": c_exists,
                "size_kb": round(c_size, 1),
                "last_modified": c_time,
                "status": "Opérationnel" if c_exists else "Erreur"
            },
            "secondary": {
                "drive_present": d_drive_available,
                "path": str(SECONDARY_DB_PATH),
                "exists": d_exists,
                "size_kb": round(d_size, 1),
                "last_modified": d_time,
                "status": "Synchronisé" if (d_drive_available and d_exists) else ("Non disponible" if not d_drive_available else "En attente")
            }
        }

    @staticmethod
    def trigger_sync():
        """Déclenche manuellement la synchronisation vers D:."""
        db = get_db()
        success = db.sync_to_secondary()
        if success:
            return True, f"Base synchronisée avec succès sur {SECONDARY_DB_PATH}"
        else:
            if not SECONDARY_DRIVE.exists():
                return False, "Lecteur D: introuvable sur cette machine."
            return False, "Échec de la synchronisation vers la partition D:."

    @staticmethod
    def export_manual_backup(target_directory=None):
        """Crée une archive horodatée de sauvegarde de la base de données."""
        if not PRIMARY_DB_PATH.exists():
            return False, "Base de données principale introuvable."
        
        target_dir = Path(target_directory) if target_directory else (EXPORTS_DIR / "backups")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = target_dir / f"cosmetique_backup_{timestamp}.db"
        
        try:
            shutil.copy2(PRIMARY_DB_PATH, backup_filename)
            return True, f"Sauvegarde exportée avec succès : {backup_filename}"
        except Exception as e:
            return False, f"Erreur lors de l'export de sauvegarde : {e}"
