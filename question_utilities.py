import re
 
class QuestionUtilities:
    """
    Utility class for parsing and iterating through interview questions.
    (NOTE: This is an agnostic workflow component.
    It has no dependencies on a specific orchestration framework (LangChain, LangGraph, CrewAI etc)
    """
    INTERVIEW_REGEX = r"_ENOUGH_INFO"
    ORIGINAL_QUESTIONS_REGEX = r"### START QUESTIONS(.*?)### END QUESTIONS"
    INCOMPLETE_QUESTIONS_REGEX = r"NOT_ENOUGH_INFO([^a-zA-Z]*)?(.*)?"
    COMPLETE_QUESTIONS_REGEX = r"HAS_ENOUGH_INFO([^a-zA-Z]*)?(.*)?"
    
    def __init__(self):
        """
        Initializes the question utility tool.
        """
        self.incomplete_questions = []

        self.complete_questions = []

        self.original_questions = ""

    def update_questions(self, questions: str = ""):
        """
        Updates the question metadata.
        """

        if QuestionUtilities.INTERVIEW_REGEX in questions:
        
            self.incomplete_questions = self.initialize_questions(questions, QuestionUtilities.INCOMPLETE_QUESTIONS_REGEX)
            
            self.complete_questions = self.initialize_questions(questions, QuestionUtilities.COMPLETE_QUESTIONS_REGEX)

        else:

            self.original_questions = self.parse_questions(questions)
        
    def parse_questions(self, content: str) -> str:
        """
        Retrieves the question list from the given content.
        """
        if content is None:
            return ""
            
        pattern = QuestionUtilities.ORIGINAL_QUESTIONS_REGEX
        
        match = re.search(pattern, content, re.DOTALL)
        
        return match.group(1).strip() if match else ""

    def initialize_questions(self, questions: str, pattern: str) -> str:
        """
        Initializes the list of complete and incomplete questions.
        Complete questions are questions marked with the HAS_ENOUGH_INFO classifier, while
        incomplete questions are questions marked with the NOT_ENOUGH_INFO classifier.
        """
        if questions is None:
            return [] 
            
        original_questions = self.original_questions.split("\n")
        
        processed_questions = questions.split("\n")

        results = [(orig, re.findall(pattern, processed, re.DOTALL)) for orig, processed in zip(original_questions, processed_questions)]

        results = ["" if not processed else orig for orig, processed in results]

        results = list(filter(None, results))
        
        return results

    def next_questions(self, content: str) -> int:
        """
        Returns a list of interview questions that still need to be completed.
        """
        self.update_questions(content)
        
        continue_interview = self.is_in_interview_mode()
        
        return self.incomplete_questions if continue_interview else []
    
    def is_in_interview_mode(self) -> bool:
        """
        Returns a boolean indicator of whether or not the interview mode is still in progress.
        based on whether or not the number of complete questions exceeds the number of incomplete questions.
        If true, interview mode is still ongoing (meaning the invoker of this component should continue the interview).
        Else, interview mode is no longer ongoing, so the invoker of this component can end the interview.
        """
        return self.incomplete_questions and (len(self.complete_questions) < len(self.incomplete_questions))
        