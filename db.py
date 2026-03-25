import os

import pg8000


def _get_cfg():
	return {
		"host": os.getenv("DB_HOST", "localhost"),
		"port": int(os.getenv("DB_PORT", "5432")),
		"database": os.getenv("DB_NAME", "postgres"),
		"user": os.getenv("DB_USER", os.getenv("USER") or os.getlogin()),
		"password": os.getenv("DB_PASS", ""),
	}


def get_conn():
	cfg = _get_cfg()
	return pg8000.connect(
		host=cfg["host"],
		port=cfg["port"],
		user=cfg["user"],
		password=cfg["password"],
		database=cfg["database"],
	)


def ensure_schema():
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id serial PRIMARY KEY,
				username text UNIQUE NOT NULL,
				password text NOT NULL
			)
			"""
		)
		cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role text DEFAULT 'user'")
		cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked boolean DEFAULT false")
		cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts integer DEFAULT 0")
		conn.commit()
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def get_user(username: str):
	if not username:
		return None
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute("SELECT id, username, password, role, blocked, failed_attempts FROM users WHERE username = %s", (username,))
		row = cur.fetchone()
		if not row:
			return None
		return {
			'id': row[0],
			'username': row[1],
			'password': row[2],
			'role': row[3],
			'blocked': row[4],
			'failed_attempts': row[5],
		}
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def increment_failed(username: str) -> tuple[int, bool]:
	if not username:
		return 0, False
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute("UPDATE users SET failed_attempts = COALESCE(failed_attempts,0) + 1 WHERE username = %s RETURNING failed_attempts", (username,))
		row = cur.fetchone()
		if not row:
			return 0, False
		attempts = row[0] or 0
		blocked = False
		if attempts >= 3:
			cur.execute("UPDATE users SET blocked = true WHERE username = %s", (username,))
			blocked = True
		conn.commit()
		return attempts, blocked
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def reset_failed(username: str):
	if not username:
		return
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute("UPDATE users SET failed_attempts = 0 WHERE username = %s", (username,))
		conn.commit()
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def block_user(username: str):
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute("UPDATE users SET blocked = true WHERE username = %s", (username,))
		conn.commit()
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def unlock_user(username: str):
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute("UPDATE users SET blocked = false, failed_attempts = 0 WHERE username = %s", (username,))
		conn.commit()
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def authenticate_user(username: str, password: str) -> dict:
	user = get_user(username)
	if not user:
		return {'ok': False, 'blocked': False, 'role': None, 'reason': 'no_user', 'attempts': 0}
	if user.get('blocked'):
		return {'ok': False, 'blocked': True, 'role': user.get('role'), 'reason': 'blocked', 'attempts': user.get('failed_attempts', 0)}
	if user.get('password') == password:
		reset_failed(username)
		return {'ok': True, 'blocked': False, 'role': user.get('role'), 'reason': 'ok', 'attempts': 0}
	attempts, blocked = increment_failed(username)
	return {'ok': False, 'blocked': blocked, 'role': user.get('role'), 'reason': 'wrong_password', 'attempts': attempts}


def test_connection() -> bool:
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute("SELECT 1")
		_ = cur.fetchone()
		return True
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def list_users():
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute("SELECT username FROM users ORDER BY id")
		return [row[0] for row in cur.fetchall()]
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def add_user(username: str, password: str, role: str = 'user') -> bool:
	if not username:
		return False
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute(
			"INSERT INTO users (username,password,role) VALUES (%s,%s,%s) ON CONFLICT (username) DO NOTHING",
			(username, password, role),
		)
		conn.commit()
		cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
		return cur.fetchone() is not None
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def delete_user(username: str) -> bool:
	if not username:
		return False
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute("DELETE FROM users WHERE username = %s", (username,))
		deleted = cur.rowcount
		conn.commit()
		return deleted > 0
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass


def update_user(username: str, password: str = None, role: str = None, blocked: bool = None) -> bool:
	if not username:
		return False
	conn = None
	cur = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		parts = []
		vals = []
		if password is not None:
			parts.append("password = %s")
			vals.append(password)
		if role is not None:
			parts.append("role = %s")
			vals.append(role)
		if blocked is not None:
			parts.append("blocked = %s")
			vals.append(blocked)
		if not parts:
			return False
		vals.append(username)
		sql = "UPDATE users SET " + ", ".join(parts) + " WHERE username = %s"
		cur.execute(sql, tuple(vals))
		updated = cur.rowcount
		conn.commit()
		return updated > 0
	finally:
		try:
			if cur:
				cur.close()
		except Exception:
			pass
		try:
			if conn:
				conn.close()
		except Exception:
			pass



