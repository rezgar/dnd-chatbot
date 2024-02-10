import asyncio
from autogen import UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
from user_proxy_agent_async import UserProxyAgentAsync

#from group_chat_manager import GroupChatManager

class DnDSessionChat:
    def __init__(self, chat_id=None, websocket=None):
        self.websocket = websocket
        self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        self.client_receive_queue = asyncio.Queue()

        self.player = UserProxyAgentAsync(
            name = "player",
            human_input_mode="TERMINATE", 
            system_message="""You speak for a character in a Dungeons and Dragons game""",
            #max_consecutive_auto_reply=5,
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("Your turn!"),
            code_execution_config=False
        )
        self.player.set_queues(self.client_sent_queue, self.client_receive_queue)

        self.gamemaster = AssistantAgent(
            name="gamemaster",
            system_message="A Dungeons and Dragons 5 game master. Responsible for enforcing DnD 5 rules by identifying required checks (e.g. perception check, attack roll) in characters' actions and storyteller's story, making the necessary rolls and reporting results to all other participants (i.e. storyteller and players). Relies on Storyteller for leading the story. Game Master reacts to every user input, verifies whether it doesn't violate the story and DnD 5 rule set and informs Storyteller (in private) whether it's safe to continue the story. Game Master never communicates to Player privately or via shared chat, unless it's to notify them of checks (like ability checks, combat rolls). Game Master always communicates their calculations and thought process step by step.",
            llm_config={
                "model":"gpt-3.5-turbo",
                "temperature": 0,
                "config_list": [
                    { "model": "gpt-3.5-turbo" }
                ],
            }
        )

        self.storyteller = AssistantAgent(
            name="storyteller",
            system_message="World-class fantasy writer. Responsible for telling a compelling story and prompting Player to contribute Character's perspective, thoughts and actions. Incorporates Player's actions and provides colourfull feeback. Never gets out of character. Relies on Game Master for technical side of the DnD game. When player input is required ends the story with the exact statement 'Your turn!' - no variations are allowed because this triggers player's turn. Storyteller does act on Player's inut until Game Master has confirmed in chat that it's safe to continue the story. Storyteller never replies to Game Master - neither in private nor in general chat. Storyteller only communicates to Player.",
            llm_config={
                "model":"gpt-3.5-turbo",
                "temperature": 1,
                "config_list": [
                    { "model": "gpt-3.5-turbo" }
                ]
            },
        )

        self.groupchat = GroupChat(
          agents=[
              self.player, 
              self.gamemaster, 
              self.storyteller
          ], 
          admin_name='gamemaster',
          speaker_selection_method='auto',
          messages=[], 
          max_round=20
        )
        self.groupchat_manager = GroupChatManager(
            groupchat=self.groupchat,
            human_input_mode="TERMINATE",
            llm_config={
                "model":"gpt-3.5-turbo",
                "temperature": 0.5,
                "config_list": [
                    { "model": "gpt-3.5-turbo" }
                ]
            },
        )

    async def start(self):
        await self.storyteller.a_initiate_chat(
            recipient= self.groupchat_manager,
            clear_history=True,
            message="Ah, Player, it's good to see you once again! What sort of adventure are you in the mood for today? Are you seeking thrills and danger, or perhaps a more lighthearted tale of exploration and discovery? Your turn!"
        )