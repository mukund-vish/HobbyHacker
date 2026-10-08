# HobbyHacker Plan v1

## What is HobbyHacker ?

**HobbyHacker** is a pentesting and bug hunting autonomous framework. </br>
Which utilizes **Docker Containers** for isolation. You can connect any **LLM** via an **open ai** compatible url.</br>
The LLM runs inside the docker container where the environment is setuped.<br/>
You can choose tools on as per your choice, or can choose a preset which already have some selected tools which you can add or remove.<br/>
Using the reasoning of LLM and capabilties of tools choosen, our framework starts an engagement on the given target under the given guidelines.

## How does this framework works ?

Well, first we have our **agent** which lives inside the **container** is the intermidatery between the tools execution and llm. This **agents** talks to the llm and takes in the **tool call** then this agent gives that **tool call** to a **broker** which lives on the **host** that **broker** is responsible to check the command in question against an immutable **deny list** that also lives on the host. **Broker** after checking returns **True** or **False** (if false also list the reason) along side the **command in question**(if true).<br/>

On receiving the status and reason/command it proceeds further.
