import streamlit as st
import pandas as pd
import anthropic
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Amazon Reply Generator", page_icon="🤖", layout="wide")

st.title("🤖 Amazon Seller Reply Generator")
st.markdown("Automatically generate professional replies to customer reviews using AI")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("🔑 Anthropic API")
    api_key = st.text_input("Anthropic API Key", type="password", help="Get your key from console.anthropic.com")
    
    st.markdown("---")
    
    st.subheader("📧 Gmail Settings")
    sender_email = st.text_input("Your Gmail Address", placeholder="seller@gmail.com")
    sender_password = st.text_input("Gmail App Password", type="password", help="Generate from Google Account > Security > 2-Step Verification > App Passwords")
    
    st.markdown("---")
    st.markdown("### 📝 CSV Format Required:")
    st.code("customer_name,rating,review_text,customer_email")
    st.markdown("**Example:**")
    st.code("John Doe,5,Great product!,john@example.com")
    
    with st.expander("ℹ️ How to get Gmail App Password"):
        st.markdown("""
        1. Go to your Google Account
        2. Security → 2-Step Verification (enable it)
        3. App Passwords → Generate new
        4. Select 'Mail' and 'Other'
        5. Copy the 16-character password
        """)

# Initialize session state
if 'reviews_df' not in st.session_state:
    st.session_state.reviews_df = None
if 'generated_replies' not in st.session_state:
    st.session_state.generated_replies = None
if 'emails_sent' not in st.session_state:
    st.session_state.emails_sent = []
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Reviews", "✨ Generate Replies", "📧 Preview", "🚀 Send Emails"])

with tab1:
    st.header("Step 1: Load Your Reviews")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload CSV file with reviews", type=['csv'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Load Sample Reviews"):
            sample_data = {
                'customer_name': ['Naveen Meena', 'Sarah Johnson', 'Mike Brown', 'Emily Davis', 'Robert Wilson'],
                'rating': [5, 2, 4, 1, 5],
                'review_text': [
                    'Excellent product! Exceeded my expectations. Fast delivery too.',
                    'Product arrived damaged. Very disappointed with the packaging.',
                    'Good quality but took longer to arrive than expected.',
                    'Not as described. Color was completely different. Requesting refund.',
                    'Amazing! This is exactly what I needed. Will buy again!'
                ],
                'customer_email': [
                    'nmeena64@gmail.com',
                    'sarah.j@email.com',
                    'mike.b@email.com',
                    'emily.d@email.com',
                    'robert.w@email.com'
                ]
            }
            st.session_state.reviews_df = pd.DataFrame(sample_data)
            st.session_state.last_uploaded_file = None  # Clear uploaded file tracking
            # Reset replies when new data is loaded
            st.session_state.generated_replies = None
            st.session_state.emails_sent = []
            st.success(f"✅ Sample data loaded! ({len(st.session_state.reviews_df)} reviews)")
    
    # Process uploaded file ONLY if it's a new file
    if uploaded_file is not None:
        # Check if this is a new file
        file_id = uploaded_file.file_id if hasattr(uploaded_file, 'file_id') else uploaded_file.name
        
        if file_id != st.session_state.last_uploaded_file:
            try:
                st.session_state.reviews_df = pd.read_csv(uploaded_file)
                st.session_state.last_uploaded_file = file_id
                # Reset replies when new data is loaded
                st.session_state.generated_replies = None
                st.session_state.emails_sent = []
                st.success(f"✅ File uploaded! ({len(st.session_state.reviews_df)} reviews)")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    # Display loaded data
    if st.session_state.reviews_df is not None:
        st.subheader("📊 Loaded Reviews")
        st.dataframe(st.session_state.reviews_df, use_container_width=True)

