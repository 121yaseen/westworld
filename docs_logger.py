import os
import datetime
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# The Doc provided by the user
DEFAULT_DOC_ID = '1-j9UpwqoW915e0v2Uak1Y4zud1e8QCz0fZKuu0CPnhc'
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']

class DocsLogger:
    def __init__(self, doc_id: str = DEFAULT_DOC_ID):
        self.doc_id = doc_id
        self.service = None
        self.enabled = False
        
        try:
            # Attempt to get default credentials
            creds, _ = default(scopes=SCOPES)
            self.service = build('docs', 'v1', credentials=creds)
            self.enabled = True
            
            # Try to log immediately to verify permissions
            self.log(f"\n\n--- NEW SESSION STARTED: {datetime.datetime.now()} ---\n", verify=True)
            print(f"✅ Google Docs Live Logging enabled for Doc: {self.doc_id}")
            
        except Exception as e:
            self.enabled = False
            print(f"⚠️  Google Docs Logging Disabled. Reason: {e}")
            print("NOTE: Even public docs require API Authentication.")
            print("TRY THIS FIX: Run the following command in your terminal:")
            print("gcloud auth application-default login --scopes='https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive'")

    def log(self, text: str, verify: bool = False):
        if not self.enabled or not self.service:
            return

        try:
            # We append to the END of the document.
            doc = self.service.documents().get(documentId=self.doc_id).execute()
            content = doc.get('body').get('content')
            end_index = content[-1]['endIndex'] - 1 

            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': end_index
                        },
                        'text': text + "\n"
                    }
                }
            ]

            self.service.documents().batchUpdate(
                documentId=self.doc_id, body={'requests': requests}
            ).execute()
        except Exception as e:
            self.enabled = False # Disable logger on first error to prevent spam
            if verify:
                raise e # Let init catch it
            print(f"\n⚠️  Docs Logging Failed (Disabling Logger): {e}")
            if "insufficient authentication scopes" in str(e):
                print(">> PLEASE RUN: gcloud auth application-default login --scopes='https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive'")
