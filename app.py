import streamlit as st
import pandas as pd
import anthropic
import httpx

st.set_page_config(page_title="Amazon Reply Generator", page_icon="🤖", layout="wide")

st.title("🤖 Amazon Seller Reply Generator")
st.markdown("Automatically generate professional replies to customer reviews using AI")

# Sidebar for API key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Anthropic API Key", type="password", help="Get your key from console.anthropic.com")
    st.markdown("---")
    st.markdown("### 📝 CSV Format Required:")
    st.code("customer_name,rating,review_text,customer_email")
    st.markdown("**Example:**")
    st.code("John Doe,5,Great product!,john@example.com")

# Initialize session state
if 'reviews_df' not in st.session_state:
    st.session_state.reviews_df = None
if 'generated_replies' not in st.session_state:
    st.session_state.generated_replies = None

# Tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload Reviews", "✨ Generate Replies", "📧 Preview"])

with tab1:
    st.header("Step 1: Load Your Reviews")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload CSV file with reviews", type=['csv'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Load Sample Reviews"):
            sample_data = {
                'customer_name': ['John Smith', 'Sarah Johnson', 'Mike Brown', 'Emily Davis', 'Robert Wilson'],
                'rating': [5, 2, 4, 1, 5],
                'review_text': [
                    'Excellent product! Exceeded my expectations. Fast delivery too.',
                    'Product arrived damaged. Very disappointed with the packaging.',
                    'Good quality but took longer to arrive than expected.',
                    'Not as described. Color was completely different. Requesting refund.',
                    'Amazing! This is exactly what I needed. Will buy again!'
                ],
                'customer_email': [
                    'john.smith@email.com',
                    'sarah.j@email.com',
                    'mike.b@email.com',
                    'emily.d@email.com',
                    'robert.w@email.com'
                ]
            }
            st.session_state.reviews_df = pd.DataFrame(sample_data)
            st.success(f"✅ Sample data loaded! ({len(st.session_state.reviews_df)} reviews)")
    
    # Process uploaded file
    if uploaded_file:
        try:
            st.session_state.reviews_df = pd.read_csv(uploaded_file)
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
                status_text.empty()
                progress_bar.empty()
                st.success("✅ All replies generated successfully!")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tab3:
    st.header("Step 3: Preview & Send")
    
    if st.session_state.generated_replies is None:
        st.warning("⚠️ Please generate replies first in the 'Generate Replies' tab")
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

st.markdown("---")
st.markdown("Built with ❤️ using Streamlit + Claude API")
