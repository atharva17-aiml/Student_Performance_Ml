import logging
from database import get_connection

logging.basicConfig(level=logging.INFO)


def log_action(
    user_id=None,
    username=None,
    action="UNKNOWN",
    description=None,
    ip_address=None
):
    """
    Store an important application action in the audit log.
    """

    conn = None

    try:

        conn = get_connection()

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO audit_logs
            (
                user_id,
                username,
                action,
                description,
                ip_address
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                username,
                action,
                description,
                ip_address
            )
        )

        conn.commit()

        logging.info(
            f"AUDIT | user={username} | action={action}"
        )

    except Exception as e:

        logging.error(
            f"Audit log error: {e}"
        )

    finally:

        if conn and conn.is_connected():
            conn.close()


def get_audit_logs(limit=200):

    conn = None

    try:

        conn = get_connection()

        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT
                id,
                user_id,
                username,
                action,
                description,
                ip_address,
                created_at
            FROM audit_logs
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,)
        )

        return cur.fetchall()

    except Exception as e:

        logging.error(
            f"Error fetching audit logs: {e}"
        )

        return []

    finally:

        if conn and conn.is_connected():
            conn.close()