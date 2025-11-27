from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any

class PHQ9AssessmentTool:
    """
    Based on the PHQ-9 (Patient Health Questionnaire-9) depression screening tool.
    https://www.mdcalc.com/calc/1725/phq9-patient-health-questionnaire9
    The 8 core questions of the PHQ-9 (scores 0-3)
    9th question is a suicide related, for which we have made a custom tool:

    Perform suicide risk assessment in patients who respond positively to item 9:
    "Thoughts that you would be better off dead or of hurting yourself in some way."
    Rule out bipolar disorder, normal bereavement, and medical disorders causing depression.

    """
    PHQ9_QUESTIONS = {
        1: "Little interest or pleasure in doing things?",
        2: "Feeling down, depressed, or hopeless?",
        3: "Trouble falling or staying asleep, or sleeping too much?",
        4: "Feeling tired or having little energy?",
        5: "Poor appetite or overeating?",
        6: "Feeling bad about yourself—or that you are a failure or have let yourself or your family down?",
        7: "Trouble concentrating on things, such as reading the newspaper or watching television?",
        8: "Moving or speaking so slowly that other people could have noticed? Or the opposite—being so fidgety or restless that you have been moving around a lot more than usual?",
        9: "Thoughts that you would be better off dead or of hurting yourself in some way?",
    }
    
    def __init__(self):
        self.administer_question = FunctionTool(self._administer_question)
    
    async def _administer_question(self, question_number: int, user_response: str) -> Dict[str, Any]:
        """
        Process PHQ-9 question responses and return next steps.
        """
        score = self._extract_score(user_response)
        if score is not None:
            next_question = question_number + 1
            if next_question in self.PHQ9_QUESTIONS:
                return {
                    "score": score,
                    "next_question": next_question,
                    "question_text": self.PHQ9_QUESTIONS[next_question],
                    "completed": False
                }
            else:
                total_score = score
                category = self.classify_score(total_score)
                return {
                    "score": score,
                    "total_score": total_score,
                    "category": category,
                    "completed": True
                }
        else:
            return {
                "error": "Please respond with: 0 (Not at all), 1 (Several days), 2 (More than half the days), or 3 (Nearly every day)",
                "current_question": question_number,
                "question_text": self.PHQ9_QUESTIONS[question_number]
            }
    
    def _extract_score(self, response: str) -> int:
        response_lower = response.lower()
        if '0' in response or 'not at all' in response_lower:
            return 0
        elif '1' in response or 'several' in response_lower:
            return 1
        elif '2' in response or 'more than half' in response_lower:
            return 2
        elif '3' in response or 'nearly every' in response_lower:
            return 3
        return None
    
    def classify_score(self, score: int) -> str:
        if score >= 20:
            return "Severe depression"
        elif score >= 15:
            return "Moderately severe depression"
        elif score >= 10:
            return "Moderate depression"
        elif score >= 5:
            return "Mild depression"
        else:
            return "Minimal or no depression"