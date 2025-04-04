from fastapi import FastAPI
from pydantic import BaseModel
from chatbox import DietAssistant

# ��ʼ�� DietAssistant
diet_assistant = DietAssistant()

# FastAPI Ӧ��ʵ��
app = FastAPI()

# �����û����ݵ�����ģ��
class UserData(BaseModel):
    height: int
    weight: int
    age: int
    gender: str
    pre_meal_glucose: int
    pre_meal_insulin: int
    activity_level: str

class Question(BaseModel):
    question: str

@app.get("/")
async def index():
    return {"message": "welcome!"}

# ����·�ɣ��ش���û����ݵ������������
@app.post("/answer-diabetes-question")
async def answer_diabetes_question(question: Question, user_data: UserData):
    response = diet_assistant.generate_response(
        question.question, 
        user_data.model_dump()
    )
    print(response)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10086)
