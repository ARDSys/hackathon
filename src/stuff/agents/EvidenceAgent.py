from .AbstractAgent import AbstractAgent
from .AbstractAgent import AgentResult
from ..ApiController import ApiController, ModelConfig
from src.stuff.utils.prompts import gen_prompt, EVIDENCE_AGENT
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from .pubmed import pubmed_tool
from langchain_community.tools.pubmed.tool import PubmedQueryRun



class EvidenceAgent(AbstractAgent):
    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config, role_prompt=EVIDENCE_AGENT)
    """Evidence Agent: This expert agent provides evidence to support the hypothesis proposed by the Thinker Agent."""

    def get_evidence(self, hypothesis: str) -> str:
        # tools = [pubmed_tool]
        # results = tools[0].run(hypothesis)
        tool = PubmedQueryRun()
        result = tool.invoke(hypothesis)
        # import pdb;pdb.set_trace()
        return result

    def parse_pubmed_response(self, response: str):
        # Example response parsing logic
        # This is a simplified example and may need to be adjusted based on the actual response format
        parsed_data = []
        articles = response.split("Published: ")

        for article in articles[1:]:
            lines = article.split("\n")
            published_date = lines[0].strip()
            title = lines[1].strip().replace("Title: ", "")
            copyright_info = lines[2].strip().replace("Copyright Information: ", "")
            summary = "\n".join(lines[4:]).strip().replace("Summary::", "")

            parsed_data.append({
                "published_date": published_date,
                "title": title,
                "copyright_info": copyright_info,
                "summary": summary
            })

        return parsed_data

    def run(self, input: AgentResult) -> AgentResult:
        print("Running EvidenceAgent...")

        print("EvidenceAgent: Searching info in Pubmed")
        hypothesis = input.llm_response
        print(hypothesis)
        evidence = self.get_evidence(hypothesis=hypothesis)
        print("Info from Pubmed has been searched")
        parsed_evidence = self.parse_pubmed_response(evidence)
        # print(parsed_evidence)

        # print(evidence)

        print("Generating prompt")
        prompt = gen_prompt(role=self.role_prompt, input_data=evidence)
        response = ApiController.execute_prompt(prompt=prompt, model_config=self.model_config)



        print("Done EvidenceAgent!")

        res = AgentResult(llm_response=response)
        if parsed_evidence != []:
            res.metadata["article"] = parsed_evidence
            print("parsed evidence: ", parsed_evidence)
        else:
            res.metadata["article"] = None
            print("No evidence")
        return res
