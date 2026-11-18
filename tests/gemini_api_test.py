
# ============================================
# SMARTPICK HUB - GEMINI API TESTING
# ============================================
# Purpose:
# 1. Verify Gemini API key
# 2. List available Gemini models
# 3. Test Gemini models
#
# Run this script in Google Colab.
# API key must be saved in Colab Secrets.
# Never add API keys directly to this file.

from google import genai
from google.colab import userdata

# STEP 1: Get API key securely
GEMINI_API_KEY = userdata.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in Google Colab Secrets."
    )

# STEP 2: Connect to Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# STEP 3: Verify API key and list models
print("Checking Gemini API key...")

try:
    models = list(client.models.list())

    print("\nAPI KEY VERIFIED SUCCESSFULLY!")
    print("\nAvailable models supporting generateContent:")

    for model in models:
        if "generateContent" in (model.supported_actions or []):
            print(model.name)

except Exception as error:
    print("\nAPI verification failed:")
    print(error)
    raise

# STEP 4: Test Gemini models
models_to_test = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]

working_model = None

for model_name in models_to_test:
    try:
        print(f"\nTesting: {model_name}")

        response = client.models.generate_content(
            model=model_name,
            contents="Reply only: SmartPick Hub AI is working!"
        )

        print("SUCCESS!")
        print(response.text)

        working_model = model_name
        break

    except Exception as error:
        print("Not working:", str(error)[:250])

# STEP 5: Final result
if working_model:
    print("\n================================")
    print("GEMINI TEST COMPLETED!")
    print("Working model:", working_model)
    print("================================")
else:
    print("\nNo tested model responded successfully.")
