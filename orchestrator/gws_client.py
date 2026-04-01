import subprocess
import json
import logging
import os

logger = logging.getLogger("gws_client")

class GWSClient:
    """
    A robust Python bridge for the GWS CLI. 
    Bypasses shell-quoting issues by using subprocess lists.
    """
    
    @staticmethod
    def run_command(args: list):
        """Executes a gws command and returns the JSON output."""
        cmd = ["gws"] + args
        try:
            # Use subprocess without shell=True to avoid injection and quoting issues
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                logger.error(f"GWS Command Failed: {result.stderr}")
                return {"error": result.stderr, "code": result.returncode}
            
            # gws often outputs JSON
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"output": result.stdout.strip()}
                
        except Exception as e:
            logger.exception(f"Unexpected error running GWS: {e}")
            return {"error": str(e)}

    @classmethod
    def create_folder(cls, name: str, parent_id: str = None):
        """Creates a folder in Google Drive."""
        params = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            params["parents"] = [parent_id]
        
        return cls.run_command(["drive", "files", "create", "--params", json.dumps(params)])

    @classmethod
    def create_spreadsheet(cls, title: str, parent_id: str = None):
        """Creates a spreadsheet and optionally moves it to a parent folder."""
        params = {"properties": {"title": title}}
        # Note: gws sheets create doesn't support parents directly in the params
        # We create it first then move it if parent_id is provided.
        res = cls.run_command(["sheets", "spreadsheets", "create", "--params", json.dumps(params)])
        
        if parent_id and "spreadsheetId" in res:
            spreadsheet_id = res["spreadsheetId"]
            # To move, we add the parent and remove the current parents (usually 'root')
            file_info = cls.run_command(["drive", "files", "get", spreadsheet_id, "--params", '{"fields": "parents"}'])
            if "parents" in file_info:
                current_parents = ",".join(file_info["parents"])
                cls.run_command([
                    "drive", "files", "update", spreadsheet_id,
                    "--add-parents", parent_id,
                    "--remove-parents", current_parents
                ])
        
        return res

    @classmethod
    def append_rows(cls, spreadsheet_id: str, range_name: str, rows: list):
        """Appends rows to a spreadsheet."""
        params = {
            "spreadsheetId": spreadsheet_id,
            "range": range_name,
            "valueInputOption": "USER_ENTERED"
        }
        body = {"values": rows}
        return cls.run_command([
            "sheets", "spreadsheets", "values", "append", 
            "--params", json.dumps(params),
            "--json", json.dumps(body)
        ])

    @classmethod
    def send_gmail(cls, to: str, subject: str, body: str):
        """Sends an email via Gmail API."""
        # Simple RFC822 message construction
        message = f"To: {to}\r\nSubject: {subject}\r\n\r\n{body}"
        # GWS gmail send takes the raw message? Let's check help again.
        # Usually it takes a base64 encoded string or a json body.
        # But gws might handle construction. Let's use the simplest form.
        # Actually, let's use the 'users.messages.send' format.
        import base64
        encoded_message = base64.urlsafe_b64encode(message.encode()).decode()
        
        body_json = {"raw": encoded_message}
        return cls.run_command([
            "gmail", "users", "messages", "send",
            "--json", json.dumps(body_json)
        ])
