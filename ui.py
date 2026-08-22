import streamlit as st
st.set_page_config(page_title="DocScannerLLM", page_icon="✡")
st.title("Test Code")
st.write("Checking Browser")
st.divider()
st.header("Interactive")
user=st.text_input("Enter gibberish")
slider_val=st.slider("Check Slider", 1, 1000, 69)
st.header("Buttons")
if st.button("Click here"):
    st.snow()
    st.success("Test Complete")