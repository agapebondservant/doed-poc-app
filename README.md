# Sample Generative / Agentic AI App
To run the app locally:
  1. Set up a virtual environment: python3.12 -m venv venv
  2. Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  3. Install dependencies: pip install -r requirements.txt
  4. Start the app: python3 -m streamlit run app.py
  

To deploy the app:
1. Update .env-template and make a copy of the file (name it ".env")
2. Run the script below:

```
source .env
oc new-build --binary --strategy=docker --name $APP_NAME
oc start-build $APP_NAME --from-dir . --follow
oc new-app -i $APP_NAME:latest -e VLLM_TARGET_DEVICE=$VLLM_TARGET_DEVICE -e CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES -e GRANITE_API_KEY=$GRANITE_API_KEY -e GRANITE_API_BASE=$GRANITE_API_BASE -e TAVILY_API_KEY=$TAVILY_API_KEY
oc expose deploy $APP_NAME
oc expose service $APP_NAME
```