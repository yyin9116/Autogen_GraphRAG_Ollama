# GraphRAG + AutoGen + Ollama + Chainlit UI = 本地多代理 RAG Superbot

![Graphical Abstract](https://github.com/karthik-codex/autogen_graphRAG/blob/main/images/1721017707759.jpg?raw=true)

此应用程序将 GraphRAG 与 AutoGen 代理集成，由来自 Ollama 的本地 LLMs 驱动，用于免费和离线嵌入和推理。主要亮点包括：

* Agentic-RAG：- 通过函数调用将 GraphRAG 的知识搜索方法与 AutoGen 代理集成。

* 离线 LLM 支持：- 配置 GraphRAG（本地和全局搜索）以支持来自 Ollama 的本地模型，用于推理和嵌入。

* 非 OpenAI 函数调用：- 扩展 AutoGen 以支持通过 Lite-LLM 代理服务器从 Ollama 进行非 OpenAI LLMs 的函数调用。

* 交互式 UI：- 部署 Chainlit UI 来处理持续对话、多线程和用户输入设置



## 📦 在 Windows 上安装 

按照以下步骤在 Windows 上使用 Ollama 和 Chainlit UI 设置并本地运行 AutoGen GraphRAG :

1. **安装 LLMs:**

    [Ollama's website](https://ollama.com/) 先下载 Ollama App。

    启动 App 后，先用任务管理器关掉 Ollama 的所有进程，因为 App 开着会占用我们的端口导致无法使用命令安装模型。

    在命令行中使用 Ollama.exe 而不是 Ollama app.exe 来执行以下命令：
    ```pwsh
    # 先启动 Ollama
    ollama serve
    # 拉取模型，大概10个G，注意流量
    ollama pull mistral
    ollama pull nomic-embed-text
    ollama pull llama3
    ```
    如果输入 ollama 发现找不到， 或者修改了安装位置，需要根据安装 Ollama 时的提示，修改系统环境变量 Path 中对应  Ollama.exe 所在路径的值。
    ```
    Path: Ollama App 根目录
    ```

2. **使用 uv 来管理依赖:**
    
    打开 powershell ，安装 uv
    ```pwsh
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.7.4/install.ps1 | iex"
    ```
    写入环境变量
    ```pwsh
    $env:Path = "C:\Users\你的用户名\.local\bin;$env:Path"
    ```
    检查是否安装成功
    ```pwsh
    uv --version
    ```
    Clone 我创建的分支，切换到项目路径
    ```pwsh
    git clone -b yin https://github.com/yyin9116/Autogen_GraphRAG_Ollama.git
    
    cd Autogen_GraphRAG_Ollama
    ```
    在当前路径根目录创建虚拟环境
    ```pwsh
     uv venv autogen_venv --python=3.12
    ```
    这段命令里 `autogen_venv` 就是创建的虚拟环境名称，可以在当前文件夹里找到

    激活环境（记得每次切换新终端都要激活一次）
    ```pwsh
    autogen_venv/Scripts/activate.ps1
    ```
    安装依赖
    ```pwsh
    uv pip install -r requirements.txt
    ```    
    手动安装两个库，防止报错
    ```
    uv pip install litellm[proxy]
    ```
    ```
    uv pip install chainlit==2.0.0
    ```
3. **初始化 GraphRAG，拷贝设置文件到根目录下:**
    ```pwsh
    mkdir input input/markdown
    python -m graphrag.index --init  --root .
    cp ./utils/settings.yaml ./
    ```      
4. **用 Utils 文件夹下的两个同名文件替换 GraphRAG 库中的 'embedding.py' 和 'openai_embeddings_llm.py' :**
    ```pwsh
    cp ./utils/openai_embeddings_llm.py .\autogen_venv\Lib\site-packages\graphrag\llm\openai\openai_embeddings_llm.py
    cp ./utils/embedding.py .\autogen_venv\Lib\site-packages\graphrag\query\llm\oai\embedding.py 
    ```      
5. **创建嵌入和知识图:**
    ```pwsh
    python -m graphrag.index --root .
    ```         
6. **启动 Lite-LLM 代理服务器:**
    使用 llama3 来负责对话（发送请求到 4000 端口）
    ```pwsh
    litellm --model ollama_chat/llama3
    ```    
7. **启动 app:**
    ```pwsh
    chainlit run appUI.py
    ```
    如果在环境路径 Scripts 文件夹下找不到 Chainlit.exe，尝试手动重新装一下 chainlit
    ```pwsh
    uv pip install chainlit==2.0.0
    ```
8. **注意事项：**
   1. 由于版本问题，utils 中的 pdf 转换脚本目前不可用
