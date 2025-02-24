import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import auth, credentials, firestore
import requests
import json
import os

FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")  # Store as environment variable

if not firebase_admin._apps:
    if FIREBASE_CREDENTIALS:
        cred = credentials.Certificate(json.loads(FIREBASE_CREDENTIALS))
        firebase_admin.initialize_app(cred)
    else:
        st.error("❌ Firebase credentials are missing. Set them as an environment variable.")

db = firestore.client()

FIREBASE_WEB_API_KEY = "YOUR_FIREBASE_WEB_API_KEY"  # Replace with your actual API key

def login():
    """Handles user login and authentication."""
    st.title("🔐 Login to Your Portfolio")
    
    email = st.text_input("📧 Email", key="login_email")
    password = st.text_input("🔑 Password", type="password", key="login_password")

    if st.button("Login"):
        try:
            # Authenticate user using Firebase REST API
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
            payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, data=payload, headers=headers)
            res_data = response.json()

            if "idToken" in res_data:
                st.session_state["user"] = res_data["localId"]
                st.success(f"✅ Logged in as {email}")
                st.experimental_rerun()  # Redirect to dashboard
            else:
                st.error(f"❌ {res_data.get('error', {}).get('message', 'Invalid credentials.')}")
        
        except Exception as e:
            st.error(f"❌ Login failed: {str(e)}")

def signup():
    """Handles user registration."""
    st.title("🆕 Create an Account")

    email = st.text_input("📧 Email", key="signup_email")
    password = st.text_input("🔑 Password", type="password", key="signup_password")

    if st.button("Create Account"):
        try:
            # Register user using Firebase REST API
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
            payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, data=payload, headers=headers)
            res_data = response.json()

            if "idToken" in res_data:
                st.session_state["user"] = res_data["localId"]
                st.success(f"✅ Account created successfully! Welcome, {email}")
                st.experimental_rerun()
            else:
                st.error(f"❌ {res_data.get('error', {}).get('message', 'Could not create account.')}")
        
        except Exception as e:
            st.error(f"❌ Signup failed: {str(e)}")

def logout():
    """Logs out the user."""
    st.session_state["user"] = None
    st.experimental_rerun()

def authentication():
    """Displays login/signup page if user is not authenticated."""
    if "user" not in st.session_state or not st.session_state["user"]:
        tab1, tab2 = st.tabs(["🔐 Login", "🆕 Sign Up"])
        with tab1:
            login()
        with tab2:
            signup()
    else:
        st.sidebar.button("🚪 Logout", on_click=logout)

def save_portfolio(user_id, portfolio_df):
    """Saves the user's portfolio to Firestore so they can access it later."""
    if not user_id:
        st.error("❌ You must be logged in to save your portfolio.")
        return

    doc_ref = db.collection("portfolios").document(user_id)
    doc_ref.set({"portfolio": portfolio_df.to_dict()})
    st.success("✅ Portfolio saved successfully!")

def load_portfolio(user_id):
    """Retrieves the user's saved portfolio from Firestore."""
    if not user_id:
        st.error("❌ You must be logged in to load your portfolio.")
        return None

    doc_ref = db.collection("portfolios").document(user_id)
    doc = doc_ref.get()

    if doc.exists:
        return pd.DataFrame(doc.to_dict()["portfolio"])
    else:
        st.warning("⚠️ No saved portfolio found.")
        return None


