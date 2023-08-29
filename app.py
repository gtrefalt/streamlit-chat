import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from apputils import (
    create_chat_interface,
    create_sidebar,
    create_history,
    create_user,
    create_users_from_auth_config,
)
import utils

# load config
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# get settings from config
auth_on = config["authentication"]["authentication_on"]
auth_config_file = config["authentication"]["authentication_config"]
st.session_state["all_models"] = config["models"]
models_list = list(config["models"].keys())


# create user table in db
@st.cache_data
def create_users(auth_config):
    create_users_from_auth_config(auth_config=auth_config)


# setup authenticator and users table
if auth_on:
    with open(auth_config_file) as file:
        auth_config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        auth_config["credentials"],
        auth_config["cookie"]["name"],
        auth_config["cookie"]["key"],
        auth_config["cookie"]["expiry_days"],
    )

    name, authentication_status, username = authenticator.login("Login", "main")

    create_users(auth_config)

else:
    name = "Anon"
    user_name = "Anonymous"
    email = "anon@anon.com"
    st.session_state["name"] = name
    st.session_state["username"] = user_name

    create_user(user_name, email)


if auth_on:
    # if model not yet set get the default model
    if not st.session_state.get("model", None):
        st.session_state["model"] = models_list[0]

    if st.session_state["authentication_status"]:
        # if authenticated show content
        create_chat_interface()
        create_sidebar(authenticator)
        create_history()

    # if not authenticated
    elif st.session_state["authentication_status"] is False:
        st.error("Username/password is incorrect")
    elif st.session_state["authentication_status"] is None:
        st.warning("Please enter your username and password")

# if authentication is not set, show the interface
elif not auth_on:
    authenticator = None

    # if model not yet set get the default model
    if not st.session_state.get("model", None):
        st.session_state["model"] = models_list[0]

    create_chat_interface()
    create_sidebar(authenticator)
    create_history()