with tab2:
    st.header("Step 2: Generate AI Replies")
    
    if st.session_state.reviews_df is None:
        st.warning("⚠️ Please upload reviews first in the 'Upload Reviews' tab")
    elif not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar")
    else:
        if st.button("✨ Generate Replies", type="primary"):
            try:
                # Initialize Anthropic client with custom http client (no proxies)
                http_client = httpx.Client(proxies=None)
                client = anthropic.Anthropic(
                    api_key=api_key,
                    http_client=http_client
                )
                
                replies = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, row in st.session_state.reviews_df.iterrows():
                    status_text.text(f"Generating reply {idx + 1}/{len(st.session_state.reviews_df)}...")
                    
                    # Create prompt for Claude
                    prompt = f"""You are a professional Amazon seller. Generate a personalized, empathetic reply to this customer review.

Customer: {row['customer_name']}
Rating: {row['rating']}/5 stars
Review: {row['review_text']}

Write a professional reply that:
- Thanks the customer by name
- Addresses their specific feedback
- Is warm and genuine
- Is 2-3 sentences long
- For negative reviews, apologizes and offers to help resolve the issue

Reply:"""
                    
                    # Call Claude API
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=200,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    reply = message.content[0].text.strip()
                    replies.append(reply)
                    
                    progress_bar.progress((idx + 1) / len(st.session_state.reviews_df))
                
                # Store replies
                st.session_state.generated_replies = replies
                st.session_state.emails_sent = []  # Reset sent status
                status_text.empty()
                progress_bar.empty()
                st.success("✅ All replies generated successfully!")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tab3:
    st.header("Step 3: Preview & Edit")
    
    if st.session_state.generated_replies is None:
        st.warning("⚠️ Please generate replies first in the 'Generate Replies' tab")
    elif len(st.session_state.generated_replies) != len(st.session_state.reviews_df):
        st.error("⚠️ Data mismatch detected. Please regenerate replies in the 'Generate Replies' tab")
    else:
        preview_data = []
        for idx, row in st.session_state.reviews_df.iterrows():
            preview_data.append({
                'Customer': row['customer_name'],
                'Rating': f"{'⭐' * row['rating']}",
                'Review': row['review_text'][:50] + "...",
                'Generated Reply': st.session_state.generated_replies[idx],
                'Email': row['customer_email']
            })
        
        preview_df = pd.DataFrame(preview_data)
        st.dataframe(preview_df, use_container_width=True)
        st.success(f"✅ {len(preview_df)} replies ready to send!")
        st.info("💡 Proceed to 'Send Emails' tab to send these replies to customers")

with tab4:
    st.header("Step 4: Send Emails to Customers")
    
    if st.session_state.generated_replies is None:
        st.warning("⚠️ Please generate replies first in the 'Generate Replies' tab")
    elif not sender_email or not sender_password:
        st.warning("⚠️ Please configure your Gmail settings in the sidebar")
    elif len(st.session_state.generated_replies) != len(st.session_state.reviews_df):
        st.error("⚠️ Data mismatch detected. Please regenerate replies in the 'Generate Replies' tab")
    else:
        st.info(f"📧 Ready to send {len(st.session_state.generated_replies)} emails from **{sender_email}**")
        
        # Email subject customization
        email_subject = st.text_input("Email Subject", value="Thank you for your review!")
        
        # Show what will be sent
        with st.expander("📋 Preview Email Content (First Review)"):
            if len(st.session_state.reviews_df) > 0:
                first_customer = st.session_state.reviews_df.iloc[0]['customer_name']
                first_reply = st.session_state.generated_replies[0]
                first_email = st.session_state.reviews_df.iloc[0]['customer_email']
                
                st.markdown(f"**To:** {first_email}")
                st.markdown(f"**Subject:** {email_subject}")
                st.markdown(f"**Body:**")
                st.text_area("", value=first_reply, height=150, disabled=True)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🚀 Send All Emails", type="primary"):
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    success_count = 0
                    
                    for idx, row in st.session_state.reviews_df.iterrows():
                        status_text.text(f"Sending email {idx + 1}/{len(st.session_state.reviews_df)}...")
                        
                        # Create email
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = row['customer_email']
                        msg['Subject'] = email_subject
                        
                        # Email body
                        body = st.session_state.generated_replies[idx]
                        msg.attach(MIMEText(body, 'plain'))
                        
                        # Send email via Gmail SMTP
                        try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(sender_email, sender_password)
                            server.send_message(msg)
                            server.quit()
                            
                            st.session_state.emails_sent.append({
                                'customer': row['customer_name'],
                                'email': row['customer_email'],
                                'status': '✅ Sent'
                            })
                            success_count += 1
                            
                        except Exception as email_error:
                            st.session_state.emails_sent.append({
                                'customer': row['customer_name'],
                                'email': row['customer_email'],
                                'status': f'❌ Failed: {str(email_error)}'
                            })
                        
                        progress_bar.progress((idx + 1) / len(st.session_state.reviews_df))
                    
                    status_text.empty()
                    progress_bar.empty()
                    st.success(f"✅ Email sending complete! {success_count}/{len(st.session_state.reviews_df)} sent successfully")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Show sending results
        if st.session_state.emails_sent:
            st.subheader("📊 Email Sending Results")
            results_df = pd.DataFrame(st.session_state.emails_sent)
            st.dataframe(results_df, use_container_width=True)

st.markdown("---")
st.markdown("Built with ❤️ using Streamlit + Claude API")
