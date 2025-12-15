from db_manager import *
from db_tools import *

def create_all_tables(db_manager):
    """
    Create all necessary tables for the application using DatabaseManager instance.
    
    Args:
        db_manager: An initialized DatabaseManager instance
    """
    db_manager.create_table(
        "clients",
        "(client_id INT PRIMARY KEY,client_username VARCHAR(255), client_password VARCHAR(255), client_ip VARCHAR(255), client_port INT, client_last_active VARCHAR(255), client_ddos_status BOOLEAN)"
    )
    
    db_manager.create_table(
        "files",
        "(file_id INT PRIMARY KEY, file_owner_id INT, file_original_path VARCHAR(255), file_result_path VARCHAR(255), file_orig_size VARCHAR(255), file_new_size VARCHAR(255))"
    )


def populate_clients(db_manager):
    all_rows = get_all_rows("clients")
    if len(all_rows) == 0:
        insert_row("clients",
                           "(client_id, client_username, client_password, client_ip, client_port, client_last_active, client_ddos_status)",
                           "(%s, %s, %s, %s, %s, %s, %s)",
                           (1, "user", 0, 0, 0, 0, False))