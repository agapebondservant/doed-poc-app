# Sample Generative / Agentic AI App
To run the app locally:
  1. Set up a virtual environment: python3.12 -m venv venv
  2. Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  3. Install dependencies: pip install -r requirements.txt
  4. Start the app: python3 -m streamlit run app.py
  

To deploy the app:
1. Deploy Chroma:

```
oc new-project chroma
helm repo add chroma https://amikos-tech.github.io/chromadb-chart/
helm repo update
helm install chroma chroma/chromadb
oc expose service chroma-chromadb
```

2. Update .env-template and make a copy of the file (name it ".env")
3. Run the script below:

```
export APP_NAME=<your app name>
source .env
oc new-project $APP_NAME
oc new-build --binary --strategy=docker --name $APP_NAME
oc start-build $APP_NAME --from-dir . --follow
oc new-app -i $APP_NAME:latest --env-file .env
oc create -f openshift/pvc.yaml
oc set volume deployment/$APP_NAME --add --name=huggingface -t pvc --claim-name=huggingface-pvc --mount-path=/app/.cache 
oc expose deploy $APP_NAME --port 8501
oc expose service $APP_NAME
```
4. The app should be accessible at the FQDN below:
  
  ```
  echo http://$(oc get route -o json | jq -r '.items[0].spec.host')
  ```

5. Troubleshooting:
  
  ```
  oc logs $(oc get pod -o name -l deployment=$APP_NAME)
  ```
  
5. To delete the app:

```
oc delete all,configmap,pvc,serviceaccount,rolebinding --selector app=$APP_NAME
oc delete buildconfig $APP_NAME
oc delete imagestreamtag $APP_NAME:latest
oc delete -f openshift/pvc.yaml
```