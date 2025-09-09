# firebase_config.py

import firebase_admin
from firebase_admin import credentials, firestore
import os
from django.conf import settings
from django.utils.functional import LazyObject

class FirestoreClient(LazyObject):
    def _setup(self):
        if not firebase_admin._apps:
            try:
                cred_path = os.path.join(settings.BASE_DIR, 'secrets', '/home/user/test1/test2-2c8fe-firebase-adminsdk-fbsvc-fde22105a1.json')

                if not os.path.exists(cred_path):
                    raise FileNotFoundError(f"Firebase credentials file not found at: {cred_path}")

                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK successed")
            
            except Exception as e:
                print(f"Firebase Admin SDK false")
                raise e

        self._wrapped = firestore.client()

db = FirestoreClient()