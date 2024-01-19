#----------Import libraries----------# 
import streamlit as st
import psycopg2
import os
import time as t
import vertexai
from vertexai.language_models import ChatModel, InputOutputTextPair
from vertexai.language_models import CodeChatModel
from vertexai.preview.generative_models import GenerativeModel, Part
import base64
from vertexai.preview.generative_models import GenerativeModel, Part

#----------Database Credentials----------# 
DB_NAME=os.getenv("DB_NAME") 
DB_USER=os.getenv("DB_USER")
DB_HOST= os.getenv("DB_HOST")
DB_PORT=os.getenv("DB_PORT")
DB_PASSWORD=os.getenv("DB_PASSWORD")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD")
SPECIAL_NAME=os.getenv("SPECIAL_NAME")
#----------Cloud Credentials----------# 
PROJECT_NAME=os.getenv("PROJECT_NAME")
vertexai.init(project=PROJECT_NAME, location="us-central1")

#----------Page Configuration----------# 
st.set_page_config(page_title="Matt Cloud Tech",
                   page_icon=":cloud:" ,
                   layout="wide")

#--------------Title----------------------#
st.header("", divider="rainbow")

#----------Connect to a database----------# 
def connection():
    con = psycopg2.connect(f"""
                           dbname={DB_NAME}
                           user={DB_USER}
                           host={DB_HOST}
                           port={DB_PORT}
                           password={DB_PASSWORD}
                           """)
    cur = con.cursor()
    # Create a table if not exists
    
    # Multimodal
    # cur.execute("DROP TABLE <TABLE_NAME>")
    cur.execute("CREATE TABLE IF NOT EXISTS toolkit_db(id serial PRIMARY KEY, name varchar, prompt varchar, output varchar, model varchar, time varchar, start_time float, end_time float, image_detail varchar, saved_image_data_base_string varchar, total_input_characters int, total_output_characters int)")
    cur.execute("CREATE TABLE IF NOT EXISTS guest_toolkit_db(id serial PRIMARY KEY, name varchar, prompt varchar, output varchar, model varchar, time varchar, start_time float, end_time float, image_detail varchar, saved_image_data_base_string varchar, total_input_characters int, total_output_characters int)")
    
    # Guest Limit
    cur.execute("CREATE TABLE IF NOT EXISTS toolkit_guest_chats(id serial PRIMARY KEY, name varchar, prompt varchar, output varchar, model varchar, time varchar, count_prompt int)")
    
    # Total Prompts
    # cur.execute("DROP TABLE total_prompts")
    cur.execute("CREATE TABLE IF NOT EXISTS total_prompts(id serial PRIMARY KEY, name varchar, prompt varchar, output varchar, model varchar, time varchar, count_prompt int)")

    # Counter
    cur.execute("CREATE TABLE IF NOT EXISTS chat_view_counter(id serial PRIMARY KEY, view int, time varchar)")
    
    con.commit()
    return con, cur


#----------Models----------#
def models():
    # Chat Capable Model
    mm_model = GenerativeModel("gemini-pro")
    mm_chat = mm_model.start_chat()
    # print(mm_chat.send_message("""Hi. I'm Matt.""", generation_config=mm_config))
    
    return mm_model, mm_chat



