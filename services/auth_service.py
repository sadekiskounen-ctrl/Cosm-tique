import hashlib
from database.db_manager import get_db
from database.models import User

class AuthService:
    _current_user = None

    @classmethod
    def hash_password(cls, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @classmethod
    def login(cls, username: str, password: str) -> tuple[bool, str]:
        """Tente de connecter l'utilisateur. Retourne (Succès, Message)."""
        db = get_db()
        pwd_hash = cls.hash_password(password)
        
        rows = db.execute_query(
            "SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
            (username.strip(), pwd_hash)
        )
        
        if rows:
            row = rows[0]
            cls._current_user = User(
                id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                full_name=row["full_name"],
                role=row["role"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"]
            )
            return True, "Connexion réussie"
        else:
            return False, "Identifiant ou mot de passe incorrect"

    @classmethod
    def logout(cls):
        cls._current_user = None

    @classmethod
    def get_current_user(cls) -> User:
        return cls._current_user

    @classmethod
    def is_admin(cls) -> bool:
        return cls._current_user is not None and cls._current_user.role == "admin"

    @classmethod
    def get_all_users(cls):
        db = get_db()
        return db.execute_query("SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY id ASC")

    @classmethod
    def create_user(cls, username, password, full_name, role):
        db = get_db()
        pwd_hash = cls.hash_password(password)
        try:
            db.execute_query(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                (username.strip(), pwd_hash, full_name.strip(), role),
                commit=True
            )
            return True, "Utilisateur créé avec succès"
        except Exception as e:
            return False, f"Erreur : Nom d'utilisateur déjà utilisé ({e})"

    @classmethod
    def update_user(cls, user_id: int, username: str, full_name: str, role: str, password: str = None, is_active: bool = None) -> tuple[bool, str]:
        """Met à jour les informations d'un utilisateur (nom, identifiant, rôle, mot de passe éventuel)."""
        db = get_db()
        username = username.strip()
        full_name = full_name.strip()

        if not username or not full_name:
            return False, "L'identifiant et le nom complet sont obligatoires"

        # Vérifier si l'identifiant est déjà pris par un autre utilisateur
        existing = db.execute_query("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
        if existing:
            return False, "Cet identifiant est déjà utilisé par un autre compte"

        # Empêcher de retirer le rôle admin au dernier admin
        if role != "admin":
            admin_count = db.execute_query("SELECT COUNT(*) as c FROM users WHERE role = 'admin' AND is_active = 1 AND id != ?", (user_id,))
            if admin_count and admin_count[0]["c"] == 0:
                return False, "Impossible de rétrograder le dernier administrateur actif du système"

        try:
            if password and password.strip():
                pwd_hash = cls.hash_password(password.strip())
                if is_active is not None:
                    db.execute_query(
                        "UPDATE users SET username = ?, full_name = ?, role = ?, password_hash = ?, is_active = ? WHERE id = ?",
                        (username, full_name, role, pwd_hash, 1 if is_active else 0, user_id),
                        commit=True
                    )
                else:
                    db.execute_query(
                        "UPDATE users SET username = ?, full_name = ?, role = ?, password_hash = ? WHERE id = ?",
                        (username, full_name, role, pwd_hash, user_id),
                        commit=True
                    )
            else:
                if is_active is not None:
                    db.execute_query(
                        "UPDATE users SET username = ?, full_name = ?, role = ?, is_active = ? WHERE id = ?",
                        (username, full_name, role, 1 if is_active else 0, user_id),
                        commit=True
                    )
                else:
                    db.execute_query(
                        "UPDATE users SET username = ?, full_name = ?, role = ? WHERE id = ?",
                        (username, full_name, role, user_id),
                        commit=True
                    )
            return True, "Compte utilisateur mis à jour avec succès"
        except Exception as e:
            return False, f"Erreur lors de la modification : {e}"

    @classmethod
    def delete_user(cls, user_id: int) -> tuple[bool, str]:
        """Supprime un compte utilisateur en réassignant proprement l'historique financier."""
        db = get_db()
        
        # Vérifier si l'utilisateur existe
        u_rows = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
        if not u_rows:
            return False, "Utilisateur introuvable"
        
        target_user = u_rows[0]
        
        # Empêcher de supprimer le dernier admin
        if target_user["role"] == "admin":
            admin_count = db.execute_query("SELECT COUNT(*) as c FROM users WHERE role = 'admin' AND is_active = 1 AND id != ?", (user_id,))
            if admin_count and admin_count[0]["c"] == 0:
                return False, "Action refusée : Vous ne pouvez pas supprimer le seul administrateur du système."

        # Vérifier si c'est l'utilisateur actuellement connecté
        if cls._current_user and cls._current_user.id == user_id:
            return False, "Action refusée : Vous ne pouvez pas supprimer votre propre compte en session active."

        try:
            # Trouver un compte administrateur de secours pour conserver l'historique comptable
            admin_rows = db.execute_query("SELECT id FROM users WHERE role = 'admin' AND id != ? ORDER BY id ASC LIMIT 1", (user_id,))
            fallback_admin_id = admin_rows[0]["id"] if admin_rows else 1

            # 1. Réassigner les ventes et sessions de caisse pour préserver l'intégrité comptable et éviter l'erreur FOREIGN KEY
            db.execute_query("UPDATE sales SET user_id = ? WHERE user_id = ?", (fallback_admin_id, user_id), commit=True)
            db.execute_query("UPDATE cash_sessions SET user_id = ? WHERE user_id = ?", (fallback_admin_id, user_id), commit=True)
            db.execute_query("UPDATE stock_movements SET user_id = NULL WHERE user_id = ?", (user_id,), commit=True)

            # 2. Supprimer l'utilisateur
            db.execute_query("DELETE FROM users WHERE id = ?", (user_id,), commit=True)
            
            # 3. Réordonner les IDs pour qu'ils soient strictement consécutifs (1, 2, 3...)
            cls.resequence_user_ids()

            return True, f"Compte '{target_user['username']}' supprimé avec succès."
        except Exception as e:
            return False, f"Erreur lors de la suppression : {e}"

    @classmethod
    def resequence_user_ids(cls):
        """Réorganise les IDs utilisateurs pour qu'ils soient consécutifs (1, 2, 3...) sans trou."""
        db = get_db()
        users = db.execute_query("SELECT id, username FROM users ORDER BY id ASC")
        if not users:
            return

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            for new_id, u in enumerate(users, 1):
                old_id = u["id"]
                if old_id != new_id:
                    cursor.execute("UPDATE sales SET user_id = ? WHERE user_id = ?", (new_id, old_id))
                    cursor.execute("UPDATE cash_sessions SET user_id = ? WHERE user_id = ?", (new_id, old_id))
                    cursor.execute("UPDATE stock_movements SET user_id = ? WHERE user_id = ?", (new_id, old_id))
                    cursor.execute("UPDATE users SET id = ? WHERE id = ?", (new_id, old_id))
            
            # Réajuster la séquence auto-increment SQLite
            max_id = len(users)
            try:
                cursor.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'users'", (max_id,))
            except Exception:
                pass
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.commit()

        if cls._current_user:
            updated = db.execute_query("SELECT * FROM users WHERE username = ?", (cls._current_user.username,))
            if updated:
                cls._current_user.id = updated[0]["id"]

        db.sync_to_secondary()

    @classmethod
    def update_password(cls, user_id, new_password):
        db = get_db()
        pwd_hash = cls.hash_password(new_password)
        db.execute_query("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id), commit=True)
        return True, "Mot de passe mis à jour"

    @classmethod
    def toggle_user_status(cls, user_id, is_active):
        db = get_db()
        db.execute_query("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id), commit=True)
        return True, "Statut modifié"


