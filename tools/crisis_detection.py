from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any

class CrisisDetectionTool:
    
    def __init__(self):
        self.detect_crisis = FunctionTool(self._detect_crisis)

    async def _detect_crisis(self, user_message: str) -> Dict[str, Any]:
        """
        Detect crisis situations in user messages.
        Returns crisis response if detected, otherwise empty.
        """
        crisis_indicators = [
            "kill myself", "suicide", "end it all", "want to die",
            "harm myself", "self harm", "not worth living",
            "better off dead", "can't go on", "end my life"
        ]
        
        message_lower = user_message.lower()
        if any(indicator in message_lower for indicator in crisis_indicators):
            return {
                "crisis_detected": True,
                "response": """🚨 **I'm deeply concerned about what you're sharing.**

**Please reach out for immediate help:**
• National Suicide Prevention Lifeline: 0800 587 0800
• Alternative Suicide Prevention Lifeline:  0800 689 0880
• Emergency Services: 999

You are not alone, and there are people who want to help you right now."""
            }
        
        return {"crisis_detected": False, "response": ""}