def main():
    mm_model, mm_chat = models()
    column_num_A = 1.5
    column_num_B = 2
    round_number = 2
    limit_query = 1
    count_prompt = 1
    info_sample_prompts = """
                        You can now start the conversation by prompting in the text bar. You can ask:
                        * List the things you are capable of doing 
                        * What is Cloud Computing? Explain it at different levels, such as beginner, intermediate, and advanced
                        * What is Google Cloud? Important Google Cloud Services to know
                        * Compare Site Reliability Engineering with DevOps
                        * Tell me about different cloud services
                        * Explain Multimodal Model in simple terms
                        """
    current_time = t.strftime("Date: %Y-%m-%d | Time: %H:%M:%S UTC")
    prompt_error = "Sorry about that. Please prompt it again, prune the history, or change the model if the issue persists."
    button_streaming = False
    output = ""
    sleep_time = 1
    prompt_character_limit = 5000
    prompt_character_limit_text = f""":red[CHARACTER LIMIT]: Exceeds the prompt character limit of :blue[{prompt_character_limit}]""" 
    current_model = ""
    
    apps = st.selectbox("Choose a tool", ["Text Only (One-Turn)", "Text Only (Multi-Turn)", "Code Analysis (One-Turn)", "GCP CLI Maker (One-Turn)"])

    if apps == "Text Only (One-Turn)":
        current_model = "Text Only (One-Turn)"
        st.info(info_sample_prompts)

        col_A, col_B = st.columns([column_num_A, column_num_B])

        with col_A:
            user_prompt = st.text_area("Prompt")
            button = st.button("Generate")
            button_streaming = st.button("Generate (Streaming)")
            reset = st.button(":blue[Reset]")
            # button_multi_turn = st.button("Generate (Multi-Turn)")


        with col_B:
            start = t.time()
            if user_prompt and button:
                if (len(user_prompt) >= prompt_character_limit) and GUEST:
                    st.info(f"{prompt_character_limit_text}  \n\n Total Input Characters: {(len("".join(user_prompt.split())))}")
                else:
                    with st.spinner("Generating..."):
                        response = mm_model.generate_content(user_prompt)
                        # st.write(response.text)
                        st.info("Output in markdown \n")
                        st.markdown(response.text)
                        # st.text(mm_chat.history)
                        end = t.time()
                        st.caption(f"Total Processing Time: {round(end - start, round_number)}")
            if user_prompt and button_streaming:
                if (len(user_prompt) >= prompt_character_limit) and GUEST:
                    st.info(f"{prompt_character_limit_text}  \n\n Total Input Characters: {(len("".join(user_prompt.split())))}")
                else:
                    with st.spinner("Generating..."):
                        response_ = ""
                        response = mm_model.generate_content(user_prompt, stream=True)
                        st.info("Output streaming... \n")
                        for chunk in response:
                            st.write(chunk.text)
                            response_ = response_ + chunk.text 
                        st.info("Output in markdown \n")
                        st.markdown(response_)
                        end = t.time()
                        st.caption(f"Total Processing Time: {round(end - start, round_number)}")
            # if prompt and button_multi_turn:            
            #    pass
                # st.caption(f"Total Processing Time: {end - start}")
            if reset:
                st.rerun()

            # for message in mm_chat.history:
            #    st.markdown(f'**{message.role}**: {message.parts[0].text}')

    if apps == "Text Only (Multi-Turn)":
        current_model = "Text Only (Multi-Turn)"
        st.info(info_sample_prompts)

        col_A, col_B = st.columns([column_num_A, column_num_B])

        with col_A:
            user_prompt = st.text_area("Prompt")
            button = st.button("Generate")
            reset = st.button(":blue[Reset]")
            if reset:
                st.rerun()
            prune = st.button(":red[Prune History]")
            if prune:
                cur.execute(f"""
                            DELETE  
                            FROM toolkit_db
                            WHERE name='{input_name}'
                            """)
                con.commit()
                st.info(f"Data was successfully deleted.")
                t.sleep(sleep_time)
                st.rerun()


        with col_B:
            start = t.time()
            if user_prompt and button:
                if (len(user_prompt) >= prompt_character_limit) and GUEST:
                    st.info(f"{prompt_character_limit_text}  \n\n Total Input Characters: {(len("".join(user_prompt.split())))}")
                else:
                    prompt_history = ""
                    current_start_time = t.time() 
                    cur.execute(f"""
                            SELECT * 
                            FROM toolkit_db
                            WHERE name='{input_name}'
                            ORDER BY time ASC
                            """)                    
                    try:
                        with st.spinner("Generating..."):
                            for id, name, prompt, output, model, time, start_time, end_time, image_detail, saved_image_data_base_string, total_input_characters, total_output_characters in cur.fetchall():
                                prompt_history = prompt_history + f"\n\n User: {prompt}" + f"\n\n Model: {output}"

                            if prompt_history == "":
                                response = mm_model.generate_content(user_prompt)
                            elif prompt_history != "":
                                prompt_history = prompt_history + f"\n\n User: {user_prompt}"
                                response = mm_model.generate_content(prompt_history)
                            output = response.text
                    except:
                        output = prompt_error

                    output_characters = len(output)
                    characters = len(user_prompt)
                    end_time = t.time() 
                    SQL = "INSERT INTO toolkit_db (name, prompt, output, model, time, start_time, end_time, total_input_characters, total_output_characters) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    data = (input_name, user_prompt, output, current_model, current_time, current_start_time, end_time, characters, output_characters)
                    cur.execute(SQL, data)
                    con.commit() 


            with st.expander("Past Conversations"):
                cur.execute(f"""
                SELECT * 
                FROM toolkit_db
                WHERE name='{input_name}'
                ORDER BY time ASC
                """)
                for id, name, prompt, output, model, time, start_time, end_time, image_detail, saved_image_data_base_string, total_input_characters, total_output_characters in cur.fetchall():
                    message = st.chat_message("user")
                    message.write(f":blue[{name}]") 
                    message.text(f"{prompt}")
                    message.caption(f"{time} | Input Characters: {total_input_characters}")
                    message = st.chat_message("assistant")
                    message.markdown(output)
                    message.caption(f"{time} | Model: {model} | Processing Time: {round(end_time-start_time, round_number)} seconds | Output Characters: {total_output_characters}")

            cur.execute(f"""
            SELECT * 
            FROM toolkit_db
            WHERE name='{input_name}'
            ORDER BY time DESC
            LIMIT {limit_query}
            """)
            for id, name, prompt, output, model, time, start_time, end_time, image_detail, saved_image_data_base_string, total_input_characters, total_output_characters in cur.fetchall():
                message = st.chat_message("user")
                message.write(f":blue[{name}]") 
                message.text(f"{prompt}")
                message.caption(f"{time} | Input Characters: {total_input_characters}")
                message = st.chat_message("assistant")
                message.markdown(output)
                message.caption(f"{time} | Model: {model} | Processing Time: {round(end_time-start_time, round_number)} seconds | Output Characters: {total_output_characters}")



    if apps == "Code Analysis (One-Turn)":

        info_sample_prompts = """
            You can now start the conversation by prompting in the text bar. You can ask:
            * What is this code about?
            * How to optimize this code?
            * Add comments
            """
        st.info(info_sample_prompts)

        col_A, col_B = st.columns([column_num_A, column_num_B])

        with col_A:

            user_code = st.text_area("Code")
            text_prompt = st.text_area("Prompt")
            user_prompt = f"This is the code: \n\n {user_code} \n\n {text_prompt}"
            button = st.button("Generate")
            button_stream = st.button("Generate (Stream)")
            details = st.toggle("Show details")
            if details:
                st.info(f"""Total Code and Text Characters: {len(user_code + text_prompt)} 
                        \n Code: {len(user_code)} 
                        \n Text (Prompt): {len(text_prompt)}
                        """)
            reset = st.button(":blue[Reset]")

        with col_B:
            start = t.time()
            with st.spinner("Generating..."):
                if (user_code or text_prompt) and button:
                    if (len(user_prompt) >= prompt_character_limit) and GUEST:
                        st.info(f"{prompt_character_limit_text}  \n\n Total Input Characters: {(len("".join((user_code + text_prompt).split())))}")
                    else:
                        response = mm_chat.send_message(prompt)
                        st.info("Output in markdown \n")
                        st.markdown(response.text)
                        end = t.time()
                        st.caption(f"Total Processing Time: {round(end - start, round_number)}")
                if (user_code or text_prompt) and button_stream:
                    if (len(user_prompt) >= prompt_character_limit) and GUEST:
                        st.info(f"{prompt_character_limit_text}  \n\n Total Input Characters: {(len("".join((user_code + text_prompt).split())))}")
                    else:
                        response_ = ""
                        response = mm_chat.send_message(prompt, stream=True)
                        st.info("Output streaming... \n")
                        for chunk in response:
                            st.write(chunk.text)
                            response_ = response_ + chunk.text 
                        st.info("Output in markdown \n")
                        st.markdown(response_)
                        end = t.time()
                        st.caption(f"Total Processing Time: {round(end - start, round_number)}")
            if reset:
                st.rerun()

    if apps == "GCP CLI Maker (One-Turn)":

        info_sample_prompts = """
            You can now start the conversation by prompting in the text bar. You can ask:
            * Command line to List down GCP Services
            * Command line to create a bucket
            * Command line to create a compute engine
            """
        st.info(info_sample_prompts)

        col_A, col_B = st.columns([column_num_A, column_num_B])

        with col_A:

            user_prompt = st.text_area("Prompt")
            button = st.button("Generate")
            button_streaming = st.button("Generate (Stream)")
            refresh = st.button(":blue[Reset]")

        with col_B:
            start = t.time()
            if user_prompt and button:
                if (len(user_prompt) >= prompt_character_limit) and GUEST:
                    st.info(f"{prompt_character_limit_text}  \n\n Total Input Characters: {(len("".join(user_prompt.split())))}")
                else:
                    response = mm_chat.send_message(f"Write only the Google Cloud Command Line in code format markdown: {user_prompt}")
                    st.info("Output in markdown \n")
                    st.markdown(response.text)
                    # st.text(mm_chat.history)
                    end = t.time()
                    #st.caption(f"Total Processing Time: {end - start}")
            if user_prompt and button_streaming:
                if (len(user_prompt) >= prompt_character_limit) and GUEST:
                    st.info(f"{prompt_character_limit_text}  \n\n Total Input Characters: {(len("".join(user_prompt.split())))}")
                else:
                    response_ = ""
                    response = mm_chat.send_message(prompt, stream=True)
                    st.info("Output streaming... \n")
                    for chunk in response:
                        st.write(chunk.text)
                        response_ = response_ + chunk.text 
                    st.info("Output in markdown \n")
                    st.markdown(response_)
                    end = t.time()
                    # st.caption(f"Total Processing Time: {end - start}")
            if refresh:
                st.rerun()
                    
    #------------------For Multimodal Guest Limits-----------------------#
    if (GUEST == True and button) or (GUEST == True and button_streaming):
        ### Insert into a database
        SQL = "INSERT INTO toolkit_guest_chats (name, prompt, output, model, time, count_prompt) VALUES(%s, %s, %s, %s, %s, %s);"
        data = (input_name, user_prompt, output, current_model, current_time, count_prompt)
        cur.execute(SQL, data)
        con.commit()

    #---------------- Insert into a table (total_prompts) ----------------#
    if button or button_streaming:
        SQL = "INSERT INTO total_prompts (name, prompt, output, model, time, count_prompt) VALUES(%s, %s, %s, %s, %s, %s);"
        data = (input_name, user_prompt, output, current_model, current_time, count_prompt)
        cur.execute(SQL, data)
        con.commit()

                    
