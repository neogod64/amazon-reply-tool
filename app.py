import streamlit as st
import pandas as pd
import anthropic

# Page config
st.set_page_config(page_title="Amazon Review Reply Tool", layout="wide")

# Initialize session state
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'reviews_df' not in st.session_state:
    st.session_state.reviews_df = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

# Sidebar for API key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Claude API Key", type="password", help="Get from console.anthropic.com")
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ API Key loaded!")

# Main content
st.title("🤖 Amazon Seller Reply Generator")
st.markdown("Automatically generate professional replies to customer reviews using AI")

# Tab 1: Upload Reviews
tab1, tab2, tab3 = st.tabs(["📤 Upload Reviews", "✨ Generate Replies", "📧 Send Emails"])

with tab1:
    st.subheader("Step 1: Upload Your Reviews")
    
    st.markdown("---")
    if st.button("📋 Load Sample Reviews (for testing)", key="sample_data"):
        sample_data = {
            'review_id': ['R001', 'R002', 'R003', 'R004', 'R005'],
            'customer_name': ['John Smith', 'Sarah Johnson', 'Mike Chen', 'Emily Davis', 'Robert Wilson'],
            'customer_email': ['john@email.com', 'sarah@email.com', 'mike@email.com', 'emily@email.com', 'robert@email.com'],
            'rating': [5, 4, 5, 3, 5],
            'review_text': [
                'Amazing product! Arrived quickly and exactly as described. Highly recommend!',
                'Good quality but shipping took longer than expected. Still satisfied.',
                'Excellent! Best purchase I\'ve made this year. Customer service was great too.',
                'Decent product but a bit overpriced. Expected better for this cost.',
                'Perfect! This is my second purchase. Love the durability.'
            ],
            'product_name': ['Wireless Earbuds', 'Phone Case', 'Wireless Earbuds', 'USB Cable', 'Wireless Earbuds']
        }
        st.session_state.reviews_df = pd.DataFrame(sample_data)
        st.success("✅ Sample data loaded! (5 reviews)")
        st.dataframe(st.session_state.reviews_df, width='stretch')

with tab2:
    st.subheader("Step 2: Generate AI Replies")
    
    if st.session_state.reviews_df is None:
        st.warning("⚠️ Please load reviews first!")
    else:
        if not st.session_state.api_key:
            st.error("❌ Please enter your Claude API Key in the sidebar!")
        else:
            if st.button("🚀 Generate All Replies", key="generate_all"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                client = anthropic.Anthropic(api_key=st.session_state.api_key)
                
                for idx, row in st.session_state.reviews_df.iterrows():
                    review_id = row['review_id']
                    
                    if review_id not in st.session_state.responses:
                        prompt = f"""You are a professional Amazon seller responding to customer reviews. 
Generate a warm, professional, and personalized reply to this review. Keep it concise (2-3 sentences max).
Address the customer by name if positive, offer solution if negative.

Customer Name: {row['customer_name']}
Product: {row['product_name']}
Rating: {row['rating']}/5
Review: {row['review_text']}

Write ONLY the reply message, nothing else."""
                        
                        try:
                            message = client.messages.create(
                                model="claude-opus-4-1-20250805",
                                max_tokens=200,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            st.session_state.responses[review_id] = message.content[0].text
                        except Exception as e:
                            st.session_state.responses[review_id] = f"Error: {str(e)}"
                    
                    progress = (idx + 1) / len(st.session_state.reviews_df)
                    progress_bar.progress(progress)
                    status_text.text(f"Generating reply {idx + 1}/{len(st.session_state.reviews_df)}...")
                
                status_text.text("✅ All replies generated!")
            
            # Display generated replies
            if st.session_state.responses:
                st.markdown("---")
                st.subheader("📝 Review Replies (Edit if needed)")
                
                for idx, row in st.session_state.reviews_df.iterrows():
                    review_id = row['review_id']
                    
                    with st.expander(f"📌 {row['customer_name']} - {row['product_name']} ({row['rating']}⭐)", expanded=False):
                        st.markdown(f"**Email:** {row['customer_email']}")
                        st.markdown(f"**Review:** {row['review_text']}")
                        st.markdown("---")
                        
                        original_reply = st.session_state.responses.get(review_id, "")
                        edited_reply = st.text_area(
                            "Your reply:",
                            value=original_reply,
                            height=100,
                            key=f"reply_{review_id}"
                        )
                        
                        st.session_state.responses[review_id] = edited_reply

with tab3:
    st.subheader("Step 3: Send Replies via Email")
    
    if not st.session_state.responses:
        st.warning("⚠️ Generate replies first!")
    else:
        st.info("📧 Email sending ready (foundation for phase 2)")
        
        preview_data = []
        for idx, row in st.session_state.reviews_df.iterrows():
            preview_data.append({
                'Customer': row['customer_name'],
                'Email': row['customer_email'],
                'Product': row['product_name'],
                'Reply': st.session_state.responses.get(row['review_id'], '')[:80] + '...'
            })
        
        preview_df = pd.DataFrame(preview_data)
        st.dataframe(preview_df, width='stretch')
        st.success(f"✅ Ready to send {len(preview_df)} emails!")

st.markdown("---")
st.markdown("Built with ❤️ using Streamlit + Claude API")
```
