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
export APP_NAME=<your app name>
source .env
oc new-project $APP_NAME
oc new-build --binary --strategy=docker --name $APP_NAME
oc start-build $APP_NAME --from-dir . --follow
oc new-app -i $APP_NAME:latest --env-file .env
oc expose deploy $APP_NAME
oc expose service $APP_NAME
```