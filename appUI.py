import autogen
from rich import print
import chainlit as cl
from typing_extensions import Annotated
from chainlit.input_widget import (
   Select, Slider, Switch)
from autogen import AssistantAgent, UserProxyAgent
from utils.chainlit_agents import ChainlitUserProxyAgent, ChainlitAssistantAgent
from graphrag.query.cli import run_global_search, run_local_search

# LLama3 LLM from Lite-LLM Server for Agents #
llm_config_autogen = {
    "seed": 42,  # change the seed for different trials
    "temperature": 0,
    "config_list": [{"model": "llama3", 
                     "base_url": "http://0.0.0.0:4000/v1", 
                     'api_key': 'ollama',
                     'price': [0, 0]
                     },
    ],
    "timeout": 600,
}

@cl.on_chat_start
async def on_chat_start():
    try:
        settings = await cl.ChatSettings(
            [      
                Switch(id="Search_type", label="(GraphRAG) Local Search", initial=True),       
                Select(
                    id="Gen_type",
                    label="(GraphRAG) Content Type",
                    values=["prioritized list", "single paragraph", "multiple paragraphs", "multiple-page report"],
                    initial_index=1,
                ),          
                Slider(
                    id="Community",
                    label="(GraphRAG) Community Level",
                    initial=0,
                    min=0,
                    max=2,
                    step=1,
                ),

            ]
        ).send()

        response_type = settings["Gen_type"]
        community = settings["Community"]
        local_search = settings["Search_type"]
        
        cl.user_session.set("Gen_type", response_type)
        cl.user_session.set("Community", community)
        cl.user_session.set("Search_type", local_search)
  
        retriever = AssistantAgent(
            name="Retriever", 
            llm_config=llm_config_autogen, 
            system_message="""你是一个专业的信息检索助手。请遵守以下规则：
                            1. 必须使用 query_graphRAG 函数工具来搜索和获取上下文信息
                            2. 当成功获取并返回答案后，请立即输出"TERMINATE"结束会话
                            3. 如果无法找到相关信息，也请输出"TERMINATE"
                            4. 不要尝试回答任何与检索无关的问题""",
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER", 
            description="Retriever Agent"
        )

        user_proxy = UserProxyAgent(
            name="User_Proxy",
            human_input_mode="TERMINATE",
            llm_config=llm_config_autogen,
            is_termination_msg=lambda x: "TERMINATE" in x.get("content", "").upper(),
            code_execution_config=False,
            system_message='''A human admin. Interact with the retriever to provide any context''',
            description="User Proxy Agent"
        )
        

        groupchat = autogen.GroupChat(
            agents=[user_proxy, retriever],
            messages=[],
            max_round=10,
            speaker_selection_method="round_robin",
        )

        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config=llm_config_autogen,
        )
        cl.user_session.set("user_proxy", user_proxy)
        cl.user_session.set("groupchat", groupchat)
        cl.user_session.set("manager", manager)
        cl.user_session.set("Retriever", retriever)


        def _register_reply():
            @user_proxy.register_for_execution()
            @retriever.register_for_llm(description="检索内容用于代码生成和问题回答")
            async def query_graphRAG(
                query: Annotated[str, '查询字符串，包含你想要从RAG搜索中获取的信息']
            ) -> str:
                LOCAL_SEARCH = cl.user_session.get("Search_type")
                RESPONSE_TYPE = cl.user_session.get("Gen_type")
                COMMUNITY = cl.user_session.get("Community")
                
                INPUT_DIR = None
                ROOT_DIR = '.'
                config_filepath = './settings.yaml'
                
                if LOCAL_SEARCH:
                    result = run_local_search(
                        config_filepath=config_filepath, 
                        data_dir=INPUT_DIR,
                        root_dir=ROOT_DIR, 
                        community_level=COMMUNITY, 
                        response_type=RESPONSE_TYPE, 
                        streaming=False, 
                        query=query
                    )
                else:
                    result = run_global_search(
                        config_filepath=config_filepath, 
                        data_dir=INPUT_DIR,
                        root_dir=ROOT_DIR, 
                        community_level=COMMUNITY, 
                        response_type=RESPONSE_TYPE, 
                        streaming=False, 
                        query=query
                    )
                
                # 发送结果到前端
                await cl.Message(content=result).send()
                return result

        _register_reply()

        # 发送欢迎消息
        welcome_msg = cl.Message(content="您好！我是您的智能助手，请问您需要什么帮助？", author="User_Proxy")
        await welcome_msg.send()

    except Exception as e:
        print("Error: ", e)


@cl.on_settings_update
async def setup_agent(settings):
    response_type = settings["Gen_type"]
    community = settings["Community"]
    local_search = settings["Search_type"]
    cl.user_session.set("Gen_type", response_type)
    cl.user_session.set("Community", community)
    cl.user_session.set("Search_type", local_search)
    print("on_settings_update", settings)

@cl.on_message
async def run_conversation(message: cl.Message):


    try:

        user_proxy = cl.user_session.get("user_proxy")
        manager = cl.user_session.get("manager")
        groupchat = cl.user_session.get("groupchat")
        
        if not all([user_proxy, manager, groupchat]):
            await cl.Message(content="会话未正确初始化，请重新开始对话").send()
            return
        
        # 动态调整最大对话轮数
        complexity_factor = len(message.content.split()) / 50
        dynamic_max_iter = max(5, min(20, int(10 + complexity_factor * 10)))
        groupchat.max_round = dynamic_max_iter
        
        # 使用Chainlit集成的消息处理方法
        await cl.make_async(user_proxy.initiate_chat)(
            manager,
            message=message.content,
        )
            
    except Exception as e:
        error_msg = f"处理消息时出错: {str(e)}"
        print(error_msg)
        await cl.Message(content=error_msg).send()




# 