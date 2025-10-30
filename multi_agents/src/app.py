import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv
from agents.vision_processor import VisionProcessorAgent
from agents.explanation import ExplanationAgent
from agents.validation import ValidationAgent

# Load environment variables
load_dotenv()

# Initialize Agents
vision_processor = VisionProcessorAgent()
explanation_agent = ExplanationAgent(os.getenv('OPENAI_API_KEY'))
validation_agent = ValidationAgent(os.getenv('OPENAI_API_KEY'))

def main():
    st.title("Nutrition Label Analyzer")
    st.write("Upload an image of a nutrition label to get an easy-to-understand explanation")

    # File uploader
    uploaded_file = st.file_uploader("Choose a nutrition label image", type=['png', 'jpg', 'jpeg'])

    if uploaded_file:
        # Display the uploaded image
        st.image(uploaded_file, caption="Uploaded Image", width='stretch')

        if st.button("Analyze"):
            with st.spinner("Analyzing the nutrition label..."):
                # Save the uploaded file temporarily
                temp_path = Path("temp_image.jpg")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Process image with GPT-4 Vision
                image_result = vision_processor.process_image(temp_path)
                if image_result["status"] == "error":
                    st.error(f"Error processing image: {image_result['error']}")
                    return

                # Vision API returns structured data directly
                parse_result = {"status": "success", "data": image_result["data"], "error": None}

                # Show raw Vision API response
                with st.expander("GPT-4 Vision Response"):
                    st.code(image_result.get("text", ""))

                # show parsed items
                st.subheader("Parsed Items")
                parsed_data = parse_result["data"]
                items = parsed_data.get('items', [])
                if items:
                    # First show serving information if available
                    serving = parsed_data.get('serving', {})
                    if serving:
                        st.write("**Serving Information:**")
                        st.write(f"- Size: {serving.get('size', 'N/A')}")
                        st.write(f"- Per Container: {serving.get('per_container', 'N/A')}")
                    
                    st.write("**Nutrients:**")
                    for it in items:
                        amount = it.get('amount', '')
                        unit = it.get('unit', '')
                        pct = it.get('pct_dv')
                        pct_str = f" ({pct}% DV)" if pct is not None else ""
                        st.write(f"- {it.get('name', '')}: {amount}{unit}{pct_str}")
                else:
                    st.write("No items found in the nutrition label")

                # Validate results
                validation_result = validation_agent.validate_nutrition_data(
                    "",  # No raw text needed for Vision API results
                    parse_result["data"]
                )
                if validation_result["status"] == "error":
                    st.error(f"Error validating results: {validation_result['error']}")
                    return

                if not validation_result["is_valid"]:
                    st.warning("⚠️ The extracted information might not be completely accurate")
                    st.write("Validation Details:", validation_result["validation_details"])

                # Get explanation
                explanation_result = explanation_agent.explain_nutrition(parse_result["data"])
                if explanation_result["status"] == "error":
                    st.error(f"Error generating explanation: {explanation_result['error']}")
                    return

                # Display results
                st.success("Analysis Complete!")
                
                # Display summary
                st.subheader("Summary")
                st.write(explanation_result["summary"])

                # Display detailed explanations
                st.subheader("Detailed Breakdown")
                for nutrient, explanation in explanation_result["explanation"].items():
                    with st.expander(f"About {nutrient.title()}"):
                        st.write(explanation)

                # Clean up
                temp_path.unlink()

if __name__ == "__main__":
    main()