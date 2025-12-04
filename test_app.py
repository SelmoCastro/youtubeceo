import streamlit as st
try:
    from moviepy.editor import *
    st.write("MoviePy imported successfully!")
except Exception as e:
    st.error(f"Error importing MoviePy: {e}")
