from fastapi import FastAPI
from pydantic import BaseModel
from chatbox import DietAssistant

# ��ʼ�� DietAssistant
diet_assistant = DietAssistant()

# FastAPI Ӧ��ʵ��
app = FastAPI()

# �����û����ݵ�����ģ��
class UserData(BaseModel):
    height: float
    weight: float
    age: int
    gender: str
    pre_meal_glucose: float
    pre_meal_insulin: int
    activity_level: str

class DiabetesQuestionRequest(BaseModel):
    question: str
    user_data: UserData

@app.get("/")
async def index():
    return {"message": "welcome!"}

# ����·�ɣ��ش���û����ݵ������������
@app.post("/answer-diabetes-question")
async def answer_diabetes_question(request: DiabetesQuestionRequest):
    print(request)
    response = diet_assistant.generate_response(
        request.question, 
        request.user_data
    )
    print(response)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10086)
