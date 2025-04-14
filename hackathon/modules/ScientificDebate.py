import re # Import regex for parsing
from typing import Optional # For type hinting

# Assuming these imports are correctly set up in your project structure
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from ard.hypothesis.hypothesis import Hypothesis # Assuming Hypothesis class exists
from .Module import Module # Assuming base Module class exists
from hackathon.autogen.llm_config import get_llm_config # Assuming config getter exists

class ScientificDebate(Module):
    """
    A module orchestrating a multi-agent scientific debate to refine a given hypothesis.

    Uses Proponent, Critic, Moderator, and Refiner agents within an AutoGen GroupChat
    to analyze, critique, summarize, and ultimately improve a scientific hypothesis.
    """
    def __init__(self, model: str = "fast", temperature: float = 0.7):
        """
        Initializes the ScientificDebate module and its agents.

        Args:
            model (str): The name of the language model to use (e.g., "fast", "gpt-4").
            temperature (float): The temperature setting for the language model.
        """
        self.llm_config = get_llm_config(model)
        self.llm_config["temperature"] = temperature # Ensure temperature is applied

        # --- Agent Definitions with Refined Prompts ---

        self.proponent = AssistantAgent(
            name="Proponent",
            llm_config=self.llm_config,
            system_message=(
                "You are the Proponent. Your role is to vigorously defend the provided hypothesis. "
                "Construct strong arguments using logical reasoning, citing potential empirical evidence "
                "(even if hypothetical), and relevant theoretical frameworks. "
                "Anticipate criticisms and preemptively address potential weaknesses. "
                "Your goal is to persuade others of the hypothesis's validity and strength. "
                "Focus *only* on arguments supporting the hypothesis."
            )
        )

        self.critic = AssistantAgent(
            name="Critic",
            llm_config=self.llm_config,
            system_message=(
                "You are the Critic. Your role is to rigorously challenge the provided hypothesis and the Proponent's arguments. "
                "Identify logical fallacies, point out unsupported assumptions, question the methodology (implied or explicit), "
                "highlight potential biases, limitations, and alternative explanations. "
                "Demand strong evidence and logical coherence. Be skeptical and analytical. "
                "Your goal is to expose weaknesses in the hypothesis and its defense. "
                "Focus *only* on critiquing the hypothesis and proponent's arguments."
            )
        )

        self.moderator = AssistantAgent(
            name="Moderator",
            llm_config=self.llm_config,
            system_message=(
                "You are the Moderator. Your role is to objectively summarize the debate between the Proponent and the Critic. "
                "Do not take sides. Briefly outline the main points of agreement and disagreement. "
                "Identify the strongest arguments presented by both sides. "
                "Highlight key weaknesses or unanswered questions regarding the hypothesis that emerged from the debate. "
                "Conclude by stating the apparent status of the hypothesis based *only* on the preceding arguments. "
                "Keep your summary concise and neutral."
            )
        )

        self.refiner = AssistantAgent(
            name="Refiner",
            llm_config=self.llm_config,
            system_message=(
                "You are the Refiner AI. Your task is to synthesize the preceding debate (Proponent's defense, Critic's challenges, Moderator's summary) "
                "and the original hypothesis to formulate an improved scientific hypothesis and a suitable title.\n\n"
                "Instructions:\n"
                "1. Analyze the entire debate history provided.\n"
                "2. Identify the core strengths, weaknesses, nuances, conditions, and variables discussed.\n"
                "3. Synthesize these insights to formulate a **Refined Hypothesis**. This hypothesis MUST:\n"
                "    - Be a single, clear, declarative statement proposing a specific, testable relationship.\n"
                "    - Be more precise, robust, or specific than the original hypothesis, incorporating insights from the debate.\n"
                "    - Use formal, objective, and unambiguous scientific language.\n"
                "    - State the relationship directly, avoiding uncertainty phrases like 'may be linked' or 'requires more study' *within* the hypothesis itself.\n"
                "    - Be falsifiable.\n"
                "4. Propose a concise, informative **Refined Title** suitable for a paper presenting this hypothesis.\n\n"
                "Output Format:\n"
                "You MUST output *only* the following two lines, in this exact order, with nothing before or after:\n"
                "REFINED_TITLE: [Your proposed title here]\n"
                "REFINED_HYPOTHESIS: [Your formulated refined hypothesis statement here]"
            )
        )

        # Removed self.final agent and self.final_prompt_template


    def get_hypothesis_str(self, h: Hypothesis) -> str:
        """Formats the Hypothesis object into a string for the initial prompt."""
        # Cleaner formatting
        references_str = "\n  - ".join(h.references) if h.references else "None"
        return f"**Original Hypothesis Title:** {h.title}\n" \
               f"**Original Hypothesis Statement:** {h.statement}\n" \
               f"**Associated References:**\n  - {references_str}"

    def forward(self, h: Hypothesis, max_rounds: int = 10) -> Hypothesis:
        """
        Executes the scientific debate and refinement process.

        Args:
            h (Hypothesis): The initial hypothesis object to be debated and refined.
            max_rounds (int): The maximum number of conversation turns allowed.

        Returns:
            Hypothesis: The potentially refined hypothesis object. If refinement fails
                      or the refiner doesn't produce valid output, the original
                      hypothesis object `h` is returned.
        """
        initial_hypothesis_str = self.get_hypothesis_str(h)

        # UserProxyAgent acts as the entry point and triggers termination
        user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1, # Prevents loops if termination fails
            is_termination_msg=lambda x: isinstance(x, dict) and \
                                        "REFINED_TItTLE:" in x.get("content", "") and \
                                        "REFINED_HYPOTHESIS:" in x.get("content", ""),
            code_execution_config=False, # No code execution needed for this agent
            # default_auto_reply="Continue", # Optional: Can add a default reply if needed
        )

        # Define the sequence of speakers
        agents = [user_proxy, self.proponent, self.critic, self.moderator, self.refiner]
        allowed_transitions = {
            user_proxy: [self.proponent],
            self.proponent: [self.critic],
            self.critic: [self.moderator],
            self.moderator: [self.refiner],
            self.refiner: [user_proxy] # Refiner output should be checked by UserProxy for termination
        }

        groupchat = GroupChat(
            agents=agents,
            messages=[],
            max_round=max_rounds,
            allowed_or_disallowed_speaker_transitions=allowed_transitions,
            speaker_transitions_type="allowed",
            # send_introductions=True # Optional: Can be useful for debugging agent awareness
        )

        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=self.llm_config,
            is_termination_msg=user_proxy._is_termination_msg # Manager can also check for termination
            )

        # Initiate the chat
        user_proxy.initiate_chat(
            manager,
            message=f"""The following hypothesis is presented for debate and refinement:

{initial_hypothesis_str}

Follow this sequence strictly:
1.  **Proponent**: Defend the hypothesis.
2.  **Critic**: Critique the hypothesis and the Proponent's arguments.
3.  **Moderator**: Summarize the debate objectively.
4.  **Refiner**: Analyze the debate and provide the refined title and hypothesis in the specified format (REFINED_TITLE: ... REFINED_HYPOTHESIS: ...).

Ensure each agent completes their turn before the next begins. The goal is a more robust and precise hypothesis based on the discussion. Maintain the core relationship of the original hypothesis unless the debate strongly justifies modification.
"""
        )

        # --- Post-Debate Processing ---
        # Extract the refined hypothesis from the Refiner's last message
        refiner_message = None
        for msg in reversed(groupchat.messages):
             # Check if the message is likely from the refiner and contains the keywords
            if isinstance(msg, dict) and msg.get("name") == self.refiner.name and \
               "REFINED_TITLE:" in msg.get("content", "") and \
               "REFINED_HYPOTHESIS:" in msg.get("content", ""):
                 refiner_message = msg['content']
                 break # Found the message

        if refiner_message:
            # Use regex to reliably extract title and hypothesis
            title_match = re.search(r"REFINED_TITLE:\s*(.*)", refiner_message, re.IGNORECASE)
            hypothesis_match = re.search(r"REFINED_HYPOTHESIS:\s*(.*)", refiner_message, re.IGNORECASE | re.DOTALL) # DOTALL allows matching across newlines

            if title_match and hypothesis_match:
                refined_title = title_match.group(1).strip()
                refined_statement = hypothesis_match.group(1).strip()

                # Update the hypothesis object
                h.title = refined_title
                h.statement = refined_statement
                print(f"Refinement successful. New Title: {h.title}") # Added print statement
                print(f"New Statement: {h.statement}")
                return h
            else:
                print("Warning: Refiner output keywords found, but parsing failed. Returning original hypothesis.")
                # Log error or handle appropriately
                return h
        else:
            print("Warning: Refiner did not produce the expected output format. Returning original hypothesis.")
            # Log that refinement didn't occur as expected
            return h