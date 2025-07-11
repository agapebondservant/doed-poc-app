import time
import math


#####################################
## ENABLE STREAMING RESPONSES ##
##################################### 
def stream_response(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.1)
        
def is_important_section(text, important_keywords: list = ["FROM REPORTER", "FROM ANALYST"]):
    return [i for i in important_keywords if i in text]
  
#####################################
## WIDGET PROPERTY CONFIGURATION ##
#####################################         
def estimate_scroll_height(text: str, 
                           estimated_line_height: int = 50, 
                           max_scroll_height: int = 200) -> int :
    if not text:
        return max_scroll_height
    if is_important_section(text):
        return max_scroll_height
    num_newlines = text.count("\n")
    num_charlines = math.ceil(len(text) / 100)
    return int(min(max_scroll_height, (num_charlines + num_newlines) * estimated_line_height))

#####################################
## INTERRUPTS ##
##################################### 
  
def handle_interrupt(interrupt, config, st):
    """
    Handles human interruptions in the self.workflow.
    """
    questions = ("<br>").join(interrupt[0].value)
    
    with st.chat_message(name="assistant",avatar="images/redhat.png"):
    
        st.subheader("Please tell me more about yourself.", divider=True,)
        
        with st.popover("I need guidance"):
        
            st.markdown(f"{questions}", unsafe_allow_html=True, )
        
        if input_text := st.text_area("Your answer"):
        
            return input_text


#####################################
## CHAT UI VIEW ##
##################################### 
def render_question_chat(response_content, 
                         config, 
                         st):
    
    with st.chat_message(name="assistant",avatar="images/redhat.png"):
        
        if is_important_section(response_content):
            st.write_stream(stream_response(response_content))
            
        else:
            with st.expander("🚧 Processing is ongoing. Click to expand/collapse...", expanded=True):
                st.write_stream(stream_response(response_content))
            