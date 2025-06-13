import streamlit as st
import requests
import tempfile
import markdown2
from weasyprint import HTML

st.set_page_config(page_title="EventPlanGenie", page_icon="🎉", layout="wide")
st.title("EventPlanGenie")
st.caption("Your personalized multi-agent event planning assistant powered by Agentic AI.")

def convert_markdown_to_pdf(markdown_text: str):
    html = markdown2.markdown(markdown_text)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        HTML(string=html).write_pdf(tmp_pdf.name)
        return tmp_pdf.name

for key in ["submitted", "options", "selected_idea", "selected_venue", "selected_vendor", "final_output"]:
    if key not in st.session_state:
        st.session_state[key] = None

if not st.session_state["submitted"]:
    st.markdown("## 📝 Step 1: Describe Your Event")

    with st.form("event_form"):
        col1, col2 = st.columns(2)
        with col1:
            event_name = st.text_input("📛 Event Name")
            location = st.text_input("📍 Location")
            date = st.date_input("📅 Event Date")
        with col2:
            event_type = st.selectbox("📂 Event Type", ["Wedding", "Birthday", "Corporate", "Concert", "Custom"])
            description = st.text_area("📝 Brief Description", height=150, placeholder="Describe the theme, vibe, or purpose...")

        submitted = st.form_submit_button("✨ Generate Ideas & Options")

    if submitted:
        with st.spinner("🤖 Generating options from AI agents..."):
            try:
                res = requests.post("http://localhost:8000/generate", json={
                    "event_name": event_name,
                    "event_type": event_type,
                    "location": location,
                    "date": str(date),
                    "description": description
                })

                if res.status_code == 200:
                    st.session_state["submitted"] = {
                        "event_name": event_name,
                        "event_type": event_type,
                        "location": location,
                        "date": str(date),
                        "description": description
                    }
                    st.session_state["options"] = res.json()
                    st.experimental_rerun()
                else:
                    st.error(f"❌ Backend error: {res.status_code}\n\n{res.text}")

            except Exception as e:
                st.error(f"🚨 Request failed:\n\n{e}")

elif st.session_state["submitted"] and not st.session_state["selected_idea"]:
    st.markdown("## 🎯 Step 2: Select Your Preferences")
    st.subheader("🎨 Choose an Idea")
    idea = st.radio("Ideas", st.session_state["options"].get("ideas", []))
    if st.button("✅ Select This Idea"):
        st.session_state["selected_idea"] = idea
        st.experimental_rerun()

elif st.session_state["selected_idea"] and not st.session_state["selected_venue"]:
    st.markdown("## 📍 Step 3: Choose a Venue")
    venue = st.radio("Venues", st.session_state["options"].get("venues", []))
    if st.button("✅ Select This Venue"):
        st.session_state["selected_venue"] = venue
        st.experimental_rerun()

elif st.session_state["selected_venue"] and not st.session_state["selected_vendor"]:
    st.markdown("## 🛍️ Step 4: Choose a Vendor Package")
    vendor = st.radio("Vendor Packages", st.session_state["options"].get("vendors", []))
    if st.button("✅ Select This Vendor"):
        st.session_state["selected_vendor"] = vendor
        st.experimental_rerun()

elif all([st.session_state.get("selected_idea"), st.session_state.get("selected_venue"), st.session_state.get("selected_vendor")]):
    st.markdown("## ✅ Step 5: Finalize Your Event Plan")
    if st.button("🎉 Generate Final Event Plan"):
        with st.spinner("🛠️ Finalizing your event plan..."):
            payload = {
                **st.session_state["submitted"],
                "selected_idea": st.session_state["selected_idea"],
                "selected_venue": st.session_state["selected_venue"],
                "selected_vendor": st.session_state["selected_vendor"]
            }

            try:
                final_res = requests.post("http://localhost:8000/generate_final_plan", json=payload)

                if final_res.status_code == 200:
                    final_output = final_res.json().get("final_output", "⚠️ No final plan generated.")
                    st.session_state["final_output"] = final_output
                    st.experimental_rerun()
                else:
                    st.error(f"❌ Backend error: {final_res.status_code}\n\n{final_res.text}")
            except Exception as e:
                st.error(f"🚨 Final plan request failed:\n\n{e}")

if st.session_state["final_output"]:
    st.markdown("## 📄 Finalized Event Plan")
    with st.expander("🔍 View Full Plan", expanded=True):
        st.markdown(st.session_state["final_output"], unsafe_allow_html=True)

    pdf_path = convert_markdown_to_pdf(st.session_state["final_output"])
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="🧾 Download as PDF",
            data=f.read(),
            file_name=f"{st.session_state['submitted']['event_name'].replace(' ', '_')}_event_plan.pdf",
            mime="application/pdf"
        )

    with st.expander("📧 Email This Plan"):
        recipient_email = st.text_input("Enter recipient email:")
        if st.button("📤 Send Email"):
            if recipient_email:
                email_payload = {
                    **st.session_state["submitted"],
                    "selected_idea": st.session_state["selected_idea"],
                    "selected_venue": st.session_state["selected_venue"],
                    "selected_vendor": st.session_state["selected_vendor"],
                    "recipient_email": recipient_email
                }
                email_res = requests.post("http://localhost:8000/send_email", json=email_payload)

                if email_res.status_code == 200 and email_res.json().get("success"):
                    st.success("✅ Email sent successfully!")
                else:
                    st.error(f"❌ Failed to send email.\n{email_res.json()}")