#----------Execution----------#
if __name__ == '__main__':

    # Connection
    con = False
    try:
        con, cur = connection()
        con = True
    except:
        st.info("##### :computer: ```DATABASE CONNECTION: The app can't connect to the database right now. Please try again later.```")
    if con == True:
        con, cur = connection()

        with st.sidebar:
            st.header(":star: AI-Powered Cloud Toolkit :toolbox:", divider="rainbow")
            login = st.checkbox("Login")
            guest = st.checkbox("Continue as a guest")
        
        # Admin
        if login and not guest:
            with st.sidebar:
                input_name = "Admin"
                input_name = st.text_input("Username", input_name)
                password = st.text_input("Password", type="password")
                st.button("Login")
                                        
            if password == ADMIN_PASSWORD:
                GUEST = False
                main()
        
                # Prompt History
                with st.sidebar:
                    prompt_history = st.checkbox("Prompt History")
                    if prompt_history:
                        # Prune All
                        prune_all = st.button(":red[Prune All]")

                        # Guest Limit
                        prune_multimodal_guest_chats = st.button(":red[Prune Guest Limit]")
                        if prune_multimodal_guest_chats or prune_all:
                            cur.execute("DROP TABLE toolkit_guest_chats")
                            st.info(f"Guest Limit was successfully deleted.")
                            con.commit()

                        # All Guest and Admin DB
                        prune_db = st.button(":red[Prune Guest and Admin DB]")
                        if prune_db or prune_all:
                            admin_DB = ["toolkit_db"]
                            for DB in admin_DB:
                                cur.execute(f"DROP TABLE {DB}")
                            con.commit()
                            st.info(f"Database was successfully deleted.")

                        # Prune Total Prompts
                        prune_total_prompts = st.button(":red[Prune Total Prompts DB]")
                        if prune_total_prompts or prune_all:
                            cur.execute("DROP TABLE total_prompts")
                            st.info(f"Total Prompts DB was successfully deleted.")
                            con.commit()

                        # Prune Chat View Counter
                        prune_chat_view_counter = st.button(":red[Prune Chat View Counter DB]")
                        if prune_chat_view_counter or prune_all:
                            cur.execute("DROP TABLE chat_view_counter")
                            st.info(f"Chat View Counter DB was successfully deleted.")
                            con.commit()
                            st.rerun()
                            
                    counter = st.checkbox("Counter")
                    if counter:
                        st.header("Counter")
                        st.caption("""
                                    Count every request in this app.
                                    """)
                        st.subheader("",divider="rainbow")
                        # Total views
                        cur.execute("""
                                    SELECT SUM(view) 
                                    FROM chat_view_counter
                                    """)
                        st.write(f"#### Total views: **{cur.fetchone()[0]}**")
                        # Current view
                        time = t.strftime("Date: %Y-%m-%d | Time: %H:%M:%S UTC")
                        st.write(f"Current: {time}")
                        # Total views today
                        time_date = time[0:15]
                        cur.execute(f"""
                                    SELECT SUM(view) 
                                    FROM chat_view_counter
                                    WHERE time LIKE '{time_date}%'
                                    """)
                        st.write(f"#### Total views today: **{cur.fetchone()[0]}**")
                        st.divider()
                        # Previous views
                        views = st.checkbox("See Previous Views")
                        if views:
                            st.write("**Previous Views**")
                            cur.execute("""
                                        SELECT * 
                                        FROM chat_view_counter
                                        ORDER BY time DESC
                                        """)
                            for _, _, time in cur.fetchall():
                                st.caption(f"{time}")
                        
        # Unchecked box
        if not login and not guest:
            st.info("Login or Continue as a guest to get started")
        
        # Checked box
        if login and guest:
            with st.sidebar:
                st.info("Please choose only one")
        
        # Guest
        if not login and guest:
            with st.sidebar:
                input_name = st.text_input("Username")
                if input_name == "Admin" or input_name == "admin":
                    st.info("Please use different username")
                    input_name = ""
                start = st.button("Let's go")
                
            GUEST = True
            # Guest Limit
            LIMIT = 30
            time = t.strftime("Date: %Y-%m-%d | Time: %H:%M:%S UTC")
            time_date = time[0:15]
            cur.execute(f"""
                    SELECT SUM(count_prompt)
                    FROM toolkit_guest_chats
                    WHERE time LIKE '{time_date}%'
                    """)
            for total in cur.fetchone():
                if total is None:
                    total_count = 0
                else:
                    total_count = total

            with st.sidebar:
                guest_limit = st.checkbox("Show Guest Limit")
                if guest_limit:
                    st.info(f"Guest Daily Limit Left: {LIMIT - total_count}")


                    # st.write(total_count)

            # More than the Guest Limit
            #------------------ Guest limit --------------------------#
            if GUEST == True and total_count >= LIMIT:
                with st.sidebar:
                    st.info("Guest daily limit has been reached.")

                    # If the limit is reached, this will automatically delete all Guest prompt history. Note: "multimodal_guest_chats" is not included.
                    guest_DB = ["guest_toolkit_db"]
                    for DB in guest_DB:
                        cur.execute(f"DROP TABLE {DB}")
                    con.commit()

                st.info("Guest daily limit has been reached.")

            # Less than the Guest Limit
            #------------------ Guest limit --------------------------#
            if GUEST == True and total_count < LIMIT and input_name:
                main()

        # Chat View Counter
        time = t.strftime("Date: %Y-%m-%d | Time: %H:%M:%S UTC")
        view = 1
        SQL = "INSERT INTO chat_view_counter (view, time) VALUES(%s, %s);"
        data = (view, time)
        cur.execute(SQL, data)
        con.commit()
    
#----------Footer----------#
#----------Sidebar Footer----------#
with st.sidebar:
    st.markdown("""
                ---
                > :gray[:copyright: Portfolio Website by [Matt R.](https://github.com/mregojos)]            
                > :gray[:cloud: Deployed on [Google Cloud](https://cloud.google.com)]

                > For demonstration purposes only
                ---
                """)